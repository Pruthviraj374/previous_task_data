# dynamo/emulate-int8-accel — int8 quantized-inference requantization as a latent crux

| | |
|---|---|
| **Outcome** | **ACCEPTED** — every gate green, `accepted` label |
| **Repo** | `dynamo-602128a-hardware-embedded-and-low-level-systems`, branch `submission`, fork `charan-sr` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-602128a-hardware-embedded-and-low-level-systems/pull/1 |
| **Category / sub** | Hardware, Embedded, and Low-Level Systems / **GPU kernels and accelerators** (pre-seeded) — **first task in this subcategory in the corpus** |
| **Benchmarked model** | `task.toml` names Opus-4.8 / Terminus-2 (fixed dataset fields); reported as "Model A" on Daytona |
| **Final commit** | `3dd68c8` |
| **Headline** | **pass@5 = 2/5 solved, 3 good-valid fails, avg@5 = 0.400** — right on the acceptance bar. pass@2 0/2 twice (25m/15m). 2 pushes; everything passed first push except one `qc_gate` mutation hole. |

The most valuable things here: §3 (int8 requantization is a rich, integer-exact accelerator stump
source), §4 (the single `qc_gate` block and why the fix was a boundary fixture, not a redesign), and
§6 (run the FULL internal-mutant battery before push — QC found the one rounding branch I hadn't
enumerated).

---

## 1. What the task asks

A retired int8 inference accelerator ("TESSERA-Q") ran quantized **dense (fully-connected)** layers;
its runtime is gone, a per-layer archive survives. The agent writes `/app/emulate.py`, invoked
`python3 /app/emulate.py <layer_dir> <out_file>`, that reads a layer's `input.bin` (M×K int8),
`weights.bin` (N×K int8, symmetric), `bias.bin` (N int32 LE) and `params.json` (input/output
zero-points, per-channel int32 `multiplier` + int `shift`, `fused_activation`), and writes the M×N
int8 output tile row-major, byte-identical to the accelerator's output.

- **Agent sees:** `instruction.md`, `/app/data/ACCEL.md` (byte-layout format note), and one worked
  sample layer at `/app/data/sample/` **with** its `output.bin` (self-check).
- **Graded on:** the sample plus **13 held-out layers**, all-or-nothing, **exact integer** byte
  comparison. Categorical/integer grading → no tolerance class exists anywhere (`lumenp` §6 /
  `filer-audit` applied to numeric output).

## 2. The crux, and the invariants that keep it alive

The compute is standard integer-only quantized inference: int32 accumulation of
`(activation − input_zp) * weight` plus bias, then the per-channel fixed-point `multiplier`/`shift`
requantization used by **gemmlowp / TFLite reference int8 kernels** (`SaturatingRoundingDoublingHighMul`
→ `RoundingDivideByPOT`), then output zero-point, fused activation, and int8 narrowing. `ACCEL.md`
**names that standard as the locator and restates none of its rules** (`readout-builder` §3.3 /
`filer-audit` §2 — name the standard, stop). `allow_internet = true`, so it is derivable.

Two behaviours of that standard **never fire on the shipped sample**, so an emulator that reproduces
the sample byte-for-byte is still wrong on held-out layers and gets no signal that it is:

| Axis | Real rule (named-not-restated) | Natural mistake | Fires when |
|---|---|---|---|
| **A** | the per-channel `shift` is a signed exponent; **positive = left shift** (`MultiplyByQuantizedMultiplier` left-shifts the operand before the high-multiply) | implement only the right-shift the sample shows | a layer has a positive shift |
| **B** | a **fused activation** sets the output clamp bounds — a fused **RELU clamps the lower bound to the output zero-point**, not to the int8 minimum | clamp to the full int8 range `[−128,127]`, ignoring `fused_activation` | a layer fuses RELU and an output falls below the zero-point |

**Invariants (all machine-checked in the scratchpad generator before the first push):**
1. **The sample is bit-inert under each wrong reading** — 0 of 48 outputs change under the axis-A or
   axis-B mutant. Measured, not assumed.
2. **The machinery is pinned by the sample** — a truncating requant mutant changes 16 outputs, a
   zero-point-ignoring mutant changes 44. So an agent must get zero-points and gemmlowp rounding
   right *to match the sample at all* — which keeps those from being accidental hidden axes and
   keeps the sample fairly reproducible.
3. **Both axes break disjoint held-out sets** (`readout-builder` gold standard): axis A breaks the
   `posshift*`+`combo*` layers (naive-B inert there), axis B breaks the `relu*`+`combo*` layers
   (naive-A inert there). Different agents fail different axes.
4. **Every positive-shift held-out layer keeps `acc << shift` inside int32** (realistic scaling via a
   TFLite-style `QuantizeMultiplier`, checked per channel).
5. **No crux vocabulary in the agent-visible surface** — `ACCEL.md`/`instruction.md` never say
   "positive/left shift", "clamp at zero-point", or "gemmlowp edge case"; they name `shift` and
   `fused_activation` only as data fields.

The failures were exactly as designed: pass@5 3 good-valid fails on axes A and B (and the rounding
tie, §4), `difficulty_crux` PASS on every failing trial, all 5 `approach_validity` PASS —
*"legitimate agent implementation errors — incomplete consulting of the referenced external standard
— not task/verifier problems."* Agents built the correct skeleton and quit having matched the sample.

## 3. Why this domain is a strong accelerator stump source (transferable)

Int8 quantized-inference requantization is, for "GPU kernels and accelerators", what NFSv4 ACLs were
for access-control and OTLP was for metrics: a **real, published, integer-exact standard with subtle
conditional edges that a benign sample can be made to hide.** Specifically:

- **Integer-exact / categorical grading.** Every value is a byte; comparison is exact; there is no
  tolerance, no rounding band, no `difficulty_evidence` threshold-artifact risk. This alone removes a
  whole class of `deep_review` blocks.
- **Real conventions that are *noticed/derived*, not just recalled.** The signed-shift and
  fused-activation rules are in gemmlowp/TFLite, reachable online — but the natural implementation
  (write the requant you can see in the sample) skips them, and the sample never punishes the
  omission. This is `filer-audit`'s "knowing a rule ≠ implementing it" repeated: the graders said the
  agents' skeleton was correct and grounded in the named standard; they just didn't consult its edge
  behaviour because nothing forced them to.
- **Naming the exact standard did NOT make it too easy.** Unlike `decode-vibration-log` (same
  category), where *documenting a rule of a fictional device* got it transcribed, here the rules live
  in a **real external standard the sample doesn't exercise** — so naming gemmlowp/TFLite satisfied
  B5/discoverability *and* the axes still stumped the model, because the model doesn't fully
  reverse-engineer a named standard it thinks it already knows. Same shape as `request-preconditions`
  ("a conditional exception inside a rule the model is sure it knows").

The realistic scaling matters: I made each layer's effective multiplier map accumulators to a spread
of int8 outputs (a real quant layer is scaled that way), which is what makes the positive-shift axis
*robust* — an unscaled layer just rails at the ±127 clamps and both readings agree, giving 1-diff
fragile cases. Scale-aware fixtures gave 6-8 diffs per positive-shift layer.

## 4. The one gate that blocked — `qc_gate` C3, and the boundary-fixture fix

Everything passed first push — static, **rubric 31/31 first time** (difficulty/unambiguous/anti_cheat/
reviewable/taxonomy all PASS), duplicate UNIQUE, validation, pass2 (0/2, `pass2_suggestion` skipped),
ava_review, deep_review, qc_exec, tier1 — **except `qc_gate`**, a single C3 "Narrow / Hardcodable
Held-Out Coverage":

> Mutated spec-faithful emulate.py: removed the sign-dependent rounding threshold
> `thr=(mask>>1)+(1 if x<0 else 0)` → `thr=(mask>>1)`, violating the pinned gemmlowp RoundingDivideByPOT
> rounding. Verifier still gives reward=1.

The `RoundingDivideByPOT` rounds negatives half-toward-zero via a `+1` threshold bump for `x<0`. That
correction only diverges from the mutant when a **negative** value being right-shifted lands on the
**exact half** of its low bits — a case my random fixtures never hit. `QC-BASE` matched `HEAD`, so it
was current, not stale.

**Fix = three targeted rounding-tie held-out layers, not a redesign** (`motion-register` §"enumerate
every comparison, give each a fixture on its boundary"). I searched per channel for a bias offset that
makes `SRDHM(acc,mult)` land negative with low `exp` bits `== 2^(exp-1)` (the negative tie), alternating
neg/pos across channels. Confirmed the exact QC mutant now fails those layers.

**A trap the eval had already flagged and I had to clear.** The dynamo eval's non-blocking note said
`solution/emulate.py` and `tests/_reference.py` (two independent gemmlowp formulations — nudge/divide vs
64-bit slice) "can differ by ±1 only at a negative exact-half boundary" — *exactly the boundary the new
tie fixtures deliberately create.* So I re-verified byte-for-byte agreement of all three implementations
(solution / verifier reference / generator) on all 14 layers **including the ties** before pushing. They
agreed — the two formulations implement identical semantics at that boundary; the note was a possibility,
not a defect. **Lesson: if a gate warns a boundary *could* diverge, and you then add fixtures on that very
boundary, re-run the cross-check on those fixtures specifically.**

**Bonus difficulty.** The rounding-tie fixtures, added only for coverage, became a genuine second-order
trap: one pass@5 failing trial (`task__zNh8sDr`) failed on the **rounding-tie direction** — an additional
hidden edge the graders noted the agent exposed. Coverage fixtures turning into stumps is `cron-window-counts`
§4.1 repeated: closing a QC coverage hole can buy difficulty too.

## 5. Gate-by-gate log

| Push | Commit | Result |
|---|---|---|
| 1 | `41f7403` | static ✅ · **rubric ✅ 31/31 first time** · duplicate ✅ UNIQUE · validation ✅ · **pass2 ✅ 0/2** (suggestion skipped) · ava_review ✅ · deep_review ✅ · qc_exec ✅ · tier1 ✅ · **qc_gate ⛔ C3** (negative-tie rounding correction unpinned) → trials skipped |
| 2 | `3dd68c8` | added 3 rounding-tie held-out layers; README + `task.toml` verification synced. **All green**: pass2 0/2 (25m8s), ava/deep/qc_eval/qc_exec/**qc_gate ✅**, tier1 ✅, **trials ✅ pass@5 2/5, avg@5 0.400, 3 good-valid** → **`accepted`** |

Timings: pass2 15-25m, qc_eval ~16m, trials ~20m, whole run ≈ 1h. No infra flakes, no soundness
blocks, no ambiguity blocks.

## 6. What passed first time, and why (the upfront-calibration payoff)

Like `reduce-palaeomag` / `filer-audit`, almost everything cleared on push 1 because the corpus's
pre-push checks were done *before* submitting, not in response to a block:
- **Verifier soundness (ava_review/deep_review first-time PASS):** expected computed **in-process** by
  an independent reference, **never written to disk**; `/tests` chmod-sealed 0700; graded program run as
  **`nobody`** (setgroups/setgid/setuid); inputs staged into isolated world-readable copies; output read
  with **`O_NOFOLLOW`**; a naive mutant was run through the **real harbor sandbox** (0.0) before pushing.
- **No dead-branch QC holes I could foresee:** dropped the always-zero `weight_zero_point` from the
  schema and reference entirely (symmetric weights) so there was no unexercised subtraction for QC to
  mutate. Kept only reachable branches (the `SRDHM` `INT32_MIN` overflow case can't fire for `q>0`, so I
  omitted it rather than ship a dead branch).
- **Machinery pinned by the sample** so the two headline axes were the only latent things.

The one hole I missed was the *internal* rounding-correction branch — I mutated the **two headline axes**
and the top-level operations (zero-point, truncation, activation) locally, but not every sub-branch of
`RoundingDivideByPOT`. **Run the full internal-mutant battery** (every comparison and sign-dependent term,
including rounding-correction toggles), not just the design axes, and confirm each is killed by ≥1 fixture,
before the first push. Had I done that I'd have shipped the tie fixtures on push 1.

## 7. Reusable checklist

Design:
- [ ] For an accelerator/GPU-numerics task, prefer a **real published integer-exact standard** (int8
      quantized inference / gemmlowp-TFLite requantization; fixed-point DSP; tensor-core int8 GEMM) whose
      conditional edges a benign sample can hide. Integer/categorical grading kills the tolerance class.
- [ ] Name the standard as a **locator inside `/app`** (satisfies B5/discoverability); restate no rule.
- [ ] Two independent latent axes reached by **different questions**, breaking **disjoint** held-out sets;
      measure the disjointness with mutants, don't assume it.
- [ ] Make fixtures **realistically scaled** (map accumulators across the output range) so a latent axis
      produces many diffs, not 1 fragile clamp-edge diff.
- [ ] Pin all **machinery** with the sample so the agent must get it right to match — and so it stays fair
      and gives no self-check signal on the hidden axes.

Verifier / QC:
- [ ] Compute expected **in-process**; seal `/tests`; run the graded program as `nobody`; stage isolated
      input copies; read output `O_NOFOLLOW`. Run a naive mutant through the **real** verifier → 0.0.
- [ ] **Enumerate every comparison AND every sign-dependent term** in the reference (rounding corrections,
      nudge signs, clamp bounds) and give each a **boundary fixture**; run the full mutant battery and
      confirm each mutant is killed. QC will find the one you skip.
- [ ] Two structurally independent implementations agree byte-for-byte on **every** fixture, especially any
      boundary a gate warns *could* diverge — re-check on the fixtures that sit on that boundary.

Process:
- [ ] **Omit** the "You have N seconds…" line (confirmed again — `instruction_concision` PASS without it).
- [ ] `difficulty_explanation` states **synthetic provenance** + **real-world audience** (rubric PASS).
- [ ] `.dockerignore` in `environment/` from push 1; `.gitattributes` `* text=auto eol=lf` + `*.bin binary`
      to keep text LF and binaries intact on Windows; stage explicit paths, `jobs/` gitignored.
- [ ] README + `task.toml` explanation fields synced in the **same commit** as any fixture/verifier change
      (the tie-fixture push updated the held-out count 10→13 in both).

## 8. One-paragraph version for future me

First "GPU kernels and accelerators" task in the corpus, accepted at **pass@5 2/5, avg@5 0.400** in two
pushes. The design is the proven latent-crux recipe transplanted onto **int8 quantized-inference
requantization**: reconstruct a retired accelerator's exact int8 dense-layer outputs, name the
gemmlowp/TFLite integer arithmetic as the standard in `ACCEL.md` and restate none of it, and build the
shipped sample homogeneous exactly where that arithmetic bites — every channel's `shift` non-positive and
no fused activation — so two real, derivable behaviours never fire on it: a **positive shift is a left
shift**, and a **fused RELU clamps the output lower bound to the output zero-point** rather than to the
int8 minimum. Both are integer-exact, invisible on the sample, and break **disjoint** held-out sets, and
the machinery (zero-points, gemmlowp rounding, int8 narrowing) is pinned by the sample so the model must
get it right to self-validate — which it does, then ships wrong on the held-out edges. Naming the *real*
standard did not make it easy (unlike documenting a *fictional* device's rule, per decode-vibration-log):
the graders confirmed the agents built the correct skeleton grounded in the named standard and simply
didn't consult its edge behaviour, which nothing forced them to. Everything passed first push —
rubric 31/31, verifier soundness, pass2 0/2 — except one `qc_gate` C3: a mutation dropping the
sign-dependent rounding correction for negatives still scored 1, because no held-out layer landed a
negative requant value on the exact rounding tie; fixed with three targeted rounding-tie fixtures (not a
redesign), after re-verifying the two independent gemmlowp formulations still agree byte-for-byte on
exactly that boundary — the same boundary the dynamo eval had flagged as a possible ±1 divergence. The
tie fixtures then became a bonus trap that took down a fifth-trial agent on rounding-tie direction. Carry
forward: int8/gemmlowp requantization is a rich, integer-exact accelerator stump domain; realistic
per-channel scaling is what makes the positive-shift axis robust rather than a fragile clamp-edge; and run
the full internal-mutant battery (every sign-dependent rounding term, not just the headline axes) before
push, because QC enumerates them all.
