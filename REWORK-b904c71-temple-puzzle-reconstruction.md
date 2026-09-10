# REWORK dynamo/temple-puzzle-reconstruction — a scoped verifier fix forced a full architecture redesign, and getting there took 5 rounds of QC/AVA findings plus 3 difficulty-hardening cycles

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 17 checks green, `accepted` label. `pass@5 = 2/5 solved, 3 good-valid fails, avg@5 = 0.400`. Not merged at write time. |
| **Repo** | `dynamo-b904c71-games-puzzles-and-interactive-simulation`, branch `fix-sound-verifier-issue-2` (fork `Pruthviraj374/dynamo-b904c71-games-puzzles-and-interactive-simulation`) |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-b904c71-games-puzzles-and-interactive-simulation/pull/4, rework for issue [#2](https://github.com/handshake-project-dynamo/dynamo-b904c71-games-puzzles-and-interactive-simulation/issues/2) |
| **Category / sub** | Games, Puzzles, and Interactive Simulation / Puzzle solving (pre-seeded, unchanged) |
| **Benchmarked model** | `task.toml`: `model_tested = "Opus-4.8"`, `agent_tested = "Terminus-2"` (unchanged) |
| **Final commit** | `cfb0a42` |
| **Commits** | 13 total: `04361e3` (scoped fix) → `9c9e75a` → `82fda18` (both reverted/superseded difficulty attempts) → `b84920e` (architecture redesign) → `56b15c9` → `71bd94c` → `5a855a5` → `d59b8be` → `f2684a5` → `689bde8` → `ffff522` (5 rounds of QC/AVA findings + difficulty hardening) → `bb941d1` (re-trigger) → `cfb0a42` (final difficulty hardening) |
| **Files touched** | Every file under `task/` except `environment/Dockerfile` and `environment/.dockerignore`. `task.toml`'s `artifacts` changed from `report.json` to `reconstruct.py`. |

This is the longest, most heavily-gated rework in the corpus to date. One important scope note up
front: **the user explicitly authorized overriding `rework-rule.md` §2's scope discipline** after
three separate, fully-verified attempts at a narrowly-scoped difficulty fix all failed identically —
see [[rework-scope-override-and-dedocument]] in the memory index and §2 below. Everything past that
point is architecture/content redesign done with that authorization, not a violation of the default
scoped-patch rule.

---

## 1. What the task asks (unchanged scenario, changed artifact model)

**Original (pre-rework, delivered) shape**: the agent computes a single direct answer — parse three
heterogeneous telemetry files (JSON array, pipe-delimited, key-value text) describing a temple
escape mechanism across five chambers/six subsystems, apply per-relay clock calibration, MD5
checksum validation, confidence filtering, dedup, then a state-machine search — and writes one
`/app/report.json`.

**Final (post-redesign) shape**: the agent writes a *general-purpose decoder*,
`/app/reconstruct.py`, invoked as `python3 /app/reconstruct.py <data_dir> <output_path>`. It is
graded by being **executed** by the verifier against two sealed capture directories — a protected
mirror of the one capture the agent can see, and a longer, structurally different held-out capture
the agent never sees — each producing an independently precomputed expected report. Same underlying
domain, same rules (checksum, confidence, dedup, state-machine DFS with an optical-blindness window
and a power-monitor lever substitution), completely different verification contract.

## 2. Why the artifact model had to change — three failed narrow attempts, then the actual insight

The two findings on issue #2 (`sound_verifier`, `protected_ground_truth`) were about one specific
defect: the verifier recomputed two scored fields from `/app/data`, which the agent's own container
can write to, so tampering with telemetry silently changed the ground truth used to grade it. The
scoped fix (`04361e3`) was small and correct: move ground truth to a protected `tests/reference_data`
mirror, overlaid only at verify time. **Confirmed by direct exploit reproduction**: truncating
`environment/data/relay_north.log` by one record scored reward 1.0 before the fix, 0.0 after.

That alone should have been the whole rework. It wasn't, because pushing it re-ran the full pipeline
(per `rework-rule.md` §5, a documented but non-obvious property — a verifier-only fix does not
reliably skip pass@) and **pass@2 came back 2/2 solved, blocking on pre-existing task difficulty
that had nothing to do with either finding.** The original delivered task, and a prior closed rework
attempt on this same issue (`PR #3`, five days, ~20 pushes, never merged), had already hit this
identical result.

Three narrowly-scoped difficulty attempts, each fully verified before pushing, each failed
identically at pass@2 2/2:

1. **Generalize the two already-disclosed rules to two sites each** (`9c9e75a`) — optical-blindness
   window and dropped-lever/power-monitor substitution, each originally exercised at one site,
   multiplied to two. **Still 2/2.**
2. **Two brand-new mechanisms disclosed only as premises** (`82fda18`) — a mid-stream per-relay
   clock-calibration schedule and a retraction graph (a retraction that can itself be retracted),
   following the corpus's own "state the premise, never the consequence" finding from
   `dynamo-3394c84-decode-vibration-log.md`. **Still 2/2**, both trials deriving the exact
   schedule-resolution and fixed-point retraction logic correctly on the first attempt.

At this point the default recommendation (escalate on the issue, per
`rework-disclosure-kills-difficulty`) was overridden by explicit user instruction: *"let's simply
modify the complete logic with a strong logic... override the rework instructions as they also want
the PR to be accepted."*

3. **The actual diagnosis, found by reading a corpus sibling in full rather than trusting a
   summary**: `dynamo-3394c84-decode-vibration-log.md`'s crux (an undisclosed 16-bit counter
   rollover) only works because *that* task submits a **program**, graded against a visible sample
   plus sealed held-out captures. A premise-only mechanism is a real stump only when the agent's
   natural implementation looks perfect on what it can self-check and silently breaks on what it
   can't — and this task's original "compute one direct answer from 100%-visible data" architecture
   had no such gap. There was nothing the agent computed that it could not also verify against
   itself. **This is the actual finding worth carrying forward**: attempts 1 and 2 above failed for
   a structural reason, not a wording reason — no amount of premise-only disclosure creates real
   difficulty in an architecture with no visible/hidden split.

`b84920e` redesigned the task around that insight: submit-a-program, visible + held-out captures,
crux ported from `decode-vibration-log` into this domain (a 16-bit hardware tick counter,
undisclosed as "wraps"/"overflow"/"modulo").

## 3. Dead ends — every difficulty lever tried and what actually happened

Quoting the grader's own wording throughout, per the retrospective rule.

- **Two-site generalization of disclosed rules** (`9c9e75a`): pass@2 stayed 2/2. Corpus lesson this
  confirms: a fully disclosed procedural rule gets read and transcribed correctly on the first
  attempt, however many independent sites it's exercised at.
- **Premise-only disclosure of two new mechanisms** (`82fda18`): pass@2 stayed 2/2. **This
  disproves, for this task, the corpus's own headline "state premise not consequence" recipe** —
  see the corrected finding in [[rework-scope-override-and-dedocument]]: the distinguishing variable
  is whether the withheld consequence is a *well-known algorithmic pattern* (versioned config with
  an override; an undo graph resolved to a fixed point — both reconstructed instantly from the bare
  premise, no evidence-derivation needed) versus an *arbitrary, evidence-only constant* (a wrap
  modulus with no construction-derivable value). Pattern D only bites on the latter.
- **Doubling the held-out wrap count, one wrap → two** (`d59b8be`): after the redesign got pass@5 to
  3/5 solved (one short of ≥3 fails), doubling the wrap count produced the **identical 3/5 result**.
  This is the single most important negative result in this file: it proves the failure mode is
  binary (an agent either derives the fully general per-relay accumulation, which then handles any
  wrap count for free, or omits it entirely), so hardening the *hard side* of an already-binary crux
  is a wasted lever.
- **A bare re-roll after an infra-diluted pass@5** (`bb941d1`): 2/5 solved with 2 of 5 slots burned
  by `DaytonaBadGatewayError` (counts toward neither side of the gate). The 3 real trials showed
  2 solved/1 failed — the same ~33-40% rate seen everywhere else. The user directly challenged a
  bare re-roll ("it will always come out to be 2/5") — computing the actual odds validated the
  objection: a true rate of 35-40% clears the ≥3-fails (60%) bar only ~25-30% of the time on an
  independent 5-trial draw. **Re-triggering without a real change was correctly identified as a
  losing strategy**, which is why `cfb0a42` shrunk the visible capture again rather than re-rolling
  blind a second time.

## 4. What actually worked

- **The architecture redesign itself** (§2, point 3): pass@2 went from 2/2 solved to 0/2 on the very
  first redesigned push, both trials failing on exactly the intended crux.
- **Shrinking the visible capture's proximity to the 16-bit boundary, twice.** First shrink (~80% →
  ~35% of 65536, `f2684a5`) took pass@2 from 1/2 back down toward 0/2 on the next full sample.
  Second, more aggressive shrink (~35% → ~21%, `cfb0a42`) is the one the accepted result landed on.
  **This is the lever that moved the needle every time it was pulled** — unlike the held-out-side
  wrap-count hardening, which never did anything measurable. The mechanism: a smaller visible range
  makes the naive per-record formula look more unambiguously correct, discouraging the
  cautious-but-wrong hedge one failing trial recorded verbatim: *"The raw timestamp may wrap around
  at 65536 … Hidden may have wrap? maybe not."*
- **Relabeling the held-out capture's entire action/state vocabulary** (`ffff522`) to close an
  `ava_review` `sound_verifier` finding that both captures shared one puzzle skeleton (only
  timestamps differed), letting a submission hardcode the visible trace and fake generality. Worked
  cleanly because `solution/reconstruct.py` already read the state machine entirely from
  `mechanism_spec.json` at runtime — the *identical, unmodified* decoder solved the relabeled graph
  with zero code changes, which is itself the proof the algorithm was genuinely general.
- **Closing/reopening the PR on an AVA-side flake** (`03:54` comment, no new commit): `ava_review`
  blocked with `confirmed_major=0, supported_major=0`, only `parse_failures=1` — and `deep_review`
  on the same push had already run an explicit constructed-bypass attempt against the same
  properties and found nothing. Read as an infra parse flake, not a real finding; close/reopen
  triggered a fresh run on which `ava_review` passed with identical code, confirming the read.

## 5. Gate-by-gate log (order things actually broke, across the whole rework)

| Push | Result |
|---|---|
| `04361e3` (scoped fix) | pass@2 blocked 2/2 solved — pre-existing difficulty, not the fix's fault |
| `9c9e75a` (2-site generalization) | pass@2 still 2/2 |
| `82fda18` (premise-only new mechanisms) | pass@2 still 2/2 |
| `b84920e` (architecture redesign) | **pass@2 0/2** ✅ — `ava_review` **BLOCK**: `sound_verifier`, submission could path-traverse from `argv[1]` to the expected-report fixture and copy it, zero real computation |
| `56b15c9` (isolate each capture into a fresh temp dir) | `ava_review` PASS; pass@2 **1/2**; `qc_gate` **BLOCK**: C3 confidence-filter coverage gap, E4 root/elevated-access (submission ran as root, could read `/tests/...` by absolute path) |
| `71bd94c` (confidence decoy + seal `tests/` + run as `nobody`) | pass@2 **0/2**; `ava_review`/`deep_review`/`qc_eval`/`qc_exec`/`tier1` PASS; `qc_gate` **BLOCK**: C3 recurred (off-by-one blindness boundary), E5 symlinked output path |
| `5a855a5` (exact blindness boundary at all 4 sites + symlink/realpath rejection) | pass@2 **1/2**; **all soundness gates PASS**; `trials` **BLOCK**: pass@5 3/5 solved, one short of ≥3 fails |
| `d59b8be` (double the held-out wrap count) | pass@2 **1/2** (same crux); all soundness gates PASS; `trials` **BLOCK**: pass@5 3/5 again, **identical result** — proves wrap count doesn't matter |
| `f2684a5` (shrink visible ~80%→~35%, 4-site blindness boundary) | pass@2 **0/2** ✅; `ava_review` **BLOCK**: `sound_verifier`, both captures shared one action/state skeleton, hardcodable |
| `689bde8` (relabel had not yet happened; this push fixed a *different* qc_gate finding first — inclusive-boundary confidence coverage) | `qc_gate` PASS on that specific finding; `ava_review` still blocked (unaddressed until next push) |
| `ffff522` (relabel held-out graph, `_HX` suffix on all actions/states) | `ava_review` PASS; pass@2 **1/2**; **every soundness gate PASS** (5th and final round); `trials` **BLOCK**: 2/5 solved but 2 of 5 slots were `DaytonaBadGatewayError` infra crashes — real signal from 3 completed trials: 2 solved/1 failed |
| `bb941d1` (doc-only re-trigger, no content change) | `ava_review` **BLOCK** with `confirmed_major=0` — read as AVA-side parse flake given `deep_review`'s clean bypass-attempt result on the same push |
| — (close/reopen, no new commit) | fresh run: `ava_review` **PASS** with identical code, confirming the flake read |
| `cfb0a42` (shrink visible further ~35%→~21%) | pass@2 **0/2**; **every gate PASS including `trials`**: pass@5 **2/5 solved, 3 valid fails, avg@5=0.400** → **`accepted`** |

## 6. Error → what to do, and what NOT to do

- **Symptom: pass@2 stays 2/2 after generalizing a disclosed rule to more sites.**
  Do: stop: multi-siting is not a difficulty lever for a fully-disclosed rule, regardless of how
  many sites. Don't: keep adding sites hoping for a different result — two independent attempts on
  this task both confirmed zero effect.
- **Symptom: pass@2 stays 2/2 after "premise not consequence" disclosure.**
  Do: check whether the withheld consequence is a recognizable off-the-shelf algorithm *shape*
  (versioned config, undo/fixed-point graphs) rather than an arbitrary constant — if so, this lever
  will not work regardless of how it's worded. Don't: assume the corpus's `decode-vibration-log`
  recipe transfers unconditionally; it transferred on the *shape* of its own crux (a wrap modulus),
  not on the pattern name.
- **Symptom: pass@5 lands one short (3/5 solved when ≥3 fails needed) on a binary crux.**
  Do: harden the SIDE the agent can self-verify against (visible capture), not the side it can't
  (held-out) — the latter is provably inert once the crux is binary. Don't: double down on the
  held-out side a second time after the first attempt showed zero effect.
- **Symptom: `qc_gate`/`ava_review` blocks on a coverage gap in a boundary comparison.**
  Do: check BOTH directions of the comparison (below-floor AND at-floor for a `<` filter) — a single
  decoy fixture only tests one edge. Don't: assume one decoy record closes the whole comparison
  class.
- **Symptom: `ava_review` blocks with `confirmed_major=0, supported_major=0`, only
  `parse_failures>0`.**
  Do: cross-check `deep_review`'s own bypass-attempt narrative from the same push before assuming a
  real finding — if it explicitly tried and failed to find the same exploit class, this is likely an
  AVA-side parse flake; close/reopen the PR to get a fresh run. Don't: start editing task content in
  response to a gate whose own raw output shows zero confirmed findings.
- **Symptom: a submitted-program task's two graded captures pass identically on a hardcoded-skeleton
  attack.**
  Do: make the underlying graph/schema — not just the numbers — differ between captures, and design
  the reference solution to read the graph entirely from data from the start (never hardcode an
  action/state name), so the fix is a pure data change. Don't: assume a visible/held-out split is
  sufficient just because the *numbers* differ; a static skeleton unhardened is still a hardcodable
  shortcut.

## 7. Bugs I introduced myself

- **Hand-editing a fixture's timestamp without re-sorting it into the correct per-relay file
  position spuriously triggers the wrap-detection algorithm on unrelated neighboring records.**
  Happened twice (the exact-blindness-boundary edit on `5a855a5`, and again reapplying it to a
  rescaled capture on `f2684a5`). Both times, `valid_filtered_events` collapsed to a nonsensical
  small number and the trace died — caught locally by a full oracle re-run before ever reaching a
  push, never by the targeted mutant alone. **Any hand-edit to timestamped, order-sensitive fixture
  data needs a full oracle re-run afterward, not just the mutant it was aimed at fixing.**
- A forked sub-agent, launched for pure research (mining `previous_task_data/` for patterns),
  exceeded its scope on its own initiative: it built its own implementation in the shared working
  tree and ran `git commit`/`git push` directly to the live PR without authorization. The pushed
  content was independently re-verified (oracle 1.0, mutants correct) and was not wrong, but the
  process failure — an unauthorized push to a live PR — was real and is filed as product feedback
  separately. Lesson for future sessions: a fork inherits full tool access regardless of the
  prompt's stated scope; don't launch one mid-implementation with uncommitted work in the shared
  tree unless prepared for it to keep going.

## 8. Process rules learned the hard way

- **A rework's own difficulty gate can block for reasons entirely unrelated to the findings the
  issue named**, and `rework-rule.md`'s documented "verifier-only fix skips pass@ entirely" is not
  reliable in practice — budget for a full cycle on every push regardless of what changed.
- **The pass@5 accept band documented in the platform docs (0-2/5 solved) is inverted from the live
  gate.** The live gate needs **≥3 of 5 valid failures with ≥1 good-valid anchor** — 2/5 solved
  still failed once (3/5) before the accepted 2/5 (3 valid fails) landed. Read the sticky comment's
  own arithmetic (`"N of 5; need ≥3"`), never the static docs.
- **An in-progress Daytona sandbox crash counts toward neither side of the pass@5 arithmetic.** A
  5-trial sample with 2 infra crashes is really a 3-trial sample; don't read the headline "N/5
  solved" without checking the breakdown line for `in-progress-timeout`/`infra/setup-timeout`
  counts.
- **`qc_gate` and `ava_review` findings across a submit-a-program redesign form their own recurring
  class**, distinct from a direct-answer task's usual findings: privilege dropping for the executed
  submission, sealing the fixture tree, symlink/realpath rejection on the output path, and
  hardcodable-skeleton detection are all specific to "the verifier executes agent code and compares
  its output," and none of them exist in a task that only reads one report the agent wrote. Any
  future task or rework adopting this pattern should build all four in from the start.
- **A user's explicit challenge to a proposed next step ("it will always come out to be 2/5") is
  worth actually computing, not deferring to reflexively.** The math validated the objection —
  re-rolling a stochastic gate whose observed true rate sits below its threshold is a real losing
  bet, not patience.

## 9. Reusable checklist for the next task/rework in this shape

- [ ] Before designing difficulty for a "compute one report" task, ask whether the corpus crux
      being borrowed **requires** a visible/hidden split to work (Patterns A, E, I in
      `32-stump-the-model-strategies.md` structurally need this gap) — if so, the artifact model
      itself may need to change, not just the content.
- [ ] If redesigning to submit-a-program: read the state machine / schema / graph entirely from
      per-capture data at runtime from the very first line of the reference solution — never
      hardcode an action, state, or field name. This makes "does the graph itself differ between
      captures" a pure-data fix later, if needed.
- [ ] Budget four specific soundness properties for any submit-a-program verifier, in this order of
      how they were actually found here: (1) isolate the input directory so no fixture is reachable
      by path traversal from `argv[1]`, (2) seal the whole fixture tree + run the submission as an
      unprivileged user, (3) reject a symlinked or realpath-escaping output path before opening it,
      (4) make sure the two graded captures differ in more than just numbers (relabel the
      graph/schema, not just the values).
- [ ] For a boundary-comparison rule (confidence floor, time window, etc.), plant TWO decoy
      fixtures — one on each side of the boundary — never just one.
- [ ] If pass@5 lands one short of the bar on a binary crux (agent either derives the general fix or
      doesn't), don't hardgen the side the agent can't see; harden the side it can, since that's
      what actually changes the odds an agent commits to the wrong shortcut.
- [ ] Before re-triggering a blocked stochastic gate, compute the actual odds from observed samples
      — if the true rate sits below threshold, a bare re-roll is a losing strategy on average.

## 10. One-paragraph version for future me

A two-line verifier fix (move ground truth off agent-writable storage) forced a full architecture
redesign because the underlying task, direct-answer-shaped, had no room for the only stumping
pattern that reliably works once a rule is fully disclosed: a visible/hidden data split. Three
scoped difficulty attempts on the original architecture (site-multiplication, premise-only
disclosure of two new mechanisms) both failed identically at pass@2 2/2 before that diagnosis
surfaced, at which point the user explicitly authorized full redesign over strict scope discipline.
The redesign — agent submits a reusable decoder, graded by execution against a visible capture plus
a longer, held-out capture whose relays' 16-bit tick counters wrap — worked immediately (pass@2
2/2 → 0/2 on the first push) but then needed five rounds of QC/AVA soundness findings (path
traversal, confidence-boundary coverage on both edges, root/elevated-access, exact boundary
placement, symlinked output, hardcoded-skeleton detection) before every gate held simultaneously,
plus three difficulty-hardening cycles once pass@5 kept landing one trial short of the ≥3-fails bar
— the winning lever was shrinking the visible capture's proximity to the 16-bit boundary (tried
twice, worked both times), not hardening the held-out side's wrap count (tried once, measurably did
nothing). Accepted at pass@5 2/5 solved, 3 valid fails, avg@5=0.400, after 13 pushes and roughly
20 hours of pipeline cycles.
