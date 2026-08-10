# dynamo/retired-normalizer — the disclosure deadlock, and how withholding was made fair

Repo: `dynamo-493df7d-mathematics-and-formal-reasoning`, PR #1, branch `submission`,
fork `Pruthviraj374`. (The PR title still reads "Add chain-complex-homology task" — a legacy
title from the repo's first design, never renamed. Do not let it confuse you.)
Category: **Mathematics and Formal Reasoning** / Sub-category: **Computational Linear algebra**.
Benchmarked against Opus-4.8 via Terminus-2. Accepted by every automated gate on 2026-08-09
at commit `4e50071`.

**Final result: pass@5 = 0/5 solved, avg@5 = 0.000, 5 good valid failures, 0 soft-timeout,
0 task/verifier issues, 0 reward hacking.** Best possible outcome. `difficulty_crux: PASS` and
`approach_validity: PASS` on all five trials, with a *single unified root cause* named in the
graders' own words.

Four gate cycles in this session, on top of ~20 commits of earlier redesign. The task had been
stuck for days in a loop that is the whole reason this file exists:

> **B5 demands the archive determine the rule. pass@2 demands the rule not be obvious.
> Three consecutive attempts resolved that by disclosing more, and each one passed B5 and
> died at pass@2.**

§4.1 is the way out, and it generalises past this task.

---

## 1. The task

A retired matrix-processing pipeline recorded three integer fields per square integer matrix.
The code is gone; the records survive; the archive *is* the specification.

- **Agent sees:** `instruction.md` and `/app/data/archive.json` — 123 cases, n=2..10, each pairing
  a matrix with its three-field `record`. Nothing else (`environment/Dockerfile` copies only
  `data`).
- **Agent produces:** `/app/solve.py`, invoked as
  `python3 /app/solve.py <input_json> <output_json>`, emitting a JSON object keyed by case `id`
  with exactly `sig`, `hnf_trace`, `det_sign` — each a plain integer. Plus the report for the
  archive's own matrices at `/app/output/records.json`.
- **Graded on:** exact integer equality, on the archive re-run plus three held-out batches
  (`batch-seen-sizes` n=2–6, `batch-larger-sizes` n=7–10, `batch-mixed-sizes` n=2–10).

The three fields, and what each is for:

| Field | True rule | Role |
|---|---|---|
| `sig` | `Σ w(n,k)·c_k` over char-poly coefficients, `w(n,k) = A + Bk + Cn + Dnk + En² + Fn²k`, `(23,−17,−11,29,7,−13)` | designed easy win |
| `hnf_trace` | `Σ w(n,j)·f_j`, `f_j = H[j][j]·Σ_{i<j} H[i][j]` over canonical HNF, `w(n,j) = P(−1)^j + Qn + Rn(−1)^j + Sj`, `(11,3,−7,5)` | **the crux** |
| `det_sign` | `sign(det)` ∈ {−1,0,1} | silent singular branch |

---

## 2. The crux — and the one that was *believed* to be the crux

The task shipped believing its difficulty was **reverse-engineering the withheld rule**. pass@5
says otherwise, unambiguously:

> "**Single unified root cause across all 5 trials: edge-case trap — incorrect HNF algorithm for
> rank-deficient matrices.** All agents correctly recovered all three field formulas from the
> archive and passed every archive-based test."

Across **nine** measured trials (pass@2 ×2 + pass@5, over three commits), **not one agent failed
to recover the rule.** The real crux is narrower and much sharper:

> **Every archived matrix is invertible, so every archived HNF has its pivots on the diagonal.
> The natural implementation — walk column `i`, assume its pivot is at row `i`, reduce above it
> by `H[i][i]` — is correct on all 123 archived records and undefined the moment the rank drops.**

Two surface manifestations, both observed:

- **crash variant** — `q = H[j][i] // H[i][i]` with `H[i][i] == 0` → `ZeroDivisionError`,
  solver dies, no output (1 of 5 trials);
- **silent-wrong variant** — zero-diagonal column skipped without zeroing the entries above it,
  so `f_j = H[j][j]·ΣH[i][j]` evaluates to a large nonzero where the golden expects **0**
  (4 of 5 trials; `batch-seen-sizes/h08/hnf_trace` expected `0`, agents produced `1260` and `720`).

### The invariants that keep it alive

1. **The archive contains no singular matrix.** 0 of 123. The defect is 0/123 against the
   archive and 15/30, 8/24, 17/36 against the held-out batches. There is no residual to notice
   and no reason to look.
2. **The feature reads reduced off-diagonal entries.** `f_j` depends on the canonical reduction,
   not just the diagonal — which is also what defeats the C3 execution probe (§3.1). Measured:
   a non-canonical row form changes **116 of 123** archived values.
3. **Rank deficiency arrives in six shapes, not one.** Zeroed row, zeroed column, duplicated row,
   scaled row, rank deficit two, all-zero. §4.2 explains why one shape was not enough.
4. **Every size pins its own weight vector** (§4.3). Without this the withheld rule is not
   derivable and B5 blocks — correctly.

### Why `sig` and `det_sign` are not the difficulty

`sig` is a similarity invariant, so char-poly is the forced basis and the rest is exact
Gaussian elimination; every trial got it. `det_sign` reads off the char-poly constant term
once `sig` is done. Both are there so the agent spends its budget feeling successful. The
graders confirmed the shape: all five trials quit confident, having reproduced the entire archive.

---

## 3. Dead ends — do not retry these

### 3.1 Diagonal-only and pairwise-diagonal-product features (C3-exec BLOCK)

Two successive `hnf_trace` designs used only HNF **diagonal** entries — first consecutive
products `H[i][i]·H[i+1][i+1]`, then all pairwise products. Both died at the QC execution probe:

> "**Narrow / Hardcodable Held-Out Coverage** — Mutated the spec-faithful solver's
> `canonical_hnf` to skip the above-pivot reduction loop, producing a NON-canonical row form
> (violates stated req: entries above each pivot must lie in `[0,H[i][i])`, unique HNF).
> E.g. input `[[2,7,1],[0,3,5],[0,0,4]]` -> oracle canonical `[[2,1,3],[0,3,1],[0,0,4]]` vs…"

**Why it is a good probe:** the above-pivot reduction changes only entries *above* the diagonal.
Any feature built from the diagonal alone is invariant to it, so the task can *state* that
canonical HNF is required while nothing actually requires it. The probe is asking: does your
graded output distinguish a canonical HNF from a merely triangular one?

**The fix class:** make the feature read off-diagonal entries. Not "add a stronger assertion",
not "reword the requirement". `f_j = H[j][j]·Σ_{i<j}H[i][j]` fixed it permanently — verified
locally before the push (116/123 divergence) rather than waiting a cycle for QC to agree.

### 3.2 Resolving B5 by disclosing more (three consecutive cycles)

The loop that consumed the days before this session. Each B5 block was answered by writing more
of the rule into `instruction.md`:

| Commit | What was disclosed | Result |
|---|---|---|
| `9737f86` | explicit degree bounds + uniqueness claim | B5 again |
| `7910c8d` | named the consecutive-product feature | B5 again |
| `3624d74` | the **entire** weight formula basis | B5 **passed** — pass@2 failed, 2/5 |
| `0a38058` | pairwise products, still fully disclosed | B5 passed — **C3-exec** failed |
| `c4b0398` | column features, still fully disclosed | C3 fixed — pass@2 **2/2 solved** |

At `c4b0398` the instruction handed over the exact feature formula *and* the exact weight
structure. The pass@2 suggestion's diagnosis was blunt and correct:

> "The task is too easy because `instruction.md` **over-specifies the rules**. … the task
> reduces to three mechanical steps every competent agent executes reliably: compute
> characteristic-polynomial coefficients, compute a canonical HNF, and solve two small exact
> linear systems by Gaussian elimination. The three intended 'cruxes' … are all explicitly
> described in the instruction, so they no longer function as difficulty."

**Do not spend another cycle on this axis.** Disclosure and difficulty are directly opposed;
the fix is to change *what makes the rule derivable*, not how much of it you write down (§4.1).

### 3.3 The stale pass@2 difficulty suggestion (a cycle almost lost)

The handoff document said the next action was to add a `k²` term to the weight formula, quoting
a pass@2 suggestion. **That suggestion was for a different design.** Two suggestions were sitting
on the PR:

- `slug=dynamo-archive-signature-rule date=2026-08-05` — the `k²` advice. Root cause: agents were
  reading per-size weight vectors as **arithmetic progressions**.
- `slug=dynamo-retired-normalizer date=2026-08-08` — matching the current design. Root cause:
  **over-disclosure**; fix: withhold.

The agents at `c4b0398` did not fit per-size at all — both ran one joint Gaussian elimination
over all 72 cases. A seventh parameter in a *disclosed* linear model is one more design column
and no extra thinking. **Check the `slug=` and `date=` on a suggestion before acting on it;
sticky comments accumulate across redesigns and older ones are not retracted.**

### 3.4 Believing the QC sticky without checking `QC-BASE`

At session start the QC sticky read `⛔ Needs revision` with a C3 finding, and the handoff
recorded C3 as the live blocker. The sticky's `<!-- QC-BASE:0a380588… -->` marker showed it was
the verdict for the **previous** commit; `pass2` had failed at `c4b0398`, so `gate` failed and
`qc_eval`/`qc_exec` were **skipped** entirely. The C3 fix had never been tested.

**Always read `QC-BASE` out of the sticky and compare it to HEAD.** And note the ordering: a
`pass2` failure short-circuits `gate`, which skips `qc_*`, `tier1` and `trials`. A green-looking
QC comment after a `pass2` failure is stale by construction.

### 3.5 Withholding alone, as a difficulty mechanism

Withholding the feature and weight family (§4.1) was **necessary but not sufficient**. It earned
the QC pass, but across the first seven trials it produced **zero** rule-recovery failures.
Agents beat the parity crux by a route not anticipated: they never discovered `(−1)^j` as a basis
function — they **split the fit by parity of `j`** and fitted each half. When a polynomial fit
fails, splitting even/odd is the obvious next move.

It is not worthless — one later trial did burn its whole budget on exactly this, having restricted
its regression to polynomials in `(n,j)` and correctly concluded "no weights found". But **do not
plan a task's difficulty on a search-space trapdoor**; the model out-searches small catalogues.
Plan it on an implementation edge case the sample data cannot reveal.

---

## 4. What actually worked

### 4.1 Withhold the rule; prove derivability with a machine check instead of prose

**The move that broke the deadlock, and the most transferable thing in this file.**

`instruction.md` was cut back to qualitative facts only:

- `sig` — "a single fixed **low-degree** integer-coefficient polynomial in n and k" (no degrees).
- `hnf_trace` — "a weighted sum of one feature per column of H, where the feature is a fixed
  simple function of that column's entries — **it depends on entries off the diagonal as well as
  on it** — and the weight … a single fixed low-degree integer formula in n and j."
  Neither the feature nor the weight family is given.
- The HNF convention **stays**. It is a normative definition, not a puzzle. Withholding a
  definition is unfairness; withholding a rule the data determines is difficulty.

The reason earlier withholding attempts were blocked is that the *oracle* hardcoded the answer.
At `47d1952` `recover_hnf_rule` simply wrote the design columns for the true feature. The rule
was undisclosed **and** undemonstrated, which is exactly what a discoverability check flags. It
was never objecting to withholding — it was objecting to *unearned* withholding.

So the oracle was rewritten to **search**:

- `sig` — escalate `(deg_n, deg_k)` through `(1,1), (2,1), (2,2), (3,2)`, accepting the first
  candidate with full column rank and zero residual. Over-generous degrees recover the same rule
  with surplus coefficients exactly zero, so escalation cannot overshoot.
- `hnf_trace` — cross **7 column features** (`d`, `a`, `d·a`, `d+a`, `d²`, `a²`, `d·(d+a)`, where
  `d` is the diagonal and `a` the sum above it) with **3 weight families** (polynomial in `(n,j)`
  of degree 1 and 2, and one carrying `(−1)^j`). Fit all 21 pairs exactly.
  **Exactly one survives; the archive refutes the other 20.**

Then the claim was made checkable rather than asserted — `_reference.py` gained
`assert_rule_decisive`, run at collection time: sweep the same 21 readings, keep every one the
archive fails to refute, and require each to agree with the true rule on 80 matrices **outside**
the archive, including singular ones and every size in range. If a rival reading of the shipped
evidence existed, collection fails rather than a solver being graded down for choosing it.

`qc_eval` + `qc_exec` came back clean — 44 checks, `QC-FIXES-B64: W10=` (empty) — with the
feature and weight family hidden. **Three prior attempts could not hold B5 and pass@2 at once;
this held both.**

> **The generalisable rule: "determinable" does not mean "stated."** 123 exact integer equations
> against a handful of unknowns pin a rule far harder than prose can. When a gate says the mapping
> is underdetermined, the fix can be *more evidence in the data plus a collection-time proof*,
> not more words in the instruction.

One necessary companion fix: `_solve_exact` returned a solution for a **full-rank but
inconsistent** system, so a refuted candidate could pass as a fit. It now returns `None` on any
residual. Without that the whole search is meaningless.

### 4.2 Put the difficulty where the failures actually are, in six shapes

pass@2 and pass@5 evidence said the failures were HNF robustness on degenerate input, not rule
recovery (§3.5). The held-out batches were building **every** singular case one way — zero the
last row. That is rank deficit one, in the single position an implementor is most likely to have
already considered.

They now rotate through six families (zeroed row, zeroed column, duplicated row, scaled row,
rank deficit two, all-zero) and carry **41** rank-deficient matrices, up from 23.

Measured against a diagonal-pivot HNF before pushing:

| | breaks it |
|---|---|
| archive | **0 / 123** |
| `batch-seen-sizes` | 15 / 30 |
| `batch-larger-sizes` | 8 / 24 |
| `batch-mixed-sizes` | 17 / 36 |

The rotation earned its keep immediately: the very next pass@2 failure was an agent whose HNF
"silently breaks for rank-deficient held-out matrices **with zero columns**" — the `zero_col`
family, which the old single-shape data never produced.

### 4.3 Make every size pin its own weight vector (the B5 fix)

`qc_gate` blocked with:

> "**Underdetermined / Hidden-Knowledge Mapping** — Archive has 8 matrices/size; sig weight
> `w(n,k)` design matrix is rank-deficient for n=9 (rank 8 of 9) and n=10 (rank 8 of 10).
> Rival = oracle weight + null-space vector for n=9 reproduces ALL 72 disclosed cases
> (0 mismatches) but differs on every held-out 9x9."

Correct, and worse than reported. Auditing both fields per size found `hnf_trace` far more
deficient — **rank 2 of 7 at n=8, rank 3 of 9 at n=10** — for a structural reason the probe never
reached:

> Canonical reduction forces `0 ≤ H[i][j] < H[j][j]`, so a column whose HNF **diagonal is 1** has
> nothing above it and its feature is **identically zero**. Only columns with a nontrivial
> diagonal carry information, and under uniform sampling those concentrate at the end. Measured
> reachability at n=10: column 9 fires on 100% of draws, column 1 on **0.1%**.

So the archive never exercised the early columns at large `n`, while held-out matrices eventually
do. That is genuinely unrecoverable knowledge.

The archive is now **sampled until each size pins its own weight vector**: random cases first,
then targeted draws while the char-poly design at size `n` is below rank `n`, or the
column-feature design is below rank `n−1` (column 0 is inert — nothing is ever above it).
123 cases, twelve or more per size. `assert_archive_pins_weights` enforces it at collection time.

**Why this is the right shape of fix, not a bigger sample:** a weight vector pinned coordinate by
coordinate has **no null direction to perturb**, so no rival can agree on the archive and differ
off it — *for any weight family*, not merely the one the reference searches. Verified directly:
null space empty at every size for both fields. That is precisely what licenses keeping the
degrees and the feature withheld.

### 4.4 Measure the trap locally before every push

Each cycle, three numbers were computed locally first: C3 divergence under a mutated
`canonical_hnf`, the diagonal-pivot break rate on archive vs held-out, and per-size design rank.
Every one later matched what the gate concluded. The cost is a few seconds; the alternative is an
hour per cycle.

---

## 5. Gate-by-gate log

### 5.1 Cycle A (`c4b0398`) — `pass2` FAIL, everything downstream skipped

Green: `changes`, `cosine_similarity`, `similarity`, `validation`, `ratelimit`, `review`,
`pass2_suggestion`, `claude-cost-report`.

**`pass2` → FAIL, 2/2 solved.** `difficulty_crux: NA` on both trials — both agents recovered all
ten constants exactly, implemented canonical HNF correctly, and wrote the `det=0` branch, in
~12–15 minutes of a 60-minute budget. `gate` failed; `qc_eval`, `qc_exec`, `qc_gate`, `tier1`,
`trials`, `ava_review`, `deep_review` all **skipped**.

The C3 fix in this commit was therefore never exercised by the pipeline (§3.4). Confirmed
locally instead: 68/72 archived values change under a non-canonical HNF.

### 5.2 Cycle B (`3ab2d3d`) — QC clean for the first time; `trials` FAIL

> Fix: withheld the feature and weight family; searching oracle; `assert_rule_decisive` (§4.1).

`pass2` → **PASS, 1/2**. The valid fail was a `ZeroDivisionError` on a zero pivot — the
pre-existing singular trap, not the new withholding. `qc_eval`/`qc_exec`/`qc_gate` → **PASS**,
44 checks, empty fix list, one non-blocking advisory ("Correctness Not Statically Confirmable" —
inherent to executing an arbitrary agent program). `tier1`, `deep_review`, `ava_review` → PASS.

**`trials` → FAIL, 4/5 solved.** The single failure was a terminal wedge: the agent's own HNF
entered an infinite loop, and it spent ~25 minutes sending escape signals until the timeout. It
had *already derived the correct feature offline*. `difficulty_crux: FAIL` — it never reached the
intended crux.

The value table is what redirected the whole design: all four passing trials recovered the
withheld feature **and** the weight family, several by fitting parity-split halves
(`even→−4n+5j+11, odd→10n+5j−11`) rather than discovering `(−1)^j`.

### 5.3 Cycle C (`686387a`) — `pass2` best yet; `qc_gate` BLOCK on B5

> Fix: six degenerate families, 41 rank-deficient held-out matrices (§4.2).

`pass2` → **PASS, 0/2**, and the failures were *stratified* — one per mechanism:

> "1. **Near-miss timeout**: … arrived at a valid HNF and the correct feature candidate … but
> restricted its weight regression to polynomials in (n, j). The true weight contains alternating
> parity terms … The agent's solver correctly reported 'no weights found' …
> 2. **Edge-case trap**: … used `for i in range(n)` treating the loop variable `i` as both column
> index and pivot row … silently breaks for rank-deficient held-out matrices with zero columns."

**`qc_gate` → FAIL**, B5 Underdetermined / Hidden-Knowledge Mapping (§4.3) — even though both
`qc_eval` and `qc_exec` reported `pass` as job conclusions. `trials` skipped.

**Note the trap:** the finding was latent long before this cycle. It only became *blocking*
once the parametric form was withheld — a stated formula interpolates over gaps that an
archive-only derivation cannot. Withholding raises the evidentiary bar on your own data.

### 5.4 Cycle D (`4e50071`) — everything green

> Fix: full-rank archive sampling, 123 cases, `assert_archive_pins_weights` (§4.3).

All 17 checks pass. `pass2` **0/2**. `qc_eval`, `qc_exec`, `qc_gate`, `tier1`, `deep_review`,
`ava_review` → PASS. **`trials` → pass@5 0/5, avg@5 = 0.000, 5 good-valid fails**, single unified
root cause, `accepted`.

Collection-time assertions total ~24s against the 1800s verifier budget
(`assert_similarity_invariant` dominates at 16.6s over 123 cases).

---

## 6. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| QC "Narrow / Hardcodable Held-Out Coverage" naming a mutated normalisation step | Make the graded value **depend** on the step (read off-diagonal entries). Verify the divergence count locally | Reword the requirement, or add an assertion that the solver "must" canonicalise — the probe tests observable output, not stated intent |
| QC "Underdetermined / Hidden-Knowledge Mapping" | Add data until each stratum pins its parameters **coordinate by coordinate**; assert the rank at collection time | Disclose the parametric form to paper over the gap. It fixes B5 and hands you a pass@2 failure (§3.2). Also do not just add *more random* samples — uniform sampling was exactly what missed the rare columns |
| pass@2 "not hard enough", full formula disclosed | Withhold the structure and make derivability a **machine-checked property of the data** (§4.1) | Add another parameter to a disclosed model. One more design column is not one more insight (§3.3) |
| A pass@2 difficulty suggestion arrives | Check its `slug=` and `date=` against the current design first | Act on the top suggestion in the thread. They accumulate across redesigns and stale ones are never retracted |
| QC sticky shows a blocking verdict | Read `<!-- QC-BASE:… -->` and compare with HEAD | Trust the sticky, or the job conclusions — `qc_eval`/`qc_exec` report `pass` while the consolidated verdict blocks |
| Your crux is "the agent must discover a hidden basis function" | Treat it as a bonus, and build the real difficulty on an implementation edge case the samples cannot reveal | Rely on it. The model brute-forces small catalogues and splits fits by parity without being told (§3.5) |
| Only one shape of an edge case in held-out data | Rotate several shapes of the same degeneracy | Ship one shape. An agent that special-cases the shape you thought of passes, and the next agent's different mistake goes uncaught (§4.2) |

---

## 7. Bugs I introduced myself

1. **Rank-deficient archive** (§4.3). The 8-per-size archive never pinned `sig` at n=9,10 nor
   `hnf_trace` above n=3. Survivable while the formula was disclosed; unfair the moment it wasn't.
   **Audit the per-size design rank of every field before withholding anything.**

2. **`assert_hnf_canonical` probed only random dense matrices.** Random integer matrices are
   effectively never singular, so canonicity went unverified on precisely the input the held-out
   batches lean on. A third of the probes are now deliberately degraded. Verified canonical across
   2592 permutation checks over six degenerate families. **A property assertion that never
   constructs the hard input is decorative.**

3. **`_solve_exact` accepted a full-rank inconsistent system** as a fit, which would have let a
   refuted candidate win the search (§4.1).

4. **A wrong measurement, nearly acted on.** The first probe written to measure the diagonal-pivot
   trap divided by a pivot it had *just proved nonzero*, and reported `0` breaks on every batch —
   suggesting the new degenerate data was worthless. The defect being modelled assumes the pivot
   is at `H[i][i]`; the probe did not. Rewritten, it showed 15/30, 8/24, 17/36.
   **Before concluding a fixture does not discriminate, check that the probe reproduces the
   defect you are modelling.** (`audit-build-context` §6 records the same lesson from a different
   direction.)

5. **An AI co-authorship trailer reached a commit message** and had to be amended out with
   `git commit --amend` + `--force-with-lease` before the next cycle. `CLAUDE.md` prohibits this
   anywhere — commits, PR bodies, comments, task files. It is invisible in a diff, so add it to
   the pre-push list rather than trusting review:
   `git log --format='%B' <base>..HEAD | grep -ci "co-authored\|generated with"`.
   Amending is cheap **only** while no run is in flight; a force-push cancels one.

---

## 8. Process rules

- **`pass2` short-circuits everything.** On failure, `gate` fails and `qc_*`, `tier1`, `trials`,
  `ava_review`, `deep_review` are all skipped — so a fix aimed at QC gets **zero** feedback until
  pass@2 clears. Sequence the work accordingly: difficulty first, soundness second.
- **Read sticky comments, never job conclusions.** `qc_eval` and `qc_exec` both showed `pass` in
  the run that blocked on B5.
- **Never push while a check is pending** (`concurrency: cancel-in-progress`). Verified with
  `gh pr checks 1 | grep -c pending` before each of the four pushes.
- **Never `git add -A`.** `task/jobs/`, `pass2-output/`, `qc-*-results/`, `claude-costs-*/` and
  `harbor-output-*/` all land in the working tree from local runs. Stage explicitly.
- **Use a heredoc for commit messages** (`git commit -F - <<'EOF'`). zsh history-expands `!` in
  double quotes.
- **Re-run oracle/nop only when the archive, held-out data, `_reference.py` or `solve.py` change** —
  but *always* then. Both were re-run in cycles B, C and D.
- **`lab6/run_calibration.py` is stale** (references a removed `parity` field). Use
  `lab6/generate_task_data.py` for data, and `harbor run` for calibration.

---

## 9. Reusable checklist

Before withholding any part of a rule:
- [ ] Does the **oracle derive it**, or does it hardcode it? Hardcoding is what discoverability
      checks actually flag — not the withholding itself.
- [ ] Per-stratum design rank audited for **every** field, so each stratum pins its parameters
      with no null direction.
- [ ] A collection-time assertion that sweeps rival readings and requires them to agree **off**
      the sample data, on inputs the sample never contains.
- [ ] The normative *definitions* stay stated; only the *rule the data determines* is withheld.

For the difficulty:
- [ ] Is the crux an implementation edge case the sample data cannot reveal? Prefer that to a
      search-space trapdoor.
- [ ] Measure it: break rate on the archive should be **0**, on held-out substantial.
- [ ] Several shapes of the same degeneracy, not one.
- [ ] Read the pass@ value table — it tells you what the model actually did, which is usually not
      what the design assumed.

Before every push:
- [ ] `gh pr checks 1 | grep -c pending` → 0.
- [ ] Oracle 1.0, nop 0.0.
- [ ] Trap divergence numbers recomputed; stale counts in `task.toml` / `instruction.md` /
      `solve.py` docstrings updated in the same commit.
- [ ] No AI attribution in any commit message.
- [ ] Root `README.md` matches `task/` (`readme-rule.md`).

---

## 10. One-paragraph version for future me

A three-field matrix-archive reconstruction that spent days deadlocked between B5 ("the archive
must determine the rule") and pass@2 ("the rule must not be obvious"), because every B5 block was
answered by writing more of the rule into `instruction.md` — which passed B5 and got the task
solved 2/2. The way out was to withhold the feature and weight family entirely and make
derivability a *property of the data*, proved at collection time: an oracle that searches 21
candidate readings and finds exactly one survivor, plus an assertion that no surviving reading
disagrees with the truth off-archive. QC passed clean with the rule hidden. That fixed fairness
but not difficulty — nine trials showed the model recovers withheld rules reliably, even beating a
parity basis by splitting the fit even/odd. The difficulty was already in the data and had been
mis-attributed: every archived matrix is invertible, so an HNF that assumes column `i`'s pivot sits
at row `i` reproduces all 123 archived records and is undefined on rank-deficient input.
Broadening held-out degeneracy from one shape to six took pass@5 to **0/5 with a single unified
root cause**. Two lessons worth the cycles: withholding a rule raises the evidentiary bar on your
own sample data (a latent rank deficiency became a blocking B5 the moment the formula stopped
being stated), and the pass@ value tables tell you what the model actually did — believe them
over your design intent.
