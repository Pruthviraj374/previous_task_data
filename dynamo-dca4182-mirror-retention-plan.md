# dynamo/mirror-retention-plan — build log, gate failures, and what finally worked

Repo: `dynamo-dca4182-build-dependency-and-release-management`, PR #1, branch `submission`.
Category: **Build Dependency and Release Management** / Sub-category: **Release Artifacts**.
Benchmarked against Opus-4.8 via Terminus-2. Accepted 2026-08-05 at commit `a0b5110`.

**Final result: pass@5 = 0/5 solved, avg@5 = 0.000, all five graded good valid failures.**
All 16 checks green, 1 skipped by design. Seven consecutive pass@2 runs came back 0/2.

This is the second Release Artifacts task in the playbook. Read it alongside
`dynamo-3419465-rebuild-release-tarballs.md` — the two cruxes are different in kind
(architectural delegation there, per-ecosystem convention here), but the gate behaviour
rhymes almost exactly.

---

## 1. The task

An internal package mirror stores release artifacts from three ecosystems side by side.
The agent writes `/app/solve.py`, invoked as
`python3 /app/solve.py <registry_csv> <channels_csv> <plan_csv>`, which emits a
garbage-collection plan: `artifact_id,rank,action`, one row per registry row in registry
order. `rank` orders each `(ecosystem, package)` group newest-first; `action` is `keep`
for rank ≤ 3 or anything a channel pins, `purge` otherwise.

- **Agent sees:** `/app/data/registry.csv` (36 rows), `/app/data/channels.csv`, and
  `/app/data/expected_plan.csv` — the correct plan for the shipped data, as a self-check.
- **Graded on:** eight held-out inventories (51 rows, 11 packages each) generated at
  verify time, plus the shipped one.
- **Constraint:** single self-contained file, standard library only, no external programs.

---

## 2. The design reasoning

### 2.1 The shape that works: heterogeneous key field + per-value published convention

This is the `accrued-interest` shape from `34-stump-the-model-live-examples.md`, mapped
onto release artifacts. That task had a `market` column (UST/UKT/DBR) where each value
implied a different published day-count convention, and the sample was all-US. Here the
`ecosystem` column (npm/pypi/deb) implies SemVer 2.0.0 / PEP 440 / Debian Policy 5.6.12,
and the shipped inventory is homogeneous exactly where the three specs diverge.

Why this shape survives review where an invented convention does not: the deciding rule is
**a real, published, field-standard convention tied to a visible data field.** The rubric
explicitly permits requiring field-standard conventions without restating them. The
previous repo's task died on `decisive_answer_discoverable` because its convention was
author-chosen; this one never came close to that failure.

### 2.2 Naming the dimension, never the rule

`instruction.md` says versions are ordered by "the version precedence rules of their own
ecosystem — each of the three ecosystems defines its own and they do not agree with each
other." It never names SemVer, PEP 440, Debian Policy, tilde, epoch, post-release, or
trailing zeros. A competent release engineer maps ecosystem → spec instantly; the model
must too, and then implement all three correctly.

### 2.3 Calibrating the trap before writing anything else

Before the first push I wrote three plausible first-draft comparators and ran them against
both datasets. Two scored **0 diffs on the shipped sample and 12–14 on held-out**. That
separation is the whole task, and measuring it took ten minutes. (Playbook rule from the
previous case study, applied and confirmed again.)

---

## 3. Issues faced, and the fixes

### Issue 1 — Dockerfile static check trips on a *comment*

`Dockerfile does not COPY solution/ or tests/` failed because a comment read "so
`tests/test.sh` installs nothing at verify time." The check greps for the substring; there
was no `COPY`. **Fix:** never write the words `tests/` or `solution/` anywhere in the
Dockerfile, comments included.

### Issue 2 — the instruction-suffix trap, again

Rubric FAILed `instruction_concision` on the `"You have N seconds…"` line, exactly as the
previous case study warned. This repo's static checks contain no `check-instruction-suffix`
— all 24 are listed and it is not among them. **Fix:** omit the line entirely. Confirmed
twice now across two repos; treat the older docs as wrong on this point.

### Issue 3 — QC mutation-tests your reference, so mutation-test it yourself first

QC (`qc_gate`, 44 checks + probes, **blocking**) repeatedly found rules my graded data did
not pin, by mutating the reference and re-scoring:

| QC found | Why my data missed it |
|---|---|
| tie-break `pa-pb` → `pb-pa` | no equal-precedence pair existed anywhere |
| SemVer numeric-vs-alphanumeric identifier rank | every pre-release started with `beta`, never a bare numeric identifier |
| bare `.devN` branch | I had dev-*of-post* but no bare `X.Y.Z.devN` |

Running the same harness myself found seven more survivors in one pass (deb
letter-vs-punctuation ordering, last-hyphen revision split, PEP 440 trailing zeros,
dev-of-post, epoch, local versions, SemVer build metadata).

**Rule: before every push, enumerate one-token mutations of your reference and confirm each
changes a graded plan.** Final count: 19 mutants, all caught. Two of the rules QC forced me
to pin — deb character classes and the implicit `-N` post-release — are exactly what killed
agents in later trials. Mutation coverage *is* difficulty coverage.

### Issue 4 — the answer-key escalation (three rounds)

The adversarial cheat-pass found, in successive rounds:

1. **Committed answer key.** `tests/data/heldout_expected.csv` in a public fork is a lookup
   table. → Moved to generating inventories at verify time from `tests/heldout.py`, graded
   against `tests/reference.py` (a copy of `solution/solve.py`).
2. **Fixed seeds are precomputable.** Anyone holding `heldout.py` can regenerate every
   graded row offline. → Switched to `secrets.randbits(64)`.
3. **…which QC then blocked** (see Issue 5).

Randomising also exposed two coverage gaps that fixed seeds had masked (a rule pinned only
by the committed *sample*, and an identifier pair that agreed lexically and numerically
~8% of the time). Worth running a randomised sweep even if you ship deterministic.

### Issue 5 — two gates in direct contradiction

- **Adversarial (advisory):** "Do not seed the held-out generator from committed constants."
- **QC (blocking):** "Seed every graded generation / solution / verification path with a
  fixed constant."

These cannot both be satisfied. **Resolution: the blocking gate wins, and the rubric's
`deterministic_reproducible` criterion agrees with it.** Back to fixed seeds — eight of
them — with the trade-off written into `heldout.py` and `verification_explanation` so human
reviewers see a considered decision rather than a regression. Adversarial still FAILs on
this and the task was accepted anyway.

**Generalisable:** when gates conflict, rank them blocking > advisory, cite the rubric
criterion that breaks the tie, and *document the loser in the artifact itself*.

### Issue 6 — do not state a constraint you cannot enforce

AVA BLOCKed because `instruction.md` forbade network use while nothing enforced it
(`RLIMIT_NPROC` stops processes, not sockets). **Fix: delete the clause.** Keeping only
enforceable constraints — stdlib-only, no external programs — cleared it immediately. The
mirror-image failure (enforcing something unstated) had already been flagged on the
previous repo. Both directions are graded.

### Issue 7 — static scans lose the arms race; use the kernel

AVA broke my `getattr`-based spawn scan with `getattr(os, "sys" + "tem")`. Patching the
pattern would just invite the next spelling. **Fix:** enforce at run time —
`preexec_fn` does setgid/setgroups/setuid to `nobody`, *then* lowers
`RLIMIT_NPROC` to `(1, 1)`. Every fork/spawn/exec then fails with `EAGAIN` regardless of
spelling. Verified inside the image: `subprocess.run` → `BlockingIOError`, `os.fork()` →
`BlockingIOError`, `getattr(os,"sys"+"tem")(...)` → status 127, shell never ran.

**Order is load-bearing:** `setuid()` itself fails with EAGAIN if the target user is already
at the limit, so the uid change must happen while the limit is still unset.

For imports (which the kernel cannot police) keep a static check, but flag the *call name*
(`__import__`, `import_module`, `CDLL`) rather than its argument — then
`__import__('sub'+'process')` is caught anyway.

### Issue 8 — convert assumptions into checked invariants

AVA kept flagging "agent code can import the oracle from `/tests`". Rather than argue,
`_assert_reference_out_of_reach()` now stats `/tests` and asserts no group/other bits before
running anything. It passes under real Harbor, so the property is demonstrated. (AVA still
emits the advisory — it appears to be a pattern-level flag — but it is now answerable with
evidence.)

### Issue 9 — pushing mid-pass@2 cancels it and burns budget

One push landed while pass@2 was running; that run recorded `n_completed_trials: 0` and
consumed one of the two daily difficulty-suggestion slots. The suggestion correctly
diagnosed it as an interrupted run needing no task change.

**Practice that worked:** when a fix is non-blocking, commit it *locally* and hold; push
only when bundled with a blocking fix. I did this three times (`1e0ecb9`, `3bf8e57`, plus
the AVA advisories) and it saved several pipeline runs.

---

## 4. What worked, in one page

**Design**
- Heterogeneous key field where each value implies a different *published* convention.
- Sample homogeneous exactly where the specs diverge → shipped answer key is a false green.
- Name the dimension ("each ecosystem's own precedence rules"), never the rule.
- Disclose the *mechanism* in the sample where a gate demands it, on an axis the held-out
  data does not use. When QC demanded pin-normalisation be witnessed, I used a leading-zero
  pin (`0.24.01` ≡ `0.24.1`) and kept the graded axes (leading `v`, explicit epoch, trailing
  zero) latent. Difficulty was unchanged — the very next pass@2 still failed 0/2.

**Verification**
- Exact whole-plan equality; no tolerances (ranks are ints, actions are two literals).
- Held-out inventories generated at verify time; reference derived by running the oracle
  copy over the same rows.
- Structure fixed, values seeded → same submission, same verdict.
- Run the agent's program as `nobody`, empty `PATH`, `-E -s -S`, `RLIMIT_NPROC` floored.

**Calibration before every push**
- Oracle 1.0 / nop 0.0.
- Naive-implementation check (0 sample diffs, ~50% held-out rows wrong).
- Mutation sweep: all 19 mutants caught.
- Leak scan of the built image (`find / -xdev …`) → only the intentional sample key.

---

## 5. Reusable checklist for the next task

Before writing code:
- [ ] Is the deciding rule a *published* convention tied to a visible data field? If it is
      author-invented, it will die at `decisive_answer_discoverable`.
- [ ] Is it absent from everything the agent can see, but derivable by a domain expert?
- [ ] Write the plausible-wrong implementation first; confirm 0 sample diffs and heavy
      held-out divergence.

While building:
- [ ] `.dockerignore` present; no `tests`/`solution` substrings anywhere in the Dockerfile.
- [ ] No `"You have N seconds"` line. `[task].description` non-empty.
- [ ] State only constraints you enforce; enforce only constraints you state.
- [ ] Prefer kernel enforcement over source scanning; where you must scan, match call names
      not arguments.
- [ ] No `task/README.md`; replace the root `README.md`.

Before every push:
- [ ] Oracle 1.0, nop 0.0, leak scan clean.
- [ ] **Mutation sweep — invert every rule in the reference; each must change a graded plan.**
- [ ] Batch non-blocking fixes into the next blocking push; never push while pass@2 runs.
- [ ] Update the root README in the same commit as the design change.

---

## 6. Observations worth carrying forward

- **Gate order:** static → rubric → duplicate → validation → ratelimit → pass@2 → three
  reviews (adversarial advisory, deep-review + AVA union gate blocking) → tier1 → QC
  (blocking) → pass@5. A blocking failure anywhere skips everything downstream, so an early
  cheap failure costs no agent budget.
- **Sticky comments are edited in place.** A stale FAIL right after a push is almost always
  the previous commit's verdict; check `QC-BASE` / the "Ran on `<sha>`" line before reacting.
- **Failure mode drift:** early trials failed by *silent mis-ranking* (deb tilde, epoch),
  final trials by `ValueError` *crashes* (`v6.5.7`, `7.5.5+build`). Crashes are weaker as a
  stump — they signal loudly — but they still counted as good valid fails. If tuning for
  elegance, bias the held-out data toward constructs a naive parser mis-orders rather than
  chokes on.
- **`near_miss` FAIL is healthy**, not a defect: it means the fix was ≤3 lines, which is the
  mark of a fair crux rather than an impossible one. Four of five final trials were
  near-misses.

---

## 7. Pointers

| Thing | Where |
|---|---|
| Reference comparators + planner | `task/solution/solve.py` (SemVer / PEP 440 / dpkg `verrevcmp`) |
| Held-out generator (11 group templates) | `task/tests/heldout.py` |
| Verifier oracle copy | `task/tests/reference.py` |
| Verifier + sandbox | `task/tests/test_outputs.py` (`_drop_privileges`, `_assert_reference_out_of_reach`) |
| Shipped inventory | `task/environment/data/{registry,channels,expected_plan}.csv` |
| Key commits | `ad99145` initial · `27545b3` drop timeout line · `b6d80ce` witness pin normalisation · `ed4c12c` generate held-out at grade time · `010db58` restore determinism · `dfb1a67` bare-dev + precedence wording · `a0b5110` enforceable constraints (accepted) |
