# dynamo/reduce-palaeomag-collections — accepted on the second push, and why the sample data did all the work

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 17 checks green, `accepted` label |
| **Repo** | `dynamo-a28b601-scientific-computing-and-domain-science`, branch `submission` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-a28b601-scientific-computing-and-domain-science/pull/1 |
| **Category / sub** | Scientific Computing and Domain Science / Statistical Modeling (pre-seeded) |
| **Benchmarked model** | reported as `Model A` (`task.toml` names Opus-4.8 / Terminus-2 — fixed dataset fields) |
| **Final commit** | `364a5bb` |
| **Headline** | **pass@5 = 0/5 solved, avg@5 = 0.000, 5 good valid fails, every rubric criterion PASS on all 5 trials.** pass@2 was 0/2 on the **first** push, and `qc_gate` passed **first time** |

Two pushes, two pipeline runs. This is the cheapest task in this corpus so far, and the reason
is worth stating plainly: **the design was taken from the corpus rather than from the strategy
pages.** Nothing here was invented at the design stage that had not already been measured to
work on `experiment-analysis-frame`, `retired-normalizer` or `lumenp`.

---

## 1. What the task asks

A palaeomagnetic lab reduced its collections with an in-house program until the machine it ran
on was scrapped. The collections survived; the program did not.

- **Agent sees:** `instruction.md`, one collection at `/app/data/collections/AWASH/`
  (`sites.csv` — site lat/lon and bedding attitude; `specimens.csv` — per-specimen declination
  and inclination in geographic coordinates), and `/app/data/reports/AWASH.json`, the report the
  retired program produced for it.
- **Agent produces:** `/app/reduce.py`, invoked
  `python3 /app/reduce.py <collection_dir> <out_json>`.
- **Graded on:** the shipped collection plus **seven held-out collections** (`tests/` overlay),
  all-or-nothing across 27 tests. Per site `n, dec, inc, k, a95`; per collection
  `n_sites, dec, inc, k, a95, pole_lat, pole_lon, pole_k, pole_a95`.
- Angles to 0.05° (`dec`/`pole_lon` circularly **and** range-checked), κ to 0.2 % relative.

The reduction: restore each specimen to stratigraphic coordinates through the site's bedding,
Fisher-average specimens per site, Fisher-average site means for the collection, convert site
means to virtual geomagnetic poles under the geocentric axial dipole hypothesis and
Fisher-average those.

---

## 2. The crux, and the invariants that keep it alive

Two axes, both **real published palaeomagnetic conventions**, both **conditional**, both
**structurally absent from the shipped collection**, both **silent** when wrong.

| Axis | Fires when | Cost of getting it wrong |
|---|---|---|
| **A. Polarity collapse before collection-level averaging** | the collection spans more than one polarity epoch | κ 26–64× too small, α95 8–22× too large |
| **B. The dipole pole longitude condition** | a site's VGP falls outside the principal arcsine branch | pole longitude off by up to 88° |

**The deciding rule for A.** Site means from a mixed-polarity collection must be brought onto a
common mode before the Fisher mean, and membership is decided by **angular distance to the
resultant**, not by the sign of the inclination. On a single-polarity collection the step is a
**no-op**, so omitting it reproduces the shipped report exactly.

**The deciding rule for B.** The textbook arcsine form of the VGP longitude carries a condition
(`cos p ≥ sin λ_site · sin λ_pole`, else `φ_s + 180° − β`). Written as an `atan2`
bearing-and-distance step it is correct everywhere and needs no condition at all.

**Invariants that must never break:**

1. **AWASH is single-polarity**, so axis A is inert there — measured bit-exact, not assumed
   (`tools/calibrate.py` asserts `< 1e-9` divergence under the no-collapse reading).
2. **AWASH's sites are low-latitude with steep inclinations**, so every VGP sits in the
   principal branch and axis B is inert there — same assertion.
3. **The machinery *is* pinned by AWASH.** Skipping the bedding correction moves the sample's
   mean declination 4.4°; pooling specimens instead of two-stage averaging moves α95 5.6°.
   Both assertions run in `calibrate.py`. Without them the withheld steps would be
   underdetermined and B5 would have blocked — this is `retired-normalizer` §4.1 applied
   preventively.
4. **Every mixed-polarity collection is clearly single-mode dominant** (8:3, 7:5, 8:4, 9:4), so
   "collapse onto the dominant mode" is uniquely pinned and rival common-polarity conventions
   converge on the same reported direction. `deep_review` checked exactly this and said so.
5. **κ and α95 are invariant to the collapse convention entirely**, so the two decisive
   discriminators cannot turn on a convention choice at all.
6. **The instruction never names polarity, reversal, antipode, hemisphere, flip or branch.**
   Grepped before every push. It says only *"Follow standard palaeomagnetic practice throughout;
   where a step has an established convention in the field, the retired program used it."*
7. **Two shallow-inclination collections** (BREIDDAL, ELLESMERE) contain sites whose *same-mode*
   inclination is slightly negative from scatter alone, so the "flip anything with negative
   inclination" shortcut fails too. Rotating shapes of the same degeneracy — `retired-normalizer`
   §4.2.

---

## 3. Dead ends

**There were none.** This is the first task in this corpus where no design was thrown away, and
that is the finding, not a boast: every dead end had already been paid for by an earlier file.
The candidate cruxes rejected *at the design stage, on paper*, using this corpus:

| Rejected candidate | Rejected because | Corpus source |
|---|---|---|
| ISO 13528 Algorithm A robust statistics | memorised — the model fetches the standard and implements it | `experiment-analysis-frame` §3.3 |
| Kendall tau-a/tau-b, Spearman midranks | ambiguity unless the instruction names the variant; naming it discloses it | `sweep-replay` §3 (single published definition) |
| Rank-deficient design matrix → wrong residual df | error bounded at a few percent → `difficulty_evidence` threshold artifact | `experiment-analysis-frame` §3.5 |
| udunits `months since` nominal-vs-exact | real and counterintuitive, but the drift is ~1 day — too small | same |
| CF `calendar = "360_day"` | the flag is an explicit named attribute; the agent reads it and branches | `lumenp` §3 (disclosure kills dismissability) |
| Left-truncation / competing-risks survival | "exclude vs adjust" is a defensible alternative → ambiguity | rubric `unambiguous` |
| Concise uncertainty notation `1.2345(67)` | the `(12)` vs `(1.2)` distinction is not single-valued enough to defend | `sweep-replay` §3 |
| Type I vs Type III sums of squares | genuine statistical controversy; a reviewer can defend either | rubric `unambiguous` |
| Tilt correction as a *crux* | any withheld target coordinate frame is ambiguous; demoted to **machinery** taught by the sample | `fir` §6.3 |

**Two hours of design reading bought a two-push acceptance.** The reading order that mattered:
`previous-task-data.md` index → `experiment-analysis-frame` (the whole file) →
`retired-normalizer` §3–4 → docs `33`/`34`. Doc `44` is the software-engineering addendum and
there is **no addendum for this subcategory** — the transferable content came from the corpus,
not the doc set.

---

## 4. What worked

### 4.1 Copy the *shape* of the accepted crux, never the convention

`experiment-analysis-frame` §4(b): the deciding rule must be **noticed, not recalled** — decided
by a property of the input an otherwise-correct implementation will not think to check. `P2D` vs
`PT48H`; cron's first-character `*`. Here it is **"are these site means antipodally split?"** —
a property of the data, checkable by looking, named nowhere.

An exponent table is recall. A structural property of the sample is a distinction. That
sentence is the entire design.

### 4.2 Two independent axes, and only one of them needs to fire

`experiment-analysis-frame` §4: *"two independent external conventions is why the result is 0/5
rather than 2/5."* Held here, in a way worth recording precisely:

- **4 of 5 trials** failed on axis A alone.
- **1 trial (`task__rub6nPv`)** failed on **both** — and its trace is the reason to keep a
  secondary axis even when it looks redundant: it *"explicitly tested both formulations against
  AWASH in trajectory step 4, found both gave the same result, and chose the simpler asin
  form."* That is `experiment-readout` (live example 4) reproduced exactly — compute both, see
  them agree on the sample, pick the wrong one.
- `deep_review` on run 1 noted axis B *"did not gate"* because both pass@2 agents used `atan2`.
  **That was a correct observation about two trials and a wrong prediction about five.** Do not
  delete a secondary axis because a two-trial sample did not exercise it.

### 4.3 Ship a complete-*looking* self-check that is silent on the trap

`contact-export` §9 items 1–2. `AWASH.json` lets an agent validate the entire pipeline end to
end and reach 100 % agreement — while being structurally incapable of exercising either deciding
step. The graders described the consequence in their own words:

> "the AWASH single-polarity training oracle structurally conceals this gap, producing
> overconfident early-quit"

Agents quit at **3.5 and 5.7 minutes of a 3600 s budget**. The amplifier is the sample, not the
spec.

The `merge-lora` §3.1 exposure (a graded artifact whose answer ships under `/app`) is defused
here by grading a **program** run against seven collections whose answers exist nowhere in the
image. `ava_review` raised nothing on it.

### 4.4 Prove inertness and pinning with a script, not with prose

`tools/calibrate.py` asserts four things every run, and each maps to a gate that would otherwise
have caught it a cycle later:

| Assertion | Gate it pre-answers |
|---|---|
| sample divergence `< 1e-9` under no-collapse | pass@2 "too easy" |
| sample divergence `< 1e-9` under no-branch | pass@2 "too easy" |
| sample divergence `> 1.0°` under no-bedding-correction | `qc_gate` B5 underdetermined |
| sample divergence `> 0.5` under single-stage averaging | `qc_gate` B5 underdetermined |

`retired-normalizer` §4.4 — measure the trap locally before every push. Cost: seconds. It has
now paid on three tasks.

### 4.5 Two independently-written implementations, agreeing to 2e-11

`experiment-analysis-frame` §7 warns that `oracle = 1.000` is *"nearly vacuous"* when
`solution/` is byte-identical to `tests/_reference.py`. So they were written from different
formulations — Rodrigues rotation vs an explicit rotation matrix, a branched arcsine vs an
`atan2` great-circle step. They agree to **2e-11 degrees** on all eight collections.

Two returns beyond the intended one:
- The disagreement *would have* localised a branch-condition error immediately. It was the
  fastest way to confirm the condition was right.
- Both `deep_review` and the rubric cited it unprompted as evidence the expecteds are not an
  oracle echo (`correct_expected_results` PASS, `reviewable` PASS).

### 4.6 Three plausible-wrong implementations, not one

`audit-build-context` §7. Built before the first push: no-collapse (8 failing tests), no-branch
(6), inclination-sign flip (4). The third existed only because invariant 7 was designed in — and
it is the one that guards a shortcut no gate ever probed.

---

## 5. Gate-by-gate log

### Push 1 — `0ae8ab2`

| Gate | Verdict |
|---|---|
| `changes`, `cosine_similarity`, `similarity`, `ratelimit` | pass |
| static (`review`) | **pass, all 25 checks first time** — `.dockerignore`, Qwen3 token limit (918/1500), no timeout-suffix line |
| `review` (rubric eval) | **PASS — all 31 criteria, zero failures** |
| `similarity` (duplicate) | UNIQUE; closest TB2 match `cobol-modernization` at 0.080 lexical |
| `validation` | docker / oracle / nop all ✅ |
| **`pass2`** | **PASS — 0/2 solved, 2 valid fails**, identical root cause |
| `deep_review` | **PASS**, no blocking issues |
| **`ava_review`** | **BLOCK** — one `sound_verifier` finding (§5.1) |
| `tier1`, `qc_*`, `trials` | skipped (union gate blocked) |

### 5.1 The only blocking finding in the whole task

> **`sound_verifier` (AVA)** — *"at `tests/test_outputs.py _close(): CIRCULAR={'dec','pole_lon'}`
> … Any value congruent mod 360 to the reference passes regardless of range; expected reject per
> instruction range clause, but the verifier would instead accept."*

`instruction.md` says *"Report declinations and longitudes in `[0, 360)`"*. The circular
comparison absorbed `-12.3` and `372.4` alike. Correct and cheap: range-check before the
circular distance, and bound `inc`/`pole_lat` the same way.

**Note the routing quirk that cost a minute of confusion.** The AVA comment listed this finding
under *"Advisory (non-blocking)"* while its own header said **BLOCK**, and the Blocking Issues
section said only *"see the deep-review comment"* — where `deep_review` had returned **PASS with
no blocking issues**. The union gate blocks on either side; the *routing footer* (`Routing:
block · flagged by: AVA`) is the authoritative line, not the section the bullet is printed
under.

### 5.2 Push 2 — `364a5bb`, everything green

Fix + the two advisories bundled (`sweep-replay` §7: fix the debatable ones in the same push):

- per-invocation `subprocess` timeout 300 s → 30 s, so one hung run cannot eat the whole
  verifier budget (deep_review advisory 1);
- synthetic-data provenance stated outright in `difficulty_explanation` and the README rather
  than implied (rubric note on `difficulty_explanation_quality`).

| Gate | Verdict |
|---|---|
| `pass2` | PASS — **0/2 again**, all 7 per-trial criteria PASS on both |
| `ava_review`, `deep_review` | **PASS** |
| `tier1` | PASS |
| **`qc_eval`, `qc_exec`, `qc_gate`** | **PASS, first time** — `QC-BASE` matched HEAD, `QC-FIXES-B64:W10=` (empty) |
| **`trials`** | **pass@5 0/5, avg@5 = 0.000, 5 good valid fails** |
| `pass2_suggestion` | **skipping** (no difficulty suggestion needed — a good sign) |
| `gate` | pass → `accepted` |

`qc_gate` clearing first time is the outlier worth noting: it took **four** rounds on
`experiment-analysis-frame` and **three** on `retired-normalizer`. The difference was §4.4 —
the pinning assertions were written before the first push instead of in response to a B5 block.

### 5.3 pass@5 value table

| Quantity | Golden | Agent | Off by | Trials |
|---|---|---|---|---|
| KARAKORAM κ | 72.058 | ~1.12 | **~64×** | 4 of 5 |
| KARAKORAM α95 | 5.148° | ~113.2° | +108° | 4 of 5 |
| TARIM κ | 82.190 | ~1.392 | ~59× | 3 of 5 |
| VERKHOYA κ | 51.914 | ~1.636 | ~32× | **all 5** |
| VERKHOYA α95 | 6.397° | ~55.7° | +49° | **all 5** |
| BREIDDAL `pole_lon` | 118.86° | 31.47° | **87°** | `rub6nPv` only |
| ELLESMERE `pole_lon` | 144.65° | 232.54° | **88°** | `rub6nPv` only |

Every trial: `task_specification` PASS, `reward_hacking` PASS, `difficulty_crux` PASS,
`near_miss` PASS, `refusals` PASS, `low_timeout` PASS, `approach_validity` PASS.

---

## 6. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| `ava_review` **BLOCK** whose Blocking Issues bullet only points at `deep_review`, which passed | Read the **routing footer** (`Routing: block · flagged by: AVA`) and treat the *advisory-labelled* AVA finding as the blocker | Do not conclude the block is spurious because `deep_review` says PASS — the union gate blocks on either side |
| Verifier compares an angle **circularly** | Range-check the value **first**, then compare circularly. The stated range is part of the contract | Do not assume a circular comparison is a superset of a range check — it silently accepts `-12.3` for `347.7` |
| About to tighten any comparison | Probe **both** sides in the same run: a mutant that must now fail, and the oracle that must still pass (here: 25 failing / 27 passing) | `contact-export` §3.3 — two tightenings there rejected a *correct* solver |
| `deep_review` says one of your two axes "did not gate" | Keep it. Two trials is not five | Do not delete a secondary axis on a two-trial sample — ours failed a fifth-trial agent that had *tested both formulations and picked the simpler one* |
| Choosing a real external convention as the crux | Ask whether it is **noticed** (a structural property of the input: is this set antipodally split? does this branch condition hold?) or **recalled** (a table, a code list) | `experiment-analysis-frame` §3.3 — only the first discriminates |
| A candidate crux would need a target coordinate frame / output convention withheld to work | Demote it to **machinery** and let the sample teach it | Do not withhold a normative definition — that is unfairness, not difficulty (`retired-normalizer` §4.1) |
| Worried a withheld step is underdetermined | Assert at calibration time that the sample **does** pin every step you are *not* withholding, and does **not** pin the ones you are | Do not answer it with more prose in `instruction.md` (`retired-normalizer` §3.2, three lost cycles) |
| A shortcut heuristic might pass by accident (e.g. "flip if inclination < 0") | Build a fixture where the shortcut and the correct rule disagree, and a mutant that implements the shortcut | Do not assume the obvious wrong rule is the only wrong rule |

---

## 7. Bugs I introduced myself

1. **A greedy, order-dependent mode collapse.** The first `_to_common_mode` accumulated signs
   incrementally, so the answer depended on the order sites appear in `sites.csv`. Replaced with
   align-to-first then majority-vote on the sign — order-independent by construction, which
   `deep_review` then cited under `no_brittle_time_dependence`. **A collapse rule that depends on
   input order is a latent non-determinism the verifier will not catch, because the reference has
   the same bug.**
2. **Realistic data sat exactly on the branch boundary.** A direction consistent with the
   geocentric axial dipole puts the pole *at* the geographic pole, where
   `cos p == sin λ_s · sin λ_p` exactly and the pole longitude is ill-conditioned. Designing
   collections with genuine declination/inclination anomalies moved every fixture off the
   boundary. **Check the conditioning of a branch crux before building fixtures around it — the
   "natural" parameter values may all be degenerate.**
3. **`grep -c pending` returned 0 and broke a `&&` chain**, silently skipping a commit — `grep`
   exits 1 on zero matches. The pre-push guard has to be
   `PEND=$(... | grep -c pending || true)` and then an explicit test, or the guard skips the very
   command it was protecting.
4. **`solve.sh` initially wrote an output file the instruction never named.** Harmless, but an
   artifact no requirement asks for is exactly what `no_orphaned_behavior` looks for. Removed
   before the first push.

---

## 8. Process rules

- **Never push while a check is pending.** Verified with `gh pr checks 1 | grep -c pending`
  before both pushes. `deep_review` was still running when the AVA fix was ready; it was held.
- **Never `git add -A`.** `task/jobs/` is harbor output. Added `jobs/` to `task/.gitignore` and
  staged explicit paths. 30 files, counted.
- **Set the commit identity at clone time** from `gh api user` — `git config user.email
  "<id>+<login>@users.noreply.github.com"`. `gh api user --jq .email` returns empty for a private
  email.
- **`.dockerignore` before the first push.** `task/environment/` has a `data/` subdirectory, so
  the static check requires it. Three tasks have now hit this; it is 30 seconds.
- **Omit the "You have N seconds…" line.** Confirmed again — `instruction_concision` PASS with
  it absent. Six tasks, no exceptions.
- **Validate `task.toml` parses** before pushing. macOS system Python is 3.9 with no `tomllib`;
  run it inside the task image instead.
- **Grep the agent-visible surface for the crux vocabulary before every push:**
  `grep -rin 'polar|revers|antipod|hemisph|flip|branch|180' task/instruction.md task/environment/`
  — must be empty.
- **Timings, for planning:** whole run ≈ 2 h. `pass2` 11–12 min, `deep_review` 5–8 min,
  `ava_review` 6–9 min, `qc_eval` 9–10 min, `qc_exec` 3 min, `trials` the remainder.

---

## 9. Reusable checklist

Design:
- [ ] Is the deciding rule **real, external and published**? Invented rules must be disclosed,
      and disclosed rules get implemented.
- [ ] Is it **noticed** (a structural property of the input) rather than **recalled** (a table)?
- [ ] Is it **conditional** — does it fire only on inputs the sample does not contain?
- [ ] Is the error **orders of magnitude**, not a fraction of the grading band?
- [ ] Are there **two independent** axes? Keep the second even if an early run says it is inert.
- [ ] Would a rival reading of the same rule give a *different* graded answer? If so, either pin
      the convention in the instruction or grade only the quantities invariant to it (κ and α95
      here are invariant to the collapse convention — that is what makes it defensible).

Data:
- [ ] Sample **bit-inert** under every wrong reading of the crux — asserted, not assumed.
- [ ] Sample **does** pin every non-crux step — asserted, with a divergence number.
- [ ] Each crux witnessed by **≥3** held-out fixtures; at least one fixture **combines** them.
- [ ] Several **shapes** of the same degeneracy, including the plausible shortcut's failure mode.
- [ ] Every held-out case comfortably clear of any branch/tie boundary.

Verifier:
- [ ] Every stated output **range** enforced, not just the value.
- [ ] Reference written from a **different formulation** than the oracle; agreement measured.
- [ ] **Three** plausible-wrong implementations run against it, with failing-test counts.
- [ ] Any tightening probed on the **accept** side in the same run.
- [ ] Per-subprocess timeout well inside `[verifier].timeout_sec`.

Before every push:
- [ ] `gh pr checks 1 | grep -c pending` → 0 (with `|| true`).
- [ ] Oracle 1.0, nop 0.0, re-run after any data or reference change.
- [ ] Crux vocabulary absent from the agent-visible surface.
- [ ] Root `README.md` re-read against the **complete** diff.
- [ ] No AI attribution in any commit message or file.

---

## 10. One-paragraph version for future me

The first task in this corpus accepted without a single redesign, in two pushes, with
`qc_gate` and the rubric passing first time and pass@5 at **0/5, avg@5 = 0.000**. Nothing
clever was invented: the design is `experiment-analysis-frame`'s conclusion applied literally —
put the machinery where the sample can pin it, and put the deciding rule in a real published
convention that is **noticed rather than recalled**, decided by a structural property of the
input. Here that property is "are these site means antipodally split?", and the shipped
collection is single-polarity so the answer is always no and the step is always a no-op. A
second axis (the dipole pole longitude condition) looked redundant after pass@2, where both
agents happened to use `atan2` and `deep_review` said it "did not gate" — keeping it anyway was
right, because the fifth pass@5 agent tested both formulations against the sample, saw them
agree, and shipped the wrong one. The only blocking finding in the whole task was a verifier
soundness bug of my own: comparing declinations circularly silently accepted values outside the
`[0, 360)` range the instruction requires. The lesson that generalises beyond the crux is
§4.4 — the four calibration assertions (sample inert under each wrong reading, sample *not*
inert under each machinery step) were written before the first push instead of in response to a
B5 block, and that alone is most likely why `qc_gate` cost zero cycles here and four on the task
this design was copied from.
