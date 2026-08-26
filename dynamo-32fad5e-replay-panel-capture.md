# dynamo/replay-panel-capture — recalled-vs-obscure, twice, then difficulty from state-management breadth

| | |
|---|---|
| **Outcome** | **ACCEPTED** — every gate green, `accepted` label |
| **Repo** | `dynamo-32fad5e-hardware-embedded-and-low-level-systems`, branch `submission`, fork `charan-sr` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-32fad5e-hardware-embedded-and-low-level-systems/pull/1 |
| **Category / sub** | Hardware, Embedded, and Low-Level Systems / **Embedded and firmware** (pre-seeded; second in this subcategory after [[dynamo-c086412-replay-flash-capture]]) |
| **Benchmarked model** | `task.toml` names Opus-4.8 / Terminus-2; pipeline reports "Model A" (a pass@2 trial ran `deepseek/deepseek-v4-pro`) |
| **Final commit** | `963f899` (7 task commits) |
| **Headline** | **pass@5 = 2/5 solved, 3 good-valid fails, avg@5 = 0.400.** Two full designs were measured TOO EASY first (HD44780 pass@2 2/2; SSD1306 pass@5 4/5) before difficulty came from **state-management breadth**, not from any single recalled behaviour. |

The one lesson worth the read: **§2 — a display controller's addressing is the model's headline knowledge, so "latent crux on a famous part's marquee behaviour" is recalled = solved. The escape was not a new crux family but a different *source* of difficulty: many independent subtle STATE-management edges under all-or-nothing, which are implementation bugs the model makes regardless of what it "knows."**

---

## 1. What the task ends as (accepted design)

Reconstruct the final GDDRAM (8 pages × 128 columns = 1024 bytes, page-major) of a **128×64
SSD1306-compatible OLED controller** by replaying a text bus capture (`<type> <byte_hex>`,
type 0=command / 1=data). Agent writes `/app/emulate.py <capture> <out>`; graded on the sample +
**28 held-out captures**, byte-exact, all-or-nothing, no tolerance class. `OLED.md` documents the
capture container + geometry and names the SSD1306 as the authority, restating none of its
programming model (one minimal scope note only — see §4). Same verifier/Docker/replay infra as
`replay-flash-capture`: expected images planted by the generator, sealed under `/tests`, run as
`nobody`, `O_NOFOLLOW`, neutral staged filename, immutable-input integrity pins on `/app/data`.

Six independent axes, each inert on the horizontal-full-frame sample:
- **3 addressing** — memory MODE (horizontal/vertical/page auto-advance), column/page WINDOW
  confinement, and PAGE-mode column/page addressing (nibble+page-select, column wraps at full
  width with the page fixed; plus the power-on-reset default = page, not horizontal).
- **3 state-management** — the pointer PERSISTS across a mode change; a new column-window command
  MOVES the pointer to the window start; a page-select leaves the column UNCHANGED.
Data bytes are **non-monotonic** so outputs can't be eyeballed.

---

## 2. The load-bearing finding: recalled = solved, TWICE, and how difficulty was finally sourced

Two complete designs were measured too easy before acceptance, both for the **same reason**:

- **v1 — HD44780 20×4 character LCD** (3 latent axes: non-contiguous DDRAM→row map, entry-mode
  decrement, CGRAM exclusion). Rubric 30/31, verifier sound, **pass@2 = 2/2 SOLVED.** Both agents
  reconstructed the *entire* HD44780 model — including the non-contiguous `0x00/0x40/0x14/0x54`
  row map — from training. **HD44780's weird addressing IS its famous identity**, so naming it
  hands the whole model to the weights. (Same shape as [[decode-vibration-log]],
  [[dynamo_saturated_crux_families]], [[dynamo_enumeration_defeats_evidence_inference]].)

- **v2 — SSD1306 OLED, addressing axes only** (mode/window/page). Cleared every soundness gate and
  **pass@2 passed** (flapping 1/2 ↔ 2/2, borderline), but **pass@5 = 4/5 SOLVED (avg 0.800).** The
  analysis was blunt: *"4/5 agents implemented the full SSD1306 model from training knowledge; did
  NOT fall into the naive linear-framebuffer trap."* The bet that SSD1306 addressing modes were
  "detail-level, not headline" (like [[dynamo-602128a-emulate-int8-accel]]'s shift-direction edge)
  was **wrong** — the addressing modes are recalled. It also flagged the captures as
  "monotonically sequential → predictable by inspection."

**Why the int8/flash escape did not transfer.** `emulate-int8-accel` (named gemmlowp) and
`replay-flash-capture` (named JEDEC 25-series) both stumped because the model's *first-recall*
mental model is the **simple/naive** one (plain matmul; flash = writable byte array), and the real
edge requires consulting detail it skips. For a **display controller** the model's first-recall
model is already the **correct weird** one — the addressing IS the famous part — so there is no gap
between naive and correct to exploit. **Filter: does the model's first-recall model match the WRONG
(naive) answer or the RIGHT one? Displays fail this test; flash/accelerators pass it.**

**The escape that worked.** The lone pass@5 v2 failure was not an addressing error at all — it was
a **state-management bug** (a column-window register shared across modes). That is the opening:
difficulty that does **not** depend on what the model knows about the part, but on whether it tracks
the device's pointer/register STATE correctly across a long, entangled sequence. So v3 kept the
SSD1306 framing but added **three independent state-management axes** (pointer persists across a
mode switch; window command moves the pointer to its start; page-select leaves the column
unchanged) — each a real, datasheet-implied rule the sample never stresses, each a different subtle
bug different implementations slip on, **under byte-exact all-or-nothing** (one wrong rule fails the
whole task). That plus non-monotonic data moved pass@5 from **4/5 → 2/5**. This is
[[dynamo-c086412-replay-flash-capture]]'s "build every fair inert axis you can, all-or-nothing,
read the value table afterwards" — breadth of independently-graded consequence, not a single deep
insight (the [[dynamo-093d3d6-target-abi-audit]] revised hypothesis, confirmed again).

---

## 3. Gate-by-gate log

| Commit | Design | Result |
|---|---|---|
| `ae60b36` | v1 HD44780 | static ✅ · rubric ⛔ `instruction_concision` — the "You have N seconds…" line |
| `e743827` | drop that line | rubric ✅ 30/31 · validation ✅ · **pass2 ⛔ 2/2 SOLVED (too easy)** |
| `c4654ce` | **redesign → SSD1306** (addressing axes) | rubric/similarity/validation ✅ · **pass2 ✅** · deep_review ✅ · ava/qc_eval/qc_exec/tier1 ✅ · **qc_gate ⛔** (page-mode wrap: coverage hole + B1 ambiguity) |
| `e32c854` | pin page-mode wrap + OLED.md scope note + advisory fixes | qc_gate ✅ · pass2 ✅ · deep_review ✅ · **tier1 ⛔ 3/4** (E2 immutable-input integrity un-attempted) |
| `1f60d33` | E2 integrity pins on `/app/data` | tier1 ✅ 4/4 · **pass2 ⛔ 2/2 SOLVED** (borderline re-roll) |
| `5ddfbbc` | trim over-disclosing scope note + POR-default + deeper held-out | pass2 ✅ · qc_gate ✅ · tier1 ✅ · **trials ⛔ pass@5 4/5 SOLVED (too easy)** |
| `963f899` | **+3 state-management axes + non-monotonic data, 28 held-out** | **everything ✅ · trials ✅ pass@5 2/5, avg@5 0.400, 3 good-valid → `accepted`** |

---

## 4. QC / gate specifics worth reusing

- **`instruction_concision` FAILs the "You have N seconds to complete this task…" line** — it is now
  prohibited TB3 boilerplate; the budget lives in `task.toml [agent].timeout_sec`. OMIT it. The old
  spec's `check-instruction-suffix` requirement is stale. (Confirmed again; see
  [[dynamo-602128a-emulate-int8-accel]] §7.)
- **qc_gate on the page-mode column wrap** was a *coupled* finding: a coverage hole (mutant wrapping
  at the window end vs. 127 was an *equivalent* mutant because no page-mode fixture set a non-default
  window) **and** a B1 ambiguity (two defensible readings, nothing agent-visible picks one). Fixed by
  (a) two `page-mode + non-default-window` held-out captures that make wrap-at-127 ≠ wrap-at-window,
  killing the mutant, and (b) ONE datasheet-accurate scope note in `OLED.md`. **Over-disclosing that
  note (naming that 0x21/0x22 configure H/V) made pass@2 go 2/2** — trim a disambiguation to the
  minimum that resolves the exact ambiguity, or it leaks a difficulty axis.
- **tier1 is a fix-addressal tracker**: it held at 3/4 until the diff *touched* E2 (immutable-input
  integrity), even though grading never trusts `/app/data`. Fix = pin every declared-immutable path
  (sample capture/image against their sealed `/tests` twins; `OLED.md` against a hardcoded SHA-256).
  Attempt every co-listed item in the same push. ([[dynamo-6204d9b-pairing-token-bitflip]] §6.)
- **A hardcoded fixture hash drifts** — the `OLED_SHA256` pin must be recomputed from the *image*
  bytes whenever `OLED.md` changes (compute via `docker run … sha256sum /app/data/OLED.md`).

---

## 5. Reusable checklist

Design:
- [ ] **Before betting a latent crux on a named real part, ask: is the naive first-recall model of
      this part the WRONG answer or the RIGHT one?** Flash/accelerator → naive is a simple byte
      array / plain matmul (wrong) → good. Display controller / famous part whose marquee feature IS
      the weird behaviour → naive is already correct → the crux is recalled → too easy.
- [ ] When a single-behaviour crux is recalled, **source difficulty from STATE-management breadth**:
      many independent, subtle, datasheet-implied pointer/register-sharing rules, each inert on the
      sample, under byte-exact all-or-nothing. Different implementations slip on different ones.
- [ ] Make the sample **inert on every axis** and the graded data **non-predictable** (non-monotonic),
      so passing the sample proves nothing and the agent can't eyeball the expected output.

Verifier / QC:
- [ ] Plant expected images in the generator; seal `/tests`; run as `nobody`; `O_NOFOLLOW`; neutral
      staged filename; pin declared-immutable inputs (twins + hash); perform the copy-cheat as a probe.
- [ ] Machine-enforce in the generator: sample inert under **every** naive reading; each axis caught
      by ≥2 held-out with a non-hairline effect; the QC mutant (if any) pinned by ≥1 fixture.
- [ ] A disambiguation added for a QC B-check must be the **minimum** that resolves it — over-stating
      it leaks a difficulty axis and re-opens "too easy."

Process:
- [ ] OMIT the "You have N seconds…" line. `difficulty_explanation` names synthetic provenance +
      real-world audience, and must describe **every** axis the fixtures exercise (or deep_review
      flags orphaned behaviour). README + `task.toml` synced in the same commit as any change.
- [ ] Recompute any hardcoded fixture hash from image bytes after editing the hashed file.
- [ ] pass@2 (2 trials) is high-variance on a borderline design (flaps 1/2 ↔ 2/2); a genuine
      **2/2-SOLVED is a "make it harder" signal**, not a re-roll (re-roll is only for
      in-progress-timeout). Read the breakdown before reacting.

---

## 6. One-paragraph version for future me

Second "Embedded and firmware" task, **accepted at pass@5 2/5 (avg 0.400, 3 good-valid)** after two
complete designs measured too easy for the SAME reason: a display controller's addressing is the
model's *headline* knowledge, so a latent crux on a famous part's marquee behaviour is recalled =
solved — HD44780 went 2/2 at pass@2 and SSD1306-addressing-only went 4/5 at pass@5, with graders
noting the agents "implemented the full part model from training knowledge." The
int8/flash escape (name a real standard, hide its edge) did NOT transfer, because for flash the
model's first-recall model is a naive byte array (wrong, so the edge bites) whereas for a display the
first-recall model is already the correct weird addressing (nothing to exploit). The fix was not a
new crux family but a different *source* of difficulty: the one pass@5 failure on the addressing-only
design was a STATE-management bug (a register shared across modes), so v3 added three independent,
datasheet-implied, sample-inert state rules — pointer persists across a mode change, a window command
moves the pointer to its start, a page-select leaves the column unchanged — under byte-exact
all-or-nothing with non-monotonic data, which are implementation bugs the model makes regardless of
what it knows, and pass@5 dropped from 4/5 to 2/5. Along the way: `instruction_concision` still FAILs
the "You have N seconds" line (omit it); qc_gate's page-mode-wrap block was a coupled coverage-hole +
B1-ambiguity fixed with witnessing fixtures plus a MINIMAL scope note (over-stating it flipped pass@2
back to 2/2); and tier1 held until the diff touched the E2 immutable-input pin even though grading
never trusts `/app/data`. Carry forward the filter for the next "emulate a real part" task: **does the
naive first-recall model of this part give the wrong answer? If not, the crux is recalled — source
difficulty from state-management breadth instead.**
