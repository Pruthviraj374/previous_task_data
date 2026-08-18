# dynamo/decode-vibration-log — a documented decode task is transcription; de-document or die

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 17 checks green, `accepted` label |
| **Repo** | `dynamo-3394c84-hardware-embedded-and-low-level-systems`, branch `submission`, fork `charan-sr` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-3394c84-hardware-embedded-and-low-level-systems/pull/1 |
| **Category / sub** | Hardware, Embedded, and Low-Level Systems / **DSP and signal hardware** (pre-seeded) — first task in this category in the corpus |
| **Benchmarked model** | `task.toml` names Opus-4.8 / Terminus-2 (fixed dataset fields); reported as "Model A" |
| **Final commit** | `667e532` |
| **Headline** | **pass@5 = 2/5 solved, 3 good-valid fails, avg@5 = 0.400 — right on the acceptance bar.** pass@2 0/2 (2 valid). 5 pushes + one close/reopen re-trigger. |

The single most valuable thing in this file is §3. This task took **two full "pass@2: 2/2 solved" rounds** before it stumped the model at all, and the reason is the central lesson: **a "decode this fully-documented binary format" task is a transcription exercise, and the benchmarked model is nearly perfect at transcription** — it reads the spec and implements every rule, including edge cases the sample never exercises. Latency/dormancy in the sample does *not* stop it. The only thing that produced failures was **de-documenting** the deciding rules so they had to be *inferred*, not *read*.

---

## 1. What the task asks

A retired vibration recorder left binary capture files ("VBR1") and no reader. The agent writes
`/app/decode.py`, invoked `python3 /app/decode.py <capture.bin> <out.csv>`, that decodes every
fixed-size record into `abs_tick,amplitude` rows. It is graded on the shipped sample plus seven
held-out captures. Agent-visible material: `instruction.md`, `/app/data/DEVICE.md` (format spec),
`/app/data/capture.bin` (sample), `/app/data/expected.csv` (the sample's correct decoding).

Format: 16-byte header (magic, codec, tick_hz, record_count) + 4-byte records (`tick` u16, `code`
u8, `status` u8). Output per record: `abs_tick` (counter ticks since the first record, first = 0)
and `amplitude` (the fully decoded signed sample). Integer-only pipeline → exact grading,
all-or-nothing.

Three intended crux axes, each dormant on the sample:
- **Rollover (time):** the 2-byte `tick` counter overflows at 2**16; the sample never crosses it,
  held-out captures span multiple wraps → `abs_tick` must accumulate `(tick-prev) & 0xFFFF`.
- **Companding profile (value shape):** the `codec` byte selects one of two custom companding
  laws that diverge ~99%; the sample is entirely profile 0.
- **Range exponent (value scale):** `status & 0xF` is a gain-range exponent `e`; amplitude is
  scaled by `2**e`; the sample is `e=0` throughout.

---

## 2. The design that finally worked — and why two earlier ones didn't

**The task was accepted almost entirely on ONE axis: rollover, de-documented.** The companding and
gain axes never produced a single trial failure — the model implemented both from the doc every
time. pass@5 landed at exactly 3/5 fails, all on rollover. This is `rebuild-readout-builder` §3.1
("one axis is a coin flip") confirmed once more: 2/5 is the coin flip barely clearing the bar, and
the automated deep-review *advisory* predicted the risk correctly ("counter-rollover on a
documented 2-byte field is an accessible concept… pass@5 ≥3/5 at real risk").

### Why the first two designs were solved 2/2

- **Design 1 (G.711 companding + fully-spelled rollover).** DEVICE.md said the counter "wraps
  modulo 2**16" and that spacing is "always less than one counter period," and named G.711.
  Result: the model **recalled** G.711 from training data and **transcribed** the wrap rule
  verbatim. Both agents solved in 3–8 minutes. (This is `rebuild-plate-rasterizer` §3.1: naming
  the standard/parameter = recall.)
- **Design 2 (custom companding + gain-ranging axis added + softened rollover).** Replaced G.711
  with a custom two-profile law, added the gain-range axis, and removed "wraps modulo 2**16."
  **Still 2/2 solved.** The pass@2 difficulty analysis was blunt: *"DEVICE.md hands the agent every
  decisive formula verbatim… nothing guards against the formulas themselves being given away."* A
  **custom** documented formula is transcribed just as easily as a recalled one — removing recall
  was necessary but nowhere near sufficient.

### What made design 3 finally stump it

**De-document the deciding rules; state the raw premise, never the consequence** (`fir-boundary-metrics`
§6.3 applied to a whole format):

- **Counter:** removed *every* wrap/width cue. DEVICE.md's prose no longer says "free-running,"
  "16-bit," "wraps," or "overflow" — only that a *2-byte* `tick` field holds a "sample-timing
  counter" that "advances at tick_hz." The 2-byte width lives only in the field-layout table. The
  agent must *infer* that a 2-byte counter overflows at 2**16 and that held-out captures can span
  it. Both pass@2 agents that solved earlier designs had explicitly cited the phrase
  "free-running 16-bit hardware counter" as their trigger to add `& 0xFFFF`; deleting that phrase
  is what moved the needle.
- **Companding profile 1:** removed its verbatim magnitude formula. DEVICE.md gives profile 0's
  formula and describes profile 1 *structurally* ("the segment shift is taken from the opposite
  end of the 0–7 range… largest when seg is 0, reaching 0 when seg is 7"), so the agent must
  **derive** `<< (7-seg)`. (This was endorsed by the pass@2 suggestion; in practice it did not
  measurably add failures — the model derives structural descriptions reliably.)

Net effect: pass@2 went 2/2-solved → 0/2-solved, and pass@5 = 2/5. **The rollover de-documentation
did essentially all the work.**

---

## 3. The transferable lesson: documented ≠ hard, and dormancy ≠ hard

This is the finding worth carrying to the next decode/parse task.

1. **A fully-documented decode/parse spec is a transcription task, and the model is excellent at
   transcription.** It will implement every documented rule, including branches the sample never
   exercises. Do not expect a documented rule to stump, however obscure — if it's written down, it
   gets implemented.

2. **"Documented but dormant in the sample" is NOT a reliable stump for a decode task.** I added
   two dormant-field axes (companding profile 1 never in the sample; gain exponent always 0 in the
   sample) expecting the `rebuild-plate-rasterizer` OPM effect ("agents hardcode a field that's
   constant in the sample"). It did **not** happen: both agents implemented both profiles and the
   gain scaling from the doc, every trial. **The OPM effect needs the *natural implementation to
   actively discard* the field** (plate-rasterizer's "widen Separation → CMYK" normalization threw
   the colour-space away *before* the rule could apply). A decoder that simply *reads a field and
   applies it* has no such discard step, so dormancy alone buys nothing.

3. **What *does* stump: a rule that must be INFERRED from a stated premise, where the sample makes
   the wrong (simpler) default look correct.** Rollover works because "the field is 2 bytes" (a
   premise the format forces) implies "it can overflow across a long capture" (a consequence the
   doc never states, and the sample never shows). The naive `tick - tick0` is the natural default
   and is exactly right on the sample. This is the `gnss-log-decode` structure (Opus 8/8) and the
   `fir-boundary-metrics` "state the range, not the wraparound consequence" sweet spot.

4. **De-documentation is a tightrope, and the fairness gates *will* let it through if the premise
   uniquely determines the answer.** `deep_review`'s oracle-derivation audit explicitly accepted
   `& 0xFFFF` as "follows from the documented 2-byte width" and `<< (7-seg)` as "uniquely pinned by
   the structural description." State the premise precisely enough that a sound solver can derive
   the rule, and omit only the consequence — then it reads as fair, not ambiguous.

5. **Your calibrate vocabulary guard must ban the FORMULAS, not just the consequence words.** My
   first guard banned "unwrap", "rollover", "modular delta" — but the *formulas themselves*
   (`((2*step+1) << seg)`, "free-running 16-bit") were sitting in DEVICE.md handing the answer over.
   Ban the giveaways at both levels.

6. **A single inferred axis is a coin flip; expect pass@5 ≈ 2/5 and an advisory.** Rollover alone
   put this at exactly the 3/5-fail bar. It cleared, but the deep-review advisory ("borderline-easy,
   pass@5 spend risk") was accurate. If a second *genuinely inferred* axis had been available it
   would have been safer — but on a per-record decode task the value axes are structurally
   transcribe-or-unfair (see §6), so there was no clean second inferred axis to add. **Know going
   in that a decode task may only support one such axis.**

---

## 4. QC / gate specifics worth reusing

- **QC C3 (mutation testing) on reserved/unused bits.** `qc_gate` mutated the reference
  `exponent = status & 0xF` → `exponent = status` (unmasked) and it still scored reward 1, because
  every fixture had a **zero upper status nibble** — nothing pinned the mask. Fix
  (`rebuild-motion-register` §6 "enumerate every distinction"): set the reserved upper nibble
  **nonzero on many records including the sample**, and state in the spec that only the low 4 bits
  are the exponent. Now a decoder that fails to mask fails on the sample itself. **Any reserved /
  always-zero field is a QC coverage hole — exercise it with nonzero values in fixtures.**
- **The first gate failure was `difficulty_explanation_quality`, not a crux problem.** The static
  rubric FAILed because `task.toml`'s `difficulty_explanation` omitted (1) **data provenance**
  (state the captures are synthetic/generated) and (2) **real-world audience** (who solves this and
  why). Cheap to pre-empt: always put one provenance sentence and one audience sentence in
  `difficulty_explanation`.
- **Infra 429 on `actions/checkout`.** `tier1` failed twice with `429 Too Many Requests` after 3
  download retries — pure infra, not content. `gh pr close 1` + `gh pr reopen 1` re-triggered onto
  a fresh runner and it passed (same fix as `hydrophone-pair-tdoa` §5's `Connect Timeout`). Always
  read the raw job log before reacting to a `tier1`/gate red — check for 429/timeout first.
- **Stale QC/tier1 stickies.** After the C3 fix, the visible `qc`/`tier1` stickies still carried
  `QC-BASE:<old sha>` from the pre-fix run (because the re-run had crashed on the 429). Confirm
  `QC-BASE`/`TIER1-BASE` against `git rev-parse HEAD` before believing a QC sticky
  (`rebuild-motion-register` §8).
- **deep_review advisory 2/3 (non-blocking, left as-is):** the *sample* case's `expected.csv` is
  agent-writable and could be echoed — neutralised by the 7 sealed held-out cases under
  all-or-nothing, so no reward advantage. And the per-subprocess `timeout` equalled the whole
  verifier budget. Both were advisory; accepted without change. Worth hardening pre-emptively next
  time (seal or drop the sample case; use a smaller per-call timeout).

---

## 5. Gate-by-gate log

| Push | Commit | Result |
|---|---|---|
| 1 | `4696097` | static `review` **FAIL** — `difficulty_explanation_quality` (missing provenance + audience). Everything else 30/31 PASS. |
| 2 | `bb75dd1` | static ✅ 31/31 · validation ✅ · **pass2 ⛔ 2/2 solved** — G.711 recalled + rollover spelled out verbatim. |
| 3 | `f5a0dc6` | custom companding + gain-range axis + softened rollover. **pass2 ⛔ 2/2 solved** — "DEVICE.md hands every formula verbatim." |
| 4 | `22b70ef` | **de-documented counter** (no "free-running/16-bit/wraps") + **structural profile 1**. **pass2 ✅ 0/2** · deep_review ✅ · ava_review ✅ · qc_eval/exec ✅ · tier1 ✅ · **qc_gate ⛔ C3** (unmasked status). |
| 5 | `667e532` | pin status mask (nonzero reserved nibble incl. sample). Local calibrate ✅ / oracle 1.0 / nop 0.0. **tier1 ⛔ infra 429** → `gh pr close`+`reopen` re-trigger → **all green**: pass2 0/2, deep/ava ✅, qc_eval/exec/gate ✅, tier1 ✅, **trials ✅ pass@5 2/5, avg@5 0.400, 3 good-valid** → **`accepted`**. |

pass@2 was measured 0/2 twice (design 3) and 2/2 twice (designs 1–2). The winning change between
"2/2 solved" and "0/2 solved" was purely **removing the wrap/formula wording from DEVICE.md** — no
logic, fixture, or verifier change. Concrete proof that difficulty here is set by *what the doc
discloses*, not by the design's mechanics.

---

## 6. Why the value axes couldn't be made hard (dead-end analysis)

Kept for the next decode task, so the same hours aren't re-spent. For a **fictional** format,
every decoding rule is in one of two states, and neither stumps:

- **Documented** → transcribed (the model implements it, dormant-in-sample or not — §3.2).
- **Undocumented** → underdetermined → **unfair** (`qc_gate` B5 / `deep_review` ambiguity): if the
  sample never shows profile 1 or a nonzero exponent and the doc doesn't define them, the agent
  *cannot* know they exist. There is no fair-and-hidden middle for a value the sample doesn't
  witness.

The escape hatches other tasks used don't apply cleanly to a per-record decode:
- **Real recalled-but-dropped convention** (`accrued-interest` UK gilts) needs a *real* convention
  the model knows and rationalises away — a fictional device has none.
- **Normalize-away property** (`plate-rasterizer` colour-space) needs the natural implementation to
  *discard* the field before the rule fires — a decoder that just reads-and-applies a field never
  discards it.
- **Inferred-from-premise** (rollover) works, but the value fields (`code`, `status`) have no
  premise that forces an un-stated consequence the sample hides — their meaning is either given or
  not.

**Practical implication:** if a future decode task needs two *robust* hard axes, don't rely on the
value fields. Either make the crux a **counter/time reconstruction** (rollover, epoch, non-uniform
sampling — all "infer the consequence of a stated width/rate"), or move to a **reduction/aggregate**
shape (`rebuild-readout-builder`, `hydrophone-pair-tdoa`) where the deciding rule is *how to
combine* records and the sample can fairly under-determine it. A pure "decode each record per a
written spec" task tops out near one inferred axis ≈ pass@5 2/5.

---

## 7. Reusable checklist

Design:
- [ ] Is the crux **inferred from a stated premise** (field width, rate) whose **consequence** the
      doc never states and the sample never shows? That is the only reliable stump for a decode
      task. Documented rules and dormant-documented fields do **not** stump this model.
- [ ] State the **premise precisely** (e.g. "the field is 2 bytes") so the answer is uniquely
      derivable (fair), and **omit only the consequence** (that it overflows and must be
      accumulated). `deep_review` accepts this; ambiguity gates do not fire if the premise pins it.
- [ ] Assume **one inferred axis ≈ pass@5 2/5** (coin flip). If you need margin, prefer a
      reduction/aggregate task shape over piling value-field axes that just get transcribed.
- [ ] Ban the **formulas and premise-giveaways** in your calibrate vocabulary check, not just the
      consequence words ("unwrap", "rollover").

Verifier / QC:
- [ ] Any **reserved / always-zero field** is a QC mutation hole — exercise it with **nonzero**
      values in fixtures **including the sample**, so an unmasked/over-broad read fails.
- [ ] Isolate held-out inputs, seal `/tests` (0700), run `decode.py` as `nobody`, symlink-guard the
      output. Consider sealing or dropping the **sample** ground-truth case too (advisory here).
- [ ] Plant ground truth from an independent generator; keep a third-implementation mutant table in
      `calibrate.py` that asserts each wrong reading fails its intended **disjoint** held-out set.

Process:
- [ ] `difficulty_explanation` must name **data provenance** (synthetic/generated) and **audience**,
      or static `review` FAILs it — pre-empt on push 1.
- [ ] A `tier1`/gate red with `429`/`Connect Timeout` in the raw log is **infra** — `gh pr close` +
      `gh pr reopen`, don't touch files. Check `QC-BASE`/`TIER1-BASE` vs `HEAD` before trusting a
      QC sticky.
- [ ] Calibrate locally (oracle 1.0, nop 0.0) + run the mutant table before every push; batch
      changes (each push re-rolls pass@2/pass@5 against a 6/day budget).

---

## 8. One-paragraph version for future me

First task in the "Hardware, Embedded, and Low-Level Systems / DSP and signal hardware" category,
accepted at pass@5 2/5 (3 good-valid fails, avg@5 0.400) — right on the bar. It took two
"pass@2: 2/2 solved" rounds to learn the one lesson: **a fully-documented binary-decode task is a
transcription exercise and Opus-4.8 is near-perfect at transcription** — it implements every
documented rule including sample-dormant branches, so neither a *custom* (non-recallable) companding
law nor *documented-but-dormant* fields (a second profile, a gain exponent) produced a single trial
failure. The `plate-rasterizer` "hardcode the constant field" effect did **not** reproduce, because
a decoder that merely reads-and-applies a field never *discards* it the way plate-rasterizer's
normalize-to-CMYK step did. What finally stumped it was **de-documenting** the counter: stating only
that `tick` is a *2-byte* field advancing at `tick_hz` and deleting every "free-running/16-bit/wraps"
cue, so the agent had to *infer* that a 2-byte counter overflows across a long capture (the
`gnss-log-decode` rollover crux; the `fir` "state the range, not the wraparound" sweet spot). That
single wording change — no logic, fixture, or verifier edit — flipped pass@2 from 2/2-solved to
0/2-solved. QC then caught a reserved-bit coverage hole (mutating `status & 0xF` → `status` passed
because every fixture had a zero upper nibble), fixed by exercising the reserved nibble nonzero in
the sample; and `tier1` twice died on a GitHub `429` infra flake, cleared by close/reopen. Carry
forward: for a fictional decode format, value fields are transcribe-or-unfair with no fair-hidden
middle, so build difficulty from **time/counter reconstruction inferred from a stated width/rate**,
budget for **one inferred axis ≈ 2/5**, and reach for a **reduction/aggregate** shape when you need
more margin.
