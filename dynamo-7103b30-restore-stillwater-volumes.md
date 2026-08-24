# dynamo/restore-stillwater-volumes — the crux the model reads, names, and throws away

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 16 checks green, `accepted` label |
| **Repo** | `dynamo-7103b30-file-and-media-operations`, PR #1, branch `submission`, fork `Pruthviraj374` |
| **Category / sub** | File and Media Operations / Recovery and repair (pre-seeded) |
| **Benchmarked model** | reported as `Model A` (`task.toml` names Opus-4.8 / Terminus-2) |
| **Final commit** | `891572a` — the initial submission, never revised |
| **Headline** | **pass@5 = 0/5 solved, 5 good valid fails, avg@5 = 0.000, on ONE push.** Static 25/25, rubric 31/31, `qc_gate` 37/37 probes clean first cycle, `deep_review`/`ava_review` no blocking issues |

The third File and Media Operations entry (after `recover-zip-headers`, same sub-category, and
`rebuild-plate-rasterizer`). **Disjoint from both:** `recover-zip-headers` reconstructs entry
boundaries inside a corrupted container by decoding DEFLATE; this task's container is intact and
trivially parseable, and the difficulty is entirely in *replaying* recorded state onto a live
filesystem. No shared artifact, no shared governing authority (PKWARE APPNOTE vs. POSIX
semantics), no shared crux family.

---

## 1. The task

A retired STILLWATER shelf appliance wrote nightly dumps of the archival volumes it hosted. The
volumes and the restore tool are gone; the dumps survived.

- **Agent sees:** `/app/DUMPFMT.md` (the invented `SWDUMP1` format, documented exhaustively) and
  `/app/dump`, one complete recovered dump — a text `MANIFEST` plus a content-addressed `blobs/`.
- **Agent produces:** `/app/restore.py`, run as `python3 /app/restore.py <dump_dir> <target_dir>`
  **as an unprivileged user**, not root.
- **Graded on:** the shipped volume plus nine held out, each restored into a private temp tree.
  Exact and categorical throughout — no tolerances anywhere.

---

## 2. The crux, and why it is a different *kind* of crux from this corpus's usual one

> **Parsing is deliberately trivial and nothing about the format is withheld. The difficulty is
> that a filesystem does not simply accept the state you hand it — and every awkward part is a
> consequence of the recorded data, never a rule stated anywhere.**

This is the corpus's first accepted task where the crux is **neither a withheld published
convention nor a reverse-engineered rule**. It is *the platform's own behaviour under a faithful
transcription of fully-disclosed data* — the `repair-portal-dispatch` §2 shape ("disclose every
rule and let the tool's defaults defeat a faithful transcription"), transplanted from nginx to
POSIX. That shape is why discoverability gates had nothing to bite: `deep_review` recorded
`decisive_answer_discoverable` PASS, and `qc_gate` raised **zero** findings, on the first cycle.

Five held-back mechanisms, each a consequence rather than a rule:

| Mechanism | The natural implementation does |
|---|---|
| A record is a **name**, not an object — several names can record one node | writes a second copy; names no longer share an inode |
| Times carry nanoseconds | `os.utime(p, (t, t))` through a float, losing ~10²ns |
| A directory's recorded mode can be narrower than the writes still to come | applies it at `mkdir`, then `PermissionError` on its children |
| Mode words are four octal digits | masks to `0o777`, or lets the umask trim a create-mode, or chmods before writing and lets the kernel clear the set-user bit |
| Names are byte strings | decodes escapes into text, writes a re-encoded name |

### The invariant that carried the whole task

**The shipped volume is *inert* under every held-back mechanism — the wrong reading is
byte-identical there, not merely untested.** Its recorded times all land on a whole second, its
one restrictive directory mode is on an *empty* directory, its mode words are all umask-safe
low-three-digit, its names are all ASCII, and no two records name the same node.

Two mechanisms are deliberately **taught** by the sample instead (a directory's time must be
applied after its contents; a link's time must be set on the link), plus two files with identical
bytes on separate nodes — which kills a dedup-by-content shortcut early and, critically, makes the
agent *feel* it has understood the node/blob distinction. `tools/invariants.py` asserts both
halves and refuses to pass otherwise.

---

## 3. What the model actually did — 5/5 on one mechanism, by five different routes

Every trial read the `node` field, understood it, and discarded it. The routes differed, which is
what makes this the strongest confirmation of doc 34's central finding in this corpus:

- `task__io9LUyD` — *"Node number is recorded but we don't need to restore it."*
- `task__UwvKY6P`, `task__GpkbEm9` — explicit analytical dismissal: *"just informational."*
- `task__GpkbEm9` — parsed it, then **commented it out**: `# node_str = fields[1]  # ignored`
- `task__QXHEfXN` — parsed it into a local, omitted it from the records dict downstream
- `task__vtavdQH` — silently skipped column 1 during parsing

And the pass@2 trial, whose reasoning is the cleanest statement of the failure mode in the whole
corpus: *"Potential issue with `node` field not checked nor used. **Fine.**"*

`task__io9LUyD` also hit float mtime loss (+27 ns) — and the grader's note on it is worth keeping:
**the agent's own validation script used correct integer arithmetic for the comparison, and it
never applied that arithmetic in `restore.py`.** It had the right code in its hand, in the same
session, and shipped the wrong one.

---

## 4. What made this a one-push acceptance

### 4.1 The divergence matrix existed before any task file did

Eleven plausible-wrong restorers, each wrong in exactly one way, written and measured **before**
`instruction.md` existed — then re-run through the *real verifier in the built image* after every
change. `recover-zip-headers` §7 says write a *validating* variant too, and the analogue here was
`link_by_content` and `chmod_then_write`: the "more careful shortcut" versions. Both are caught by
the shipped volume, which is exactly where you want a careful-but-wrong implementation caught —
it makes the agent confident, not suspicious.

### 4.2 Planted ground truth, so `oracle = 1.000` is not a tautology

One declaration per volume emits **both** the dump and the expected end state (`tools/swdump.py`).
No `tests/_reference.py`, no second implementation to drift. `deep_review` singled this out:
*"the verifier's expecteds cannot silently drift toward an Oracle quirk — a real strength an
expert would trust."* Fourth confirmation of `reassemble-tap-sessions` §4.

### 4.3 Auditing my own reference against the fixtures found a gap no gate reached

After every gate had passed, I enumerated each decision the reference makes and asked which volume
pins it. **Narrowing directories deepest-first was implemented and graded by nothing** — every
restrictive directory still carried a traverse bit, so an outermost-first pass passed everything.
This is `replay-deposit-ledger` §C3 found by hand instead of by QC. Fixed locally (a directory
with mode `0444`, plus a `shallow_dirs` variant proving it discriminates) and **parked, not
pushed** — see §5.

### 4.4 A calibration variant that failed everything, and was not a triumph

The first `shallow_dirs` patch broke `latin1_path` (bytes vs str in the new sort key), so that row
failed all nine volumes and *looked* like a stronger result. Caught only by reading the row rather
than the verdict. `depot-batch-claims` §3(f) and `nfs4-access-audit` §4.3, third form: **a
calibration variant that fails everything is a bug in the variant until proven otherwise.**

---

## 5. The decision not to push after acceptance

Four validated improvements are parked in a local stash and were never pushed: the three
`deep_review` advisories (working-directory integrity check, per-call timeout 120s→20s with the
verifier budget raised to 600s, `tools/` labelled dev-only), and the §4.3 ordering fixture.

`reassemble-tap-sessions` §6 is explicit and was followed: **a push on an accepted PR re-rolls all
31 rubric criteria and burns a rate-limited pass@ slot.** The task scored the maximum on the
commit that is in origin. The pushed README describes the pushed implementation accurately (it
says pipeline results are recorded as they land, which was true when pushed), so there is no
README drift forcing a push either — the readme-rule's "never leave a stale README" applies to
drift *against the implementation*, and there is none.

**Rule confirmed:** hold improvements on an accepted PR unless something else forces the push.

---

## 6. Reusable checklist

- [ ] Ask whether the crux can be **the platform's behaviour under fully-disclosed data**, rather
      than a withheld convention. Discoverability gates have no purchase on it, and the model
      cannot recall its way past a `PermissionError` it has to predict.
- [ ] Build the shipped sample so every wrong reading is **byte-identical** there, and assert that
      as a standing invariant — not "the case is absent" but "the case is inert".
- [ ] **Teach** two mechanisms with the sample deliberately, so the agent converges to a green
      self-check with real confidence. Omission leaves it uncertain; equivalence makes it sure.
- [ ] Write the plausible-wrong implementations first; include the *careful shortcut* variants;
      re-run them through the real verifier in the built image after every change.
- [ ] Plant ground truth from the same declaration that emits the input.
- [ ] After the gates pass, enumerate every decision the reference makes and name the volume that
      pins it. Expect to find one that nothing grades.
- [ ] `.dockerignore` from the first commit; `jobs/` in `.gitignore` before the first `git add`.
- [ ] Once `accepted`, stop pushing.

### One-paragraph version for future me

Put the crux in the gap between *recorded state* and *what a filesystem will actually accept*,
disclose the format exhaustively, and make the shipped sample inert under every consequence of
that data while deliberately teaching two others — the model then validates against the sample,
goes green, and quits. It worked 5/5 by five different routes, and every trial had read and named
the deciding field before throwing it away; one of them had correct integer-nanosecond arithmetic
in its own validation script and still shipped floats in the restorer. Measure eleven wrong
implementations through the real verifier before writing any task file, plant ground truth from
the declaration that emits the input so `oracle = 1.000` means something, and after the gates go
green audit your own reference decision-by-decision for a rule nothing grades — that audit found
one here. Then, once the `accepted` label lands, hold every further improvement.
