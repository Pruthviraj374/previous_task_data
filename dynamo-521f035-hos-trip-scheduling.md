# dynamo/hos-trip-scheduling — a domain pivot, then two author-side algorithm bugs QC found

Repo: `dynamo-521f035-scientific-computing-and-domain-science`, PR #2, branch `submission`,
fork `charan-sr`.
Category: **Scientific Computing and Domain Science** / Sub-category: **Optimization and
Operations Research**.
Benchmarked against Opus-4.8 via Terminus-2.

**Accepted on 2026-08-11 at commit `c836ab5`. pass@5 = 0/5 solved, avg@5 = 0.000, 3 good
valid failures + 2 in-progress-timeouts (soft, don't count toward the ≥3 bar but didn't need
to), 0 task/verifier issues, 0 reward hacking.** Best outcome the spec defines. An earlier
accepted state (commit `5f37214`, before a docs-only + then a correctness push re-rolled the
pipeline) had already cleared 1/5.

Eleven pushes total, across **two entirely different task domains** in the same category/
subcategory. The first four pushes (inventory EOQ / safety-stock) never got past pass@2 and
were abandoned as a dead line, not fixed. The pivot (push 5, commit `592061f`) to Hours-of-
Service trip scheduling is what actually worked, but even that design shipped with two real
bugs in the author's own reference solution — not fairness or disclosure problems, actual
wrong answers — that QC and AVA caught by constructing inputs outside the shipped dataset.
**That's the finding worth carrying forward from this task**: for an algorithmic/DP crux,
adversarially probing your own reference the way QC will is not optional, and "it matches my
one shipped dataset" is not evidence the algorithm is correct.

Commits: `f8c83f8` initial submission (EOQ/reorder-point) · `4202fd0` remove disclosed
lead-time-distribution hint · `46f1f94` add price-break EOQ complexity · `592061f`
**domain pivot to HOS scheduling** · `7af3497` fix: greedy isn't always optimal · `765ca77`
grade compliance+minimum-time, not exact segment match · `24be362` fix: drive-limit doesn't
restrict on-duty · `5f37214` README sync (accepted here, 1/5) · `c836ab5` fix: window-limit
also doesn't restrict on-duty (accepted here, 0/5).

---

## 1. Era 1 — inventory EOQ / safety-stock (abandoned after 3 pass@2 solves)

Initial design: given raw demand-history and replenishment-log CSVs, compute a per-SKU order
quantity (EOQ) and a reorder point meeting a 98% service level. The intended crux was that
reorder point must combine variance from **both** demand and lead time (the standard formula
for the variance of a sum of a randomly-distributed number of random draws), not just demand
— lead time was given as raw historical order/receipt-date pairs, not a stated constant.

- **Push 1 (`f8c83f8`):** instruction explicitly said lead time was "independently normally
  distributed, mean and std estimated from history." pass@2: **2/2 solved**, both agents
  reproduced the compound-variance formula verbatim in code comments.
- **Push 2 (`4202fd0`):** removed the explicit distribution hint, described lead time
  neutrally. pass@2: **2/2 solved again.** The automated pass@2 analysis explicitly noted two
  different agent architectures converged on the identical formula, "strongly suggesting this
  pattern is well-represented in training data rather than derived from first principles."
- **Push 3 (`46f1f94`):** added a genuine second difficulty axis — a quantity-discount
  price-break schedule, requiring per-tier feasibility clamping and total-cost (not just
  ordering+holding) comparison across tiers, a real multi-step algorithm rather than a
  one-line formula. pass@2: **2/2 solved a third time**, both agents independently derived
  the *entire* algorithm — tier clamping, purchase-cost inclusion, and the reorder-point
  formula — from scratch.

**Three confirmed solves on three different framings of the same domain is the signal, not
noise.** This matches the playbook's own `stumping_guidelines.md` finding almost exactly:
Opus-4.8 self-verifies aggressively and recalls entire methodologies from training data; any
task whose correctness the agent can both *derive* and *self-check* against textbook
knowledge is solved regardless of how much structural complexity gets bolted on, as long as
every piece is itself a named, well-documented technique. EOQ and safety-stock formulas are
arguably the single most heavily-drilled worked example in the entire operations-management
curriculum — embellishing them (price breaks, hidden distributional facts) changes the
implementation effort, not the recall risk. **Practical rule confirmed a further time: after
~2 confirmed catch-22 solves on one crux line, stop tweaking it and pivot the mechanism
entirely** — a third attempt on the same domain (push 3) cost a full cycle and still failed
for the identical underlying reason.

---

## 2. Era 2 — the pivot, and the crux that actually worked

Same category/subcategory, different mechanism: compute the **time-minimizing**,
Hours-of-Service-compliant multi-day driving schedule for a fixed sequence of trip legs
(on-duty/loading time then driving time, per leg), given real 49 CFR Part 395 rules (11h
drive limit, 14h on-duty window, mandatory 30-min break after 8h driving, 10h reset).

Two deliberately layered traps, one that survived and one the trials didn't actually need:

1. **Greedy-maximal-consumption is not globally optimal.** The obvious strategy — always
   drive/work as much as legally allowed before ever resetting — looks unimpeachable (total
   on-duty and driving content is fixed and mandatory regardless of scheduling) but is
   provably wrong: because each leg's on-duty time must directly precede that leg's driving,
   a voluntary, not-yet-required early reset can shift a later boundary favorably enough to
   save an entire downstream 10-hour reset cycle. This is the crux that actually discriminated
   in both pass@5 runs (see §4).
2. **The 14-hour window is elapsed wall-clock time since coming on duty and keeps running
   through the 30-minute break** (only a full 10-hour reset stops it) — a real, independently
   web-search-confirmed point of confusion among actual truckers, not an invented gotcha.

Why this survived where Era 1 didn't: it isn't a single named formula. Even an agent that
recalls "greedy isn't always optimal for scheduling" still has to notice that *this specific*
problem shape admits the failure mode, then implement a real search (a short memoized DP) —
a multi-step, code-dependent derivation, not a lookup. Confirmed directly in the pass@5
trace analysis: the one agent that solved it (in the 1/5 run) explicitly built and
cross-checked a DP; every other trial either never considered voluntary early resets at all,
or — in one case — talked itself out of the correct approach with flawed reasoning after
having identified it (see §4).

---

## 3. Two author-side bugs QC/AVA found in the reference itself (the important part)

Both of these were **not** fairness, disclosure, or verifier-tolerance issues — the kind this
playbook otherwise spends most of its pages on. They were the author's own DP being
**objectively wrong**, caught by QC and AVA constructing inputs the shipped dataset never
exercised.

### 3.1 — `qc_gate` A6: greedy-vs-DP was fine, but the DP itself had a bug (push `7af3497`)

First real design (push `592061f`) used a *greedy* forward simulation as the reference,
believing it obviously optimal. `qc_eval` constructed a counterexample directly: on the
shipped 9-leg dataset, an independent model found a legal schedule 30 minutes shorter than
the reference. **Verified by writing a brute-force memoized search from scratch and
confirming QC was right** — 147.5h true optimum vs. the greedy reference's 148.0h. Replaced
the greedy reference with the DP everywhere (`solve.py` and the independent copy in
`test_outputs.py`).

**This did not end the story** — see 3.2. The same class of bug recurred twice more because
the *first* fix only addressed the specific way greedy-vs-DP diverged, not the DP's own
correctness on inputs unlike the shipped one.

### 3.2 — `qc_gate` A6 again: the DP's "forced reset" logic was wrong for a different reason (push `24be362`)

Next `qc_gate` cycle constructed a **synthetic 2-leg input never resembling the shipped
data** (leg1: 11h drive/1.5h on-duty; leg2: 11h drive/3.5h on-duty) and found the DP-fixed
reference still wrong by **540 minutes** — far too large to be a tie-break artifact. Traced
it by hand (writing the DP inline in a scratch script and probing intermediate states) to a
genuine logic bug: the "forced reset" condition treated the 11-hour drive-hour limit as
forcing an immediate reset the instant it was hit, **regardless of whether the next required
action was actually driving**. But the drive limit only restricts *driving* — when on-duty
(non-driving) work remained for the next leg and the window still had room, the correct move
was to do that on-duty work first, not reset immediately. Fixed the forced-condition to only
consider the drive limit when driving is actually next; verified against QC's exact
counterexample (now correctly finds the 2280-minute optimum) and confirmed no regression on
the shipped dataset.

### 3.3 — `ava_review` no_false_rejection: same mistake, different clock (push `c836ab5`)

Two cycles later, after the exact-segment-match verifier had already been relaxed to
compliance + minimum-time checks (§4), `ava_review` blocked with a **BLOCK verdict** on
`no_false_rejection`: re-reading `instruction.md`'s own four literal rules, **only the
14-hour-window rule also restricts driving specifically** — nothing in the stated rules caps
on-duty time by the window either. The verifier's compliance replay (and the DP) still
capped ON_DUTY segments by the 14-hour window, incorrectly rejecting a legal schedule where
on-duty work straddles the 14-hour mark. This is the *identical class of bug* as 3.2 (an
activity-type-blind "forced/blocked" check) recurring on the **other** clock (window instead
of drive-hours). Fixed all three call sites (DP in `solve.py`, DP in `test_outputs.py`,
compliance replay), and this time **constructed AVA's exact scenario directly** — a
single-leg dataset with 1h drive / 20h on-duty — and confirmed the oracle now produces
`ON_DUTY (20h) → RESET → DRIVE (1h)` and all four tests pass.

**The generalizable lesson (new to this playbook):** when your crux is "the obvious algorithm
is subtly wrong, here's the actual DP," the same trap that's supposed to catch the *agent* can
also catch *you*, more than once, in different corners of the same state machine. Two
different clocks (drive-hours, window) had the identical class of bug (treating a
non-driving activity as gated by a driving-specific limit) — fixing the first instance did not
surface the second by inspection; it took QC/AVA constructing genuinely different inputs to
find each one. **Before shipping an algorithmic reference, write your own adversarial inputs
that stress every clock/limit independently** (not just the shipped dataset's specific
shape), and check a general invariant like "does relaxing any one constraint ever produce a
schedule my reference wrongly calls illegal or wrongly calls suboptimal?" — don't wait for
QC to be your only source of counterexamples.

---

## 4. The verifier-design lesson: exact segment match vs. compliance + optimal time

Push `7af3497`'s corrected DP still graded the agent's output by exact segment-by-segment
match against one reference schedule. The `review` (rubric) gate caught a genuine ambiguity:
**total elapsed time is invariant to exactly where the mandatory break falls within an
otherwise-fixed window** (driving 6h then breaking then 3.5h costs the same total time as
driving 8h then breaking then 1.5h). More than one schedule is genuinely time-optimal, so
exact-match grading was rejecting some of them as wrong — grading on an undisclosed tie-break
the instruction never established, not on what it actually asked for.

Fixed (push `765ca77`) by replacing exact-match with two checks aligned to what the
instruction actually states: a **compliance replay** (every submitted segment checked
directly against the real HOS rules — no rule may be violated anywhere, on-duty must precede
driving per leg) and a **minimum-total-time check** (recomputed independently via the same
search). This is more robust than exact-match by construction: it accepts any legal,
time-optimal schedule, and it's what actually discriminates — a fully-compliant-but-greedy
schedule passes the compliance half and fails only on time. Verified locally that the
reviewer's own cited counterexample (break earlier in a window) now passes, a legal-but-30-
min-slower schedule still fails on time, and a schedule that actually violates a rule still
fails on compliance.

**Generalizable:** when the "obvious" verifier design is exact-match against one reference
and a reviewer names a concrete alternative that's equally valid, the fix is a real legality
+ objective-function auditor, not a wider tolerance band on the exact-match check. This also
turned out to *increase* apparent difficulty rather than reduce it — see the pass@5 group-B
failures below, which are wide misses (17.5–19.5h over optimal), not near-misses that a
looser exact-match tolerance would have needed to paper over.

---

## 5. What the pass@5 trials actually showed (both accepted runs)

**Run 1 (commit `5f37214`, 1/5 solved):** the four failures were a clean single root cause —
plain greedy or leg-boundary-restricted DP, none considering a leg's drive time split across
a voluntary mid-leg reset. One agent (`task__SknNWvY`) is worth naming specifically: it
built a greedy schedule, correctly diagnosed it as suboptimal, **built a Dijkstra-based
optimizer (the right approach)**, then cancelled it mid-run citing runtime concerns, checked
pairwise leg-driving-hour sums, concluded "no two legs can share a shift," and reverted to
the suboptimal greedy artifact — despite the instruction explicitly not prohibiting
cross-reset drive splitting. The correct insight was reached and then talked out of.

**Run 2 (commit `c836ab5`, 0/5 solved, avg@5 = 0.000):** stratified into two groups. Group A
(2 trials) produced schedules exactly 30 minutes over optimum and were still actively
iterating when the 1800s budget expired (`low_timeout: FAIL`, `near_miss: FAIL` — genuinely
close, not stuck). Group B (3 trials) produced schedules 17.5–19.5 hours over optimum (8–9
resets vs. the true 6–7) and voluntarily called task-complete before the timeout — the same
"correct insight, abandoned" pattern as run 1's `task__SknNWvY`. `approach_validity` PASSED
across all five trials in both runs: the failures are legitimate agent limitations, not task
or verifier defects, and the task author's own `difficulty_explanation` predicted the exact
failure mode in advance in both cases.

---

## 6. Pre-push checklist used from push 5 onward

- [ ] `harbor run -p . --agent oracle` = 1.0, `--agent nop` < 1.0
- [ ] For an algorithmic/DP reference specifically: construct at least one input **unlike**
      the shipped dataset (different leg count, different limit-boundary alignment) and
      check the reference against an independently-written second implementation
- [ ] Mutation-test the verifier directly: build 2-3 plausible-wrong implementations
      (naive/greedy, a specific known misconception) and confirm each fails; build one
      legitimate-alternative implementation (different but equally sound convention) and
      confirm it passes
- [ ] `rm -rf task/jobs` before every commit (harbor local-run output)
- [ ] README.md and `task.toml` prose (`difficulty_explanation`, `solution_explanation`,
      `verification_explanation`) updated **in the same commit** as any design/verifier
      change — missed once (push `24be362`→`765ca77` gap), caught and fixed the next time a
      human asked to check it, cost one extra docs-only push
- [ ] Never push while a check is in flight (`gh pr checks`, look for zero `pending`)
- [ ] Grep commit messages for AI/Claude attribution before every push

---

## 7. One-paragraph version for future me

If a domain's difficulty rests on a named, well-documented formula or technique — however
much structural complexity you bolt around it (price breaks, multi-tier comparisons) — a
strong self-verifying model will recall and correctly apply the whole thing, confirmed a
third time here across three different framings of an inventory-EOQ task; stop after two
confirmed solves and pivot the mechanism, not just the wording. What actually survives is an
algorithm whose obvious/greedy approach is *provably* wrong in a way that requires real
multi-step derivation to discover (here: voluntary early resets sometimes beat greedy
maximal-consumption, because a leg's on-duty time gates its driving) — and even then, build
the verifier as a legality-plus-objective auditor, not exact-match against one reference,
the instant a reviewer names a second equally-valid schedule. Most importantly: once your
crux is "the obvious algorithm is subtly wrong," budget for the possibility that *your own*
reference has the identical class of bug, possibly more than once, in different corners of
the same state machine — QC and AVA will find it by constructing inputs unlike your shipped
dataset (a synthetic 2-leg case; a 20-hour-on-duty edge case), and "matches my one shipped
example" was never evidence the algorithm was right. Write those adversarial inputs yourself,
for every independent limit/clock in the design, before a gate has to find them for you.
