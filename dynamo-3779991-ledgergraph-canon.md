# dynamo/ledgergraph-canon — three full redesigns, and the one that survived disclosure

| | |
|---|---|
| **Outcome** | **ACCEPTED** — every gate green, `accepted` label |
| **Repo** | `dynamo-3779991-data-querying-and-databases`, branch `submission`, fork `charan-sr` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-3779991-data-querying-and-databases/pull/1 |
| **Category / sub** | Data Querying and Databases / Graph and semantic queries (pre-seeded) |
| **Benchmarked model** | `task.toml` names Opus-4.8 / Terminus-2; stickies call it `Model A` |
| **Final commit** | `0e18607` |
| **Headline** | **pass@5 = 0/5 solved, avg@5 = 0.000, 5 good valid fails.** Best possible outcome. Reached only on the **third full redesign** of this task, after ~28 commits total |

This is the single most expensive task in this corpus to date — three genuinely different
designs (GRAPHOS path-queries → Cartograph/SPARQL property paths → Ledgergraph/RDF
canonicalization), each one killed by the same underlying wall stated in
[`dynamo_enumeration_defeats_evidence_inference`](../dynamo_enumeration_defeats_evidence_inference.md):
against this model, "disclose an arbitrary convention just enough that sample evidence
disambiguates it" does not survive `pass@2`. What finally worked was giving up on disclosure
calibration entirely and picking a crux where **disclosure was free** — a real, externally
documented algorithm the model has never had to *derive*, only *apply completely*.

---

## 1. What the task asks

A retired internal record-linkage store, Ledgergraph, held facts about entities and the
relationships between them, some identified only by blank nodes. The agent writes
`/app/solve.py`, invoked `python3 /app/solve.py <graph_nt> <output_nt>`, that reproduces
Ledgergraph's own canonical N-Triples serialization of any export in the same format.

- **Agent sees:** `instruction.md`, `/app/data/graph.nt` (one small export, 3 triples, 1 blank
  node), `/app/data/store_notes.md` (the N-Triples format and what Ledgergraph produced), and
  `/app/data/sample_expected.nt` (Ledgergraph's real output for the sample, as a self-check).
- **Graded on:** the sample plus four held-out exports, `tests/data_heldout/` overlaid at
  verify time, all-or-nothing across 8 tests (4 fixtures × direct-run, plus 5 derived-at-test-
  time variants).
- **Constraint:** Python standard library only, no third-party packages, no network.

`store_notes.md` names the governing standard — **RDF Dataset Canonicalization, W3C RDFC-1.0,
formerly URDNA2015** — and states only that no export here needs more than the algorithm's
first step (Hash First Degree Quads); it never restates the hash construction itself.

---

## 2. The crux, and the invariants that keep it alive

> **A blank node's canonical identifier must come from a content hash of its own local
> neighbourhood, not from any positional or label-based shortcut.** The dangerous naive
> reading — assign canonical IDs in file-appearance order — is deterministic, consistent, and
> reproduces the correct answer on the shipped sample (one blank node, so there's no order to
> get wrong) and on many small hand-written graphs, including the first draft of one of this
> task's own fixtures (caught and fixed before shipping by deliberately swapping which blank
> node appeared first and re-checking against pyld).

| Fixture | Forces | Sample inert because |
|---|---|---|
| `hA` | file order ≠ hash order | sample has only 1 blank node — no order to get wrong |
| `hB` | same rule at scale (longer chain) | same |
| `hC` | literal escaping (quotes, `@lang`, non-default datatype) survives relabeling | sample's one literal is a plain string |
| `hD` | *(added post-acceptance-block, see §4.3)* an RDF graph is a **set** of triples — a repeated input line collapses to one output line | sample has no repeated line |

**Load-bearing invariants:**

1. Naive-order mutant, run through the **real verifier**, scores 0.000 — passes
   `test_reproduces_shipped_sample` and `test_heldout_literal_fidelity` but fails `hA`/`hB` and
   their test-time-derived variants.
2. Reference differential-tested against pyld's real URDNA2015 — several hundred randomized
   graphs, 0 mismatches, plus a targeted duplicate-triple regression added in the final round
   (§4.3).
3. First-degree hash collisions are asserted on, never silently mishandled — no shipped
   fixture has one (would need the algorithm's N-degree step, deliberately out of scope;
   `store_notes.md` states this directly).
4. `/tests` stays out of reach of `/app/solve.py`: privilege-dropped subprocess execution,
   root-only `tests/` directory. A constructed delegation attack (importing the verifier's own
   `_reference()`) scores 0.000 through the real verifier.
5. No crux vocabulary anywhere agent-visible: never "hash", "first-degree", "placeholder",
   "collision", "N-degree", "duplicate", or "set" in `instruction.md`/`store_notes.md`. The
   sentence that satisfies discoverability — "computed the way RDF Dataset Canonicalization
   defines it" — already covers set semantics *by naming the standard*, without ever stating
   the consequence.

---

## 3. Dead ends — two full redesigns, ~24 commits, before this one

### 3.1 Design 1 — GRAPHOS (path-query semantics), 16 commits

Same category, different crux family entirely: shortest/counted path semantics over a
temporal graph (edge-trail vs node-uniqueness, point-in-time `as_of` resolution,
count-and-continue past target, no-empty-path when `start == target`). Every one of four
axes went through the identical cycle: leave it implicit → `pass2` blocks it as a spec gap
(a rival sound reading exists) → disclose the rule outright → `pass2` returns 2/2 solved
because the disclosed rule is trivially implementable. By the fourth axis, `pass2`'s own
analysis said it in as many words: *"no meaningful divergence... this convergence across two
different agents suggests these rules are clearly derivable from the provided specification
rather than requiring obscure inference."* One trial derived all four cruxes in a single
~11,590-token reasoning block. **Fully disclosed means derivable — the catch-22 that killed
this design has its own memory file,
[`dynamo_enumeration_defeats_evidence_inference`](../dynamo_enumeration_defeats_evidence_inference.md).**

### 3.2 Design 2 — Cartograph (SPARQL 1.1 property paths), 3 commits

The attempted escape: name a **real, published standard** instead of inventing rules, on the
theory that "real and external" would dodge the disclosure trap that killed GRAPHOS. It
looked like it worked at first — one genuine `pass2` valid fail (later shown to be a timeout
artifact, not a real stump) — but after raising the agent budget to fix the timeout, `pass2`
came back **2/2 solved three consecutive times**, with the third run's own reviewer
commentary naming why: convergence on `Counter`-based multisets and visited-set BFS across
two different models was *"consistent with agents drawing on established SPARQL
implementation knowledge rather than first-principles derivation."*

**The refinement this bought:** naming a real standard only escapes the trap if the standard
is **genuinely obscure**, not merely real. SPARQL property paths are mainstream and
thoroughly documented — countless tutorials cover exactly the dedup-vs-multiset distinction
these axes were built on. The filter that survived: *would a competent engineer already know
the decisive edge case, or would they need to open the spec?* SPARQL fails that test for this
model; RDF blank-node canonicalization — normally reached for as a library call (rdflib,
pyld, jsonld-signatures), never implemented by hand — was chosen for Design 3 specifically
because it should pass it.

### 3.3 Rejected on paper before Design 3 was built

Per the refined memory rule, the design search explicitly asked of RDF canonicalization: is
this the subject of a thousand tutorials (SPARQL's failure mode) or a fact that lives in one
spec most engineers never read start-to-end? Blank-node canonicalization is the latter —
confirmed by the fact that every mainstream RDF library exposes it as a single opaque
function call rather than something practitioners reimplement.

---

## 4. What actually worked

### 4.1 Disclose the standard, restate nothing, scope out the hard half honestly

`store_notes.md` names RDFC-1.0/URDNA2015 as a locator and states plainly that no export here
needs more than the algorithm's *first step* (Hash First Degree Quads) — the recursive
N-degree step, needed only when two blank nodes tie at the first-degree level, is out of
scope by construction and the notes say so directly, rather than leaving an agent to guess
whether to invest in it. This is the same "name the standard, state the scope, restate
nothing" move validated repeatedly elsewhere in this corpus
(`dynamo-093d3d6`, `dynamo-a4b5561`, `rebuild-release-tarballs`) — but applied here to an
algorithm rather than a mechanism, which is what let it survive three `pass2` measurements
without a single solve.

### 4.2 Verify the crux is genuinely un-derivable, not just unrecalled

Before shipping, the design was checked against pyld's actual source for the hash
construction (the `_:a`/`_:z` self-vs-other placeholder convention, the exact
sort-then-concatenate-then-SHA-256 order) — read directly from a real conformant
implementation, not from memory, then differential-tested against that same implementation
across several hundred randomized graphs. `pass@5`'s own trace confirms the bet: all four
agents that produced code independently derived the **same** `_:a`/`_:z` convention and
SHA-256 structure (correctly — this part is well-represented in training data, since it's the
literal spec text), and it was never what stumped them.

### 4.3 The one gate that blocked: a genuine oracle bug, found and fixed in one round

`qc_gate` blocked once, on `9061b6d`, with a real "Oracle Edge-Case or Logic Bug": QC
constructed a valid N-Triples export with a literal duplicate triple line and found the
reference emitted the duplicate line twice in its canonical output. This was **not** a repeat
of the GRAPHOS/Cartograph disclosure-vs-difficulty pattern — it was a mechanical correctness
bug (RDFC-1.0 canonicalizes a *set* of triples; the reference never deduplicated parsed
triples before hashing/serializing), the same class of finding nearly every task in this
corpus eventually hits from QC. Recognising that distinction *before* reacting — reading the
full three-design history, checking `QC-BASE` against HEAD, confirming the finding wasn't
another instance of the enumeration wall — is what kept this round to one fix instead of a
fourth redesign.

**The fix, verified before pushing:** dedupe parsed triples (`list(dict.fromkeys(...))`)
immediately after parsing, in both `solution/canon_solve.py` and the verifier's independent
`_reference()` copy. Checked against pyld on the QC-cited shape plus three structural
variants and a same-graph-two-serializations invariant; confirmed behavior-neutral on all
four existing fixtures (byte-identical before/after, since none contained a duplicate); a
60-graph regression fuzz with no duplicates confirmed no unrelated regression. A fifth
fixture, `hD` (a statement repeated verbatim), was added to pin the fix as a held-out
discriminator rather than leave it as an unexercised branch — confirmed the *old* buggy code
diverges from pyld only on `hD`, not on the other four, so it's a real test rather than
padding. `harbor` oracle=1.0/nop=0.0 reconfirmed; README.md and `task.toml`'s three
explanation fields updated in the same commit.

**`hD` then turned out to be load-bearing for the actual result**, not just insurance: 4 of 5
pass@5 trials failed *specifically* on it (see §5.2).

---

## 5. Gate-by-gate log (Ledgergraph design only — see §3 for the two prior designs' full histories)

| Push | Commit | Result |
|---|---|---|
| 1 | `9061b6d` | static/rubric/duplicate/validation ✅ · **pass2 ✅ 1/2, 1 valid fail** (1h3m, genuine) · deep_review ✅ · ava_review ✅ (1 non-blocking advisory) · qc_eval/qc_exec/tier1 ✅ · **qc_gate ⛔** — Oracle Edge-Case or Logic Bug (duplicate-triple dedup) |
| 2 | `0e18607` | everything ✅ — pass2 unaffected (no agent-visible change) · deep_review/ava_review/qc_eval/qc_exec/tier1/**qc_gate ✅** (37 checks, empty fix list) · **trials ✅ pass@5 0/5, avg@5 = 0.000, 5 good valid fails** → `accepted` |

### 5.1 What the two prior designs' own histories say about this one

Three consecutive `pass2` measurements on Cartograph (2/2 solved every time) versus one
genuine valid fail plus 0/5 on Ledgergraph is the sharpest within-task confirmation in this
corpus of the refined rule: naming a standard is not the variable that matters, its
*obscurity to the model* is.

### 5.2 pass@5, and what the model actually did

Two root causes account for all five failures:

- **Root cause A — edge-case trap / overconfidence early-quit (4 of 5 trials).** All four
  agents correctly implemented the algorithmically hard part (Hash First Degree Quads,
  `_:a`/`_:z` substitution, SHA-256, canonical label assignment by ascending hash) — passing 6
  of 8 tests — and uniformly omitted deduplicating repeated input triples before output. The
  only self-check fixture available during development (`graph.nt`/`sample_expected.nt`)
  contains no repeated triple, so the gap was invisible until `hD`. One trial's own reasoning
  trace shows it explicitly: *"RDF graph is set; duplicates should be ignored"* — and then
  chose not to implement it anyway.
- **Root cause B — terminal wedge (1 of 5 trials).** A heredoc write of `/app/solve.py` was
  truncated mid-keystroke-string; the shell sat waiting for the closing delimiter for ~56 of
  60 minutes. Mechanical, unrelated to algorithmic difficulty.

`approach_validity` PASS 5/5, `near_miss` FAIL (= is a near-miss) 4/5 — the grader's own
framing: *"four near-misses out of five... a strong signal that the task is consistently
discriminating on a narrow property (deduplication) rather than on the concept the task is
nominally testing... this does not indicate the task is too easy — the agents genuinely
struggled to implement the full standard."* `task_specification` PASS 5/5 — deduplication is
explicitly judged derivable from the cited standard, not an undisclosed rule.

---

## 6. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| `pass2` returns 2/2 solved on a design built around a named real standard | Ask: is this standard the subject of countless tutorials (SPARQL, common config formats), or a fact that lives in one spec most engineers reach for a library instead of reading? Only the second survives | Assume "real and external" alone is sufficient — confirmed insufficient a fourth time on this task alone (three consecutive Cartograph 2/2s) |
| An invented rule gets disclosed to satisfy a fairness gate, then solved 2/2 | Recognise the catch-22 immediately (see the dedicated memory file) rather than re-tuning the wording — re-tuning oscillates between the fairness gate and the difficulty gate without escaping either | Spend another round adjusting how much of an *invented* rule to disclose. GRAPHOS burned 4 axes this way before the whole design was abandoned |
| `qc_gate` finds a genuine correctness bug in the reference after a from-scratch redesign | Before fixing, explicitly check it against the redesign history: is this the same structural pattern that killed prior designs, or an ordinary QC finding? Say which, out loud, before proceeding | Treat every post-redesign gate failure as evidence the new design is also doomed — this one was a one-line dedup bug, fixed and accepted in the very next round |
| A QC-found gap gets fixed in code | Add a held-out fixture that pins it, and confirm the *pre-fix* code actually diverges only on that fixture (not a coincidental fail-everything mutant) | Fix the reference and move on without a regression fixture — this task's `hD` fixture is what actually decided the final pass@5 result (4/5 failures landed on it) |

---

## 7. Process rules confirmed

- **Never push while a run is in flight** — checked before every push across all three designs.
- **`QC-BASE` vs `HEAD`** checked before trusting any qc_gate sticky, every round.
- **Recalibrate locally (`harbor run -p . --agent oracle`=1.0, `nop`<1.0) before every push**,
  including a push that "obviously" wouldn't break anything.
- **README.md and `task.toml`'s three explanation fields synced in the same commit** as any
  fixture or reference change — fixture counts (4→5) and held-out counts (3→4) updated
  alongside the fix, not after.
- **No AI/Claude attribution anywhere** in commits, PR body, or task files.
- **Category/subcategory pre-seeded, never edited** across all three designs (Data Querying
  and Databases / Graph and semantic queries).
- **Long iteration on one task warrants a deliberate stop-and-verify checkpoint.** After ~25
  commits without acceptance, the user paused the session and required the next failure to go
  through a full re-read of the handoff, the playbook, and cross-task memories before any fix
  — rather than reactively patching. That checkpoint is what correctly distinguished "this qc_gate
  finding is the same wall as before" (it wasn't) from "this is ordinary iteration" (it was),
  and the task was accepted one round later.

---

## 8. Reusable checklist

Design:
- [ ] Is the crux's governing authority **real and named**, or invented? Invented rules that
      get disclosed for fairness get implemented — confirmed 4+ times on this task's first
      design alone.
- [ ] If real: would a competent engineer already know the decisive edge case, or would they
      need to open the spec? Only the second survives `pass2` against this model. Mainstream,
      tutorial-heavy standards (SPARQL) fail this test; algorithms normally reached for as a
      library call and rarely hand-implemented (RDF canonicalization) pass it.
- [ ] Verify the hash/algorithm construction against a **real conformant implementation's
      source**, not memory, then differential-test against it across hundreds of randomized
      inputs before writing any task files.
- [ ] State the algorithm's scope honestly (what step is and isn't required) rather than
      leaving an agent to guess whether to invest in an out-of-scope path.

Process:
- [ ] On a `qc_gate`/gate finding after a redesign, explicitly compare it against the prior
      designs' failure history before reacting — say out loud whether it's the same structural
      wall or ordinary iteration.
- [ ] Fix the reference *and* the verifier's independent copy identically, every time.
- [ ] Pin any QC-found gap with a held-out fixture, and confirm the pre-fix code diverges only
      there.
- [ ] After ~20+ commits without acceptance, treat the next failure as a checkpoint, not
      another autonomous cycle — full re-read before any fix.

---

## 9. One-paragraph version for future me

Three full redesigns and ~28 commits to reach `pass@5 0/5, avg@5 = 0.000` — the best possible
outcome — on a task whose real subject was never graph queries at all but the disclosure-vs-
difficulty catch-22 this playbook already had a memory file for. GRAPHOS (path-query
semantics) died the way every invented-rule task in this catch-22 dies: disclose enough for
fairness, `pass2` solves it 2/2, four times running. Cartograph (SPARQL 1.1 property paths)
tried the obvious escape — name a *real* standard instead of inventing one — and still died
2/2, three consecutive measurements, because SPARQL is mainstream enough that naming it just
told the model which memorized recipe to run. The refinement that survived: a real standard
only escapes the trap if it's **genuinely obscure to the model**, not merely real and
published — the filter is whether a competent engineer would need to open the spec or would
already know the answer cold. RDF blank-node canonicalization (RDFC-1.0/URDNA2015) passed
that test, because it's normally reached for as a library call, never hand-implemented. The
only gate that ever blocked this final design was a genuine, mechanical `qc_gate` finding — a
missed dedup step, since RDFC-1.0 canonicalizes a *set* of triples and the reference emitted
duplicate output lines for a duplicate input line — fixed in one round after explicitly
checking it wasn't a fourth instance of the disclosure wall. That fix's own regression
fixture, `hD`, turned out to be exactly what the model tripped on: four of five pass@5 agents
correctly derived the hard half of the algorithm and uniformly missed the one-line
deduplication step, an omission the shipped self-check fixture was structurally incapable of
exposing.
