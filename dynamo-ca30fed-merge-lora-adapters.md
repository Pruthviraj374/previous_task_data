# dynamo/merge-lora-adapters — the shipped self-check that must not be the graded answer

Repo: `dynamo-ca30fed-model-training-and-ml-infrastructure`, PR #2, branch `submission`,
fork `Pruthviraj374`.
Category: **Model Training and ML Infrastructure** / Sub-category: **Fine tuning**.
`task.toml` declares `model_tested = Opus-4.8`, `agent_tested = Terminus-2`; the pipeline
stickies name the benchmarked model only as `Model A`. Accepted 2026-08-09 at commit
`502d6e5`.

**Final result: pass@5 = 0/5 solved, avg@5 = 0.000, 5 good valid failures, 0 soft-timeout,
0 in-progress-timeout, 0 task/verifier issues, 0 reward hacking.** Best possible outcome. All
seven per-trajectory rubric criteria PASS on all five trials.

Two content cycles, two commits. `qc_gate` passed **first time** (44 checks and probes,
`QC-FIXES-B64: W10=`), as did the rubric review (**31/31, zero failures**), `deep_review`,
`tier1` and both `pass2` measurements. The single blocking failure was `ava_review`, and it was
a *new* class not yet in this directory: not the AST deny-list, but **grading an artifact whose
correct answer ships inside the agent's own image.**

---

## 1. What the task asks

A platform's LoRA merge service — the thing that folds a trained adapter back into its base
checkpoint so serving loads one plain set of weights — is gone. The agent rebuilds it.

- **Agent sees:** `/app/data/base/dsl-360m/model.safetensors` and three adapters under
  `/app/data/adapters/`. Two of them (`sql-formatting`, `summary-v2`) ship their correct merged
  checkpoints under `/app/data/expected/` as an end-to-end self-check. The third
  (`promptfix-v3`) ships **no** reference.
- **Agent produces:** `/app/merge.py`, invoked as
  `python3 /app/merge.py <base_dir> <adapter_dir> <out_file>`, plus
  `/app/output/promptfix-v3.safetensors`.
- **Graded on:** that one output artifact, a re-run of the program over the verifier's own
  copies of all three shipped adapters, and **thirteen held-out adapters** never shipped.
- **Constraint:** standard library plus `numpy` and `safetensors`, no child processes, no
  native libraries of its own, no network.

Held out: `plain`, `rslora`, `alphapat`, `rankpat`, `fanin`, `savehead`, `dora`, `embed`,
`bias`, `bias_rs`, `combo_rsdora`, `combo_fanpat`, `combo_embsave`.

---

## 2. The crux

> **A LoRA adapter is not a pair of matrices; it is a checkpoint plus a configuration, and the
> configuration decides the arithmetic. The one-line merge everybody knows is exactly right for
> the adapters that ship with reference answers.**

`W += (lora_alpha / r) · B @ A` reproduces both self-check merged checkpoints to the bit. Nine
published PEFT behaviours diverge from it:

| Mechanism | What the one-liner gets wrong |
|---|---|
| `use_rslora` | `alpha/r` instead of `alpha/√r` |
| `alpha_pattern` | default alpha everywhere |
| `rank_pattern` | config default rank in the scaling |
| Pattern-key matching | treats the key as a substring; PEFT anchors it as a regex over a whole dot-delimited tail, so a mid-path key like `self_attn` matches **nothing** |
| `fan_in_fan_out` | delta added in the wrong orientation |
| `use_dora` | adds a delta where the merge renormalises each output row of the sum to a saved magnitude |
| `modules_to_save` | adds the verbatim retrained tensor instead of replacing |
| Embedding factors | `lora_embedding_A/B` carry no `.weight` suffix and the product is oriented the other way |
| `lora_bias` | bias dropped, or added unscaled |

### The invariants that keep it alive

1. **The shipped self-check exercises none of the nine.** Both reference adapters are plain
   LoRA. Measured, not assumed — §7.
2. **The shipped adapter configs are older-tooling files.** They carry `fan_in_fan_out`,
   `modules_to_save`, `bias`, `init_lora_weights` — and simply do **not contain** the keys
   `use_rslora`, `use_dora`, `rank_pattern`, `alpha_pattern`, `lora_bias`. Real PEFT gained
   those fields across releases, so an archive spanning years genuinely looks like this. If the
   samples carried the modern config with everything at its default, the file would *enumerate
   the knobs* and the task would be far easier.
3. **`instruction.md` names the dimension, never a rule.** It defines correctness as "the same
   merged checkpoint PEFT's own merge produces… for whatever the adapter's configuration says",
   and says the archive's configurations "are not all shaped like these". It never says rslora,
   dora, transpose, pattern, or bias. Same move as `audit-build-context`'s "interpreted exactly
   as the container builder does it".
4. **No graded artifact has a shipped answer.** This one was learned the hard way — §3.1.

### Why breadth mattered more than depth

`audit-build-context` §2's finding held again: what survives is the **number of
independently-checkable consequences**. pass@5 proves it — one trial got `bias`/`bias_rs`
right and still scored 0; two crashed on `fan_in_fan_out` while three handled it; one uniquely
failed `savehead` on a prefix bug. No single mechanism was load-bearing. A task resting on DoRA
alone would have been solved.

---

## 3. Dead ends — do not retry these

### 3.1 Grading an output whose reference answer ships in the agent's image

**This is the blocking failure, and it is a new class for this directory.** The first design
shipped two adapters with `/app/data/expected/*.safetensors` as the self-check, and *also*
graded `/app/output/sql-formatting.safetensors` and `/app/output/summary-v2.safetensors`
against them. AVA:

> **`sound_verifier`** — at `tests/test_outputs.py test_ground_truth_is_out_of_reach`, Only
> removes /tests/fixtures and forbids expected.safetensors under /tests; /app/data/expected is
> untouched; expected Rejected — no real merge computed, but the verifier would instead
> Sample/reproduce tests pass; archive tests still fail, so not full reward —
> partial-credit/anti-copy weakness only.

I wrote the exploit before fixing it (`freight` §4's rule) and it was real: a `merge.py`
consisting of `raise SystemExit("not implemented")` plus two `cp` commands passed
`test_shipped_adapter_outputs[sql-formatting]` and `[summary-v2]`.

**The tempting fix is to delete `/app/data/expected/`. That is wrong.** The shipped self-check
*is* the trap — pass@2 confirmed both agents validated against it, saw zero diff and quit. It
is the "no self-check" amplifier inverted: a complete-*looking* oracle that is silent on the
crux (`contact-export` §9). Removing it would have removed the mechanism that makes the task
work.

**What to do instead: ship one more adapter with no reference and grade that one.** See §4.1.

### 3.2 Making a version difference between library releases the deciding case

Current PEFT resolves `rank_pattern` and `alpha_pattern` against their **own** key sets
(`get_pattern_key(rank_pattern.keys(), …)` and again for alpha, independently). Older releases
picked one shared `target_name_key` from `chain(rank_keys, alpha_keys)`. The two disagree when
a module is named by a full-path key in one dict and a suffix key in the other.

Both the rubric review and AVA flagged my independent resolution. The rubric called it
"minor, non-blocking… Worth a human note if the case set is expanded." AVA, advisory:

> **`verifier_coverage`** — separate resolution per dict rather than PEFT's chained
> pattern_keys single target selection… the alpha_pattern override is dropped for that module,
> but the verifier would instead Golden resolves alpha independently via K_a and APPLIES the
> alpha_pattern override, yielding a different scaling and different merged weights.

My reference is right for peft 0.20.0 — the ground truth came from running it. **I still
deleted the fixture.** Cycle 1 I had *added* a case (`patboth`) carrying both pattern dicts to
pin the behaviour; cycle 2 I removed it, so no case populates both and the two schemes merge
identically everywhere.

Rationale, following `container-dependency-resolver` §5.1 (QC called a rule ambiguous; deleting
it beat disambiguating it): the distinction was **not load-bearing** — pass@2 showed agents use
a global `r`/`alpha` and never reach it — and two automated graders raising it means a human
will too. Grading a difference between library versions is a fair objection. Cost of deletion:
zero measured difficulty. Cost of defending it: a third round of the same argument.

### 3.3 The `"You have N seconds…"` closing line

Never shipped, on the strength of `fir` §6.2 and `audit-build-context` §8. The local doc set
mandates it and claims CI enforces it; both are false and the live rubric fails it under
`instruction_concision`. `instruction_concision` PASSED here with the explicit note "no
time-budget string". **The doc set has since been corrected in `verify/CLAUDE.md`.**

---

## 4. What actually worked

### 4.1 Give the graded artifact no shipped answer, instead of removing the self-check

Added a **third** shipped adapter, `promptfix-v3`, whose merged checkpoint exists only in
`tests/fixtures/`. `/app/output/promptfix-v3.safetensors` became the sole graded output;
`artifacts` was narrowed to it. The other two kept their references and reverted to being
purely a self-check.

The result is that the self-check trap is untouched while nothing gradable can be copied. Two
tests pin it:

- `test_release_output` grades the file against the verifier's private copy.
- `test_no_shipped_reference_for_release_output` asserts no reference for it exists under
  `/app/data/expected` — so a future edit that "helpfully" adds one fails loudly.

Re-running the exploit after the change: 4 structural tests, reward 0. AVA passed on the next
push.

`promptfix-v3` itself carries `use_rslora` and an `alpha_pattern`, so the graded artifact is
also unreachable without implementing the crux — it is not a freebie.

### 4.2 Ground truth from running the real library

Same decisive move as `audit-build-context` §4.1. I built the base checkpoints and adapters
with **real PEFT 0.20.0 under torch**, called `save_pretrained` and `merge_and_unload`, and
dumped the result. The numpy reference then had to agree with 16 of 16 fixtures — max abs
difference **5.96e-08**, float32 rounding.

This converts every correctness question into a diff. It also pre-answered the reviewer note I
would otherwise have collected: the rubric ran read-only ("I could not execute the solution or
read the binary `.safetensors` headers") and credited byte-exactness on internal consistency,
asking human reviewers to confirm it — which `validation` had already done on the same SHA by
running the oracle to reward 1.0.

**Do not port the library's source and reason about it.** Reading `dora.py` alone would not
have settled that `get_weight_norm` normalises over `dim=1` of the *transposed-if-fan_in_fan_out*
weight; running it does.

### 4.3 Three plausible-wrong implementations before fixing the fixture set

`audit-build-context` §7's methodology, and it earned its keep again. Written before the case
list was final, run against the real verifier:

| Naive implementation | Self-check | Held-out failures | Reward |
|---|---|---|---|
| Textbook `alpha/r · B@A`, transposing only when shapes demand it | pass | 13 | 0 |
| Reads the config carefully; scales rsLoRA like plain LoRA, skips DoRA, matches pattern keys by substring | pass | 9 | 0 |
| Knows rsLoRA and DoRA; normalises DoRA over the wrong axis, ignores `alpha_pattern` | pass | 6 | 0 |

**All three reproduce both self-check checkpoints exactly, and no two fail the same set.** That
table *is* the task. It also flags the freeloaders in advance: `plain` and `embed` are passed by
all three, so they are coverage, not difficulty — recorded in the README as a decision rather
than left to look like an oversight.

### 4.4 Mutation sweep, and analysing the survivors

14 one-rule inversions; 12 killed. Both survivors were analysed rather than dismissed, and both
are genuinely equivalent:

| Survivor | Verdict |
|---|---|
| Rank-consistency assertion removed | Equivalent for any valid adapter. Deriving `r` from the saved factor shapes instead of the config is an equally correct implementation and passes — which is the *right* outcome, not a hole |
| Shared vs. independent pattern-key resolution | Unobservable by construction after §3.2. Documented as deliberate |

### 4.5 Runtime enforcement, probed on both sides

`audit-build-context` §4.2's recipe, reused verbatim and confirmed again. `tests/guard.py` drops
to `nobody` and installs a `sys.addaudithook` guard. Twelve bypass spellings probed **inside the
built image**, all blocked; and the accept-side probe — a `try/except ImportError` fallback to
numpy — still runs.

One new detail worth carrying: **do not block all `ctypes.*` audit events.** `ctypes/__init__.py`
does `pythonapi = PyDLL(None)` at import, and numpy imports ctypes, so a blanket block breaks
every correct submission. Block `ctypes.dlopen` only when `args[0]` is truthy — `dlopen(None)`
is the interpreter's own handle.

---

## 5. Gate-by-gate log

### 5.1 Cycle 1 (`3ff2828`) — `ava_review` BLOCK, everything else green

Green first time: `changes` (static, 25/25), `review` (rubric **31/31, zero failures**),
`cosine_similarity`, `similarity` (**UNIQUE**; nearest TB3 `training-cluster-recovery` at 0.153,
instruction/verifier similarity 0.775/0.777 against a 0.9 threshold), `validation`
(Docker/Oracle/Nop), `ratelimit`, `pass2` (**0/2, both valid fails, 0 timeouts**),
`deep_review`, `pass2_suggestion` skipped by design.

**`ava_review` → BLOCK**, `sound_verifier` (§3.1), plus a `verifier_coverage` advisory (§3.2).

> Fixed in `502d6e5`: third shipped adapter with no reference, graded output moved to it,
> `artifacts` narrowed, two new tests, the `patboth` fixture deleted.

### 5.2 Cycle 2 (`502d6e5`) — everything green, `accepted`

Every gate PASS. `pass2` 0/2 again. `qc_eval`, `qc_exec`, `qc_gate` (44 checks,
`QC-BASE:502d6e57…`, `QC-FIXES-B64:W10=`), `tier1`, `deep_review`, `ava_review`, `gate`.
`trials` → **pass@5 0/5, avg@5 0.000, 5 good valid fails**.

Three independent pass@ measurements (pass@2 on `3ff2828`, pass@2 and pass@5 on `502d6e5`)
returned 0 solved with `approach_validity: PASS` throughout — the difficulty was robust to the
redesign, not an artifact of one roll.

### 5.3 The one advisory left unfixed, on purpose

Final AVA carried a non-blocking `sound_verifier` advisory: `compare()` has no dtype assertion,
so a float64 checkpoint passes the numeric comparisons (`np.allclose` upcasts). It is not
exploitable — `test_output_tensor_schema` checks dtype and would fail, so reward is still 0 —
and `container-dependency-resolver` §6 is explicit: **do not push cosmetic fixes onto a green
run**, every push re-rolls pass@2 and pass@5. Left for a future substantive commit if one comes.

---

## 6. Bugs I introduced myself

- **Handing the graded program the expected answer in its own input directory.** The first
  `run_merge()` did `shutil.copytree(case_dir, …)`, and each held-out case directory contains
  `expected.safetensors` and `case.json`. Caught before the first push by reading the staging
  code, not by any test. **Stage named files, never a directory, into anything the graded
  program is pointed at.**

- **A calibration probe invalidated by my own sandbox.** The first naive-implementation run
  reported all three failing *everything*, including the samples — which should have been
  impossible. Cause: the probe was `sys.path.insert(0,"/naive"); import naive`, and the guard
  correctly refused a non-stdlib import, so nothing ever ran. Inlining each naive into one file
  fixed it. `audit-build-context` §6 says it and it happened again: **check the diff is
  *structured* before concluding anything from it.** All-fail and all-pass are both smells.

- **`sed` patterns that silently did not match.** Repointing the mutant/naive runner scripts at
  the new output path used a `$`-anchored pattern against lines ending in `2>/dev/null`. Nothing
  matched, no error, and every mutant then "failed" `test_release_output` — including two that
  are provably equivalent. Two minutes of confusion over whether the equivalence analysis was
  wrong. **Grep the file back after any scripted edit; a no-op `sed` exits 0.**

- **Non-reproducible fixture regeneration.** Seeds came from `abs(hash(name))`, and Python
  randomises string hashing per process, so every regeneration produced different weights.
  Harmless (the fixtures are committed, and every generation was re-verified against real PEFT)
  but it makes diffs enormous and defeats "regenerate and confirm nothing changed". **Use an
  explicit integer seed table.**

---

## 7. Process rules

- **Never push while a check is in flight** — held throughout. Cycle 1's improvement was
  committed locally and deliberately *not* pushed while `pass2` ran; when `ava_review` later
  blocked, the fix and the improvement went out in one commit. One cycle spent instead of two.

- **Do not push a non-blocking improvement onto a green run.** The `patboth` fixture was ready
  and locally verified during cycle 1. Pushing it would have cancelled a live `pass2` for
  something no gate had asked for.

- **Squash unpushed history before pushing.** Cycle 1's local commit described *adding* the
  fixture that cycle 2 then removed. `git reset --soft` to the last pushed SHA and one honest
  commit; the pushed history describes what actually shipped.

- **Local git identity at clone time**, from `gh api user`
  (`<id>+<login>@users.noreply.github.com`). `audit-build-context` §3.3 cost a live pass@5 to
  learn this; it cost nothing here.

- **Never `git add -A` from the repo root** — always `git add -A task README.md`.

- **Sticky comments are edited in place.** The `needs-revision` label and the cycle-1 AVA BLOCK
  stayed visible well into cycle 2. Check `QC-BASE:` / `Ran on <sha>` against HEAD before
  believing any verdict.

- **`.dockerignore` in `task/environment/` from the first commit.** Static check passed first
  time.

---

## 8. Error → what to do, and what not to do

| Symptom | Do | Do **not** |
|---|---|---|
| `ava_review` `sound_verifier`: a graded artifact has a shipped reference | Add an input whose answer ships nowhere under `/app` and grade that one; assert the absence in a test | Delete the self-check — it is usually the amplifier that makes the task hard |
| A grader questions your reading of a library's behaviour | If the distinction is not load-bearing, delete the fixture that observes it | Argue it across cycles; two graders flagging it means a human will |
| Naive/mutant probe reports all-fail or all-pass | Check the harness before the task — a blocked import or a no-op `sed` looks exactly like this | Redesign a reference that was correct |
| Rubric says it could not execute your task | Nothing — `validation` already ran the oracle on the same SHA | Push a "clarification"; it re-rolls every stochastic gate |
| Non-blocking advisory on an accepted PR | Record it and leave it | Push a cosmetic fix over the commit pass@5 was measured on |

---

## 9. Checklist for the next task

Before writing code:
- [ ] Is the deciding rule a **published convention tied to a visible input**? Here: PEFT config
      fields, public semantics, open internet — `decisive_answer_discoverable` passed cleanly.
- [ ] Can ground truth come from **running the real tool**? If yes, do that.
- [ ] Count the independently-checkable consequences. Nine was comfortable; fewer than six and
      one lucky insight solves it.
- [ ] Write **three** plausible-wrong implementations. Require 0 sample diffs from all of them.
- [ ] **List every artifact the verifier grades, and for each ask: does its correct answer exist
      anywhere under `/app`?** If yes, the task is one `cp` from a partial bypass.

While building:
- [ ] Local git identity set from `gh api user` before the first commit.
- [ ] `.dockerignore` in `environment/`; no `tests`/`solution` in the Dockerfile.
- [ ] **No `"You have N seconds"` line.**
- [ ] Stage *named files* into anything handed to the graded program, never a directory.
- [ ] Audit hook for imports / native libraries / spawns — and let `ctypes.dlopen(None)` through.
- [ ] Explicit integer seeds for fixture generation.

Before every push:
- [ ] Oracle 1.0, nop 0.0, leak scan, and **the copy exploit** run against the real verifier.
- [ ] Mutation sweep; analyse each survivor, and say in the README why an equivalent one is
      equivalent.
- [ ] Root `README.md` reviewed against the *complete* diff being pushed, in the same commit.
- [ ] `gh pr checks` clean of `pending` before pushing.

---

## 10. One-paragraph version

The trap was a complete-looking self-check that is silent on the crux: two shipped LoRA adapters
whose merged checkpoints ship beside them, both plain LoRA, so the one-line merge everyone knows
reproduces them to the bit — while thirteen held-out adapters carry the nine PEFT mechanisms
that one line gets wrong. All five pass@5 agents validated against the self-check, saw zero
diff, and quit at 16–17 minutes of a 3600-second budget. The one blocking gate was `ava_review`
noticing that the self-check's answers were *also* the graded answers, making two criteria
passable by `cp`; the fix was not to delete the self-check but to add a third shipped adapter
with no reference anywhere and grade that instead. Ground truth came from running peft 0.20.0
under torch rather than porting it, which made every correctness question a diff and
pre-answered the read-only reviewer's one caveat. And when two graders questioned a
library-version detail in the pattern-key resolution, deleting the fixture that observed it beat
defending it — it cost no measured difficulty and ended the argument.
