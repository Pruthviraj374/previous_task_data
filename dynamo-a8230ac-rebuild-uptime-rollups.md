# dynamo/rebuild-uptime-rollups — six consecutive runs died in a vendor outage, not in the task

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 17 checks green, `accepted` label |
| **Repo** | `dynamo-a8230ac-data-querying-and-databases`, branch `submission` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-a8230ac-data-querying-and-databases/pull/3 |
| **Category / sub** | Data Querying and Databases / Analytical queries (pre-seeded) |
| **Benchmarked model** | `task.toml`: `model_tested = "Opus-4.8"`, `agent_tested = "Terminus-2"`; the `trials` runner logged `adhoc • terminus-2 • deepseek/deepseek-v4-pro` |
| **Final commit** | `11bba90` (21 pushes, 24 commits) |
| **Headline** | **pass@5 = 1/5 solved, 4 valid fails, avg@5 = 0.200.** Bar is ≤2/5. `reward_hacking` clean 5/5, `approach_validity` 5/5, `task_specification` 5/5 |

Two findings this task exists to record.

**One: classify a CI failure by reading the job log, or you will redesign a task that works.**
Six consecutive runs (pushes 15–20) came back red. Every one of them died in a *comment-writing*
step, and in each the gate wrapped around that step had already returned PASS. The cause was a
single GitHub incident. The task tree that finally scored 1/5 is **byte-identical** to the tree
that had been sitting there since push 15 — nothing was fixed, because nothing was broken.

**Two: of the two withheld axes, the one I could not stop defending did nothing, and the one I
nearly lost to a gate did everything.** All four pass@5 failures landed on axis F. Axis E, which
cost roughly eight pushes and three separate `qc_gate` blocks to keep alive, gated **zero** trials.

---

## 1. What the task asks

MERIDIAN is a withdrawn vendor product that published monthly service-availability rollups. The
vendor is gone and took the reporting with it; one period's rollup survives with the bundle it was
computed from.

- **Agent sees:** `instruction.md`, `/app/warehouse/2024-03/` (a six-file bundle),
  `/app/reports/2024-03.json` (the rollup MERIDIAN published for it), `/app/MERIDIAN.md` (the
  vendor's own note on the bundle format).
- **Agent produces:** `/app/rollup.py`, invoked `python3 /app/rollup.py <bundle_dir> <out_json>`.
- **Graded on:** the shipped period plus **eight held-out bundles**, `tests/` overlaid at verify
  time, all-or-nothing across 12 tests.
- **Output:** `period_id`, `services` (per `service_id`), `tiers` (per tier name), each entry
  exactly `covered_seconds` and `unavailable_seconds`.
- **Exact integer equality, no tolerance anywhere** — the whole report is a count of seconds.

A bundle is `period.json`, `services.csv`, `tier_history.csv`, `exclusions.csv`, `incidents.csv`,
`revisions.csv`. Every interval is half-open. The instruction states the machinery in full and
closes with a flat sentence: *"MERIDIAN followed standard availability-reporting practice
throughout; where a step has an established convention, it used that convention."*

---

## 2. The crux, and the invariants that keep it alive

Two withheld conventions carry the difficulty. Both are **inert in the shipped period by
construction**, so an agent that validates end-to-end against `/app/reports/2024-03.json` sees green
and stops.

| Axis | Withheld convention | Why it is invisible in the shipped period |
|---|---|---|
| **E** | A rollup published as the period closed carries the incident times the books held *then*. A correction in `revisions.csv` with `recorded_at` after the close was never in it. | Every shipped correction landed before its close. |
| **F** | `exclusions.csv` holds the windows the platform *recorded*. Only work announced ahead is **scheduled** maintenance, and only scheduled maintenance is subtracted from covered time. | The one unannounced window (`mw-0005`) is nested inside an announced one (`mw-0004`), so subtracting it changes nothing. |

Four further conventions (incident union, maintenance/in-service clipping, pre-period incidents,
uncleared incidents) are withheld too, and agents get them right. Tier aggregation (D) and the
correction-cutoff boundary are **stated**, not withheld — `qc_gate` required both.

**Invariants that must not break** (each is one commit from breaking by accident):

1. **Every wrong reading is byte-identical on the shipped period.** Not merely untested — identical.
   `tools/calibrate.py` asserts this for all six crux misreadings.
2. **Each wrong reading breaks held-out periods.** E breaks 8 of 8, F breaks 5 of 8, and the four
   secondary axes break 4–5 each.
3. **Three rival readings left unsaid are moot on all 9 bundles** (`cutoff_read_inclusively`,
   `clip_maintenance_to_period`, `uncleared_ends_at_period_end`). If a reading is *not* stated and
   *not* moot, it is an ambiguity the verifier punishes and a `qc_gate` B4 waiting to happen.
4. **Every stated step must break the shipped period.** Nothing disclosed may be underdetermined by
   the sample. `mutants.sh` runs the machinery in reverse to prove it.
5. **The data-shape guarantee sentence** — *"No other timestamp in a bundle coincides with the
   period's `start` or `end`"* — plus its `calibrate.py` enforcement. This is what ended the
   correction-boundary loop (§3).
6. `mw-0005` stays nested inside `mw-0004`. Un-nest it and axis F becomes visible in the sample.

---

## 3. Dead ends, with the grader's own wording

### 3.1 Difficulty in interval arithmetic alone — pass@2 **2/2 solved**

First design put all four axes in the interval algebra (union, clipping, pre-period, tier split).
Graders: *"derivable from first principles."* Replaced wholesale. This is the corpus's most-repeated
lesson (`motion-register` §3, `experiment-analysis-frame`) and I paid for it again anyway.

### 3.2 The correction-cutoff boundary — three configurations, three different blocks

The single most expensive dead end. Whether a correction recorded exactly *on* the period close is
in or out:

| Configuration | Blocked by |
|---|---|
| Boundary absent from the fixtures | `qc_gate` **B5** — underdetermined |
| Boundary present but inert | `qc_gate` **C3** — mutating `<` to `<=` passed everything |
| Boundary present and discriminating | `qc_gate` **B1 + B4** — contradicts the instruction |

Every configuration is blocked by a *different* check, so each fix reopened another. Flipping the
cutoff to inclusive (`<=`) was also wrong: it contradicted the instruction's own half-open sentence,
and B4 said so.

**What ended it: deleting the case rather than choosing a side.** Corrections were moved off the
close entirely, and the instruction gained the data-shape guarantee that no other timestamp
coincides with `start`/`end`, enforced in `calibrate.py`. There is now no boundary to argue about.
`tier1` accepted B1 and B5 on that guarantee.

### 3.3 Withholding the tier aggregation (D) — `qc_gate` B1 + B5

D is an **output definition**, not a field convention: the report has a `tiers` key, so how it
aggregates is part of the schema the agent is owed. Now stated verbatim — *"over the time each
service was assigned to that tier"* — and pinned by 5 held-out bundles because the shipped period
cannot pin it.

### 3.4 An AVA source screen for stdlib-only — not attempted

The corpus records three consecutive `ava_review` blocks on static screens
(`contact-export`, `audit-build-context`, `plate-rasterizer`). Not attempted. See §4.2.

### 3.5 Inventing a MERIDIAN-specific deviation from standard practice — deliberately not attempted

This was pass@2's own difficulty *suggestion*. The corpus rule: disclosed → the agent implements it;
undisclosed → `qc_gate` B5 blocks it. A vendor-specific quirk is unreachable by reasoning, so it is
not difficulty, it is a guess. Declining a grader's suggestion was correct here.

### 3.6 Restating an already-fixed guard to satisfy `tier1`'s diff window — rejected as cosmetic

`tier1` compares **only the diff since the last QC verdict**, so a carried finding must be touched in
every push until QC confirms it. The temptation is to restate. Each time, the guard was made
genuinely stronger instead — and each was then accepted.

---

## 4. What worked

### 4.1 A conditional rule the agent must *notice*, not recall

Both surviving axes are real, external, published, **conditional**, and reached by noticing a field
rather than remembering a table. `announced_at` is present in the CSV and named in `instruction.md`
("the platform schedules maintenance by announcing it to customers **ahead of the window**"). Nothing
is hidden — the rule is *dismissable*, which is the property that makes it fire. The pass@5 verdict
on the fifth trial says it exactly: *"the agent correctly identified the ambiguity around
`announced_at` but made a faulty deduction from the sample data and chose the wrong interpretation."*

### 4.2 `python3 -I` instead of a source screen

`ava_review` blocked push 14 on a real hole: running `python3 /app/rollup.py` puts `/app` on
`sys.path[0]`, so a solver could split logic across files in `/app` and import them, defeating "only
`/app/rollup.py` is graded". The fix is interpreter isolation, not an AST deny-list. Cleared
`ava_review` and never came back.

### 4.3 Grading the shipped period against a sealed baseline

`/app/reports/2024-03.json` is the agent's self-check, so the verifier must not grade against it —
otherwise a program that copies the file scores 1.0. At verify time `/tests` **and** `/app/reports/`
are sealed, and the shipped period is graded against `tests/shipped_expected.json`, which the
program cannot reach. This is `merge-lora-adapters`' finding applied directly.

### 4.4 Four local checks that replace guessing

Run before every push; between them they caught more than the gates did:

```
cd task && python3 tools/calibrate.py     # "all calibration checks passed"
bash tools/mutants.sh                     # reference 12/12; rival readings moot 12/12
harbor run -p . --agent oracle            # 1.000
harbor run -p . --agent nop               # 0.000
```

`mutants.sh` drops each deliberately-wrong reading at `/app/rollup.py` inside the built image with
`tests/` overlaid and runs the **real** verifier. It is the only thing that proves a crux reading
actually fails, and it caught two README numbers that had silently drifted from the code.

---

## 5. Gate-by-gate log

| Gate | Verdict | Fix |
|---|---|---|
| `changes` (static) | passed throughout (25/25) | — |
| `similarity` / `cosine_similarity` | **UNIQUE**, passed first time and every time | — |
| `review` (rubric) | passed; final run **30 PASS / 1 N/A, "Failures: None"** | never blocked |
| `validation` | Docker ✅ Oracle ✅ Nop ✅ throughout | — |
| `pass2` | 2/2 solved on design 1; then **0/2 on seven of eight measured rounds**, 1/2 once | redesign (§3.1) |
| `deep_review` | passed every time it ran | — |
| `ava_review` | **blocked twice** — `verifier_coverage` (fixture gap), then `/app` on `sys.path` | added `h03`/`h07`/`h04` shapes; `python3 -I` |
| `tier1` | held 3× on findings outside its diff window | strengthen the guard, never restate it |
| `qc_eval`, `qc_exec` | passed whenever reached | — |
| `qc_gate` | **blocked 5×** — B1, B4, B5, C3, in rotating combinations, mostly the correction boundary | §3.2, §3.3 |
| `trials` | **never executed until push 21**, then 1/5 | it was the outage, not the task |

**Pushes 15–20: six consecutive red runs, none caused by `task/`.**

| Push | Died at | Error | What the gate had already returned |
|---|---|---|---|
| 15 `d8e7cdb` | `review` → `.dynamo/report.sh` | `Resource not accessible by integration` | — |
| 16 `082ed09` | same, twice in one run | same | — |
| 17 `6030b3d` | `changes`, before any check | `429` fetching `actions/checkout` | — |
| 18 `4e9147d` | `pass2` → "Post pass@2 comment" | `503` | 1 solved + 1 valid fail |
| 19 `281e9f4` | `deep_review` → "Post Automated Review comment" | `503` | `**Verdict:** PASS`, "proceeding to pass@5" |
| 20 `eead068` | `review` → `.dynamo/report.sh` | `gh: … (HTTP 503)` | `Verdict: PASS (all criteria pass / only N/A)` |

GitHub's status page: **one incident, opened `2026-08-17T13:40:03Z`**, `Issues` (the API PR comments
are written through) `degraded_performance` throughout, `API Requests` reaching `major_outage`. All
six runs start inside it, the first three minutes after it opened. Push 21 on an unchanged `task/`
went green on all 17 checks.

---

## 6. pass@5, and what the model actually did

**1/5 solved, avg 0.200.** Judge criteria: `task_specification` 5/5 PASS, `reward_hacking` 5/5 PASS
(*"No evidence of cheating across any trial"*), `approach_validity` 5/5 PASS, `refusals` 5/5,
`low_timeout` 5/5 (agents finished in 6–10 min against 3600s), `difficulty_crux` 4 PASS + 1 N/A.

**All four failures landed on axis F. Axis E gated nothing.**

| Trial | Reward | Root cause |
|---|---|---|
| 1 | 1.0 | all 12 tests passed |
| 2 | 0 | *"systematically computing `covered_seconds` too low"* — failed h02, h04, h06, h07, h08 |
| 3 | 0 | *"misinterpreted 'scheduled maintenance' and subtracted ALL recorded exclusions (including unannounced windows) … when only announced windows qualify"* |
| 4 | 0 | *"edge-case trap — agent included all maintenance windows (announced and unannounced)"* |
| 5 | 0 | *"correctly identified the ambiguity around `announced_at` but made a faulty deduction from the sample data and chose the wrong interpretation"* |

Every failing trial failed the **same five** held-out periods — h02, h04, h06, h07, h08 — the exact
set `mutants.sh` predicted for `every_window_excluded`. The local mutant harness forecast the live
failure set precisely.

**The ranking was inverted.** Axis E cost ~8 pushes and three `qc_gate` blocks to defend and gated
nothing. Axis F — one nested window and one adjective — did all the work. This is
`filer-access-audit`'s finding repeated: *my* judgement of which axis will stump the model is not
evidence, and the axis that survives a gate fight is not thereby the one that matters.

---

## 7. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| A check is red | **Read the job log** (`gh run view --job <id> --log`). Find whether the *gate* returned a verdict or the *step around it* died | Do not read the PR sticky comments. Stickies here were up to 24h stale, and a session reported a false PASS from one. Date any sticky by its content |
| Failure is in a reporting step, or a 429/503 | Classify as platform. Re-trigger with a README-only commit recording what happened | **Do not touch `task/`.** Six runs here were platform-side; changing the task in response would have destroyed a design that scores 1/5 |
| Repeated CI failures with no task cause | Check `githubstatus.com/api/v2/summary.json` and probe the API directly | Do not keep re-pushing into a live outage — each push burns a rate-limited pass@2/pass@5 |
| `qc_gate` B5 "underdetermined" on a boundary case | Consider **deleting the case** — move the data off the boundary and state a shape guarantee | Do not rotate the boundary configuration. All three configurations are blocked by a *different* check; it loops |
| `qc_gate` B1/B5 on a withheld rule | Ask whether it is an *output definition* (owed to the agent) or a *field convention* (fair to withhold). State the former | Do not withhold anything the output schema depends on |
| `ava_review` blocks on stdlib-only / sandbox escape | Use interpreter or kernel isolation (`python3 -I`) | Do not add a source/AST screen. Four tasks in this corpus have now been blocked doing that |
| `tier1` holds a finding "outside the diff window" | Touch the finding in **every** push until QC confirms it, making the fix genuinely stronger | Do not restate an existing fix cosmetically. It is rejected as cosmetic |
| pass@2 2/2 solved | Change the *kind* of difficulty | Do not add held-out coverage of the axis you already have — coverage ≠ rate (`motion-register` §3(f)) |
| pass@2 swings 0/2 → 1/2 | Re-measure before acting | Do not redesign on a two-trial sample. The 1/2 here was variance; the next round returned 0/2 and pass@5 came in at 1/5 |

---

## 8. Bugs I introduced myself

1. **README numbers drifted from the code.** Two `mutants.sh` rows in the README
   (`first_correction_wins`, `ignore_in_service_dates`) no longer matched what the harness reported.
   Nothing failed — the README is reviewer-facing, so it just quietly lied. **Re-run the harness and
   diff its output against the README before every push**, rather than trusting the last transcription.
2. **Trusting the handoff's summary over the CI record.** The handoff said "four consecutive runs
   died in a reporting step" and framed a 1/2 pass@2 as an unresolved difficulty risk. Pulling the
   per-run failing-job list from CI showed the *real* shape: gates failing in rotation, and the last
   six deaths all in one outage. Ten minutes of `gh run view` reframed the whole task.
3. **Nearly redesigned a working task.** With six red runs and a "3/5 is plausible" warning, adding a
   third axis looked prudent. It would have changed a tree that had already passed every gate, and
   re-rolled every LLM-graded criterion. The evidence said hold.

---

## 9. Process rules confirmed or learned

- **Never push while any check is pending** — it cancels the run and burns a rate-limited pass@2/pass@5.
  `PEND=$(gh pr checks N | grep -c pending)`; push only at 0.
- **Never `git add -A`.** `harbor` writes `task/jobs/`, and a stray `jobs/` appears at the repo root
  when it runs from the wrong cwd. Stage explicit paths.
- **One push per round of work.** Hold improvements locally while a run is in flight; ship them with
  the next required change.
- **README.md is a strict pre-push gate.** A README-only fix pushed *later* re-triggers the whole
  pipeline, which on an accepted PR costs a rate-limited run and re-rolls every LLM-graded criterion.
- **Read the gate's EVIDENCE line, not its headline.** Several `qc_gate` headlines here were wrong
  while their evidence was correct.
- **When tightening any check, probe both sides in the same run** — the exploit must fail *and* the
  reference must still pass 12/12.
- `gh run rerun` returns **404** for a fork contributor and `/rerun` is admin-only. Re-triggering
  means pushing, which is why outage discipline matters.
- `gh pr checks` hits GraphQL and returns **503** during incidents. Retry 2–6×, and do not mistake a
  503 on your own query for a task problem.
- **Gate a push on a measured probe, not on the status banner.** GitHub still showed
  `Issues: degraded_performance` when the surfaces that matter probed 75/75 clean. The banner lags;
  probe Issues-REST and GraphQL directly and push on that.
- **`instruction.md` must not end with the "You have N seconds…" line** — it fails the rubric.

---

## 10. Reusable checklist

- [ ] Read §"Dead ends" and §"The crux" in every file here **before designing**, and survey again
      immediately before opening the PR.
- [ ] Crux is real, external, published, **conditional**, and **noticed rather than recalled**.
- [ ] Crux is **dismissable** — visible in the data, plausibly ignorable. Hidden is not the same as hard.
- [ ] **Two independent** withheld axes minimum; expect one to do all the work and not to know which.
- [ ] Every wrong reading is **byte-identical** on the sample, asserted in `calibrate.py`.
- [ ] Every wrong reading **breaks** held-out fixtures, proven by a mutant harness against the real verifier.
- [ ] Every rival reading you leave unstated is **moot on every fixture**.
- [ ] Every *stated* step **breaks** the sample — nothing disclosed is underdetermined.
- [ ] Anything the output schema depends on is **stated**, not withheld.
- [ ] No graded boundary case sits on a value an equality mutation can flip — or delete the case and
      state a shape guarantee.
- [ ] The self-check artifact the agent ships with is **sealed at verify time** and graded against a
      copy it cannot reach.
- [ ] Isolation is enforced by interpreter/kernel (`python3 -I`), never by a source screen.
- [ ] Held-out fixtures include the shapes the sample shows (mid-period commissioning, empty group).
- [ ] All four local checks green immediately before every push.
- [ ] README numbers re-derived from a fresh harness run, not transcribed.
- [ ] Retrospective written and indexed once `accepted` lands.

---

## 11. One-paragraph version for future me

A withdrawn vendor's monthly availability rollups, rebuilt from one surviving period plus the report
it produced; two withheld conventions decide it, and both are inert in that surviving period by
construction, so an agent that validates end-to-end against it sees green and stops. It reached
**pass@5 1/5** with all four failures on the same axis — *only maintenance announced ahead of time is
scheduled maintenance* — while the other axis, which cost eight pushes and three `qc_gate` blocks to
keep alive, gated nothing at all; assume your ranking of your own axes is wrong and keep both. The
correction-boundary loop is the expensive lesson: absent → B5, inert → C3, discriminating → B1/B4, so
stop choosing a side and **delete the case**, moving the data off the boundary and stating a shape
guarantee you enforce in `calibrate.py`. The costliest mistake was almost non-technical: six
consecutive red runs made the task look broken, and it was a **GitHub outage** — every one died in a
comment-writing step *after* its gate had returned PASS, and the tree that finally scored 1/5 was
byte-identical to the one that had been failing for six rounds. Read the job log, not the sticky;
classify platform-vs-task before touching anything; and when the platform is down, hold the push and
probe the API directly rather than believing the status banner.
