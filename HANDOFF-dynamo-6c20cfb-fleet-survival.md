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
