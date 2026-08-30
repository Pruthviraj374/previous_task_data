# dynamo/trace-junction-graph — seven designs, seven clean solves: Computational Geometry saturated

| | |
|---|---|
| **Outcome** | **DEAD END, not accepted** — PR #3 left open with the seventh (final) design in place; no design across the whole task reached a valid pass@2 failure |
| **Repo** | `dynamo-06c66c0-mathematics-and-formal-reasoning`, PR #3, branch `submission`, fork `charan-sr` |
| **Category / sub** | Mathematics and Formal Reasoning / Computational Geometry (both pre-seeded) |
| **Benchmarked model** | Opus-4.8 / Terminus-2 (per `task.toml`) |
| **Span** | Seven full designs across one very long session; dozens of commits |
| **Headline** | **Every design solved 2/2, every time.** Real facts, disclosed rules, undisclosed rules, raw implementation difficulty, forced-library environments, and — the final, most sophisticated attempt — a genuinely entangled two-stage compound where a stage-1 mistake corrupts stage 2 in a way that still passes internal self-checks. All seven landed the same way. |

This entry exists because the pattern here is bigger than any one crux family (contrast
`dynamo-24cd443-keepcase-restore.md`, where four saturated designs were escaped by moving to an
adjacent mechanism family within the same category). Here, seven designs spanning **disjoint**
mechanism families, disjoint disclosure strategies, and even genuine cross-mechanism entanglement
all failed the same way. The honest reading, after this much surface area: Computational Geometry
itself is functionally saturated for this model on a platform that forces `allow_internet = true`
with no way to deny tool/library access.

---

## 1. The starting shape

`task.toml`'s subcategory (Computational Geometry) was pre-seeded and could not be changed.
`allow_internet = true` was later confirmed, via an actual rejected push, to be a **hard, platform-
wide static-check requirement** — not a per-category or per-task setting, and not something a
Dockerfile-level network restriction can quietly route around either (the static check re-derives
the effective setting). This one fact eliminates an entire category of otherwise-promising designs:
anything whose difficulty depends on denying the agent a library or on making a naive approach too
slow, since a fast, well-optimized library is always one `pip install` away regardless of the
task's own timeout budget.

## 2. The seven designs

| # | Name | Mechanism | Result |
|---|------|-----------|--------|
| 1 | `trace-junction-graph` (+3 sub-variants) | Exact-vs-float road-segment junction extraction; self-intersection/degeneracy ordering; collinear-overlap definition | Clean pass@2, every variant |
| 2 | `parcel-net-topology` | Nested-ring containment, signed net-area accumulation, depth-parity role alternation (island/pond/parcel) | Clean pass@2 |
| 3 | `floor-area-takeoff` | DCEL/half-edge planar-arrangement extraction from raw wall segments, room/column subtraction | Clean pass@2, split 1/1 — one trial used `shapely.ops.polygonize` (a real library one `pip install` away), the OTHER implemented the DCEL correctly from scratch, unassisted |
| 4 | `scaled-junction-graph` | 10,000-segment scale-forcing (grid-pruned spatial search vs. O(n²) infeasibility), `allow_internet = false` to block the library escape hatch | **Rejected by the static check before pass@2 could even run** — confirmed `allow_internet=true` is non-negotiable platform-wide |
| 5 | `riparian-lot-apportionment` | Real surveyor's perpendicular/angle-bisector lot-boundary construction, tried at TWO disclosure levels (full algorithm spec, then a goal-only rewrite per the platform's own pass2-difficulty-suggestion) | Clean pass@2 at BOTH disclosure levels — proof the "how" was never genuinely hidden information |
| 6 | `hull-onion-peeling` | Cascading convex-hull "onion" layer peeling with exact edge-collinear-point inclusion, 14 nested layers | Clean pass@2 — raw from-scratch implementation difficulty alone, again, did not stump this model |
| 7 | `nested-riparian-rings` | Genuinely entangled COMPOUND of #6 + #5: peel into layers, then apportion each ring gap via the bisector construction, so a peeling mistake corrupts downstream apportionment invisibly (the miter-join construction tiles whatever polygon it's handed, correct or not — the corrupted output still passes internal area-conservation) | **Also clean pass@2** — the most sophisticated entanglement attempt available, still solved cleanly |

## 3. The settled derivability rule, confirmed nine-plus times across this task alone

The load-bearing finding, already recorded in `dynamo_enumeration_defeats_evidence_inference.md`
before this task started and reconfirmed here at unusual depth:

> **Obscurity to humans is not the filter. Derivability is.** If a competent agent could derive the
> unique correct output by reasoning carefully from disclosed material, expect a clean pass@2 solve
> regardless of how obscure, real-world, or implementation-heavy the construction feels. Difficulty
> needs either a genuinely arbitrary, undisclosed, real convention (which the platform's own
> fairness bar — `decisive_answer_discoverable`, `unambiguous` — actively works against) or a fact
> not present in mainstream training data (increasingly rare for anything a task author can verify
> without unacceptable research risk).

Design 5's two-disclosure-level result is the cleanest isolation of this rule available in the
corpus: identical geometry, identical verifier, only the instruction's prescriptiveness changed
(full step-by-step algorithm vs. goal-only problem statement), and it made **no difference** to the
outcome. The platform's own automated pass2-difficulty-suggestion diagnosed the first version
almost verbatim to the pre-existing memory rule, independently: *"instruction.md is not a problem
statement; it is a step-by-step algorithm spec... the task reduces to a straightforward coding
exercise."* Rewriting it as a goal-only spec removed the "algorithm spec" framing but didn't remove
any actually-hidden information — every "hint" that was cut (bisector = vector sum, extend to the
thread line, follow the arc not a chord) was mechanically derivable from the stated goal by a
competent reasoner. There was no real information asymmetry to exploit by withholding it.

## 4. The real-library escape hatch, and its limits

Design 3 (`floor-area-takeoff`, DCEL/half-edge arrangement extraction) is the sharpest confirmation
in this corpus of a *different*, complementary escape mechanism: **any standard geometric operation
with a mature Python library is trivially escapable via `pip install`, regardless of implementation
difficulty, whenever `allow_internet` can't be denied.** One trial reached for
`shapely.ops.unary_union` + `polygonize` and solved the entire task in three lines, bypassing the
intended half-edge/turn-direction difficulty entirely.

**But this does NOT mean closing the escape hatch fixes anything.** The *other* design-3 trial
implemented the DCEL correctly from scratch, unassisted — proving raw algorithmic skill alone is
often sufficient even without the library shortcut. Design 6 (hull-onion-peeling) was built
specifically to test this: it requires edge-collinear-point handling that most hull libraries
(including `scipy.spatial.ConvexHull`/Qhull) drop by default, so a naive library call doesn't
directly satisfy the schema — and it still solved cleanly, via correct from-scratch implementation.
**Closing the library escape hatch only removes one of two independent paths to a clean solve; the
other (genuine skill) remains, and this model has it in Computational Geometry.**

A related, now-closed sub-finding: `allow_internet = false` was tried explicitly (design 4,
`scaled-junction-graph`) as a more direct way to deny the library escape hatch, and was rejected
outright by the platform's static check — confirmed as a hard, platform-wide requirement with no
per-task override, not a category-specific constraint as originally assumed.

## 5. The entanglement attempt, and why it wasn't enough either

Design 7 was the deliberate answer to "what if independently-derivable pieces just aren't hard
enough, no matter how many are chained?" (Pattern G, cascading application, vs. Pattern H, genuine
entanglement.) Rather than inventing an eighth wholly-new mechanism, it combined two already-
individually-solved mechanisms (peeling, apportionment) so that a mistake in the first stage feeds
corrupted input into the second stage — and critically, the corruption is *invisible to the agent's
own self-checks*, since the apportionment construction tiles whatever shoreline/thread-line polygon
it's handed, correct or not, and the resulting lots still pass internal area-conservation. This
closes the gap where a standalone peeling task's failure mode (a simple point-count mismatch) might
be too easy for an agent to self-verify away.

It still solved cleanly, 2/2, both trials. The working hypothesis after this result: this model's
strength in Computational Geometry isn't really about "can it debug via self-checking" — it's a
more fundamental "given a precisely stated geometric construction, of essentially any complexity or
compound structure, this model correctly implements it in one shot." Compounding difficulty by
chaining more correctly-implementable stages doesn't accumulate failure probability the way it
might for a weaker model; it just means more correct code gets written.

## 6. Fixture-engineering lessons (reusable regardless of the category-level outcome)

These are independent of whether Computational Geometry pans out on a future task — they're
technique-level findings from building seven exact-arithmetic geometry fixtures under real time
pressure, in a subject area (miter-join/angle-bisector construction, convex-hull peeling) with
almost no prior worked examples in this corpus.

1. **An open shoreline/polygon with two free "ends" is a trap.** Design 5's first riparian attempt
   used an open polyline for the shoreline, with the two endpoints handled via a simple
   perpendicular-only rule. This produces self-intersecting lot boundaries whenever a nearby real
   corner's bisector swings far enough — there is no principled way to close off two open ends
   consistently with the interior bisector logic everywhere else. **Fix: use a closed loop.** Real
   lake shorelines are closed loops anyway; this sidesteps the whole problem rather than patching it.

2. **A single rectangular thread-line inset cannot satisfy both "straight corners need width" and
   "sharp turns need clearance" at once.** A rectilinear shoreline with a deep notch produces
   bisector rays that swing far enough to overshoot a tightly-inset thread line, landing on a
   non-adjacent ring edge (wraparound ambiguity in which arc to follow). A widely-inset thread line
   then fails to reach straight-run corners whose bisector points straight "up." **Fix used:**
   either avoid concave/reflex shoreline corners entirely (design 5's final convex 12-gon), or make
   the thread line a genuine constant-offset copy of the shoreline's own shape rather than a generic
   rectangle (not attempted here, but the principled fix for a future concave-shoreline design).

3. **A plain axis-aligned rectangle survey is hand-derivable, and the rubric will catch it.**
   Design 5's first non-degenerate fixture decomposed entirely into plain rectangles and 45-45-90
   triangles — flagged as `code_dependent` FAIL ("hand-derivable... short-circuitable by
   reasoning"). **Fix: use genuinely non-axis-aligned, non-90-degree geometry** — a convex polygon
   built from several different scaled Pythagorean triples (3-4-5, 4-3-5, etc. rotated through 12
   angles) gives equal-length edges at varied angles, so the exact-rational bisector-as-vector-sum
   shortcut still works but the resulting shapes and bisector directions are genuinely irregular.

4. **A strict-vertex-chain function needs a DIFFERENT monotone-chain pop threshold than a
   boundary-inclusive chain function, and copy-pasting one into the other is a real, easy-to-miss
   bug.** `hull_boundary_points`'s inner chain (used to find every point on a hull boundary,
   including edge-collinear ones) correctly pops on `cross(...) < 0` — strict clockwise turns only,
   keeping collinear continuations in the chain so they can later be tested as boundary members.
   `hull_vertex_chain` (used to get ONLY the strict extreme vertices, for use as an ordered
   frontage polygon) needs `cross(...) <= 0` — also popping on exact collinearity — or it silently
   keeps every edge-collinear point as its own "vertex," corrupting the equal-length-edge invariant
   the bisector shortcut depends on. Caught by the incremental validation discipline (self-check the
   generator against the oracle's own functions before trusting either), not by inspection.

5. **Grading by a positional/labeling convention the instruction never discloses is an unfairness
   bug, not a minor nit.** Design 7's `lot_id` was originally graded by exact string match, but
   `instruction.md` never specified which frontage gets which number or which direction numbering
   proceeds — so a geometrically perfect answer with different (equally valid) labeling would have
   failed. **Fix: grade by geometry, not by label** — a greedy bipartite match between expected and
   actual lot boundaries (each canonicalized to its corner set), independent of `lot_id` or list
   order. Verified directly: a correct solution with shuffled, arbitrarily-relabeled lot_ids now
   passes; both known wrong-construction rejections still correctly fail.

6. **Generate ground truth by calling the oracle's own functions directly, never a separately
   re-implemented copy.** Every design from #5 onward built the fixture generator by importing
   `solution/solve.py` and calling its functions to produce `expected_*.json`, rather than keeping a
   second independent implementation in the generator script. This makes "oracle output exactly
   matches ground truth" a triviality rather than a real test, but it also makes the *converse*
   check — a deliberately wrong construction, hand-written separately, correctly rejected by the
   verifier — the load-bearing correctness signal instead. Both checks were run for every design
   before push.

7. **A wedged GitHub Actions runner is real and needs a specific recovery path.** One CI run's
   `review/cosine_similarity` job hung on its "Extract read-only task fingerprint" step for over an
   hour with zero step progress, while every step before and after it was seconds-fast — a genuine
   runner-level hang, confirmed via `gh api .../actions/jobs/<id>` step timestamps, not a broader
   platform slowdown (other stages on the same run completed normally). `gh run rerun --failed` and
   `gh run cancel` both returned `404 Not Found` — this fork/PR's token lacks `actions:write` on the
   upstream org repo. **Fix: `git commit --allow-empty` with a message explaining why, then push** —
   forces a fresh workflow run via the normal push trigger, which resolved cleanly on retry.

## 7. Reusable checklist

1. **Before spending hours on a Computational Geometry crux for this model/platform combination,
   read this entry and `dynamo_saturated_crux_families.md`'s category-level-saturation extension
   first.** Seven genuinely disjoint approaches (disclosed-rule, undisclosed-rule, real-vs-obscure,
   raw implementation difficulty, scale-forcing, single-mechanism, and genuine cross-mechanism
   entanglement) all failed identically. A category/subcategory change is the load-bearing lever
   here, not another mechanism variant.
2. **`allow_internet = true` is a hard, platform-wide static-check requirement with no per-task
   override.** Do not attempt `allow_internet = false` to block a library escape hatch — it will be
   rejected before pass@2 even runs.
3. **Closing a library escape hatch does not, by itself, fix a saturated design.** Check whether the
   OTHER path to a clean solve (genuine correct from-scratch implementation) is also viable before
   investing effort in blocking the library-specific one.
4. **For any miter-join/angle-bisector construction: use a closed shoreline loop, not an open one
   with special-cased ends.** Real closed-loop shorelines sidestep an entire class of
   self-intersection bugs at the open ends.
5. **A rectangular/generic thread-line inset cannot handle both straight-run corners and sharp
   concave turns simultaneously.** Either avoid concave shoreline corners, or make the thread line a
   true constant-offset copy of the shoreline's own shape.
6. **A plain axis-aligned rectangle (or any shape decomposable into textbook primitives) will be
   flagged `code_dependent` FAIL as hand-derivable.** Use genuinely irregular, non-90-degree
   geometry — scaled Pythagorean triples at multiple angles keep exact-rational arithmetic tractable
   while avoiding trivial decomposition.
7. **A "strict vertices only" chain function needs a stricter pop condition than a
   "boundary-inclusive" chain function** — verify this explicitly if reusing hull-construction code
   for both purposes; they are NOT the same function with a different name.
8. **Grade compound/multi-entity outputs by content, not by a labeling convention the instruction
   never discloses** — a positional/ID-based match is an unfairness bug waiting for the rubric to
   catch it.
9. **Build fixture generators by calling the oracle's own functions, and separately hand-write at
   least one deliberately-wrong construction to confirm the verifier actually discriminates** — both
   halves are needed; matching-the-oracle alone proves nothing about the verifier's real power.
10. **A CI stage stuck 10x+ its normal duration on one step, with everything after it still
    `pending`, is a wedged runner, not a slow one — confirm via the jobs API before waiting further,
    and recover with an empty retrigger commit if `gh run rerun`/`cancel` return 404.**

### One-paragraph version for future me

Seven designs across a full session in Mathematics and Formal Reasoning / Computational Geometry —
exact-vs-float junction extraction, nested-ring topology, DCEL arrangement extraction, scale-forced
spatial search, real surveyor's bisector construction at two disclosure levels, cascading
convex-hull peeling, and a deliberately entangled compound of the last two — every single one
solved cleanly, 2/2, every time. `allow_internet=true` is a hard platform-wide requirement (no
per-task override), which kills any design relying on denying tool/library access; but even where
the specific library escape hatch was closed (hull peeling's edge-collinear handling, which most
libraries drop by default), the model's raw from-scratch implementation skill carried it through
regardless. The settled derivability rule held at every test: obscurity doesn't matter, only whether
the unique correct output is derivable from disclosed material — confirmed most cleanly by design
5's two-disclosure-level result (full algorithm spec vs. goal-only rewrite, identical outcome, since
nothing withheld was ever genuinely hidden information). Compounding two already-solved mechanisms
into one genuinely entangled pipeline (design 7) — where a stage-1 mistake corrupts stage 2
invisibly, defeating internal self-checks — was the most sophisticated attempt available and it
still didn't move the needle. The honest conclusion: Computational Geometry is functionally
saturated for this model on this platform, and the next lever for this task is a category or
subcategory change, not another mechanism inside this one.
