# dynamo/hydrophone-pair-tdoa — accepted after 6 pushes, and why "the window bound is load-bearing" is the lesson

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all checks green, `accepted` label |
| **Repo** | `dynamo-6d2827f-scientific-computing-and-domain-science`, branch `submission`, fork `charan-sr` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-6d2827f-scientific-computing-and-domain-science/pull/1 |
| **Category / sub** | Scientific Computing and Domain Science / **Signal Processing** (pre-seeded) — first Signal Processing task in this corpus |
| **Benchmarked model** | `task.toml` names Opus-4.8 / Terminus-2 (fixed dataset fields) |
| **Final commit** | `05cebcf` |
| **Headline** | **pass@5 = 0/5 solved, avg@5 = 0.000, 4 good valid fails + 1 soft in-progress-timeout (didn't need it). pass@2 was 2/2 valid fails. qc_gate passed first time on every design revision.** |

Six pushes. Two of them were routine anti-cheat/verifier-soundness hardening (the kind every task needs), one was a pure instruction-wording trim that turned out not to be the real fix, and one was a genuine mid-flight redesign of the fixture geometry after `pass2` found a class of correct-but-different agent approach the original design didn't anticipate. The task was **not** abandoned or pivoted to a different domain at any point — the core two-axis crux survived unchanged from the first push to the last; only the *placement* of one of the two axes needed fixing.

---

## 1. What the task asks

A marine-acoustics group uses a fixed two-hydrophone array to track a range-calibration pinger emitting short tone-burst pulses. Reprocess a backlog of recorded pulse events to get the time-difference-of-arrival (TDOA) of each pulse's **direct acoustic path** between the two hydrophones.

- **Agent sees:** `instruction.md`, one event at `/app/data/events/example/` (`ch0.wav`, `ch1.wav`, `meta.json` with `sample_rate_hz`, `hydrophone_separation_m`, `sound_speed_mps`, `nominal_pulse_frequency_hz`, `pulse_duration_s`, `trigger_time_s`), and `expected_tdoa.json` for that one event as a self-check.
- **Agent produces:** `/app/estimate_tdoa.py`, invoked as `python3 /app/estimate_tdoa.py <event_dir> <output_path>`.
- **Graded on:** the shipped example plus **seven held-out events** (`tests/fixtures/events/` overlay), each independently re-run through the agent's own script; each event's expected value is recomputed at grading time from a second, independently-coded reference implementation — never a stored ground-truth number.
- Tolerance: 75 microseconds, calibrated from the two independent implementations' sub-microsecond agreement with a wide margin over legitimate implementation differences.

The reduction: for each channel, matched-filter the Hilbert envelope against a template of the disclosed pulse duration (envelope domain — no carrier-cycle periodicity); within the physically-derivable post-trigger search span, take the **earliest** significant detection above a robust noise threshold, not the loudest; subtract the two channels' arrival samples for a coarse TDOA; refine to sub-sample accuracy with a narrowband cross-correlation restricted to ±half a carrier cycle around the coarse estimate.

---

## 2. The crux, and why one axis needed a mid-flight fix

Two axes, both real acoustic-engineering conventions, both invisible in the one shipped example, both silent when wrong:

| Axis | Real convention | Fires when |
|---|---|---|
| **A. Carrier-cycle ambiguity** | A narrowband tone burst's cross-correlation is quasi-periodic (peaks spaced one carrier cycle apart); coarse detection must happen in the envelope domain, not the raw/bandpass-filtered narrowband signal, to avoid locking onto the wrong cycle. | The array baseline is wide enough that the physically valid delay range (`separation / sound_speed`) spans more than about half a carrier cycle. |
| **B. Reflection (earliest vs. loudest)** | The direct acoustic path always arrives before any reflection, regardless of which is louder; a detector must take the *earliest* significant arrival, not the tallest. | A reflected arrival is present and louder than the direct path. |

**Both axes are demonstrably real, external, and *noticed*, not recalled** — the deciding property is "does this baseline exceed half a cycle" and "is there a louder-but-later arrival," both structural properties of the *data*, not a lookup table. This is `experiment-analysis-frame`'s and `reduce-palaeomag-collections`' design principle applied to a new domain.

### The mid-flight bug: axis B was placed outside the window a careful agent would actually use

The first working design (pushes 1–3) placed the reflection 35–48 ms after the direct arrival — far enough to be a cleanly *separate* peak in the envelope/matched-filter domain (required for peak-based earliest-vs-loudest detection to even apply), but also far enough outside any *physically-justified* search window (`trigger_time ± separation/sound_speed ± small margin`) that a careful, well-reasoning agent who correctly bounded their search would simply **never encounter the reflection at all**. Being more careful was accidentally being rewarded with an easier task — backwards from the intended difficulty. `pass2` found this directly: an agent using a tight, physically-derived window plus bandpass filtering plus plain `argmax` passed all 8 events without any envelope-domain or earliest-peak logic.

**The fix:** move the combined-axis fixtures to a much wider baseline (70 m instead of 6 m) so the *physically necessary* search window (which any correct implementation must derive from the disclosed `separation`/`sound_speed` — there is no way to justify a narrower one) is itself wide enough that a reflection placed inside it — at a delay between the pulse duration (so it's still a separable peak) and the geometric bound — **cannot be excluded by any legitimate windowing choice, tight or loose.** This is the generalizable finding: when a crux depends on "does the agent's search span include X," don't rely on the agent choosing a wide span by *habit* — make the span **required by the disclosed geometry itself**, so carefulness and the crux stop being in tension.

---

## 3. Dead ends

None at the domain/mechanism level — unlike `hos-trip-scheduling`, this task never needed a full pivot. The one real redesign was fixing axis B's *placement*, not abandoning it. Two things were considered and rejected at the design stage:

| Rejected approach | Rejected because |
|---|---|
| Leading-edge (threshold-crossing) detection instead of earliest-peak-above-threshold | Empirically *worse*: a wide (25 ms) Hann-template matched-filter's rising edge is shallow, so the exact threshold-crossing sample is far less stable than the peak itself — introduced whole-cycle errors (~667 µs) even on the *original*, already-working fixtures when tested locally. Reverted before ever reaching a push. |
| A short pulse duration for axis-B-only fixtures (to let the reflection sit close in time) | Would have made axis A (which needs a *long* pulse for near-tied cycle sidelobes) inert on the same fixture; the two axes have a genuine physical tension (long pulse for A, close-in-time reflection for B) that the wide-baseline redesign resolves without touching pulse duration at all. |

---

## 4. What worked

### 4.1 Copy the *shape*, adapt the specifics, for a category with no prior task

This is the **first Signal Processing task** in the corpus — no direct precedent to copy from. The transferable design principle (noticed-not-recalled, structural property of the data, invisible on the one shown sample, real published/standard convention) came from `reduce-palaeomag-collections` (Statistical Modeling) and `hos-trip-scheduling` (Optimization); the specific mechanism (envelope-domain detection, earliest-vs-loudest) was derived from first principles of acoustic TDOA engineering (matched filtering, first-arrival vs. strongest-arrival conventions used in real sonar/GPS/UWB positioning), not copied from any existing task.

### 4.2 Pre-push mutation testing against your own algorithm caught real gaps before every push

Before the first push: three plausible-wrong implementations (naive full-band correlation, the same windowed, envelope-domain-but-loudest-not-earliest) were built and confirmed to fail by 600–15,000 µs on the fixtures designed to catch them, while two independently-formulated correct implementations agreed to sub-microsecond precision. This is why `qc_gate` passed **first time on every single design revision** across the whole PR — every fixture was already adversarially probed before it ever reached QC.

### 4.3 When a mutant defeats your fixtures, reconstruct it exactly and re-validate against it — don't just patch and hope

`pass2` reported *prose* about the agent's approach (bandpass filter, tight window, absolute-max peak). Rather than guessing at a fix, the exact approach was reconstructed as a new local mutant (`algo_bandpass_naive.py`) and run against the current fixtures — which immediately revealed the mutant *already* failed on the cycle-ambiguity-only fixtures (confirming axis A was never the problem) but passed cleanly on the reflection fixtures (isolating the real gap to axis B's placement). This turned a vague "make it harder" instinct into a precise, verifiable, one-variable fix.

### 4.4 A verifier that recomputes "truth" from an importable module, invoked as the agent's own program at verify time, has a structural exploit — twice

Two distinct exploits were found by automated review (not by internal testing) and both trace to the same root pattern — a Harbor task where the agent produces a *program* that the verifier re-invokes against held-out data (the `reduce-palaeomag-collections` shape):

1. **QC**: the verifier recomputed "expected" by re-reading the *same* input files the agent's script had just been invoked against — a script that mutated its own input (e.g. overwriting one channel with the other) would corrupt the value it was graded against. **Fix:** snapshot the input into two separate isolated copies per test, one for the agent's script, one for the reference recomputation, both taken before either runs.
2. **AVA**: since the agent's script runs as a subprocess *after* `tests/` is overlaid, a script could simply `import` the verifier's own reference module from `/tests` and echo its answer — zero real computation, `got == expected` exactly, every time. **Fix:** precompute every expected value during test *collection* (before any agent subprocess is ever spawned), then delete the reference module (and its bytecode cache) from disk.

**Generalizable rule for this task shape:** if your verifier's "second implementation" lives anywhere on disk that the agent's own re-invoked program could reach, it must be gone from disk before the first subprocess spawn — not just "not disclosed in the instruction." Both exploits were caught and fixed *before* they cost a real pass@5 cycle, but only because pre-push mutation testing didn't extend to "can the graded program read its own answer key" — a category of exploit worth adding to the standard pre-push checklist for any task with this program-re-invoked-at-verify-time shape.

### 4.5 An instruction-wording hint that pre-announces the crux costs you a valid pass@5 cycle, but confirm it's the *actual* bottleneck before trusting the fix

After the first `trials` run came back 3/5 solved (too easy), the instruction's clause "*can differ in hydrophone spacing and contain the realistic background noise and acoustic clutter*" was identified as pre-announcing both axes almost by name and trimmed. This was the *wrong* diagnosis in isolation — the very next `pass2` still found a passing approach that used none of the intended mechanism, proving the technique itself (envelope + earliest-peak) is recallable enough from general DSP training that wording alone wasn't the bottleneck; the real gap was the axis-B window-placement bug in §2. The wording trim was still worth keeping (harmless, plausibly marginal help), but treating it as *sufficient* without waiting for the next empirical result would have wasted a cycle believing the task was fixed when it wasn't.

---

## 5. Gate-by-gate log

### Push 1 — `45cc888` (initial submission)

All static checks, rubric review (31/31), duplicate check (UNIQUE), docker/oracle/nop validation passed. `ava_review`: **BLOCK** — `sound_verifier` finding: `test_outputs.py`'s held-out event list silently fell back to grading only the agent-visible example if `/tests/fixtures/events` was ever missing, instead of hard-failing. Routing footer said BLOCK despite the finding being printed under "Advisory."

### Push 2 — `bda63c3` (ava_review fix)

Added module-level assertions that the held-out overlay exists with ≥7 events before test collection, so any degradation is a hard failure, never a silent pass. `pass2`: **PASS, 2/2 valid fails.** `deep_review`: PASS. `ava_review`: **BLOCK again** — new `sound_verifier` finding, this time from **QC**: a wrong `estimate_tdoa.py` that force-overwrites `ch1.wav` with `ch0.wav`'s contents (so any TDOA computed from them is 0) passes every case, because the reference recomputation re-read the same files after the agent's script had already run.

### Push 3 — `935f91d` (qc_gate exploit fix)

Fixed by snapshotting each event's input into two isolated copies per test (§4.4.1). Verified the exact exploit QC demonstrated now fails end-to-end through harbor. `pass2`: PASS again (32m25s). `deep_review`, `ava_review`: **BLOCK again** — new `sound_verifier` finding, this time a genuinely different exploit: a script that `import`s `/tests/_reference.py` at verify time and echoes its answer passes trivially, since the agent's script runs as a subprocess after `tests/` is overlaid (§4.4.2).

### Push 4 — `50e9095` (reference-reuse fix)

Precomputed all expected values during test collection, then deleted the reference module and its bytecode cache from disk before any agent subprocess is spawned. Verified the exact import-and-echo exploit now fails. `deep_review`, `ava_review`, `qc_eval`, `qc_exec`, `qc_gate`, `tier1` **all passed clean** — first time reaching `trials`.

**`trials`: 3/5 solved (avg@5 = 0.600). Blocked — not hard enough** (need ≥3 total with ≥1 valid; got 2 valid fails). Both failures failed *precisely* on the intended crux events; `approach_validity` and `difficulty_crux` PASS 5/5; no rubric criterion failed anywhere. The three passing trials each independently derived the full golden method (Hilbert envelope → matched filter → earliest-peak → narrowband refine) — a real, standard-enough DSP technique that self-verifying models recall/derive reliably. `decisive_rule_disclosed` noted the rule was fairly derivable, but also flagged that `instruction.md` explicitly signposted both axes ("can differ in hydrophone spacing and contain... acoustic clutter").

### Push 5 — `bc6415d` (instruction hint trim)

Trimmed the signposting clause; no design/solution/verifier change (§4.5). `pass2` **failed this time** (different failure mode from before): 1 trial passed cleanly using a bandpass-filter + tight-window + absolute-max-peak approach that used no envelope/earliest-peak logic at all and still passed all 8 events; the other trial failed only due to an unrelated terminal-wedge tooling accident (`difficulty_crux: FAIL` — correctly flagged as not a real signal). **Blocked — 0 valid failures.**

### Push 6 — `05cebcf` (fixture-geometry redesign — the real fix)

Reconstructed the exact bandpass+tight-window+argmax approach locally (§4.3): confirmed it still failed correctly on the cycle-ambiguity-only fixtures (axis A was never broken) but passed on the reflection fixtures, because the reflection sat 35–48 ms outside any window a reasonable agent would use. Replaced the four `held_B`/`held_AB` fixtures with four `held_C` fixtures on a 70 m baseline (vs. 6 m), keeping the reflection delay between the pulse duration and the now much-larger geometric bound, so no legitimate window choice excludes it (§2). `held_A` (cycle-ambiguity alone) unchanged. Verified locally: primary/secondary agree to 0.00 µs on every new fixture; the reconstructed exploit now fails by ~28,000–38,000 µs end-to-end through harbor; both earlier exploits (§4.4) remain blocked; oracle=1.0, nop=0.0. Updated `task.toml`'s three explanation fields and the root README to describe the corrected design and explicitly name the bandpass-tight-window pitfall for reviewers.

One transient infra failure (`Connect Timeout Error` in the `cosine_similarity` job's GitHub API call, unrelated to task content) blocked the re-run; fixed with `gh pr close 1` + `gh pr reopen 1` to re-trigger the workflow, per the queue-wedge precedent in this playbook.

**Result: all gates green.** `pass2`: 2/2 valid fails. `deep_review`, `ava_review`, `qc_eval`, `qc_exec`, `qc_gate`, `tier1`: all PASS. **`trials`: 0/5 solved, avg@5 = 0.000** — 4 valid fails (all four producing trials independently converged on `np.argmax`/loudest-peak selection instead of earliest-peak, failing every `held_C` event by 8,000–30,000 µs against the 75 µs tolerance) + 1 soft in-progress-timeout that didn't affect the outcome. `gate`: PASS → **accepted**.

---

## 6. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| A crux depends on the agent's search window including some far-away signal feature | Place that feature *inside* the window any correct implementation is geometrically forced to use (derive the window bound from disclosed physics, then make the feature fall within it) | Do not just place the feature "far enough to be a separate peak" and hope agents use a wide window — a careful, well-reasoning agent's narrower window will exclude it, rewarding carefulness with an easier task |
| `pass2`/`trials` reports a passing agent's approach in prose | Reconstruct that exact approach as a local mutant and re-run it against your current fixtures before redesigning anything | Do not guess at what made it pass and patch blindly — the reconstruction told us axis A was fine and isolated the bug to axis B's placement in one script run |
| `ava_review`/`qc_gate` finds "truth recomputed from agent-writable/agent-readable inputs" on a program-re-invoked-at-verify-time task | Snapshot inputs into isolated copies before use; precompute all reference values during test collection and delete the reference module from disk before any agent subprocess spawns | Do not assume `tests/` being "overlaid only at verify time" alone protects a reference module from a script that's *itself invoked* during that same verify phase |
| A `trials` run comes back "too easy" and you suspect over-disclosure in `instruction.md` | Trim the hint, push, and treat the *next* empirical result as the real test of whether that was the actual bottleneck | Do not assume a plausible-sounding fix (wording trim) is sufficient without confirming it against a fresh `pass2`/`trials` result — ours wasn't |
| A gate fails with a generic infra error (`Connect Timeout`, similar) unrelated to any content in your diff | Check the raw job log for the specific error before touching any task file; if it's infra, `gh pr close` + `gh pr reopen` to re-trigger | Do not start redesigning task content in response to an infra flake |

---

## 7. Process rules

- **Reconstruct a passing agent's approach as a real local mutant before redesigning.** Prose descriptions of "what the agent did" are lossy; running the actual reconstructed algorithm against your fixtures tells you precisely which axis is broken and which is fine, turning a vague "make it harder" into a one-variable fix.
- **A crux that depends on window/scope inclusion must be backed by geometry the agent is forced to derive, not by hoping they choose a wide enough scope.**
- **On a "verifier recomputes truth via a second implementation, and the agent's own program is re-invoked at verify time" task shape, budget for at least two rounds of anti-cheat findings** (agent-writable input, importable reference module) — both are structural to the shape, not one-off bugs, and pre-push mutation testing should explicitly include "can the graded program read its own answer key," not just "does the algorithm work."
- **Don't trust a plausible fix until the next empirical result confirms it.** The instruction-hint trim looked like the obvious fix for "too easy" and wasn't; the fixture-geometry bug was the real one and only surfaced because the next `pass2` was watched carefully rather than assumed fixed.
- **A transient infra error in a job log (`Connect Timeout`, similar generic network errors) is not a task defect** — check the raw log before touching any file; `gh pr close`/`gh pr reopen` re-triggers the workflow without a wasted content push.
- **Never push while a check is in flight** (`gh pr checks 1 | grep -c pending` → 0 first) — held throughout across 6 pushes.
- **README.md and `task.toml`'s three explanation fields were updated in the same commit as every design/verifier change**, including the fixture-geometry redesign, with an explicit note when a change (e.g. the reference-collection fix) didn't require README wording changes.
- **`.dockerignore` added before the first push** (build context has `environment/data/`) — zero cycles lost to this, unlike several tasks earlier in the corpus.
- **Commit identity set from `gh api user` id at clone time** (`user.email = "<id>+<login>@users.noreply.github.com"`), matching the private-email workaround used across the corpus.

---

## 8. Reusable checklist

Design:
- [ ] Is the deciding rule **real, external, and published** (not invented)?
- [ ] Is it **noticed** (a structural property of the input) rather than **recalled** (a table/formula)?
- [ ] If the rule depends on the agent using a sufficiently wide search/scope, is that width **geometrically forced** by disclosed parameters, not just "probably" what a careful agent would choose?
- [ ] Are there **two independent axes**, and does at least one combined fixture require both simultaneously?
- [ ] Build ≥3 plausible-wrong implementations (including any "obvious professional preprocessing step," e.g. bandpass filtering) and confirm each fails by orders of magnitude on the fixtures meant to catch it, before the first push.

Verifier (program-re-invoked-at-verify-time shape specifically):
- [ ] Does the reference/expected-value computation depend on any file the agent's own re-invoked script could have mutated? → snapshot inputs into isolated copies before use, for both the agent's run and the reference recomputation.
- [ ] Does any file containing the reference algorithm or expected values remain on disk when the agent's script is spawned? → precompute everything during test collection and delete it first.
- [ ] Confirm the held-out overlay is asserted present/complete, not silently defaulted to the agent-visible example alone.

Before every push:
- [ ] `gh pr checks 1 | grep -c pending` → 0.
- [ ] Oracle 1.0, nop 0.0, re-run after any fixture or algorithm change.
- [ ] If a prior `pass2`/`trials` run reported a passing approach, **reconstruct it as a local mutant and confirm it now fails** before pushing the fix.
- [ ] README.md and `task.toml`'s explanation fields checked against the diff; update in the same commit or state explicitly why not needed.
- [ ] No AI attribution in any commit message or file.

---

## 9. One-paragraph version for future me

The first Signal Processing task in this corpus, accepted in six pushes with the best possible final result (pass@5 = 0/5, avg@5 = 0.000). The core two-axis crux (carrier-cycle ambiguity from a wide baseline; earliest-vs-loudest peak selection under reflection) never needed to be abandoned or pivoted — both are real, external, structurally-noticed acoustic-engineering conventions invisible on the one shown bench-calibration example. Two of the six pushes were routine anti-cheat hardening specific to the "agent produces a program the verifier re-invokes against held-out data at verify time" shape (truth recomputed from agent-writable input; an importable reference module reachable by the agent's own re-invoked script) — expect both exploit classes on any task with this shape, not just this one. The one substantive design bug — and the generalizable lesson worth carrying forward — was that the reflection axis was originally placed far enough outside any *physically justified* search window that a careful agent's narrower, better-reasoned window accidentally excluded it entirely; `pass2` caught this by producing a bandpass-filtered, tightly-windowed, argmax-based solution that passed every fixture without touching the intended mechanism. Reconstructing that exact approach as a local mutant (rather than guessing from the prose description) isolated the fix precisely: move the crux-triggering baseline wide enough that the geometrically-necessary search window is itself too wide to exclude the reflection, so carefulness and difficulty stop being in tension. An instruction-wording trim tried first (removing a clause that pre-announced both axes) was harmless but not sufficient on its own — confirmed only because the next `pass2` result was checked rather than assumed fixed.
