# dynamo/consolidate-zero-checkpoints — a real library's two layouts, one of which the sample can't show

| | |
|---|---|
| **Outcome** | **ACCEPTED** — 16 checks green, `accepted` label, two commits total |
| **Repo** | `dynamo-f4b9eeb-model-training-and-ml-infrastructure`, branch `submission`, fork `Pruthviraj374` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-f4b9eeb-model-training-and-ml-infrastructure/pull/1 |
| **Category / sub** | Model Training and ML Infrastructure / **Checkpointing and resumption** (second task in this sub-category; `checkpoint-resume-plan` was the first) |
| **Benchmarked model** | `task.toml` declares Opus-4.8 / Terminus-2; stickies call it "Model A". The one passing pass@5 trial's own transcript self-identified as `terminus-2/deepseek-v4-pro` — same unreliable-model-identity signal `replay-rollout-gae` recorded. Don't design around it |
| **Final commit** | `ba1cae9` |
| **Headline** | **pass@5 = 1/5 solved, avg@5 = 0.200, 4 good-valid failures, 0 soft-timeout, 0 task/verifier issues.** pass@2 0/2 on push 1, 1/2 on push 2. Rubric 31/31 both pushes. One blocking gate in the whole run (`qc_gate` C3) |

Two content pushes, roughly six hours end to end, most of it spent building fixtures rather
than arguing with gates. The transferable parts are §2 (why this crux survived where
`replay-rollout-gae`'s three disclosure rounds did not), §4 (the one gate failure — an
unreachable branch, and why *making it live* beat deleting it), and §5, which is the most
interesting thing this task produced: **four agents built their own synthetic test data,
self-validated against it, and the bug stayed invisible** — the no-self-check amplifier
holding even when the agent manufactures its own checker.

---

## 1. What the task asks

A training platform is retired along with the service that consolidated its sharded
checkpoints. The agent writes `/app/consolidate.py`, invoked
`python3 /app/consolidate.py <checkpoint_dir> <out_dir>`, which rebuilds the model's
full-precision weights and writes `weights.bin` (little-endian binary32, row-major, any
order) plus `index.json` (per tensor: shape and byte offset).

- **Agent sees:** `/app/data/CHECKPOINT.md` (the container) and one complete checkpoint at
  `/app/data/checkpoints/step-4200/`. **No expected output ships anywhere.**
- **Graded on:** fifteen held-out checkpoints, plus the shipped one re-run against the
  verifier's pristine copy, plus a content-hash tamper check on `/app/data`.
- **Constraint:** standard library only, no network, no child processes.

### The archive is a transcription of a real DeepSpeed checkpoint, not an invented format

This is the whole design. The checkpoints are byte-for-byte what DeepSpeed writes for a
ZeRO-sharded job — the pickled payloads rewritten as flat `.bin` files and the state dicts
as JSON, with every key name, file name and payload ordering preserved (`mp_rank_00_model_states`,
`zero_pp_rank_<r>_mp_rank_00_optim_states`, `single_partition_of_fp32_groups`,
`fp32_flat_groups`, `param_shapes`, `frozen_param_shapes`, `frozen_param_fragments`,
`shared_params`, `buffer_names`, `partition_count`, `zero_stage`). `CHECKPOINT.md` says so
explicitly and names the authority, so discoverability gates have no purchase; the
converter DeepSpeed drops into every checkpoint directory is simply not part of the archive,
and DeepSpeed is not installed.

The transcription is what makes this buildable without torch: no pickle, no 1 GB image,
tensor payloads as raw little-endian floats a stdlib solver reads with `array`/`struct`.
**Consider this move for any task whose crux lives in a real binary format's semantics
rather than its serialisation** — you keep the real authority and drop the dependency.

---

## 2. The crux, and why it survived where disclosure-tuning failed elsewhere

`CHECKPOINT.md` documents the container exhaustively and says nothing about how a rank's
partition maps back onto parameters — because that is **not a property of the container**.
It is a property of the ZeRO stage:

- **Stages 1 and 2.** Each parameter group is flattened whole and cut into
  `partition_count` contiguous slices, one per rank. Concatenate the ranks in rank order,
  let *that group's* parameters consume the result in `param_shapes` order, leave the
  alignment padding unread at the end.
- **Stage 3.** Each *individual parameter* is cut into `ceil(numel / partition_count)`
  slices, padded to a whole number of elements per rank, and each rank stores its slice of
  every parameter back to back. Take one slice from each rank at a shared running offset
  that walks the groups merged into one sequence, concatenate, trim that parameter's tail
  padding.

The two gathers return **completely different numbers, silently, at exactly the right
shapes, from exactly the right byte count.**

Ten further real behaviours compound it: natural vs lexicographic rank-file ordering
(diverges only at ≥10 ranks), `partition_count` recorded per group rather than as a scalar,
`stage <= 2` vs `stage == 2` for the key, frozen parameters (whole at stages 1–2, one
fragment per rank at stage 3), tied parameters with no partition of their own, and bf16
buffers that must be widened.

**The invariant:** the shipped checkpoint is stage 2, four ranks, one parameter group,
nothing frozen, nothing tied, no alignment padding, fp32 — the single configuration in
which all thirteen wrong readings reproduce it *element for element*.

### Why this one held

`replay-rollout-gae` (same category) burned three rounds proving that for this model,
*"state the fact, let the reader derive the one-step consequence"* survives but *"state the
resolution"* gets implemented verbatim — and that a convention it already knows cold gets
recalled regardless of wording. `20141f7` established the sharper filter: **derivability,
not obscurity**. Cruxes mathematically derivable from disclosed definitions got solved 2/2
four times running; an arbitrary real-world encoding convention did not.

This crux passes that filter cleanly. The stage-3 layout is **not derivable from a stage-2
sample by any amount of reasoning** — it is an arbitrary engineering decision DeepSpeed
made, recoverable only from knowing (or reading) DeepSpeed. And unlike `lumenp`'s BMP row
padding, it is **conditional**: it fires only at stage 3, so there is a judgement to get
wrong. Real + conditional + unstated + non-derivable is the combination; three out of four
is not enough.

---

## 3. Gate-by-gate log

| # | Commit | Gate | Verdict | Cause | Fix |
|---|---|---|---|---|---|
| 1 | `9cfeca8` | `changes`, `cosine_similarity`, `review` (31/31), `similarity`, `validation`, `ratelimit`, `pass2`, `deep_review`, `ava_review`, `tier1`, `qc_eval`, `qc_exec` | all PASS first try | — | — |
| 2 | `9cfeca8` | `pass2` | **PASS — 0/2**, `Rerun Recommended: NO`, all 7 per-trajectory criteria PASS on both trials | — | — |
| 3 | `9cfeca8` | `qc_gate` | **BLOCK — C3 "Narrow / Hardcodable Held-Out Coverage"** | The bfloat16 decode branch was dead; QC mutated it and the verifier still paid 1.0 | Made the branch live rather than deleting it (§4) — `ba1cae9` |
| 4 | `ba1cae9` | everything, including `qc_gate` (37 checks + probes clean) | all PASS | — | — |
| 5 | `ba1cae9` | `trials` | **PASS — 1/5 solved, avg@5 0.200, 4 good-valid fails** | — | — |

`review` scored **31/31 with zero failures on both pushes**, including after the second
push rewrote a sentence in `instruction.md` and three `task.toml` explanations.
`cosine_similarity` headroom was comfortable and stable: instruction 0.756, verifier 0.789,
fingerprint 0.810 against a 0.90 block. The closest TB3 candidate,
`mp-checkpoint-consolidation`, shares the *framing* (a distributed run left shards, the
tooling is gone) and was still ruled UNIQUE because the mechanism differs — Megatron
TP/PP/EP splitting under PyTorch/safetensors graded on logit equivalence, versus ZeRO
partition semantics graded byte-exact. **Framing overlap with a TB3 task is survivable;
mechanism overlap is what the gate bites on.**

---

## 4. The one blocking gate: an unreachable branch, and the fix that beat deletion

`qc_gate` C3 mutated the bfloat16 decode in `solution/consolidate.py` — putting each word
in the *low* half of the binary32 word instead of the top, so bf16 `0x3F80` decodes as
2.28e-41 instead of 1.0 — ran the full verifier, and **the submission still scored 1.0.**

The diagnosis was immediate and is worth internalising: **the branch was dead.** `bfloat16`
appeared only on `module` records for *trainable parameters*, and the correct answer never
reads those — trainable parameters come from the optimizer's fp32 masters. The bf16 records
existed purely as a realistic decoy.

`read-cavity-captures` §5 says the remedy for an untested branch is to measure whether a
fixture can gate it at a realistic value, and delete the branch if not. **Here a third
option was better: make the branch live.** A job that trains in bf16 casts the *whole
module, buffers included* — which is exactly why DeepSpeed's own `parse_model_states`
widens buffers with `.float()`. So the bf16 fixtures now record their buffers in
`bfloat16`, putting the widening on the graded path, and `h15_bf16_buffers` isolates it at
stage 2 where nothing else is unusual. Two mutants were added — `bf16_low_half`
(reproducing QC's own mutation) and `bf16_untouched` — both inert on the shipped
checkpoint, both caught.

**Deleting would have removed a real behaviour to satisfy a coverage metric; making it live
added an axis and closed the hole.** Prefer that ordering when the dead branch corresponds
to something the real system actually does.

The same pass swept three more branches nothing exercised, before they became round two's
finding: the `sys.byteorder` swaps (hosts are little-endian), the `or {}` defaults on
`frozen_param_shapes`/`shared_params` (both keys are always written), and the
`if source in result` guard on tied parameters (the source is always present). **Audit for
these before pushing, not after** — `replay-deposit-ledger` §4.1 warns C3 recurs if you
patch only the named case, and every one of these was the same shape as the finding.

**Proving the fix, the right way.** Local calibration through `tools/mutation_matrix.py`
was not sufficient evidence: my `bf16_low_half` lives in `tools/reference.py`, a *different*
implementation from the one QC patched. So I applied QC's exact edit to
`solution/consolidate.py` itself and ran the real verifier: 0.000, where it had been 1.0.
**When QC names a file and a line, reproduce the mutation in that file, not in your mutant
harness's equivalent.**

### The instruction sentence the fix invalidated

`instruction.md` said *"every value is already an fp32 number sitting somewhere in the
checkpoint."* Making buffers bf16 turned that into a false statement — the "no uncorrectable
lie" fairness line. It was rewritten to *"none of them has to be computed: each is already
recorded in the checkpoint, in the dtype its own record declares."* **A QC fix that changes
what the data holds can silently falsify a sentence in the instruction; grep the
agent-visible prose for claims about the data after every data change**, along with
`task.toml`'s three explanations (`sweep-replay` §6).

---

## 5. What pass@5 actually showed — the most transferable finding here

**Four of five trials failed on exactly one decision point**, and the analyzer's summary is
worth quoting because it names a failure mode this corpus has not recorded before:

> *All four agents self-validated Stage 3 with synthetic checkpoints they constructed. Those
> synthetic checkpoints did not reproduce the per-parameter interleaving pattern, so the bug
> was invisible during self-testing.*

This is the **no-self-check amplifier surviving the agent's own attempt to build a check.**
The agents did the responsible thing — no shipped answer existed, so they manufactured test
data — and it did not help, because the data they generated encoded the same wrong mental
model as the code they were testing. A self-test written from a misunderstanding validates
the misunderstanding.

**Design consequence:** withholding expected outputs is stronger than it looks. It does not
merely remove a checking opportunity; against a crux about *how bytes are laid out*, it
makes any self-generated check circular by construction. This works specifically because
the layout is the thing in dispute — an agent cannot generate a fixture in a layout it does
not know. Expect it to transfer to any format/encoding crux, and **not** to transfer to
cruxes about algorithm behaviour, where an agent can test properties without knowing the
answer.

Two more observations from the run:

- **`strict_length_check` fired live.** One trial (`task__Ypk77rf`) added a strict equality
  guard raising `RuntimeError` when bytes remained after consuming a group's parameters —
  the exact mutant I had invented to give `h02_stage2_padding` something to catch, after
  calibration flagged that fixture as catching nothing. It cost that trial two extra test
  failures. **When calibration says a fixture catches nothing, the fix is to find the real
  mistake it guards, not to delete the fixture** — mine turned up in a live trial three
  hours later. (Contrast `read-cavity-captures` §6, where believing the table and deleting
  was right; the difference is whether you can name a plausible engineer who writes it.)
- **`test_bf16_buffers` passed in every trial.** The axis added to satisfy `qc_gate` did not
  gate anything. That is fine and expected — it was added to close a coverage hole, not to
  discriminate. Don't confuse the two jobs a fixture can have.

### The disclosure line that invited the wrong inference

All four failing agents read `CHECKPOINT.md`'s

> `fp32_flat_groups` | the same thing at ZeRO stage 3, where DeepSpeed writes it under this key instead

as "same structure, same algorithm." The sentence is *true* — it is the same thing, the fp32
master partitions — but "the same thing … under this key instead" reads as though only the
key changed. I did not touch it, because it produced the accepted result and because the
statement is accurate rather than misleading (the layout is documented publicly under the
name the file gives you).

**Recording it as a live lever, not a defect:** if a future task in this family runs too
easy, tightening that phrase toward "DeepSpeed writes this key at stage 3" — dropping "the
same thing" — would remove the invitation. Conversely, if a task runs too hard, a phrase of
that shape is a cheap way to soften without disclosing anything. `motion-register` §4 found
the mirror image (a data-shape guarantee read as permission) and it became that task's
strongest trap.

---

## 6. What worked

1. **Real, conditional, unstated, non-derivable.** All four properties, not three. The stage
   test — a rule that fires for *some* checkpoints — is what `lumenp` §6's BMP row padding
   lacked.
2. **Breadth of genuinely real mechanisms under all-or-nothing grading**, matching
   `merge-lora-adapters` (nine) and `replay-rungear-runs` (ten). Eleven here at the first
   push, thirteen after QC. Every one is DeepSpeed's documented behaviour; none is invented.
3. **Byte-exact grading with no tolerance at all**, because the reconstruction is copying
   plus an exact widening — no arithmetic anywhere. `lumenp` §6 recommends reaching for an
   integer-only pipeline where one exists; a copy-only pipeline is the same idea taken
   further, and it deletes the entire tolerance/rounding argument class. The analyzer
   confirmed it works as intended: *"the deviations are not near-misses; the wrong gather
   reads from structurally unrelated positions."*
4. **Ground truth planted by the generator, then round-tripped.** `gen_fixtures.py` plants
   the weights, derives the partitions, reads each checkpoint back through
   `tools/reference.py` and asserts equality with what was planted — so a fixture and its
   answer cannot drift. Three independent implementations (generator, `tools/reference.py`,
   the verifier's own `_reference_consolidate`) agreed on all sixteen checkpoints before the
   first Docker cycle. This also satisfies `reviewable`'s "derived, not hardcoded."
5. **`-S` rather than `-I` to enforce stdlib-only.** `-S` drops site-packages, so nothing the
   agent pip-installed (DeepSpeed included) is importable, while the program's own directory
   stays on `sys.path` so a two-file solution still works. This threads
   `replay-deposit-ledger` §6 (`-I` alone is insufficient) and `nfs4-access-audit` §4.4
   (`-I` breaks multi-file solvers) simultaneously. Documented in the README so a reviewer
   sees it was deliberate.
6. **Shipping no expected output at all**, per `sweep-replay` §5.1 and `replay-rollout-gae`
   §4.5 — and §5 above is the strongest evidence yet for it.

---

## 7. Reusable checklist

Before writing code:
- [ ] Score the crux on **all four**: real, conditional, unstated, non-derivable. Three is
      not enough — `lumenp` died on conditional, `20141f7` on derivable.
- [ ] If the crux is a real binary format's *semantics*, consider transcribing the container
      (pickle → JSON + flat `.bin`) to keep the authority and drop the dependency. State the
      transcription plainly in the agent-visible doc.
- [ ] Name the authority in the agent-visible doc. It costs no difficulty (measured twice in
      this category) and pre-empts every discoverability finding.

Before every push:
- [ ] **Audit the reference for branches nothing exercises** — `or {}` defaults on keys
      always written, byteorder swaps, `if x in y` guards where `x` is always present,
      `raise` arms for values the spec forbids, and any dtype/enum the correct path never
      reads. This is `qc_gate` C3 waiting to happen, and it was the *only* gate that blocked
      this task.
- [ ] A dead branch that mirrors real behaviour should be made **live**, not deleted.
- [ ] After any change to what the data holds, grep `instruction.md` and `task.toml`'s three
      explanations for claims about the data that the change falsifies.
- [ ] Oracle 1.000, nop 0.000, `calibrate.py`, `mutation_matrix.py` — all four, after fixture
      edits as well as code edits.
- [ ] When a gate names a file and a line, **reproduce its mutation in that file** and run
      the real verifier. A same-shaped mutant in your dev harness is not the same evidence.
- [ ] Check `gh api .../check-runs` for anything `in_progress` before pushing.

When a gate result looks like a verdict but might not be:
- [ ] Check `https://www.githubstatus.com/api/v2/status.json` first. This task was built
      through a **critical GitHub Actions outage** (2026-08-26 15:11–18:01 UTC, database
      primary failover + Vitess throttling). The correct response was to change nothing:
      no push, no empty commit, no `gh pr close`/`reopen` (`replay-rungear-runs` §8.1 —
      cycling into a live outage reproduces the fault). The queue drained on its own and
      every gate ran normally. **Total cost of the outage to this task: zero.**

---

## 8. One-paragraph version for future me

The crux was DeepSpeed's two ZeRO gathers — stage 1/2 slices a whole flattened parameter
group per rank, stage 3 slices every individual parameter per rank with its own padding —
and the shipped checkpoint was a stage-2 job in the one configuration where all thirteen
wrong readings reproduce it element for element. It cleared every gate on the first push
except `qc_gate`, which found the single real defect: the bfloat16 decode branch was
unreachable, because bf16 only ever appeared on module records the correct answer never
reads. The fix that worked was making the branch live rather than deleting it — a bf16 job
casts its buffers along with its parameters, which is why DeepSpeed widens buffers with
`.float()` — which added an axis instead of removing a behaviour, and I proved it by
applying QC's own mutation to the actual file it named rather than to my mutant harness's
equivalent. The most valuable thing the run produced was in the pass@5 analysis: four
independent agents built their own synthetic stage-3 checkpoints, self-validated against
them, and the bug stayed invisible, because data generated from a wrong mental model
confirms that model — which is the strongest argument this corpus has for shipping no
expected output when the crux is about how bytes are laid out. Accepted at 1/5 with four
good valid failures, all four on the same single decision point.

---

## 9. Pointers

| Thing | Where |
|---|---|
| Reference solution | `task/solution/consolidate.py` (stdlib only, ~150 lines) |
| Verifier + independent reference + sandbox | `task/tests/test_outputs.py` (`_reference_consolidate`, `_drop_privileges`, `_stage`) |
| Held-out fixtures (15 checkpoints) | `task/tests/fixtures/h01…h15/` |
| Shipped checkpoint | `task/environment/data/checkpoints/step-4200/`, `task/environment/data/CHECKPOINT.md` |
| Generator / calibration / mutation sweep | `task/tools/{gen_fixtures,reference,calibrate,mutation_matrix}.py`, documented in `task/README.md` |
| Design writeup + design history | repo-root `README.md` |
| Upstream authority | `deepspeed/utils/zero_to_fp32.py` — `_get_fp32_state_dict_from_zero2_checkpoint`, `_get_fp32_state_dict_from_zero3_checkpoint`, `zero3_partitioned_param_info` |
| Key commits | `9cfeca8` task submission · `ba1cae9` bf16 branch made live, accepted |
