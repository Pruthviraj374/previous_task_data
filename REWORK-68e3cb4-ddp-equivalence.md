# REWORK dynamo/ddp-equivalence — when three behavioral anti-cheat heuristics have each failed, stop iterating on behavior and change what a process can physically access

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all current-run checks green, `accepted` label. `pass@5 = 1/5 solved, 4 good-valid-fail, avg@5 = 0.200`. Not merged at write time. |
| **Repo** | `dynamo-68e3cb4-model-training-and-ml-infrastructure`, branch `rework-issue5-shard-isolation` (fork `Pruthviraj374/dynamo-68e3cb4-model-training-and-ml-infrastructure`) |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-68e3cb4-model-training-and-ml-infrastructure/pull/6, rework for issue [#5](https://github.com/handshake-project-dynamo/dynamo-68e3cb4-model-training-and-ml-infrastructure/issues/5) (supersedes [#2](https://github.com/handshake-project-dynamo/dynamo-68e3cb4-model-training-and-ml-infrastructure/issues/2)) |
| **Category / sub** | Model Training and ML Infrastructure / Distributed training (pre-seeded, unchanged) |
| **Final commit** | `2950e4e` |
| **Commits** | 1 |
| **Files touched** | 8: `README.md`, `task/environment/Dockerfile`, `task/environment/_refcore.pyx`, `task/environment/train_dist.py`, `task/instruction.md`, `task/solution/train_dist_fixed.py`, `task/task.toml`, `task/tests/test_outputs.py` |

## The pattern this task completes: three behavioral heuristics, then a structural fix

This task's `sound_verifier` finding has now been through four verifier designs across two
review rounds, and the sequence is the actual lesson:

1. **Original delivery**: self-reported per-rank sample count. Removed — fabricable by a process
   holding the whole dataset.
2. **PR #3 (closed, unmerged)**: checked each worker's `/proc/<pid>/cmdline` for `"train_dist"` or
   `"multiprocessing"`. Trivially spoofable (any decoy can match a string) and never merged.
3. **PR #4 (issue #2, closed as superseded here)**: a per-worker CPU-share bar, then a
   peer-established-TCP-socket check (require `world_size` grader-owned sockets seen
   `ESTABLISHED` to another grader-owned socket). This passed Tier1/QC/AVA and even reached
   `pass@5 = 1/5` once, but issue #5's adjudication showed the exact hole predicted by its own
   docstring's caveat: a rank can **honestly** join the process group and hold a live peer socket
   — satisfying the check — while a single rank does all the real computation and the rest merely
   participate in collectives without ever touching real per-rank data.
4. **This PR (issue #5)**: per-UID shard isolation. The verifier itself launches `world_size` OS
   processes, one per rank, each as its own unprivileged user (`grader0`..`grader3`), each handed
   only its own `chmod 0600`, individually-owned shard (row `i` → rank `i % world_size`). No
   rank's process can open another rank's shard — a filesystem permission fact, not a runtime
   signal, so it cannot be satisfied by *any* process behavior, honest or decoy.

**The generalizable lesson**: every prior design tried to *infer* real distributed computation
from something a process does at runtime (a self-report, a cmdline string, CPU share, a socket).
Every one of those is a **behavior**, and a sufficiently informed submission (or a red-team
constructing a bypass) can always replicate the behavior without doing the underlying work,
because behavior and the property being checked for are only correlated, not identical. The fix
that actually closed it is not a better heuristic — it is removing the *premise* every heuristic
depended on (a single process ever having the full dataset) via an OS-level access control that
holds regardless of what any process does. This generalizes
[[dynamo-late-branch-vs-structural-crux]]: a check bolted on after the fact (any behavioral
signal) gets defeated; a constraint enforced by the pipeline's own first step (the verifier
decides what each process can even open, before it runs) cannot be.

## Isolating the data is necessary but not sufficient — the collective-API denylist

Per-UID shard isolation alone still has a hole: nothing stops a rank from *voluntarily* handing
its shard to another rank over a genuine `torch.distributed` collective — `all_gather_object`
would reconstruct the full dataset in one process, honestly, using only the framework's own
public API. This was reasoned out and fixed *before* pushing (not found by AVA), by disabling the
bulk-data-moving collective functions (`all_gather`/`gather`/`scatter`/`broadcast`/`send`/`recv`/
`all_to_all` and variants) in the graded process, leaving `all_reduce`/`barrier`/
`init_process_group`/`destroy_process_group` untouched.

**First attempt at this was an allowlist (deny everything not explicitly needed) and it broke the
oracle**: `torch.optim.SGD.__init__` lazily imports `torch._dynamo` on first construction (for
compile support), which imports a long chain ending in `torch.testing._internal.distributed.fake_pg`
defining `class FakeStore(dist.Store)` — a class the allowlist had already replaced with a plain
deny-function, since `Store` is callable and wasn't in the allowed set. The failure mode was a
cryptic `TypeError: function() argument 'code' must be code, not str` from Python trying to use a
function object as a class base. **Fix: switch to a narrow denylist of only the specific bulk-data
functions**, leaving every class (`Store`, `ReduceOp`, `Backend`, ...) and everything else torch's
own import graph might reach for untouched. A denylist is less theoretically complete than an
allowlist but is what actually survives contact with a large library's own internal lazy imports —
confirmed by running the oracle locally (`harbor run -p . --agent oracle`) immediately after
writing the guard, before ever pushing.

**AVA's own advisory findings (non-blocking, did not gate this PR) independently found the same
class of residual gap**, worth recording since a future rework on this task will likely need to
close it: (1) `all_reduce` itself is unrestricted in tensor size/call count, so a submission could
in principle disguise a raw-data payload as an oversized or superfluous `all_reduce` call — this
is the *same* covert-channel problem one level down, since `all_reduce` genuinely needs to stay
available for gradients; (2) the denylist enumeration is not exhaustive (`new_group`,
`monitored_barrier`, `all_reduce_coalesced` are absent). Left unfixed here because both are
advisory-only (`AVA verdict: PASS`) and this repo's own history (`REWORK-845764f-morrowlens-exposure`)
already established that editing an agent-visible surface after a PR is otherwise accepted risks
an unnecessary full pass@ re-run for no required gain — but a future round should either shape-check
`all_reduce` against known model-parameter tensor shapes, or accept and document the gap explicitly
(as this PR already does for raw-socket/private-internals exfiltration, a materially more
contrived attack than the ones actually seen in this corpus).

## Preserving exact-to-1e-8 equivalence under a forced re-partition

Switching from "each rank can see the whole dataset and slice an arbitrary contiguous range of a
shuffled batch" (the pre-existing, accepted algorithm) to "each rank only has row `i` where
`i % world_size == rank`" required re-deriving the distributed reduction, not just relocating
code. The insight that made this a mechanical, zero-risk change rather than a new numerical
design: **the reference's per-batch loss is a sum over the batch's rows divided by a global
constant (the batch's weight sum); summing over *any* partition of those rows and combining via
`all_reduce(SUM)` is exactly the same value, regardless of which rows go to which rank** — the
former partition (contiguous position within the shuffled batch) and the new one (row index modulo
world_size) are just two different, equally valid decompositions of the same sum. Concretely: every
rank independently derives the same global permutation (same seed, and `n_total` obtained via a
real `all_reduce` of local shard sizes rather than read from a file), filters each batch window to
`idx % world_size == rank`, and looks up `idx // world_size` in its own shard. Confirmed empirically,
not just algebraically: `harbor run -p . --agent oracle` still lands every scenario within 1e-8 of
the reference (same ~1e-15 margin as before) on the first attempt.

## Gate cycle

- **First pass@2**: `0/2 passed`, both trials landed as `in-progress-timeout` (`low_timeout: FAIL`
  both) — one trial never broadened its synthetic probes past feature-7 < 2.0 (a reasoning miss,
  reproducing the task's own documented trap), the other found the crux and implemented it
  correctly but hit an untested empty-shard edge case (a non-differentiable `torch.zeros()` giving
  `p.grad = None`, crashing `all_reduce`) before reaching multi-rank validation. The automated
  difficulty-suggestion bot recommended raising `[agent].timeout_sec` 3600→5400-7200. **Not done**:
  this repo's own PR #4 history had already established that raising the budget on this exact
  block class (agent still actively, productively working at cutoff) converts near-misses into
  solves rather than into decisive valid fails — the near-miss trial here needed only a few more
  minutes to self-correct, which is exactly the scenario where more time helps the *wrong* side of
  the pass@ arithmetic. `gh pr close`/`gh pr reopen` with no content change instead, per the
  established remedy for an in-progress-timeout block
  (`REWORK-e843ed4-vault-salvage-round2.md`, `REWORK-845764f-morrowlens-exposure`).
- **Second pass@2**: `1/2 passed` (one valid failure) — accept, proceeded to Automated Review.
- **Automated Review / AVA**: both `PASS` on the first attempt, with the three advisory findings
  discussed above.
- **Tier-1 fix-addressal**: both findings (`RW5F1` sound_verifier, `RW5F2` protected_ground_truth)
  materially addressed on the first check, citing the exact files/mechanisms above.
- **QC Tier 2**: `37 checks passed` clean on the first attempt.
- **pass@5**: `1/5 solved, 4 good-valid-fail, avg@5 = 0.200` — accept band, no difficulty knob
  touched. Failures stratified across the task's own documented traps (narrow probe range never
  crossing the threshold; correct weighting recovered but the wrong feature column inferred on a
  wider-export scenario) — no task/verifier defect flagged in any trial.
- **Closing the issues**: both `gh issue close` calls failed with `does not have the correct
  permissions to execute CloseIssue`, confirming `REWORK-2ee102a-sonarscope-contact-repair`'s
  prediction for a fork contributor. Posted a completion comment on each (checking off both
  findings on #5 by name, and noting #2 is superseded) instead, per that file's precedent and
  `rework-rule.md` §1/§4's "may need a manual comment" guidance.

## What this confirms for the next rework that hits a spoofable anti-cheat check

Before writing a fourth heuristic on a `sound_verifier` finding, check whether the finding is
really about *inferring an internal process property from external behavior* (self-reports, CPU
share, socket presence, cmdline strings) — if so, no heuristic closes it completely, because
behavior and the underlying property are only correlated. The question to ask instead is: what
access can the verifier grant or withhold, structurally, before the submission ever runs, such
that the dishonest path is not just discouraged but physically impossible? On this task that was
per-UID file permissions; on a different task it might be a different resource axis (network,
memory, a cryptographic capability) — but the shape of the fix is the same: move the constraint
from "checked after the fact" to "enforced by construction."
