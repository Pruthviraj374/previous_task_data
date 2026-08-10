# dynamo/copybook-extract-decoder — case study

**Status:** Accepted by every automated gate on 2026-08-05. PR labeled `accepted`.
**PR:** https://github.com/handshake-project-dynamo/dynamo-3d7dc7e-data-processing-and-etl/pull/1
**Repo:** `handshake-project-dynamo/dynamo-3d7dc7e-data-processing-and-etl`, branch `submission`.
**Category / Sub-category (pre-seeded):** Data Processing and ETL / **Text processing**.
Benchmarked against Opus-4.8 via Terminus-2.

**Final result: pass@5 = 0/5 solved, avg@5 = 0.000, five good valid failures.**
All seven per-trial rubric criteria PASS on all five trials. Zero timeouts, zero
verifier issues, zero reward hacking. This is the best outcome the spec defines.

Two pushes total: the initial submission, and one batched fix for a QC block.

---

## 1. The task

A mainframe billing system is being decommissioned. Its nightly character extracts must
be moved onto a modern platform, and each extract ships with the COBOL copybook that
describes its records.

- **Agent sees:** `/app/data/` — four extracts (`customers`, `invoices`, `shipments`,
  `tariffs`), each as a `.cpy` copybook plus a `.dat` fixed-length character file, plus
  `/app/data/expected/*.csv` as an end-to-end self-check.
- **Agent produces:** `/app/decode.py`, invoked as
  `python3 /app/decode.py <copybook> <extract> <output_csv>`, plus the four
  `/app/output/<name>.csv` results.
- **Graded on:** six *held-out* extracts with their own copybooks, never shipped.
- **Constraint:** Python standard library only, no network. Load-bearing — PyPI has
  several copybook parsers that would bypass the whole task.

---

## 2. The design reasoning

### 2.1 The crux

> **A copybook is a formal notation whose clauses independently determine (a) how many
> characters a field occupies and (b) how those characters encode a value. Implement the
> notation; do not infer it from the four shipped copybooks.**

The shipped four exercise only the plain half: level numbers and groups, `FILLER`,
alphanumeric and unsigned numeric pictures, and signed pictures in their *default* form
(sign in the zone of the last digit, costing no extra character). The held-out six use
more of the same standard notation:

| Held-out layout | Notation withheld | What it breaks |
|---|---|---|
| `budget` | `OCCURS n TIMES` | field storage multiplied; everything after it shifts |
| `payroll` | `SIGN ... SEPARATE`, on a group *and* on a single field | +1 character per signed field |
| `meters` | `SIGN IS LEADING` (non-separate); `PICTURE IS` / `PIC IS` | sign on the first digit; regex misses the keyword form |
| `claims` | `REDEFINES`; level-88 condition names | overlaid storage adds zero bytes; 88s occupy nothing |
| `ledger` | entries continuing across source lines; `/` comment indicator; mixed-case names | an entry ends at a period, not at a newline |
| `stock` | card-image reference format (sequence area cols 1–6, identification cols 73–80) | sequence number parsed as a level number |

**Why this shape works.** It is the playbook's §9 recommendation applied literally: an
*architectural* crux with many independent, differently-shaped held-out consequences,
rather than a single atomic fact. Disclosure of one mechanism cannot collapse it, because
generalising across the other shapes is still real work. Confirmed empirically — see §4.

### 2.2 Amplifiers dialled up

- **Silent failure** — offsets accumulate, so one mis-sized field shifts every field after
  it. The output is a CSV of plausible-looking values, not an error. (In practice the
  agents' decoders crashed on held-out data rather than producing near-misses, which the
  reviewers explicitly credited as *not* a threshold near-miss.)
- **No self-check** — the extract has no delimiters, headers or types, so a wrong reading
  of the copybook cannot be detected by inspecting the data. All four shipped extracts
  pass under the naive implementation.
- **All-or-nothing** — pytest all-pass gates reward; any one held-out layout wrong scores 0.

### 2.3 Fairness — the two pre-checks, applied before writing code

1. *Does the deciding case need outside knowledge the sample never demonstrates?* Yes —
   COBOL data-description semantics and the fixed reference format. This is field-standard
   and documented (so a domain expert would call the failure fair, and the rubric
   explicitly permits requiring field-standard conventions), but it is absent from
   everything the agent can see.
2. *Is the deciding case written anywhere readable?* No. `instruction.md` states only the
   output schema and value formatting. It never names `SIGN`, `REDEFINES`, level-88,
   continuation, or the column areas.

---

## 3. Gate-by-gate log

### Push 1 (`e9d1e12`) — everything green up to QC

Static checks (25/25), rubric review (**PASS**, all 31 criteria), duplicate check
(**UNIQUE**), validation, pass@2 (**0/2**, all criteria PASS), deep_review (**PASS**),
ava_review (**PASS**), adversarial_review (**PASS**), tier1, qc_eval, qc_exec — all passed.

**`qc_gate` blocked**, exactly as the playbook predicted (§6.6 of the fir case study):

> **C3 — Narrow / Hardcodable Held-Out Coverage.** *"Mutated /app/decode.py lay_out:
> `item.size = unit * item.occurs` -> `item.size = unit` (ignore OCCURS). Verifier still
> returns reward=1 (all 9 tests PASS) because no sample or held-out copybook uses OCCURS."*

QC then built its own `occ.cpy` to prove the mutation was a real violation. The reference
had an `OCCURS` code path that no fixture exercised.

### Push 2 (`afb875f`) — one batched fix, then accepted

Everything below went out in a single commit, because every push re-rolls pass@2/pass@5:

1. **New held-out `budget` extract** with `PIC S9(7)V99 OCCURS 13 TIMES` followed by two
   further fields, so ignoring the multiplier shifts everything after the array.
2. **Instruction gains the occurrence column rule** (`NAME(1)`, `NAME(2)`, …). A repeating
   entry's column naming would otherwise be underdetermined. This *discloses the mechanism*
   — which also pre-empts the "underdetermined / hidden-knowledge mapping" objection that
   QC raised on the `rebuild-release-tarballs` task.
3. **`SIGN IS TRAILING` written explicitly** on the budget total, clearing QC's advisory
   about default-only parameter coverage. All four position × separateness combinations now
   appear explicitly in a fixture.
4. **Negatively-signed zero** added to one shipped and one held-out record (AVA advisory).
   Putting it in a *sample* also witnesses the `0.00`-not-`-0.00` convention, so no sound
   implementation is punished for a rule it could not see.
5. **Ledger's `/` comment given text.** Found by my own mutation sweep, not by a reviewer:
   with an empty `/` line, removing `/` from the comment indicators still scored 1.0,
   because the line contributed nothing either way.
6. **Import check hardened** to reject `__import__`/`eval`/`exec`/`os.system`-style calls,
   with `instruction.md` extended so the assertion still traces 1:1 to a stated requirement.

Result: **QC passed** (44 checks and probes clean), then **pass@5 = 0/5**, label `accepted`.

---

## 4. The finding worth carrying forward: disclosure did not soften the trap

Push 2 disclosed the `OCCURS` mechanism outright in `instruction.md`. The effect was
visible and *contained*:

- pass@2 after disclosure: trial 2 **passed** `test_heldout_budget_extract` — the disclosure
  worked as intended, some agents implemented the repeating field correctly.
- It still scored reward 0, because the other five layouts bit regardless.
- pass@5: `test_heldout_budget_extract` failed in only 1 of 5 trials; the other five
  held-out tests failed in **5 of 5**.

This is the third independent confirmation of playbook §9: **an architectural crux with
several differently-shaped consequences survives disclosure, where a single-fact crux does
not.** On `fir-boundary-metrics` any disclosure collapsed the task to 2/2 solved; here and
on `rebuild-release-tarballs`, disclosing a mechanism outright cost nothing.

**Practical rule:** when a gate demands you disclose something for fairness, first ask
whether your crux is atomic or architectural. If architectural, disclose freely — it is
cheaper than the tightrope-walk, and it buys goodwill on `unambiguous` and
`decisive_rule_disclosed`.

---

## 5. What the agents actually did (pass@5, all five trials)

Every trial converged on the same implementation, independently:

> line-by-line copybook parsing · regex `PIC\s+(\S+)` · sequential offset accumulation ·
> trailing zoned sign only · no `SIGN SEPARATE` byte · no column stripping · verify against
> `/app/data/expected/` · declare complete

The analysis put it plainly: agents "verified correctness by diffing against
`/app/data/expected/`, confirmed clean diffs, and marked the task complete — without ever
attempting to implement or test standard COBOL notation features absent from the shipped
copybooks." In pass@2 they quit at ~16 and ~31 minutes of a 40-minute budget. `low_timeout`
PASS on every trial — nobody ran out of time; they *chose* to stop.

**This is the naive implementation I wrote myself during calibration, reproduced almost
line for line by the benchmarked model.** Writing it before pushing was the single
highest-value step in the build, as it was on `rebuild-release-tarballs`.

---

## 6. Reusable additions to the checklist

Everything in the two earlier case studies still held. New or sharpened here:

- [ ] **Run a mutation sweep on your own reference before pushing, not just a
      one-off thought experiment.** Script it: apply N single-token mutations, run all
      fixtures, print which tests each mutation breaks. Any mutation that breaks *nothing*
      is a QC block waiting to happen. My sweep of 14 mutations found the `/`-comment hole
      that no reviewer had flagged; the one I had *not* included (`OCCURS`) is precisely
      the one QC found. **Enumerate every branch of the reference, then confirm a fixture
      pins each one.**
- [ ] **An unexercised code path in the oracle is a coverage defect, not dead code.** If
      your reference supports a clause no fixture uses, either add a fixture or delete the
      support. (I deleted a `BLANK WHEN ZERO` branch for this reason in the same push.)
- [ ] **Widening a stated constraint gives auditors more surface.** Hardening the import
      check *and* broadening the instruction to match took AVA's advisory count from 2 to 4,
      all of them "here is another way to reach `os.system` that your AST walk misses." A
      static check can never fully honour "do not reach these facilities by any means." It
      stayed advisory because the check enforces a *constraint*, not the grading — but if it
      had blocked, the right fix would have been to narrow the promise, not to chase
      identifier patterns.
- [ ] **Output-schema rules can silently disclose your trap.** I dropped named `OCCURS`
      from the original design precisely because naming the columns would disclose it, and
      kept only clauses whose output shape needed no new rule (`REDEFINES` and level-88 fall
      out of "one column per entry with a PICTURE and a name other than FILLER"). That
      instinct was right for the trap and wrong for QC. Decide deliberately: a clause you
      exclude to avoid disclosure is a clause your verifier cannot pin.
- [ ] **Don't push advisory-only fixes mid-run.** When AVA and adversarial_review posted
      advisories while QC was still running, pushing would have cancelled the in-flight job
      and burned a fresh pass@2 from the daily budget. Waiting cost nothing and let one
      batched push address the blocking finding plus every advisory at once.
- [ ] Sharing a *domain* with an existing TB2 task is fine. The duplicate check found
      `cobol-modernization` at 0.232 lexical similarity and ruled it UNIQUE on the grounds
      that it replicates one program's behaviour while this builds a general decoder. Check
      the neighbour during design so you can articulate the difference — don't avoid the
      domain.

---

## 7. Pointers

| Thing | Where |
|---|---|
| Reference decoder | `task/solution/decode.py` (+ `solve.sh`, which also diffs against the shipped reference) |
| Sample fixtures | `task/environment/data/` — customers, invoices, shipments, tariffs |
| Held-out fixtures | `task/tests/data/heldout/` — budget, payroll, meters, claims, ledger, stock |
| Pristine sample copies for the verifier | `task/tests/data/samples/` |
| Verifier | `task/tests/test_outputs.py` (held-out fixtures read into memory, then `rmtree`'d from `/tests`) |
| Fixture generator, naive baseline, mutation sweep | scratchpad only — `build_fixtures.py`, `naive_decode.py`, `mutate_all.py`; never shipped |
| Commits | `e9d1e12` initial · `afb875f` QC fix |
