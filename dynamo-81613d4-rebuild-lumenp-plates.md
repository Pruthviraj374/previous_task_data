# dynamo-81613d4 — rebuild-lumenp-plates

| | |
|---|---|
| **Outcome** | **ACCEPTED** — every check green, `accepted` label |
| **Repo** | `dynamo-81613d4-games-puzzles-and-interactive-simulation` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-81613d4-games-puzzles-and-interactive-simulation/pull/1 |
| **Category / sub** | Games Puzzles and Interactive Simulation / Rendering graphics (pre-seeded) |
| **Benchmarked model** | reported as `Model A` / DeepSeek-V4-Pro (note: `task.toml` still names Opus-4.8 / Terminus-2, which are fixed dataset fields) |
| **Final commit** | `4872099` |
| **Headline** | **pass@5 = 1/5 solved, avg@5 = 0.200** (4 good valid fails). pass@2 = 1/2 |

This task replaced an earlier design in the same repo that was **solved 2/2 in seven
consecutive pass@2 rounds**. Read
[`dynamo-81613d4-rebuild-celstage-renderer.md`](dynamo-81613d4-rebuild-celstage-renderer.md)
for that failure in full; this file is about what finally worked and why.

---

## 1. What the task asks

A studio shipped a Game Boy game and archived its level-preview plates. The preview
tool wrote a `.frame` bundle per screen — a snapshot of what the hardware was told
to display — and the plate that came back is what the original Game Boy (DMG-01)
actually showed.

The agent gets `/app/FORMAT.md` (the container note) and 23 bundle/plate pairs under
`/app/samples/`. It writes `/app/render.py` exposing `render(source: bytes) -> bytes`
returning a 160×144 binary PGM. Graded on the 23 shipped plus **46 held-out**
bundles, **byte-exact**, all-or-nothing.

---

## 2. The crux, and the invariants that keep it alive

**The design rule that made this work, stated once:**

> **The container is invented and fully specified. The display behaviour is real and
> deliberately not restated.**

`FORMAT.md` is normative for every byte of the bundle — 2bpp planar tiles, palette
packing, two 32×32 maps, scroll/window placement, the object table's `+16`/`+8`
biases, attribute bits, 8×16 tile pairing, the output PGM. Its closing §8 says
plainly that it does **not** cover how the picture processor combined those pieces,
that this belongs to the DMG-01, and that it is in the public hardware references.
`instruction.md` says the same, and `allow_internet = true`.

Three real hardware rules decide the plate:

| # | Rule | Obvious wrong implementation |
|---|---|---|
| 1 | ≤10 objects per scanline; the scan keeps the first ten **in table order**, not by position | draw every object covering the line |
| 2 | Among those, **smaller X is in front**; table order only breaks a tie | walk the table, paint each over the last |
| 3 | Priority flag (attr bit 7) yields to background **colour index** 1–3, shows over index 0 — the index, *before* the palette maps it to a shade | object is always in front |

**The three invariants that must never break** — enforced in `generate_fixtures.py`,
which refuses to write a shipped bundle that violates one:

1. no shipped bundle puts **more than ten objects on a scanline** (one puts exactly
   ten, so the set visibly approaches the limit without crossing it);
2. **no two objects overlap** anywhere on screen in a shipped bundle;
3. **no priority-flagged object sits over background colour index ≠ 0** — the flag is
   *witnessed but inert*, so the agent parses the bit and watches it do nothing on all
   23 plates it can check.

Two more invariants keep the samples honest (each plate round-trips at the right
length; no plate is a single flat shade), and a separate **corpus-witness check**
requires the shipped set *as a whole* to exercise every container feature — both
scroll axes plus a wrap past 256, the window flush/inset/at `WX<7`, 8×16 objects,
both flips, both object palettes, non-identity palettes, transparency, objects
clipped at each edge, the priority flag itself. That check is what keeps the task out
of `qc_gate` B5: nothing outside the three hardware rules is left to guess.

---

## 3. Dead ends — with the graders' own wording

All from the CELSTAGE design in this same repo. **Seven pass@2 rounds, solved 2/2 in
every one that was not infra.**

| Approach | Verdict |
|---|---|
| Invented + disclosed architectural mechanism (six of them: multi-polygon winding, isolated-layer opacity, transform composition order, cut scoping, clip-by-coverage, sheet knockout) | Solved 2/2 six times. `deep_review`: *"the four architectural cruxes are not doing discriminating work."* |
| Softening / de-prescribing the spec prose | Two full rounds, still 2/2 |
| Undisclosed reverse-engineered function (a build-audit stamp) | Every configuration blocked by a *different* gate: withheld → agents search to the cap, *"Both agents were still executing active stamp-search scripts… **Neither was idle or stuck**"* → `low_timeout` invalid ×3; disclosed → 2/2 solved; graded on shipped only → `anti_cheat` FAIL; and `qc_gate` B5 throughout |
| **Unconditional** real convention (BMP row padding) | Solved 2/2. *Real is not sufficient.* |
| **Conditional but disclosed** real convention (an `origin bottom\|top` directive) | Solved 2/2. The analysis: both agents **"explicitly tested the `origin top` BMP case during development"**, and implemented all 8 mechanisms with **"no approach divergence."** *Conditional is not sufficient either, if it is disclosed.* |
| Tighten tolerance to catch a rounding mutant | Impossible and unfair: truncation differs by ≤1, and 2454 component values sat on exact rounding ties, so byte-exact would fail correct solvers |
| Large canvas → verifier timeout | Rejected on principle — `00-ATTEMPTER-SPEC.md:69`, difficulty from reasoning not wall-clock |

**The generalisation those seven rounds bought, and the reason this task exists:**

> **Disclosure and dismissability are mutually exclusive.** A rule the task *invents*
> must be written down, or `qc_gate` B5 blocks it as underdetermined — and a rule that
> is written down gets implemented, every time, however unusual or conditional its
> content. The traps that *do* work turn on a **real, external convention the
> instruction gestures at without enumerating**, so the model must **volunteer**
> knowledge while uncertain whether it is graded. A fictional system leaves nothing to
> volunteer.

---

## 4. What actually worked — and the surprise in it

Moving the deciding rules **outside the memo entirely**, to hardware whose behaviour
is real, published, and observable only in sub-cases the shipped set omits.

**But the failures were not what the design predicted, and this is the most
transferable finding in the file.**

`difficulty_crux` was **PASS on all five** pass@5 trials. Not one agent failed because
it did not know the DMG rules. Every trial produced a *structurally complete* renderer
that passed all 23 shipped and most held-out plates. The four failures stratified into
two root causes, in the grader's words:

- **Root cause A (1 trial)** — *"correctly stated in step-4 reasoning that 'objects
  with smaller X coordinate are drawn on top; if equal, earlier OAM index wins,' but
  the implementation never inserted [the sort] before the per-pixel loop."* Broke 8
  held-out plates.
- **Root cause B (3 trials)** — all failed on **h25 alone**, all with the identical
  symptom (16 pixels, first difference row 50 col 50). Mechanisms differed:
  one omitted `break` when the priority winner yields, so the loop fell through to a
  lower-priority sprite; one used a back-to-front painter's algorithm so the
  behind-sprite was already in the buffer when the front sprite correctly yielded;
  one was not statically identifiable. The grader: *"all three root-cause-B trials
  have structurally correct priority flag logic and simply mismanage control flow when
  the front sprite yields."*

So **the stump was not ignorance of a convention — it was the *interaction* of two
rules creating a control-flow trap.** Rule 2 (sort by X) and rule 3 (front sprite
yields to background) are each easy alone. Together they create a state the reflex
loop shape handles wrongly: when the front-most sprite yields to the background, you
must emit background and **stop**, not continue to the next sprite. Every agent knew
both rules. Four of five got the composition wrong.

**Corollary worth carrying:** pick cruxes that **compose**, and ship held-out fixtures
that exercise them *in combination*, not only individually.

---

## 5. Gate-by-gate log

Final run `31358628622` on `4872099` — **every gate passed, first time, on the
rebuild**:

| Gate | Verdict |
|---|---|
| `changes`, `ratelimit`, `cosine_similarity`, `similarity` | pass |
| `validation` | pass |
| `review` | pass |
| `pass2` | **pass — 1/2, 1 valid fail** (`Rerun Recommended: NO`) |
| `ava_review` | pass (first time this design was seen; the hardening it demanded on the old design was carried over intact) |
| `deep_review` | pass |
| `tier1`, `qc_eval`, `qc_exec`, `qc_gate` | pass |
| `trials` (pass@5) | **pass — `4 good valid + 0 soft-timeout fails of 5 (avg@5=0.200)`** |
| `gate` | pass → `accepted` |

For the predecessor design's failures (`ava_review` BLOCK on `/app/samples`,
`qc_gate` B5, `qc_gate` C3, `anti_cheat`, five pass@2 blocks) see the celstage file.

---

## 6. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| pass@2 "no valid fail — solved 2/2" on an invented-rule task | Move the deciding rule to a **real external convention the instruction names but does not enumerate**. Keep the invented part (container/format) fully specified | Do **not** add another invented mechanism. Six were added here across five rounds; every one was solved 2/2. Do not soften the prose — measured twice, no effect |
| You made the invented rule *conditional* and it still solved 2/2 | Accept that conditional-but-disclosed does not discriminate; the agents will test the conditional branch deliberately | Do not conclude the rule was "not strange enough" and make it stranger |
| You need a real convention but worry about `qc_gate` B5 | Name the system explicitly, say the memo does not cover it, say it is publicly documented, and leave `allow_internet = true`. Make the shipped set witness **every** container feature so only the external rules are unstated | Do not withhold a rule you invented yourself — that is the stamp trilemma, blocked by three different gates |
| Crux candidate is a real convention but *unconditional* | Reject it. BMP row padding was real and still solved 2/2, because every writer must always pad — no judgement to get wrong | Do not assume "real" is sufficient |
| Your task has float arithmetic near the grading threshold | Design the pipeline to be **integer table lookups end to end**, then grade byte-exact | Do not tighten a tolerance to catch a mutant — measured impossible and unfair on the predecessor |
| A mutation probe reports a clean sweep | Make every mutation **assert its pattern still matches** the source | Do not trust a probe after a refactor; one here silently stopped testing and reported a pass it never ran |

---

## 7. Bugs I introduced myself

- **A fixture that could not discriminate.** `h09` originally used two tiles that both
  paint colour 3, so the two sprite-ordering readings produced *identical* pixels. It
  looked like coverage and tested nothing. Caught by reading the calibration output —
  the OAM-order mutant was killed by only 3 of 46 plates. Fixed by using distinct solid
  colours, and by adding `h41`/`h42`. **Check that each mutant is caught by ≥3 fixtures;
  a suspiciously low count means a dud fixture, not a subtle mutant.**
- **A check harness that verified nothing.** My first reference self-check called
  `bundle(...)` and indexed the result as if it were a rendered plate — it was the
  6202-byte bundle. Every assertion was reading input bytes. Only visible because an
  assertion failed for the *wrong* reason.
- **An "off-by-one correction" that was wrong.** I changed a `task.toml` comment from
  "66 subprocess renders" to 67, reasoning 1 + 1 + 23 + 42. The probe invocation is
  **cached**, so both contract tests share one call and 66 was right. Count the *cache
  keys*, not the test functions.
- **A stale README shipped for three commits.** An audit found "54 calls" against a
  2400 s timeout when the real numbers were 66 and 2900, "six mechanisms" when the
  table had eight, and no test names at all. None of it was caught by any local check.

---

## 8. Process rules learned the hard way

- **Never push while a run is in flight** — it re-triggers everything and burns a
  rate-limited pass@2. Budgets: pass@2 **6/day**, difficulty suggestions **2/day**,
  reset midnight UTC.
- **Sticky PR comments update in place**, so `createdAt` stays at the original date.
  Filtering comments by date finds nothing; filter by **body content**.
- **A `pass2` failure skips everything downstream** (`tier1`, `qc_*`, `deep_review`,
  `ava_review`, `trials`), so a QC objection fixed while pass@2 is blocked never gets
  re-tested. Two rounds were spent on exactly that.
- **The pass@5 result is not posted as its own PR comment** — read it from the
  `trials` job log (`pass@5 gate OK: N good valid …`).
- Stage explicit paths, never `git add -A`; `task/jobs/` is gitignored local output.
- Root `README.md` is a strict pre-push gate — run the checklist in `readme-rule.md`,
  including the test-name diff, in the same commit.

---

## 9. Reusable checklist

1. Is the deciding rule **real, external, and publicly documented**? If you invented
   it, stop — it will be solved.
2. Does the instruction **name the system but not enumerate the rule**?
3. Does the rule fire **only in a sub-case** absent from every shipped sample?
4. Do your cruxes **compose**? Ship held-out fixtures exercising them *in combination*
   — that is where the real failures landed here.
5. Are the sample invariants **machine-enforced** in the generator, so a future edit
   cannot quietly leak the trap?
6. Does a **corpus-witness check** prove the shipped set exercises every feature that
   is *not* the crux?
7. Can grading be **byte-exact**? Make the pipeline integer-only and it can.
8. Every mutant: passes **all** shipped, caught by **≥3** held-out.
9. Mutation probe asserts each pattern still matches.
10. Second, structurally different implementation agrees byte-for-byte, plus a fuzz.
11. Independent decoder opens every output artifact.
12. Oracle 1.0 / nop 0.0, README current, no AI attribution.

---

## 10. One-paragraph version for future me

Seven pass@2 rounds proved that any rule this task *invents* gets implemented no
matter how strange or conditional, because an invented rule must be disclosed or
`qc_gate` blocks it as underdetermined — disclosure and dismissability are mutually
exclusive. The fix was to keep the invented container fully specified and move the
deciding rules **outside** it, to real Game Boy hardware behaviour that the memo names
as out of scope and the public references document: a ten-object-per-scanline limit
selected by table order, sprite priority by smaller X with table order only as a
tie-break, and a priority flag that reads the background *colour index* rather than
the palette-mapped shade — each invisible unless objects crowd a line, overlap, or a
flagged object sits over non-zero background, none of which any shipped bundle does.
That reached **pass@5 1/5, avg@5 0.200, accepted on the first run**. The surprise:
`difficulty_crux` passed on all five trials — nobody failed from not knowing the
hardware. Four of five failed on the **interaction** of two rules, mismanaging control
flow when the front sprite yields to the background, three of them on a single
held-out plate. Build cruxes that compose, and ship fixtures that combine them.
