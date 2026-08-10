# dynamo/sweep-replay — replaying an asynchronous HPO controller

**Repo:** `dynamo-2bb7b69-model-training-and-ml-infrastructure` · **PR #3** ·
**Category:** Model Training and ML Infrastructure / Hyperparameter tuning ·
**Outcome:** `accepted`, all checks green at `130a894` · **pass@5: 0/5** (avg@5 = 0.000, 5 of 5 good
valid failures) · pass@2 0/2

> Reached `accepted` twice. At `80f7f25` with pass@5 **2/5** while the worked example still shipped
> its expected outputs; that configuration later measured **0/2 solved-on-pass@2 → too easy** once an
> unrelated fix retired a second failure mode, because agents were diffing against the example and
> self-correcting. Removing the example's outputs took it to **0/5**. See §5.1 — it is the most
> transferable thing in this file.

---

## 1. The task

A hyperparameter sweep ran on a cluster under an asynchronous scheduler and the controller's
state store was lost. What survives is a *replay specification*: scheduler settings, the order
the search space handed over candidates, and a tabular benchmark giving each candidate's
objective at each rung resource plus its measured epoch time. The agent writes `/app/solve.py`
and reconstructs the run — a dispatch log (one row per job, in dispatch order) and a summary
(incumbent, job count, epochs consumed, makespan, per-rung occupancy).

Reaching any correct output line requires a discrete-event simulation of a multi-worker cluster:
rung ladder, checkpoint-resume epoch accounting, occupancy clock, promotion policy, terminating
condition. Nothing can be computed or checked a piece at a time.

## 2. The crux, and the invariants that make it work

Two properties of asynchronous successive halving decide the answer. The instruction specifies
the format, cost model, worker mechanics, output schemas and the tie-breaks it grades, and says
the promotion policy is the one belonging to the scheduler named in `scheduler.algorithm`. It
never restates that policy — that is the domain knowledge under test.

1. **Promotion is a property of the rung, not of the job that just landed.** The rung is
   re-ranked on every worker request, so a config passed over earlier becomes promotable once
   the rung grows underneath it.
2. **Rung members rank on their score at that rung**, not the best score the config recorded
   anywhere. Only visible once a curve turns and degrades with more training.

The invariants that carry it:

- **The visible data is homogeneous on exactly those two axes.** In the graded sweep, at every
  promotion the best unpromoted member happens to be the job that just finished, and every curve
  improves monotonically — so a misreading produces a plausible dispatch sequence rather than an
  obviously broken one, and nothing in the shipped input marks it wrong.
- **Nothing under `/app` lets the agent check itself.** The image ships the graded spec and a
  *second, different* sweep's spec — **inputs only, no expected output for either**. This is the
  form that survived. The earlier design shipped that second sweep's two output files as a worked
  self-check, on the theory that both misreadings reproduce it byte for byte (true of both local
  mutants). An agent whose misreading took a different shape diffed against it, saw the mismatch,
  and fixed itself — the design's one measured failure. See §5.1.
- **Cheaper errors are no longer caught for the agent.** `ceil` instead of `floor` on the promotion
  budget, counting in-flight jobs as rung members, drawing from the queue before promoting, acting
  only on exact multiples of eta — these all diverge on the example and were *deliberately* left
  catchable while its outputs shipped, to give the sample diagnostic value. Removing the outputs
  gave that up on purpose: the same trade that made the sample fair also made the crux survivable.

This is the `accrued-interest` shape (§34 live examples): name the standard in the data, specify
everything else, let the convention come from expertise. Confirmed again — a pure
logic/algorithm-correctness trap would not have survived.

## 3. Dead ends

**Median stopping rule as the crux — rejected before building.** The running-average comparison
in Ray's `MedianStoppingRule` is a genuinely surprising convention (Ray issue #5485 exists
because practitioners find it surprising). But Optuna's `MedianPruner` uses the *point value at
step t* under a near-identical name. Two real conventions, same name family, both defensible —
that is ambiguity, not a stump, and the sound-alternative test would have killed it at review.
ASHA's promotion variant has a single published definition (Li et al., Algorithm 1), which is
why it was chosen instead.

**Top-down vs bottom-up rung scan — measured unobservable, dropped.** Intended as a third crux.
With one worker freeing per completion, at most one rung is ever promotable at any request, so
scan order never changes the output. Verified over ~4,000 seeds across seven parameter
combinations: zero divergence. Worth knowing before writing a test that can never discriminate.

**A strictly monotone quality ordering in the sample.** The first sample seed that kept both
latent rules dormant had config quality descending in queue order — a visible artifact a
reviewer would flag as unrealistic. Searching `ordered=False` found seeds with the same dormancy
property and randomly-spread quality. Cost: one extra search, no design change.

## 4. What worked

1. **Answering the "too easy" verdict with a rebuild, not a patch.** The eval said the previous
   task's difficulty was "not fixable by editing metadata." It was right. Replacing a per-trial
   `min()` with a feedback-driven simulation moved `code_dependent` and `essential_difficulty`
   from FAIL to PASS in one push.
2. **Wrong-controller mutants run through the real verifier.** Six of them, each wrong in exactly
   one way, each run under `harbor`. This is what proved the sample validates and does not
   diagnose — and the pass@5 analysis then reproduced mutant A's failure almost exactly.
3. **A fixed LCG instead of `random` for fixture generation.** Local Python was 3.9, the image
   3.13. `random.shuffle`/`sample` are not guaranteed stable across versions; the verifier
   rebuilds fixtures at verify time and would have diverged. Eight lines of LCG removed a whole
   class of failure that no local test would have caught.
4. **Deriving every expectation at verify time**, plus a test that rebuilds the graded spec from
   its seed and asserts the on-disk file still matches — which is also the anti-tamper guard.

## 5. Gate-by-gate failure log

| # | Commit | Gate | Verdict | Cause | Fix |
|---|---|---|---|---|---|
| 1 | — | `review` | FAIL — `code_dependent`, `essential_difficulty`, `test_instruction_alignment` | Solution was a ~110-line parser whose only trap was two rules printed verbatim in the instruction; a tie-break was graded but never stated | Full rebuild (§1) |
| 2 | `f106481` | `review` | FAIL — `instruction_concision` (30/31 pass) | The `"You have N seconds…"` closing line | Deleted (§6) |
| 3 | `1cb9b0f` | `qc_gate` | BLOCK — `qc_exec` "Underdetermined / Hidden-Knowledge Mapping" | Rival incumbent reading (globally best metric, any rung) that no fixture could distinguish | Two hand-built witness fixtures (§6) |
| 4 | `80f7f25` | — | **all green, `accepted`** — pass@2 1/2, pass@5 **2/5**, avg@5 0.400 | — | — |
| 5 | `3e0765b` | `qc_gate` | BLOCK — `qc_exec` "non-unique named algorithm" | README-only push re-triggered everything and re-rolled QC. `asha` alone is genuinely ambiguous: Ray's `AsyncHyperBandScheduler` *stops* trials, Li et al. Algorithm 1 *promotes* them | Named the variant precisely (Li et al., Algorithm 1, the promotion form) |
| 6 | `0b437db` | `ava_review` | BLOCK — **fail-closed flake** | `routing=block confirmed_major=0 supported_major=0 potential_major=3 gaps=4 parse_failures=1`. Nothing substantiated, no `ava.json` artifact, and `deep_review` (same union gate) returned PASS with "Blocking Issues: None" | Re-triggered; passed next run. **Did not edit the task** (§6) |
| 7 | `0d3cbc5` | `qc_gate` | BLOCK — `qc_exec` "Ambiguous Rule, No Disambiguation" `[1/3 samples FAIL]` | **Genuine.** Completion sequencing fixed the *entry* order for same-instant completions but never said whether dispatch happens between two entries or after both. Corroborated: the `80f7f25` pass@5 had already lost a trial to an agent that batched | Stated the rule explicitly in `instruction.md` (`f858f17`) |
| 8 | `91cd96f` | `pass2` | FAIL — **0/2 valid failures, task too easy** | Fixing #7 retired one of three pass@5 failure modes, and the remaining crux was defeated by the worked example itself: an agent's first draft made the intended misreading, diffed against the example's shipped `dispatch_log.jsonl`/`sweep_result.json`, and self-corrected in ~27 min. See §5.1 | Removed the example's two output files (`eeaa63a`) |
| 9 | `eeaa63a` | `review` | FAIL — `verification_explanation_quality` | The fix removed the mechanism but `task.toml`'s `[metadata]` prose still described it ("the two files the controller wrote for it… a test replays that specification to confirm the shipped example is genuinely correct") | Corrected `difficulty_explanation` + `verification_explanation` (`130a894`) |
| 10 | `130a894` | — | **ALL GREEN, `accepted`** — pass@2 **0/2**, pass@5 **0/5**, avg@5 **0.000**, 5 of 5 good valid failures | — | — |

`validation`, `tier1`, `deep_review`, `qc_eval`, `similarity` and `cosine_similarity` passed first
time and never regressed. `ava_review` passed on the first attempt and every attempt but the one
fail-closed flake at #6 — notable given it blocked three consecutive pushes on `contact-export`; the
difference is that this task makes **no absolute claim** (no "stdlib only", no "no network"), so
there was nothing for a static screen to fail to keep.

### 5.1 The worked example was the difficulty, and it was load-bearing in both directions

The design's central bet was that the crux misreading (promotion checked only at completion, never
revisited) would replay the shipped worked example **byte for byte**, so the agent's own end-to-end
check comes back green while its replay of the graded sweep is wrong. Two mutants confirmed this
locally: both reproduced the example exactly while failing 7 and 5 of 8 held-out specs respectively.

That bet held at `80f7f25` (pass@5 2/5) and then failed at `91cd96f` (pass@2 0/2). The reason is
worth recording precisely: **the assumption was true of the mutants I wrote and false of the agent's
own implementation.** An agent's first draft embodied the misreading in a *different* shape than
either mutant, that shape did **not** reproduce the example, the diff surfaced it, and the agent
fixed it and went on to pass. Homogeneity of the example on the promotion-timing axis is not a
property of the axis — it is a property of each specific wrong implementation, and you cannot
enumerate those.

Removing the two output files fixed it decisively: pass@2 went 2/2-solved → 0/2-solved, and pass@5
went 2/5 → **0/5 with all five failures classified good-valid on the intended crux**. Both pass@2
trials made the *identical* misreading (capping total promotions at `floor(n/η)` rather than
re-checking the current top-N each request), producing 26 jobs against the reference's 33 — a 21%
structural shortfall, not a threshold near-miss.

The lesson generalises past this task: **a self-check oracle under `/app` is an iteration loop, and
a strong agent will use it to converge on correctness even when the spec alone would not get it
there.** Shipping a worked example of a *different* input (§4) removes the copy path and satisfies
`anti_cheat`, but it does **not** remove the diff-and-correct path. If the crux must survive the
agent's own verification, ship the example's *input* and no expected output — the agent still sees
the format, and there is nothing to converge against.

## 6. Error → what to do, and what not to do

| Symptom | Do | Do **not** |
|---|---|---|
| `instruction_concision` FAIL on the timeout line | Delete it. Confirmed for the **fifth** time. `00-ATTEMPTER-SPEC.md` §3, `CLAUDE.md` and eight other pages mandated it and claimed `check-instruction-suffix` enforced it; **both were false** — no static check requires it and the rubric calls it a TB3 artifact. All ten have since been corrected in place, so a future task should not hit this. `34-stump-the-model-live-examples.md` still contains the line inside quoted task transcripts; that is historical record, not guidance | ❌ re-add it from the cached docs. ❌ trust the local doc set over live pipeline output |
| QC "Underdetermined / Hidden-Knowledge Mapping" | Read the *evidence line*, not the headline. Ours said "the ONLY disclosed ground truth cannot distinguish them" — the prose was unambiguous, but **no fixture witnessed the rule**, so both readings produced identical output everywhere. Add a fixture that separates them | ❌ argue that the instruction already states it. It did, and arguing would have cost a cycle without fixing anything |
| Eval says difficulty "not fixable by editing metadata" | Believe it. Rebuild the problem shape | ❌ re-word `difficulty_explanation` and re-push |
| A rule you state has no fixture | Build one, hand-authored if random data can't produce it (exact ties, best-value-off-the-top-rung). Seeded floats never collide at 6 dp | ❌ assume a stated rule is pinned because the prose is clear |
| Tempted to grade a tie-break | Grade **only** advertised ones. Ranking within a rung is part of the undisclosed policy here, so no fixture may make a promotion turn on a ranking tie | ❌ add a within-rung tie fixture — that is grading an undisclosed convention, the top rejection cause |
| Expected outputs shipped for the graded input | Ship a *worked example of a different sweep* instead. Same self-check value, no copy path, and it satisfies `anti_cheat` literally | ❌ rely on "all tests must pass anyway" — the eval graded it PASS but flagged it as the most debatable point on the sheet |
| `pass2` FAIL "no valid agent failure", and you ship a worked example **with** expected outputs | Suspect the example first. Read the trial log for a diff-then-fix cycle: ours showed a wrong first draft corrected in ~27 min purely from the example diff. Remove the expected outputs, keep the input (§5.1) | ❌ conclude the crux itself is too easy and start designing a second mechanism. The crux was fine — it went 0/5 the moment the iteration loop was removed. ❌ assume "the misreading reproduces the example byte for byte" transfers from your mutants to the agent's implementation |
| A gate FAILs on prose after you changed a mechanism | Grep **`task.toml`'s `[metadata]` explanations** too — `difficulty_explanation`, `verification_explanation`, `solution_explanation` each restate the design independently of `instruction.md` and the README, and `verification_explanation_quality` is graded against the actual tests | ❌ assume fixing `instruction.md`, the tests and the README covers it. That exact miss cost a full cycle at `eeaa63a` |

## 7. Process rules learned or reconfirmed

- **Fix a debatable-but-passing criterion in the same push as a real failure.** `anti_cheat`
  passed with a note saying a human reviewer could flip it. Fixing it cost ~20 minutes alongside
  the mandatory `instruction_concision` fix; discovering it later would have cost a full cycle.
- **Never push while a run is in flight.** A README-only correction sat unpushed through two
  loop iterations rather than cancel a 1-hour `trials` job.
- **Audit the README against the task as it now stands, not as it was.** Two of three drift items
  were places where `task/` moved and the prose didn't — including a claim that the instruction
  "fully specifies every tie-break", which had become false and directly contradicted the design.
- Verifier timeout needed raising from 60 s to 600 s: the verifier now runs the graded program
  eight times.
- **A README-only push costs a full pipeline cycle and re-rolls every LLM-graded criterion.**
  `3e0765b` was documentation only and drew a fresh `qc_exec` BLOCK on prose that had passed at
  `80f7f25`. That block turned out to be a *genuine* finding (the algorithm name really was
  ambiguous), so the re-roll was not pure loss — but the cost is real and the lesson is to batch
  README corrections with the next substantive push whenever the README is not actually wrong.
- **The two mutants are a lower bound on agent behaviour, not a model of it.** Both mutants
  reproduced the worked example byte for byte, which is exactly what the design needed — and the
  live agent's differently-shaped version of the same misreading did not. Write mutants to prove a
  fixture *discriminates*; do not use them to prove a sample is *safe to ship* (§5.1).
- **`0/5` on pass@5 is the target, not an alarm.** The gate wants ≥1 good valid failure and ≥3 total;
  0 solved with 5 good-valid is the best available outcome, and the run still labels `accepted`.

## 8. Reusable checklist

- [ ] Difficulty lives in a **feedback-driven computation**, not a per-record loop — otherwise
      `code_dependent` fails.
- [ ] The crux is a **real-world convention with a single published definition**. If two
      libraries disagree under the same name, pick something else.
- [ ] Every stump candidate: measure whether it is even **observable** before writing a test.
- [ ] Sample/example is homogeneous on the crux axes.
- [ ] **Decide explicitly whether the agent gets any expected output at all.** Shipping a different
      input's outputs keeps cheaper errors catchable and the task fair — and hands a strong agent an
      iteration loop that can converge past your crux (§5.1). Inputs-only is what survived here.
      If you do ship outputs, do not assume your mutants' byte-for-byte agreement generalises.
- [ ] Fixture generation uses a **self-contained PRNG**, never `random`, if the verifier rebuilds.
- [ ] Every stated rule has a fixture; hand-author where random data can't reach it.
- [ ] Grade **only** advertised tie-breaks.
- [ ] No `"You have N seconds…"` line.
- [ ] Mutants run through the **real verifier**, not a local diff.
- [ ] After changing any mechanism, grep **`task.toml`'s `[metadata]` explanations** as well as
      `instruction.md`, the tests and the README — `verification_explanation_quality` is graded
      against the actual tests and caught exactly this drift.
- [ ] README re-audited against the current `task/` before every commit — run the full
      pre-push checklist in `readme-rule.md` (test-list diff, every number re-checked,
      difficulty section re-read against the instruction). Two of this task's three drift
      items were places where `task/` moved and the prose did not.
