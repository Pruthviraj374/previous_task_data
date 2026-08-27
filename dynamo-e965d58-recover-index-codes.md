# dynamo/recover-index-codes — difficulty that rests on guessing is a lottery; difficulty that rests on implementing is not

| | |
|---|---|
| **Outcome** | **ACCEPTED** — every gate green, `accepted` label |
| **Repo** | `dynamo-e965d58-mathematics-and-formal-reasoning`, branch `submission`, fork `Pruthviraj374` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-e965d58-mathematics-and-formal-reasoning/pull/1 |
| **Category / sub** | Mathematics and Formal Reasoning / **Combinatorics and enumeration** (pre-seeded) — first task in this sub-category |
| **Benchmarked model** | `task.toml` names Opus-4.8 / Terminus-2; pipeline reports "Model A" on Daytona |
| **Final commit** | `8ce6617` (11 task commits, 8 distinct designs) |
| **Headline** | **pass@5 = 0/5 solved, 5 good-valid fails, avg@5 = 0.000** — best available outcome. `qc_gate` 37/37 checks clean, zero advisories |

The expensive lesson here is §3 and §4: **eight designs, and the seven that failed all put the
difficulty in something the agent had to *guess*.** Guessing is a lottery that averages out over
five trials. The design that was accepted put the difficulty in a branch the agent has to
*implement*, and implementations do not average out.

---

## 1. What the task asks

A retired stock-control system assigned every product word an integer index code. The program is
gone, the rule was never written down, the archive survives — and **is** the specification.

- **Agent sees:** `instruction.md` and `/app/data/archive.json` — 120 records, each `{id, word,
  code}`, words over `a`–`d`, length 9–14. Nothing else (`environment/Dockerfile` copies only
  `data/`).
- **Agent produces:** `/app/solve.py`, invoked `python3 /app/solve.py <input_json> <output_json>`,
  emitting a JSON object keyed by `id` with a plain integer per word. Plus its self-check run on
  the archive at `/app/output/result.json`.
- **Graded on:** exact integer equality — the archive re-run, plus four held-out batches
  (`runs`, `period_two`, `period_three`, `tail_overlap`, 72 words total).

The rule, withheld: split the word by the **Lempel-Ziv (1976) factorisation**; each factor
contributes `len(factor) x (1 + index of its smallest letter)`; contributions are weighted by
`w(n,j) = 5 - 3n + 2nj + 7j^2` over word length `n` and factor position `j`.

Integer-only grading throughout, deliberately — there is no tolerance anywhere, so no failure can
be dismissed as a threshold or rounding artifact.

---

## 2. The crux, and the invariants that keep it alive

**The crux is an implementation defect, not a recall defect.** The LZ definition says an earlier
occurrence need only *start* earlier — it may run past the point where the factor begins, so a
factor may read the letters it is itself producing. The natural implementation caps the match at
the current position, because that is what bounding a search against already-processed text
normally means.

The grader caught precisely this, in the one trial that produced a deliverable:

> "exploratory step 3 used the correct overlapping search (`w.startswith(pat, s)`, no end bound),
> but the final solve.py switched to `word.find(pattern, 0, i)` which caps the search end at `i`,
> preventing overlap detection. This is an **edge-case trap / implementation regression** — the
> bug was invisible on the 120 archive words (which factor identically with or without the cap)
> and only exposed by the 72 held-out overlap-requiring words."

The agent got the rule *and* wrote the correct search while exploring, then regressed to the
capped form in the final program. That is the shape worth designing for.

**Invariants, all machine-checked by `scratchpad/gen_lz.py`, which refuses to emit fixtures if any
break:**

1. **The archive is inert under the cap** — all 120 archived words factor identically with and
   without overlap, so a capped implementation reproduces every archived code exactly and has no
   way to discover the error. Measured: **0 / 120**.
2. **Held-out is fully live** — **72 / 72** wrong under the cap.
3. **The archive determines the rule** — 11 candidate readings x 5 weight families = 55 pairings,
   solved exactly over the rationals; exactly one survives, 54 refuted. The candidate library must
   contain every rival reading the design makes plausible (see §3, dead end 6).
4. **The factorisation is cross-checked against an independent formulation** — a longest-first
   search using `str.startswith(sub, start)`, which honours the overlap without any index
   bookkeeping, over 250 words that deliberately include runs and periodic tails.
5. **Four shapes force the overlap**, not one — long run, period-two tail, period-three tail,
   repeated two-letter tail. Straight from `retired-normalizer` §4.2.

Why the error is large rather than marginal: a capped match yields a *short* factor, which
increases the factor count and shifts the position `j` of every later factor, so every subsequent
weight changes. Observed deviations ran **+50% to +296%**, systematically inflated.

---

## 3. Dead ends — seven designs, with the graders' own wording

### 1. Team-split counting, five scales — `pass2` 2/2 solved, four times
Each scale change only moved which shortcut won. No grader quote worth keeping; the lesson is that
re-tuning a solved design's parameters is not a fix.

### 2. Bead designs (row / ring / bracelet) — `pass2` 2/2
Agents applied Burnside correctly, periodic and even-*n* cases included.

### 3. Graph labellings up to automorphism — `pass2` 2/2
The agent recognised Burnside at step 2, **confirmed the sample was rigid at step 4**, and wrote
its own symmetric tests (K8, K4,4, C6). **Symmetry was the headline, so the agent tested it.** A
crux you advertise as the point of the task is not a crux.

### 4. Withheld rule, Lyndon split, `f = len x min-letter` — `pass2` 0/2, **pass@5 3/5 solved**
First design to pass pass@2. The grader was explicit that the *designed* crux never fired:

> "Neither agent reached the author's intended architectural crux (handling non-strictly-decreasing
> Lyndon splits / repeated blocks)."
> "All three passing trials independently implemented Duval's algorithm … The convergence …
> strongly suggests this is **recalled from training-data knowledge** of the standard algorithm."

The two failures were upstream, at rule recovery: "the agent could not identify the correct
block-contribution function f(block)" — taxonomy "Analytical failure — incomplete candidate
enumeration".

### 5. Same, `f` = base-5 numeral + `j^2` weight — `pass2` **2/2 solved in 5.5 and 7 minutes**
A regression, and an instructive one. Both agents listed a base-5 reading among their **first three**
candidates. **Never make `f` a base-N numeral reading** — it is the first thing tried, every time.
Widening the search space by picking a "harder-looking" `f` deleted the only lever that was working.

### 6. Lyndon + non-alphabetical letter ranking (`a<c<b<d<e`) — `pass2` 0/2, **`qc_gate` FAIL**
Difficulty worked; soundness did not. `qc_gate`: "Missing Definition, Field, or Data" (Major, **no
evidence recorded**), with advisories "Underdetermined / Hidden-Knowledge Mapping" and "Narrow /
Hardcodable Held-Out Coverage".

The real defect, found by reading the pass@2 analysis rather than the finding text: one trial's
reading `len x natural_rank(first char)` **fit all 120 archive records with zero residual**. It was
not merely wrong — it was *indistinguishable from the truth on the archive*.

And the cause was structural, not a bad seed: keeping the letter-order trap silent forces every
archived word to split identically under both orders, which makes every block a Lyndon word under
the ordinary alphabet too, and **a Lyndon word begins with its smallest letter**. Measured over
20,000 words: of the 10,886 that split identically under both orders, **0** contained a block that
could separate the two readings; of the 9,114 that split differently, 4,991 did.

> **"Archive silent about trap X" and "archive determines rule Y" can be mutually exclusive for a
> structural reason. Prove it with a sweep before shipping, not after.**

### 7. Same, contribution ranked in the system's own order + tightened instruction — `pass2` **2/2 solved**
The rule change was correct and fixed `qc_gate`. The *instruction tightening shipped alongside it*
handed over the answer. Two leaks, both quoted in the analysis:

- I wrote that the ranking governs "taking a letter's position in the alphabet". Trial
  `task__TsktLwe` built `LETTER_POS = {a:1, c:2, b:3, d:4, e:5}` **at step 4** and finished in
  **11.5 minutes**.
- I wrote "integer polynomial of total degree at most 2 in n and j … coefficients … may be
  negative". The analysis writes the recovered weight back as "total degree ≤ 2 in n and j, integer
  coefficients" — read off the instruction, not recovered from the archive.

### 8. Same, over-disclosure reverted — `pass2` 0/2, `qc_gate` PASS, **pass@5 4/5 solved**
The revert worked exactly as intended: `difficulty_crux` **PASS** on both pass@2 trials for the
first time, and the same rule that had been solved in 11.5 minutes became unreachable in 60. Both
agents searched hundreds to **900+** candidate contribution functions and never included the right
one.

Then pass@5 returned **4/5 solved on the same commit whose pass@2 was 0/2.**

> That spread is the finding. Same code, same archive, same rule. It is not difficulty — it is a
> **search lottery**: whether a trial passes turns on whether the agent's candidate enumeration
> happens to contain the right function. Four enumerations did. The fifth tested block length,
> letter counts, base-2 through base-6 encodings and **6,822 injective digit maps**, and timed out.

`difficulty_crux` was **NA on 3 of the 4 solvers**. Across every trial ever run against the Lyndon
family, **no agent ever fell into either designed trap.** Graders: *"the documented traps were
avoided, not hit."* Duval's algorithm is fifteen lines, agents recall it, and it handles repeated
factors and a relabelled alphabet correctly for free.

---

## 4. What actually worked

**Move the difficulty from a guess to an implementation.**

The decision came from this directory, not from invention. `retired-normalizer` §4.2 — *put the
difficulty where the failures actually are* — records that in that task **all** agents recovered
the withheld rules and failed on **HNF for rank-deficient matrices**; `rebuild-vestra-systems`
records the same shape with LAPACK Bunch-Kaufman pivot conventions. Both accepted tasks put the
crux in a **supporting algorithm's fallible branch**, never in the headline rule.

So the split was swapped from Lyndon/Duval to the Lempel-Ziv factorisation, chosen against one
criterion: *does the definition carry a branch that is genuinely easy to implement wrongly, as
opposed to easy to forget?* Duval has none. LZ has exactly one, and it is the classic one.

Everything that had already cleared a gate was kept unchanged — the withheld rule, the **searching**
oracle, the 55-pairing decisiveness proof, the verifier hardening. Only the supporting step moved.

**Why it survives where guessing did not:** an enumeration either contains the answer or does not,
and across five trials it usually does. An implementation choice is made once, in the final
program, by every trial — and the archive cannot tell anyone it was wrong. pass@5 went 4/5 solved →
**0/5**.

The result was also stratified, which is what a healthy task looks like: Cluster A (1 trial) hit the
intended LZ crux; Cluster B (4 trials) failed at rule recovery. The withheld rule was still pulling
its weight as a second, independent axis.

---

## 5. Gate-by-gate log

| Gate | Verdict | Fix | Commit |
|---|---|---|---|
| `changes`, `cosine_similarity`, `similarity`, `ratelimit`, `validation` | **never failed** | — | — |
| `review` | **never failed** on any withheld-rule design (2m27s–3m39s) | — | — |
| `tier1`, `deep_review`, `ava_review` | **never failed** once reached | — | — |
| `qc_gate` | FAIL — E4: held-out answers reachable by the agent-authored solver | stage each input alone in a fresh dir, drop to `nobody`, seal `/tests` 0700, reject symlink output | (early) |
| `qc_gate` | FAIL — "Missing Definition, Field, or Data" (no evidence) | root cause was underdetermination: rank the contribution in the system's own order so first == smallest, and put both natural-alphabet rivals in the candidate library | `7b32b90` |
| `qc_gate` | **PASS 37/37, zero advisories** on the LZ design | — | `8ce6617` |
| `qc_eval` / `qc_exec` | never failed | — | — |
| `pass2` | FAIL 2/2 across designs 1–3, 5, 7 | see §3 | — |
| `pass2` | **PASS 1/2** on the LZ design | — | `8ce6617` |
| `trials` | FAIL 3/5 solved, then 4/5 solved | redesign, §4 | — |
| `trials` | **PASS 0/5 solved, 5 good-valid, avg@5 = 0.000** | — | `8ce6617` |

`trials` never even ran until `1c4fee1` — every earlier cycle died at `pass2` or `qc_gate`.

---

## 6. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| `pass2` 2/2 solved, agents name the technique fast | Move the crux into a step the agent must *implement*, not one it must recall or guess | Do **not** re-tune the same design's parameters, and do **not** pick a "harder-looking" rule — design 5 did exactly that and got solved in 5.5 minutes |
| pass@5 mostly solved but pass@2 failed on the same commit | Treat it as **search variance** and change the *kind* of difficulty | Do **not** iterate the rule again. Two more `f` choices bought 3/5 then 4/5 |
| `qc_gate` "Missing Definition" with **no evidence recorded** | Read the pass@2 analysis for a rival reading that fits the whole archive; fix by making the archive *determine* the rule | Do **not** answer it by adding prose to `instruction.md`. That is what killed design 7 |
| Rival reading fits all archived records | Put every plausible rival in the candidate library and prove the archive refutes it | Do **not** trust `test_archive_pins_exactly_one_rule` — it proves decisiveness only *across your own library* |
| A designed trap never fires | Check `difficulty_crux` in the rubric. `NA`/`FAIL` on solvers means it is inert — replace it | Do **not** add a second trap of the same kind alongside it |
| Both traps inert, difficulty is real but thin | Pick a supporting algorithm with a genuinely fallible branch | Do **not** shorten `[agent].timeout_sec` to manufacture difficulty, and do not add busywork |
| Agents defeat the branch at step 4 | Name the standard and restate none of its rules (`vestra`, `filer-audit` §2) | Do **not** paraphrase the branch in the instruction — that *is* the trap, handed over |

---

## 7. Bugs I introduced myself

1. **Raw `"` inside a TOML basic string.** `task.toml` explanations are basic strings; an unescaped
   quote silently broke task discovery and harbor reported the wholly misleading
   `ValueError: Either datasets or tasks must be provided.` Use `'...'` inside, and validate with
   `tomllib.load` **before** running harbor — a regex sanity check is not enough and passed happily.
2. **A poller that read an API failure as success.** `gh pr checks | grep -c pending` returned 0
   because `gh` had timed out and the *error text* contained no "pending". It reported "settled"
   with no result. Require a real `^review / <name> <status>` line before drawing any conclusion.
   This nearly caused a fix to be pushed against a verdict that did not exist.
3. **Over-disclosure while fixing a soundness gate** (design 7). The gate needed determinacy; I
   also rewrote the instruction. Two changes, one gate cycle, and the difficulty died. **Change one
   variable per gate cycle** — the isolated revert in `1c4fee1` is the only reason the cause was
   ever identified.
4. **Shipped an ambiguity a sweep would have caught.** The design-6 rival reading was findable in
   minutes with a 20k-word sweep; instead it cost a full `qc_gate` cycle. A later candidate,
   `len x natural_rank(first)`, was caught *before* shipping by exactly such a probe — it admitted
   2 readings, not 1.

---

## 8. Process rules learned the hard way

- **Never push while any check is pending.** `pass2` and `trials` are rate-limited and each runs
  ~1h; a push cancels the in-flight run. Confirm `gh pr checks 1 | grep -c pending` is 0 first.
- **A passing `pass2` does not carry over.** Every push re-runs it from scratch on the new head.
- **Labels lag; `gh pr checks` is the authority.** `in-progress,needs-revision` stayed on the PR
  through several fully green runs.
- **Duration is a weak tell.** Solved `pass2` runs finished in 11m / 45m / 48m; struggling ones ran
  1h05–1h11. Useful for expectation-setting, never for a conclusion.
- **`in-progress-timeout` does not count** toward the ≥3 bar and is latency variance — re-roll, do
  not redesign. An *idle-loop* timeout after genuine analysis **does** count as a good valid fail.
- **Check a suggestion's `slug=` and `date=`.** Stale suggestions from retired designs persist on
  the PR. The one that drove the letter-ranking design was genuinely fresh — verified by its
  timestamp landing after the commit and by it citing that run's own trial detail.
- **Do not push a README-only change to an accepted PR.** It re-triggers the whole rate-limited
  pipeline, and pass@ variance could cost the `accepted` label for no benefit.

---

## 9. Checklist for the next task

- [ ] Read §"The crux" and §"Dead ends" in every file here **before** designing.
- [ ] Is the difficulty something the agent must **implement**, or something it must **guess**? If
      the latter, expect it to average out over five trials.
- [ ] Name the supporting algorithm's fallible branch explicitly, to yourself. If it has none
      (Duval, Burnside), the trap will be inert no matter how the data is built.
- [ ] Sweep 10k+ random inputs to confirm: sample inert under the wrong branch, held-out fully live.
- [ ] Sweep for rival readings that fit the whole archive. Put every one in the candidate library.
- [ ] Rotate held-out through ≥3 shapes that trigger the branch differently (`retired-normalizer`
      §4.2).
- [ ] Define every term; name every standard; **describe no rule the archive is meant to determine**.
- [ ] Validate `task.toml` with `tomllib.load` before every harbor run.
- [ ] Oracle 1.0 / nop 0.0 after **every** change under `task/`, `task.toml` included.
- [ ] One variable per gate cycle.

---

## 10. One-paragraph version for future me

Eight designs; the seven that failed all made the agent **guess** something — a counting rule, a
letter ordering, a contribution function — and guessing averages out: the same commit scored 0/2 at
pass@2 and 4/5 at pass@5, because whether a trial passes turns on whether its candidate enumeration
happened to contain the answer. The accepted design kept the whole withheld-rule scaffold (which
`qc_gate` likes: searching oracle, 55-pairing decisiveness proof, hardened verifier) and swapped
only the supporting step, from Duval's Lyndon factorisation — fifteen lines, recalled perfectly,
inert as a trap — to the Lempel-Ziv factorisation, whose definition lets a match overlap the factor
it is producing and whose natural implementation caps the search at the current position. All 120
archived words factor identically either way, so the bug is invisible in the only data the solver
can check against; all 72 held-out words expose it. pass@5 went from 4/5 solved to **0/5**, and the
grader found an agent that wrote the correct overlapping search while exploring and then regressed
to `word.find(pattern, 0, i)` in its final program. Difficulty that rests on implementing a fallible
branch does not average out. Difficulty that rests on guessing does.
