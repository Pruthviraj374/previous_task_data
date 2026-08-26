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
- [dynamo-04fda1d read-cavity-captures](dynamo-04fda1d-read-cavity-captures.md) — Machine Learning
  and AI / Computer vision (first in category); a retired inspection cell's colour reader, with
  four DNG 1.4.0.0 rules the shipped captures all leave inert; **three candidate cruxes died on
  effect size, not on realism or latency**; `qc_gate` C3 answered once by covering the whole
  geometry family and once by *deleting* an untested branch; a verifier that scored 1.000 for a
  submission that computed nothing; accepted at pass@5 0/5
- [dynamo-1286b70 depot-batch-claims](dynamo-1286b70-depot-batch-claims.md) — Debugging and Repair /
  Concurrency and synchronization debugging; **a rule your spec yields is not a stump** — the model
  read a precise spec and derived the cruxes 2/2, and only platform defaults (umask, `-15` vs shell
  status, an orphaned helper holding a pipe) held; accepted at pass@5 0/5
- [dynamo-20141f7 sdf-registration-qc](dynamo-20141f7-scientific-computing-and-domain-science.md) — Scientific Computing and Domain Science / Chemistry and materials workflows (first in subcategory); **an accidental controlled experiment**: three designs whose cruxes were mathematically DERIVABLE from disclosed definitions (triclinic PBC geometry, symmetry-orbit dedup, metric-tensor ADP conversion) were solved 2/2 four times running, then a fourth using ARBITRARY MDL/CTfile V2000 encoding conventions (charge *code* table, `M CHG` supersession) gave pass@2 0/2 and was accepted at pass@5 1/5; establishes **derivability, not obscurity, as the filter** — an agent that couldn't derive the code table invented a shifted one; qc_gate clean first try
- [dynamo-bb1a7f2 luxproof-group-render](dynamo-bb1a7f2-luxproof-group-render.md) — Games Puzzles and Interactive Simulation / Rendering graphics; a Pattern-D crux that's the only sensible way to extend an already-disclosed formula gets solved by analogy regardless of disclosure tuning (group-alpha-once, group-combine both fell 2/2 across five pass@2 rounds); the fix was a crux that changes what data gets read (GROUP KNOCKOUT, a real named PDF/Illustrator convention) rather than which formula applies; pass@5 landed at a stochastic 3/5 boundary twice for two different failure families before accepting at 1/5; AVA sample-output copy-bypass fix
- [dynamo-24cd443 keepcase-restore](dynamo-24cd443-keepcase-restore.md) — File and Media Operations /
  File permissions and metadata; successor to `restore-stillwater-volumes` and proof that shape has
  aged: **a crux *family* can be saturated** — special bits, hardlink/symlink semantics,
  directory-mode deferral and chmod-follows-symlink were each applied *correctly* by the model, so
  four consecutive designs died 2/2 and three pushes were wasted strengthening a family it had
  already mastered; the escape was an adjacent family in the same subcategory (extended attributes,
  where a `user.*` xattr needs write permission the recorded `0o444` removes, so xattrs must precede
  the chmod) chosen specifically because the `try/except` reflex that had rescued the two previous
  attempts still fails there; also **a crux built from a web summary of `os.link(follow_symlinks=True)`
  was false on Linux** and was caught only because its own mutant scored 1.0 — verify OS behaviour in
  the target image, never from docs; final AVA block fixed by making the verifier stricter rather than
  the instruction looser, because pass@2 had just started passing and every push re-rolls it; accepted
  at pass@5 2/5
- [dynamo-c086412 replay-flash-capture](dynamo-c086412-replay-flash-capture.md) — Hardware, Embedded,
  and Low-Level Systems / **Embedded and firmware** (first in subcategory); emulating a **real** 25-series
  SPI NOR part is the escape from `decode-vibration-log`'s "a fictional decode format has no fair-and-hidden
  middle" — five real device behaviours the shipped programming session makes inert; the single `qc_gate` A6
  (page-buffer semantics on a >256-byte program) was a genuine reference bug whose correct fix **became the
  fifth axis** and took down a trial that had solved everything else — the first gate-driven axis in this
  corpus to actually gate; axis ranking measured wrong three times on one design; accepted in two pushes at
  pass@5 0/5, avg@5 0.000, rubric 31/31 both pushes
- [dynamo-6c20cfb replay-fleet-survival](dynamo-6c20cfb-replay-fleet-survival.md) — Data Science
  and Reporting / **Statistical analysis and inference** (first in subcategory); **the crux must
  not live in the statistics** — four consecutive pass@2 rounds measured this model recovering
  every survival-analysis convention unaided, including two axes chosen precisely because no
  textbook discusses them, because the textbook *default* is correct either way; the filter is
  **default-right vs default-wrong**, not obscure vs known. Accepted only once the extract became
  a real **dBase III+ table** whose format rules (deleted records keep their bytes and only flip a
  status byte; the header's record count is authoritative over trailing slack) decide which
  records exist at all, with the named estimator left as breadth the model handles correctly.
  Also records a **byte-identical agent surface returning 0-solved then 2-solved**, and three of
  six pushes lost to avoidable rubric defects rather than difficulty; accepted at pass@5 1/5
- [dynamo-03da6c3 collate-modpool-batches](dynamo-03da6c3-collate-modpool-batches.md) —
  Mathematics and Formal Reasoning / **Number theory and exact arithmetic** (first in this
  category); accepted in **two pushes** by applying the derivability rule *prospectively* —
  the CRT and rational-reconstruction maths is stated in full and 5/5 trials got it right,
  while the crux sits in the archives being **Erlang external terms** whose encoding changes
  with a value's width and contents. Establishes that **needing a spec is not reading a
  spec**: agents stop reading once the shipped sample parses, so big public binary formats
  are a renewable crux source. Records the sixth inverted axis ranking — and the first
  caused by the author's **own mutant battery**, because a harmless variant scored 1.0 and
  the *branch-missing* mutant was never built. `qc_gate` clean first try; the only defect in
  push 1 was the `You have N seconds…` line, a rubric FAIL that `00-ATTEMPTER-SPEC.md` still
  claims is mandatory; accepted at pass@5 2/5
