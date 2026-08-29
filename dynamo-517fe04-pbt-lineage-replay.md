# dynamo/pbt-lineage-replay — the self-check-oracle trap, twice, and the fix that finally worked

**Repo:** `dynamo-517fe04-model-training-and-ml-infrastructure` · **PR #2** · branch `submission`,
fork `Pruthviraj374`. **Category:** Model Training and ML Infrastructure / Hyperparameter
tuning. **Outcome:** `accepted`, all 16 gates green at `310e78a`. **pass@5: 0/5 solved, 3 good
valid failures, avg@5 = 0.000** — best possible outcome. Final real `pass@2` before that: 2/2
solved (used only to reconfirm the fixed mutant, not a fresh difficulty measurement).

> **The one-sentence version, if you read nothing else:** withholding an arbitrary convention
> while shipping a worked example *with its own correct answer* as a self-check is a dead
> pattern in this corpus — confirmed twice now (`dynamo-2bb7b69-sweep-replay` and this task).
> A strong agent uses that answer key as a standing convergence loop regardless of which
> specific thing is hidden. The fix is not to disclose more or hide something different — it
> is to stop shipping a self-check with a real answer for the mechanism under test, or better,
> to restructure the task so grading happens on held-out cases the agent never sees at all
> (§4). Don't spend a cycle rediscovering this.

---

## 1. The task

A hyperparameter sweep used Population Based Training (Jaderberg et al., 2017): a population
of workers train independently and periodically checkpoint; at each of its own checkpoints a
worker's standing is compared against the rest of the population, and a poorly-performing
worker exploits (copies) a top-bracket worker's config and explores (perturbs it). The
scheduler's live state is gone; only the raw checkpoint log survives. Final shape: the agent
writes `/app/replay.py`, a **reusable** program invoked once per run
(`python3 replay.py <log> <config> <exploit_out> <final_out>`), reconstructing the
exploit/explore trace and final population state for whichever run it's pointed at.

That final shape was not the starting shape — see §3 for how it got there.

---

## 2. Dead end, confirmed twice now: withhold-a-convention-behind-an-answer-key-example

### 2.1 What was tried, in order, all on the same underlying design

The original design (inherited from the task's first submission, before this session) fully
disclosed the PBT algorithm in `instruction.md` and shipped a small worked
`/app/data/example/` **with its own correct `exploit_events.jsonl`/`final_population.json`**
— framed as "check your mechanics against a known-good run before trusting them on the real
one." Across one calendar day, five different levers were pulled on this same design, each a
real fix to a real problem, each still solved cleanly (pass@2 2/2, exact value match) the
moment the fixture was bug-free:

1. **RNG-timing convention withheld**, left derivable from the shipped example. Solved 2/2.
2. **Top-bracket indexing order withheld** instead (RNG-timing disclosed). Solved 2/2.
3. **An LCG-parity bug in the example itself** was found and fixed (`top_count=2` in the
   6-worker example made the odd-multiplier/odd-increment LCG's source-index draw a
   mathematical constant — `draw mod 2` is parity-locked, independent of data — so the
   worked example was a single frozen witness, not real evidence of the withheld
   convention). Raised to `top_count=3` with wider noise so the example exercised 11
   distinct top-bracket triples. Still solved 2/2 once fixed.
4. **A file-ordering trick** (archive the graded log in worker-major line order instead of
   `event_id` order, so a lazy top-to-bottom read is wrong) was added as an *additional*,
   independent axis. Still solved 2/2.
5. **A genuine QC-caught bug** (the graded fixture's `lr_bounds` never actually bound; a
   symlinked-parent-directory containment gap) was fixed. Still solved 2/2 once fixed.

Every one of these was a legitimate improvement to a real flaw. None of them changed the
outcome. **That repetition — fix a real bug, still solved cleanly, every time — is the tell.**

### 2.2 Why: the self-check *is* the problem, not the specific withheld fact

The diagnosis, reached only after the fifth repetition: shipping a worked example **with its
own correct answer** hands a capable agent a standing iteration loop. It doesn't just use the
example to *derive* the withheld convention once — it implements something, replays the
example, diffs its own output against the shipped answer, and iterates until the diff is
clean, *before ever touching the graded run*. That converges past whichever specific
convention is hidden, independent of which one it is. This is **exactly** the mechanism
documented in `dynamo-2bb7b69-sweep-replay.md` §5.1: that task's worked example (of a
*different* sweep, not even the graded-shaped one) still gave an agent enough of a diff-and-
correct loop that its first-draft misreading, differently shaped than either hand-written
mutant, got caught and fixed via the shipped answer — removing the example's two output
files (keeping the input only) took that task from pass@2 2/2-solved to 0/2, **with no
change to the underlying crux at all**.

**This is now confirmed on two separate tasks in this exact category.** Read this section
before designing any task in Model Training and ML Infrastructure that plans to ship a
worked example with a correct answer next to a withheld convention. It will not survive
pass@2 no matter which convention you hide, how many times you re-derive it, or how solid
your proof-of-derivability machinery is. **Do not retry this lever.**

### 2.3 The fix that was tried next, and why it *alone* was not sufficient either

Fully disclosing the algorithm (including the previously-withheld top-bracket order) and
**dropping the example's expected-output files** (ship log/config only, no answer to
converge against) was the next move, per the sweep-replay precedent. This closed the
self-check-oracle loop — but a real pass@2 run against that exact configuration **still
solved it cleanly (2/2, exact match)**. The underlying deterministic-replay algorithm was
simply never hard enough on its own; the self-check oracle had been *a* problem, not *the*
problem, in this specific task's case. (Contrast with sweep-replay, whose crux — a genuinely
subtle promotion-timing rule from a named published algorithm — was already hard; removing
its self-check oracle was sufficient there because the difficulty underneath it was real.
Ours needed an actual harder mechanism too.)

**Lesson for next time:** removing the self-check oracle is necessary whenever one is
present with a real answer, but confirm — don't assume — that it's *sufficient*. If the task
was already borderline-easy with the oracle in place, removing it alone may not clear the
bar either.

---

## 3. The next crux, and why disclosure wording alone didn't fix it either

A worker crash-restart mechanism was added: if a worker's own checkpoint `step` regresses,
its `learning_rate` must roll back to what it was as of the earlier local checkpoint it
resumed from, discarding intervening exploits. Two wordings were tried on the **same single
graded run** design (one graded input, static computed output — the original architecture):

1. **Stated as literal step-by-step pseudocode** ("reset that worker's learning_rate to
   whatever it was immediately after that worker's own most recent earlier checkpoint whose
   step is ≤ this event's step..."). Solved 2/2 — the agent just transcribed the given
   procedure verbatim.
2. **Restated semantically** ("the worker's state reflects the earlier point in its own
   local history it resumed from, not whatever this replay computed since"), so the solver
   would have to derive the mechanism rather than copy it. **Still solved 2/2.** The
   platform's own pass@2 difficulty-suggestion diagnosed why precisely: with the restart
   living in the *one graded run the agent can see*, a worker's own step sequence
   regressing exactly once, in an otherwise-clean log, is trivially surfaced by the most
   basic sanity check (confirm each worker's own step values are monotonic) that any
   competent implementer runs as a matter of course before trusting a parser. Both trial
   trajectories found it via a one-line check within minutes. Once found, correctly
   implementing a moderately-described rollback was not, by itself, hard enough — wording
   (procedural vs. semantic) didn't matter once the anomaly was this easy to locate.

**Lesson:** disclosure *phrasing* (spelled-out vs. semantic) is a much weaker lever than
where the crux physically lives. A single decisive anomaly sitting in the one input file the
agent can freely inspect is findable by inspection alone, regardless of how the rule
governing it is worded.

---

## 4. What actually worked: reusable code, graded on held-out runs it never sees

Consulted this category's own accepted precedents before guessing further —
`dynamo-411fd55-replay-rungear-runs.md` and `dynamo-aed170e-checkpoint-resume-plan.md`, both
this same category, both reached pass@5 0/5 (best outcome). Both share a structural pattern
neither this task nor sweep-replay had used: **the agent submits a reusable program, not a
one-off computed output, and the verifier re-invokes that program against several held-out
fixtures generated at build time and never shown during development.** A visible sample
still ships with its own correct answer as a self-check — but it's deliberately engineered
to be *inert* with respect to the crux, so validating against it gives no signal the
mechanism exists at all.

Restructured accordingly:
- Agent writes `/app/replay.py`, invoked as
  `python3 replay.py <log_path> <config_path> <exploit_out> <final_out>` — CLI-args-based,
  never a fixed path, because it's re-run once per graded case.
- `/app/data/sample/` ships a small run with its own correct expected output — **built
  restart-free by construction**, confirmed directly (replaying it with and without restart
  handling produces byte-identical output), not merely assumed.
- Grading happens on 11 held-out runs (`tests/reference_lib.py`'s `HELDOUT_RUNS`), generated
  fresh in-process at verify time and never written anywhere the agent's program or its own
  development session can read them. Each run's restart parameters (which worker, which of
  its own checkpoints, how far back it resumes to) were chosen by **exhaustively sweeping
  every combination** for that run and keeping the one whose divergence from a
  no-restart-handling replay is largest — not hand-picked to merely exist, but measured
  load-bearing (a direct application of the "mutants prove a fixture discriminates, not that
  a sample is safe to ship" lesson from sweep-replay §7).
- Grading is all-or-nothing across the sample plus all 11 held-out runs (`test.sh`'s
  existing pytest-exit-code aggregation needed no change).

This is what finally produced genuine pass@2 crux engagement (see §6).

### 4.1 A real anti-cheat gap this restructure introduced, and the fix

`ava_review` (`verifier_coverage`, BLOCK): `tests/` is overlaid onto the container at verify
time, so `tests/reference_lib.py` — which contains the correct `replay_correct()` — sits on
disk at `/tests/reference_lib.py` **exactly when `/app/replay.py`'s subprocess runs**. A
submission could `sys.path.insert(0, "/tests"); import reference_lib` and delegate to the
oracle instead of implementing anything; the verifier had no guard against that read/import
path. This is a new variant of the same family covered in `dynamo-411fd55-replay-rungear-
runs.md` §3.1 ("a guard that enumerates forbidden APIs is always one API behind... stage the
inputs so the answer is not on the path at all").

**Fix that worked:** `test_outputs.py` already has `reference_lib`'s functions cached in
memory from its own module-level `import reference_lib as ref` (pytest imports the whole
module before running any test function). Deleting the source file — and its compiled
`__pycache__` entry — from disk immediately after that import, before any `replay.py`
invocation, closes the import path for any *new* subprocess without affecting the verifier
process itself (which already holds live references to everything it needs). Verified with
an adversarial mutant that does exactly the exploit: it now fails on every run (empty
fallback output on `ImportError`) rather than silently passing via delegation.

**Do not** try to solve this by chmod/permissions tricks or a seal-list of forbidden paths —
per the rungear precedent, that's the pattern that costs a cycle per newly-discovered path.
Removing the file from disk once, right after your own last legitimate use of it, is a
smaller, more complete fix.

---

## 5. The final tipping point: reinforce the proven mechanism, don't invent a new one

First real `pass@5` on the restructured design: **3/5 solved** — one trial short of the
`≥3/5 failing` acceptance bar. Both failures were on the intended crux, not noise:

- **task__TRcth6k** — architectural bug: stored `(step → lr)` in a flat dict keyed by step
  value, never invalidated entries with a step *higher* than the crash's resume-to point.
  Failed **all 8** held-out runs at the time.
- **task__Eavg2oa** — a one-character boundary bug: used `h['step'] < step` where the
  correct filter is `h['step'] <= step`. Failed only **1 of 8** held-out runs, because most
  of the existing runs regressed *several* checkpoints back, so the exact same-step boundary
  was rarely the deciding value — a genuine near-miss (`near_miss: FAIL` on that trial,
  correctly flagged as "the right kind of near-miss for a well-designed task," per the
  rubric's own note, not a sign of an artificial threshold).

Per `dynamo-5727fd9-replay-rollout-gae.md` §4 ("reinforce a proven-hard mechanism with a new
stress *shape*, not a new mechanism, once pass@5 shows exactly which one is catching
agents"): rather than inventing a third crux, **3 more held-out runs were added
(`heldout-8/-9/-10`), each regressing to the *immediately preceding* own checkpoint**, so the
rollback candidate sits exactly at the crash's own step every time — maximizing exposure of
the `<=` vs `<` boundary specifically. Verified directly against a reconstructed
strictly-less-than mutant, run through the real verifier via `harbor`: it now fails **4 of
11** held-out runs (previously 1 of 8).

Next `pass@5`: **0/5 solved, 3 good valid failures, avg@5 = 0.000.** Accepted at `310e78a`.

**Lesson, reconfirmed a fifth time in this corpus (see rollout-gae, rungear-runs and others):
when pass@5 identifies exactly which mechanism is catching agents, broaden coverage of that
mechanism's edge cases before reaching for a new one.** A near-miss on a specific boundary
condition is a signal to build more fixtures that land exactly on that boundary, not a signal
that the crux itself is wrong.

---

## 6. Gate-by-gate log (the restructured design only; §2–3's dead ends never reached pass@5)

| # | Commit | Gate | Verdict | Cause | Fix |
|---|---|---|---|---|---|
| 1 | `1db60b9` | `pass2` | FAIL — 2/2 solved | Fully-disclosed algorithm + no self-check oracle, still too easy on its own (§2.3) | — |
| 2 | `26351a3`→`0af9cfe` | `pass2` | FAIL — 2/2 solved (twice, both wordings) | Restart crux in the one visible graded run, trivially found by a monotonicity check (§3) | Restructure to reusable code + held-out runs (`9c02637`) |
| 3 | `9c02637` | `ava_review` | BLOCK — `verifier_coverage` | `tests/reference_lib.py` importable by the agent's subprocess at verify time (§4.1) | Delete the file from disk after the verifier's own import (`e77e587`) |
| 4 | `e77e587` | `pass2` → `ava_review` → `deep_review` → `qc_gate`/`qc_eval`/`qc_exec` → `tier1` → `trials` | All passed in sequence | — | — |
| 5 | `e77e587` | `trials` (pass@5) | BLOCK — 3/5 solved, one trial short | Rollback-boundary edge case (`<=` vs `<`) under-covered (1 of 8 held-out runs) (§5) | Add 3 boundary-targeted held-out runs (`310e78a`) |
| 6 | `310e78a` | — | **ALL GREEN, `accepted`** — pass@5 **0/5**, avg@5 **0.000**, 3 good valid failures | — | — |

`changes`, `similarity`, `cosine_similarity`, `validation`, `ratelimit`, `review` (after two
early prose-only fixes — see §7) passed on every run once the underlying design was fixed and
never regressed.

---

## 7. Smaller repeat lessons, reconfirmed here

- **Never cite pass rates or model results in `task.toml`'s `difficulty_explanation`.**
  `review`'s `difficulty_explanation_quality` criterion explicitly forbids it ("these change;
  the difficulty does not"). Hit this **twice** in this task's history (`f96177a` and
  `e4dbaee`) — write the intrinsic reasoning only, describe mechanisms and their design
  rationale, never "solved cleanly at 2/2" or "took pass@5 from X to Y."
- **Re-verify every previously-passing gate locally before pushing a fix for a failing
  one.** Every mutant (no-restart-handling, round-grouping, no-`event_id`-sort, wrong-RNG-
  timing, descending/ranking-order top-bracket, unclamped LR, strict-less-than rollback) was
  re-run against `reference_lib.replay_correct` — and the decisive ones additionally through
  the real verifier via `harbor` — after every design change, not just once at the end.
- **A `jobs/` directory of local `harbor` run artifacts got committed by accident** partway
  through (forgot to `rm -rf jobs` before `git add -A`). Caught and removed in a later
  commit. Run `git status --short` before every `git add -A` and check for anything that
  isn't source.
- **`gh pr checks` polling**: don't tight-loop under ~15–20s; GitHub Actions' own bot token
  (not the contributor's) can hit its own rate limit mid-CI-run independently, which shows
  up as a scary-looking "rate limit exceeded" string inside a Tier-1 comment — that's the
  platform's bot, not a block on the contributor's own `gh` calls. Check `gh api rate_limit`
  on your own token before assuming you're blocked.

---

## 8. Reusable checklist for the next task in this category

- [ ] **Never ship a worked example with a correct answer next to a withheld, arbitrary
      (not-real-world-published) convention.** Confirmed dead twice (sweep-replay, this
      task). If a convention truly needs an answer key to be derivable, that's itself a sign
      to pick a different crux — one grounded in real, named domain knowledge instead (an
      arbitrary house convention has no fair way to be pinned without an answer key, and an
      answer key is exactly the thing that lets an agent converge past it).
- [ ] Removing a self-check oracle is *necessary* whenever one ships a real answer, but
      **confirm, don't assume, it's *sufficient*** — run a real pass@2 after removing it
      before concluding the crux itself is fine.
- [ ] If the deciding anomaly can live in a single visible input file, ask whether a basic
      sanity check (monotonicity, uniqueness, row-count parity, whatever the natural
      invariant is) would surface it immediately. If yes, it's not hidden, it's just findable
      — move it out of the agent's view entirely rather than relying on prose to obscure it.
- [ ] For "replay a decommissioned system's log" tasks specifically: prefer the reusable-
      code-plus-held-out-fixtures architecture (`/app/<program>.py` invoked once per case,
      several fixtures generated at build time and never shown) over a single static graded
      input with a computed output. This is now the pattern behind every accepted task with
      this shape in the category (`sweep-replay`* , `replay-rungear-runs`,
      `checkpoint-resume-plan`, this task) — *sweep-replay's own final form used input-only
      disclosure rather than held-out re-invocation, but the underlying principle (no answer
      key to converge against) is the same.
- [ ] If you ship reusable code the verifier re-invokes: check whether your own reference
      solution/ground-truth module is reachable from the agent-submitted program's runtime
      environment (e.g. `tests/` overlaid at verify time). If it contains the correct
      algorithm, delete it from disk right after your own last legitimate use, before
      invoking the agent's code.
- [ ] When `pass@5` returns a near-miss short of the bar (e.g. 3/5 solved, need ≥3/5
      failing) with a **specific identified root cause**, add more fixtures targeting that
      exact edge case before inventing a new mechanism. This worked here and in
      `dynamo-5727fd9-replay-rollout-gae`.
- [ ] Grep `task.toml`'s `[metadata]` explanations for pass-rate/model-result language before
      every push, not just `instruction.md`/README — `difficulty_explanation_quality` is
      graded against them independently and has failed on this exact mistake twice in this
      task's own history.
