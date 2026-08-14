# dynamo-93acae6 (wetland-nitrate-effect) — authoring tooling

These scripts generate the task's datasets and prove its design invariant. They are kept
here, **not** in the task repo, because they encode the data-generating process — shipping
them would hand the agent the answer. They are kept at all because the predecessor design's
generator lived only in a session scratchpad and was lost with it, which cost a later
session a full rebuild.

Nothing here is imported by the task. Set `DYNAMO_TASK_REPO` to your clone of the task repo
(or edit the default at the top of `build_data.py` / `calibrate.py`).

## Files

| File | Purpose |
|---|---|
| `gen.py` | The generator. One `Params` dataclass; every design knob is an explicit field. |
| `fixtures.py` | The twelve monitoring programs (shipped + eleven held-out): overrides plus a target confounding strength for each. |
| `autotune.py` | Solves each fixture's contractor hour gap / discharge ratio / campaign offset by bisection to hit its target `R²(treat ~ block)`. Writes `tuned.pkl`. |
| `evaluate.py` | Enumerates the accepted-analysis cloud and the violating-analysis cloud for a dataset. |
| `calibrate.py` | **Run this before every push.** Asserts the design invariant against the real shipped `test_outputs.py`. |
| `build_data.py` | Writes every CSV into the task repo and checks the shipped copy is byte-identical to its graded copy. |
| `probe_season.py` | Cheap geometry probe: how much seasonal imbalance a given round schedule actually produces. |
| `mutants/` | Reject-side and accept-side `analyze.py` variants for the real-harbor battery. |

## The invariant `calibrate.py` asserts

> **Fairness** — every analysis applying all four adjustments soundly passes on every
> monitoring program.
> **Soundness** — no analysis omitting or mis-specifying a required adjustment passes on
> *all* of them.

Grading is all-or-nothing across the twelve programs, so the second clause is exactly "no
incomplete analysis scores 1.0". The predecessor design re-searched for a safe parameter
value after every change and had no assertion to catch it when the value stopped being
safe; this is that assertion.

Order of operations after any change: `autotune.py` → `build_data.py` → `calibrate.py` →
real harbor oracle/nop → `mutants/` battery through real harbor.

## Two findings worth not rediscovering

**Season could not confound, structurally.** The predecessor ran six evenly-spaced
bi-monthly rounds across a full calendar year, with the restoration contractor's rounds a
rigid offset after the reference contractor's. Under that geometry both contractors average
to the same point on the annual cycle for *any* offset — measured `R²(treat ~ season) =
0.0000`, and `probe_season.py` confirms 0.0000 at 15/35/60/90/120-day offsets. The apparent
0.23 mg/L cost of dropping season was a second-order collinearity artifact with no designed
magnitude or stable sign, which is why its margin was always razor-thin and moved
non-monotonically when unrelated parameters changed. The fix is two contractors working
different, partially overlapping campaign windows, not a bigger offset.

**Coefficient tuning cannot open the margins.** Under a multiplicative process reported as a
mean difference in mg/L, the legitimate answer spread and the omitted-adjustment bias scale
together. Raising `b_season` 0.42 → 1.8 grew the accepted cloud 0.43 → 0.97 mg/L and left
the separation margin at exactly 0. Roughly sixty configurations across every knob, five
definitions of the accepted set, three verifier architectures and two estimands all gave a
worst-case margin of 0. Grading a program on many programs with opposed confound geometry is
what works; no calibration of a single dataset does.

## Two traps in this tooling itself

**Never run `calibrate.py` while a mutant battery is running.** The battery swaps
`solution/solve.py` in place, so calibration loaded a mutant and reported, confidently and
wrongly, that the reference solution failed on two programs. `calibrate.py` now asserts the
file is the real reference before importing it. The general form of this is already in the
playbook (`cron-window-counts` §6, on restoring mutants with `git checkout` mid-fix): any
harness that temporarily replaces a graded file must be assumed to be running.

**Calibrate against the verifier's real check, not a reimplementation of its bands.** An
earlier version compared only against the point and half-width bands and reconstructed
intervals as `estimate ± half_width` — symmetric by construction. That made it structurally
incapable of seeing a *centring* failure, which is what was actually rejecting a sound
percentile-bootstrap submission on 5 of 12 programs, while the bands themselves were fine.
Local calibration said the design was clean; real harbor said 0.0. It now calls the
verifier's own `_check_result` with the bootstrap's actual asymmetric bounds.

The lesson generalises past this task: an accept-side probe is only as good as the assertions
it exercises. If the calibration reimplements a subset of the verifier's checks, it will be
blind to exactly the ones it did not reimplement — and blind in the fairness direction, which
is the direction that gets tasks rejected rather than merely re-rolled.

**The same race will eat your commit, not just your calibration.** Staging while a battery
was running committed a reject-side mutant as `solution/solve.py`. Static checks passed 25/25
— the file is syntactically fine and in the right place — and the rubric gate caught it only
by *reading* the oracle: "the shipped Oracle would fail its own verifier: no working solution
is actually provided." One wasted pipeline cycle.

Checking the working tree before staging is not enough, because the battery can swap the file
between that check and the `git add`. Check the **staged blob**, immediately before
committing:

    git add task/solution/solve.py
    git show :task/solution/solve.py | grep -q "<a phrase only the real reference has>" || exit 1
    git show :task/solution/solve.py | grep -qE "REJECT-side|ACCEPT-side" && exit 1

and scan the whole committed tree afterwards:

    for f in $(git ls-tree -r --name-only HEAD -- task/); do
      git show "HEAD:$f" | grep -qE "REJECT-side|ACCEPT-side probe" && echo "MUTANT IN: $f"
    done

Better still: never run a mutant battery and a commit in the same window. The battery owns
`solution/solve.py` for its whole duration.
