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
- [dynamo-602128a emulate-int8-accel](dynamo-602128a-emulate-int8-accel.md) — Hardware/GPU kernels & accelerators (first in subcategory); int8 gemmlowp/TFLite requantization latent crux (positive shift = left shift; fused RELU clamps at output zero-point); accepted at pass@5 2/5
- [dynamo-0444752 repair-portal-dispatch](dynamo-0444752-repair-portal-dispatch.md) — Debugging and Repair / Configuration Repair (first in category); the tool's own silent defaults as the crux with every rule disclosed; graded by running real nginx; accepted at pass@5 0/5
- [dynamo-658c4fa replay-rulepack-scores](dynamo-658c4fa-replay-rulepack-scores.md) — ML/model inference; PMML missing-value semantics as the withheld crux; probing the real engine killed three axes before they cost a cycle; accepted on one commit at pass@5 0/5
- [dynamo-4807ee8 restore-runbook-advisor](dynamo-4807ee8-restore-runbook-advisor.md) — Data Querying and Databases / Database administration; SQL Server backup-chain semantics, `COPY_ONLY` inert on a differential as the withheld crux; the new off-GitHub pass@k harness and its five infra signatures; `qc_gate` B5 answered with data instead of prose; accepted at pass@5 1/5
- [dynamo-6edfe0d replay-deposit-ledger](dynamo-6edfe0d-replay-deposit-ledger.md) — Systems Infrastructure and Operations / Storage and filesystem administration; rebuilding a deposit gateway's ledger from an HFS Plus volume's journals; accepted on push 18
- [dynamo-6wgviv8 statement-rollup-repair](dynamo-6wgviv8-statement-rollup-repair.md) — Debugging and Repair / Performance Debugging; a pure-Python task died at pass@5 three times (0/5, 1/5, 0/5) because disclosed rules just get implemented; rebuilt around SQLite's own documented behaviour and accepted
- [dynamo-afed5c2 replay-run-histories](dynamo-afed5c2-replay-run-histories.md) — Model Training and ML Infrastructure / Training loops; a named public authority (TensorBoard's event-file reader) with only the occasion withheld; accepted at pass@5 0/5
- [dynamo-3779991 ledgergraph-canon](dynamo-3779991-ledgergraph-canon.md) — Data Querying and Databases / Graph and semantic queries; three full redesigns (path-query semantics, then SPARQL property paths, then RDF blank-node canonicalization/RDFC-1.0) before landing one obscure enough to survive `pass2`; refines the disclosure-vs-difficulty catch-22 memory (real ≠ obscure); accepted at pass@5 0/5
