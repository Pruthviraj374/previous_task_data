# dynamo/wetland-nitrate-effect — the confounder that mathematically could not confound

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 17 checks green, `accepted` label |
| **Repo** | `dynamo-93acae6-scientific-computing-and-domain-science`, branch `submission`, fork `charan-sr` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-93acae6-scientific-computing-and-domain-science/pull/1 |
| **Category / sub** | Scientific Computing and Domain Science / Statistical Modeling (pre-seeded) |
| **Final commit** | `7d3ec16` |
| **Headline** | **pass@5 = 1/5 solved, avg@5 = 0.200, 4 good valid fails, failures stratified across three root causes.** `qc_gate`, `ava_review`, `deep_review`, `tier1` all clean. 34 commits total; the last one replaced the entire grading architecture |

The task spent 32 commits and roughly two weeks being calibrated, and every round produced
thin (1–5%), non-monotonic safety margins. This file exists because the reason was not
calibration at all: **one of the four required corrections was mathematically incapable of
confounding anything**, and the architecture could not have worked regardless of parameters.

---

## 1. What the task asks

A wetland restoration nonprofit monitors surface-water nitrate at twelve sites (six restored,
six reference), several stations per site, sampled across a year, with discharge logged per
sample. The restoration-site and reference-site surveys are run by two different contractors.
The agent writes `/app/analyze.py`, which reduces one monitoring program's CSV to a
discharge-adjusted restoration effect, a 95% CI, and a significance boolean.

Four adjustments are required and none substitutes for another: discharge on a proportional
scale, time of year, time of day, and standard errors at the site level (twelve sites, not
288 samples — the textbook pseudoreplication error). All four are stated as facts about the
system; none is named as a technique.

**Graded on twelve monitoring programs**, all-or-nothing: the shipped one plus eleven held out.

---

## 2. The finding that mattered: a covariate that cannot confound

The predecessor design ran **six evenly-spaced bi-monthly rounds across a full calendar
year**, with the restoration contractor's rounds a rigid 35-day offset from the reference
contractor's. Measured on the shipped data:

```
R²(treat ~ [sin, cos] of day-of-year) = 0.0000
group mean gap:  season_sin +0.0014   season_cos −0.0026
```

Over a schedule that wraps the whole annual cycle, **both contractors average to the same
point on that cycle no matter what offset separates them.** A geometry probe confirmed
0.0000 at offsets of 15, 35, 60, 90 and 120 days — it is structural, not a calibration miss.

Season therefore could not be a confounder. Yet dropping it moved the treatment coefficient
by 0.2276 mg/L — a *second-order* effect: season is correlated with discharge and time-of-day
within groups, so removing it perturbs those coefficients, which are genuinely confounded.
That quantity has no designed magnitude, no guaranteed sign, and no stability under
regeneration. **That is exactly why the margin was always razor-thin and why the `SITE_RE_SD`
safety window moved non-monotonically when an unrelated *diurnal* parameter changed** — the
prior session had recorded that non-monotonicity as a mystery.

It was also a fairness bug wearing a soundness costume. `instruction.md` asserted "the two
site groups were surveyed at different points in that cycle." That was **false in the shipped
data**. An analyst who crossed `sample_date` against `site_type`, found the seasonal positions
identical, and concluded season was not a confound was reasoning *correctly* and then failing
— doc 40's Reject trigger ("input data contains incorrect information"). `qc_gate` had flagged
the resulting submission as an over-permissive tolerance; it was really an incorrect premise.

> **Transferable check: for every covariate you require, measure `R²(treatment ~ covariate)`
> on the shipped data before shipping.** If it is ~0, that covariate cannot confound, whatever
> the story says, and any observed effect of dropping it is a second-order artifact you do not
> control. This is one line of code and it invalidated two weeks of calibration.

The fix is not a bigger offset. Any rigid translation of a full-cycle schedule gives 0.0000.
The two contractors now work **different, partially overlapping campaign windows**, which
produces a real imbalance (R² ≈ 0.19–0.39 across programs).

---

## 3. Why no amount of tuning could have worked

Two measurements, both cheap, both decisive.

**Coefficient tuning is scale-invariant.** Raising the seasonal amplitude 0.42 → 1.8 grew the
legitimate-answer cloud from 0.43 to 0.97 mg/L and left the separation margin at **exactly 0**.
Under a multiplicative process reported as a mean difference in mg/L, the spread of sound
answers and the bias from omitting an adjustment scale together. The ratio is fixed by *how
many conventions you accept*, not by any coefficient.

**One dataset cannot separate sound from incomplete here.** Worst-case margin was **0.0000**
across ~60 generator configurations (effect sizes, discharge range and group separation,
between-site variance, schedule geometry), five definitions of the accepted set, three
verifier architectures, and two estimands (mean difference and ratio).

Concretely, on the shipped design the pooled band **accepted 173 of 876 incomplete analyses
and rejected 16 of 112 sound ones** — simultaneously too loose and too tight.

The prior session's proposed fix — union-of-per-method windows instead of one pooled band —
was **refuted by measurement**: at ±0.02 mg/L / ±3% (far tighter than legitimate variation
allows) 54 wrong submissions still passed. The reason is worth stating precisely: the
inverse-discharge-without-season mutant landed at −0.886, *between* log-discharge-OLS (−0.916)
and log-discharge-MixedLM (−0.861). It was not near inverse-discharge's own window; it was
inside log-discharge's. No window architecture over that scalar separates them.

---

## 4. What worked: grade a program, on many datasets with opposed geometry

Every accepted task in this corpus grades a **program against held-out inputs**. This task's
single-dataset/four-numbers contract was unique in the corpus and is precisely the shape that
denies the verifier leverage: with one dataset the verifier can only ask "is this number in a
range," and the legitimate range is as wide as the errors.

The rebuild grades `/app/analyze.py` against **twelve monitoring programs whose confound
geometry is deliberately opposed**:

- which contractor worked the later part of the season — reversed on some programs
- which contractor's crews sampled earlier in the day — reversed on some
- which group sits on the larger channels — reversed on some
- discharge range varies ~2× to ~55×, campaign length 212–345 days
- **the true effect differs per program**, so no constant passes

An omitted adjustment is biased in a direction set by each program's own geometry, so it is
wrong on programs whose geometry points opposite ways. **The conjunction discriminates where
no single band can.** Grading is all-or-nothing, so a wrong method that lands in band on one
program by luck has near-zero chance across twelve.

Fixture geometry is not hand-tuned: `autotune.py` bisects each program's contractor hour gap,
discharge ratio and campaign offset to hit a *chosen* `R²(treat ~ block)` target. Each program
therefore carries a stated confounding strength rather than whatever fell out of the parameters.

**Enumerate variation; do not pad for it.** The accepted cloud contains 210 analyses — two
proportional discharge conventions × five seasonal × three time-of-day encodings × four
site-level estimators, plus the rating-curve convention across the same encodings, both
back-transformations, and **four bootstrap seeds**. Seed noise is enumerated for the same
reason encodings are: padding the half-width wide enough to absorb a twelve-cluster
percentile interval's seed noise costs the raw-linear-discharge discriminator outright.

**Half-width bounds are asymmetric** (÷1.05 below, ×1.06 above) because only the lower one
grades a stated requirement. Getting the unit of replication wrong makes an interval too
*narrow*; nothing in the task makes one too *wide*.

Result against the real verifier on all twelve programs: every accepted analysis passes
everywhere, and **none of 438 incomplete analyses passes all twelve**.

---

## 5. Two harness races that produced confident, wrong results

Both cost a cycle. Both are the same bug in different clothes: **a mutant battery owns
`solution/solve.py` for its whole duration.**

**It ate the calibration.** Running `calibrate.py` while the battery ran loaded a mutant as
the reference and reported, with total confidence, that the reference solution failed on two
programs. Twenty minutes went into hunting a nonexistent verifier bug.

**It ate the commit.** Staging while the battery ran committed a reject-side mutant as
`solution/solve.py`. Static checks passed **25/25** — the file is syntactically fine and
correctly placed — and only the rubric gate caught it, by *reading* the oracle: *"the shipped
Oracle would fail its own verifier: no working solution is actually provided."* One wasted
pipeline cycle.

Checking the working tree before staging is **not enough** — the battery can swap the file
between the check and the `git add`. Check the **staged blob**, immediately before committing,
and scan the committed tree afterwards. Better: never overlap a battery with a commit.

---

## 6. The accept-side probe blindness — the most transferable methodological lesson

Local calibration said the design was clean. Real harbor scored a **sound** power-law
submission **0.0**, twice.

The cause was not the design. My calibration compared against the point and half-width bands
and reconstructed intervals as `estimate ± half_width` — **symmetric by construction**. It was
therefore structurally incapable of observing the *centring* assertion, which was what actually
rejected the submission on 5 of 12 programs while both bands passed fine.

Worse, the centring check was internally contradictory: it rejected intervals deviating >35%
of their half-width, while the verifier's **own** accepted percentile-bootstrap convention
reaches **55%** across programs, encodings, smearing choices and seeds. The verifier was
rejecting intervals its own blessed method produces. (The predecessor had already widened this
15% → 35% for the same reason and stopped short.)

> **An accept-side probe is only as good as the assertions it exercises.** If calibration
> reimplements a *subset* of the verifier's checks, it is blind to exactly the ones it did not
> reimplement — and blind in the *fairness* direction, which gets tasks rejected rather than
> merely re-rolled. Call the verifier's real `_check_result`, never a paraphrase of it.

---

## 7. Gate-by-gate

| Push | Commit | Result |
|---|---|---|
| — | `2852129` | inherited state: `qc_gate` ⛔ Over-Permissive Tolerance (the finding that opened the session) |
| 1 | `5ed899f` | static ✅ 25/25 · **rubric ⛔ FAIL** — `solvable` + `solution_explanation_quality`: a battery mutant was committed as the oracle (§5). Everything downstream skipped; **no pass@2 budget burned** |
| 2 | `7d3ec16` | **everything green** — static 25/25 · rubric ✅ · validation ✅ · **pass2 0/2, 2 valid fails**, `pass2_suggestion` skipping · deep_review ✅ · ava_review ✅ · tier1 ✅ · qc_eval/qc_exec/**qc_gate** ✅ (44 checks, `QC-FIXES-B64:W10=`, `QC-BASE` = HEAD) · **trials 1/5, avg@5 0.200** → `accepted` |

`ava_review` passing first time is worth noting: the anti-cheat hardening for the
program-re-invoked-at-verify-time shape was built in up front rather than after a block —
bands computed before the graded program runs once, fixture tree deleted, each input isolated
read-only in its own directory, reference inlined rather than importable, `/tests` sealed
`0700` against the unprivileged account the program runs as. Sibling tasks in this corpus lost
three to five cycles to exactly these findings.

---

## 8. What the model actually did, and the one caveat

**All five agents independently identified all four required adjustments.** Every failure was
in implementation detail, stratified across three root causes:

1. **Degenerate optimizer** (1 trial) — `method='lbfgs'` in MixedLM converged to a degenerate
   minimum on 8/12 programs, collapsing the treatment coefficient to ~10⁻¹⁵ and the covariance
   to singular (CI half-widths of millions of mg/L). *The shipped program happened to avoid
   that geometry; the held-out programs did not* — the latent-crux shape, at the level of
   numerical conditioning rather than domain knowledge.
2. **Non-standard CI on a log-log model** (1 trial) — parametric sampling from the REML
   fixed-effects covariance, which does not propagate site-level variance through the
   nonlinear back-transformation. CIs 1.5–3× too narrow on 8 of 10 failing programs.
3. **Near-miss bootstrap variants** (2 trials) — a *stratified* cluster bootstrap (always 6+6
   sites, constraining group-size variance) and REML shrinkage inside the bootstrap loop. Both
   land 11–29% below the floor on h06 and h10 specifically.

h06 and h10 failed in **all four** failing trials — the two programs whose geometry sets the
tightest lower bound.

**The caveat, stated plainly.** The conjunction was designed to fix the *point-estimate* axis,
and that is not what did the work. Every agent got the point estimate right; **four of four
failures were CI-width failures against the half-width lower bound**, with the thinnest at
11%. `near_miss` FAILed on 2 of 5 trials. The design is sound and `approach_validity` passed
5/5, but the discrimination rests on a tighter axis than intended, and a human reviewer may
reasonably press on that. If it comes back, the lever is to move discrimination onto the point
estimate (more programs with more extreme opposed geometry) rather than to tighten `hw_lo`
further.

---

## 9. Reusable checklist

Design:
- [ ] For **every** required covariate, measure `R²(treatment ~ covariate)` on the shipped
      data. ~0 means it cannot confound — the story does not matter, and any effect of
      dropping it is a second-order artifact you do not control.
- [ ] Beware schedules that wrap a full cycle: a rigid offset across a whole period produces
      **zero** imbalance for any offset.
- [ ] If the answer is a scalar from one dataset, ask whether the map (analysis choices) →
      (that scalar) is injective enough. If several sound conventions are accepted, it is not,
      and no tolerance will separate sound from incomplete.
- [ ] Prefer grading a **program on held-out inputs with opposed geometry** over a band on one
      dataset. The conjunction discriminates where a band cannot, and it lets each band stay
      generous enough to be fair.
- [ ] Vary the true answer per fixture. It removes the hardcoded-constant risk outright.
- [ ] Solve fixture geometry to a **target** confounding strength (bisection) instead of
      hand-tuning; keep each block out of the near-collinear zone (>~0.55 R² and the effect
      stops being identified — one fixture blew the band up to 1e15 before this was capped).

Verifier:
- [ ] Enumerate methodological variation in the accepted set — including **bootstrap seeds** —
      rather than padding the band for it. Padding costs discriminators.
- [ ] Make band bounds **asymmetric** where only one direction grades a stated requirement.
- [ ] Derive every tolerance from a measurement of the accepted conventions' own behaviour.
      A centring tolerance tighter than the reference bootstrap's own skew is self-contradictory.

Calibration:
- [ ] Call the verifier's **real** check function. Never reimplement a subset of its
      assertions — you will be blind exactly there, in the fairness direction.
- [ ] Probe the accept side through **real harbor**, not only locally. Two sound-submission
      rejections here were invisible to local checks.
- [ ] Never run a mutant battery concurrently with calibration **or** with a commit. Guard the
      **staged blob**, not the working tree.

---

## 10. One-paragraph version for future me

This task was stuck for 32 commits on razor-thin, non-monotonic calibration margins, and the
cause was that one of its four required corrections was mathematically incapable of
confounding: six evenly-spaced bi-monthly rounds across a full year make both contractors
average to the same point on the annual cycle for *any* offset, so `R²(treat ~ season) =
0.0000` and the 0.23 mg/L cost of dropping season was a second-order collinearity artifact
with no designed magnitude or stable sign. Measure `R²(treatment ~ covariate)` for every
covariate you require — it is one line and it would have saved two weeks. The second finding
is that no calibration could have rescued the architecture: under a multiplicative process
reported as a mean difference, the sound-answer spread and the omitted-adjustment bias scale
together, so raising the seasonal amplitude 4× left the separation margin at exactly zero, and
the worst-case margin was 0.0000 across ~60 configurations, five accepted-set definitions,
three band architectures and two estimands — the prior session's preferred fix
(union-of-per-method windows) was refuted at tolerances far tighter than fairness allows,
because the binding mutant sat *between* two accepted methods rather than near its own. What
worked was abandoning the single-dataset four-number contract for the shape every accepted
task in this corpus already uses: grade the agent's **program** against twelve monitoring
programs whose confound geometry is deliberately *opposed*, so an omitted adjustment is biased
one way on some and the other way on others and cannot be tuned into agreement with all of
them. Two process traps cost a cycle each, both the same bug — a mutant battery owns
`solution/solve.py` while it runs, and it will silently poison a concurrent calibration *and*
a concurrent `git add` (static checks passed 25/25 on a committed mutant oracle; only the
rubric caught it by reading the file). And the most transferable methodological lesson: my
local calibration reconstructed intervals as `estimate ± half_width`, symmetric by
construction, which made it structurally blind to the *centring* assertion that was actually
rejecting a sound bootstrap submission — an accept-side probe is only as good as the
assertions it exercises, so call the verifier's real check rather than a paraphrase of it.
Final: pass@5 1/5, avg@5 0.200, four good valid fails stratified across three root causes,
`approach_validity` PASS on all five, every gate green — with the honest caveat that all four
failures landed on the half-width floor rather than the point-estimate conjunction the design
was built around.
