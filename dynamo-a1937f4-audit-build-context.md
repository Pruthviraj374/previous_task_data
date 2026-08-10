# dynamo/audit-build-context — gate failures, fixes, and what finally worked

Repo: `dynamo-a1937f4-build-dependency-and-release-management`, PR #2, branch `submission`,
fork `Pruthviraj374`.
Category: **Build Dependency and Release Management** / Sub-category: **Container Builds**.
Benchmarked against Opus-4.8 via Terminus-2. Accepted by every automated gate on 2026-08-09
at commit `76074b3`.

**Final result: pass@5 = 0/5 solved, avg@5 = 0.000, 5 good valid failures, 0 soft-timeout,
0 task/verifier issues, 0 reward hacking.** Best possible outcome. All seven per-trajectory
rubric criteria PASS on all five trials.

Two content cycles. `qc_gate` passed **first time** — the first task in this playbook to do so,
against `target-abi-audit`'s two QC cycles and `mirror-retention`'s repeated ones. §7 argues that
was earned by the pre-push discipline rather than luck, because the same sweeps QC runs were run
locally first. The single blocking failure was `ava_review`, and it was a repeat of a symptom
already in this directory.

---

## 1. The task

A build context is not the directory on disk — the builder filters it through the ignore file that
applies to the build. The agent reconstructs that filter.

- **Agent sees:** `/app/data/contexts/webapp` (built from `Dockerfile`) and
  `/app/data/contexts/apisvc` (built from `Dockerfile.api`), plus their correct reports at
  `/app/data/expected/*.txt` as an end-to-end self-check.
- **Agent produces:** `/app/ctxaudit.py`, invoked as
  `python3 /app/ctxaudit.py <context_dir> <dockerfile_name> <out_file>`, writing one relative path
  per line, sorted ascending by byte value, for every regular file the context carries — plus
  reports for both shipped contexts at `/app/output/`.
- **Graded on:** twelve *held-out* contexts, never shipped, each isolating one rule of the dialect.
- **Constraint:** one self-contained file, standard library only, no other process, no native
  library.

Shipped: webapp, apisvc. Held out: ledger, telemetry, printsvc, atlas, mailer, renderfarm, kioskui,
warehouse, warehouse-web, sensorhub, sunset, beacon.

---

## 2. The crux

> **The container builder's ignore dialect is not the ignore dialect every engineer has
> internalised from version control — and the resemblance is what makes the wrong one feel right.**

Ten independently-gradable divergences, all published Docker behaviour:

| Mechanism | What the familiar dialect gets wrong |
|---|---|
| Root anchoring | `*.log` taken to reach `svc/gateway/gateway.log`; patterns are anchored at the context root |
| Trailing separator | `build/` matched literally against `build/collector.o` and missing |
| Pattern normalisation | `./tmp`, `/etc-local`, `//legacy`, `deploy//staging`, `firmware/blobs/../blobs` matched as written |
| Negation re-admitting a subtree | `vendor` then `!vendor/patches` treated as "a pruned directory cannot be re-entered" |
| Single-star / `?` boundaries | `fnmatch`'s `*` spans separators, so `*/temp*` reaches `outbox/archive/tempfile` |
| Double-star depth | `**/cache` missing root-level `cache/`; `frames/**` not a prefix test; `**tmp` read as a directory boundary |
| Dockerfile-specific ignore file | `Dockerfile.worker.dockerignore` never consulted |
| Fallback to the root ignore file | over-correcting the previous rule breaks the ordinary case |
| Comment / whitespace handling | `!  calib/baseline.json` keeps its leading spaces and never matches |
| Regular files only | a symlink reported as if it were a file |

### The three invariants that make it work

1. **The samples never punish the shortcut.** Both shipped contexts stay inside the region where
   the two dialects coincide: no nested file matches a root-level glob, no trailing-separator
   pattern, no re-admission, no dedicated ignore file. Measured, not assumed — see §7.
2. **`instruction.md` names the dimension, never a rule.** It says the context is decided by the
   ignore file "resolved and interpreted exactly as the container builder does it," and that builds
   are "driven from Dockerfiles under various names." It never says anchored, `**`, negation,
   trailing separator, or `<dockerfile>.dockerignore`. Same move as `mirror-retention`'s "each
   ecosystem's own precedence rules."
3. **Held-out contexts exist only in `tests/`**, materialised from a declarative spec at verify
   time, with expectations computed in memory.

### Why breadth mattered more than depth

`target-abi-audit` §4's revised hypothesis held again: what survives is **the number of
independently-checkable consequences**, not whether they share one generating principle. pass@5
proves it directly — two trials (`DuMFHx7`, `nRtLz5H`) *did* implement the
`<dockerfile>.dockerignore` lookup correctly and still scored 0, because anchoring and
normalisation sank them. No single mechanism was load-bearing. A task resting on the dedicated
ignore file alone would have been solved 2/5.

---

## 3. Dead ends — do not retry these

### 3.1 An AST deny-list as the enforcement mechanism for "stdlib only / no dynamic exec"

**This is the third repo to lose a cycle to it.** `contact-export` §3.2 says it in plain words —
*do not patch the AST screen again* — and I shipped one anyway, banning `import_module`, `CDLL`,
`LoadLibrary` as *attribute* calls and `eval`/`exec`/`compile`/`__import__` as *name* calls.

AVA broke it in one pass with the obvious asymmetry: `from importlib import import_module` then
`import_module(...)` is a **Name** call, and `from ctypes import CDLL` then `CDLL(...)` likewise.
Neither was checked. The finding was `sound_verifier`, blocking.

The lesson is not "widen the list." Every widening invites the next spelling, and
`contact-export` §3.3 records two widenings that **rejected a correct solver**. See §4.2 for the
fix that actually holds.

### 3.2 Promising something you cannot enforce

The original instruction forbade "execute code dynamically (`eval`, `exec`, `__import__` or
equivalent)". At runtime that is not enforceable at sensible cost: `exec` and `compile` audit events
fire on every stdlib import of a `.py` module, so blocking them wholesale is impossible, and a code
object can still be run through `types.FunctionType` without touching any banned name.

**Deleted the clause.** `mirror-retention` Issue 6 is the precedent (network ban deleted for the
same reason), and the rubric never objected to the shorter sentence — `unambiguous` and
`test_instruction_alignment` both re-passed on the reworded instruction.

### 3.3 Taking commit identity from ambient session context

Both commits went out authored `Pruthviraj374 <vishnusai2183@gmail.com>` — right display name,
wrong person's email, taken from the environment rather than from the account that owns the fork.
Rewriting it later cost an in-flight pass@5 (§6). **Set `user.name`/`user.email` in the repo's
local git config at clone time**, from `gh api user` (`<id>+<login>@users.noreply.github.com`), and
never pass identity per-commit.

---

## 4. What actually worked

### 4.1 Ground truth from the real tool, not from a port of its source

The decisive authoring move. I fetched `moby/patternmatcher` and `ignorefile` and ported them to
Python — and then **ran every one of the fourteen context trees through an actual `docker build`**
(29.6.2, BuildKit) with `COPY . /ctx` + `find . -type f`, and diffed. 14/14 identical.

This is new to the playbook. Previous tasks derived ground truth from a specification or a
reference implementation; here the authority was executable, so "is my reference right?" stopped
being a judgement call. It also pre-answered the one question both the rubric review and
`deep_review` raised — each noted it could not re-run a real build to confirm the claim, and
neither could fault it.

It caught real behaviour a careful reading of the source would have got wrong. `**/*.pyc` looks
like it compiles to a suffix match (moby sets `suffixMatch` when `i == 0`), which would make it
match almost nothing; in fact a later loop iteration overwrites the type back to `regexpMatch`.
Only running it settles that.

### 4.2 Enforce behaviour with an audit hook, and probe **both** sides

Replacing the deny-list with a `sys.addaudithook` guard installed by a launcher before the graded
program runs:

- `import` event → reject any module whose top-level name is outside `sys.stdlib_module_names`
- `ctypes.dlopen` family → reject native-library loads
- `os.system` / `os.exec` / `os.fork` / `subprocess.Popen` family → reject process creation
  (the kernel also refuses, via `RLIMIT_NPROC (1,1)` after `setuid` to `nobody`)

Twelve bypass spellings probed **inside the built image**, all blocked: plain import,
`__import__`, `importlib.import_module`, from-imported `import_module`, `eval`-wrapped import,
`sys.path` injection, `CDLL`, `getattr(ctypes,'C'+'DLL')`, `cdll.LoadLibrary`, `subprocess`,
`getattr(os,'sys'+'tem')`, `os.fork`.

**The detail that matters, and that the playbook did not have: raise `ImportError`, not a bespoke
exception.** A solver that tries a third-party package inside `try/except ImportError` and falls
back to the standard library is *correct*, and a `RuntimeError` would kill it. Probed that case
explicitly — it still runs. That is the accept-side probe `contact-export` §3.3 demands, and it is
cheap: one extra fixture in the same script as the reject side.

AVA passed on the next push and again on the one after.

### 4.3 Mutation sweep before the first push, not after the gate

Eighteen one-rule inversions of the reference, each required to change some graded report. The
first run left four survivors, and analysing them was worth more than the sweep itself:

| Survivor | Verdict |
|---|---|
| leading `**` not a suffix test | **Real gap.** Closed by adding `**tmp` + `scratch/rendertmp/mesh.abc` to `renderfarm` |
| symlinks and specials included | **Real gap.** No fixture had a symlink. Closed by adding three to `beacon` |
| no lexical cleaning in the parser | Looked equivalent (`_Pattern.__init__` cleans too) — **but is not**, for a leading `//`. Closed by adding `//legacy` to `printsvc` |
| comment test after stripping | Genuinely unobservable — needs a tree containing a file whose name starts with `#`. Left, and documented in the README so a reviewer sees a decision, not an oversight |

Two of those four were the difference between accepted and a QC finding. The symlink one is
striking: **4 of 5 pass@5 trials failed `beacon` on exactly that guard** (`os.path.isfile` follows
symlinks; nobody adds `islink`). A mutation survivor became a load-bearing discriminator.

### 4.4 Coverage for every stated rule, including the boring ones

`instruction.md` said "a context that carries no files produces an empty report" and nothing pinned
it. `freight` §3 and `contact-export` §3.1 both record that as a `complete_test_coverage` FAIL
waiting to happen — a rule stated with no fixture witnessing it. Added `sunset` (`.dockerignore`
containing `**`). One pass@5 trial failed on precisely that test, having force-included the
Dockerfile against explicit instruction text.

---

## 5. Gate-by-gate log

### 5.1 Cycle 1 (`9699c70`) — `ava_review` BLOCK, everything else green

Green first time: `changes`, `review` (rubric **31/31**, zero failures), `cosine_similarity` +
`similarity` (UNIQUE, nearest `reshard-c4-data` at 0.101), `validation`, `ratelimit`,
`pass2` (**0/2, both valid fails**), `deep_review` (PASS, no blocking issues).

**`ava_review` → BLOCK**, `sound_verifier`: the AST deny-list checked `import_module`/`CDLL` only
as attribute calls. Two further advisories in the same class, plus a `verifier_coverage` advisory
("verifier imports its oracle module").

> Fixed in `76074b3`: deny-list deleted, `sys.addaudithook` launcher added, instruction reworded to
> promise only the three enforceable constraints, `test_reference_is_out_of_reach` added so the
> `verifier_coverage` advisory is answerable with a checked assertion rather than an argument.

### 5.2 Cycle 2 (`76074b3`) — everything green

`pass2` 0/2 again. `deep_review`, `ava_review`, `tier1`, `qc_eval`, `qc_exec`, `qc_gate` all PASS.
`pass2_suggestion` skipped by design. `trials` → **pass@5 0/5**, `accepted`.

Three independent pass@2 measurements (two on `9699c70`/`0aea05c`, one on `76074b3`) all returned
0/2 with `approach_validity: PASS` — the difficulty was robust to both the AVA fix and the history
rewrite, not an artifact of one roll.

### 5.3 What QC did *not* find, and why

`qc_gate` blocked nothing, twice. The classes it probes had all been run locally first:

- **Mutation of the reference** → §4.3, 17 of 18 caught before the first push.
- **Valid inputs no fixture constructs** (`target-abi-audit` §6's addition) → probed 14 of them
  against real Docker while a run was in flight: BOM, CRLF, no trailing newline, backslash escapes,
  `.`, `..`, `**/`, `[0-9]` classes, trailing whitespace, empty file, comments-only. Twelve agreed
  exactly. The three that made the reference *raise* are inputs **the real builder also rejects** —
  `docker build` returns `illegal exclusion pattern: "!"` and `syntax error in pattern`, the former
  being verbatim the message the reference raises. That is the answer to `freight` §4's "Oracle
  crashes, not wrong" finding: not a mishandled valid input, an input the tool itself refuses.
- **Harness erasing a requirement's signal** → checked that no fixture's input order is already the
  output order, which is why the "report left unsorted" mutant dies.

---

## 6. Process rules — one learned expensively

- **Never push while a run is in flight** — held for every content push. Then broke it deliberately
  to fix commit authorship, which cancelled a live pass@5 with **4 trials unanalysed**, consuming
  daily budget for nothing (`mirror-retention` Issue 9, same cost, different cause).

  The reasoning that made it the right call anyway is worth keeping: **a force-push re-runs every
  gate on the new SHA regardless, so a result on the old commit was going to be discarded either
  way.** Waiting would have burned the same budget and bought nothing. When a history rewrite is
  coming, do it *immediately* — the cost is fixed, and delay only adds a wasted measurement.

  The rule that would have avoided it entirely is §3.3: set the identity at clone time.

- **Verify your own probe harness before believing its output.** The edge-input probe reported 14
  mismatches at first. Every one was the harness writing a `Dockerfile` into the context *after*
  computing the reference answer, so all 14 differed by exactly that one path. Ten seconds of
  reading versus a redesign of a correct reference. Check that the diff is *structured* before
  concluding anything from it.

- **Sticky comments are edited in place** (confirmed again). A `BLOCK` visible right after a push is
  the previous commit's verdict until AVA re-runs; check the "Ran on `<sha>`" line.

- **`.gitignore` will silently drop your fixtures.** The repo's `.gitignore` excludes
  `node_modules/`, `.venv/`, `.env`, `*.pyc` — all of which the shipped contexts contain *on
  purpose*, since they are what an ignore file is for. `git add -f task/environment/data` and check
  `git diff --cached --name-only | wc -l` against the file count. These would have gone missing
  without changing any expected report (they are excluded from the context anyway), so no test
  would have caught it — only a reviewer noticing that `.dockerignore` names a directory that
  isn't there.

- **Never `git add -A`**; `task/jobs/` added to `.gitignore` up front.

---

## 7. The methodology that mattered

**Write the plausible-wrong implementations first, and make them plural.**

Before committing to the design I wrote three, each wrong in a different way: `fnmatch` on the path
plus ancestors; gitignore semantics with basename matching and directory pruning; anchored regex
with `**` collapsed to `*`. Then ran all three against every candidate fixture.

```
context         N1       N2       N3
webapp          ok       ok       ok       SAMPLE
apisvc          ok       ok       ok       SAMPLE
ledger          2        3        ok
printsvc        7        4        7
atlas           ok       ok       2
mailer          2        ok       ok
renderfarm      2        2        ok
kioskui         ok       ok       2
warehouse       7        7        7
sensorhub       1        ok       ok
beacon          2        2        2
```

**Zero diffs on both samples for all three; each fails five or six held-out contexts, and no two
fail the same set.** That table is the task. Note what it also proves: `telemetry`,
`warehouse-web` and `sunset` discriminate *nothing* — all three naive matchers pass them. They earn
their place as coverage (pinning a stated rule, guarding against over-correcting the dedicated-
ignore-file lookup), not as difficulty. Knowing which fixtures are which is worth the ten minutes.

`contact-export` §9 item 4 measured that 5 of 8 held-out fixtures carried the whole result and one
discriminated 0/5. Same here — and the plural-naive table tells you *in advance* which are which,
where a single naive implementation cannot.

---

## 8. Reusable checklist for the next task

Before writing code:
- [ ] Is the deciding rule a *published* convention tied to a visible input? If author-invented, it
      dies at `decisive_answer_discoverable`.
- [ ] Can ground truth be produced by **running the real tool** rather than reasoning about it? If
      yes, do that — it converts every correctness question into a diff, and pre-answers the
      reviewer note you will otherwise get.
- [ ] Write **two or three** plausible-wrong implementations, not one. Require 0 sample diffs from
      all of them and heavy held-out divergence from each.
- [ ] Count the independently-checkable consequences. Fewer than about six and one lucky agent
      insight solves it.

While building:
- [ ] Local git identity set from `gh api user` before the first commit.
- [ ] `git add -f` anything the repo `.gitignore` would swallow; verify the staged file count.
- [ ] `.dockerignore` present in `environment/`; no `tests`/`solution` substrings in the Dockerfile.
- [ ] No `"You have N seconds"` line. `[task].description` non-empty. No `task/README.md`.
- [ ] **Enforce constraints at run time; do not ship an AST deny-list of call names.** Audit hook
      for imports / native libraries / spawns, `RLIMIT_NPROC` for processes.
- [ ] State only what you enforce — delete any clause you cannot.
- [ ] Every rule stated in the instruction has a fixture that witnesses it, including the dull ones
      ("empty output", "regular files only").

Before every push:
- [ ] Oracle 1.0, nop 0.0, leak scan clean.
- [ ] Mutation sweep; **analyse each survivor rather than dismissing it** — two of mine were real
      coverage gaps and one became the discriminator that failed 4 of 5 trials.
- [ ] Probe the sandbox on **both** sides: bypass spellings blocked *and* a correct solver
      (including a graceful third-party fallback) still accepted.
- [ ] Probe valid-but-unfixtured inputs against the real tool; where the reference raises, confirm
      the real tool raises too.
- [ ] Root `README.md` updated in the same commit.

---

## 9. Final state

- **PR HEAD: `76074b3`** — the commit pass@5 was measured on. Do not push over it.
- Commits: `9699c70` initial submission · `76074b3` audit-hook enforcement (accepted).
  Both were rewritten from `e95c2b3`/`0aea05c` to correct the author email; content byte-identical.
- Authoring tooling (`author.py`, `naive.py`, `mutate.py`, `probe_guard.py`, `edge.py`, the ported
  `pm.go`/`ig.go`) lived only in the session scratchpad, never committed.

### What stumped the agents, in their own words (graders' pass@5 analysis)

> "The task's two shipped fixture contexts were deliberately chosen so that gitignore-style basename
> matching and Docker's root-anchored matching produce identical results; every agent verified clean
> diffs against those two contexts and declared success."

Four root causes in every trial, and the distribution is the design premise holding:

| Root cause | Trials |
|---|---|
| Root anchoring — matched the last path component at any depth | **5 of 5** |
| Pattern normalisation — never applied `filepath.Clean` to patterns | **5 of 5** |
| Symlinks — `os.path.isfile` follows them, no `islink` guard | 4 of 5 |
| Early `dirnames` pruning killing negation re-admission | 3 of 5 |
| Missing `<dockerfile>.dockerignore` lookup | 3 of 5 |
| Force-including the Dockerfile against explicit instruction text | 1 of 5 |

Two trials got the dedicated-ignore-file rule *right* and still scored 0. All five quit voluntarily
— in pass@2, at 11–13 minutes of a 60-minute budget — after the shipped contexts self-checked
clean. Every trial `approach_validity: PASS`, `near_miss: PASS` (structurally wrong, not marginal),
`reward_hacking: PASS`.
