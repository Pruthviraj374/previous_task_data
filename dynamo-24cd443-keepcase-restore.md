# dynamo/keepcase-restore — when the whole crux *family* is already in the weights

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 17 checks green, `accepted` label |
| **Repo** | `dynamo-24cd443-file-and-media-operations`, PR #1, branch `submission`, fork `charan-sr` |
| **Category / sub** | File and Media Operations / File permissions and metadata (pre-seeded) |
| **Benchmarked model** | reported as `Model A` (`task.toml` names Opus-4.8 / Terminus-2); gating pass@2 ran GPT-5.4 and DeepSeek v4-pro across the cycles |
| **Final commit** | `6b6a4d6`, after **9 commits and four consecutive "too easy" rejections** |
| **Headline** | **pass@5 = 2/5 solved, 3 good valid fails, avg@5 = 0.400.** Final pass@2 came back **0/2 (both valid fails)**. Reviewer's own summary: *"all failures trace to a single one-line ordering bug (chmod before xattr) on the task's hardest intended crux"* |

The fourth File and Media Operations entry, and the **direct successor to
`restore-stillwater-volumes`** — same category, adjacent sub-category, same "replay recorded state
onto a live filesystem" shape. That kinship is exactly what made it hard, and it is the reason this
entry exists: **`stillwater` was a one-push acceptance in this shape; fifteen months of model
progress later, the same shape needed nine commits and a jump to a different mechanism family.**

---

## 1. The task

A retired KEEPCASE document-archival appliance took nightly snapshots into a custom binary format.
The appliance's software is gone; the archives and a format note survive.

- **Agent sees:** `/app/data/KEEPCASE.md` (the invented `KVLT1` wire format, documented
  exhaustively — magic, record types `D`/`F`/`L`/`H`, exact field widths, endianness, bit layouts,
  and the data-shape guarantees every archive satisfies) plus one sample archive and a plain-text
  description of the tree it restores to.
- **Agent produces:** `/app/restore.py`, run as `python3 /app/restore.py <archive> <out_dir>`.
- **Graded on:** sixteen held-out archives, each restored into a private temp tree **as an
  unprivileged system account (uid/gid 1500)**, through a launcher that installs a
  `sys.addaudithook` guard. Exact and categorical throughout — no tolerances anywhere.

Parsing is deliberately trivial and nothing about the format is withheld. As in `stillwater`, every
difficulty is a **consequence** of the recorded data meeting real POSIX semantics, never a rule
stated anywhere.

---

## 2. The finding: a crux family can be *saturated*, and no amount of polishing escapes it

> **Four consecutive designs — four, five, and six mechanisms deep — were each solved 2/2 by the
> gating model. Not by shortcut. By knowing the material.**

This is the important part of this entry and I have not seen it recorded elsewhere in the corpus.

The first four mechanisms were textbook `stillwater`-family cruxes, each individually sound:

| # | Mechanism | The natural implementation does |
|---|---|---|
| 1 | Special bits live in a `special_flags` byte separate from `permission` | forgets to OR them in |
| 2 | An `H` record carries no metadata — it is a second *name* for one inode | writes a copy; inodes differ |
| 3 | A directory's recorded mode can be narrower than the writes still to come | applies it at `mkdir`, then `PermissionError` |
| 4 | A symlink target is raw text that may dangle or forward-reference | "safely" validates it first |

All four are real, documented, and dormant in the shipped sample. All four were **applied
correctly, first try, by two independent models.** The pass@2 analysis said it outright:

> *"Both agents independently used `reversed()` over a deferred directory list, OR-combined
> special_flags with POSIX constants from `stat`, and keyed hardlink lookups by record index —
> suggesting these patterns are directly readable from KEEPCASE.md and/or are well-established
> Python idioms for archive restoration."*

**What did not work — three attempts, each rejected 2/2:**

- **Strengthening mechanism 3.** The nested fixture used `0o500` for both levels, which retains the
  execute bit, so *any* finalization order passed. Changing the outer directory to `0o600` (no
  execute) made deepest-first genuinely mandatory. Correct fix to a real hole — and both trials
  still sailed through it.
- **Mechanism 5: symlink permission + `chmod` follows the link.** `L` records gained a `permission`
  field; applying it via `os.chmod` on the link's own path silently rewrites the *target's* mode
  (no `lchmod` on Linux). Genuinely subtle. **Both trials defended against it deliberately** — one
  wrapped `lchmod`/`fchmodat` in `try/except`, the other skipped symlink chmod entirely. It is a
  well-known enough Python FAQ that capable models treat it as a *reflex*, not an obstacle.
- **Mechanism 6: hardlink whose referent is an earlier symlink.** Also solved; one trial reached for
  `os.link(..., follow_symlinks=False)` unprompted.

**The escape was a different family, not a harder member of the same one.**

Mechanism 7: `F` records carry **extended attributes**. Setting a `user.*` xattr requires *write
permission on the file*, and a recorded mode of `0o444` removes it — **from the owner as much as
from anyone else.** So attributes must be applied *before* the chmod, not afterwards with the rest
of the metadata.

Three properties made this one land where four others had not:

1. **Nothing else about a mode-first ordering looks wrong.** `os.utime` on that same read-only file
   still succeeds. Only the attributes fail, so there is no general "apply metadata last is bad"
   signal to learn from — the punishment is surgical.
2. **The defensive reflex does not save you.** This is the direct lesson from mechanism 5's death.
   Wrapping the call in `try/except` — precisely what rescued both trials before — merely swallows
   the `EACCES` and leaves the attributes unset, which the verifier compares directly. **Both the
   crash path and the swallow path fail.**
3. **It is squarely in the pre-seeded sub-category** (file permissions and metadata) while being
   outside the saturated gotcha family.

Result: pass@2 flipped from 2/2 solved to **0/2 solved (both valid fails)** on the very next push,
and pass@5 landed at 2/5 with every failure tracing to this exact ordering.

### The design rule this yields

> **When trials fail a "too easy" gate, first ask whether they *shortcut* the crux or *knew* it.
> A shortcut means fix the fixture. Knowing it means the family is saturated — move to an adjacent
> mechanism family, and prefer a crux where the natural defensive reflex still fails.**

Reading the approach trace is what distinguishes these. Three pushes were spent strengthening a
family the model had already mastered, because "2/2 solved" alone does not tell you which case
you are in.

---

## 3. The near-miss: a crux built on documentation that was wrong

Worth recording on its own, because it nearly shipped.

Mechanism 6's **first** framing was: `os.link()` defaults to `follow_symlinks=True`, so hardlinking
a symlink dereferences it and links the target instead. A web search of the Python docs said exactly
that. I wrote the wire-format change, the fixture, the instruction bullet, the `task.toml` prose,
and the README — then built the mutant that "should" fail.

**The mutant scored 1.0.** On Linux, plain `os.link()` on a symlink source does *not* dereference.
The documented default does not describe the platform behaviour, and I had designed an entire
mechanism around a sentence that was false in the only environment that mattered.

Direct check in the target image settled it in one command:

```
docker run --rm python:3.13-slim-bookworm python3 -c "..."   # link2 is symlink: True, same inode: True
```

I reverted the whole framing with `git checkout --` on the unpushed tree and rebuilt the crux around
the real, verifier-checkable signal — **inode sharing** (a restorer that "recreates" an equivalent
symlink produces two links that read back identically but do not share an inode). That version's
mutant failed correctly, caught by exactly one test.

> **Rule: never design a fixture around a claimed OS/stdlib behaviour you have not executed in the
> actual target image.** A doc summary is a hypothesis. The mutant is the experiment — and it is the
> only reason this did not reach a reviewer.

Every behavioural claim in mechanism 7 was verified this way *before* any file was edited: `EACCES`
at `0o444`/`0o400`/`0o000`, `utime` unaffected, xattrs surviving a later chmod, and the whole thing
working under uid 1500 on the real overlayfs.

---

## 4. Gate-by-gate log

| # | Commit | Trigger | Fix |
|---|---|---|---|
| 1 | `0adcddc` | initial submission, 4 mechanisms | — |
| 2 | `534e5bb` | static check "Dockerfile must not COPY solution/ or tests/" | a **comment** contained the literal substring `tests/test.sh`. Pure string scan; reworded |
| 3 | `d130d07` | `deep_review` ran a pass@2 trial that crashed | **real bug:** verifier pre-created `output_dir` while `instruction.md` promised it would not exist. My own `solve.py` used `exist_ok=True` and masked it from local calibration. A trial using strict `os.mkdir()` exposed it |
| 4 | `f8e6f2b` | pass@2 too easy (1/4) | nested dir fixture used `0o500` both levels → execute bit retained → any order passed. Outer changed to `0o600` |
| 5 | `1f9a4e7` | `ava_review`: unenforced constraint | instruction claimed "no network, no shelling out" but only `-I -S` was enforced. Added `guard_launcher.py`, a `sys.addaudithook` runtime guard — **never a source scan** |
| 6 | `32b806e` | pass@2 too easy (2/4) | mechanism 5 (symlink permission / chmod-follows-link) |
| 7 | `5237c89` | pass@2 too easy (3/4) | mechanism 6 (hardlink to a symlink) — after the false-doc near-miss in §3 |
| 8 | `27259ea` | pass@2 too easy (4/4) | **mechanism 7 (xattrs before chmod)** → pass@2 **passed**, gate unlocked, `deep_review`/`qc_*`/`tier1` all green |
| 9 | `6b6a4d6` | `ava_review`: `verifier_coverage` | `instruction.md` required symlinks to end up with their recorded permission bits, but `assert_tree_matches` never asserted `S_IMODE` on symlinks — the stated requirement was unverified. Added the assertion → **ACCEPTED** |

### 4.1 Once pass@2 passes, prefer the *stricter* fix

Commit 9 is the one worth generalising. `ava_review` flagged a genuine instruction↔verifier gap, and
there were two ways to close it: relax the instruction (drop the symlink-permission requirement) or
tighten the verifier (assert it).

Every push **re-rolls the stochastic pass@2**, and pass@2 had just started passing after eight
commits of trying. Relaxing the instruction is a change that *could* make the task easier and put
that at risk. Asserting `S_IMODE` provably cannot — it is a no-op for every correct submission
(a Linux symlink invariably `lstat`s as `0o777`, exactly what the format records; verified across
dangling, forward-referencing, resolvable, and hardlinked links, under a restrictive umask).

pass@2 held on the re-roll. **When a stochastic gate is finally passing, choose the fix whose
worst case is "no effect".**

### 4.2 The `tmp_path` trap, caught during first calibration

`run_restore()` initially used pytest's `tmp_path`. The unprivileged subprocess got `PermissionError`
just *reading the archive* — `tmp_path` lives under a root-owned `0700` tree
(`/tmp/pytest-of-root/pytest-0/…`), so chowning the leaves is useless when the parent is impassable.
Fixed with `tempfile.mkdtemp(dir="/tmp")`. This is the identical finding as `read-cavity-captures`
§7 — **reading the corpus first is what made this ten minutes instead of an afternoon.**

### 4.3 Ground truth planted, and mutants for every mechanism

The `Builder` emits archive bytes and records the expected end state *in the same call* — never
re-derived by parsing the format a second time. Eight single-flaw mutants were kept in a scratch
dir and **re-run after every wire-format change** to confirm none had been silently neutered; each
still failed on its own mechanism test at the end. That discipline is what caught §3.

---

## 5. Reusable checklist

1. **On a "too easy" verdict, read the approach trace before touching anything.** Shortcut → fix the
   fixture. Correct application → the family is saturated; change families.
2. **Prefer cruxes where the defensive reflex still fails.** Capable models wrap risky syscalls in
   `try/except` by habit. If swallowing the error yields a passing state, the crux is already dead.
3. **Never design a fixture around a claimed OS/stdlib behaviour you have not executed in the target
   image.** `docker run <exact image> python3 -c "…"`. Docs describe intent; the kernel decides.
4. **Build the mutant before you trust the mechanism.** A mechanism whose mutant scores 1.0 is not a
   mechanism. This caught a false crux that was otherwise fully written and ready to push.
5. **Once a stochastic gate is passing, take the fix whose worst case is "no effect"** — tighten the
   verifier rather than loosen the instruction.
6. **A verifier that does not check a stated requirement is an acceptance-boundary gap**, even when
   the requirement is trivially satisfied. `ava_review` blocks on it. Assert everything the
   instruction demands.
7. **Static "Dockerfile must not COPY tests/" checks are string scans** — they match comments too.
8. **Enforce claimed constraints at runtime** (`sys.addaudithook`), never with a source scanner.
9. **Never use pytest's `tmp_path` when an unprivileged subprocess must reach the files.**
10. **A defensive `exist_ok=True` in your own reference can mask a verifier bug** from local
    calibration. Match the instruction's stated preconditions exactly on both sides.

### One-paragraph version for future me

KEEPCASE is the successor to `restore-stillwater-volumes` and proves that shape has aged: the entire
POSIX archive-restoration gotcha family — special bits, hardlink/symlink semantics, directory-mode
deferral, chmod-follows-symlink — is now saturated in frontier weights, and **four consecutive
designs were solved 2/2 by models that simply knew the material, not by shortcutting it.** Three
pushes were wasted strengthening that family before I read the traces closely enough to see the
pattern. The escape was an adjacent family in the same sub-category: extended attributes, where
setting a `user.*` xattr needs write permission the recorded `0o444` mode removes, so attributes
must precede the chmod — surgical (`utime` still succeeds, so nothing else looks wrong) and immune
to the `try/except` reflex that had rescued the two previous attempts (swallowing `EACCES` just
leaves the attribute unset, which the verifier compares directly). pass@2 went 2/2-solved →
0/2-solved on that one push; pass@5 finished 2/5 with every failure on that crux. Along the way a
mechanism built on a web summary of `os.link(follow_symlinks=True)` turned out to be **false on
Linux** and was caught only because its own mutant scored 1.0 — verify OS behaviour in the target
image, never from docs. Final block was `ava_review` catching that the instruction demanded symlink
permission bits the verifier never asserted; fixed by making the verifier stricter rather than the
instruction looser, deliberately, because pass@2 had just started passing and every push re-rolls it.
