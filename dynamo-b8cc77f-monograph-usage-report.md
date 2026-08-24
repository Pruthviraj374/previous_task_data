# dynamo/monograph-usage-report — an axis the standard did not actually force blocked four rounds

| | |
|---|---|
| **Outcome** | **ACCEPTED** — 16 checks pass, 0 fail, `accepted` label |
| **Repo** | `dynamo-b8cc77f-data-querying-and-databases`, branch `submission` (fork `Pruthviraj374`) |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-b8cc77f-data-querying-and-databases/pull/1 |
| **Category / sub** | Data Querying and Databases / Analytical queries (pre-seeded) |
| **Benchmarked model** | `task.toml`: `model_tested = "Opus-4.8"`, `agent_tested = "Terminus-2"`; trials logged `Model A` on Daytona |
| **Final commit** | `07ff23c` (6 pushes) |
| **Headline** | **pass@5 = 0/5 solved, 4 good valid fails + 1 in-progress timeout, avg@5 = 0.000.** "Difficulty OK". pass@2 was 0/2 on every measured round |

Three findings this file exists to record.

**One: an axis that is not *forced* by the standard you cite will be rejected, repeatedly, in a
different costume each time.** The same defect was raised as `qc_gate` B1+B5, then the rubric
eval's `unambiguous` + `test_instruction_alignment`, then `qc_gate` B3, then B1+B5 again. Four
rounds, four rewordings of my defence, four rejections. The gate was right every time: COUNTER
R5.1 §7.3 says a session "is defined **any of the following ways**" and mandates no precedence
among four, so the session-id scoping I was grading was my choice, not the standard's. Cutting
it — and making the choice unobservable by construction — cleared the gate on the next run.

**Two: cite the clause verbatim in the reviewer-facing README, not just in your own head.** The
rubric eval failed `unambiguous` and named the exact evidence that would reverse it: *"If a
reviewer with authoritative COUNTER R5.1 knowledge established that keep-last … [is] mandated by
the standard, then #6/#13 would flip to PASS."* Quoting the MUST-level sentences in `README.md`
flipped it to 31/31 on the next push, with no change to the task's behaviour.

**Three: a ±1 divergence reads as a threshold artifact, not as your crux.** pass@2 returned a
valid failure with `near_miss` **FAIL** because every held-out period was out by only ±1–2
counts. The fix is more *witnesses of the same conventions*, never more conventions: 8 more
untracked visitors and two helper shapes took divergence to ±9 across 4–16 metrics per period,
and `near_miss` passed on both trials of the next round.

---

## 1. What the task asks

VELLUMGATE is a university press's ebook platform. Each month it exports its catalogue and raw
access log as a SQLite database, and the press must produce the COUNTER-conformant usage figures
it sends to subscribing libraries.

- **Agent sees:** `instruction.md`, `/app/data/export_2025-03.sqlite`, `/app/data/PLATFORM.md`
  (table/column meanings, named standard, no rule text), and `/app/data/audited_2025-03.json` —
  the audited report for that period, its end-to-end self-check.
- **Agent produces:** `/app/usage_report.py`, one self-contained standard-library file, invoked
  `python3 /app/usage_report.py <export.sqlite> <report.json>`.
- **Graded on:** the audited period plus **eight held-out periods**, 13 tests, all-or-nothing.
- **Output:** `period` plus one entry per catalogue title ordered by ISBN, each with
  `total_item_investigations`, `total_item_requests`, `unique_item_investigations`,
  `unique_item_requests`, `unique_title_investigations`, `unique_title_requests`.
- **Exact integer equality, no tolerance anywhere** — so no `difficulty_evidence` "threshold
  artifact" argument is available to anyone.

---

## 2. The crux, and the invariants that keep it alive

Two conventions, both stated at MUST level in the COUNTER Code of Practice Release 5.1, both
**inert in the audited period by construction** — an agent that validates end to end against the
shipped report sees green on a complete-looking self-check and stops.

| Axis | Convention | Wrong reading | Held-out periods it changes |
|---|---|---|---|
| **A** | §7.2 *"Any additional requests for the same URL within 30 seconds (**between clicks**) MUST be treated identically"* — the window runs between successive clicks, so a run collapses however long its span | anchor the window on the first click of a group | 4 |
| **C** | §7.3 — every one of the four session definitions is a date-and-hour slice of an identifier | a 30-minute inactivity window | 6 |

**Invariants, machine-enforced — `tools/generate.py` writes nothing if one breaks:**

1. Both crux readings are **bit-identical to the reference on the audited period**.
2. Each is caught by ≥2 held-out periods (actual: 4 and 6).
3. Every *machinery* reading (status filter, landing-vs-request, per-URL not per-item collapse,
   window size, period filter, per-session uniqueness, title roll-up, and **keep-first**) breaks
   the audited period, so the agent's own self-check rejects it.
4. Five rival readings left unstated are **moot on all nine exports**, including both
   session-establishment readings — that is what makes leaving §7.3's permissiveness unstated
   fair rather than underdetermined.
5. **No logged session spans a clock hour or a calendar date.** This is what makes invariant 4
   true; break it and the §7.3 precedence question becomes observable and the task unsound again.
6. No same-URL repeat gap falls in the 28–32s band, so `< 30` and `<= 30` cannot disagree.
7. The 30s threshold is pinned from **both** sides — a 27s repeat (collapses) and a 33s one (does
   not). `calibrate.py` sweeps 5s–90s every run and fails if the accepted range is
   non-contiguous, excludes 30s, or spans more than 8s. Measured: **27s–32s**.
8. One client address per visitor and back, so double-click grouping is identity-reading
   independent.

---

## 3. Dead ends, with the grader's own wording

### 3.1 Grading a session precedence the standard does not mandate — four rounds, four verdicts

The single most expensive dead end in this task. The axis: a logged `session_id` is scoped to the
calendar date with no hour component, unlike every other identifier.

| Round | Gate | Verdict text |
|---|---|---|
| 2 | `qc_gate` B1 | *"The session-derivation rule is stated only by delegation to 'established practice…'"* |
| 2 | `qc_gate` B5 | *"instruction.md … never names a standard"* |
| 3 | rubric eval #6 | *"neither disclosed … nor uniquely determined by the COUNTER R5.1 standard the instruction cites"* |
| 4 | `qc_gate` B3 | *"which member of a collapsed double-click run survives … is stated nowhere the agent can see"* |
| 5 | `qc_gate` B1+B5 | *"not uniquely forced by the named external standard — so multiple COUNTER-consistent, March-consistent interpretations produce [different outputs]"* |

Each round I answered in prose — first the flat "established practice" sentence, then naming the
standard, then quoting §7.3 — and each round the objection returned in a new form. **The gate was
right.** §7.3's "any of the following ways" is permissive; a conformant platform may key every row
on IP + user agent + date + hour even where a session id is logged.

**Do not** defend an axis by re-describing it. Apply the normative-verb test to your *own* axis
before designing around it: if the clause offers alternatives rather than mandating one, the axis
is not sound, and no amount of citation will make it so. `filer-access-audit` §3 says this
already ("a SHOULD with escape clauses or an under-specified fallback — drop it or confine the
data so the loose branch is unreachable"); I did not apply it to myself.

### 3.2 Withholding the authority's name — `qc_gate` B1+B5, round 2

Design 1 used the corpus's standard flat sentence (`replay-strata-plans` §3.2,
`rebuild-uptime-rollups`): *"VELLUMGATE follows established practice for scholarly-platform usage
reporting throughout."* QC blocked with the evidence line *"instruction.md … never names a
standard"*.

I had withheld the name deliberately, fearing agents would fetch §7.2/§7.3 and solve it. That
fear was wrong on the evidence: naming COUNTER R5.1 and enumerating none of its clauses cleared
B1/B5, and pass@2 stayed 0/2 on every subsequent round. This is `replay-run-histories` §4
confirmed in a second category — **name the authority, withhold only the occasion**.

### 3.3 Answering the eval's `unambiguous` FAIL with more disclosure — nearly repeated

The eval flagged `keep_earlier` as a "defensible alternative". The tempting fix is to state the
rule in `instruction.md`, which spends the axis (`lumenp` §3). What worked instead was quoting the
MUST-level clause in the **reviewer-facing** `README.md` — the eval had named that exact evidence
as what would flip the grade. Disclosure to the reviewer is not disclosure to the agent.

### 3.4 My own tooling arguing the gate's case for it

`tools/variants.py` described the crux readings as *"defensible-looking misreadings"*. The eval
**quoted that string back** as corroboration that the task was ambiguous. Wording in dev tooling
is read by graders. Each entry now names the clause it violates.

### 3.5 Adding mechanisms to raise difficulty — deliberately not attempted

pass@2 sat at 0/2 with 3+ live axes throughout. `request-preconditions` §3(e) and `lumenp` §3 both
say: hold the design and spend the cycle on the gate that actually failed. Every round's change
was a gate fix, never a difficulty addition. The one time difficulty needed strengthening
(`near_miss`), the fix was more witnesses of the *existing* conventions.

---

## 4. What worked

### 4.1 Refuting a rival reading with data, not prose

`keep_earlier` (which member of a collapsed run survives) drew B3. Rather than state it, the
audited period gained a repeat click either side of midnight followed by the same chapter's other
format twenty minutes later: keeping the earlier member splits those into two sessions instead of
one, so the shipped report refutes it directly. The shape is deliberately narrow — untracked
visitor, every §7.3 definition agreeing on it — so it settles that one question and leaks nothing
about the clock-hour slice. `restore-runbook-advisor` §3.2 confirmed in a second category.

### 4.2 Making an under-forced question unobservable instead of grading it

The escape from §3.1: guarantee no logged session spans a clock hour or a date, enforce it in
`generate.py`, and assert both session readings **moot on all nine exports**. The rival cannot
produce a different answer, so there is nothing to disclose and nothing to grade. `qc_eval`
returned PASS on the next run after three consecutive blocks.

### 4.3 Quoting the normative clause in the README

A read-only reviewer cannot fetch the standard. A table mapping each graded convention to its
verbatim MUST sentence turned `unambiguous` from FAIL to PASS with no behavioural change.

### 4.4 Witness amplification for `near_miss`

±1 on a small integer count reads as a rounding artifact. Eight extra untracked visitors, a
`hour_straddle` helper (one chapter read either side of a clock hour, once per visitor) and a
`click_run` helper (a three-click run per visitor) took divergence to **±9 across 4–16 metrics**
per period. `near_miss` PASS on both trials of the next round.

### 4.5 Five local checks that caught more than the gates did

```
cd task
python3 tools/generate.py    # refuses to write on a data-shape violation
python3 tools/calibrate.py   # inertness / discrimination / mootness + window sweep
python3 tools/mutants.py     # every reading through the REAL verifier in the image
python3 tools/probes.py      # 13 attacks actually performed
python3 tools/prepush.py     # static checks + README audit + docstring-drift guard
harbor run -p . --agent oracle   # 1.000
harbor run -p . --agent nop      # 0.000
```

`calibrate.py`'s window sweep found a hole **no gate had reached at that point**: a 45-second
double-click window was inert on all nine exports and would have scored 1.0. Found by chasing a
pass@2 analyzer claim rather than accepting it.

---

## 5. Gate-by-gate log

| Gate | Verdict | Fix |
|---|---|---|
| `changes` (static, 25) | **passed first time and every time** | `.dockerignore` and the ≤1500-token count clean from commit 1 |
| `similarity` / `cosine_similarity` | **UNIQUE**, passed every time | fingerprint 0.7887 → 0.8096 across rounds; instruction flat at 0.7150 |
| `validation` | Docker ✅ Oracle ✅ Nop ✅ throughout | — |
| `review` (rubric) | 31/31, then **FAIL** once on `unambiguous` + `test_instruction_alignment`, then 31/31 for the rest | §3.3 / §4.3 |
| `pass2` | **0/2 on every measured round**, always ≥1 valid fail, "Rerun Recommended: NO" | never a blocker |
| `deep_review` | passed every time it ran | — |
| `ava_review` | **blocked once** — `verifier_coverage`: `-I` does not drop system site-packages, so a program violating the stated stdlib-only requirement was accepted | added `-S`; §7.2 |
| `tier1` | passed every time | — |
| `qc_exec` | passed, then **blocked once** on stale test docstrings, then passed | §7.3 |
| `qc_eval` | **blocked 3×** (B1, B3, B5, C3 in rotation), then **PASS** | §3.1 → §4.2 |
| `qc_gate` | blocked 4× (once on a missing `qc-exec-results` artifact, not a verdict), then **PASS** | — |
| `trials` (pass@5) | **0/5, 4 good valid fails, avg@5 = 0.000, "Difficulty OK"** | — |

---

## 6. pass@5, and what the model actually did

**0/5 solved. 4 good-valid-fail + 1 in-progress-timeout. avg@5 = 0.000.** `task_specification`,
`reward_hacking`, `difficulty_crux`, `near_miss`, `refusals`, `approach_validity` PASS on all
five; `low_timeout` FAIL on one.

The analyzer's stratification:

- **4 of 5 never produced `/app/usage_report.py`.** *"The agent spent the entire 3600-second
  budget in reverse-engineering mode — inspecting the SQLite schema, running ad-hoc diagnostic
  Python snippets against `audited_2025-03.json`, and iterating over candidate counting-formula
  parameters — without ever transitioning to implementation."* Single reasoning calls consumed
  20–42 minutes of the 60.
- **1 of 5 was the designed failure.** *"Produced a functional `/app/usage_report.py` … but
  implemented two wrong COUNTER R5.1 rules: a 15-second fixed-anchor dedup where the first of a
  run survives … and a 30-minute inactivity session window … These errors were masked on the
  audited period for total counts — a calibration trap the task author explicitly designed — but
  produced large absolute errors on held-out exports"* (h06: 30 vs 14; h08: 48 vs 32).

**The honest caveat, for the next task.** Only 1 of 5 trials exhibited the intended
implement-then-diverge shape; the other 4 were non-delivery. The graders counted all four as
*good valid fails* and the gate as "Difficulty OK", so this was accepted — but a task whose
dominant failure mode is "ran out of budget before writing anything" is testing horizon as much
as insight. Doc 33's amplifier ideal is a *believable near-miss*, and non-delivery is the opposite
shape. The pattern was visible from round 3 and I tracked it without acting, because
`[agent].timeout_sec` was already at the 3600s cap pass@2 enforces regardless of `task.toml`, so
no lever existed. If a future task in this family shows the same, the lever is reducing the
*discovery* surface (fewer tables to explore before a draft is possible), not the crux.

---

## 7. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| A gate rejects the same axis in a new form each round | Re-read the clause and ask whether it **mandates** your reading or merely permits it. If permissive, cut the axis and make the choice unobservable | Do not re-word the defence. Four rounds were lost this way |
| `qc_gate` B5 *"never names a standard"* | Name the authority, enumerate none of its clauses | Do not keep the flat "established practice" sentence and hope; and do not then enumerate rules — that spends the axis |
| Rubric eval fails `unambiguous` naming a "defensible alternative" | Quote the MUST-level clause in the **reviewer-facing README**; the eval usually states the evidence that would flip it | Do not disclose the rule in `instruction.md` |
| A grader quotes your own dev tooling against you | Fix the wording — call wrong readings non-conformant and cite the clause each violates | Do not leave "defensible" / "plausible alternative" language in `variants.py` or metadata prose |
| `near_miss` FAIL on an otherwise valid failure | Add more **witnesses of the same conventions** so divergence is large | Do not add a new mechanism, and do not loosen grading |
| `qc_exec` blocks on a mutation "nothing catches" | Check whether your own docstrings still describe the fixture. A probe reads them as the stated requirement | Do not make an equivalent mutation catchable — that reintroduces the unsound axis |
| `qc_gate` fails in ~12s with `Artifact not found for name: qc-exec-results` | Read the step, not the verdict. The sticky says "Execution probes produced no output this run" — re-run | Do not change `task/` |
| `ava_review` `verifier_coverage` on a stdlib-only claim | `-I` is **not** enough — `-S` drops system site-packages. Measure both in the built image | Do not add an AST/source screen; five tasks have now been blocked doing that |
| An analyzer states a fact about a trial | Measure it against your corpus. Mine claimed a 15s window matched the audited period; it does not — but the sweep that checked it found a real 45s hole | Do not accept analyzer detail uncritically, and do not dismiss it either |

---

## 8. Bugs I introduced myself

1. **`grep -c` broke a `&&` chain and the commit never ran.** `PEND=$(… | grep -c pending)` exits
   1 on zero matches, so `git add && git commit` silently skipped and the push sent only the
   previous commit. Exactly `reduce-palaeomag` §7.3. Use `$(… | grep -c … || true)` then test.
2. **A mutant wrong in two ways at once.** `anchored_window` anchored the window *and* retained
   the earlier member, so the moment keep-first was refuted by the sample it went visible on the
   audited period and calibration failed. One error per mutant, always.
3. **Test docstrings drifted from their fixtures.** Cutting the session axis replaced h04/h05, but
   their docstrings still named the old shapes — and `qc_exec` blocked on it. Now every held-out
   docstring quotes its export builder verbatim and `prepush.py` parses both files and fails on
   drift.
4. **A nested heredoc inside `bash -lc` never ran.** The tamper probe silently no-opped, which is
   indistinguishable from a caught attack. Only the probe's own assertion caught it. Single-quoted
   one-liners for setup strings.
5. **Stale numbers in README/metadata after every regeneration** — test count, row counts, SHA-256
   pin, mutant reach, "Twelve tests". Caught each time only by reviewing the diff before pushing.

---

## 9. Process rules confirmed

- **Never push while a check is pending.** One exception taken deliberately: only
  `cosine_similarity` was in flight and `pass2` had not started, so cancelling cost no
  rate-limited slot. Check *which* job is pending before deciding.
- **Never `git add -A`.** Stage explicit paths; `harbor` writes `jobs/`.
- **Update the root `README.md` in the same commit as any `task/` change**, and re-derive every
  number from a fresh harness run rather than transcribing.
- **`instruction.md` must not carry the "You have N seconds…" line** — confirmed again.
- **`.dockerignore` in `environment/` from the first commit** — static passed 25/25 every round.
- **Set `user.name`/`user.email` in the repo's local config at clone time.**
- **A task accepted at pass@5 0/5 must not be pushed to again.** 0/5 is the ceiling; a push
  re-rolls all 31 rubric criteria plus `deep_review`/`ava_review`/QC for nothing.
- `gh pr checks` hits GraphQL and returns TLS/503 errors during incidents — retry, do not
  diagnose the task.

---

## 10. Reusable checklist

- [ ] Read §"Dead ends" and §"The crux" in every file here **before designing**; survey again
      immediately before opening the PR.
- [ ] For each candidate axis, check the governing clause's **normative verb**. Permissive
      ("any of the following ways", MAY, SHOULD) → not an axis. Do this before writing code.
- [ ] Name the authority in `instruction.md`; enumerate none of its clauses; repeat the sentence
      inside `/app` because the prompt is never a file in the image.
- [ ] Quote each graded convention's MUST-level sentence in the reviewer-facing `README.md`.
- [ ] Every crux reading **bit-identical** on the sample, asserted; every machinery reading
      **breaks** the sample; every unstated rival **moot on every export**.
- [ ] Pin every threshold from **both** sides and sweep it on every run.
- [ ] Held-out periods witness each convention **several times**, so divergence is large.
- [ ] Ground truth sealed (`chmod 700 /tests`) and the graded program run as `nobody` under
      `python3 -I -S`; probe the accept side in the same run as the reject side.
- [ ] Pin every path the instruction declares read-only — listing included — and resolve the whole
      path so a symlinked parent is rejected.
- [ ] Test docstrings quote their fixture builders; a pre-push check enforces it.
- [ ] All five local checks green immediately before every push.
- [ ] Retrospective written and indexed once `accepted` lands.

---

## 11. One-paragraph version for future me

A university press's COUNTER-conformant monthly usage report, rebuilt from one SQLite access
export plus the audited report for that period, graded on eight held-out periods with exact
integer equality. It reached **pass@5 0/5, avg@5 0.000** on two conventions — the repeat-click
window is measured *between successive clicks*, and a user-session is a clock-hour slice rather
than an inactivity window — both inert in the audited period by construction, so an agent that
validates end to end against the shipped report sees green and stops. The expensive lesson is
that a third axis, which I defended through four rejections in four different costumes, was never
sound: §7.3 defines a session "any of the following ways" and mandates no precedence, so I was
grading my own preference. Apply the normative-verb test to your own axes before designing around
them, not after the gate says so. What cleared each block, in order: naming the authority while
enumerating nothing; quoting the MUST-level clauses in the reviewer-facing README (the eval had
stated exactly that as the evidence that would flip it); refuting a rival with a shipped data
case rather than prose; deleting the under-forced axis and making the question unobservable by
construction; `-S` for the stdlib-only claim the instruction made and `-I` alone could not keep;
and making every test docstring quote its fixture after `qc_exec` caught mine drifting. Only 1 of
5 pass@5 trials produced any artifact at all — the other four burned the hour exploring — which
the graders counted as good valid fails, but is worth watching in any task with this much surface
to discover before a draft is possible.
