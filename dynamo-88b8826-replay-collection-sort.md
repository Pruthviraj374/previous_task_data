# dynamo/replay-collection-sort — the two axes added to satisfy a gate did nothing; the two designed first took all five trials

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 17 checks green, `accepted` label |
| **Repo** | `dynamo-88b8826-data-querying-and-databases`, branch `submission` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-88b8826-data-querying-and-databases/pull/1 |
| **Category / sub** | Data Querying and Databases / NoSQL and document stores (pre-seeded) |
| **Benchmarked model** | reported as `Model A` (`task.toml` names Opus-4.8 / Terminus-2 — fixed dataset fields) |
| **Final commit** | `a88caa7` (4 pushes) |
| **Headline** | **pass@5 = 0/5 solved, 5 good-valid-fails, avg@5 = 0.000.** Bar is ≤2/5. `difficulty_crux` PASS 5/5, `approach_validity` PASS 5/5, `reward_hacking` clean 5/5 |

Three findings worth the read.

**One: no gate ever objected to the crux.** `qc_gate` and `ava_review` blocked three times between them and *not once* on the withheld MongoDB rules. Both blocks were about **verifier soundness and coverage** — machinery, not difficulty. This is the opposite of `replay-strata-plans`, `monograph-usage-report` and `rebuild-uptime-rollups`, where B1/B5 fought the crux for four to eight pushes each. The reason is §2: the instruction names a public authority and enumerates nothing, so there is no "underdetermined" claim available to a discoverability gate — the rules are in the MongoDB manual, one lookup away, and the gate can see that.

**Two: my ranking of which axis would gate was wrong again, in the now-standard direction.** Four axes shipped. The two I designed the task around (empty-array ranking, array min/max by direction) caused **all five** failures. The two added later to satisfy gates (numbers-below-strings, added for `qc_gate` C3; the empty-filter fixtures, added for `ava_review`) gated **nothing** — every trial passed h09, h10, h11, h12. That is the fifth or sixth confirmation of this pattern in the corpus, but note the inversion: in `filer-access-audit` and `restore-runbook-advisor` the *cheapest/weakest* axis did the work. Here the axes added under gate pressure were the dead ones. **A gate-driven axis is coverage, not difficulty — do not expect it to gate, and do not count it toward your difficulty budget.**

**Three: four of five trials named the correct rule and then abandoned it after the sample went green.** The analysis quotes them reasoning "comparing the smallest elements of the array" and then shipping positional lexicographic comparison anyway. This is `accrued-interest`'s *"probably isn't being tested"* exactly, in a fourth category. The model is not missing the knowledge; the green self-check overrides it.

---

## 1. What the task asks

A MongoDB collection export and a list of queries survive; the agent must reproduce what the server would have returned.

- **Agent sees:** `instruction.md`, `/app/data/collection.json` (12 support-ticket documents: `_id`, `severity`, optional `priority_score`, optional `labels` array), `/app/data/queries.json` (two queries in `find(filter).sort(spec)` shape), and `/app/data/expected.json` — the correct result for those, its end-to-end self-check.
- **Agent produces:** `/app/query.py`, invoked `python3 /app/query.py <collection.json> <queries.json> <output.json>`.
- **Graded on:** the shipped sample plus **twelve held-out collection/query pairs**, `tests/` overlaid at verify time, all-or-nothing across 14 tests.
- **Output:** a JSON object keyed by `query_id`, each value the ordered list of matching `_id` strings.
- **Exact equality on an ordered list of identifiers. No tolerance exists anywhere** — so no `difficulty_evidence` "threshold artifact" argument is available to anyone. This was free here, unlike the integer-pipeline gymnastics `lumenp` and `reassemble-tap-sessions` needed: a permutation of ids has no numeric margin to argue about.

Disclosed in full: filter semantics, that an absent/empty filter matches everything, compound sort-field precedence, and the ascending-`_id` tie-break. Withheld: the comparison rules, behind one flat sentence (§2).

---

## 2. The crux, and the invariants that keep it alive

Four real, documented MongoDB/BSON comparison rules, none stated. The instruction says only:

> *"This collection is a genuine MongoDB export, and it sorts and compares field values exactly the way a real MongoDB server does."*

| Axis | Rule | Inert in the shipped sample because | pass@5 result |
|---|---|---|---|
| **1** | A missing field compares as `null`, the **lowest** rank — first ascending, last descending | the only shipped `priority_score` sort is descending, where "missing is lowest" and "missing goes last" agree | **gated nothing** (h01, h02 passed 5/5) |
| **2** | An **empty array ranks below null/missing**, not at the array type's slot | no shipped document has an empty `labels` list | **4 of 5 failures** (h03, h04) |
| **3** | An array field is represented by **one element chosen by direction** — min ascending, max descending — not positionally | every shipped `labels` array is already stored in ascending order, so `element[0] == min` | **5 of 5 failures** (h05, h06, h08) |
| **4** | A **number ranks below a string** | every shipped `priority_score` is a number; no shipped sort mixes types | **gated nothing** (h09, h10 passed 5/5) |

**Invariants, machine-enforced in `tools/generate.py` — it writes nothing if one breaks:**

1. the shipped sample is **bit-identical to the reference under all four misreadings** (not merely untested — identical, so the self-check is green under every wrong reading);
2. each misreading is caught by **≥2 held-out fixtures** (measured 6, 5, 2, 2);
3. every **disclosed** mechanic demonstrably breaks the shipped sample if dropped — the `_id` tie-break (which is why `T-002` is listed before `T-001` with an equal score) and the empty-filter rule. Nothing disclosed may be underdetermined by the sample;
4. the shipped `labels` arrays stay in ascending order. Un-sort one and axis 3 becomes visible in the sample and the task dies.

### The shape that made the gates cheap

`instruction.md` **names MongoDB as normative and enumerates no rule.** This is `replay-run-histories` §4 and `monograph-usage-report` §3.2 — *name the authority, withhold only the occasion* — and it is now confirmed in a sixth category. It cost nothing in difficulty: pass@2 was 0/2 on every round and pass@5 was 0/5, while `qc_gate` B1/B5 never fired once. Compare `replay-strata-plans` §3.2, where the same disclosure in a *louder register* ("everywhere it is silent…") took pass@2 from 0/2 to 2/2. The register rule holds: flat and descriptive, naming no area and giving no sign a gap exists.

---

## 3. Dead ends and gate fights, with the grader's own wording

### 3.1 `qc_gate` C3 — an axis I claimed in metadata but never graded

> *"Mutated the spec-faithful reference to swap the number/string type ranks (strings<numbers, violating the stated 'numbers then strings' ordering). Ran full verifier: 10 passed, reward=1. The mutation is caught by NO fixture because no held-out fixture ever places both a number and a string in the same…"*

The finding was **correct and entirely self-inflicted**. `solution_explanation` described the numbers-below-strings rank scale, my `solve.py` implemented it, and *no fixture had ever put the two types in one sorted field*. A documented rule that nothing grades is a coverage hole by definition — this is `replay-rungear-runs` §3.2 ("ask whether the rule is *observable given the data*, not whether it is documented") in a fifth category.

**Fix:** disclose the *data shape* without the rule. `instruction.md` gained one sentence — a handful of older tickets, triaged before the field was standardised, still carry the string a support lead typed (`"P1"`), never migrated — and held-out `h09`/`h10` mix the types in one sort. The sentence says the situation exists; it does not say which type ranks where.

**It gated nothing** (§ headline finding two). Correct fix, real hole closed, zero difficulty gained.

### 3.2 `ava_review` `verifier_coverage` — a disclosed mechanic graded only by the sample

> *"Each query carries a non-empty `filter` (always `severity=<value>`); no fixture exercises absent/empty filter; … the submission is contractually incorrect, but the verifier would instead PASS — all 11 graded queries include a non-empty filter, so the defect is never triggered."*

Same class as 3.1, different clause: the disclosed "no/empty filter matches every document" rule was exercised **only** by the shipped self-check. Fixed by adding `h11` (filter key omitted entirely) and `h12` (`filter: {}`), plus a `no_filter_matches_none` mutant proving both now break under the misreading.

**Lesson for the generator, applied both times and worth doing up front next task:** invariant 3 above (*every disclosed mechanic must break the shipped sample*) is **not sufficient** — it must be *every disclosed mechanic must break the shipped sample **and ≥1 held-out fixture***. That is `restore-runbook-advisor` §3.3's exact conclusion, which I had read and still did not encode in the generator before the first push. Encoding it would have deleted both of these blocks before they cost a cycle each.

### 3.3 `ava_review` `sound_verifier` — the answer key readable by the graded program

> *"/app/data/expected.json is copied with default perms (world-readable) and is not removed before grading; expected Program must compute results from the given collection/queries; reading expected.json is not computing, but the verifier would instead test_shipped_sample passes without computation…"*

The gate itself noted the overall reward was never at risk (the twelve held-out tests have no such file to read, so a read-and-echo submission still scores 0). The unsound part was narrower and real: `test_shipped_sample` alone could be satisfied without computing.

**The fix that does *not* work, and why:** sealing a *duplicate copy* with identical content. A cheat reads whichever copy it can reach and gets the same answer — content-identical copies are not a security boundary. Two structural changes were needed together:

1. `tests/test.sh` seals `/app/data` (`chmod -R go-rwx`) alongside the existing `/tests` seal, **timed at grading**, so the agent's legitimate self-check reads while developing are unaffected and only the graded run is denied;
2. `test_shipped_sample` grades against a new sealed `tests/shipped_expected.json`, never the agent-visible copy.

This is `rebuild-uptime-rollups` §4.3 (grade the shipped period against a sealed baseline) — which I had *read* and implemented only halfway, sealing `/tests` but not the agent-visible answer key. **Proven closed by performing the attack:** `tools/mutants/reads_shipped_expected.py` computes nothing and echoes `/app/data/expected.json`; through the real verifier it fails 13 of 14 tests (only the fixtures-present sanity check, which needs no computation, survives).

### 3.4 Rejected on paper, before any code

| Rejected candidate | Why | Source |
|---|---|---|
| CouchDB deterministic winning-revision selection (deepest revision wins; ASCII-highest `_rev` breaks ties) | genuinely attractive and correctly researched, but it is *one lookup and one rule* — a single memorised fact, not a rule that must be **noticed** | `experiment-analysis-frame` §3.3 (a table to look up = recalled, not noticed) |
| Any axis resting on a permissive clause ("may", "any of the following") | `monograph-usage-report` spent four rounds and four verdicts on exactly this | `monograph-usage-report` §3.1 |
| An invented store-specific deviation from MongoDB behaviour | disclosed → the agent implements it; undisclosed → B5 blocks it | `rebuild-uptime-rollups` §3.5, `lumenp` §3 |
| Aggregation-pipeline semantics (`$group`, `$unwind`) | far larger ambiguity surface; single-collection find+sort *is* document-store querying | — |

---

## 4. What worked

### 4.1 Naming the authority, enumerating nothing

Covered in §2. The decisive evidence: `deep_review` wrote *"the decisive rules are MongoDB-documented behavior the instruction explicitly delegates to"* and passed `decisive_answer_discoverable`, while all five trials still failed. Discoverability and difficulty are not in tension when the rule is **dismissable rather than hidden** — the model finds it, then talks itself out of it.

### 4.2 A no-tolerance output type chosen at design time

The graded artifact is a permutation of identifiers. There is no rounding, no float, no margin, and therefore no `difficulty_evidence` threshold argument for any gate to reach for. Prior tasks engineered integer-only pipelines to reach this state; picking an *ordering* problem gets it for free. Worth weighting in future crux selection.

### 4.3 Two independent decompositions, and the cross-check earning its keep

`tools/generate.py` authors ground truth with a single `cmp_to_key` three-way comparator; `solution/solve.py` uses multi-pass stable sorts, least-significant field first. `deep_review` cited the independence unprompted. Note the irony worth recording: **all five trials independently chose the `cmp_to_key` architecture** — the generator's shape, not the oracle's — and still failed, because the architecture was never the difficulty.

### 4.4 Local checks that replace guessing

```
cd task
python3 tools/generate.py     # rebuilds data+fixtures; refuses on a broken invariant
python3 tools/calibrate.py    # solve.py vs every expected.json, no Docker (fast)
bash tools/mutants.sh         # real verifier, built image, one mutant per misreading
harbor run -p . --agent oracle   # 1.000
harbor run -p . --agent nop      # 0.000
```

`mutants.sh` reports **pytest node IDs from the real verifier**, so "passes shipped, fails h05/h06" is a claim about the grader rather than about my own comparison function. It is also what proved 3.3's fix, by performing the attack rather than arguing it.

### 4.5 Answering each gate at the layer it complained about

All three blocks were verifier-layer findings and all three were fixed at the verifier layer — fixtures, seals, sealed baseline — with **the crux untouched across all four pushes**. `instruction.md` changed exactly once, to add the legacy-string data-shape sentence. `pass2` returned 0/2 on every round and `deep_review` passed on every round it ran, which is the signal that the fixes were not spending difficulty. Resisting the urge to "strengthen" the design while a gate is complaining about plumbing is `monograph-usage-report` §3.5, confirmed.

---

## 5. Gate-by-gate log

| Push | Commit | What it did | Result |
|---|---|---|---|
| 1 | `87250d8` | initial | static ✅ 25/25 · eval ✅ **31/31** first try · similarity **UNIQUE** (0.806/0.9) · validation ✅ · **pass2 0/2, 2 valid fails, Rerun NO** · deep_review ✅ · ava_review ✅ · tier1 ✅ · qc_eval ✅ · qc_exec ✅ · **qc_gate ⛔ C3** (§3.1) |
| 2 | `ff81a94` | axis 4 + `h09`/`h10`; README/toml synced | static ✅ · eval ✅ · validation ✅ · **pass2 0/2** · deep_review ✅ · **ava_review ⛔ `verifier_coverage`** (§3.2) |
| 3 | `766bf6e` | `h11`/`h12` + empty-filter mutant + generator invariant | static ✅ · eval ✅ · validation ✅ · **pass2 0/2** · deep_review ✅ · **ava_review ⛔ `sound_verifier`** (§3.3) |
| 4 | `a88caa7` | seal `/app/data`; sealed `tests/shipped_expected.json`; cheat probe | **everything ✅** — qc_gate ✅ · ava_review ✅ · **trials 0/5, 5 good-valid-fails, avg@5 = 0.000** → `accepted` |

Timings: pass2 27–53 min, qc_eval ~10 min, ava_review/deep_review 4–9 min, trials ~26 min. A full cycle ran ≈1h20m–2h. **Zero platform faults across four pushes** — no harbor outage, no rate-limit fail, no stale `H` status. Worth recording because the corpus is dense with the opposite.

---

## 6. pass@5, and what the model actually did

0 solved · 5 good-valid-fail · avg@5 = 0.000. Every trial finished in **8.5–17 minutes of a 3600s budget** — the corpus's most-repeated failure shape (`bytecode-vm-debug`: quit in 77–137s of 900s).

| Fixture | Trials failing | Axis |
|---|---|---|
| `h08` | **5 of 5** | 3 (descending max-element) |
| `h05`, `h06` | 4 of 5 | 3 |
| `h03`, `h04` | 4 of 5 | 2 (empty array below null) |
| `h01`, `h02`, `h07`, `h09`–`h12`, shipped | **0 of 5** | axes 1 and 4 gated nothing |

Every agent built a sound BSON-style comparator, got filtering, null-vs-missing, number-vs-string, and the `_id` tie-break right, validated against the shipped sample, saw `MATCH: True`, and stopped.

The quotes are the finding:

- `task__Li8PfjQ` — step 5: *"comparing the smallest elements of the array"* — then shipped positional lexicographic comparison.
- `task__yAxEvuA` — step 4: *"I'll implement full array lexicographic"* — the one trial that ranked empty arrays correctly, failing on `h08` alone, a single adjacent swap.
- The analysis's own summary: agents *"accessed the relevant MongoDB knowledge from training data but lacked confidence to act on it when the sample seemed to contradict it."*

**The sample did not contradict it — the sample was silent, and silence read as contradiction.** That is the whole mechanism, and it is why invariant 1 (bit-identical under every misreading, not merely untested) is the load-bearing one.

`near_miss` came back 2 PASS / 3 FAIL. The graders disagreed among themselves on whether a 5-of-12-fixture systematic failure is a near-miss; the analysis explicitly said the split *"reflects differing interpretations … not a signal of threshold artifacting."* **A mixed `near_miss` did not block acceptance** — do not redesign on it alone.

---

## 7. Error → what to do, and what NOT to do

| Symptom | Do | Do NOT |
|---|---|---|
| `qc_gate` C3 naming a rule your metadata claims but no fixture grades | believe it; add held-out fixtures that witness it. Disclose the **data shape** that makes the case arise, never the rule | do not delete the rule from `solution_explanation` to make the finding go away — you would be hiding an untested branch rather than testing it |
| `ava_review` `verifier_coverage` on a **disclosed** mechanic | add held-out fixtures for it. It is coverage, not difficulty — expect it to gate nothing | do not count the new axis toward difficulty, and do not compensate by adding a crux elsewhere in the same push |
| `ava_review` `sound_verifier` on an agent-visible answer key | seal it **at grading time** in `test.sh`, and grade against a separate sealed copy under `tests/`. Prove it with a probe that performs the cheat | do not seal a content-identical duplicate and call it fixed; do not delete the self-check (it is what makes the green feel earned — `merge-lora` §4.5) |
| Choosing between a rule the model does not know and one it knows but dismisses | pick the **dismissable** one. Axes 2 and 3 are in the manual and took 5/5 anyway | do not withhold a rule to make it "harder" — that is what draws B5, and it did not help here |
| A gate blocks while pass@2 is already 0/2 | fix the gate at its own layer and leave the design alone | do not "strengthen difficulty" in the same push; you cannot attribute the next result |
| `near_miss` returns a mixed PASS/FAIL split | read the analysis's reasoning before reacting; a split can be graders disagreeing on definitions | do not redesign, and do not tighten the verifier, on a split `near_miss` alone |

---

## 8. Bugs I introduced myself

1. **A `.gitignore`d `jobs/` directory was already handled, but the first `git add -A` came within one `.gitignore` line of committing harbor run artifacts.** Verified with `git status --porcelain | grep jobs` before every commit. Cheap habit; keep it.
2. **`tools/mutants.sh` bind-mounted relative paths** — `docker run -v solution/solve.py:...` fails with *"includes invalid characters for a local volume name"*. Resolve to an absolute path inside `run_one`. Cost one run.
3. **Three separate README/`task.toml` count drifts** (8→10→12 fixtures, 10→12→14 tests) across four pushes. Every one was caught by grepping for the stale numbers before committing rather than by re-reading prose. `grep -rn "eight held-out\|/ 8\b\|Nine tests" README.md task/task.toml` is faster and more reliable than reading.
4. **The first `axis1` mutant was written against the wrong framework** — a `field_rank` override could not express "missing sorts last in both directions" and the invariant-1 assertion caught it immediately (the shipped sample was *not* inert under it). The generator refusing to write is exactly the intended behaviour; the mutant needed to be a full comparator, not a rank swap.

---

## 9. Process rules confirmed or learned

1. **Encode `restore-runbook-advisor` §3.3's rule in the generator before the first push:** every disclosed mechanic must break the shipped sample **and ≥1 held-out fixture**. Two of three gate blocks on this task were that rule, unencoded.
2. **Prove every soundness fix by performing the attack as a committed probe.** `reads_shipped_expected.py` is 25 lines and converts "I believe this is closed" into a verifier result.
3. **The pre-push README gate works, but grep it, don't read it.** Numbers drift silently; prose does not announce staleness.
4. **`pass2` genuinely running looks identical to `pass2` wedged.** One call distinguishes them: `gh api .../jobs --jq '.jobs[] | select(.name=="review / pass2") | {status,started_at}'` against the current UTC time. Fifty minutes elapsed of a 60-minute GitHub watch window is normal, not a stall.
5. **A stale `needs-revision` label persists through a green re-run** until the gates finish. Read `gh pr checks`, never the label, mid-cycle.
6. `previous_task_data` had **6 remote commits** waiting. `git pull --no-rebase` first; the default pull config in this clone errors out with *"Need to specify how to reconcile divergent branches."*

---

## 10. Reusable checklist for the next task

- [ ] Before designing: list every task in `previous-task-data.md` and write down why this design is none of them. (Here: four prior Data Querying tasks were Query optimization, Analytical queries ×2, Database administration — this is the first NoSQL/document-store one, and no prior task rebuilds a database engine's *comparison semantics*.)
- [ ] Pick an output type with **no numeric tolerance** if the domain allows one — an ordering, a permutation, an id list.
- [ ] Name the authority in `instruction.md`; enumerate nothing; keep the register flat and descriptive.
- [ ] Prefer a **dismissable documented rule** over an obscure one. The model finding it and abandoning it is the mechanism.
- [ ] Generator invariants, all machine-enforced, refusing to write on failure:
  - shipped sample **bit-identical** under every misreading;
  - each misreading caught by ≥2 held-out fixtures;
  - **every disclosed mechanic breaks the shipped sample AND ≥1 held-out fixture**;
  - the structural property that keeps each axis inert (here: shipped arrays stay ascending) asserted explicitly.
- [ ] Two independent decompositions for oracle vs. ground truth.
- [ ] Seal at grading time: `/tests` **and** any agent-visible answer key; grade the shipped case against a sealed copy under `tests/`.
- [ ] One committed probe per soundness claim, run through the real verifier.
- [ ] Before every push: `git status --porcelain | grep jobs`; grep README/`task.toml` for stale counts; `harbor oracle`/`nop`; `mutants.sh`.
- [ ] Expect gate-driven axes to gate nothing. Budget difficulty from the axes you designed first.

---

## 11. One-paragraph version for future me

A MongoDB `find().sort()` replay from a static export, graded on exact `_id` ordering against twelve held-out fixtures. Four documented BSON comparison rules withheld behind one flat sentence naming MongoDB as normative and enumerating nothing — which is why no discoverability gate ever touched the crux, unlike the four tasks before it. All three gate blocks (`qc_gate` C3, `ava_review` `verifier_coverage`, `ava_review` `sound_verifier`) were verifier-layer: two were disclosed mechanics graded only by the shipped sample, one was the agent-visible answer key being readable by the graded run. All three were fixed at the verifier layer with the crux untouched, `pass2` holding 0/2 every round. The two axes added under gate pressure gated nothing; the two designed first took all five trials, with four of five agents explicitly naming the array min/max rule in their reasoning and then abandoning it once the shipped sample went green. Final: 0/5 solved, avg@5 = 0.000, accepted on the fourth push, zero platform faults. Next time: encode "every disclosed mechanic must break the shipped sample **and** a held-out fixture" in the generator before push one, and it is a two-push task.
