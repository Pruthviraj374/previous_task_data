# dynamo/model-clock-peripheral — accepted after a pass2 variance rerun, not a redesign

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 17 checks green, `accepted` label |
| **Repo** | `dynamo-a3ab813-systems-infrastructure-and-operations`, branch `submission` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-a3ab813-systems-infrastructure-and-operations/pull/1 |
| **Category / sub** | Systems Infrastructure and Operations / Virtualization and emulation (pre-seeded) |
| **Benchmarked model** | reported as `Model A` |
| **Final commit** | `35adc2d` — "Close the content-keyed table channel" |
| **Headline** | **pass@5 = 0/5 solved, avg@5 = 0.000, 3 good-valid-fail, 2 in-progress-timeout.** pass@2 = 1 solved · 1 valid-fail on the accepting run. `qc_gate`: "No blocking soundness defects — 37 checks + probes ran clean." |

The task passed every gate on **commit `35adc2d`**, but the *first* pipeline run on that exact
commit (run `32755939589`) had `pass2` come back `1 solved · 0 valid-fail · 1 in-progress-timeout`
— a non-passing result with **zero task changes involved**. Closing and reopening the PR to
re-trigger the pipeline on the unchanged SHA (run `32774780326`) produced `1 solved · 1
valid-fail`, and every downstream gate then passed on the first try. The lesson this task adds to
the corpus: **`pass2` is measurably high-variance on byte-identical agent-visible content**, and
the fix for a single non-passing `pass2` run is to rerun it, not to touch the task.

---

## 1. What the task asks

A withdrawn HYDRA-9 telemetry concentrator runs under a plant emulator. Its board memo
(`task/environment/data/docs/HYDRA9.md`) names the fitted real-time clock as an
**MC146818A-compatible** part and documents the board around it: a 4-port bus window, a 16-bit
interrupt-edge counter, reset state, the 32.768 kHz time base, and both capture JSON schemas —
without restating the part's own programming model.

- **Agent sees:** `instruction.md`, `HYDRA9.md`, three rig bus captures with inline `bus_reply`,
  and `/app/model.py` — a **partial port** of the clock/calendar device model, presented as the
  model already in service (not flagged as broken).
- **Agent produces:** a finished `/app/model.py`, invoked to emit register bytes for a bus
  capture; interface (stdlib-only, single file) fixed by the port already on disk.
- **Graded on:** exact integer byte equality against 16 held-out bus captures (`h01`–`h18`, some
  numbers unused) not present in the image, computed in-process from a sealed, independently
  written ground-truth model (`tests/_device.py`).

The port reproduces all 3 shipped rig captures byte-for-byte (a green self-check gives no signal
anything is wrong) and fails 7/16 graded captures.

---

## 2. The crux, and the invariants that keep it alive

**Invented board, real part.** The board is fictional (HYDRA-9); the fitted part is real and
named (MC146818A-compatible), so the agent's difficulty is auditing a plausible-looking port
against the *published part's* behavior, not reverse-engineering an invented spec.

Six decisive rules are graded. The shipped port gets four right and departs on two:

| # | Rule | Port status |
|---|---|---|
| 1 | 12-hour hour encoding — hour 0 **and** hour 12 both encode as twelve, never 0 | **WRONG** (`h % 12`) |
| 2 | rate-select table — codes 1 and 2 are 128/256 counts, not a doubling series | correct |
| 3 | alarm field ≥ `0xC0` is a don't-care, not compared at all | **WRONG** (compares for equality) |
| 4 | first calendar step is half a second after divider release | correct |
| 5 | update-inhibit skips a step without stopping the chain | correct |
| 6 | flags set regardless of enable bits; enables gate only the pin | correct |

This started as a 6-departure port (§7) and was cut to 2 after pass@5 showed 6 departures gives
agents too much surface to diagnose-but-not-finish inside the clock (see §6, `low_timeout`).

**Invariants that must never break:**
1. The 3 shipped rig captures never exercise rules 1 or 3 (`tools/build_captures.py` asserts this
   — the port must reproduce all 3 rig captures byte-identically despite being wrong).
2. Each wrong reading is caught by **≥2** of the 16 graded captures (redundant coverage; no rule
   rides on a single test).
3. The 2 moot variants (update-in-progress transient, edge-counter saturation) change nothing on
   any capture — they are stated as data-shape guarantees in the memo instead of graded, because
   no capture can observe them (found by `qc_gate` C3, see §5).
4. `solution_explanation`'s departure count matches the actual diff, mechanically asserted by
   `tools/build_captures.py` (a text-substitution mismatch here failed the rubric twice — §6).
5. `solution/model.py` (reference) ≡ `tests/_device.py` (sealed ground truth, second independent
   implementation) on all 19 captures.

---

## 3. Dead ends — every approach tried that failed, with the grader's own wording

**Raising `[agent].timeout_sec` past 3600 (tried 7200, then 5400).** `pass2`'s agent-run budget
**caps at 3600s regardless of `task.toml`** — it does not scale with the requested value. At
5400s the trial recorded `override_timeout_sec=3600.0`, cutting the agent off 1500s (25 min)
early relative to what it was told it had, and the analyzer classified the result as
**`task/verifier-issue`** — a *harder* block than a plain timeout FAIL:

> "Both pass@2 trials failed solely because the run applied `override_timeout_sec=3600.0`
> (recorded in `pass2-output/32684016766-pass2/config.json` and each trial's `result.json`)
> against the task-specified `[agent].timeout_sec = 5400.0`... a 1500s (25 minute) shortfall."

The pipeline's own `pass2-difficulty-suggestion` bot then recommended raising the timeout further
— and that recommendation is wrong for this specific gate; it doesn't know about the 3600s cap.
Reverted to 3600 (commit `b99e17d`, "Put the budget back to 3600 and name the graded artifact").

**Redesigning against pass2 timeouts, four rounds.** Multiple task-shape changes were tried to
"help" agents finish inside the clock before the actual root cause (pass2 variance, not task
weight) was identified. Wasted cycles; none of the redesigns were the fix.

**Telling the agent the port was unvalidated / "still comes out wrong".** Guaranteed exhaustive
hunting across the whole file until timeout, because the agent had no reason to stop once it
found *a* bug — it kept looking for more. Reverted; `instruction.md` now presents the port as
already in service. **Do not reintroduce a "this is broken" framing for a partial-port task.**

**6 port departures (commit history `25f8452` → `6feba73`).** At pass@5 agents correctly *named*
the remaining bugs in their reasoning but ran out of time typing/deploying the fix — recorded as
`in-progress-timeout`, which counts for nothing toward the pass@5 bar. Cut to 2 departures
(`6feba73`, "Leave the port wrong in two places, not six").

**Blanket "five"→"six" text substitution when the departure count changed.** Failed the rubric
twice because the prose in `solution_explanation` drifted out of sync with the actual code diff.
Fixed by making `tools/build_captures.py` assert the count mechanically instead of relying on a
manual find-and-replace.

**Never writing a file (early design, "write the model from scratch").** Trials showed a mode
where the agent explored extensively and never produced `/app/model.py` at all. Replaced by
shipping the partial port for the agent to *finish* rather than *write* — this is what actually
unblocked `pass2` the first time it passed (commit `c4e2706`).

---

## 4. What actually worked, and why

**Ship a partial, plausible-looking port instead of an empty file or a flagged-broken one.**
Gives the agent a concrete artifact to audit against the named real part, converting "explore an
empty directory" into "verify six behavioral rules," which is the actual intended difficulty.

**Cut departures from 6 to 2.** Two independent, individually-checkable rules gave agents enough
to find *and* enough clock left to fix and redeploy. Six gave them enough to find but not enough
to land, producing uncountable `in-progress-timeout` results instead of countable failures.

**Rerun `pass2` on an unchanged SHA when it returns a single in-progress-timeout with
`difficulty_crux=PASS`.** This is the actual accepting move for this task (see header). Verified
twice in this task's history that identical agent-visible bytes produce different `pass2`
verdicts (`7d9e904` FAILED, `c6fc98e` — byte-identical `instruction.md`/`environment/` — PASSED;
and again `32755939589` FAILED → `32774780326` PASSED on literally the same commit `35adc2d`).

**Coverage audit over hand-picked mutants.** `tools/coverage_audit.py` replays every graded
capture under every single-decision mutation of the reference model (each integer literal
perturbed, each comparison/boolean flipped) instead of trusting a hand-picked mutant table. First
run found **90** unguarded decisions, not the 3 QC had sampled — see §5.

---

## 5. Gate-by-gate log, in the order things actually broke

| Gate | Verdict | Fix | Commit |
|---|---|---|---|
| Static checks / duplicate check | pass (first time) | — | — |
| Dynamo eval (rubric, 31 criteria) | pass (first time) | — | — |
| `changes`/`cosine_similarity`/`similarity`/`review`/`validation`/`ratelimit` | pass every run | — | — |
| Docker/Oracle/Nop validation | pass (oracle 1.0, nop <1.0) | — | — |
| `pass2` (early rounds, budget=7200/5400) | FAIL → `task/verifier-issue` | revert timeout to 3600 | `b99e17d` |
| `pass2` (6-departure port) | FAIL / uncountable (in-progress-timeout) | cut to 2 departures | `6feba73` |
| `pass2` (told agent port was "wrong") | FAIL (exhaustive hunting) | present port as in-service | `b3ba63e` |
| `qc_gate` — C3 narrow/hardcodable held-out coverage | BLOCK | built `tools/coverage_audit.py`; grew graded set 12→17 captures; moved 2 unobservable decisions to memo guarantees | `e6bb529` |
| `qc_gate` — E1 oracle/answers readable by agent | BLOCK | removed answer directory; rig captures carry `bus_reply` inline; graded captures carry no reply | `e6bb529` |
| `qc_gate` — E2 immutable-input integrity | BLOCK | SHA-256 archive digests + `O_NOFOLLOW`; 3 tamper probes | `e6bb529` |
| `qc_gate` — B2 internal contradiction (reset-state memo claim) | BLOCK, "real bug, QC understated it" | rewrote memo to state reset *state*, not reset *bytes* (bytes are a deciding rule) | `7121ba0` |
| `sound_verifier` — identity-keyed table | found by `ava_review` | opaque `_token()` capture id | (kept, §7 of handoff) |
| `sound_verifier` — content-keyed table | found by `ava_review` | verify-time scratch-memory epilogue | `35adc2d` |
| `pass2` on `35adc2d`, run `32755939589` | **FAIL** — 1 solved · 0 valid-fail · 1 in-progress-timeout, `Rerun Recommended: YES` | reran, no task change | close/reopen PR #1 |
| `pass2` on `35adc2d`, run `32774780326` | **PASS** — 1 solved · 1 valid-fail | — | (same commit) |
| `ava_review`, `deep_review`, `tier1`, `qc_eval`, `qc_exec`, `qc_gate` | pass (first time, this run) | — | — |
| `trials` (pass@5) | **PASS** — 0 solved · 3 good-valid-fail · 2 in-progress-timeout · avg@5=0.000, all 7 rubric criteria clean | — | — |
| Final `gate` | pass, PR labeled `accepted` | — | — |

---

## 6. Error → what to do, and what NOT to do

**Symptom: `pass2` FAILs with exactly one non-passing trial, that trial has
`difficulty_crux=PASS` and `low_timeout=FAIL`, and the bot itself says
`Rerun Recommended: YES`.**
- **Do:** verify no run is in flight (`gh run list --limit 1 --json status`), then
  `gh pr close <n> && gh pr reopen <n>` to re-trigger on the same SHA. This is the gate's own
  recommendation and it worked on the first retry here.
- **Do NOT:** touch `task/` in response to a single such result. Two independent instances in
  this task's history proved `pass2` swings PASS/FAIL on byte-identical agent-visible content.
- **Do NOT:** raise `[agent].timeout_sec` past 3600 in response to a `low_timeout=FAIL`. It caps
  at 3600 regardless of what `task.toml` requests, and pushing past it turns a soft-FAIL into a
  hard `task/verifier-issue` block (§3).

**Symptom: `pass2`/`trials` return `in-progress-timeout` instead of countable failures.**
- **Do:** reduce the amount of work the port leaves the agent, i.e. fewer departures/rules to
  fix — this task went from 6 departures (uncountable) to 2 (countable, 3/5 valid-fail).
- **Do NOT:** add more rules, and do NOT raise the timeout. Both were tried; both make the
  in-progress-timeout problem worse, not better, because agents correctly diagnose more surface
  than they can finish typing/deploying inside a fixed clock.

**Symptom: `qc_gate` finds a narrow/hardcodable coverage gap on a sampled mutant.**
- **Do:** build an exhaustive coverage tool (every single-decision mutation, not a hand-picked
  few) before patching the one instance QC found — it will very likely find more (90 here vs. 3
  sampled) and you'd otherwise fix one and get blocked again on the next.
- **Do NOT** patch only the specific mutation named in the finding; QC's evidence is a sample, not
  an exhaustive list.

**Symptom: `solution_explanation` prose drifts from the code diff after a departure-count
change.**
- **Do:** make the count assertion mechanical (`tools/build_captures.py` guard), not a manual
  find-and-replace across prose.
- **Do NOT** trust a blanket text substitution ("five"→"six") to keep prose and diff in sync —
  failed the rubric twice here before the guard was added.

---

## 7. Bugs I introduced myself

**Reset-state memo contradiction (B2, §5).** The memo claimed the register file reads `0x00` at
every index except two — but in the shipped data the calendar registers hold nonzero values at
reset, and the hour register doesn't read back as zero at all (it sits in the part's own reset
data format). Writing the *correct byte* into the memo wasn't an option — that byte is one of the
deciding rules, and disclosing it would have handed the answer away. Fixed by stating the
reset **state** (calendar zeroed at day 1/month 1/year 00, alarm/scratch zero, register `0x0A`
holding `0x70`) and saying explicitly that what a read returns for that state follows from the
part's programming model — true, self-consistent, and it keeps the encoding where it belongs (an
inference the agent must make, not a fact stated outright).

**Blanket text substitution leaving `solution_explanation` inconsistent with the actual diff**
(§6) — twice, before the mechanical guard was added.

---

## 8. Process rules learned the hard way

- **`pass2` has a hard 3600s agent-budget cap independent of `[agent].timeout_sec`.** Confirmed
  twice by `override_timeout_sec=3600.0` appearing in trial `config.json`/`result.json` even when
  `task.toml` requested more. Don't fight it; design the workload to fit inside it.
- **`pass2` is high-variance on identical content.** Treat one non-passing `pass2` run with
  `Rerun Recommended: YES` as noise to be rerun, not a signal to redesign — confirmed twice on
  this task alone (`7d9e904`/`c6fc98e`, and `32755939589`/`32774780326` on the *same* commit).
- **Never push while a pipeline run is in flight** — checked with
  `gh run list --limit 1 --json status --jq '[.[]|select(.status!="completed")]|length'`
  before every trigger.
- **`README.md` must be updated in the same commit as any `task/` change** — a strict pre-push
  gate; review the complete diff before pushing.
- **Regeneration order matters:** `tools/build_captures.py` writes `archive_digests.json` last;
  rerun it after any edit to `task/environment/data/` or `test_archive_unmodified` fails on a
  stale digest.
- **`git config` identity must be set per freshly forked repo** before the first commit —
  `Pruthviraj Gundadi <g.pruthviraj2002@gmail.com>`, never the session's ambient account context.

---

## 9. A reusable checklist for the next task

1. If the crux is "audit a plausible port/implementation against a named real external spec,"
   ship the port **partial and presented as in-service**, never flagged broken — a flagged-broken
   framing turns the agent into an exhaustive bug hunter that never stops early.
2. Keep the number of silent departures small (2, here) once pass@5 shows agents diagnosing more
   than they can land inside the fixed agent-budget cap. `in-progress-timeout` counts for
   **nothing** — it is not a countable failure, no matter how close the agent was.
3. Build the mutation/coverage audit tool (every single-decision mutation replayed against every
   graded fixture) *before* `qc_gate` asks for it — it will very likely find more gaps than a
   hand-picked mutant table would, and building it once avoids a second QC cycle.
4. Assert prose-vs-diff consistency (departure counts, rule counts) mechanically in the build
   tool; don't rely on manual text substitution across a memo/explanation.
5. When a memo needs to describe reset/initial state and the actual byte value is itself a
   graded/deciding rule, describe the *state*, never the byte — state the programming-model fact
   that determines the byte, not the byte.
6. On a single non-passing `pass2` run with `Rerun Recommended: YES` and no other gate signal:
   verify no run is in flight, close/reopen the PR on the unchanged SHA, and wait. Do not touch
   `task/`.
7. `[agent].timeout_sec` in `task.toml` should stay at what `pass2`'s actual cap allows (3600s
   observed here) — raising it past the cap produces a harder `task/verifier-issue` block, not
   more agent time.

---

## 10. One-paragraph version for future me

A withdrawn HYDRA-9 board's clock/calendar model ships as a plausible-looking partial port of a
named real part (MC146818A-compatible); the agent must find and fix two silent departures (12-hour
hour encoding, alarm don't-care ≥0xC0) among four correct rules, graded byte-exact on 16 held-out
captures the shipped port fails 7 of. It took the usual QC cycle (C3 coverage, E1/E2 tamper
independence, a B2 reset-state contradiction, two `sound_verifier` table-keying closures) plus one
earlier round of learning that `pass2`'s agent budget hard-caps at 3600s regardless of
`task.toml` and that 6 silent departures produce uncountable `in-progress-timeout` results where 2
produce countable failures — but the move that actually closed it out was recognizing that a
single `pass2` FAIL with `Rerun Recommended: YES` and `difficulty_crux=PASS` on the sole failing
trial is gate noise, not a task defect: closing and reopening PR #1 on the byte-identical commit
`35adc2d` turned `pass2` from FAIL to PASS with zero task changes, after which every remaining
gate — including `trials`, the one gate this task had never cleared — passed on the first try
(pass@5 = 0/5 solved, 3/5 good-valid-fail, avg@5 = 0.000).
