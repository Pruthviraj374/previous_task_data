# dynamo/replay-strata-plans — the same disclosure, in two registers, is 2/2 and 0/2

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 17 checks green, `accepted` label |
| **Repo** | `dynamo-e1ed1a7-data-querying-and-databases`, branch `submission` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-e1ed1a7-data-querying-and-databases/pull/1 |
| **Category / sub** | Data Querying and Databases / Query optimization (pre-seeded) |
| **Benchmarked model** | reported as `Model A` (`task.toml` names Opus-4.8 / Terminus-2 — fixed dataset fields) |
| **Final commit** | `aa2265d` |
| **Headline** | **pass@5 = 1/5 solved, 4 good valid fails, avg@5 = 0.200.** Four pushes. `qc_gate` blocked once and pass@2 swung 0/2 → **2/2** → 0/2 on *one sentence of instruction prose*, with the data untouched |

The finding this task exists to record: **a disclosure's register matters as much as its scope.**
The same sentence, saying the same thing about the same rules, is the difference between
`qc_gate` calling the task underdetermined and pass@2 calling it too easy. Everything else here
is confirmation of things `reduce-palaeomag`, `lumenp` and `experiment-analysis-frame` already
paid for.

---

## 1. What the task asks

STRATA is a retired query planner from an in-house analytics store. Its binary is gone; one
workload it planned survives.

- **Agent sees:** `instruction.md`, `/app/workload/catalog.json` (two tables, row/page counts,
  per-column `ndv`/`n_null`/bucketed histogram, five indexes), `/app/workload/queries.json`
  (twelve single-table queries), and `/app/workload/plans.json` — STRATA's report for them.
- **Agent produces:** `/app/plan.py`, invoked
  `python3 /app/plan.py <catalog.json> <queries.json> <report.json>`.
- **Graded on:** eight held-out workloads over three catalogs, `tests/` overlay, all-or-nothing
  across 11 tests. Per query: `path` (`"seq"` or an index name), `rows`, `cost` in page reads.
- **Exact integer equality, no tolerance anywhere.**

The cost model is *invented*, so `instruction.md` states it in full: page counting, independence,
half-up rounding with a floor of 1, leaf-page scaling, the candidate-index rule.

---

## 2. The crux, and the invariants that keep it alive

Three real, published, **conditional** relational-database conventions, none stated:

| Axis | Rule | Inert in the shipped workload because | Cost of misreading |
|---|---|---|---|
| **A** | A B-tree scan reads a contiguous run, so the run is delimited by the leading equalities plus at most one further comparison; a predicate past that comparison, or past an unconstrained column, is checked per entry but cannot narrow the run | every shipped query constrains an unbroken run of index columns with its lone comparison **last** | **139×** (h08/c1: 2495 vs 18) |
| **B** | A row holding no value satisfies no comparison, so `ndv` and the histogram describe only rows that hold one | no shipped query predicates a column with `n_null > 0` | 5–7× on rows |
| **C** | An index entry carries the indexed columns, so a query reading nothing else never touches the table | no shipped query is answerable from an index alone | **92–151×**, and the path flips |

**Invariants, machine-enforced in `tools/generate.py` — it refuses to write anything if one breaks:**

1. shipped workload **bit-identical** under all four crux misreadings;
2. shipped workload **not** identical under any step of the disclosed cost model (≥2 queries must
   move per step) — this is what keeps B5 off the *stated* machinery;
3. no estimate within 0.001 of a half-way rounding point or a ceiling boundary;
4. no plan cost ties;
5. every predicate value inside its column's histogram;
6. each axis witnessed by ≥3 held-out workloads, each misreading moving a number by ≥3×.

### The moot-variant idea, and why it is the reusable part

Three readings are deliberately left unstated **and proven not to matter**: whether `<>` can
delimit a range, whether the leaf-page share is taken before or after rounding, and whether a
value's frequency comes from `ndv` or from bucket density. Each is a `plan_all(..., variant)` that
must equal the golden output on **every** workload, asserted at generation time.

This is `reassemble-tap-sessions` §6 turned from an observation into a build step: *a probe that
reports two rival readings agreeing everywhere is reporting that you removed the ambiguity.* Here
the generator won't let the ambiguity exist in the first place. It caught nothing the day it was
written and caught the density bug (§3.1) the day after.

---

## 3. Dead ends and self-inflicted defects

### 3.1 An ambiguity of mine that no gate caught — pass@2's *analysis* caught it

Four columns had histograms spanning exactly `ndv` values but with **non-uniform density**. Reading
one value's frequency off the bucket density then gives a different answer from `stored / ndv`
(5250 vs 4500 on `region_id`). Both pass@2 agents took the density reading — and it is defensible
from the instruction, so this was **ambiguity, not a crux**.

It was failing **baseline** queries, which is the tell. The rubric passed `unambiguous` (read-only,
could not run); QC never raised it; only the pass@2 root-cause table exposed it, and only because it
named `h01/b1` — a query with no crux in it.

**Fix:** flatten those four histograms to uniform density spanning exactly `ndv`, so both readings
coincide by construction. No prose added, no crux weakened. Then add `eq_from_density` as a moot
variant *and* as an accept-side mutant that must pass all 11 tests.

> **A crux mutant must fail held-out fixtures. A rival-reading mutant must fail nothing. Probe both.**

### 3.2 The register lesson — the expensive one

`qc_gate` blocked with three Major findings, all one shape: **B5** (a rival B-tree range rule
reproduces all 12 shipped plans) and **B4** (the null handling for `<>` and for equality on
`n_null > 0` columns is stated nowhere).

`reduce-palaeomag` cleared `qc_gate` first time carrying one sentence — *"Follow standard
palaeomagnetic practice throughout; where a step has an established convention in the field, the
retired program used it."* My instruction had no equivalent. So I added one. **It was too loud:**

> *"Everything above is STRATA's own arithmetic. Everywhere it is silent, STRATA behaved the way
> relational query planners and SQL comparison semantics are publicly documented to behave — it
> invented nothing of its own beyond the costing described here, so treat established practice in
> those two areas as normative rather than guessing."*

`qc_gate` was satisfied. **pass@2 went 0/2 → 2/2.** Both agents derived all three rules in ~13
minutes and called them *"genuine but derivable"*. Three separate leaks in one sentence:

| Phrase | What it hands over |
|---|---|
| "Everywhere it is silent" | there *are* gaps — go hunt for them |
| "relational query planners **and** SQL comparison semantics" | names the two areas holding axes A and B |
| "rather than guessing" | filling a gap is decisive |

**The fix kept the scope and changed only the register:**

> *"STRATA followed standard relational-database practice throughout; where a step has an
> established convention, it used that convention."*

Flat, descriptive, names no area, gives no sign a gap exists. `qc_gate` **passed**; pass@2 went back
to **0/2**. In the same push I removed the word **contiguous** from the cost narrative — it had been
my fairness bridge for axis A, and the sentence now carried that load, so it was pure hint.

> **Scope satisfies the discoverability gate. Register decides whether the trap survives.** A
> sentence that says "established convention governs" is safe; the same sentence that also says
> *where* the gaps are, or that filling them matters, is not.

### 3.3 The difficulty suggestion's headline was a dead end; its optional item was the fix

`experiment-analysis-frame` §3.4, reproduced exactly in a different category.

- **Headline:** *"Introduce at least one STRATA-specific behavior that deviates from standard
  planner/SQL practice."* That is `lumenp` §3 — an invented rule must be disclosed or B5 blocks it,
  and a disclosed rule gets implemented; six were solved 2/2 there. Following it walks straight back
  into the `qc_gate` block just cleared.
- **Optional item 1:** *"the sentence … is the single biggest difficulty leak."* That was the fix,
  and it cost one instruction-only push.

**Read the optional items first when the headline names something your corpus already killed.**

### 3.4 Rejected on paper, before any code

| Rejected candidate | Why | Source |
|---|---|---|
| Cardenas/Yao distinct-pages formula for unclustered fetches | several published variants under near-identical names → ambiguity | `sweep-replay` §3 |
| Clustered-vs-unclustered index costing | the catalog would need a `clustered` flag; an explicit named attribute gets read and branched | `lumenp` §3 |
| Merging two range predicates on the same column | the spec must state independence, which then *defends* the wrong reading → ambiguity, not a stump | rubric `unambiguous` |
| MCV-list selectivity | a table to look up = recalled, not noticed | `experiment-analysis-frame` §3.3 |
| "Interesting orders" / sort avoidance | needs `ORDER BY` in the grammar; large scope for a fourth axis | `lumenp` §4 (stop adding mechanisms) |
| Joins of any kind | multiplies ambiguity surface; single-table access-path selection already *is* query optimization | — |

---

## 4. What worked

### 4.1 Two implementations from different decompositions

`tools/planmodel.py` carries **row counts** and rounds per quantity; `solution/solve.py` carries a
**selectivity Fraction** and rounds once at the end. They agree on all nine workloads. The rubric
cited it unprompted under `reviewable`. `experiment-analysis-frame` §7 — `oracle = 1.000` is vacuous
when the two sides are the same code.

### 4.2 Integer-only pipeline, so grading is exact

`lumenp` §6 and `reassemble-tap-sessions` §2. All statistics are integers, selectivities are exact
`Fraction`s, one stated rounding rule at the end. No tolerance exists, so no `difficulty_evidence`
"threshold artifact" argument is available to anyone.

**Confirmed by a pass@5 trial:** the one agent that solved it *"used floating-point arithmetic
rather than `Fraction` but produced identical integer results."* The `MARGIN = 1/1000` assertion on
every rounding and ceiling boundary is what made float and exact arithmetic interchangeable. Without
it that agent would have been failed on arithmetic, not on the crux.

### 4.3 Keep the axis you think is weakest

I judged axis C (index-only scans) the weakest of the three and nearly cut it — the disclosed
sentence *"a predicate on a column the index stores is answered from the index entry"* hints at it,
so I expected agents to get it.

**It was a dominant cause in 3 of the 4 failures** (h06/c1 92×, h08/c3 151×, h03/c1 and h08/c2 both
flipping the path to `seq`). `reduce-palaeomag` §4.2 said keep the secondary axis; that is now true
in a second category, and this time the axis I doubted was the *hinted* one.

### 4.4 Mutants through the real verifier, not just the model

`tools/mutants.sh` builds the environment image, copies `tests/` in, drops each mutant at
`/app/plan.py`, and runs `tests/test.sh`. Reporting *pytest node IDs* rather than model diffs is what
made the accept-side probe (§3.1) meaningful — "11 passed, 0 failed" is a claim about the grader, not
about my own comparison function.

### 4.5 Fix the borderline advisories in the same push

`sweep-replay` §7. Three came back non-blocking and all three were real:

- **Type-coercion bypass.** `compare()` used `got[k] != want[k]` on dicts, and Python evaluates
  `True == 1`, so a boolean `rows`/`cost` would have passed every held-out test. The strict type check
  existed but ran only on the shipped workload. Now every entry on every workload is checked.
- **Default-only parameter.** Every index had `height = 2`, so a solver hardcoding `2` passed. Now
  2 or 3; a `hardcoded_height` mutant fails the shipped workload plus six held-out ones.
- **Untested advertised behaviour.** The instruction advertised a tie-break that no fixture could
  exercise, because the generator asserts no cost ever ties. Removed from `instruction.md` **and**
  from `task.toml`'s `solution_explanation` — orphaned metadata prose is its own gate failure.

---

## 5. Gate-by-gate log

| Push | Commit | What it did | Result |
|---|---|---|---|
| 1 | `3a64fed` | initial | static ✅ all 25 · similarity **UNIQUE** (fingerprint 0.813/0.9) · eval **30/31**, `difficulty_explanation_quality` FAIL — no data provenance, no named audience. Everything downstream skipped |
| 2 | `4f8f1fb` | provenance + audience in `difficulty_explanation`; named `calibrate.py`/`mutants.sh` in `verification_explanation` | eval ✅ **all 31** · validation ✅ · **pass2 0/2, 2 valid fails, Rerun NO** · deep_review ✅ · ava_review ✅ · tier1 ✅ · qc_exec ✅ · **qc_gate ⛔ B5 + B4 + B3** |
| 3 | `f3d1340` | standard-practice clause (too loud); histogram flattening; three advisories | eval ✅ · validation ✅ · **pass2 ⛔ 2/2 solved — too easy** |
| 4 | `aa2265d` | clause → descriptive register; `contiguous` removed. **`instruction.md` only** | **everything ✅** — pass2 0/2 · qc_gate ✅ · **trials 1/5, 4 good valid fails, avg@5 = 0.200** → `accepted` |

Timings: pass2 19–30 min, qc_eval 12–13 min, ava_review ~8 min, deep_review 4–5 min, qc_exec 4–5 min,
trials the remainder. Whole run ≈ 1h45m.

### 5.1 The pass@2 infra loss

Push 4's pass@2 breakdown read **1 valid-fail · 1 infra/setup-timeout** — one trial died in a Daytona
`_attempt_tmux_installation` timeout with no instruction delivered and no verifier run. The gate needs
only one genuine failure so it passed, and `deep_review` flagged the thin sample as advisory. Nothing
to fix task-side; pass@5 settled it with five. `freight` §4 (re-run with an empty commit) was **not**
needed — the gate had already passed.

---

## 6. pass@5, and what the model actually did

**1/5 solved · 4 good valid fails · avg@5 = 0.200.** Every per-trial criterion PASS on all five,
including `difficulty_crux`, `near_miss`, `low_timeout` and `reward_hacking`.

The graders' own classification: *"analytical failure — overconfidence early-quit driven by an
insensitive shipped workload. Each agent matched the 12-query shipped `plans.json` exactly and
declared success."*

| Root cause | Trials | Detail |
|---|---|---|
| **A — range delimitation** | **all 4** | All four independently wrote `if pred['col'] in index_columns` — unordered set membership instead of an ordered walk. h08/c1: 18 against 2495 |
| **C — covering index** | 3 full, 1 partial | Always charged table fetches. h06/c1 827 vs 9; h08/c2 flipped to `seq` at 21600 against 248 |
| **B — null semantics for `<>`** | 1 | Returned `n_null + (non_null − eq)`, including rows `<>` cannot match. 7× on h02/c2 |

Three things worth carrying:

1. **All four agents converged on the identical wrong construct** for axis A. That is the
   wrong-default lure working exactly as designed — a set-membership test is what everyone writes.
2. **The axes stratified the failures.** h01/h04/h07/h08 failed in all four trials; h03/h06 failed in
   three; h02/h05 failed only in the null trial — and that trial *passed* h03/h06, because its null
   bug partially masked other errors. No single fixture explains the result, which is precisely the
   argument for three independent axes.
3. **The one passing trial got all three right**, using floats. It is a legitimate solve, not a
   grading accident.

### 6.1 A verifier-reporting wrinkle worth knowing

Two per-trial analyses noted that **`ctrf.json` collapses an entire `@pytest.mark.parametrize` group
into a single entry**; the graders had to recover individual fixture names from `test-stdout.txt`.
The task still graded correctly and no gate objected, but a parametrized held-out suite costs the
reviewer resolution. If per-fixture visibility in `ctrf.json` matters, generate explicit test
functions instead.

---

## 7. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| `qc_gate` B5 "a rival reading reproduces all shipped samples" | Add **one flat descriptive sentence** declaring established practice normative — `reduce-palaeomag`'s wording, not your own expansion of it | Do not name the areas, say "everywhere it is silent", or tell the agent gaps matter. Do not enumerate the rules |
| pass@2 goes **2/2 right after you answered a discoverability gate** | Suspect the **register** of the sentence you just added, not the design. Re-read it for gap-hunting cues | Do not add a mechanism, and do not revert the sentence outright — that just re-opens B5 |
| A difficulty suggestion says "add a rule that *deviates* from standard practice" | Check it against `lumenp` §3 first, then read its **optional** items | Do not implement an invented deviating quirk — disclosed it gets solved, undisclosed it gets B5'd |
| pass@2 root-cause analysis names a failure on a **baseline** query | Stop and check for an ambiguity of your own. A baseline query failing is not the crux working | Do not count it as difficulty. It will read as unfair to a human reviewer |
| You are about to grade a quantity two published readings could produce | Make the two readings **provably identical on every workload** and assert it as a moot variant, with an accept-side mutant that must pass all tests | Do not argue in prose that one reading is more standard |
| An axis looks weak because the instruction hints at it | Keep it and measure | Ours was a dominant cause in 3 of 4 failures — `reduce-palaeomag` §4.2, now confirmed twice |
| A verifier compares whole dicts with `!=` | Type-check each field first — `True == 1` in Python | Do not assume a schema test on one workload covers the others |
| Every instance of a config parameter has the same value | Vary it and add a hardcode mutant | A parameter with one value is a parameter the solver can ignore |
| Your instruction advertises a rule no fixture can exercise | Delete the advertisement, or build the fixture | Do not leave it — QC flags "untested advertised behavior", and deleting is the smaller diff when the generator already forbids the case |

---

## 8. Process rules confirmed or learned

- **`gh repo fork <repo> --clone --remote` still fails** with a usage dump when a repo argument is
  given. `--clone` alone works — and it clones into **the current directory**, not the one you meant;
  move it before doing anything else.
- **Hold improvements while a run is in flight.** The histogram fix (§3.1) was built, validated and
  committed to a local `held-improvements` branch while `qc_eval` was pending, then merged into the
  push that answered `qc_gate`. `merge-lora` §7 — it cost nothing and burned no rate-limited run.
- **Never `git add -A`.** `task/jobs/` is harbor output; `task/.gitignore` carries `jobs/` and
  `__pycache__/`, and every push staged explicit paths.
- **Set commit identity at clone time** from `gh api user`; `gh api user --jq .email` is empty for a
  private email, so use `<id>+<login>@users.noreply.github.com`.
- **`.dockerignore` before the first push** — `environment/` has a `data/` subdirectory, so the static
  check requires it. Four tasks have now hit this.
- **Omit the "You have N seconds…" line.** Confirmed again; `instruction_concision` PASS without it.
- **Re-grep the agent-visible surface before every push:**
  `grep -rinE 'prefix|covering|index-only|three-valued|residual|contiguous' task/instruction.md task/environment/`.
  This caught the instruction describing a histogram bucket as *"covering"* an interval — an accidental
  echo of the covering-index crux, reworded to *"spanning"*.
- **Grep `task.toml`'s `[metadata]` prose after every mechanism change.** Removing the tie-break from
  `instruction.md` left it alive in `solution_explanation`.
- **Instruction token budget:** 736 cl100k on the final push, measured after the last edit.

---

## 9. Reusable checklist

Design:
- [ ] Is every deciding rule **real, external and published**? Invented rules must be disclosed, and
      disclosed rules get implemented.
- [ ] Is each **conditional** — firing only in a sub-case absent from every shipped sample?
- [ ] Is each **noticed** (a structural property of the input) rather than **recalled** (a table)?
- [ ] **Three independent** axes. Keep the one you think is weakest.
- [ ] Can the pipeline be **integer-only**? Ask before reaching for a tolerance.

The discoverability sentence:
- [ ] Present — a task with no such sentence gets B5'd on any rival reading of a withheld convention.
- [ ] **Flat and descriptive.** Names no area, mentions no gap, states no consequence.
- [ ] Compare it against `reduce-palaeomag` invariant 6 word for word before pushing.
- [ ] Anything the sentence now covers (a fairness-bridge word like *contiguous*) is redundant — cut it.

Data:
- [ ] Sample **bit-inert** under every wrong reading — asserted in the generator, not assumed.
- [ ] Sample **does** pin every disclosed step, with a per-step divergence count.
- [ ] Every rival reading you leave unstated asserted **moot on every workload**.
- [ ] No estimate within a safe margin of a rounding or ceiling boundary — this is what lets a
      float solver and an exact solver agree.
- [ ] No config parameter takes the same value everywhere.

Verifier:
- [ ] Type-check every field before comparing values.
- [ ] Reference written from a **different decomposition** than the oracle; agreement measured.
- [ ] Mutants run through the **real verifier** in the built image, reporting node IDs.
- [ ] Accept-side probes for rival readings — they must fail **nothing**.
- [ ] Every rule the instruction states has a fixture, or the rule comes out of the instruction.

---

## 10. One-paragraph version for future me

Accepted in four pushes at pass@5 1/5 (avg@5 0.200), on three real relational-database conventions —
B-tree range delimitation, three-valued comparison semantics, and index-only scans — layered over a
fully disclosed invented cost model, with the shipped workload constructed to be bit-inert under all
three. The expensive lesson was not the design but one sentence of prose. `qc_gate` blocked because a
rival B-tree reading reproduced all twelve shipped plans, which is what every latent-crux task looks
like; the answer is the flat "standard practice governs" sentence `reduce-palaeomag` used. I wrote a
louder version — it said gaps existed, named the two areas holding them, and said filling them
mattered — and pass@2 went 0/2 to 2/2 with both agents deriving everything in thirteen minutes.
Rewriting the same disclosure in a descriptive register, and deleting the word *contiguous* that the
sentence made redundant, took it back to 0/2 with `qc_gate` still green: **same scope, different
register, opposite outcome.** Two other things paid for themselves: asserting at generation time that
every rival reading I left unstated changes no number on any workload (which turned up a real
ambiguity of my own — four histograms whose bucket density disagreed with `ndv`, found not by a gate
but by a pass@2 root-cause table naming a *baseline* query), and keeping the axis I thought was
weakest, which turned out to be a dominant cause in three of the four failures.
