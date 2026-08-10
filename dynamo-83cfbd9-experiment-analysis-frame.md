# dynamo/experiment-analysis-frame — the crux that is *known* vs the crux that is *noticed*

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 17 checks green, `accepted` label |
| **Repo** | `dynamo-83cfbd9-data-science-and-reporting`, branch `submission` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-83cfbd9-data-science-and-reporting/pull/1 |
| **Category / sub** | Data Science and Reporting / Experiment and metrics analysis (pre-seeded) |
| **Benchmarked model** | reported as `Model A` / DeepSeek-V4-Pro (`task.toml` names Opus-4.8 / Terminus-2 — fixed dataset fields, not the model actually run) |
| **Final commit** | `4da05c8` (run `31392597630`) |
| **Headline** | **pass@5 = 0/5 solved, avg@5 = 0.000, 5 good valid fails.** Two runs earlier the *same* task scored pass@5 5/5, avg@5 = 1.000 |

33 pipeline runs, 28 commits. The last four rounds are the whole story: this task was
**solved 5/5 twice** and then failed 0/5, and the difference was not a new mechanism.

---

## 1. What the task asks

An experimentation platform was retired before its analysis-frame builder was ported. The agent
writes `/app/frame.py`, invoked `python3 /app/frame.py <export_dir> <out_dir>`, turning an archived
export into one CSV frame per experiment: one row per analysis unit, with the variant it was
measured under, the instant its measurement started, and its metric values.

- **Agent sees:** `instruction.md` and one sample export at `/app/data/export/` — **inputs only, no
  expected frames**.
- **Graded on:** the sample plus **eight held-out exports (27 experiments)**, all-or-nothing across
  11 tests.
- Frames are compared by parsed value: unit set and order exactly, `measured_from` as an instant,
  metric cells numerically within half the smallest unit the expected figure is reported in.

---

## 2. The crux, and the invariants that keep it alive

The task ended with **three** independent axes, any one of which zeroes the reward. What matters
is *why the third one worked when the first two did not*.

| Axis | Kind | Did it fail the model? |
|---|---|---|
| Point-in-time composition (bitemporal `frozen_at`, ITT, cross-unit layer exclusion, re-bucketing) | invented, fully disclosed | **No** — solved in every trial of two pass@5 runs |
| ISO 4217 minor units | real, external, **memorised** | Only after being made worth ×10 — see §4 |
| ISO 8601 nominal vs exact durations (`P2D` ≠ `PT48H`) | real, external, **counterintuitive** | **Yes** — 3 of 5 trials |

**The deciding rule.** `attribution` is an ISO 8601 duration. The standard splits a duration at
`T`: the part before counts calendar units, the part after counts fixed seconds. `P2D` is two
calendar days and `PT48H` is forty-eight hours, and they name the same span *only* where no UTC
offset change falls between the endpoints. Experiments carry an IANA `timezone`; three held-out
experiments use `P1D`/`P2D`/`P3D` in `America/Chicago`, `America/New_York` and
`America/Los_Angeles`, whose clocks move on 2026-03-08 inside the analysis window. There the
nominal form closes **an hour earlier in absolute terms** than the exact form of the same length.

**Invariants that must never break:**

1. **The shipped sample cannot reveal it.** Every sample window is an exact `PT` form and the
   sample's zone is `UTC`. A solver reading every duration as fixed hours reproduces all three
   sample frames exactly and has every reason to stop. *That concealment is the difficulty.*
2. **The instruction signposts without disclosing.** It says `attribution` is "an ISO 8601
   duration", gives the IANA `timezone`, and says a window "is long enough to run across a
   daylight-saving change in the experiment's `timezone`". It never says which form does what —
   because ISO 8601 already does, which is what keeps it out of `qc_gate` B5.
3. **The divergence is witnessed on both sides.** Each probe unit has activity inside the nominal
   deadline, inside the extra hour, and past both. The timed metric's **untimed sibling** reads
   the same rows, so the two readings differ on one column and agree on the other — a per-metric
   deadline, not a row filter.
4. **No fixture lands in an ambiguous or nonexistent local time.** Re-localising inside a DST gap
   is undefined-ish; the generator keeps every deadline clear of one.
5. **Sample is all `USD`** (exponent 2, the universal default), so the currency axis is equally
   inert there.

---

## 3. Dead ends — with the graders' own wording

### 3.1 Six invented, disclosed mechanisms → solved every time

`population`, `frozen_at`, the mutual-exclusion layer clause, `attribution_hours`, re-bucketing,
cross-unit translation. All invented by the task, all necessarily written down. pass@5 on
`3863917`:

> **pass@5: 5/5 passed** · `avg@5=1.000`
> *"All five agents converged on the same architecture and decisions, independently… No
> architectural variation was observed"* and *"the model has reliable training-data knowledge of
> bitemporal data patterns and experiment-frame export conventions, rather than deriving them
> purely from first principles."*

The graders were explicit this was **not** a spec defect — `task_specification` 5/5 PASS,
`reward_hacking` 5/5 PASS, zero near-misses. **Do not read a 5/5 as "the spec leaked".**

### 3.2 Withholding the consequences of an invented rule → 2/2 solved *and* QC findings

Naming only the premises of ITT and `frozen_at` (`f61e94c`):

> *"ITT and frozen_at are intentionally left to practitioner domain knowledge, which both agents
> possessed."*

It also triggered `qc_gate` B3/B4/B5. Worst of both: no difficulty gained, spec risk added.

### 3.3 A real external convention that is *memorised* → 2/2 solved

ISO 4217 minor units, with the rule spelled out ("the decimal places ISO 4217 gives that currency,
which is not always two"). pass@2 on `f8c8e90`: **2/2 solved**, both agents independently building

> *"identical `CURRENCY_DECIMALS` lookup tables"*

**Real and external is necessary, not sufficient.** They did not miss the convention — they were
told to go and fetch it, and fetching is what this model is good at.

### 3.4 The pass@2 difficulty suggestion, which was wrong for this task

After the 2/2 the automated suggestion said the instruction "is a near-complete solution
specification" and recommended restating the hardest semantics as *properties* rather than
*procedures*. That is §3.2, already measured here as a dead end. **Its *optional* item was the
good one** — "an additional export that layers three or more of the sample-absent mechanisms". Read
suggestions for the optional items too; the headline may be a repeat of your own failed round.

### 3.5 A real convention whose error is bounded by the tolerance → `deep_review` BLOCK

With money stored as a decimal amount, a wrong ISO 4217 exponent could only ever move a figure by
a fraction of a unit (`107.585` → `107.58`). pass@2 passed 0/2 but both trials scored
`near_miss` FAIL and `difficulty_crux` FAIL, and `deep_review` blocked:

> **`difficulty_evidence` (C)** — *"the empirical difficulty is a single ISO 4217 formatting
> near-miss, not the stated analytical crux… a pass rate driven by a tight numeric threshold /
> formatting near-miss rather than the intended challenge is a FAIL"*

This bound is **structural**: any exponent error on a decimal column is at most half a minor unit,
which is also the grading band. No choice of currency, tolerance or fixture escapes it.

---

## 4. What actually worked

Two changes, in this order. Both are about *magnitude* and *kind*, not about adding rules.

**(a) Make the external rule change the meaning of the input, not the spelling of the output.**
`events.csv` now stores money as an integer count of the currency's minor units, the way a ledger
does. The exponent is needed to **read** the column, not to format the answer. The same cents
assumption is now wrong by ×10 on a three-decimal currency and ×100 on a zero-decimal one, and
three things fell out that were previously impossible:

- `near_miss` and `difficulty_crux` flipped to PASS and `deep_review` cleared;
- `JPY` began discriminating at all (on a decimal column `120.00` sits 0.3 from `120`, inside a
  band of 0.5 — permanently inert);
- the *"just don't round"* escape closed, because an unscaled program emits `172603` where
  `172.603` is expected. Previously a solver that never rounded passed **every** experiment without
  consulting the standard at all.

**(b) Move the deciding rule from a fact to recall to a distinction to notice.** This came
straight from `dynamo-d5a485c-cron-window-counts` — the only comparable task in this corpus that
reached acceptance. Its crux was whether a cron field's **first character** is `*`, documented in
`cron(8)`, invisible in its sample; it returned pass@5 0/5. The property that transfers is not
"use a standard" but **the rule must be decided by a textual property of the input that an
otherwise-correct implementation will not think to check.** `P2D` against `PT48H` is that same
shape. An exponent table is recall; the nominal/exact split is a distinction.

**Final pass@5 (`4da05c8`): 0/5 solved, 5 good valid fails, avg@5 = 0.000**, stratified across
three modes — and notably, the currency axis *did* finally fire once it was worth ×10:

| Mode | Trials | Detail |
|---|---|---|
| ISO 8601 P-form read as fixed hours | 3 | `P1D`/`P2D`/`P3D` parsed as `timedelta(days=N)`; one agent *"explicitly reconsidered DST in step 16 and dismissed it as 'just informational'"* |
| ISO 4217 exponent table incomplete | 2 | Hardcoded a partial dict defaulting to 2; `OMR` absent → revenue ×10. One agent flagged the gap in step 21 (*"Let's add a more comprehensive currency exponent list"*) **then called `mark_task_complete` without applying it** |
| Terminal heredoc wedge | 1 | A ~600-line `cat > frame.py << 'PYEOF'` truncated at 10,000 bytes; shell stuck in PS2 for the remaining 42 minutes. No `frame.py` written |

Only one trial hit both analytical axes at once. **Two independent external conventions is why the
result is 0/5 rather than 2/5** — different agents failed on different ones.

---

## 5. Gate-by-gate log, in the order things actually broke

| Gate | First verdict | Fix | Commit |
|---|---|---|---|
| `changes`, `cosine_similarity`, `similarity`, `ratelimit` | pass throughout | — | — |
| static (`review`) | FAIL — `[task].description` missing | it is **required**; restored | `2226bcd` |
| static (`review`) | FAIL — instruction **1502** Qwen3 tokens, max 1500 | trimmed; see §7 | `f8c8e90` |
| `pass2` | FAIL 2/2 solved, ×4 separate designs | see §3.1–3.3 | — |
| `qc_gate` | FAIL ×4 rounds — C3 hardcodable coverage, B3 missing definition, B6 unstated data anomaly, E7 `__pycache__` oracle leak; later A6 oracle edge case, B5 underdetermined mapping | each fixed individually; B5 answered by *documenting the rule*, not by changing sample data | `3337a16`, `3863917` |
| `deep_review` | FAIL — `difficulty_evidence`, threshold artifact | §3.5 → §4(a) | `4d58d0f` |
| `trials` | FAIL 5/5 solved ×2 | §4(b) | `4da05c8` |
| `ava_review`, `tier1`, `qc_eval`, `qc_exec` | passed whenever reached | — | — |
| `gate` | pass on `4da05c8` → `accepted` | — | — |

**A `pass2` failure skips everything downstream** (`tier1`, `qc_*`, `deep_review`, `ava_review`,
`trials`), so a QC objection fixed while pass@2 is blocked never gets re-tested that round.

---

## 6. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| pass@5 **5/5 solved** with every rubric criterion passing | Believe it: the mechanisms are sound and simply known. Move the *deciding* rule to a real convention decided by a **textual property of the input**, and keep the existing machinery as the substrate | Do **not** rebuild the whole task. Four gates already approve of that machinery; ripping it out re-exposes `qc_gate`, which took four rounds to win |
| pass@2 2/2 on a task whose rules are all invented and disclosed | Move the deciding rule outside the memo to a published standard | Do **not** add a seventh invented mechanism, and do **not** withhold an invented rule — B5 blocks it |
| You moved to a real external convention and it was still solved | Ask whether the convention is **memorised** (an exponent table, a code list) or **noticed** (a syntactic distinction). Only the second discriminates | Do **not** conclude "real external conventions don't work" — conclude the *kind* was wrong |
| `deep_review` `difficulty_evidence` — "threshold / formatting near-miss" | Make the mistake change the **meaning of the input**, not the spelling of the output, so the error is orders of magnitude | Do **not** tighten the tolerance — grading on formatting trivia is a documented reject trigger, and the near-miss bound is structural anyway |
| A grading tolerance of "half the smallest reported unit" | Check what it makes **uncatchable**: correct rounding and no rounding differ by at most half a unit, so a non-rounding solver can never be caught, and a zero-exponent currency can never discriminate | Do **not** assume a variant that differs on N experiments fails N tests — re-score against the *verifier's* comparison, not a frame diff |
| pass@2 difficulty suggestion contradicts a round you already ran | Check it against your own dead-end list first; then read its **optional** items, which are often the useful part | Do **not** act on the headline because it is automated |
| `qc_gate` B5 "underdetermined / hidden-knowledge mapping" | Name the standard in the field description, keep `allow_internet = true`, and make the shipped sample witness the feature **inertly** | Do **not** answer B5 by changing the sample data to demonstrate the rule — that teaches the crux and regresses pass@2 |
| A fixture change "fixes" a QC finding | Re-measure the crux divergence table on the fixture afterwards | One fix here removed the transfer that separated a first-match scan from a real interval join, and silently deleted the only crux the model had missed |

---

## 7. Bugs I introduced myself

- **Estimated the token count with the wrong tokenizer and lost a whole cycle.** A cl100k-scaled
  estimate read 1479 when the truth was **1502**; `review` failed and every downstream gate
  skipped. The only reliable calibration point is the checker's own: **1496 cl100k measured as
  1502 Qwen3**, factor ≈ **1.0040**. Even with that factor, a later edit silently landed at
  **1513** and had to be caught pre-push. **Never push under ~20 tokens of margin; re-measure
  after every edit, not once at the end.**
- **Three harness patterns went silently stale** when `attribution_hours` was renamed to
  `attribution` — they matched nothing and tested nothing. Only the harness's own **no-op guard**
  caught them ("its pattern was silently a no-op, fix the pattern"). Two others had been reading
  the old decimal money column, and one rendered with a hardcoded `/100`, which had been
  **conflating the currency mistake into two unrelated variants' counts**. Every mutation and
  variant must assert its pattern still matches.
- **`oracle = 1.000` is nearly vacuous** when `solution/frame.py` is byte-identical to
  `tests/_reference.py`: it only proves the file equals itself. The real check is that the
  *harness* reference and the *shipped* reference agree on every fixture — verify that separately.
- **A new fixture initially produced a frame of zeros.** The probe's exposures were placed so late
  in the window that almost no traffic followed. A column of zeros looks like coverage and tests
  nothing.
- **A clause that was accidentally true.** The layer rule said a unit "both of them reached" ends
  up measured by neither — fine until an ITT experiment joined a pool, where units are measured
  without ever being reached. Found by building the fixture that breaks it, not by re-reading the
  prose. Rewritten population-neutrally as "whether or not it had reached that unit itself".

---

## 8. Process rules learned the hard way

- **Never push while a run is in flight**; one push per round of work. A push re-triggers
  everything and burns a rate-limited pass@2.
- **Read the QC sticky's `QC-BASE` against HEAD before believing it.** `QC-FIXES-B64:W10=` decodes
  to `[]` — zero blocking findings. A sticky can sit at a two-commit-old base and look current.
- **Bundle README/prose corrections with the next blocking fix.** A prose-only push on an accepted
  PR re-runs the whole pipeline and re-rolls every LLM-graded criterion.
- **Stage explicit paths**; `task/jobs/` is gitignored harbor output and will otherwise show up in
  greps as false positives for stale terms.
- `pass2_suggestion` **skipping** is a good sign — it skips when no difficulty suggestion is needed.
- Timings on the accepted run, for planning: `pass2` 37m, `trials` **1h02m**, `qc_exec` 18m,
  `qc_eval` 12m; whole run ≈ 2h.

---

## 9. Reusable checklist

1. Is the deciding rule **real, external and published**? If the task invented it, it must be
   disclosed, and disclosed rules get implemented.
2. Is it **noticed rather than recalled** — decided by a textual/syntactic property of the input
   (`P` vs `PT`, first character `*`), not by a table the model has memorised?
3. Does the shipped sample reproduce **exactly** under the naive reading? Prove it with a variant.
4. Does the instruction **name the standard and stop**? `allow_internet = true`.
5. Is the error **orders of magnitude**, not a fraction of the grading band? Re-score every
   variant through the verifier's own comparison, not a frame diff.
6. Do at least **two independent** external conventions decide the result? Different agents fail
   on different ones; that is the difference between 2/5 and 0/5.
7. Is each crux witnessed by **≥3 held-out experiments**, in more than one shape and more than one
   zone/currency?
8. Does every mutation and calibration variant **assert its pattern still matches** the source?
9. Do the harness reference and the shipped reference agree on every fixture?
10. Instruction ≤1500 **Qwen3** tokens with ≥20 to spare, re-measured after the last edit.
11. README and `task.toml` `[metadata]` re-read against the final diff — both restate the design
    independently and go stale silently.

---

## 10. One-paragraph version for future me

This task was solved **pass@5 5/5 twice** with a fully correct, fully disclosed bitemporal
analysis-frame spec, and the graders were consistent that nothing was wrong with it — the model
simply has strong training-data priors for bitemporal interval-join problems. Moving the deciding
rule to a real external standard (ISO 4217 minor units) was necessary but not sufficient, because
an exponent table is **memorised**: both agents built the lookup the moment the instruction told
them to, and when the instruction stopped telling them, the mistake was still only worth half a
minor unit, so `deep_review` blocked it as a threshold artifact. Two changes fixed it. First,
money moved into the input as an integer count of minor units, so the exponent is needed to *read*
the data and a wrong one costs ×10 or ×100 — which also made `JPY` discriminate for the first time
and closed the "just don't round" escape that had been passing every experiment for free. Second,
and decisively, the deciding rule moved from a fact to recall to a **distinction to notice**:
`attribution` became an ISO 8601 duration, where `P2D` is two calendar days and `PT48H` is
forty-eight hours and they diverge only across a DST transition that the shipped sample never
crosses. That is the same shape as the accepted cron task's first-character `*` test. Result:
**0/5, five good valid fails, avg@5 = 0.000**, with agents failing on *different* conventions —
three on the duration split, two on a currency exponent they had themselves noticed was incomplete
and shipped anyway.
