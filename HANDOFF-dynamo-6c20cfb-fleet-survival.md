HANDOFF: dynamo-6c20cfb-data-science-and-reporting (PR #1)
==========================================================
Category / sub (fixed): Data Science and Reporting / Statistical analysis and inference
Local clone: /Users/gundadiprudwiraj/dev/handshake/dynamo-6c20cfb-data-science-and-reporting
Branch: submission. Pushed commit 3f9f9d4; four further commits held locally
(893b038, 5d1cd0d, 15215c2, 6cddea7) and never pushed.

STATUS: design 1 measured as TOO EASY. pass@2 = 2/2 solved, reward 1.0 both trials.

## Design 1 — replay-fleet-survival

Rebuild a retired fleet-reliability readout: product-limit (Kaplan-Meier) survival at
requested ages, Greenwood SE, median life, restricted mean life to a horizon, from an
archive of left-truncated / right-censored coverage spans. Five latent axes, all inert
in the shipped extract, ten single-edit mutants all caught, oracle 1.000 / nop 0.000.

Gates: changes, similarity, cosine_similarity, review, ratelimit, validation ALL PASS
on the first push. Only pass2 failed, and only on difficulty.

## Why it failed — the finding

Both agents recovered EVERY axis unaided:
  - delayed entry (units only at risk from entry_age_h)
  - the strict `entry < t <= exit` risk-set boundary
  - withdrawals at a failure age staying in the risk set
  - distinct unit_id vs row counting
  - median at S <= 0.5, flat tail to the horizon

The gate's own wording: *"convergence on bisect-based logic across two independent runs
suggests this is a well-represented algorithmic pattern in training data."* Both wrote
the bisect cumulative-count risk set — the same decomposition as tools/generate.py.

**Left-truncated Kaplan-Meier is inside this model's confident prior.** Add it to the
0cfa37b list of dead ends for this category: named statistical conventions (Tukey
hinges, modified z-score), disclosed procedural rules, DST/zoneinfo, and now
survival-analysis risk-set semantics. Real + external + conditional + sample-inert was
NOT sufficient here, because the convention is famous and fires the moment the schema
names an entry age.

**Every axis I built changes WHICH FORMULA OR BOUNDARY APPLIES.** lumenp's finding is
the one that matters: what finally worked there was a crux that changes WHAT DATA GETS
READ, not which formula applies. That distinction is the lever for design 2.

## Second finding: the shipped self-check actively helped

Trial task__7FooTTk wrote a stale-variable bug in restricted_mean, *detected it by
diffing against /app/data/expected.json at step 5*, diagnosed it by step 9, and fixed it
inside the same run. That is sweep-replay 5.1's diff-and-correct path, live. Removing
the graded extract's expected output moved sweep-replay 2/5 -> 0/5 with the crux
untouched. Ship the self-check for a NON-GRADED extract instead (merge-lora 4.1).

## What to try next, in order

1. Keep the machinery (generator with inertness invariants + machinery pins, sandboxed
   verifier, mutant battery). It is all clean and every non-difficulty gate passed
   first time. Only the crux family needs replacing.
2. Move the deciding rule to something that changes WHAT DATA GETS READ.
3. Drop /app/data/expected.json for the graded extract; ship a reference for a
   different, ungraded extract so the end-to-end self-check survives without the
   diff-and-correct path.
4. Do NOT respond by stacking more risk-set axes. motion-register 3(f): adding held-out
   coverage of an axis you already have does nothing; you need a second axis of a
   different KIND.

---

## Measurement log — four pass@2 rounds, three solved

| Commit | What changed on the agent-visible surface | pass@2 |
|---|---|---|
| `3f9f9d4` | 5 axes, all "which formula/boundary applies" | **2 solved** |
| `4cf7aaf` | + `spans_are_units` (risk set over units, not spans) | **0 solved, 2 valid-fail** |
| `633bf86` | **nothing** — held-out fixture, tools and docs only | **2 solved** |
| `7b3715b` | + `rows_are_events` (one failure, many collectors reporting) | **2 solved** |

### The finding that matters: 4cf7aaf vs 633bf86

`instruction.md` and `environment/` are **byte-identical** between those two commits
(verified with `git diff`). Same task, 0-solved then 2-solved. So the one green pass@2 in
this whole sequence was a ~50% coin flip, not evidence the axis worked. Do not read a
single pass@2 as a verdict on a single axis — `rebuild-readout-builder` §3.1 said this and
it reproduced here exactly.

### What is now measured as inside this model's prior

Everything expressible as **"which rows go into `n` or `d`"**:
delayed entry, the `entry < t <= exit` boundary, withdrawal ties, step side at a reported
age, risk sets over units rather than spans, and event counts over units rather than rows.
The last two were chosen specifically because no survival text discusses them as
data-quality cases — and the model still got them, because the *default* lands in the
right place regardless of whether a textbook names the case.

The pass@2 suggestion diagnosed this before I did:

> these axes are all *standard* Kaplan-Meier conventions, and `instruction.md` names the
> estimator ... A domain-knowledgeable agent recalls the correct default for each axis
> without needing to reason from the archive description.

**Rule to carry forward:** "no textbook discusses this case" is NOT the same as "the
textbook default is wrong here". Only the second one stumps. Ask of any candidate axis:
*what would a competent solver do by default, and is that answer wrong?* If the default is
right, the axis is free difficulty for the model, not for you.

### Two levers still untried on this task

1. **Stop naming the estimator.** The suggestion's own next-best lever: describe the
   required behaviour without "Kaplan-Meier" / "Greenwood", so the method has to be derived
   from the archive rather than pattern-matched from a label. Risk: ambiguity / `qc_gate`
   B5, since the arithmetic then has to be pinned by description alone.
2. **Remove the graded extract's answer.** `/app/data/expected.json` is still shipped for
   the graded extract. In round 1 a trial used it to catch and fix a real RMST bug mid-run.
   `sweep-replay` §5.1 measured removing it as worth 2/5 -> 0/5 with the crux untouched.
   Ship a reference for a separate ungraded extract instead (`merge-lora` §4.1).

### Honest status

Three of four pass@2 rounds solved. Every non-difficulty gate is green and the machinery is
sound, so the cost of another attempt is one pass@2 slot, not a rebuild. But if levers 1
and 2 also fail, this is the `dynamo-20141f7` shape: a subcategory where the model derives
the answer from any well-specified description, and the honest call is to say so rather
than keep spending slots.
