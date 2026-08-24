HANDOFF: dynamo-20141f7-scientific-computing-and-domain-science (PR #1)
========================================================================
Last updated: after pass@2 returned 2/2 solved on commit `e0822f1`
(2026-08-25), the third independent pass@2 sample on the same underlying
design.

-----------------------------------------------------------------------
STATUS IN ONE SENTENCE: one design (compound triclinic-minimum-image +
unwrapped-input-robustness crux), hardened through 3 QC (mutation-testing)
fix rounds and 12 commits, has gotten a genuine pass@2 valid failure twice
(1/2, 1/2) and a clean 2/2 solve once — the clean-solve trial shows both
agents independently building fully general, correct algorithms, one of
which self-caught its own initial mistake via differential testing against
a self-built brute-force reference. This is a decision point, not a bug
to fix.
-----------------------------------------------------------------------

## Repo / PR pointers

- Local clone: `C:\Users\chara\Downloads\Handshake\dynamo-20141f7-scientific-computing-and-domain-science`
- Branch: `submission`, currently at commit `e0822f1` (nothing uncommitted)
- PR: https://github.com/handshake-project-dynamo/dynamo-20141f7-scientific-computing-and-domain-science/pull/1
- Category/subcategory (fixed, do not edit): Scientific Computing and Domain Science / Chemistry and materials workflows
  (first task in this exact subcategory — no prior in-category precedent existed to check against)
- Model/agent under test: Opus-4.8 / Terminus-2
- Root `README.md` describes the current design in full, including the QC-fix history.

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

## The decision this handoff exists to get

**Option A — push once more, cheap, stochastic.** Pass@2 is genuinely
stochastic and the platform explicitly suggests rerunning. A near-zero-cost
push (e.g., a trivial docstring tweak, or literally re-triggering CI) could
land another valid failure and let the pipeline proceed to pass@5, where the
real test (≥3/5) happens. Low cost, but the ~33% empirical trial-failure
rate makes pass@5 acceptance a real coin-flip-or-worse even if pass@2 clears
again — this may just delay hitting the same wall one stage later.

**Option B — redesign toward a genuinely externally-grounded,
self-testing-resistant crux**, per the winning formula already validated
elsewhere in this playbook (`dynamo-602128a`'s gemmlowp rounding,
`dynamo-3779991`'s RDFC-1.0 blank-node canonicalization): a crux where the
"correct" answer depends on a real external standard/algorithm's specific
step, not on geometric first-principles reasoning alone — so an agent's own
brute-force self-test can't validate correctness without *already* knowing
the external rule. Within Chemistry and materials workflows, the strongest
candidate considered but not yet built: symmetry-equivalent atom position
generation from a real space-group's full operator list (International
Tables for Crystallography) — genuinely requires applying every operation,
not just generators, handling centering translations, and deduplicating
overlapping images; there's no way to construct an independent "obviously
correct" brute-force reference without external crystallographic data,
unlike periodic-image geometry which is fully first-principles-derivable.
Higher effort (new instruction, solve.py, tests, fixtures from scratch), and
carries its own version of the disclosure-vs-difficulty tension (must avoid
naming any specific tool/library that would hand over the exact operator
data via a two-query search) — not risk-free, but addresses the
*structural* cause rather than another instance of the same wall.

**Option C — accept this task has reached a defensible-but-uncertain state
and submit as-is**, since pass@2 alone is not the acceptance gate (pass@5
is) and the design has demonstrably passed pass@2 with genuine, reviewer-
confirmed valid failures on 2 of 3 samples — it's possible pass@5 lands
≥3/5 despite the concerning trend. Not recommended without at least trying
Option A first, given the near-zero cost of a re-roll.

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
