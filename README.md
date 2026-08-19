# previous_task_data

Accumulated playbook for Project Dynamo (Terminal-Bench 2) task-authoring work. Each markdown
file here is a case study of one finished (or dead-ended) Dynamo task: what was tried, what
failed, what worked, and why — including cross-category lessons like pipeline-gate mechanics,
QC's mutation testing, disclosure-calibration patterns, README rules, and push-budget discipline.

## How this repo is used

At the start of every new Dynamo task session, the working prompt instructs the agent to read
every file in this repo before designing anything — not just the file matching the new task's
category, since cross-category findings have so far transferred across categories.

When a task finishes (accepted, or a genuine dead end reached), a new case-study file is added
here, following the existing files' format:

- Problem statement
- Design reasoning
- Gate-by-gate iteration log (what failed, and the fix)
- Reusable checklist
- One-paragraph distilled summary

## Files

Each file is named after its task (`dynamo-<hash>-<category-slug>-case-study.md` or similar).
- [dynamo-42e4474 adjudicate-gridfall-runs](dynamo-42e4474-adjudicate-gridfall-runs.md) — puzzle-solving; y-up kick tables vs y-down arrays; accepted at pass@5 2/5
<<<<<<< HEAD
- [dynamo-602128a emulate-int8-accel](dynamo-602128a-emulate-int8-accel.md) — Hardware/GPU kernels & accelerators (first in subcategory); int8 gemmlowp/TFLite requantization latent crux (positive shift = left shift; fused RELU clamps at output zero-point); accepted at pass@5 2/5
=======
- [dynamo-658c4fa replay-rulepack-scores](dynamo-658c4fa-replay-rulepack-scores.md) — ML/model inference; PMML missing-value semantics as the withheld crux; probing the real engine killed three axes before they cost a cycle; accepted on one commit at pass@5 0/5
>>>>>>> 43bf515 (Add replay-rulepack-scores case study)
