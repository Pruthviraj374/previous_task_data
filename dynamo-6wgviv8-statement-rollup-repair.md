# dynamo/statement-rollup-repair — the engine as the thing that cannot be argued with

Repo: `dynamo-6wgviv8-debugging-repair`, PR #5, branch `submission-v2`, fork `Pruthviraj374`.
Category: **Debugging and Repair** / Sub-category: **Performance Debugging**.
Benchmarked against `Model A` via Terminus-2.

**Accepted 2026-08-22 at commit `a8211d0`.** Every gate green including `qc_gate`, `trials`
and `gate`; PR labelled `accepted`.

Three days. **Two entirely different tasks** — the first, `dynamo/sla-clock-repair`, cleared
every gate except difficulty and was abandoned after three pass@5 runs; the second, a rebuild
around SQLite, was accepted. Roughly ten pushes, six platform-infra stalls, three `qc_gate`
blocks.

---

## 1. The headline lesson

> **Against this model, a task that grades pure Python against a pure-Python reference with a
> complete written specification has almost no difficulty ceiling left. Every rule you disclose,
> it implements. The difficulty has to come from a real engine whose documented behaviour
> differs from what the specification asks for.**

This is the same finding as `repair-portal-dispatch` (nginx, 0/5) arrived at from the opposite
direction, and it cost three pass@5 runs to re-learn because I built the first task in pure
Python.

---

## 2. The first task, and why it died

`dynamo/sla-clock-repair`: a business-hours SLA clock over ticket exports. Slow per-ticket day
walk, plus eight behaviours the spec required that the shipped quarter never exercised. The
crux was a cached per-site UTC offset — exact on the shipped quarter, wrong wherever an offset
moves.

pass@5 across three runs: **0/5 → 1/5 → 0/5 genuine failures**, against 3 needed.

The trial analyses were unambiguous. From the final run, the model independently implemented
*all of it*: per-date `zoneinfo` resolution, multi-window days, overnight windows, holiday
replacement windows, the clamp, strict `>`, offset-aware timestamps, exclusions, **and the
overlapping-interval merge added in response to the previous run**.

Three specific mistakes I made there:

**(a) I added axes the model already had.** After the 1/5 run I split "merging" into three
requirements (containment, per-day scope, merge-at-all). All four solvers had already merged
correctly. Measuring a mutant's blast radius tells you a wrong implementation *fails* — it tells
you nothing about how likely the model is to write that wrong implementation.

**(b) I disclosed the tells.** The spec said `billing_key` lowering "is Unicode-aware: every
character that has a lower-case form takes it, not only A–Z". That sentence *tells* the agent
that a naive lower-caser is inadequate. Removing it left the rule just as determinate and far
less flagged. Check every normative sentence for whether it names the failure mode.

**(c) I treated a coin flip as signal.** pass@2 returned 1-of-2 four times running, which reads
as ~50%. pass@5 returned 0–1 failures of 5, i.e. ~7%. **pass@2 is two samples; it cannot
distinguish 20% from 50%.** Do not harden on the strength of a pass@2 number.

---

## 3. The rebuild that worked

A monthly billing rollup over a real SQLite warehouse. Slow via N+1 (two queries per account
against an unindexed `readings` table — **167 s** against a 30-second window, where two grouped
scans take **0.2 s**).

The difficulty is four decisions the rollup leaves to SQLite that SQLite does not make the way
the spec requires. All documented engine behaviour, all silent, none visible in the shipped
warehouse:

1. `LOWER()` folds only A–Z — every shipped name is ASCII.
2. Integer `/` truncates where the spec rounds halves away from zero — every shipped account has
   meters of one unit, so one price covers its usage and the division is exact.
3. `COUNT(col)` skips NULLs where the spec counts every reading — no shipped reading lacks a
   quantity.
4. `SUM` over no rows is NULL where the spec wants 0 — every shipped account was read that month.

**Why this shape works and the pure-Python one did not:** the engine's behaviour is documented
and reproducible, so nothing rests on a judgement call — `unambiguous` and the sound-alternative
objection have nothing to bite on — while the agent still has to *know* it. Verify the
behaviours against the pinned image before designing around them; I probed all of them against
SQLite 3.40.1 first.

---

## 4. The `qc_gate` findings — the part I kept getting wrong

Three blocks, all real defects in my verifier, none in the task.

**(a) Probe timeout.** The *Symlinked Output Path* probe runs `bash /tests/test.sh` under a
**300-second cap**. My verifier ran the shipped warehouse twice at 167 s each ≈ 324 s. Fixed by
sharing one run between the two tests and capping the subprocess at 90 s — principled, since a
run that far past a 30-second budget has already failed the timing criterion. Suite went 324 s →
94.5 s while still failing 5 of 6 tests against the unrepaired program.
**→ Time your verifier against the *broken* program, not the oracle.**

**(b) Reward hack.** The verifier handed the program a database and then derived the expected
answer *from that same database*. A program that guts the warehouse makes the reference agree
with it; held-out warehouses had no integrity check at all. Fixed: each run works on a sandboxed
**copy** while the reference comes from the untouched original.
**→ If the verifier both feeds and grades from one artifact, the agent can move the target.**

**(c) Narrow held-out coverage — twice, in both tasks.** First: no graded dataset had
`resolved == raised`. Second: banker's rounding passed everything because no average landed on
an exact half. **I had measured that second one myself, seen zero divergence, and filed it as a
"dead lever".** The correct reading was not "this trap won't fire" but "**my verifier does not
cover a rule the specification states**".

---

## 5. What finally stopped the qc_gate cycle

Fixing only what the report named invited the next instance of the same class. What worked was
running QC's attack classes against myself first:

- a **mutation battery**: one mutant per rule the specification states, run against both
  held-out datasets. Fourteen mutants; it found a hole nothing had flagged — sorting by
  `billing_key` without the account tie-break gave an *identical* answer, because accounts were
  written in reference order and a stable sort coincided with the tie-break. Fixed by sharing
  billing names and shuffling the accounts table.
- an explicit **reward-hack probe** (a program that guts the database and reports on the
  wreckage), run through the real verifier. Scores 0.000.

**A mutant that produces an identical answer is a coverage hole, not a dead trap.** That single
reframing would have saved two cycles.

---

## 6. Design rules confirmed or learned

| Rule | Evidence |
|---|---|
| Disclosed rules get implemented; difficulty must come from a tool's behaviour | 3 pass@5 runs on a fully-specified pure-Python task |
| A trap that breaks *every* case is a global multiplier, not an axis | `NOT IN` + NULL in `suppressions` returned zero rows, wrecking all 390 statements and masking the other four traps — removed |
| Don't state the failure mode in a normative sentence | "Unicode-aware… not only A–Z" told the agent what to avoid |
| Blast radius ≠ likelihood | Splitting merge into three axes moved nothing; all solvers already merged |
| pass@2 cannot calibrate difficulty | 1-of-2 four times, while pass@5 said ~7% |
| Time the verifier against the broken program | 300 s probe cap, 324 s suite |
| Sandbox what you hand the agent's program | expected answer derived from the same DB it could edit |
| Mutate every stated rule before pushing | found the tie-break hole the pipeline hadn't reached |

---

## 7. Platform mechanics worth knowing

- **`review / pass2` is a *waiter*, not the evaluation.** It has a hard 60-minute limit while the
  platform sometimes needs ~80, so it goes red on schedule while the underlying run succeeds. The
  authoritative result is the `harbor / pass@k` **commit status**, not the workflow job:
  `gh api repos/OWNER/REPO/commits/SHA/status --jq '.statuses[]'`
- **Any PR event supersedes a running evaluation.** A close/reopen cost a pass@5 that was an hour
  in. Never touch the PR while `harbor / pass@k` is `pending`.
- **Statuses attach to the SHA, not the PR.** Opening a fresh PR on the *same commit* inherits
  every stale check row. When a commit's evaluation is genuinely stuck, a new **commit** is the
  clean reset; a new branch alone changes nothing.
- **Harbor comments are sticky and carry a `sha=` marker.** After replacing a task, the visible
  pass@2/pass@5 comments may belong to the *previous* commit. Always filter by SHA before reading
  a verdict.
- **`qc_gate` early-exits.** A priority check can defer ~21 others, so a clean-looking report may
  simply not have run most probes yet.
- **Don't push to an accepted PR.** It re-triggers everything and re-rolls a passing pass@5.

---

## 8. Reusable checklist

- [ ] Probe the real engine/tool in the pinned image **before** designing around its behaviour.
- [ ] Check every normative sentence for whether it names the failure mode.
- [ ] Confirm no single trap breaks every graded case.
- [ ] Write one mutant per stated rule; **any mutant producing an identical answer is a coverage
      hole** — fix the data, not the trap list.
- [ ] Build a reward-hack probe (mutate/replace the input, fabricate the artifact) and run it
      through the real verifier.
- [ ] Never derive the expected answer from an artifact the agent's program can write to.
- [ ] Time the verifier against the **broken** program; stay well inside 300 s.
- [ ] Verify the shipped sample hides every trap (assert it, don't assume it).
- [ ] Confirm a fixture-green repair still fails held-out, measured through the real verifier.
- [ ] Read `harbor / pass@k` commit statuses, not workflow jobs; filter comments by SHA.
- [ ] One push per round; never push while an evaluation is pending.

---

## 9. One paragraph

A monthly billing rollup over a real SQLite warehouse is both too slow (N+1 queries against an
unindexed table, 167 s against a 30-second window) and quietly wrong, because it leaves four
decisions to SQLite that SQLite does not make the way the specification requires — `LOWER()`
folding only ASCII, integer division truncating, `COUNT(col)` skipping NULLs, and `SUM` over no
rows returning NULL — none of which the shipped warehouse exercises, and all of which survive a
repair that turns the shipped self-check fully green. It was accepted only after a first task in
the same category was abandoned: three pass@5 runs (0/5, 1/5, 0/5) showed that a fully-specified
pure-Python task gives this model nothing it cannot read and implement, including every axis
added in response to the previous run. The rebuild's difficulty comes from a real engine whose
behaviour is documented and reproducible, which makes it simultaneously hard and unarguable. The
expensive recurring mistake was procedural rather than conceptual: fixing exactly what each
`qc_gate` report named, so the next instance of the same class blocked the following push, until
a mutation battery over every stated rule plus an explicit reward-hack probe were run against the
verifier *before* pushing — which immediately surfaced a hole the pipeline had not yet reached.
