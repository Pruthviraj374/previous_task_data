# dynamo/rebuild-release-tarballs — gate failures, fixes, and what finally worked

Repo: `dynamo-3419465-build-dependency-and-release-management`, PR #1, branch `submission`,
fork `Pruthviraj374`.
Category: **Build Dependency and Release Management** / Sub-category: **Release Artifacts**.
Benchmarked against Opus-4.8 via Terminus-2. Accepted by every automated gate on 2026-08-04
at commit `bf12f53`.

**Final result: pass@5 = 0/5 solved, avg@5 = 0.000, 5 good valid failures, 0 soft-timeout,
0 task/verifier issues, 0 reward hacking.** 16 checks green, 1 skipped by design
(`pass2_suggestion`).

Three pipeline runs across one day. Unusually clean — `adversarial_review` and `ava_review`
passed first time, which is the *opposite* of the cron task's experience. Section 4.1
explains why, because that is the transferable part.

---

## 1. The task

A project's published source tarballs still exist, with the `SHA256SUMS` that shipped
alongside them, but the pipeline that built them is gone. The agent reconstructs it.

- **Agent sees:** `/app/repos/` (five git repositories) and `/app/published/` (the tarball
  released for each project's most recent tag, plus `SHA256SUMS`). Those artifacts are
  declared the normative, byte-for-byte specification of the pipeline's output.
- **Agent produces:** an executable `/app/mkdist`, invoked as
  `/app/mkdist <repo_dir> <tag> <output_tar_gz>`.
- **Graded on:** five *held-out* repositories absent from the image, by exact SHA-256 of the
  produced tarball.

Sample repos: libratio, tinylex, hexview, cfgmerge, spoolctl.
Held-out: fenceline, saltpack, wirefmt, quilld, ledgerd.

---

## 2. The crux

> **Delegate the export to `git archive` on the tagged commit, instead of reimplementing it
> as a filtered directory walk.**

Delegating buys six independent behaviours at once:

| Behaviour | What a directory walk gets wrong |
|---|---|
| Resolves the **tag**, not the branch head | Wrong content entirely when the tag is superseded |
| Ignores **untracked** files | Build leftovers land in the tarball |
| Ignores **post-tag** commits | Files added or deleted after the tag |
| `export-ignore` at **every** directory level | Nested `.gitattributes` silently missed |
| `export-subst` expansion | `$Format:%H$` shipped literally |
| Symlinks, exec bits, empty files | Dereferenced, flattened, or dropped |

The hook that forces the mistake: **per-path mtimes.** Each member carries the committer
time of the newest commit reachable from the tag that touched that path. `git archive`
stamps everything with one commit time, so the archive *must* be unpacked, stamped and
repacked — and that repack is what tempts a solver off `git archive` altogether. The moment
they leave, they inherit the whole right-hand column.

Secondary discrimination: commits were **authored before they landed**, so a builder
reaching for author date instead of committer date is wrong wherever the two differ.

### The three invariants that make it work

1. **The samples never punish the shortcut.** All five sample tags sit at their branch head,
   with clean working trees and simple attribute patterns. A filtered directory walk
   reproduces every sample byte-exactly and has every reason to stop.
2. **`instruction.md` states the contract, never the method.** It never names `git archive`,
   `export-ignore`, `export-subst`, or the committer/author distinction. It does say the
   builder will run on other repositories from the same organisation, so derive from the
   repository and tag rather than from these five.
3. **Held-out repositories exist only in `tests/`**, materialised at verify time.

---

## 3. Dead ends — do not retry these

### 3.1 Obscure factual recall as the crux

Established across six prior designs on other repos: recall traps die at the rubric's
`essential_difficulty` criterion, which explicitly disqualifies "difficulty that comes from
obscure factual recall" — and with `allow_internet = true` (mandatory; the static check
*fails* `allow_internet = false`) a non-expert can look the fact up anyway.

The escape is a decision that is **well-documented** — therefore fair and reviewable — but
that the samples never punish you for getting wrong. Architecture, not trivia.

### 3.2 Anything fully specified and self-contained

Opus self-verifies hard: it recalls standards, writes exhaustive per-rule tests, and will
fuzz against a stated invariant. Fully-specified self-contained coding tasks get solved 2/2.
Difficulty has to live in what the *samples* fail to exercise, not in the spec's length.

### 3.3 The `"You have N seconds to complete this task"` line

`00-ATTEMPTER-SPEC.md` §3 mandates it and claims CI enforces it. **Both wrong**, confirmed
again here. No static check requires it, and the rubric flags it under
`instruction_concision` as a TB3 template artifact. Deliberately absent.

---

## 4. What actually worked

1. **An architectural crux with a single correct insight.** One decision fixes all six
   divergences, which is what keeps it fair: an expert who delegates the export gets
   everything right at once.
2. **Held-out grading on repository *shapes*, not repository *contents*.** Each held-out repo
   isolates one way working-tree and tagged-export diverge.
3. **Amplifiers dialled up deliberately** — silent failure (a wrong archive is a plausible
   near-miss; the only diagnostic is a checksum mismatch), no self-check (samples all pass
   while held-out fails), all-or-nothing (byte-exact, justified by the domain rather than
   imposed for difficulty).

### 4.1 Why adversarial_review and AVA passed first time

The cron task lost two full cycles to *"the solver shares a filesystem with the answers."*
Designing against that class up front cost about twenty minutes here:

- Expected artifacts are computed in the pytest process and held **in memory only** — never
  written where the solver could glob for them.
- `pipeline.py`, `makerepos.py` and `heldout_projects.py` are **deleted from `/tests`** before
  `/app/mkdist` is ever executed, along with `__pycache__`.
- Each held-out repo is **copied to a fresh scratch directory** per invocation, so a builder
  that mutates a repository cannot affect later checks.
- Nothing under `/app` is graded against. The four shipped sample tarballs are deliberately
  **not** used as expectations, precisely because they are agent-writable.

**Transferable rule: build the verifier as if `adversarial_review` had already failed you.**

### 4.2 Disclose the mechanism, withhold the shapes

The `approach_validity` criterion in the pass@2 analysis **blocks** the PR when a decisive
rule is undisclosed. What threads the needle: make the samples demonstrate every *mechanism*
(spoolctl exercises `export-subst` and nested `export-ignore`), and hold back only *other
shapes of the same mechanism* — anchored globs, wider `$Format:...$` sets, two-level
attributes files.

`approach_validity` passed on all 12 graded trials. pass@5 stayed 0/5 after disclosure.

---

## 5. Gate-by-gate failure log

### 5.1 `qc_gate` — two blocking findings at `6a998f6`

**C3 — narrow / hardcodable held-out coverage.** QC **mutates the reference and re-scores
it.** It swapped the timestamp source from committer date `%ct` to author date `%at` and the
mutant **still scored 1.0**, because every fixture commit had `author_date == committer_date`.
The verifier could not tell the two apart.

> Fixed in `88e0690`: added an `authored` field to the history spec, made the dates diverge
> across both sample and held-out repos, and added a fifth held-out repo (`ledgerd`) with
> `test_release_with_multi_level_attributes`.

**B5 — underdetermined / hidden-knowledge mapping.** `export-subst` appeared only in held-out
repos, so nothing agent-visible established it as part of the pipeline.

> Fixed in `88e0690`: added a fifth *sample* repo (`spoolctl`) whose published artifact
> demonstrates `export-subst` and nested `export-ignore`, plus a sentence in
> `instruction.md`'s neighbourhood of the spec and matching `task.toml` prose.

Both fixes were verified not to soften the trap: **pass@5 after them was still 0/5.**

**Generalisable:** ask *"which one-token mutations of my reference would still score 1.0?"*
while designing held-out coverage, not at the gate.

### 5.2 `pass2` — variance on a docs-only push

Runs on `6a998f6` and `88e0690` both returned **0/2**. The run on `bf12f53` — a
**README-only commit** — returned **1/2**. The gate still passed and pass@5 still came back
0/5, but a documentation change re-rolled the trials and consumed budget.

**Rule: batch changes. Never push docs separately from code.**

### 5.3 `static` — `.dockerignore`

"non-trivial build context has a .dockerignore" fails whenever the build context is more than
a bare Dockerfile. Added `task/environment/.dockerignore` up front. Cheap; don't learn it
from CI.

### 5.4 The README, missed until the end

The repo's own `README.md` closes with *"When your task is complete, replace this README with
a short description of your task (overview, approach, environment, and how verification
works)."* I had left the scaffold in place through three runs.

Note the distinction: the **root** README is required. A **`task/README.md` is optional**, and
the rubric FAILs it if it duplicates `instruction.md`, the solution, or `task.toml` metadata —
absent scores N/A, which is a pass. Root: replace. Task-level: leave out.

---

## 6. Process rules learned the hard way

- **Never push while a run is in flight** — `concurrency: cancel-in-progress: true`. Check
  `gh pr checks 1` first; any `pending`/`queued` means wait.
- **Every push re-rolls pass@2 and pass@5** on a limited daily trial budget. A green
  measurement has value; do not spend it on cosmetics.
- **Never `git add -A`** — it sweeps in `task/jobs/`, Harbor's local run output. Added
  `task/jobs/` to `.gitignore` and staged explicit paths.
- **`[task].description` must be non-empty** or the "no placeholders" static check fails.
- **Leak-scan the built image**, don't assume the multi-stage build worked:
  ```
  find / -xdev \( -name "solve.sh" -o -name "pipeline.py" -o -name "make_fixtures.py" \
    -o -name "makerepos.py" -o -name "heldout_projects.py" -o -name "mkdist*" \)
  ```

---

## 7. The methodology that actually mattered

**Write the plausible-wrong implementation yourself, before pushing anything.**

I wrote a diligent filtered directory walk — root-`.gitattributes` parsing, per-path mtimes
from `git log`, exec-bit preservation — and ran it against both sets.

The first attempt failed **all four** samples, which would have been a broken design: agents
would be forced to keep fixing and would find the right answer. The only difference was
directory mode — `os.makedirs` yields 0755 under umask 022, while git's export machinery
emits 0775 (git's default `tar.umask` is 002). One line later:

> **naive builder: 4/4 samples exact, 3/4 held-out failed.**

That single measurement is the whole task. Intuition about what the agent will write is not a
substitute — my first guess was wrong in a way that would have sunk the design.

Determinism came from the same discipline: histories generated from a declarative spec with
fixed identities and fixed author/committer dates, so object ids are byte-identical every
run; generation confined to a throwaway multi-stage builder so neither generator nor pipeline
reaches the agent image.

---

## 8. Verifier hardening checklist for the next task

- **Never grade against anything under `/app`** — it is agent-writable.
- **Expectations in memory, not on disk**, while the solver runs.
- **Delete the reference implementation and history spec from `/tests`** before invoking the
  program under test, and clear `__pycache__`. `chmod` is not enough — the verifier runs as
  **root**.
- **Copy each input to a scratch directory** per invocation, so a mutating solver cannot
  affect later checks.
- **Every implemented rule needs a fixture that fails when the rule is broken.** QC mutates
  your reference hunting for uncovered branches — the author/committer date split was exactly
  this.
- **One test per behaviour, each with a docstring**, so a failure names the broken behaviour
  rather than just the repo.
- **Justify exact comparison in `verification_explanation`** when you use it — say why no
  tolerance is the right bar, or the criterion reads it as an unjustified inequality.

---

## 9. Final state

- **PR HEAD: `bf12f53`** — the commit pass@5 was measured on. Do not push over it.
- Commits: `6a998f6` initial · `88e0690` QC fixes · `bf12f53` README replacement.
- Local scratch calibration lives outside the repo
  (`scratchpad/naive_mkdist.py`) and was deliberately never committed.

### What stumped the agents, in their own words

Across 12 graded trials, one solve. Failures split into two clusters the graders described as
*"stratified, not uniform — no shared verifier or spec deficiency explains both"*:

1. **Cluster A — rejected delegation.** Built a custom file-selection layer with hand-rolled
   `.gitattributes` parsing. Handled the literal patterns the samples show; broke on nested
   attribute files, anchored globs and wider `export-subst` format strings. Symptom: archives
   **too large** (+5 to +123 bytes) from missed `export-ignore`.
2. **Cluster B — correct architecture, narrow gaps.** Reproduced **all five sample tarballs
   exactly**, then failed on held-out: one dropped symlink tar entries (typeflag `0x32`),
   another passed the tag name instead of the dereferenced `tag^{commit}` to `git log`.
   Symptom: archives **too small** (−5 to −25 bytes).

The byte-delta sign cleanly separates the two clusters. That agents reached a *plausible,
sample-perfect* result and stopped is the design premise holding: the model has a strong prior
for "tar up a source tree", and the task sits precisely in the gap that prior leaves.
