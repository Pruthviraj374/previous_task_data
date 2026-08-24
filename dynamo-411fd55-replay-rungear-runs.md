# dynamo/replay-rungear-runs — the library's own semantics, withheld

Repo: `dynamo-411fd55-model-training-and-ml-infrastructure`, PR #3, branch `submission`,
fork `Pruthviraj374`.
PR: https://github.com/handshake-project-dynamo/dynamo-411fd55-model-training-and-ml-infrastructure/pull/3
Category: **Model Training and ML Infrastructure** / Sub-category: **Training loops**.
`task.toml` declares `model_tested = Opus-4.8`, `agent_tested = Terminus-2`; the pipeline
stickies name the benchmarked model only as `Model A`. Accepted 2026-08-22 at commit `39f990e`.

**Final result: pass@5 = 0/5 solved, avg@5 = 0.000, 5 good valid failures, 0 soft-timeout,
0 in-progress-timeout, 0 task/verifier issues, 0 infra, 0 reward hacking.** Best possible
outcome. All 16 gates green; `trials` ran 2h9m7s, final `pass2` 0/2 in 56m31s.

**Six content cycles.** Four of the six were verifier-soundness holes found by `ava_review` and
`qc_gate`, not difficulty problems — see §3. A seventh cycle was lost entirely to a platform
outage (§7.1). The difficulty itself measured 0-solved on every pass@ the pipeline ever
completed.

> **Sibling overlap, recorded honestly.** `dynamo-afed5c2-replay-run-histories.md` — same
> category **and** sub-category (Training loops), same fork — was written on the day this task
> was accepted, and shares this one's *shape*: an archive from a decommissioned system, replayed
> against a **named real authority whose behaviour is withheld** (stock TensorBoard's reader
> there, `torch.optim` here). Both reached pass@5 0/5 and both are accepted, and neither
> `similarity` nor `cosine_similarity` could have caught the resemblance because they compare
> against TB2/TB3 only. The two differ in what carries the difficulty — event-file *reader*
> conventions versus *sequential optimiser/scheduler state that compounds across steps* — but a
> human reviewer looking at both together could reasonably call the framing repetitive.
> **The next task in this category should not use "archive + named authority + replay" a third
> time.** See §"Hard rule: reuse the machinery, never the task idea" in the index, and the
> `nfs4-access-audit` banner: survey this directory again immediately before opening the PR,
> because other sessions write into it while you work — this file and afed5c2's landed hours
> apart.

---

## 1. What the task asks

A retired in-house fine-tuning service, *Rungear*, left an archive of **runcards** — the exact
loop configuration of each training job — plus each job's training series and starting
parameters. The service and its result database are gone.

- **Agent sees:** `/app/data/RUNCARD.md` (the loader note), three runcards under
  `/app/data/runs/`, their series and inits, and the recorded results for **two** of the three
  under `/app/data/expected/`.
- **Agent produces:** `/app/replay.py`, invoked as
  `python3 /app/replay.py <runcard_path> <output_path>`, plus
  `/app/output/harbor-2021-c.json`.
- **Graded on:** that one artifact, a re-run over the verifier's own copies of all three shipped
  runcards, and **41 held-out runcards** never shipped. 50 checks, all-or-nothing.
- **Constraint:** standard library plus `numpy`, no child processes, no network, no reading
  `/app/data/expected/`, and no filesystem effect beyond creating the output file.

---

## 2. The crux

> **The runcards name `torch.optim` and `torch.optim.lr_scheduler` classes and pass them
> constructor arguments. The loader note documents the *encoding* exhaustively and refuses to
> restate a single library semantic. The two runs whose answers ship are plain AdamW with decay
> explicitly zero, no scheduler, no clipping, no accumulation and a row count divisible by the
> batch size — so the textbook training loop reproduces both to the bit.**

Ten mechanisms decide a replay, none of them exercised by the self-check:

| Mechanism | What the textbook loop gets wrong |
|---|---|
| `AdamW` decoupled decay | folds decay into the gradient instead of `p *= 1 - lr*wd` before the moment update |
| `AdamW` decay default | treats an absent `weight_decay` as zero (the library default is `1e-2`) |
| `amsgrad` | ignores the running maximum of the second moment |
| `clip_grad_norm_` | clips each parameter by its own norm instead of one joint norm |
| `SGD` momentum | uses the classical buffer with the learning rate folded inside it |
| `SGD` `nesterov` / `dampening` | applies dampening on the first step; mis-forms the nesterov update |
| `SGD` `weight_decay` | decouples it, as `AdamW` does, instead of adding it to the gradient |
| closed-form schedules | reads the schedule one step late — the factor at `last_epoch = 0` already applies to the first step |
| `ConstantLR` / `LinearLR` defaults | assumes a unit start factor (both default to `1/3`) |
| `ReduceLROnPlateau` | compares absolutely rather than against a relative threshold, fires at `>= patience` instead of `> patience`, mishandles `cooldown`, ignores `min_lr` |

### The invariants that keep it alive

1. **The shipped self-check exercises none of the ten.** Measured, not assumed — four wrong
   replayers reproduce both records exactly (§4.2).
2. **The loader note names the library and refuses to restate it.** "Where it names a library
   class or one of that class's arguments, the meaning of that name is whatever PyTorch means by
   it — this note does not restate library behaviour, and the runcards do not either." The single
   load-bearing sentence is *"A constructor argument that does not appear in a runcard was not
   passed"*, which makes the non-zero `AdamW` decay default discoverable without stating it.
3. **The archive is an invented container with real external semantics.** Nothing off the shelf
   reads a runcard, so `allow_internet = true` cannot hand over the answer — but PyTorch's docs
   and source are public, so the rules are fair and discoverable (`lumenp` §2, `replay-rulepack`
   §3.3, reused).
4. **The graded artifact has no shipped answer.** `harbor-2021-c` has no reference anywhere
   under `/app`, and a test asserts it (`merge-lora` §3.1, reused).

### Why this is not `merge-lora` in different nouns

`merge-lora` and `replay-rulepack-scores` both put the crux in a **static** artifact — config
knobs, or a property of an input record. This one puts it in **sequential state evolution**: the
optimiser buffers, the scheduler's `last_epoch`, and the plateau bookkeeping all carry across
steps, so a single wrong convention compounds over 20-60 optimiser steps into a large,
unmistakable divergence rather than a near-miss. The `similarity` gate returned UNIQUE and both
`cosine_similarity` runs sat well under the 0.9 block.

---

## 3. Dead ends — do not retry these

### 3.1 Four verifier-soundness holes, all the same family

Every blocking finding on this task was some version of *the answer is reachable by a path the
guard did not anticipate*. They are listed in the order they were found, because each fix
exposed the next.

**(a) The answers one level above the archive root.** `ava_review`:

> **`sound_verifier`** — The only path the guard blocks reading is /app/data/expected. Any other
> file, including the verifier's answer key, is permitted … for runcard
> /tests/fixtures/archive/runs/<name>.json the upward walk reaches /tests/fixtures and finds
> /tests/fixtures/expected/<name>.json (not under SEALED=/app/data/expected)

`merge-lora` §3.1 is about a graded answer shipping under `/app`. **This is a new variant: the
answer was not under `/app` at all, it was one directory above the archive root at verify
time.** I wrote the exploit before fixing and it passed **29 of the 33 checks then in place**.

**Fix that worked:** stop sealing and start staging. The verifier now materialises `runs/`,
`series/` and `init/` one **named file** at a time into a fresh temp directory, so no result
record exists anywhere at or above the root the program is handed. A test asserts the absence.

**Do not** just add `/tests/fixtures/expected` to the seal list — that is the same
enumerate-the-paths game that lost three more cycles below.

**(b) `ctypes.CDLL(None)` walks straight past the audit hook.** `ava_review`:

> dlopen(None) is deliberately allowed for numpy; CDLL(None) therefore succeeds and exposes
> libc … the verifier would instead reward=1

`merge-lora` §4.5 says explicitly: *"do not block all `ctypes.*` audit events … numpy imports
ctypes, so a blanket block breaks every correct submission."* That advice is right about the
*cause* and wrong about the *remedy*, and following it verbatim cost a cycle. The exploit scored
**reward 1.0 outright** — a full bypass reading the golden records through libc `open`/`read`,
never touching Python's `open` audit event.

**Fix that worked:** import numpy **in full** (`numpy.linalg`, `numpy.random`) *before*
installing the hook, so every native library is already resolved, then refuse `dlopen`
**outright** including `dlopen(None)`. Verified the accept side still works: a replayer that
offers an optional accelerated path and falls back to numpy scores 1.0.

**(c) `os.link` is not an audited event.** Same review. Hardlink a sealed record out, read the
link; its `realpath` carries no `expected` component. Blocked by adding the event *and* by
dropping the guarded run to `nobody`.

**(d) A symlinked parent directory.** `qc_gate` E5, after I had already added an `islink` check:

> The graded release artifact `/app/output/harbor-2021-c.json` is compared byte-for-content
> against the golden … reads [...] with no symlink guard

My guard checked only the **final component**. `rm -rf /app/output && ln -s
/tests/fixtures/expected /app/output` leaves `harbor-2021-c.json` a genuine regular file whose
own `islink` is false. It scored **reward 1.0**.

**Fix that worked:** walk *every* component of both graded paths rejecting symlinks, and require
`realpath(path) == path`.

**The generalisation, and the reason this section is long:** a guard that enumerates forbidden
APIs is always one API behind. What finally held was the two structural defences — **stage the
inputs so the answer is not on the path at all**, and **drop privileges so no read mechanism
reaches it** — with the audit hook as a third layer for clean error messages, not as the
primary control.

### 3.2 Two *stated* rules that were ungradeable, and a mutation methodology that hid both

`qc_gate` found, on two separate cycles, that a mutant violating a rule `RUNCARD.md` **states
outright** still scored `reward=1`:

> Mutated the reference to violate RUNCARD.md step 2 ('gradients … each divided by grad_accum')
> … bash /tests/test.sh -> reward=1

> Mutated the reference solve to compute epoch mean loss as a ROW-COUNT-WEIGHTED mean …
> violating the stated 'unweighted arithmetic mean' requirement … reward.txt=1 (still passes).
> Root cause: no graded runcard ever uses a short [micro-batch]

Both are real and both have the same shape — **the rule was unobservable given the data**:

- **`/grad_accum`.** Every accumulation run used `AdamW`, and Adam's update is invariant to a
  constant rescaling of the gradient (`m/√v` cancels it; only `eps` at 1e-8 survives, far under
  the 1e-6 tolerance). *No AdamW accumulation run can witness that rule at all.*
- **Unweighted epoch mean.** Weighting each micro-batch loss by its row count is *identical* to
  the plain mean unless an epoch keeps a short final micro-batch. Measured: **0 of 44 runs** had
  `rows % batch_size != 0` with `drop_last` false.

**My own mutation sweep passed both, and that is the transferable lesson.** My mutants modelled
*implausible* wrong implementations — an artificial `[1.0…, 0.5]` weighting that differs even
with equal batches — so they died on every run and looked like coverage. QC's mutants modelled
what a real engineer would actually write. **A mutant that no one would write proves nothing.**

**Fix that worked:** build runcards that make each rule observable — four accumulation runs under
**SGD** (linear in the gradient; divergence 2.55, 1.05, 0.69, 0.17) and four `ragged-*` runs that
keep a short final micro-batch (divergence 9.5e-3 to 1.3e-1) — and assert both properties as
build-time invariants so a future archive cannot lose them silently.

**Do not** answer these findings by loosening the tolerance or deleting the rule from
`RUNCARD.md`. The rule is correct; the *data* was inadequate.

### 3.3 An equivalent mutant is not a coverage hole — delete the branch instead

`qc_gate` also flagged that removing `ReduceLROnPlateau`'s `eps` guard still passed. I measured
it: **exactly 0.0 difference on all runs**. The guard only bites when a reduction is ≤ 1e-8, and
every reduction the archive can produce is ≥ 0.003; at a `min_lr` floor the new value equals the
old one. Grading it would mean grading a 1e-8 difference against a stated 1e-6 tolerance, which
the fairness line forbids.

Following `merge-lora` §3.2 (*"if the distinction is not load-bearing, delete the fixture that
observes it"*), I **removed the branch from the reference** and added an invariant that
reconstructs the guarded form and asserts the two agree exactly. QC did not raise it again.

**Do not** try to build a fixture for it — there isn't one that is both realistic and above
tolerance. **Do not** argue equivalence in prose either; the invariant is the argument.

### 3.4 Raising the agent timeout to fix a pass@2 timeout — half right

`pass2_suggestion` said the one failure was a timeout mid-fix, not a difficulty failure, and
advised raising `[agent].timeout_sec` from 3600 to 5400–7200. I set 7200 **and** added eight
held-out runcards in the same commit, because a longer budget also helps the agent that was
close, and one trial had already solved it inside the hour.

That was the right call for a reason I only learned later: **`pass2` caps the agent run at
3600s regardless of `task.toml`** — its own header says *"agent-run budget = task timeout_sec,
capped 3600s/1hr"*. So the raise never reached pass@2 at all; the two subsequent pass@2 passes
came from the breadth, not the budget. The 7200 still applies to pass@5, where it mattered.

**Do not** raise the timeout alone in response to that suggestion. It cannot help pass@2, and on
pass@5 it shifts the odds *toward* the agent solving.

---

## 4. What actually worked

### 4.1 Ground truth from running real PyTorch, in two versions

The numpy reference was cross-checked against `torch.optim` driving the identical loop in double
precision: **worst relative difference 2.1e-15 across all 44 runs and every field**, against
**both torch 2.8.0 and torch 2.4.1**. Two versions, not one, because the agent may probe any
recent release — the agreement is itself the fairness argument, and it pre-empted the
"could not execute" caveat every read-only reviewer raises.

`merge-lora` §4.2 and `replay-rulepack` §4.1 both say this; confirmed a third time. Running the
library beats reading it.

### 4.2 Four plausible-wrong replayers, run through the real verifier

| Reading | Shipped self-check | Checks failed | Reward |
|---|---|---|---|
| textbook loop (L2 decay, amsgrad ignored, per-tensor clipping, schedules one step late, `>=` patience, classical momentum) | both reproduced exactly | 28 | 0 |
| docs-level reading (decoupled decay without the `lr` factor, dampening on the first step, absent decay read as zero, unit `ConstantLR` factor) | both reproduced exactly | 24 | 0 |
| nearly right (absent decay read as zero, classical momentum, `min_lr` ignored) | both reproduced exactly | 11 | 0 |
| flattened loop (`grad_accum` and `drop_last` ignored, decay decoupled for SGD too) | both reproduced exactly | 13 | 0 |

All four reproduce the self-check exactly and no two fail the same set. **That table is the
task.** It is also what proves the self-check is inert rather than merely hoped to be.

### 4.3 Breadth, measured per run

24 single-rule mutations, **zero survivors**, covering both the withheld conventions and the
rules the note states. Per-run analysis at the end: **every one of the 44 runs kills at least one
mutation** — none is dead weight — while only one run is the *sole* witness of a rule. That
overlap is deliberate. Three of the six content cycles were "add coverage"; none was ever "too
much coverage."

### 4.4 The graded shipped artifact was allowed to leak three axes

`harbor-2021-c` had to exercise something or it would be free. It got decoupled decay,
`clip_grad_norm_` and `ConstantLR`'s defaults — all visible as keys in its own runcard. The other
seven mechanisms stayed held-out-only. Same arrangement `replay-rulepack` §4.4 had blessed as
"intentional disclosure".

---

## 5. Gate-by-gate log

| # | Commit | Gate | Verdict | Cause | Fix |
|---|---|---|---|---|---|
| 1 | `b9c266e` | `review` | FAIL — `difficulty_explanation_quality` (30/31 pass) | The field omitted data provenance and a named real-world audience; the framing lived only in `instruction.md` | Two paragraphs stating the archive is synthetic-but-realistic and naming ML-infra/reproducibility engineers (`e6af3de`) |
| 2 | `e6af3de` | `ava_review` | BLOCK — `sound_verifier` ×2 | Ancestor scan reaches `/tests/fixtures/expected` (§3.1a) | Stage a clean archive of named files; assert no `expected/` reachable (`c3cde2d`) |
| 3 | `c3cde2d` | `pass2` | FAIL — 1 solved, 1 in-progress-timeout, 0 valid fails | One agent solved it; the other ran out of clock mid-fix | Raise agent timeout to 7200 **and** add 8 held-out runcards (`7f76813`) |
| 4 | `7f76813` | `ava_review` | BLOCK — `sound_verifier` ×3 | `CDLL(None)` → libc; `os.link` unaudited (§3.1b, §3.1c) | Full numpy preload then block all `dlopen`; run guarded replays as `nobody` (`bd35655`) |
| 5 | `bd35655` | `qc_gate` | BLOCK — C3 Narrow/Hardcodable | `/grad_accum` unobservable under Adam (§3.2) | 3 accumulation runs under SGD + build-time invariant (`18eef45`) |
| 6 | `18eef45` | `qc_gate` | BLOCK — C3 `eps` + B4 Undocumented Requirement | Equivalent mutant (§3.3); guard enforced filesystem rules `instruction.md` never stated | Delete the `eps` branch with an equivalence invariant; document the filesystem constraint (`e56a7c0`) |
| 7 | `e56a7c0` | `qc_gate` | BLOCK — E5 Symlinked Output Path | Only the final path component was checked (§3.1d) | Walk every component; require `realpath == path` (`7da8282`) |
| 8 | `7da8282` | — | *(seven runs lost to a platform outage — §7.1)* | — | — |
| 9 | `621696a` | `tier1` | HOLD — "no diff since the review" | An **empty commit** pushed while monitoring was paused; tier1 compared `7da8282…621696a` = 0 files | Real fix pushed (`39f990e`) |
| 10 | `39f990e` | — | **ALL GREEN, `accepted`** — pass@2 0/2, pass@5 **0/5**, avg@5 **0.000**, 5 good valid fails | — | — |

**Never failed once:** `changes` (static, 25 checks — `.dockerignore` and the ≤1500-token count
clean from the first commit), `similarity` (UNIQUE), `cosine_similarity`, `validation`
(Docker/Oracle/Nop), `ratelimit`, `qc_eval`, `qc_exec`, `deep_review` (passed every time it ran),
`tier1` (except the empty-commit hold, which was correct).

### 5.1 The pass@5 failures

All five were classified good-valid with `difficulty_crux` and `approach_validity` PASS. The
recorded pass@2 root causes across the run's life cluster on: scheduler `__init__` applying the
factor before the first step (the single most common), `ReduceLROnPlateau` cooldown/`best`
bookkeeping, `LinearLR`'s `total_iters` denominator, amsgrad bias-correction ordering, `AdamW`
`weight_decay` default, and SGD first-step dampening.

**I could not predict which axis would gate — fifth confirmation across this corpus.** I rated
the scheduler-init off-by-one a minor detail; it took more trials than any optimiser mechanism.

---

## 6. Error → what to do, and what not to do

| Symptom | Do | Do **not** |
|---|---|---|
| `ava_review` `sound_verifier`: the answer is reachable from the archive root | **Stage** the graded inputs as named files into a fresh temp dir so no answer sits at or above the root; assert the absence in a test | ❌ add the newly-found directory to a seal list — you will be back next cycle |
| A guard carve-out exists "because numpy needs it" | Preload the dependency **in full** before installing the hook, then close the carve-out; probe both sides | ❌ trust a prior task's "don't block all of X" verbatim — check whether preloading removes the need |
| A symlink check on a graded artifact | Walk **every** path component and require `realpath == path` | ❌ check only the final component — a symlinked parent leaves the leaf a genuine regular file |
| `qc_gate` C3: a mutant violating a **stated** rule still passes | Ask whether the rule is *observable given the data*, then build runcards that witness it, and assert it as a build-time invariant | ❌ loosen the tolerance; ❌ delete the rule from the spec — the rule is fine, the data was inadequate |
| A mutant of yours "proves" coverage | Write the mutant a **real engineer** would write (row-count weighting, not an arbitrary weight vector) | ❌ treat an implausible mutant's death as evidence — it is the most convincing way to fool yourself |
| A mutant survives and you cannot build a fixture above tolerance | Measure it; if it is exactly equivalent, **delete the branch** and add an equivalence invariant | ❌ argue equivalence in prose across cycles |
| `pass2_suggestion` says "raise the agent timeout" | Raise it, but pair it with real breadth | ❌ raise it alone — pass@2 caps at 3600s regardless, and on pass@5 a longer budget helps the *agent* |
| A gate fails in seconds inside a step that never reads the task | Platform fault. Change nothing; wait, then cycle the PR | ❌ start editing the task |
| You need to re-trigger without write access | `gh pr close` then `gh pr reopen` your own PR — fires a fresh pipeline on the same SHA | ❌ push an empty commit — see the next row |
| Someone pushes an empty commit to re-trigger | Push a real fix | ❌ expect it to help: `tier1` compares the review base to HEAD and holds with *"No diff since the review — required fixes not attempted"* |

---

## 7. Bugs and misjudgements of my own

- **Two mutation-sweep blind spots, same root cause** (§3.2). Both times my mutant was
  unrealistic and both times QC found the real one. After the first (`grad_accum`) I added
  "stated rules" to the sweep — but wrote the *weighted mean* mutant carelessly, and it bit
  again four cycles later. Fixing the methodology, not the instance, was the lesson.
- **A symlink guard that checked the leaf only** (§3.1d) — added in direct response to a QC
  amber note, and still incomplete.
- **Trusting a prior retrospective's remedy verbatim.** `merge-lora` §4.5's "don't block all
  `ctypes.*`" is correct about the cause and wrong about the fix. Prior findings are evidence,
  not instructions.
- **Probe-harness codegen that silently produced a syntax error.** `body.split('install()')` cut
  at `def install():` because the latter contains the former as a substring; all four naive
  probes then "failed everything", which looks exactly like a real result. `merge-lora` §6 warns
  that all-fail and all-pass are both smells; confirmed again. **Compile generated probe source
  before running it** — I added `compile()` to the generator and the next bug surfaced instantly.
- **Misparsed `gh pr checks` output and told the user nothing was failing.** The output is
  tab-separated; splitting on whitespace hid a `fail` row. Use `awk -F'\t'`.

---

## 8. Process notes

### 8.1 The platform outage, and how to tell

**Seven consecutive pipeline runs were lost to the harbor evaluation backend**, across ~13 hours
and then a 39-hour gap, in three distinct signatures:

- `DaytonaNotFoundError` — sandbox destroyed ~55s after `mark_task_complete`; the analysis said
  outright *"a platform/environment failure, not an agent or task defect."*
- `harbor / pass@k` posting *"The evaluation did not finish. Re-run it."*
- `harbor / pass@k` never reporting at all, so `pass2` failed at exactly 1h01m with
  **`the platform's 'harbor / pass@k' status did not finish within 60 minutes`** and
  "0 of 0 runs failed genuinely".

**The tell for the last one is "0 of 0".** A real difficulty failure reports N of 2; zero
analysed trials means no evaluation happened. Read the `pass2` **job log**, not the sticky.

**Cycling cadence, measured:** cycling 5 minutes after a fault reproduced it. Cycling ~80 minutes
after worked twice. Cycling after the orphaned `harbor / pass@k (gate 2)` check *cleared* worked.
The run that finally completed came after a **39-hour** idle gap. Do not cycle hourly into a
persistent outage — it consumes the daily evaluation budget for no signal.

### 8.2 Stickies lag; the job log does not

I twice read a **stale sticky** and drew the wrong conclusion — a `pass2_suggestion` still
showing "currently 3600.0" and trial ids from a run two cycles earlier. Sticky comments are
edited in place. Always check `QC-BASE:` / `TIER1-BASE:` against `git rev-parse HEAD`, and prefer
the job log for anything numeric. (`merge-lora` §7 says this; confirmed twice more.)

### 8.3 Other

- **Do not push while `trials` or `pass2` is in flight** — held throughout. One exception was
  deliberate and checked: `harbor / pass@k (gate 2)` sat "pending" for 68 minutes after its
  parent workflow had **completed**, with `review/trials` skipped. An orphaned external check
  whose consumer has finished is not live work; confirm via `gh run view <id> --json status`.
- **`.dockerignore` in `environment/` from the first commit**; static passed 25/25 every time.
- **No `"You have N seconds…"` line**; `instruction_concision` passed every run.
- **Local git identity from `gh api user` at clone time**, before the first commit.
- **`[task].description`** drew a "borderline" note on three separate rubric runs and was graded
  PASS every time. It ships in the repo's own scaffold. Leave it.
- Verifier timeout 600s for 44 subprocess replays (~18s actual); per-subprocess bound 20s so the
  sum cannot overrun the budget — a `deep_review` advisory worth pre-empting.

---

## 9. Checklist for the next task

Before writing code:
- [ ] Is the deciding rule a **published convention**, **conditional**, and **absent from the
      sample**? All three, or it is recall.
- [ ] Can an off-the-shelf package read your format? If yes, invent the container and keep the
      semantics real.
- [ ] Cross-check ground truth against the real library in **two versions**, not one.
- [ ] Count the independently-checkable consequences. Ten was comfortable; the live failures used
      six of them.
- [ ] Write **four** plausible-wrong implementations. Require zero self-check diffs from all.

While building:
- [ ] For every rule you **state**, ask: *is it observable given this data?* Adam hides gradient
      scaling; equal-size batches hide weighting; a floor hides an epsilon.
- [ ] Write mutants a **real engineer would write**. `compile()` generated probe source.
- [ ] For every graded artifact: does its answer exist anywhere at or above the root the program
      is handed — including one level *above* the staged archive?
- [ ] Stage inputs as **named files** into a temp dir; never hand over a directory.
- [ ] Drop privileges for untrusted runs. An audit hook is a third layer, not the control.
- [ ] Check **every** component of a graded path for symlinks, not just the leaf.
- [ ] Assert each hard-won property as a **build-time invariant**, not a paragraph of prose.

Before every push:
- [ ] Oracle 1.0, nop 0.0, every bypass probe, both sides of the guard, and the mutation sweep,
      against the real verifier in the built image.
- [ ] Root `README.md` reviewed against the **complete** diff, in the same commit.
- [ ] `gh pr checks` clean of `pending` — parsed with `awk -F'\t'`.

---

## 10. One-paragraph version

The trap was a loader note that documents an invented archive format exhaustively and then
refuses to restate one line of the library semantics it defers to: the runcards name
`torch.optim` classes and pass them constructor arguments, and the two runs whose recorded
results ship are plain AdamW with decay explicitly zero, no scheduler, no clipping, no
accumulation and a divisible row count — so the textbook training loop reproduces both to the
bit while 41 held-out runcards carry the ten PyTorch behaviours it gets wrong. All five pass@5
agents built a substantively correct replayer and failed, most often on the scheduler applying
its factor *before* the first optimiser step, an axis I had rated minor. The difficulty was never
the problem: four of six content cycles were verifier-soundness holes, every one of them the same
shape — the answer reachable by a path the guard had not anticipated (one directory above the
archive root, through `ctypes.CDLL(None)` into libc, through an unaudited `os.link`, and through
a symlinked parent directory that leaves the leaf a genuine regular file). What finally held was
structural rather than enumerative: stage the inputs as named files so no answer sits on the
path, and drop the guarded run to `nobody` so no read mechanism reaches one. The other two cycles
were QC proving that a rule the note *states* was ungradeable because the data could not witness
it — Adam's scale-invariance hiding the `grad_accum` division, and equal-size micro-batches
hiding the unweighted epoch mean — and both slipped past my own mutation sweep because my mutants
modelled wrong implementations nobody would write. Seven further pipeline runs were lost outright
to a harbor outage whose signature is `pass2` failing at 1h01m with "0 of 0 runs failed
genuinely"; the fix is to wait hours, not an hour, and cycle the PR rather than push.
