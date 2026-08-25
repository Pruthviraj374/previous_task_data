# dynamo/sdf-registration-qc — three derivable cruxes died, one arbitrary convention won

| | |
|---|---|
| **Outcome** | **ACCEPTED** — every gate green, `accepted` label |
| **Repo** | `dynamo-20141f7-scientific-computing-and-domain-science`, branch `submission`, fork `charan-sr` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-20141f7-scientific-computing-and-domain-science/pull/1 |
| **Category / sub** | Scientific Computing and Domain Science / Chemistry and materials workflows (pre-seeded; first-ever task in this exact subcategory) |
| **Final commit** | `520de06` (design 4, `sdf-registration-qc`) |
| **Headline** | **pass@2 = 0/2 (both valid fails), pass@5 = 1/5, avg@5 = 0.200, 4 good valid fails.** Reached on the **fourth** full design, after the first three each cleared rubric review and were then solved 2/2 by `pass@2` — **four consecutive too-easy verdicts**. `qc_gate` passed **first try** on design 4, versus three QC rounds and four bug fixes on design 1. |

This is the most instructive task in the corpus so far, because it accidentally ran a
controlled experiment. Four designs, same category, same subcategory, same author, same
benchmarked model, same verification discipline — three failed and one succeeded, and the
variable that changed was not obscurity, not self-testing resistance, and not the number of
cruxes. It was **whether the deciding fact is derivable.**

---

## 1. The four designs

| # | Design | Crux | Result |
|---|---|---|---|
| 1 | `periodic-coordination-numbers` | triclinic minimum-image geometry; later compounded with unwrapped-input reduction | 2/2 solved → **1/2 valid fail ×2** → 2/2 solved |
| 2 | `site-multiplicity` | symmetry-orbit deduplication (atoms on special positions) | 2/2 solved, twice |
| 3 | `equiv-isotropic-adp` | metric-tensor unfolding of an anisotropic displacement tensor | 2/2 solved |
| 4 | `sdf-registration-qc` | **arbitrary MDL/CTfile V2000 encoding conventions** | **0/2, then pass@5 1/5 — ACCEPTED** |

### Design 1 — periodic coordination numbers
Naive per-axis fractional rounding finds the wrong nearest periodic image once a cell is
genuinely skewed. Real, documented in GROMACS/LAMMPS/MDAnalysis. Solved 2/2: both agents
independently derived the standard inverse-lattice column-norm bound, which the reviewer
called *"well-represented in training data."* Compounding it with an unwrapped-input
robustness axis produced two genuine 1/2 valid failures and survived three QC rounds — then
a third sample came back 2/2, with one agent **catching its own bug by writing a randomized
brute-force self-test.** Reversible geometry is self-testable; that was the diagnosis.

### Design 2 — site multiplicity
Purpose-built to defeat self-testing: the deciding case (an atom exactly on a symmetry
element) is a measure-zero event a random self-test will never hit. The anti-self-testing
property held — and it didn't matter. Both agents wrote correct deduplication *from the
start*, no debugging needed. Reviewer: *"established training-data knowledge of
crystallographic multiplicity algorithms."* Nothing needed discovering, so the defense never
engaged. A second attempt after tightening disclosure also came back 2/2, with both agents
deriving periodicity-awareness unprompted.

### Design 3 — equivalent isotropic ADP
Purpose-built against the *other* mechanism: a **lossy, one-way** computation (six tensor
components collapse to one scalar), so no round-trip or differential self-check exists.
Solved 2/2 anyway — and this trial gave the decisive evidence. Both agents **derived the
metric-tensor formula from first principles** off the disclosed Debye-Waller convention.
Reviewer, verbatim: *"analytical crystallographic reasoning, not merely training-data
recall."* One trial verified its own derivation against a self-constructed triclinic case to
`1.4e-17` — the same methodology used to author the task.

At this point ten further candidates were evaluated on paper and rejected, and the task was
written up as a dead end. The user then asked for one more attempt.

### Design 4 — SDF registration QC (accepted)
Summarise MDL V2000 SDF records for compound registration: net formal charge, radical
centres, isotope-resolved formula. Four decisive conventions, all real CTfile V2000, **none
derivable**:

| Convention | Naive reading | Correct reading |
|---|---|---|
| Atom-block charge field | the stored integer *is* the charge | a **code**: `1`→+3, `2`→+2, `3`→+1, `4`→radical, `5`→−1, `6`→−2, `7`→−3 |
| `M  CHG` property line | layered on top of atom-block charges | **supersedes** the atom block entirely; unlisted atoms forced neutral |
| Charge code `4` | a charge, or ignored | a **doublet radical** — a radical centre, no charge |
| Atom-block mass-difference | an absolute mass number | an **offset** from the principal isotope (`M  ISO` is absolute) |

**You cannot reason your way to "`1` means +3."** It is a committee decision that could
equally have gone the other way, and in other formats it did.

---

## 2. The proof that it is underivable

This is the single most valuable artifact this task produced. In `pass@2`, one agent wrote a
complete, competent implementation containing an **invented, shifted charge-code table**:
codes `4` *and* `5` both treated as radical, codes `6`–`8` mapped to −1/−2/−3 instead of the
correct `5`–`7`. It also omitted `M CHG` supersession entirely.

That is what "underivable" looks like in practice. The agent could not derive the table, so
it *guessed a plausible-looking one* — and a plausible guess is wrong, because the real table
is arbitrary. Contrast design 3, where two independent agents derived the same correct
formula because only one formula is mathematically possible.

`pass@5` sharpened it further: **all four failing trials shared one primary root cause — the
`M CHG` supersession rule.** Agents that recalled the charge-code table still lost on the
precedence rule between the atom block and the properties block, which is a second,
independent arbitrary decision.

---

## 3. The rule this establishes

> **Obscurity to humans is not the filter. Derivability is.**
>
> Before building, ask: *given the exact input schema I am about to disclose, could a
> competent domain expert derive the unique correct output purely by reasoning, with no
> external fact to recall?* If **yes**, expect a clean 2/2 solve — no matter how obscure the
> topic feels, and regardless of whether the computation is reversible, discrete, or lossy.
> If **no** — the value could only be otherwise, and one specific real system happened to
> choose it this way — the crux may survive.

Corollaries confirmed here:

- **Self-testing-resistance is necessary for some mechanisms but never sufficient.** It only
  matters for a crux the agent would otherwise get *wrong and need to catch*. If the agent
  derives correctly on the first attempt, the defense never engages. Designs 2 and 3 were
  both engineered around this and both failed.
- **Disclosing data removes the recall burden, not the derivability risk.** Design 2
  disclosed the full symmetry-operation list; the *concept* applied to that data was still
  mainstream, so it was solved anyway.
- **Volume of cruxes does not help.** Consistent with `dynamo-0cfa37b`: adding mechanisms
  satisfies the rubric's breadth concern while leaving `pass@2` untouched, because this model
  transcribes any number of fully-specified rules.
- **Chemistry/materials is a hostile subcategory for this** — precisely-disclosable physical
  facts are, almost by construction, precisely computable. The winning crux was not chemistry
  at all; it was a *file-format committee decision that chemistry software happens to
  implement*.

---

## 4. Verification discipline that paid off

Everything below was done **before** the first push of design 4, and each step caught a real
problem:

- **Verify the external fact against the spec, don't recall it.** Both decisive facts (the
  code table, the supersession rule) were confirmed against the published CTfile
  specification via search before any code was written.
- **Verify the *discriminating property*, not just correctness.** Built all four naive
  mutants and checked each against every fixture. This caught two authoring bugs: the
  supersede fixture originally used charges of `+1` and `−1` that **cancelled at net +1**,
  hiding the divergence completely, and a sort key crashed on `None` isotopes.
- **Verify sample inertness explicitly.** All four mutants must reproduce the shipped sample
  exactly; all four must fail their own held-out fixture. Confirmed through the real Harbor
  verifier, not just standalone scripts: oracle 1.0, nop 0.0, four mutants 0.0 each.

That discipline is very likely why `qc_gate` passed **first try** here, against three rounds
and four legitimate bug findings on design 1.

---

## 5. Reusable checklist

- Run the derivability test above on every candidate crux **before** building.
- Prefer a real system's *arbitrary encoding/precedence decision* over any *formula*,
  *algorithm*, or *physical relationship*, however specialised the latter feels.
- Name the standard as a locator; restate none of its rules. Design 4's `instruction.md`
  says the input is MDL V2000 and never mentions a charge code.
- Construct the shipped sample so every governed field is **inert** — here, all samples use
  modern property-line encoding, so every atom-block field the conventions govern is zero.
- Give each axis its own held-out fixture, and pick values so correct and naive readings
  **cannot coincidentally coincide** (the cancelling-charges bug).
- Build every naive mutant and run it through the *real* verifier before pushing.
- Two arbitrary axes beat one: agents that recalled the charge table still lost on
  supersession.

---

## 6. Distilled summary

Four designs against Opus-4.8/Terminus-2 in Chemistry and materials workflows. The first
three — triclinic minimum-image geometry, symmetry-orbit deduplication, and metric-tensor
ADP conversion — each cleared rubric review and were then solved 2/2 by `pass@2`, four times
running, because each crux was the *unique answer forced by a disclosed definition*, and this
model derives those reliably; the anti-self-testing mechanisms built into designs 2 and 3
defended against a wrong answer that was never produced. The fourth design kept the same
domain but changed the kind of fact: four **arbitrary MDL/CTfile V2000 encoding conventions**
(a charge *code* table, property-block supersession, a radical code, and an isotope offset)
that cannot be derived from chemistry at all — only read from the specification. It returned
`pass@2` 0/2 and `pass@5` 1/5 (avg@5 0.200, four good valid fails, all four sharing the
`M CHG` supersession trap) and was accepted, with `qc_gate` clean on the first attempt. The
transferable lesson is that **derivability, not obscurity, is what decides whether a crux
survives**: if a competent expert could derive the deciding value from the disclosed inputs
with no external fact to recall, it will not stump this model — and the cleanest proof is
that an agent, unable to derive the table, invented a shifted one instead.
