HANDOFF: dynamo-20141f7-scientific-computing-and-domain-science (PR #1)
========================================================================
Last updated: after pass@2 returned 2/2 solved AGAIN on commit `5b017a4`
(2026-08-25) — the second design's second consecutive "too easy" result,
and the third "too easy" pass@2 verdict overall across two full designs on
this PR.

-----------------------------------------------------------------------
STATUS IN ONE SENTENCE: design 1 (periodic-geometry, compound triclinic +
unwrapped-input crux) hit a self-testing-resistance wall after 2 genuine
pass@2 valid failures + 3 QC rounds; the user chose to redesign (Option B
from the prior version of this handoff); design 2 (site-multiplicity from
disclosed real symmetry operations, purpose-built to resist self-testing
via a measure-zero-event crux) hit a DIFFERENT wall twice in a row — both
times the deciding crystallographic concept (Wyckoff-multiplicity dedup,
then periodic minimum-image coincidence) turned out to be elementary,
foundational training-data knowledge the model applies correctly without
needing to derive or discover it at all. This is again a decision point,
not a bug to fix — and it now looks less like "wrong specific fact" and
more like "any concept-application crux in mainstream crystallography is
within this model's reach," which should inform what's tried next.
-----------------------------------------------------------------------

## Repo / PR pointers

- Local clone: `C:\Users\chara\Downloads\Handshake\dynamo-20141f7-scientific-computing-and-domain-science`
- Branch: `submission`, currently at commit `5b017a4` (nothing uncommitted)
- PR: https://github.com/handshake-project-dynamo/dynamo-20141f7-scientific-computing-and-domain-science/pull/1
- Category/subcategory (fixed, do not edit): Scientific Computing and Domain Science / Chemistry and materials workflows
  (first task in this exact subcategory — no prior in-category precedent existed to check against)
- Model/agent under test: Opus-4.8 / Terminus-2
- Root `README.md` describes the current (design 2, site-multiplicity) design in full, including its own pass@2 iteration history.
- Task identity changed with the redesign: artifact is now `/app/compute_multiplicity.py`, `[task].name = "dynamo/site-multiplicity"` (was `dynamo/periodic-coordination-numbers`).

## The design, in order, and exactly what happened

**Design 1 (`eac184a`) — triclinic minimum-image alone.** Coordination-number
computation under general (possibly triclinic) periodic boundary conditions;
crux was the well-documented pitfall that naive per-axis fractional rounding
finds the wrong nearest periodic image once a cell is genuinely skewed.
Real, published (GROMACS/LAMMPS/MDAnalysis all document this), but proved
**too well-known**: pass@2 on this design came back 2/2 solved, with the
reviewer's analysis stating both agents independently derived the standard
inverse-lattice column-norm bound and calling it "well-represented in
training data... rather than independently derived from first principles."
This is the same disclosure-vs-difficulty pattern documented in
`dynamo_enumeration_defeats_evidence_inference` (memory), now confirmed in a
new domain (computational geometry/crystallography) beyond the previously
confirmed algorithmic/statistical/graph domains.

**Design 2 (`86a8659`, current) — compounded with unwrapped-input
robustness.** Kept the triclinic crux but added a second, independent,
non-textbook pitfall: `instruction.md` already disclosed positions may not
be pre-wrapped into the cell (realistic — unwrapped trajectory dumps for
diffusion tracking are real MD-pipeline output); a full triclinic-correct
multi-image search still silently fails if it searches around the raw,
un-reduced displacement instead of reducing it into the cell first — exactly
the gap both design-1 pass@2 agents' solutions had, just never exercised.
**Result: pass@2 1/2 valid failure** (genuine — the reviewer's own verdict:
"difficulty is genuine and well-calibrated... the failure is a legitimate
algorithm limitation, not a verifier or spec defect").

## Three QC (mutation-testing) rounds, all legitimate, all fixed

1. **`f95a1c6`** — three findings: (a) a real floating-point round-trip bug
   the reduction step introduced (an exactly-at-cutoff pair could round-trip
   to appear 1e-15 outside it and be wrongly excluded — fixed with a
   `cutoff + 1e-9` epsilon); (b) no fixture placed a pair exactly at cutoff,
   so a strict-`<` mutant passed everything (fixed: added `held_boundary_1`,
   disclosed the inclusive convention); (c) `run_agent.py`'s import denylist
   blocked stdlib `subprocess`/`multiprocessing` with no corresponding
   disclosed rule (fixed: removed both, kept only third-party-package and
   network-module blocks, both of which instruction.md's existing text
   covers). **Re-ran pass@2: 1/2 valid failure again** — the failing trial's
   errors traced to *both* the triclinic pitfall and the new
   `held_boundary_1` epsilon case.

2. **`4e373c6`** — `tier1` held on one leftover finding (E5, "Symlinked
   Output Path"): `/app/compute_coordination.py` is the one agent-produced
   artifact whose filesystem metadata (not just content) is fully
   attacker-controlled during the agent's run; without a guard, a symlink
   planted there could resolve to something sensitive once `tests/` is
   overlaid at verify time. Fixed: `run_agent.py` now refuses to execute
   unless the script resolves to a regular file directly under `/app`.
   **Cleared tier1 (4/4), qc_exec/qc_eval passed, but `qc_gate` then found
   two NEW issues** (see below) — QC apparently runs progressively deeper
   checks as earlier ones clear, not all-at-once.

3. **`e0822f1`** — two findings, both investigated by hand before fixing
   (QC's evidence text is truncated in the PR comment; do not trust it at
   face value — reproduce locally first):
   - **Oracle Edge-Case or Logic Bug**: QC's counterexample used an
     extremely skewed but entirely valid triclinic cell (perpendicular
     plane spacing as small as 0.07 Å against 2.5-13.4 Å-long lattice
     vectors). Hand-verified with a much wider independent search that the
     specific answer (`[1, 1]`) was actually *correct* — the real defect was
     robustness: the image-search bound blew up to 42/11/3 repeats for this
     cell, and an arbitrarily more skewed (but still valid) cell could blow
     it up arbitrarily further, or blow up the verifier's `O(N² × shifts)`
     tensor memory. Fixed with a lattice-basis reduction step (pairwise
     Gaussian-style reduction generalized to 3D, a unimodular transform —
     same physical lattice, far better-conditioned) before computing the
     bound, in both `solve.py` and the verifier's reference. QC's exact
     counterexample now resolves via a 3/3/3 bound instead of 42/11/3.
   - **Narrow/Hardcodable Held-Out Coverage**: a mutant excluding only the
     exact zero-shift self-image (not every image of an atom with itself)
     passed all 11 prior fixtures, because none had a cell small enough for
     a periodic self-image to matter. `solve.py`'s original self-exclusion
     logic was already fully correct (`if i == j: continue`) — this was
     purely a missing-fixture gap. Fixed: added `held_self_image_1` (2
     atoms, 2.5 Å cubic cell, 2.8 Å cutoff), and disclosed the
     self-exclusion convention in `instruction.md` (genuinely a convention,
     not a "unanimously agreed" fact — some real neighbor-list tools do
     count self-images when cutoff exceeds half the box).

   **Re-ran the full pipeline: review/similarity/validation all passed.
   pass@2 came back 2/2 SOLVED** — see below for why this is the load-bearing
   result.

## The 2/2 result on `e0822f1`, and why it's a different kind of signal

Both trials passed all 12 structures (1 example + 11 held-out) with exact
matches. Reading the trajectories:

- **task__z8wxg2P**: wrote a fully general, correct algorithm (Cauchy-bound
  derived from the inverse metric tensor to bound the search cube, wrapped
  positions to `[0,1)` first) in one pass, no in-development failures,
  validated it against self-constructed edge cases before submitting.
- **task__bStozcN**: started with the naive per-axis-rounding shortcut,
  **caught its own mistake by constructing a randomized skewed-lattice test
  and comparing against a brute-force reference it wrote itself** (detected
  round-vs-brute distance discrepancy, 2.091 vs 1.902), then iteratively
  fixed it with a QR-decomposition sphere-decoder approach.

The reviewer's own verdict: "both agents independently identified the same
two pitfalls and solved them... suggesting this strategy is well within
training-data reach." The `bStozcN` trajectory is the more important data
point — it demonstrates the crux is **not just recallable, it's
self-verifiable**: an agent doesn't need to have memorized the right
convention if it adopts a general practice of differential-testing a fast
candidate implementation against a slow-but-obviously-correct brute force on
randomized synthetic inputs (including edge cases like skew and offset,
which the instruction itself hints at by disclosing "may be triclinic" and
"not necessarily wrapped"). This is a **structurally different defeat
mechanism** from the one documented in
`dynamo_enumeration_defeats_evidence_inference` (systematic enumeration of a
small candidate-convention space): here there's no convention to guess
between, just a correctness bug that a careful agent's own testing habit
will surface, given ANY sufficiently adversarial randomized input.

**Why more geometric-correctness fixtures likely won't help further:**
both winning trajectories implemented genuinely *general* algorithms (valid
for any cell, any cutoff, any offset), not solutions tuned to pass specific
fixtures. A general, correct algorithm handles held-out edge cases by
construction — adding more such cases doesn't stress a general solution the
way it stresses a narrow one. This matches memory's documented pattern from
`dynamo-0cfa37b`: "when a trace reports no divergence at all, there is no
lever, and that is the signal to stop iterating and put redesign-vs-continue
to the user rather than inventing a case" — except here the signal is
"both trajectories converged on genuinely correct, general solutions" rather
than "both trajectories matched the golden approach."

**A second, compounding concern:** each QC round's fairness-mandated
disclosure (inclusive cutoff, self-exclusion convention, "not necessarily
wrapped") has cumulatively made `instruction.md` an increasingly complete
correctness checklist. This is individually correct and required (QC would
otherwise legitimately flag each as an undisclosed requirement) but may be
raising the *derivability* of the full correct algorithm each round —
possibly contributing to the empirical trend 1/2 → 1/2 → 2/2, though the
sample size (3 runs, 6 trials total) is too small to be certain this is a
real trend versus noise.

## Empirical pass@2 track record on this design (`86a8659` → `e0822f1`)

| Commit | Result | Failing trial's actual mistake |
|---|---|---|
| `86a8659` | 1/2 valid fail | naive per-axis rounding (didn't attempt full enumeration) |
| `f95a1c6` | 1/2 valid fail | naive per-axis rounding + missed `held_boundary_1` epsilon |
| `e0822f1` | 2/2 solved | (no failure — both built general, correct, self-verified solutions) |

Across 3 independent 2-trial samples: 4 solved / 2 failed = ~33% observed
per-trial failure rate. pass@5 needs **≥3/5 (60%) valid failures** to avoid
rejection as too easy — a materially higher bar than what's been observed
so far. Even if a future pass@2 re-roll lands another valid failure (the
platform's own "Rerun Recommended: YES" suggests this is plausible), there
is a real risk pass@5 lands at 1-2/5 and the task is rejected downstream
after clearing pass@2.

## Design 2 (site-multiplicity): what was tried, chosen per the user's
## Option B answer, and how it also failed

Per the user's explicit choice (Option B above), redesigned away from
periodic-image geometry entirely. New crux (commit `9aa9715`): given an
atom's fractional coordinates and a FULLY DISCLOSED list of real symmetry
operations (rotation + translation, taken from real published space groups
— P-1, P2_1/c, C2/c, P2_1 2_1 2_1, verified against the International
Tables for Crystallography via web search before use — not invented, not
named/lookupable by the agent), compute the atom's site multiplicity: the
number of distinct positions the operations generate. All data disclosed,
no external-lookup burden. The intended crux: an atom on a symmetry element
(inversion center, rotation axis) generates FEWER distinct positions than
the operation count, but "apply every operation, don't deduplicate" is a
natural implementation that's correct for any GENERIC-position atom — a
measure-zero event for an agent's own self-chosen test coordinates,
designed specifically to defeat the self-testing mechanism that killed
design 1.

**Result 1 (`9aa9715`): pass@2 2/2 solved, first push.** But the *reason*
mattered: both agents wrote correct deduplication logic on their first
attempt, no debugging or self-testing needed at all. Reviewer's own
diagnosis: "established training-data knowledge of crystallographic
multiplicity algorithms." **This falsifies the self-testing-resistance
premise the design was built on** — it doesn't matter that self-testing
can't discover the bug if the model already knows the correct approach
cold, without needing to discover anything. The rubric reviewer had flagged
this risk pre-emptively on the very first review: "borderline PASS... a
strong model could plausibly one-shot [this]... elementary to a
crystallographer."

The platform's automated pass@2 difficulty suggestion additionally
identified a compounding, directly-fixable issue: `instruction.md`'s
coincidence-rule wording ("two resulting positions ... count as the same
position if every fractional coordinate differs by less than `1e-6`")
handed over the *entire* comparison procedure verbatim, not just the goal.

**Fix attempted (`5b017a4`):** reworded `instruction.md` to state the goal
(count distinct positions, understood periodically) rather than the
mechanical procedure; this also surfaced and fixed a genuine latent
correctness bug the suggestion named — naive per-component coincidence
comparison isn't periodicity-aware (fractional coordinates are points on a
3-torus; two independently-wrapped images of the same point can legitimately
straddle the `[0,1)` boundary) — fixed with proper minimum-image reduction
in both `solve.py` and the verifier's reference.

**Result 2 (`5b017a4`): pass@2 2/2 solved AGAIN.** Both agents this round
*also* got periodicity-awareness right, unprompted, explicitly reasoning
in their own trajectories: "a component difference of (near) exactly 1
does not distinguish two positions" — nearly verbatim the exact phrasing
this handoff's author used internally to describe the insight, independently
arrived at. Reviewer's convergence note: "the core insight is well within
training-data knowledge for this class of computational crystallography
task." No held-out fixture ever forced the specific floating-point boundary
case in practice (constructing one reliably from real space-group fractions
proved too fragile to engineer confidently in the time available), so this
fix was never truly tested against a case that would fail a naive
implementation — but even so, both agents implemented the periodicity-aware
version anyway, unprompted, meaning a fixture wouldn't have been the
deciding factor regardless.

**What this second wall adds to the picture:** design 1's wall was one
specific defeat mechanism (self-verifiability via differential testing)
against one specific geometric crux. Design 2's wall is different in kind —
it's not that the agent COULD verify correctness via testing, it's that the
agent needed no verification step at all, on TWO independent
crystallographic concepts in a row (Wyckoff-multiplicity reduction; periodic
minimum-image coincidence). Both are textbook material (International
Tables level for the first, basic PBC handling for the second) — exactly
the kind of "well-represented in training data" concept the very first
design (triclinic MIC alone, the ORIGINAL wall on this PR) also fell to.
Three-for-three now: every mainstream crystallography/periodic-geometry
concept-application crux tried on this PR has been within this model's
reach, whether or not self-testing was needed to find it.

## The decision this handoff exists to get (second time)

**Option A — push once more, cheap, stochastic.** Same logic as before:
pass@2 is stochastic, a trivial push could land a valid failure by chance.
Weaker case this time than after design 1's first 2/2 (that design had
ALSO shown 2 genuine valid failures elsewhere in its history; design 2 has
shown zero — 0/4 trials failed across two independent pass@2 samples).

**Option B — a THIRD design, this time genuinely obscure, not just
"externally disclosed."** The lesson sharpens: disclosing data as input
(rather than requiring recall) removes the recall burden but does NOT
remove the "well-known training data" risk if the CONCEPT/ALGORITHM to
apply to that data is itself mainstream. The winning formula elsewhere in
this playbook (`dynamo-602128a` gemmlowp; `dynamo-3779991` RDFC-1.0) always
paired disclosed *data* with an *obscure implementation convention that
lives in one specific real codebase's internals*, not a generically-taught
concept — e.g. gemmlowp's specific requantization shift-sign convention
(not "quantization" the general topic), RDFC-1.0's specific
deduplicate-triples-before-hashing step (not "canonicalization" the general
topic). For Chemistry/materials workflows, this means looking further past
"textbook crystallography with the data given" toward something like a
specific numerical/format convention documented only in one real tool's
source or one real file-format spec's edge-case handling — candidates not
yet tried: partial-occupancy/split-site handling conventions in real CIF
consumers (real, documented pitfall per web search during this round, not
yet built into a task); ADP (anisotropic displacement parameter) tensor
convention differences between SHELX and CIF-standard representations.
Needs fresh design-from-scratch effort and, given two designs have now
failed, may warrant discussing the category-fit question too (see Option C).

**Option C — reconsider whether "Chemistry and materials workflows" is
survivable against this model with the time/effort remaining**, and discuss
with the user whether to keep trying within this exact subcategory or (per
docs 40/41's category-mismatch tolerance, same option surfaced in
`dynamo-0cfa37b`'s handoff for a different task) accept a small
category/subcategory-fit risk for a design better suited to a different
scientific-computing area. Not recommended over Option B without discussing
first — two failed designs is not yet the four-plus seen before this
question was raised on other tasks.

## What is NOT the problem (ruled out, don't re-litigate)

- **Mechanical soundness.** Every fix cleared `oracle=1.0`, `nop=0.0`, and
  every QC-flagged mutant re-tested at `0.0` through the real Harbor
  verifier before pushing — no exceptions across 3 QC rounds.
- **Disclosure fairness / rubric quality.** Rubric review (`review`) has
  passed cleanly on every commit since `0f49e56`, all 31 criteria, no
  regressions. `deep_review`/`ava_review` have each passed cleanly twice.
- **CI/infra hygiene.** `.dockerignore` present from the first push,
  README/task.toml synced every commit that changed design/verifier
  behavior, no AI attribution, commit messages written via message files to
  avoid shell-escaping issues with `<=` and special characters.
- **The QC process itself.** Every QC finding across all 3 rounds was a
  genuine, legitimate bug or coverage gap when investigated by hand — none
  were QC false positives. (One did require independent local
  reproduction to correctly diagnose — see the Oracle Edge-Case finding
  above, where the terse/truncated evidence text alone was insufficient and
  misleading at first glance.)

## Mandatory rules to keep following if iteration resumes

- `harbor run -p task --agent oracle` must show reward 1.0 and `--agent nop`
  must show reward < 1.0 before every push.
- Before every push, build the exact mutant matching the newest QC/pass@2
  finding and confirm 0.0 through the real (harbor) verifier — this has
  caught real gaps (and once, a real false alarm avoided) every time.
- When QC's evidence text is truncated or ambiguous, reproduce the exact
  cited input locally with a standalone Python script before assuming what
  the bug is — the Oracle Edge-Case finding in round 3 initially looked like
  a wrong-value bug but was actually a robustness/scaling bug once verified
  by hand.
- `README.md` and `task.toml`'s three explanation fields must be re-synced
  in the same commit as any design/verifier change — done every round so
  far, keep doing it.
- Commit messages containing `<=`, unescaped quotes, or other shell-special
  characters must be written to a file first (`Write` tool) and committed
  via `git commit -F <file>` — `git commit -m "..."` broke bash parsing once
  already on this PR.
- Per the user's standing instruction for this session: iterate
  autonomously, do not wait for responses, fix/redesign within category and
  subcategory. This handoff exists because the pass@2 pattern (1/2 → 1/2 →
  2/2, with the 2/2 trial showing genuine self-verified general-algorithm
  convergence) matches the documented `dynamo_pause_on_failure_after_long_
  iteration` / `dynamo-0cfa37b` "no lever, converged" signal — exactly the
  case that memory says should trigger a decision checkpoint rather than
  another autonomous guess.

## When the task finishes (accepted, or the user decides on a genuine dead end)

Write a case-study markdown into
`C:\Users\chara\Downloads\Handshake\dynamo-task-playbook\` (see other files
there for format), folding in this handoff's content and the final outcome,
then `git add`/`commit`/`git pull --rebase`/`git push` to `origin main` from
inside that folder — delete this handoff file in the same commit.
