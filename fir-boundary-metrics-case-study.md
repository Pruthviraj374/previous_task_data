# Dynamo Task Authoring Playbook — Case Study: `fir-boundary-metrics`

**Status:** Task accepted (all automated Dynamo checks passed, PR labeled `accepted`) — now in human review.
**PR:** https://github.com/handshake-project-dynamo/dynamo-7287d05-data-processing-and-etl/pull/1
**Repo:** `handshake-project-dynamo/dynamo-7287d05-data-processing-and-etl`
**Category / Subcategory (pre-seeded, never editable):** Data Processing and ETL / Geospatial data processing

This document is a reusable playbook. It captures (1) what the Project Dynamo / Terminal-Bench-2 (TB2) task-authoring program actually requires, (2) the exact design and build process that worked for this task, (3) every review-pipeline failure we hit and the fix, and (4) the general lessons that should transfer to the *next* task, in this category or any other. Read section 10 first if you're in a hurry — it's the distilled playbook. The rest is the evidence for why it's true.

**Cross-validated against a second, independent task** (`dynamo/rebuild-release-tarballs`, category *Build Dependency and Release Management / Release Artifacts*, also accepted — 0/5 pass@5, the cleanest possible outcome). Findings that only that second task surfaced are folded into §6.6–6.8 and §9 below and clearly attributed; everything else in this document was independently re-derived on both tasks, which is itself worth trusting more than either alone.

---

## 1. Program context — what you're actually building

Project Dynamo pays contributors to author **Terminal-Bench 2 (TB2) tasks**: self-contained Docker challenges designed to make a frontier coding agent (benchmarked model: **GPT-5.4 / Opus-4.8** via agent **Terminus-2**) *fail*, while a golden reference solution still proves the task is solvable. The full authoring reference lives in a local doc set:

```
C:\Users\chara\Downloads\Handshake\verify\
├── CLAUDE.md                          # top-level pointer, read first
├── stumping_guidelines.md             # empirical findings from PAST sessions — read every time
├── reviewer_guideline.md              # what a human reviewer checks (large, skim)
├── error.md                           # common rejection causes, grouped by area
└── project_dynamo\project_dynamo\
    ├── 00-ATTEMPTER-SPEC.md           # THE cheat sheet — read this first, always
    ├── 05-task-categories.md          # category/subcategory + taxonomy
    ├── 31-34 (stump-the-model-*.md)   # the 9 stumping patterns + live graded examples
    └── 44-stump-techniques-*.md       # category-specific addenda (only SE/scripting exists today —
                                        #   there was no geospatial-specific addendum; general patterns had to be applied)
```

**A task = 5 pieces, all under `task/`:**

| File | Purpose |
|---|---|
| `instruction.md` | The *only* thing the agent sees. ≤1500 tokens, human-written, absolute `/app/...` paths, ends with... actually see §7.2, this rule turned out to be wrong for this repo. |
| `solution/solve.sh` (+ helpers) | Golden reference. Proves solvability. Never shipped to the agent. |
| `tests/test.sh` + `tests/test_outputs.py` | Verifier. Overlaid at `/tests` only at *verify* time (after the agent's run ends). Writes `reward.txt` (0/1). |
| `environment/Dockerfile` | **Single** image for both agent run and verifier run. Never `COPY`s `solution/` or `tests/`. |
| `task.toml` | Metadata: name, category/subcategory (pre-seeded, don't touch), timeouts, resources, and three long free-text explanation fields you must write. |

**The golden rule:** the agent never sees the solution or tests; grading is purely from artifacts left on disk. **Difficulty must come from reasoning, never from CPU/memory/wall-clock/busywork.**

**Acceptance bar:** the agent must fail **≥3 of 5** trials genuinely (pass@5 ≤ 2/5 solved). 0/5 valid failures ("fully stumped, oracle still solves it") is the *best* outcome, not a red flag. A task that's too easy (3–5/5 solved) gets rejected and must be made *harder through more reasoning*, never through a shorter timeout or busywork.

---

## 2. The stumping framework (condensed)

**The single sentence that matters:** make the agent do ~90% of the work correctly and then fail on **one decisive, determinate point** it cannot pattern-match, recall, or self-verify its way past.

**The 9 stumping patterns** (from `00-ATTEMPTER-SPEC.md` §7 / doc 32): Latent crux (A), Wrong-default lure (B), Misdirection (C), Evidence-forced reverse engineering (D), Ordering/invariant assumption (E), Discovery-hop (F), Multi-mechanism accumulation (G), Entangled rules (H), Stale authority (I). This task used **Pattern A/B**: a rule that's real and correct but never fires on the visible sample, and a cheap heuristic that's *almost* equivalent to the correct-but-more-expensive rule, diverging only on a rare case.

**Amplifiers:** silent failure (wrong answer looks normal, no crash), no self-check (real grading is on hidden cases), all-or-nothing (no partial credit).

**Fairness lines (do not cross):** figure-out-able from what's given; punishes a real mistake, not a random gotcha; fair margins (not a hairline tolerance); no uncorrectable lie (fine to hide the deciding case, never state a wrong rule nothing can correct).

**The empirical meta-lesson** (from `stumping_guidelines.md`, itself the summary of *prior* sessions' failures on *other* repos): a hard task does not depend on the model not knowing something — Opus-4.8 self-verifies aggressively (recalls whole specs, writes its own exhaustive tests, even fuzzes against invariants). **What survives it is correctness that is NOT self-verifiable** — an obscure fact or edge case the model misremembers or forgets to apply, and *cannot self-check* because the sample never exercises it. Best categories for this pattern: `data_processing_and_etl`, `file_format_parsing_and_serialization`, `security/digital_forensics`, `scientific_computing` — this task's category was already the empirically-favored one.

---

## 3. The task we built

**`dynamo/fir-boundary-metrics`** — the agent must write `/app/solve.py`, a generic program invoked as `python3 /app/solve.py <input_geojson> <output_csv>`, that reads a GeoJSON `FeatureCollection` of airspace boundary polygons (Flight Information Regions) and computes, per region: `area_km2` (true spherical surface area) and `perimeter_km` (great-circle boundary length), modeling Earth as a sphere of radius 6371.0088 km, using **only the Python standard library** (no third-party packages, no network).

**The trap (Pattern A/B):** the standard "spherical shoelace" area formula accumulates, per vertex, `(longitude of next neighbor − longitude of previous neighbor) × sin(latitude)`. That longitude difference is a plain subtraction almost everywhere — and is exactly wrong once a ring's longitude crosses ±180° (the antimeridian): raw `179 − (−179) = 358°` where the true shortest angular step is `−2°`. The visible sample never contains a crossing region, so the naive and correct formulas agree everywhere the agent can check; the bug only manifests on two held-out regions, and produces a plausible-looking number ~17×–35× too large, with no crash, no error, nothing to catch the agent's attention.

**Perimeter is a deliberately "safe" secondary field:** haversine great-circle distance uses `sin²(Δ/2)`, which is mathematically invariant to how you express the longitude delta (verified numerically), so it's naturally correct regardless of the antimeridian bug — it adds real, separately-graded implementation work without hinting at the trap.

**Anti-cheat constraint:** stdlib-only + no network was *load-bearing*, not decorative — a web search during design confirmed a dedicated PyPI package (`antimeridian`) exists specifically to fix this exact class of bug, so without the constraint a capable agent could `pip install` its way past the whole trap.

---

## 4. Build steps (the reusable checklist)

1. **Read the doc set in order**, not just the spec — specifically doc 33 (amplifiers/fairness), doc 34 (live graded examples — read *every* example, the cross-example pattern matters more than any one strategy page), and the category-specific addendum if one exists for your subcategory.
2. **Read `stumping_guidelines.md`** — it's a memory file from prior sessions on *other* repos, but the empirical findings (which categories work, which patterns are structurally dead, the "both-horns" catch-22 described in §8.1 below) transfer directly.
3. **Web-search for domain-specific pitfalls** in your subcategory before designing — this task's design was informed by a real search confirming the antimeridian bug is a well-documented, widely-hit GIS pitfall (which cuts both ways: it confirmed the trap is *real and fair*, but also confirmed a fix-package exists, which is why stdlib-only had to be enforced).
4. **Apply the two fairness pre-checks before writing any code**:
   - Is the deciding case something requiring *outside domain knowledge* the visible sample never demonstrates — or just careful reading of the stated spec? Only the former reliably stumps the model (per the live graded examples).
   - Is the deciding case named anywhere the agent can read (instruction, comments, variable names, sample data)? It must not be.
5. **Design data + oracle together.** Build `solve.py` (the correct, antimeridian-safe implementation) *and* a throwaway "naive" variant, and numerically diff them on your planned sample + held-out data. Confirm: (a) naive == correct on every *visible* sample row, (b) naive diverges sharply (order-of-magnitude, not a near-miss) on the *held-out* rows. This numeric check is cheap and catches a dead design before it ever touches CI.
6. **Write instruction.md** — describe *what*, not *how*; name every output file and format precisely; do not hint at the trap.
7. **Write task.toml** — `task_objective`/`artifact_type` from the taxonomy file; `expert_time_estimate_hours` consistent with the described difficulty; and the three long explanation fields (`difficulty_explanation`, `solution_explanation`, `verification_explanation`) — these are read by *human and automated reviewers*, not the agent, so be fully explicit about the trap there.
8. **Write the verifier** with the isolation/anti-cheat patterns in §8.2 below *before* your first push — retrofitting them after a QC failure costs a full pipeline cycle.
9. **Calibrate locally, every single time, before every push:**
   ```
   cd task
   harbor run -p . --agent oracle   # must be reward 1.0
   harbor run -p . --agent nop      # must be reward < 1.0
   ```
   Never push without both passing. This is free and instant; the remote pipeline is not.
10. **Fork → branch `submission` → push → `gh pr create --fill`.** Iterate by pushing to the same branch; the pipeline re-runs automatically and posts sticky PR comments per gate.

---

## 5. The review pipeline, gate by gate

Pushing to the PR branch triggers, in order (each gate blocks the next):

| # | Gate | What it checks | What happens on failure |
|---|---|---|---|
| 1 | **Static checks** | Structural: file layout, `task.toml` fields filled, taxonomy labels valid, Dockerfile hygiene (pinned digests, apt cleanup, no `COPY solution/`/`tests/`), `.dockerignore` present for any non-trivial build context, instruction ≤1500 tokens, timeouts in range | Blocks everything downstream; fix is usually mechanical |
| 2 | **Rubric review ("Dynamo eval")** | LLM grades all 31 rubric criteria from `dynamo-rubric.toml` (code_dependent, essential_difficulty, unambiguous, outcome_verified, anti_cheat, solution_quality, etc.) | Posts PASS/FAIL per criterion with notes |
| 3 | **Duplicate check** | Compares `instruction.md` against existing TB2/TB3 task sets for novelty | Rare to fail if the domain+mechanism combo is genuinely novel |
| 4 | **Validation** | Actually builds the Docker image and runs oracle (must hit reward 1.0) and nop (must be < 1.0) in the real environment | If this disagrees with your local `harbor run`, something is environment-specific — investigate before pushing again |
| 5 | **pass@2 (timeout pre-check)** | Runs the real benchmarked agent **twice**, 3600s cap each. Gate = **at least one genuine agent failure** (not both solved, not both timed out/errored) | Both solved → task too easy, make it harder. Both errored → infra/task bug, don't just extend the timeout unless timeout really was the cause |
| 6 | **deep_review / adversarial_review / ava_review** | A much stricter automated pass that reads the *actual pass@2 agent traces* and checks whether every requirement is instruction-derivable, whether the verifier tests exactly what's disclosed, and whether the ground truth is genuinely agent-unreachable | Blocking issues come with a concrete fix inline; this is where subtle ambiguity gets caught |
| 7 | **tier1 → QC (qc_eval/qc_exec/qc_gate)** | An even stricter, **execution-based** adversarial probe — it actually constructs and runs adversarial/degenerate submissions against your live verifier (empty output, wrong-reading implementations, harness-exploit attempts) | This caught 4 real bugs in our verifier (see §7.3) that no amount of static reasoning would have found |
| 8 | **trials (pass@5)** | The real, final benchmark: 5 trials, needs ≥3 genuine failures | avg@5 and per-trial rubric (task_specification, reward_hacking, difficulty_crux, near_miss, refusals, low_timeout, approach_validity) all get reported |
| 9 | **gate** | Aggregates everything; sets the PR label (`accepted` / `needs-revision`) | `accepted` = ready for human R1→R2 review |

**Resource note:** pass@2 is capped at **6 runs per day** — do not burn it on speculative pushes. Every push after gate 4 restarts the *whole* remote pipeline including a fresh pass@2, even if only gate 6+ actually needs re-checking. Batch your fixes; recalibrate locally first; push once per real, considered change.

---

## 6. Iteration log — what actually went wrong, in order

This is the part worth re-reading before your *next* task, because every failure here is a **generic** failure mode, not specific to antimeridian geometry.

### 6.1 — Static check: missing `.dockerignore`
**Symptom:** `FAIL: non-trivial build context (has subdirectories) but no .dockerignore`.
**Cause:** `task/environment/` had a `data/` subdirectory but no `.dockerignore`.
**Fix:** add a minimal `.dockerignore` (`**/__pycache__/`, `**/*.pyc`, `.DS_Store`) next to the Dockerfile. Takes 30 seconds — check for this proactively on any task with a data subdirectory, don't wait to be told. *(Independently hit and fixed the same way on `rebuild-release-tarballs` too — add this file up front on every task, don't wait for CI to point it out.)*

### 6.2 — Rubric review: leftover TB3 boilerplate
**Symptom:** `instruction_concision` FAIL — "You have N seconds to complete this task..." flagged as "TB3 time-budget/anti-cheat artifact... does not belong in a TB2 task."
**Cause:** the local doc set (`00-ATTEMPTER-SPEC.md`, `CLAUDE.md`) explicitly *mandates* this exact closing line, citing a `check-instruction-suffix` CI check. **The live rubric contradicted the static docs.** The actual `dynamo-rubric.toml`'s `instruction_concision` criterion says nothing about a required timeout line, and the static-check list in this repo never enforced one either.
**Lesson: trust the live, current pipeline feedback over locally-cached documentation when they conflict.** Docs can be stale; the rubric that's actually grading you cannot be argued with. Delete the line; the budget already lives in `task.toml`'s `[agent].timeout_sec`.

**Independently confirmed on a second, unrelated repo/category** (`rebuild-release-tarballs`, Build Dependency and Release Management) — same finding, same fix, no exceptions found across two categories so far. Treat this as a near-certain trap on every new task, not a one-off quirk of this repo: omit the line by default and only add it back if a specific repo's static checks explicitly demand it.

### 6.3 — The disclosure-calibration catch-22 (the central lesson of this task)

This took **five separate pass@2 cycles** to resolve and is the single most transferable finding in this document.

**The problem:** the antimeridian trap requires *some* fairness disclosure (per `unambiguous` and per deep_review's own explicit blocking finding — see below), but any disclosure strong enough to satisfy a reviewer also taught the model exactly what to fix.

| Attempt | Instruction wording | pass@2 result | Verdict |
|---|---|---|---|
| 1 | No mention of edge convention at all | 0/2 solved (genuine fail) | ✅ hard, but... |
| — | *(deep_review flagged: "great-circle arc" is a second sound reading that would also fail — genuine ambiguity)* | | ❌ blocked |
| 2 | Added "...not a great-circle arc (the standard **simple-features convention**)" | 0/2 solved | ✅ hard |
| — | *(QC — the stricter, execution-based gate — flagged "simple-features" as literally implying a flat/Cartesian reading, i.e. the wrong/naive answer, via a constructed counter-example)* | | ❌ blocked |
| 3 | Removed "simple-features," added explicit periodicity clause: "...a value and the same value ±360° of longitude denote the identical point" | **2/2 solved** | ❌ too easy — fully spelling out the consequence handed the agent the fix |
| 4 | Removed periodicity clause entirely, kept "not a great-circle arc" only, and **shipped one antimeridian-crossing region in the visible sample** (deep_review's own suggested "stronger fix") | **2/2 solved** | ❌ *still* too easy — a witnessed example is just as strong a hint as prose, because the model already knows the underlying GIS fact and just needed permission to apply it |
| 5 | Reverted the witnessed sample; instead stated the **valid numeric range** of the coordinate fields in the schema paragraph — `longitude in (-180, 180], latitude in [-90, 90]` — as ordinary field-schema metadata, with **zero mention** of wraparound, periodicity-as-a-consequence, or the antimeridian | **1/2 solved, 0 ambiguity flags** | ✅✅ threaded the needle — carried through deep_review, adversarial_review, ava_review, QC, and pass@5 (2/5 solved, 3/5 genuine, clean fairness on all 5 trials) cleanly |

**Why attempt 5 worked where 3 and 4 didn't:** a *stated numeric range* is completely standard, expected schema documentation (any structured-input spec should state field bounds — this isn't optional per the `structured_data_schema` rubric criterion) — but it does not spell out the *consequence* of that range for a difference computation. A careful implementer who actually thinks through "what does it mean that longitude is bounded at ±180°?" can derive the fix; an implementer who reads it as inert metadata (as most did) doesn't. This is qualitatively different from restating the fix's *result* directly.

**The general, transferable heuristic:**
- **Full disclosure of a fix's consequence → the model applies it correctly essentially every time, once it's salient in *any* form** (prose, a witnessed sample, whatever). Frontier models (Opus-4.8 here) already possess the relevant domain fact cold; the sample never showing the case is what suppresses it, not lack of knowledge. The moment *anything* makes the case salient, the suppression is gone.
- **Zero disclosure of the underlying structural fact → real risk of a genuine, reviewer-confirmed ambiguity**, because your own wording can accidentally read as endorsing the wrong reading (as "simple-features convention" did) even when you didn't intend it to.
- **The sweet spot is disclosing the *raw fact* (a definition, a range, a unit, a convention) without disclosing its *consequence* for the specific computation being asked for.** State the premise; let deriving the implication be the actual skill being tested.
- **When deep_review/QC suggests a specific fix, treat "the minimum viable version of it" and "the maximal version of it" as two different experiments** — the review comment itself may offer a spectrum ("stating the rule is the minimum; a witnessed example is the stronger fix") without warning you the stronger option also destroys difficulty. Test cheaply (numeric diff, see §4 step 5) before trusting either blindly.
- **Don't panic-revert on the first "too easy."** Each of attempts 3–4 above only cost one pass@2 cycle (out of a 6/day budget) because each was reverted immediately once diagnosed, rather than compounding onto more wording changes on top of a broken base.

### 6.3.1 — Reading the automated "pass@2 difficulty suggestion"
After a too-easy pass@2, the pipeline posts an **advisory, non-blocking** "Pass@2 Difficulty Suggestion" comment diagnosing exactly which instruction clause telegraphed the fix, and what to remove. It is a real, independently-derived confirmation, worth reading before making your own guess — it correctly diagnosed attempt 3's problem before we'd finished analyzing it ourselves. It's rate-limited (2/day), so don't rely on it as your primary signal, but don't ignore it either.

### 6.4 — QC (Tier 2) found four real, non-cosmetic verifier bugs in one pass

QC is an *execution-based* adversarial prober, materially stricter than deep_review. On our first pass through it, it found:

1. **"Partial/Degenerate/Stub Output Accepted"** — our verifier only ever re-ran `solve.py` into scratch temp files and never checked the actual named artifact (`/app/output/regions_summary.csv`) the instruction told the agent to write. A submission that never produced that file (or produced an empty one) could still score reward 1.0.
   **Fix:** add a dedicated test asserting the real artifact path matches the reference, in addition to the scratch re-runs.

2. **"Ambiguous Rule, No Disambiguation"** — the wording-level finding described in §6.3 above (this was the same session that led to attempts 3–5).

3. **"Undocumented Requirement Enforced"** — our `ALLOWED_IMPORTS` stdlib whitelist was a small hand-picked subset (`sys, os, json, csv, math, ...`), narrower than what the instruction actually promised ("depend only on the Python standard library"). A legitimate solution using, say, `datetime` or `bisect` would have been wrongly rejected.
   **Fix:** build the allowlist from Python's own **authoritative** module list, `sys.stdlib_module_names` (3.10+), minus a small, *instruction-justified* denylist of networking/subprocess/dynamic-import modules (`socket, urllib, http, subprocess, importlib, ...` — justified because the instruction separately states "no network access"). Then state that denylist explicitly in the instruction too, closing the loop completely.

4. **"Reward/Harness Plumbing Exploit"** — the held-out ground-truth file (`tests/data/held_out_expected.csv`) lived in the **same directory** as the held-out input file the verifier fed to the agent's own script. Since the verifier executes the agent-writable `solve.py` directly against that path, a sufficiently adversarial submission could glob its own input's directory for a sibling "answer-looking" CSV and just copy it.
   **Fix:** before invoking `solve.py` on held-out data, copy the input file into a **fresh, isolated temp directory containing nothing else**, and pass *that* path as the argument. This is now a standing pattern — apply it to every held-out re-invocation, every time, regardless of whether the specific task seems to need it.

**Lesson:** local `harbor run --agent oracle/nop` only proves the verifier accepts the *correct* answer and rejects *doing nothing*. It says nothing about whether the verifier resists a **deliberately adversarial or degenerate** submission. QC exists specifically to catch that gap, and it will — build the anti-cheat patterns (isolated directories for held-out data, authoritative-not-hand-picked allowlists, checking the actually-named artifact) into the verifier from the start, rather than waiting to be told.

### 6.5 — Two false alarms worth recognizing early
Twice, `gh pr checks` showed a scary-looking `Oracle ❌` or a stale blocking-issue comment that turned out to be from a **cancelled, superseded run** (GitHub Actions cancels an in-progress run when a newer push arrives on the same branch/PR). Confirmed via `gh run view <run-id>` showing `"Canceling since a higher priority waiting request exists"`. **Always check whether a failing status is from the run matching your *latest* commit SHA before reacting to it** — sticky PR comments update in place, but `statusCheckRollup` entries can lag by a cycle if you push in quick succession.

### 6.6 — QC doesn't just probe adversarial submissions, it **mutates your own reference solution**
*(New finding, from the `rebuild-release-tarballs` task — not observed directly on this task, but the mechanism is generic and worth designing around from the start.)* QC's `qc_gate` job doesn't only construct degenerate/adversarial submissions (empty output, harness-exploit attempts — see §6.4). It also takes the *correct* reference solution, applies a small mutation to it (in that case: swapping the timestamp source from committer date `%ct` to author date `%at`), and re-scores the mutant against your verifier. If the mutant still scores reward 1.0, that's a blocking finding — it means your held-out coverage can't actually distinguish the correct behavior from a specific plausible-wrong one, even though your test suite "passes." On that task the fix was to make the sample *and* held-out fixtures' author/committer dates genuinely diverge, so the two readings could no longer coincidentally agree everywhere they were checked.

**Actionable pre-push check (add to your routine, not just after a QC failure tells you to):** for every deciding value or rule in your design, ask *"which small, one-token mutation of my own reference implementation would still score reward 1.0 against my current fixtures?"* If you can name one, that's a real coverage gap — QC will very likely find it before a human does. Fix it by making your sample and/or held-out data actually pin the distinction (e.g., ensure two fields that could plausibly be confused for each other actually hold *different* values somewhere the verifier checks), not by loosening or tightening tolerances.

### 6.7 — `README.md`: root-level is required, `task/README.md` should usually be omitted
Two related, easy-to-miss rules, confirmed across both tasks:
- The **repo-root** `README.md` (the scaffold one, outside `task/`) explicitly ends with an instruction to replace it with a real description once the task is done — this is a required step, not optional polish, and it's easy to forget because it has zero bearing on any automated check passing (it's for human reviewers). We did this for `fir-boundary-metrics`; it was *missed initially* on `rebuild-release-tarballs` and only caught when asked to verify.
- A **`task/README.md`** (inside the Harbor task directory itself) is optional and reviewed under the `task_readme` rubric criterion, which **FAILs it if it duplicates `instruction.md`, the solution, or `task.toml` metadata**, but scores a clean **N/A (pass) if simply absent**. Default to leaving it out entirely unless you have genuine, non-duplicative reviewer/maintainer context to add (design-decision notes, links to extra tooling) — the safe default is fewer files, not more.

### 6.8 — Every push re-rolls a stochastic result; batch changes
Confirmed sharply on `rebuild-release-tarballs`: after the task had already reached 0/5 pass@5 (fully stumped) across two clean runs, a **docs-only** push (replacing the root README, no code or task-file changes) re-ran the *entire* ~2-hour pipeline and re-rolled the trials — that run's pass@2 came back 1/2 solved, where the two prior runs had both been a clean 0/2. The gate still passed and pass@5 still landed at 0/5, but it's a direct, concrete illustration that **pass@2/pass@5 are stochastic per push, not deterministic given the same task files**, and the daily trial budget (pass@2 capped at 6/day) is not free to spend on changes that can't move the outcome. This is exactly why, on `fir-boundary-metrics`, a purely descriptive README update was deliberately left unpushed after the PR was already `accepted` — see §9 checklist item "batch non-functional changes" below.

---

## 7. Quick-reference: pipeline verdict → action

| Signal | Action |
|---|---|
| Static check fails | Fix mechanically (usually a one-line Dockerfile/toml/instruction issue); recalibrate; push |
| Rubric review flags a criterion | Read the specific criterion in `dynamo-rubric.toml`; fix precisely that, don't over-correct |
| pass@2: both solved | Task too easy — find and remove whatever made the crux salient (prose, witnessed sample, anything); never shorten the timeout |
| pass@2: both errored/timed out | Infra or task bug, not difficulty — check agent timeout is generous enough, check the verifier doesn't hang |
| pass@2: ≥1 genuine fail | Gate passed — proceed, but still read the per-trial `task_specification`/`approach_validity` columns for early ambiguity warnings even though the gate itself is green |
| deep_review/adversarial_review/QC blocking issue | Read the **exact** evidence text and file:line citation; these gates quote your actual files and often construct a real counter-example — trust the specifics over your own assumptions about what's wrong |
| pass@5: 3–5/5 solved | Too easy — raise real difficulty (never busywork, never a shorter timeout) |
| pass@5: 0/5, but flagged as invalid (timeout/infra/verifier error) | Broken, not hard — fix the actual cause |
| pass@5: ≥3/5 genuine fails, clean fairness flags | **Accepted** — done with the automated loop; human review (R1→R2) is next and out of your control |

---

## 8. Environment / process notes specific to this machine

- **Windows + Git Bash + Docker Desktop.** `harbor` and `git`/`gh` all work from Git Bash; Python for local scratch scripts needs the `py`/`python` launcher (bare `python3` isn't aliased). `/tmp` inside Git Bash is **not** the same filesystem the Windows `python` launcher sees — use the session scratchpad directory (`C:\Users\chara\AppData\Local\Temp\claude\...\scratchpad`) for any file handed between Bash and Python.
- **`git config core.autocrlf=true`** on this machine — working-tree files show CRLF locally, but `git show :<path>` on the staged blob confirms LF is what's actually committed. Don't "fix" this; it's already correct.
- **Console encoding**: printing emoji (from PR comment bodies, which contain e.g. 🤖/✅) to a Windows console can throw `UnicodeEncodeError` under the default `cp1252` codec. Write to a UTF-8 file and read it back with the `Read` tool instead of printing directly.
- **Fork workflow**: cloning directly from the base org repo does *not* make it a fork. Explicitly `gh repo fork <base> --clone=false` (or without `--clone` if already cloned), add the fork as a second remote (`git remote add fork <fork-url>`), push to `fork`, then `gh pr create --repo <base> --head <your-user>:<branch>`.
- **Autonomous monitoring loop**: a session-scoped `CronCreate` recurring job (e.g. every 15 minutes) works well for babysitting a PR pipeline across many hours without user interaction — but it's session-only (dies when the session ends, no persistence to disk) and auto-expires after 7 days. For anything that needs to survive a session close, that would need the durable `/schedule` cloud path instead.

---

## 9. Cross-task synthesis: architectural crux vs. atomic fact

*(New section — this reconciles a finding from `fir-boundary-metrics` §6.3 with a finding from the second case study, `rebuild-release-tarballs`, that at first looks contradictory but isn't.)*

On `fir-boundary-metrics`, **any** form of disclosure strong enough to satisfy the fairness reviewers — spelling out the fix's consequence in prose, or simply showing one witnessed antimeridian example in the visible sample — was enough to make the model apply the fix reliably and collapse the task to 2/2 solved. The only wording that survived was disclosing the *raw premise* (a coordinate's valid numeric range) while leaving its *implication* for the specific formula undisclosed.

On `rebuild-release-tarballs`, the opposite happened: the task team **deliberately added a witnessed sample repo demonstrating the exact disclosed mechanism** (`export-subst` placeholder expansion, shown in a sample project's published artifact) specifically in response to a QC finding that the mechanism was otherwise agent-invisible — and pass@5 was *still* 0/5 afterward. Disclosure did not soften that trap at all.

**Why both are true, and what it means for design choice:** the deciding factor isn't "was it disclosed," it's **how many independent held-out consequences the single crux has, and whether they take different shapes.**

- `fir-boundary-metrics`'s crux was a **single atomic fact** — one normalization rule, one kind of failure (a wrong number on any crossing polygon). Once the agent is confident the rule applies at all, applying it correctly is not hard, so any signal that makes the rule *salient* is equivalent to solving the whole task.
- `rebuild-release-tarballs`'s crux was an **architectural decision** (delegate export to `git archive` on the tagged commit rather than reimplementing a directory walk) that simultaneously fixes *six independent* categories of held-out divergence (tag resolution, untracked files, post-tag commits, nested `export-ignore`, `export-subst` expansion, file-mode/symlink fidelity) — each of which shows up in a *different shape* across the held-out fixtures. Witnessing one shape of one consequence (`export-subst` in one sample repo) still leaves every other shape, and every other consequence, undemonstrated. Generalizing correctly across all of them is still real, uncollapsed work, so the trap survives disclosure of the underlying mechanism.

**Practical implication for future task design:** where possible, **prefer an architectural/mechanism-level crux with multiple independent, differently-shaped held-out consequences over a single atomic fact.** It's structurally more robust to whatever disclosure level a fairness reviewer ends up requiring — you can often safely disclose the mechanism outright (or even witness one instance of it) without collapsing difficulty, sidestepping the delicate, budget-expensive tightrope-walk that a single-fact crux forces you into (see `fir-boundary-metrics` §6.3 — five separate pass@2 cycles to find the one wording that worked). If your crux really is closer to a single atomic fact, budget for that tightrope-walk explicitly: expect several disclosure-calibration iterations, test the *raw premise, not the consequence* wording first (§6.3's "sweet spot"), and treat each attempt as a cheap, fast experiment rather than something to get right on the first try.

---

## 10. The single-paragraph version, for future you

Read the doc set (spec, amplifiers, live examples, `stumping_guidelines.md`) before designing anything. Prefer, where the domain allows it, an **architectural/mechanism-level crux with several independent, differently-shaped held-out consequences** over a single atomic fact — it survives disclosure far more robustly (§9). Verify numerically (write the naive/plausible-wrong implementation yourself, confirm it passes 100% of your visible samples and fails held-out — if it fails samples too, the design is broken, not hard) before writing any task files, and enforce any anti-cheat constraint (stdlib-only, no network, generator-stage isolation) the trap actually depends on. Build the verifier's anti-cheat hardening from the start, not after QC finds the gap: isolated held-out directories, authoritative-not-hand-picked allowlists, check the real named artifact, and — critically — ask *which one-token mutation of my own reference solution would still score reward 1.0?* for every deciding value (§6.6), because QC will mutate your oracle and re-score it, not just probe adversarial submissions. Calibrate locally (oracle=1.0, nop<1.0) before every push, batch unrelated changes into one push (every push re-rolls the stochastic pass@2/pass@5 trials against a 6/day budget — §6.8), and replace the root `README.md` while leaving `task/README.md` out entirely unless it adds real non-duplicative context (§6.7). If a crux really is closer to a single atomic fact, disclose the *raw premise*, never the *consequence* — full disclosure of the fix's consequence reliably makes frontier models apply it correctly and kills the difficulty; disclosing only the underlying fact (a range, a definition, a convention) while leaving the implication to be derived is what threads the needle between "fair" and "hard." Trust the live pipeline's current feedback over locally cached docs when they conflict — the "no timeout-line" finding has now held on two separate repos. Stop iterating and flag for a human only when you hit a genuine dead end (Holding-Rejection after 2 revisions) — an "accepted" label on all automated gates is the actual finish line for autonomous iteration.
