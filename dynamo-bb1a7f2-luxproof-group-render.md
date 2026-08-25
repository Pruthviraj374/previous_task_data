# dynamo-bb1a7f2 — luxproof-group-render

| | |
|---|---|
| **Outcome** | **ACCEPTED** — every check green, `accepted` label |
| **Repo** | `dynamo-bb1a7f2-games-puzzles-and-interactive-simulation` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-bb1a7f2-games-puzzles-and-interactive-simulation/pull/1 |
| **Category / sub** | Games Puzzles and Interactive Simulation / Rendering graphics (pre-seeded) |
| **Final commit** | `78ec3a3` |
| **Headline** | **pass@5 = 1/5 solved** (2 idle-loop timeouts, 1 near-miss timeout, 1 genuine edge-case bug). `pass@2` = 1/2 the round that broke through, then 2/2 twice more on unrelated pushes before the final accepted round. |

Reconstruct a retired signage-proofing tool's multi-layer bitmap renderer
(`LUXPROOF`) from a surviving job archive and a format note. Read this if
you're about to build a Pattern-D ("evidence-forced disclosure") task in a
rendering/compositing domain — the central finding is that Pattern D alone is
**not sufficient** when the withheld rule is the only sensible way to extend a
formula the spec has already fully disclosed for a sibling record type.

---

## 1. What the task asks

The agent writes `/app/render.py` exposing `render(source: str) -> bytes`
that reproduces a retired tool's exact PPM (P6) preview bitmap for a small
DSL: `CANVAS`, `RECT` (alpha-blended rectangle, optional `MUL` combine), and
`GROUP`/`ENDGROUP` (named, nestable groups with their own alpha). The
compositing math (continuous arithmetic, round-half-up once at 8-bit output,
the `MUL` blend formula) is disclosed in full. Graded byte-exact, all-or-
nothing, against 7 shipped samples and 18 held-out jobs never shown to the
agent.

---

## 2. The three cruxes, in the order they were added — and what each one taught

**Crux 1 — group alpha applied once, not per-member.** A group's members
paint onto a fresh, isolated local surface; the group's own alpha scales that
*finished* surface's coverage once, at composite time — not distributed into
each member's alpha as it paints. This is a real, well-documented gotcha
(why a group's opacity differs from multiplying each member's own opacity;
matches SVG/PDF isolated transparency groups).

**Crux 2 — group-level `combine`.** `GROUP` lines can carry the same
optional `MUL`/`NORMAL` token `RECT` lines already have, controlling how the
group's finished surface blends against its parent. Real (blend modes are a
property of a whole layer/group in every mainstream compositing tool, not
just individual shapes), and structurally novel — no sample gave a `GROUP`
line a fourth token before this crux was added.

**Crux 3 — `KNOCKOUT` groups.** `GROUP` lines can carry a trailing
`KNOCKOUT` token. Ordinarily a group's own members paint onto an
*accumulating* local surface — each sees everything earlier siblings
painted. A `KNOCKOUT` group's members instead each composite only against
the group's *fixed initial (empty)* backdrop, so overlapping siblings never
blend with each other — the real PDF/Illustrator distinction between an
ordinary group and a knockout group.

Crux 1 alone, disclosed via a worked sample with no supporting standard-name
(pure Pattern D), was **solved 2/2 at `pass@2` three separate times in a
row** on the exact same underlying design — once with a 3-member worked
example and full disclosure prose, once after trimming the sample to 2
members/1 overlap region, once after stripping `LUXPROOF.md`'s prose down to
a bare pointer at the evidence with *zero* restatement of the timing rule.
One trial derived the rule from the sample alone in ~7 minutes even under
that minimal disclosure. Crux 2, added on the same footing, did not change
the outcome — `pass@2` solved crux 1 *and* crux 2 together 2/2 a fourth
time, both trials implementing both rules correctly with clean, modular
code in 15–23 minutes, no near-misses.

**The diagnosis, read directly off that pattern:** cruxes 1 and 2 are each
*the one obvious way to extend a formula the spec had already fully
disclosed* — reuse `RECT`'s `MUL` formula for `GROUP`; treat an isolated
surface as a single paintable unit, exactly like a `RECT`. There is only one
sensible generalisation, so it is guessable by analogy regardless of how
tightly disclosure is calibrated around it. Removing the standard's *name*
(SVG/PDF) did not help; trimming the worked sample's redundancy did not
help; stripping the prose to a bare evidence pointer did not help. None of
those levers touch the actual reason it's easy — the *shape* of the
question, not how loudly the answer is stated.

Crux 3 (`KNOCKOUT`) was chosen specifically to break that pattern: it
changes **what data a member reads while painting**, not which
already-disclosed formula applies to already-agreed inputs. There is no
"obvious" extension to reach for, because nothing in the spec's existing
machinery hints that group membership could work any way other than
accumulate-as-you-go. It worked on the first attempt: `pass@2` passed
genuinely, 1/2, and the task cleared `deep_review`/`ava_review`/`tier1`/
`qc_eval`/`qc_exec`/`qc_gate` cleanly with zero findings — the first time
this task had ever reached QC. Both agents in that round correctly derived
and implemented `KNOCKOUT`; the one valid failure was an unrelated
implementation bug (see §3).

**Reusable rule:** when a Pattern-D crux keeps getting solved 2/2 no matter
how you tune disclosure or evidence, stop tuning disclosure and evidence.
Ask instead whether the withheld rule is *structurally* forced by something
already given. If it is, no amount of concealment fixes it — pick a crux
that changes the shape of the mechanism, not just which value fills in a
blank.

---

## 3. `pass@5` landed at a stochastic boundary for three *different* reasons — match the fix to the actual failure, not the last one

Getting `pass@2` and QC to pass cleanly did not immediately produce an
accepted task. `pass@5` needs `≤2/5` solved; it came back **3/5 twice** in a
row before the third round finally landed at **1/5**.

| Round | Result | Why, exactly |
|---|---|---|
| 1 (crux 3 just added) | 3/5 | 1 idle-loop timeout (agent never wrote code); 1 genuine edge-case bug — an agent using premultiplied-color storage skipped de-premultiplying before a `MUL` blend against a genuinely *partial*-coverage backdrop (`Dcov<255`), correct whenever `Dcov=255` so it passed every sample and 13/14 held-outs, wrong only on the one held-out (`h09`) built to entangle `MUL` with partial coverage inside an overlapping fractional-alpha group |
| 2 (after adding `h15`/`h16`, two more instances of that same trap) | 3/5 | **Both** failures this round were idle-loop timeouts — agents correctly derived all three cruxes by hand, then tried to generate the entire renderer in one giant inference call that ran past budget before writing any code. `h15`/`h16` made zero difference because nobody's failure that round touched the trap they targeted |
| 3 (after adding `h17` — all 3 cruxes entangled in one job — and `h18`, four-level nesting) | **1/5 — accepted** | 2 idle-loop timeouts, 1 near-miss timeout (the agent had two structurally-plausible `render.py` drafts and was mid pixel-comparison when cut off), 1 recurrence of the exact same `h09`-style de-premultiplication bug |

The critical mistake to avoid: after round 2 showed both failures were
*pacing*, not *crux*, the instinct is to keep deepening the same
`h09`-style trap (it worked once, so it must be the lever). It wasn't the
lever that round — neither failure got anywhere near it. The fix that round
was `h17`/`h18`: raise the *total* reasoning and implementation surface per
job (stack all three cruxes in one deeply-nested fixture), which targets
the actual observed failure mode (agents running out of budget on an
increasingly large task) rather than re-running a trap nobody hit.

**Reusable rule:** read what a `pass@5` failure actually was before deciding
what to add. "Add more instances of the trap that worked before" is the
right move only when the new failures are the *same kind* as the old ones.
When they're not — timeout vs. implementation bug are different failure
families entirely — the fix has to match the new evidence, not the last
successful lever.

---

## 4. `pass@2`'s small sample means "it passed" and "it failed" are both weak signal in isolation

Across the whole task, `pass@2` on the *exact same, unchanged* crux-1-alone
design produced: 2/2, 2/2, 0/2 (genuine), 2/2, 2/2, 2/2 — six rolls, one
genuine stump, five clean 2/2 sweeps. At an estimated true per-trial solve
rate around 50–60% (independently corroborated by three `pass@5` rounds
landing at 60%, 60%, and 20%), `P(2/2 in a 2-trial sample) ≈ 0.36` — a
thoroughly unsurprising outcome, not evidence the design regressed.

Two concrete moments this mattered:
- After crux 3 first passed `pass@2` (1/2), a *later*, content-neutral push
  (`f802a6b`, adding held-outs only) triggered a fresh `pass@2` roll that
  also passed — genuinely, but this is not something to expect every time;
  a different push (`5ca38d6`, adding `h17`) rolled 2/2 on the identical
  crux logic and blocked the whole pipeline (QC and `trials` are both
  downstream of `pass@2` and get skipped entirely on a `pass@2` failure).
- The fix for that 2/2 was **not** to revert or fight the roll — it was to
  make one more legitimate, evidence-backed content addition (`h18`) and
  push again, since a trivial re-push with no substantive change wastes the
  daily `pass@2` budget without giving the reviewer anything new to see.

**Reusable rule:** before reacting to a single `pass@2` result (in either
direction), check whether the observed rate is consistent with the
per-trial solve rate you already have independent evidence for (from prior
`pass@2` rolls or `pass@5` rounds). A 2-trial sample cannot distinguish "the
design regressed" from "this was always going to happen 1 time in 3."

---

## 5. The AVA copy-bypass — verifier hardening that had nothing to do with the crux

`ava_review` (adversarial verifier-soundness review) found that
`test_sample_output` compared `/app/output/<name>.ppm` bytes against a
sealed expected bitmap without ever tying those bytes to a live call of the
agent's `render()` — an agent could pass every sample test by copying the
shipped `/app/data/samples/*.ppm` files into `/app/output/` without
implementing `render()` at all. A secondary, non-blocking finding: the
sample list itself was enumerated from the agent-writable
`/app/data/samples/` directory, so deleting those files would silently
shrink the parametrized test list rather than fail it.

**Fix:** seal a copy of every sample's `.luxp` source under
`tests/data/samples_src/` (verifier-only, chmod 0700 before any agent code
runs), enumerate the parametrize list from *that* sealed copy, and add a
second, independent assertion in `test_sample_output` that reads the sealed
source, calls the agent's `render()` on it directly (in the same isolated,
privilege-dropped, import-audited subprocess already used for held-out
grading), and checks *that* output also matches the sealed expected bitmap.
Verified the exact exploit AVA described — a fake `solve.py` that writes an
always-raising broken `render.py` then copies the shipped `.ppm` files
straight to `/app/output/` — scores `0.0` through the real pipeline after
the fix (it scored `1.0` on the 5 sample tests before it).

**Reusable rule:** never grade only against a file path an agent's own code
controls the *contents but not necessarily the provenance* of. If a test
can be satisfied by a file that exists for a reason unrelated to the
function under test having actually run, tie the grading to a fresh,
independently-invoked call of that function.

---

## 6. Gate-by-gate log (final accepted run, `78ec3a3`)

| Gate | Verdict |
|---|---|
| `changes`, `ratelimit`, `cosine_similarity`, `similarity`, `validation`, `review` | pass |
| `pass2` | pass (this design's crux logic unchanged from the round before; only held-out breadth changed) |
| `deep_review`, `ava_review`, `tier1` | pass — third clean pass in a row |
| `qc_eval`, `qc_exec`, `qc_gate` | pass, zero findings — third clean pass in a row |
| `trials` (pass@5) | **pass — 1/5 solved** (2 idle-loop timeouts, 1 near-miss timeout, 1 genuine `h09`-class edge-case bug) |
| `gate` | pass → `accepted` label |

Earlier blocking history (all on the same repo/PR, different commits):
`ava_review` BLOCK on the sample copy-bypass (§5, fixed in `bb4ac1d`);
`pass2` blocked six separate pushes on crux-1/crux-1+2 being too easy
(§2); `pass2` blocked once more (`5ca38d6`) on a stochastic 2/2 reroll of
already-passing crux logic (§4); `trials` blocked twice at 3/5 before the
accepted round (§3). No `qc_gate` B1/B4/B5-style "ambiguous/undocumented
rule" finding was ever raised against crux 3, despite it being disclosed
with less prose than crux 1 originally had — the worked sample (isolated
from the other two cruxes by construction: `alpha=255`, `combine=NORMAL`)
was sufficient Pattern-D disambiguation on its own.

---

## 7. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| `pass@2` solved 2/2 on a Pattern-D crux, repeatedly, regardless of disclosure tuning | Check whether the withheld rule is the *only sensible* extension of something already disclosed. If so, pick a crux that changes what data gets read, not just which formula applies | Do not keep trimming samples or stripping prose on the same crux — measured three times here, no effect |
| `pass@5` came back 3/5 | Read *why* each failure happened before adding anything. If it's the same trap as last time, deepen that trap. If it's a different failure family (e.g. timeout vs. implementation bug), the fix has to match the new evidence | Do not mechanically re-apply the lever that worked last round without checking whether this round's failures even touched it |
| `pass@2` solved 2/2 right after a design that was working | Check whether the observed rate is plausible given your independently-estimated true solve rate before concluding anything regressed | Do not assume a single 2-trial sample proves a regression, and do not waste push budget re-pushing with no substantive change just to reroll |
| Sample-output tests only compare `/app/output/*.ppm` against a sealed bitmap | Add a second assertion that independently invokes the agent's function on a sealed source and checks *that* output too | Do not trust a file-comparison test that never confirms the function under test actually ran |
| An initial alpha/coverage array is a "should be obvious" constant | Verify the actual convention (0–1 fraction vs. 0–255 scale) against the rest of the codebase before trusting a scratch harness's output | Do not assume a constant is right because the code runs without error — a wrong-scale constant silently shrinks the very divergence you're trying to measure (caught here by hand-deriving expected algebra and finding a 35× discrepancy) |

---

## 8. Reusable checklist

1. Is the deciding rule the **only sensible way** to extend something the
   spec already fully discloses for a sibling construct? If so, it will be
   guessed by analogy no matter how you tune disclosure — pick a different
   *kind* of rule.
2. Does the new crux change **what data gets read**, not just **which
   already-agreed formula applies**?
3. Is the crux **real and named** (a genuine external convention), not
   invented — and disclosed only enough to survive `qc_gate`'s
   ambiguity check, with a worked sample doing the actual disambiguation?
4. Is each new worked sample **isolated** from the other cruxes (inert
   values for everything else) so it disambiguates exactly one thing?
5. When `pass@5` comes back too easy, did you read *why*, per trial, before
   deciding what to add? Timeout and implementation-bug failures need
   different fixes.
6. Before reacting to any single `pass@2` result, is it consistent with the
   per-trial solve rate you already have independent evidence for?
7. Do your sample-output tests tie grading to a **live, independently
   invoked call** of the function under test, not just a file comparison?
8. Every mutant (one per crux) fails **only** the fixtures that exercise
   its crux, and passes everything else — confirms cruxes are additive,
   not restatements of one another.
9. Oracle 1.0 / nop 0.0 after every change, recalibrated through the real
   `harbor` pipeline, not just a standalone script.
10. README / task.toml synced every push that touches design or verifier
    behavior; no AI attribution anywhere.

---

## 9. One-paragraph version for future me

A Pattern-D crux (evidence-forced disclosure via a worked sample) can still
be solved cleanly and repeatedly if the withheld rule is the *only
plausible* way to extend a formula the spec has already fully disclosed for
a sibling construct — group-alpha-applied-once and group-level `MUL`
combine both fell into this trap, solved 2/2 across five separate `pass@2`
rounds despite aggressive disclosure-stripping and sample-trimming, because
there was never a real second reading to rule out. The fix was not more
concealment; it was `GROUP KNOCKOUT`, a real, named PDF/Illustrator
convention (found via web research into real print/graphics gotchas) that
changes what data a group's own members read while painting rather than
which already-given formula applies to them — nothing in the existing spec
hints at an alternative, so there was nothing to guess by analogy. That got
`pass@2` to pass genuinely on the first attempt and QC to clear with zero
findings, three times running. Even then, `pass@5` landed at a stochastic
`3/5` boundary twice, for two *different* reasons each time (a genuine
implementation bug once, pure agent time-budget pacing twice) — the fix
that finally worked matched the actual observed failure (stacking all three
cruxes into deeply-nested fixtures to raise total task complexity) rather
than mechanically repeating the deepening that had worked the round before.
Accepted at `pass@5 = 1/5`, three clean QC passes, zero verifier defects
found across the task's entire life once the AVA copy-bypass (sample tests
must independently verify a live `render()` call, not just compare output
files) was fixed early on.
