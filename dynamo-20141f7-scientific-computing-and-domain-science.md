# dynamo/equiv-isotropic-adp — four designs, four confirmations of one wall

| | |
|---|---|
| **Outcome** | **GENUINE DEAD END, not accepted** — best-quality design left open on the PR; task reassignment/further budget is the user's call, not made here |
| **Repo** | `dynamo-20141f7-scientific-computing-and-domain-science`, branch `submission`, fork `charan-sr` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-20141f7-scientific-computing-and-domain-science/pull/1 (left open, at commit `3e8d2d8`) |
| **Category / sub** | Scientific Computing and Domain Science / Chemistry and materials workflows (pre-seeded; first-ever task in this exact subcategory) |
| **Benchmarked model** | `task.toml` names Opus-4.8 / Terminus-2 |
| **Final commit** | `3e8d2d8` (design 3, `equiv-isotropic-adp`); ~10 more candidates evaluated on paper afterward, none built |
| **Headline** | **Four consecutive `pass@2` 2/2-solved verdicts across three structurally different design mechanisms**, converging on one finding: this model derives mathematically/physically *necessary* correct answers from precisely disclosed definitions extremely reliably, regardless of what obstacle stands between an agent and self-testing a wrong answer. The winning-elsewhere formula (real external standard + genuinely arbitrary, non-derivable implementation convention) could not be replicated in this subcategory within the effort invested. |

This is the first genuine, fully-documented non-acceptance in this playbook. It is included
anyway, in full, because the negative result is the valuable part: four different, carefully
reasoned hypotheses about *why* a design would resist this model each failed the same way, and
the reasoning behind each failure is a real constraint on what "Scientific Computing and
Domain Science" tasks can look like against this model/agent pairing.

---

## 1. Design 1 — periodic coordination numbers (triclinic PBC)

**Crux:** compute each atom's coordination number under general (possibly triclinic) periodic
boundary conditions. The naive shortcut — round each fractional displacement component
independently to the nearest integer to find the "nearest" periodic image — is exact only for
orthogonal cells; genuinely skewed cells need full multi-image enumeration. Real, documented
(GROMACS/LAMMPS/MDAnalysis all warn about this), not invented.

**Result: `pass@2` 2/2 solved, first push.** Reviewer's analysis: both agents independently
derived the standard inverse-lattice column-norm image-search bound, calling it "well-represented
in training data... rather than independently derived from first principles."

**Redesign within design 1 — compounded with unwrapped-input robustness.** Added a second,
independent pitfall: `instruction.md` already disclosed positions might not be pre-wrapped into
the cell (realistic — unwrapped trajectory dumps for diffusion tracking are real MD output); a
full triclinic-correct search still fails if centered on the raw, un-reduced displacement.
**This got a genuine pass@2 1/2 valid failure — twice in a row**, across three rounds of
legitimate QC (mutation-testing) hardening (a real floating-point round-trip bug the fix itself
introduced; an untested cutoff-boundary convention; an over-broad import denylist; a missing
symlink guard; a real robustness bug where extremely skewed-but-valid cells blew the image-search
bound up to 42/11/3 repeats, fixed with lattice basis reduction; a missing coverage case for
self-image exclusion on small cells).

**Then, on a third `pass@2` sample: 2/2 solved again — the load-bearing result for this whole
task.** Both agents built fully *general, correct* algorithms (a Cauchy-bound via the inverse
metric tensor; a QR-decomposition sphere decoder). One agent started with the naive shortcut,
**caught its own mistake by writing a randomized skewed-lattice test and comparing against a
brute force it built itself**, then fixed it. This is a structurally different defeat mechanism
from simple recall: an agent doesn't need to already know the right approach if it adopts
differential-testing against its own brute force as a general habit — and periodic-image
geometry is fully self-testable that way (any reversible, first-principles-computable transform
is). Abandoned after this; user chose to redesign rather than keep re-rolling a design with a
33% empirical per-trial failure rate against `pass@5`'s 60% bar.

## 2. Design 2 — site multiplicity via symmetry-operation deduplication

**Crux, chosen specifically to resist design 1's defeat mechanism:** given an atom's fractional
coordinates and a *fully disclosed* list of real symmetry operations (rotation + translation,
taken from real published space groups — P-1, P2₁/c, C2/c, P2₁2₁2₁, verified against the
International Tables for Crystallography before use), compute the atom's site multiplicity (the
number of distinct positions the operations generate). All data disclosed — no external-lookup
burden. An atom on a symmetry element (inversion center, rotation axis) generates *fewer*
distinct positions than the operation count, but "apply every operation, don't deduplicate" is
natural and *correct* for any generic-position atom — a measure-zero event for an agent's own
self-chosen test coordinates. **No round-trip or brute-force differential test validates
deduplication correctness the way it does for reversible geometry** — this was the intended
escape from design 1's wall.

**Result: `pass@2` 2/2 solved, first push.** Both agents wrote correct deduplication *from the
start*, no debugging or self-testing needed at all. Reviewer's diagnosis: "established
training-data knowledge of crystallographic multiplicity algorithms" — the *concept* itself
(Wyckoff-multiplicity reduction) is elementary, foundational crystallography this model applies
by default, so the measure-zero-event defense never mattered; nothing needed discovering.

**Fix attempted:** the platform's own pass@2 suggestion pinpointed real over-disclosure —
`instruction.md`'s coincidence rule spelled out the exact comparison procedure verbatim. Reworded
to state the goal (count distinct positions, understood periodically) rather than the mechanism;
this also surfaced and fixed a genuine latent bug (naive per-component coincidence comparison
isn't periodicity-aware — fractional coordinates are points on a 3-torus).

**Result: `pass@2` 2/2 solved again.** Both agents *also* derived periodicity-awareness
unprompted this round, one trajectory reasoning almost verbatim: "a component difference of
(near) exactly 1 does not distinguish two positions." Second confirmation that disclosing data
doesn't remove the "well-known concept" risk if the *concept* applied to that data is itself
mainstream.

## 3. Design 3 — equivalent isotropic ADP from a lossy, one-way formula

**Crux, chosen to resist design 2's defeat mechanism:** given an atom's anisotropic
displacement tensor (Uij, standard crystallographic Debye-Waller/reciprocal-basis convention —
disclosed via the exact exponent formula, the literal definition of the input data) and unit
cell parameters, compute the equivalent isotropic displacement value (one third of the trace of
the tensor in an orthonormal Cartesian frame). Six tensor components collapse into one scalar —
genuinely **lossy and one-way**, so there is no round-trip check an agent's self-testing habit
could construct, unlike design 1's reversible geometry. Deliberately avoided naming "Ueq" or
stating the metric-tensor formula in `instruction.md`, to avoid a directly searchable label.
Formula rigorously verified before authoring — not just cross-checked between two
implementations, but validated against a constructed known-isotropic test case on a genuinely
triclinic cell (this process caught a real bug in the second implementation, which had wrongly
assumed a change-of-basis matrix was orthogonal).

**Result: `pass@2` 2/2 solved — the fourth consecutive "too easy" verdict, and decisive.** The
reviewer's trajectory analysis leaves no ambiguity: both agents **independently derived the
correct metric-tensor formula from first principles**, purely from the disclosed Debye-Waller
exponent convention. Quoted directly: "the convergence on an identical, non-obvious approach...
strongly suggests the disclosed Debye-Waller formula in instruction.md contains enough
information for a capable agent to derive the correct method from first principles — this is
not merely training-data recall of a specific API, but analytical crystallographic reasoning."
One trial explicitly verified its own derived formula against a self-constructed triclinic test
case (agreement to `1.4e-17`) — the same "verify against a constructed test case" methodology
used to author the task, just applied by the agent instead. Even the read-only static rubric
reviewer independently recognized the target quantity as "the standard Fischer-Tillmanns Ueq
formula" purely from the precise-but-unnamed description.

## 4. The generalized finding

Three designs, three different theorized defeat-resistance properties — self-testable reversible
geometry; self-testing-resistant discrete concept via a measure-zero deciding case; self-testing-
resistant lossy one-way formula — four consecutive clean 2/2 results. The common thread isn't
"which specific fact was too well-known" anymore. **Every crux tried has been a correct answer
that is mathematically/physically necessary given a fairly-disclosed definition**, and this
model is evidently strong enough at first-principles derivation in scientific-computing-adjacent
domains to bridge from "precisely disclosed definition" to "correct implementation" directly,
regardless of what obstacle is placed in the way of *self-testing* a wrong answer.
Self-testing-resistance was the wrong axis to optimize across all three redesigns; the model
doesn't need to self-test because it derives correctly the first time.

This sharpens the existing `dynamo_enumeration_defeats_evidence_inference` rule (memory) rather
than contradicting it. The confirmed wins elsewhere in this playbook were never *mathematically
derivable* facts:

- `dynamo-602128a` (gemmlowp/TFLite requantization): the correct rounding/shift-sign direction
  for fixed-point requantization is an **engineering decision baked into one specific codebase**,
  not derivable from quantization theory — multiple mathematically valid rounding conventions
  exist, and only reading (or having memorized) that source tells you which one gemmlowp uses.
- `dynamo-3779991` (RDFC-1.0 canonicalization): "deduplicate triples before hashing" is one
  specific step, easy to miss, buried inside a large, genuinely complex, multi-step real
  standard — the overall shape is derivable/recognizable, but this one fine-grained branch
  requires having read the actual formal specification, not just understanding the general
  concept of "canonicalize a graph."

A metric-tensor transform, a group-orbit deduplication rule, a minimum-image geometry formula —
all of these are the *unique correct answer* forced by a clean mathematical/physical definition,
which is exactly the shape of problem this model is strongest at, independent of how obscure
that fact is to a human practitioner who's never had to derive it by hand.

## 5. Ten further candidates evaluated on paper, none built

After the third failure, six candidates were evaluated against the sharpened bar (real, but
*arbitrary* — not derivable) before concluding none was both tractable and clearly different:
CIF disorder-group/split-site occupancy handling (collapses back into design 2's already-defeated
multiplicity mechanism); bond valence sum with disclosed empirical R0/B parameters (the hard part
— periodic neighbor-finding — is design 1's already-defeated mechanism, empirical constants are
just data to plug in); pymatgen/spglib symmetry-tolerance discrepancy (real, but building a task
around it requires open-ended full symmetry-detection, risking a `solvable` FAIL); space-group
origin-choice/cell-setting ambiguity (only matters when converting between settings — no
ambiguity survives if all data is given in one consistent convention throughout); PDB hybrid-36
numeric-overflow encoding (real and arbitrary, but reads as a data-encoding puzzle rather than
domain-expert reasoning, risking an `essential_difficulty` FAIL for "clerical detail"); and
mixed-valence oxidation-state disambiguation via trying each candidate R0 (rejected as a repeat
instance of the *enumeration*-defeats-evidence pattern from a different task's BPE tie-break
work, not a new escape).

A seventh direction — Option C, compute/scale-forcing — was evaluated in more depth: reviving
design 1's verified triclinic-geometry code with the crux reframed entirely around performance
(large atom counts under a tight memory/time budget, forcing a skew-aware cell list, since naive
3×3×3-neighbor-bucket cell lists are documented to be wrong for sufficiently skewed cells — real,
per LAMMPS's own hard tilt-factor limit). Declined without building: a memory-only constraint has
an easy escape hatch (chunked/blocked brute force, a completely standard numpy pattern, defeats
the intended forcing function without real algorithmic insight); a genuinely time-binding
constraint needs tens of thousands of atoms to reliably exceed a real timeout even well
vectorized, straining "realistic structure" framing; and most fundamentally, nothing in this
task's history gave a reason to expect "implement a skew-aware cell list" — itself a well-posed,
comparably derivable engineering problem — would escape the same pattern the other four attempts
all fell to.

## 6. Reusable checklist for the next Scientific Computing / Domain Science attempt

- **Disclosed data removes the recall burden, not the derivability risk.** If the CONCEPT or
  FORMULA connecting the disclosed data to the answer is itself clean and mathematically/
  physically forced, this model derives it — whether or not self-testing could also have found
  it. Test every candidate crux against: "given the exact input schema I'm about to disclose,
  could a strong physicist/mathematician derive the unique correct output purely by reasoning
  from first principles, with no external fact to recall?" If yes, expect a clean 2/2 solve.
- **The only confirmed-working shape is: a real, published, external standard or system, where
  the DECIDING detail is an arbitrary implementation choice (not a mathematical necessity) that
  lives in that system's actual source/spec, not in general domain understanding.** Verify this
  by asking: "if I fully and correctly explained the general concept to a domain expert with no
  access to this specific system, could they derive the deciding value themselves?" If yes
  (as in Ueq, Wyckoff multiplicity, triclinic MIC), it's derivable and will not survive. If no —
  the value could only be otherwise, and only this one system happened to choose it this way —
  it may survive.
- **Self-testing-resistance (measure-zero deciding cases, lossy/one-way computations) is a
  necessary property for SOME defeat mechanisms but is not sufficient on its own** — it only
  matters for cruxes an agent would otherwise get wrong and need to catch via testing. If the
  agent derives the right answer on the first attempt (which this model does very reliably for
  clean scientific-computing problems), self-testing-resistance never gets exercised.
- **Chemistry/materials-workflows-adjacent facts are unusually likely to be "clean and
  derivable"** compared to file-format/database/ML-serving domains, because precisely-disclosable
  physical/geometric facts are, almost by construction, precisely computable too. Sibling
  categories with confirmed wins (Data Querying and Databases' engine-specific behaviors, the
  gemmlowp GPU-kernels precedent) may structurally favor the winning shape more than this
  subcategory does.
- **QC (mutation testing) is trustworthy and worth taking seriously even mid-crisis** — every
  finding across three QC rounds on design 1 was a real, legitimate bug or coverage gap, several
  caught genuine authoring mistakes (a floating-point round-trip bug, a robustness gap under
  extreme cell skew, an incorrect orthogonality assumption in an "independent" verification).
  Reproduce truncated/terse QC evidence by hand locally before trusting it at face value.
- **Formula-heavy designs need independent numerical verification before authoring fixtures**,
  not just cross-checking two code paths that implement the same idea differently — construct a
  case with an independently-known correct answer (e.g. a known-isotropic tensor) and confirm the
  candidate formula recovers it, the way this task's Ueq formula was validated.

## 7. Distilled summary

Four designs against Opus-4.8/Terminus-2 in Scientific Computing and Domain Science / Chemistry
and materials workflows, each targeting a different theorized weakness (well-known formula →
self-testing-resistant discrete concept → self-testing-resistant lossy formula), all converged
on the same underlying cause: this model reliably derives the unique, mathematically-necessary
correct answer from any precisely-disclosed definition, so no obstacle placed in the way of
*self-testing a wrong answer* matters if the agent never produces a wrong answer to begin with.
The confirmed-working formula elsewhere in this playbook — a real external standard's genuinely
arbitrary implementation choice, not derivable from first principles no matter the skill — could
not be replicated within this subcategory in the effort invested; every real, tractable candidate
considered either collapsed back into an already-defeated derivable mechanism or risked a
different, already-documented failure mode. Left as a genuine, fully-documented dead end rather
than force a fifth low-confidence build; the reusable lesson (test candidate cruxes against "could
a domain expert derive this from the general concept alone, with no access to the specific
system?") is the main asset this task produced for future attempts in this or adjacent
subcategories.
