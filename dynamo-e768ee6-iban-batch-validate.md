# dynamo/iban-batch-validate — gate failures, fixes, and what finally worked

Repo: `dynamo-e768ee6-data-processing-and-etl`, PR #2, branch `submission`, fork
`charan-sr`.
Category: **Data Processing and ETL** / Sub-category: **Data validation** — the first
playbook entry for this exact subcategory (prior Data Processing and ETL entries were
Text processing x2 and Geospatial data processing x1).
Benchmarked against Opus-4.8 via Terminus-2. Accepted 2026-08-08 at commit `e3637bd`.

**Final result: pass@5 = 0/5 solved, avg@5 = 0.000, 3 good valid failures, 2
in-progress-timeout (still counted toward the ≥3-total bar), 0 task/verifier issues, 0
reward hacking.** `approach_validity` PASS on all 5 trials — no fairness objection
survived. Eight pushes across roughly nine hours of gate cycles, no infra outages.

---

## 1. The task

A payments-processing pipeline validates the IBAN on every outgoing SEPA payment
instruction before submitting a batch to the clearing network.

- **Agent sees:** `/app/data/records.csv` (12 records, all GB/IE/AT/LU) and
  `/app/data/expected.csv` as an end-to-end self-check.
- **Agent produces:** `/app/validate.py`, invoked as
  `python3 /app/validate.py <input_csv> <output_csv>`, writing `record_id,valid` rows
  (`valid` a literal `true`/`false`), plus a self-check run at
  `/app/output/validation.csv`.
- **Graded on:** held-out records constructed at verify time, inlined directly in
  `tests/test_outputs.py` — never shipped, never on disk under `/app`.
- **Constraint:** Python standard library only, enforced by construction
  (`python3 -I -S`, not a static import scanner).

---

## 2. The crux

> **The international ISO 7064 MOD-97-10 check digit that everyone knows about is not
> sufficient.** Every SEPA jurisdiction's own national banking system defines the exact
> character-class structure of its domestic account number, and five jurisdictions
> (Belgium, Spain, France, Italy, Norway) additionally embed a *second*, jurisdiction-
> specific check digit inside the account number, verified independently of the
> international one.

The shipped sample uses only GB/IE/AT/LU — jurisdictions whose account numbers need
nothing beyond the international check, so "length + structure + universal MOD-97-10"
reproduces the sample perfectly and looks like the complete rule.

| Mechanism | What the naive validator misses |
|---|---|
| Full 37-jurisdiction structure table | A validator hardcoded to a handful of countries wrongly rejects a real IBAN (e.g. Germany) from any jurisdiction outside its table |
| Belgium domestic check | MOD-97 over the first 10 BBAN digits, 0→97 special case |
| Spain domestic check | Two MOD-11 control digits (bank+branch, account), weight table `[1,2,4,8,5,10,9,7,3,6]` |
| France domestic check | MOD-97 key over bank+branch+account using **France's own** letter-to-digit table — *not* the IBAN's own A=10..Z=35 table |
| Norway domestic check | Weighted MOD-11 (`[5,4,3,2,7,6,5,4,3,2]`); a computed check value of 10 means "no valid check digit exists" (reject), not "treat as 0" |
| Italy domestic check | A CIN control letter over ABI+CAB+account using odd/even substitution tables, mod 26 → letter — not any Luhn-style doubling scheme |
| ASCII-only input | Python's `str.isdigit()`/`isalnum()` are Unicode-aware; Arabic-Indic digits satisfy them *and* the mod-97 arithmetic |

### The invariants that make it work

1. **The shipped sample never collides with any of these mechanisms.** All 12 sample
   records are GB/IE/AT/LU, none of which have a domestic check digit, so the naive
   "length + structure + MOD-97" implementation reproduces the sample exactly and has
   every reason to stop there.
2. **`instruction.md` names the mechanism and the five certified jurisdictions
   outright, never the algorithms.** It says structural conformance applies to every
   jurisdiction, and that Belgium/Spain/France/Italy/Norway specifically require a
   domestic check digit "as published by that jurisdiction's own national banking
   authority" — but never states a single formula, weight table, or substitution
   table.
3. **Held-out records exist only in `tests/test_outputs.py`**, never written to disk
   under `/app`, with the reference implementation inlined in the same file (no
   separate importable oracle module).

---

## 3. Gate-by-gate failure log

Static checks, rubric review, duplicate/similarity check, and validation passed clean
on *every* push from the first. Every real block came from `qc_gate` or `ava_review`
— the verifier-soundness gates, never the spec or difficulty itself. In order:

### 3.1 — Static check (`02573a8`): mechanical, one-line

`solution/validate_reference.py` was copied by `solve.sh` to `/app/validate.py`, but
the intermediate filename never appeared in `instruction.md`, tripping "expected
output files are documented in instruction.md." **Fix: renamed the solution file to
`validate.py` directly** so the created-artifact name matches what's documented — no
behavior change.

### 3.2 — `qc_gate` cycle 1 (`628e920`): two findings

- **Underdetermined / Hidden-Knowledge Mapping.** The domestic-check-digit premise
  wasn't disclosed strongly enough. Fixed by stating explicitly that the international
  check alone does not establish domestic conformance.
- **Narrow / Hardcodable Held-Out Coverage.** QC's exact mutant: collapsed
  Luxembourg's `[(3,'n'),(13,'c')]` structure to `[(16,'c')]`, dropping the "first 3
  chars must be digits" rule — no fixture caught it. Added a held-out LU record with a
  letter in that 3-digit prefix, reproduced QC's literal mutant in the local mutation
  sweep to confirm the fix.
- Also fixed, same push: header-order check was comparing as an unordered *set*
  instead of an ordered list, silently accepting a shuffled `valid,record_id` header.

### 3.3 — `ava_review` (`727bbdd`): a real oracle correctness bug

AVA constructed `DE89370400440532013000` — a real, well-formed German IBAN — and
found the oracle itself returned `false`, because the country table only had 8
entries. **This wasn't a fairness/disclosure nuance, it was the golden reference being
objectively wrong** relative to the instruction's own claim of general applicability.

Fix: built the full 37-jurisdiction SEPA table from the published IBAN registry,
verifying every row's length arithmetically (`4 + sum(structure segments) ==
declared length`) *and* cross-checking newly-added countries against real published
example IBANs (Germany's and the Netherlands' own canonical examples) before touching
any task file. Added held-out generalization fixtures pinning the requirement so it
can't silently regress.

### 3.4 — `qc_gate` cycle 2 (`3ffa5f3`): two findings

- **Oracle Edge-Case or Logic Bug.** QC constructed
  `AT6119043002345732٠١` (Arabic-Indic digits for 0 and 1) and found the
  oracle accepted it — Python's `isdigit()`/`isalnum()` are Unicode-aware, and
  `int('٠', 36)` evaluates to 0, so the value even survives the mod-97
  arithmetic. **Fixed at the root**, not per call-site: a single ASCII-whitelist gate
  (`frozenset(string.ascii_uppercase + string.digits)`) at the very top of
  `validate()`, rather than patching every individual `isdigit`/`isalpha` call.
- **Narrow / Hardcodable Held-Out Coverage.** Norway's `if chk == 10: return False`
  branch (the standard's "no valid check digit exists" case) had no fixture. QC gave
  the exact counter-example, `NO4200000000060`; added it directly as a held-out
  record.

### 3.5 — `ava_review` (`0669d42`): Italy's domestic check claimed but not implemented

The instruction's "for jurisdictions whose domestic standard embeds one" clause was
still open-ended at this point, and Italy has a real domestic CIN check that wasn't
implemented — AVA constructed a broken-CIN Italian IBAN and confirmed the oracle
wrongly accepted it. Researched and implemented Italy's actual algorithm (odd/even
substitution tables over ABI+CAB+account, mod 26 → letter), verified against the
canonical published example IBAN (`IT60X0542811101000000123456`) before writing it
into any task file. Bundled cheap advisory fixes in the same push: Gibraltar missing
from the country table, no lowercase/whitespace-padding test, no digit-in-letter-
position structural fixture on any of the newly-widened countries.

### 3.6 — `ava_review` (`6df5199`): the same finding, a different country — recognized as a pattern

Immediately next cycle, AVA found **Portugal's** domestic check claimed-but-missing
(with Finland/Estonia/Poland flagged as also open). This is the third occurrence of
the identical class of finding in two cycles (Germany missing entirely → Italy's CIN
missing → Portugal's check missing). **Recognized this as an unbounded arms race**
rather than another one-country patch: real domestic check-digit conventions exist
for many more SEPA jurisdictions than could safely be researched and verified inside
this iteration budget, and chasing them one at a time invites the gate to find the
next one indefinitely.

**Strategic fix instead of another fixture patch:** narrowed `instruction.md`'s
domestic-check clause from an open claim ("for jurisdictions whose domestic standard
embeds one") to a **named, closed list** — Belgium, Spain, France, Italy, Norway,
framed as "the jurisdictions this pipeline's compliance profile has fully certified"
(a realistic framing — real payment processors do maintain closed, incrementally-
expanded certified-jurisdiction lists; no commercial IBAN library implements every
country's domestic check either). This directly resolves the soundness gap because
the instruction's claim now exactly matches what's implemented, with no room for
"you said X but don't check X" on any other jurisdiction. The structural (length +
character-class) layer stayed fully general across all 37 jurisdictions, which is
where the "must generalize beyond the sample" difficulty genuinely lives without
needing per-country algorithm coverage.

**This did not collapse difficulty** — confirmed by the next `pass2` cycle passing
clean, and ultimately by pass@5 landing at 0/5 with `difficulty_crux` PASS on all 5
trials. The reasoning that justified the risk beforehand: pass@2's one failing trial
had *already* named the original four countries' algorithms in its own reasoning
before choosing not to implement them — the stumping factor was never "doesn't know
which countries," it was "quits once the sample passes." Naming the scope explicitly
removes an ambiguity, not the behavioral trap.

### 3.7 — `qc_gate` cycle 3 (`e3637bd`): six findings, three were one root cause

- **Oracle Undocumented Assumption / Missing Definition / Undocumented Requirement
  Enforced** (three separate QC categories, same underlying gap): the oracle silently
  applied `raw.strip().upper()` normalization, and a held-out fixture tested it
  (`HELDOUT_NORMALIZATION`, added an AVA-advisory cycle earlier), but `instruction.md`
  never actually said input might carry whitespace or mixed case. **One instruction
  sentence fixed all three QC categories at once**: documented that `iban` values may
  carry surrounding whitespace/mixed case picked up from upstream systems, must be
  normalized before checking, and that jurisdiction is read from the normalized value.
- **Narrow / Hardcodable Held-Out Coverage.** France's letter-substitution table has
  26 entries; QC mutated only the `'Z': 9` entry and found no FR fixture used a letter
  past `'Y'`. Constructed a valid + broken-domestic pair specifically exercising `'Z'`
  and confirmed it against a hand-verified computation before adding it.
- **Ambiguous Rule, No Disambiguation.** Resolved in the same push as the
  normalization fix by also naming the domestic check digits as "published by that
  jurisdiction's own national banking authority" — the fifth confirmed instance of the
  playbook's "name the authority, not the rule" pattern (after `fir-boundary-metrics`,
  `dynamo-093d3d6`, `dynamo-a4b5561`, `rebuild-release-tarballs`, `dynamo-37ba44d`).

Every gate passed clean on the very next cycle: `ava_review`, `deep_review`, `tier1`,
`qc_eval`, `qc_exec`, `qc_gate` all green, `trials` (pass@5) returned 0/5 with
`approach_validity` PASS on all five trials, and the PR was labeled `accepted`.

---

## 4. What actually stumped the agents (pass@5, graders' own words)

Failures stratified into five root causes across the 5 trials, no single cause
accounting for all of them:

1. **Italian CIN — wrong algorithm, all 5/5 trials.** Every trial independently
   converged on a Luhn-style digit-doubling heuristic (`v*2; if v>9: v-=9`, sum mod 26
   → letter) instead of the real ABI-published odd/even substitution tables — a
   plausible-looking but entirely wrong formula. *"The consistent cross-trial
   convergence on the same wrong algorithm strongly suggests agents were drawing on a
   training-data heuristic rather than correctly researching the published
   standard."*
2. **Non-ASCII digit acceptance, 4/5 trials.** Every one of those trials used
   `str.isdigit()`/`isalpha()`/`isalnum()` or `\d`, all Unicode-aware, and accepted
   `AT6119043002345732٠١` (Arabic-Indic digits) as valid. One trial did apply an
   ASCII-only guard and passed this specific test.
3. **France domestic check — wrong formula or wrong BBAN structure, 2 trials.**
4. **Country-registry gaps** (Gibraltar, or wrong NL/FR structure) reflecting
   incomplete domain knowledge of the 37-jurisdiction SEPA membership list.
5. Two trials hit the 1800s timeout while actively debugging France/Italy — assessed
   by the grader as a contributing but not decisive factor, since the Italian CIN was
   already wrong before the debugging phase started (more time would not have
   guaranteed a correct algorithm, only a longer search for one).

`near_miss` FAILed on 4/5 trials, each passing 11–12 of 14 tests — explicitly assessed
by the grader as confirming genuine difficulty rather than an artificially high bar:
*"the near-miss pattern... does NOT suggest the task is easier than it looks — the
near-miss criterion signals that the solution was close, consistent with the stated
difficulty."*

`difficulty_crux` and `approach_validity` PASS on all 5 trials — the failures align
precisely with the author-stated crux, and no trial's approach was invalidated by an
undisclosed rule or verifier defect.

---

## 5. The pattern worth carrying forward: narrow the promise before it becomes an arms race

This is the sharpest new instance of a pattern the playbook has touched before
(`mirror-retention-plan` Issue 6: "a deleted decoy field is cheaper than an
implemented one"; `cross-link-closure` §3.2: same idea for an unread schema field) —
but this task hit it three times in a row on the *same* mechanism before the fix
landed, which makes the shape unusually clear:

- Cycle 1: AVA found Germany entirely missing from an 8-country whitelist → fixed by
  going *wide* (37-country structural table).
- Cycle 2: AVA found Italy's domestic check claimed-but-unimplemented → fixed by going
  *deep* on Italy specifically (implemented and verified its real algorithm).
- Cycle 3: AVA found Portugal's domestic check claimed-but-unimplemented, with
  Finland/Estonia/Poland flagged as also open → **recognized the pattern and fixed the
  promise instead of the implementation**: named a closed, five-jurisdiction list.

**The lesson: when a design's claim is "true for an open-ended class of things" but
the implementation only covers a growing subset, going deeper (implementing the next
instance) only delays the next finding — going wide once by naming the actual closed
scope resolves the whole class at once.** The tell that it's time to do this rather
than patch again: the *same* QC/AVA finding category recurring on a *different*
concrete instance two cycles running, especially when the gate's own evidence
mentions several more open instances by name (here: "Finland/Estonia/Poland" listed
as still-open in the same comment that blocked on Portugal).

This also did not require inventing an unrealistic constraint — real payment
processors and IBAN validation libraries genuinely do maintain closed,
incrementally-expanded certified-jurisdiction lists rather than implementing every
country's idiosyncratic domestic convention, so the closed-list framing reads as
authentic business logic, not a design workaround.

---

## 6. Process rules confirmed (nothing new, but worth re-confirming)

- **Never push while a run is in flight** — checked `gh pr checks 2` before every
  push, zero wasted cycles from this on this task.
- **Batch fixes into one push, always.** Every cycle above bundled the code fix, the
  fixture addition, `task.toml`/README sync, and (when relevant) the instruction
  rewording into a single commit.
- **Recalibrate and mutation-sweep locally before every push**, including QC's exact
  cited mutant reproduced as a named mutation in the sweep — every cycle ended with
  0 survivors before pushing, 17 mutations by the final push.
- **`tests/test_outputs.py` and `solution/validate.py` must be edited identically,
  every time** — both hold independent copies of the same country table and domestic-
  check algorithms; a mismatch would silently make the oracle and the held-out
  expectations disagree.
- **Numerically verify every new algorithm against a real, published example before
  writing it into any task file** — every domestic-check formula (Belgium, Spain,
  France, Norway, Italy) and every newly-added country's structure was checked against
  a real canonical example IBAN in a scratch script first. This caught a wrong
  French letter-substitution table on the first attempt (the correct table is *not*
  the IBAN's own A=10..Z=35 mapping) before it ever reached a gate.
- **A permissions bug specific to this environment, worth remembering:** pytest's own
  `tmp_path` fixture lives under a `0700`, root-owned directory tree
  (`/tmp/pytest-of-root/pytest-0/...`); chmod-ing only the leaf test directory isn't
  enough because an unprivileged subprocess can't traverse the `0700` *parents*
  either. Fixed by building a fresh directory directly under `/tmp` (mode `1777`) via
  `tempfile.mkdtemp(dir="/tmp")` instead of using pytest's `tmp_path` for any
  privilege-dropped subprocess invocation.

---

## 7. Final state

- **PR HEAD: `e3637bd`** — the commit pass@5 was measured on, the commit that got the
  `accepted` label.
- Commits: `fe798f5` initial · `02573a8` filename fix · `628e920` QC cycle 1 ·
  `727bbdd` AVA generalization fix · `3ffa5f3` QC cycle 2 (ASCII gate + Norway) ·
  `0669d42` AVA Italy CIN + advisories · `6df5199` scope-narrowing to closed
  jurisdiction list · `e3637bd` QC cycle 3 (normalization + FR 'Z' + authority naming,
  accepted).
- Fixture-generation and mutation-sweep tooling (`sepa_specs.py`, `build_fixtures.py`,
  `iban_lib.py`, `mutation_sweep.py`) lived only in the session scratchpad, never
  committed.
- Final country/mechanism coverage: 37 SEPA jurisdictions structurally validated; 5
  (Belgium, Spain, France, Italy, Norway) with a verified domestic check digit; 17
  local mutations, 0 survivors.

### One-paragraph version for future me

Build the crux as "the universally-known check isn't sufficient" with the sample
homogeneous exactly where the real complexity lives (here: four jurisdictions with no
domestic check, out of a much larger real set), and verify every domain-specific
algorithm against a real published example *before* writing it into any task file —
this catches transcription errors (a wrong letter-substitution table, a country's
exact BBAN structure) for free, before a gate ever has to find them. Expect
`qc_gate`/`ava_review` to mutate your reference and construct real counter-examples
rather than just probing adversarial submissions — reproduce their exact cited mutant
as a named mutation in your local sweep every time, not just a similar one. When a
design's claim is open-ended ("for any X that has property Y") but the implementation
only covers a growing subset, expect the gates to keep finding the next uncovered
instance — the second time the *same* finding category recurs on a *different*
concrete instance, stop implementing instances and narrow the claim to a named closed
set instead; this resolves the whole class of finding at once and, if the failing
trial already derives the relevant instances through its own reasoning (check your
pass@2 evidence for this), costs nothing in difficulty. Document every implicit
normalization (whitespace, case) in the instruction the moment you add a test for it,
not after a gate finds the gap — an oracle behavior with a fixture but no
instruction-level disclosure is an automatic QC/AVA finding waiting to happen. Name
the normative authority behind any domain convention ("as published by X's own
national banking authority") rather than just asserting the convention exists — the
"name the authority, not the rule" pattern has now resolved this exact class of
finding on six separate tasks.
