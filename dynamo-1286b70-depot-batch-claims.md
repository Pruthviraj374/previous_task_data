# dynamo/depot-batch-claims — a rule the spec yields is not a stump; a rule the platform defeats is

Repo: `dynamo-1286b70-debugging-and-repair`, PR #4, branch `submission`, fork `Pruthviraj374`.
Category: **Debugging and Repair** / Sub-category: **Concurrency and synchronization debugging**.
Benchmarked against `Model A` via Terminus-2.

**Accepted 2026-08-22 at commit `4d17657`. pass@5 = 0/5 solved, avg@5 = 0.000, 5 good valid
failures, 0 soft-timeout, 0 task/verifier issues, 0 reward hacking.** Every gate green.

Four pushes. The second task in this playbook for *Debugging and Repair*, after
`repair-portal-dispatch`, and it converges on the same conclusion from the opposite direction.

Commits: `ae60760` initial · `e926a4a` deciding rules moved off the lock semantics ·
`07bb447` two `qc_gate` findings closed · `4d17657` two platform-convention axes added (accepted).

---

## 1. The task

Several `scanhand` worker processes share one spool directory. A batch belongs to whichever
process holds an exclusive POSIX record lock on that batch's `claim.json`. The worker has
drifted from the site's written protocol and batches are being run twice.

- **Agent sees:** `/app/depot/scanhand.py` (broken, the only graded artifact),
  `/app/depot/CLAIMS.md` (the complete normative protocol), `/app/tools/sweep.py`,
  `/app/tools/scanctl.py`, and a runnable twelve-case check under `/app/checks/`.
- **Agent produces:** the repaired `/app/depot/scanhand.py`.
- **Graded on:** 16 pytest cases, each building a throwaway spool outside `/app` and running
  the agent's worker as `nobody`. Judged on files left in the spool, the line count of a
  stand-in driver's own start log, and lock observations taken **by a separate process**.
- **Graded values:** counts, exact JSON fields, `FREE`/`HELD`. No tolerances anywhere.

---

## 2. The crux — and the correction that made it work

> **A rule a careful reader derives from your spec is not a stump. A rule whose faithful
> transcription is defeated by a silent platform default is.**

This is `repair-portal-dispatch`'s finding ("the tool's own silent defaults as the crux, with
every rule disclosed") arrived at the hard way, by first building the other kind and watching
the model solve it.

Nine mechanisms, all real, all disclosed in `CLAIMS.md`, all silent:

1. reopening the claim path and closing that descriptor releases **every** record lock the
   process holds on the file;
2. temp-file-plus-`os.replace` leaves the lock on an orphaned inode;
3. record locks do not exclude **threads** of one process, so a multi-slot worker is granted
   the same batch several times by the kernel;
4. ownership is the lock, never the recorded `pid`/`state`/`heartbeat_at`;
5. a 64 KiB pipe: `Popen(stdout=PIPE)` + `wait()` works on every sample batch and blocks
   forever, claim lock held, once a batch has enough sheets to fill it;
6. a claim file that does not parse — which the protocol's own create-then-lock-then-write
   sequence guarantees exists — must be treated as carrying no record;
7. **the mode passed to `open()` is only a request**: `0664` arrives as `0644` under the
   default umask, and the rule needs an explicit `fchmod`;
8. **a signalled death is a negative number only to Python**: `wait()` returns `-15` where a
   shell reports the 128-plus-signal form;
9. **stopping an attempt means stopping what it started**: a leftover helper keeps the
   driver's output stream open, so the owner's read never ends and the attempt is *never
   recorded at all*.

### Invariants that make it work

1. **A complete-looking self-check that is blind to every deciding axis.** Twelve shipped
   checks. Measured: **six wrong repairs score 12/12 on them and still fail graded.**
2. **Equivalence, not omission.** Sample batches are 1–4 sheets (both readings of the pipe
   agree), every sample worker runs under one account (both readings of the mode agree), no
   sample driver is ever signalled or starts a helper.
3. **Grade the decision, never the representation.** Which signal stops a wedged attempt is
   not graded — only that the status is recorded the way a shell reports one. Both readings
   were measured at 16/16.
4. **Two structurally different correct implementations pass everything** (temp-file capture;
   abrupt stop), so the verifier cannot be enforcing the reference's shape.
5. **Lock state measured out-of-process.** The verifier's own descriptors would otherwise
   destroy the very lock it is measuring — the same semantics the task is about.
6. **Assertions taken at moments the verifier chooses** (gate files), not after sleeps.

---

## 3. Dead ends and corrections

**(a) The first design's cruxes were derivable from the spec, and the model derived them.**
pass@2 returned **2/2 solved**. The analysis was unusually direct: both agents produced all
three lock mechanisms — one in a *single rewrite at step 8* — and *"the CLAIMS.md specification
was sufficiently precise that the bugs were deducible from the spec alone, rather than from
training-data memorization."*

This is the single most transferable finding here, and it sharpens `31`–`34`'s general advice:
**precision in your spec is not safety.** A spec good enough to be unambiguous is also good
enough to be reasoned from. The axes that finally held (7, 8, 9) are ones no amount of reading
`CLAIMS.md` produces, because they live in the platform, not the protocol.

**(b) I enumerated the graded scenarios in `instruction.md`.** The closing paragraph stated the
scope and then listed it — several workers, multi-slot, killed workers, held claims. A pass@2
trial went **straight to the listed case**. Replaced with one flat sentence; the scope it needs
is already normative in `CLAIMS.md`. Same failure as `replay-strata-plans` §3.2, in a new form:
the register of the sentence, not its scope, is what hands the crux over.

**(c) My shipped checks advertised their own gaps.** The first check set had no multi-worker and
no multi-slot case at all — which names those as the untested areas. Added both, built to stay
green under every wrong repair.

**(d) pass@2 passing then failing on a strictly harder tree is variance, not regression.**
Push 2 passed; push 3 was strictly harder and returned 2/2 solved. Two trials against a solve
rate near 50% do that. Fourth confirmation of `rebuild-readout-builder` §3.1 — **0/2 and 2/2 are
both weak evidence at that rate.** Do not redesign on one pass@2 sample; read the *fail reasons*
instead, which is what actually identified (a).

**(e) The one failure common to both pass@2 trials was an ambiguity of mine.** Both agents got
the intended convention right (128+N) and differed only on *which signal* — `proc.kill()` (137)
against the reference's `proc.terminate()` (143). `CLAIMS.md` said "terminates the driver",
which does not choose. The grader called it *"a single peripheral detail"* and `near_miss`
FAILed on both trials.

**This was caught by reading a passing gate's detail, not a failing one.** pass@2 had *passed*.
The fix — accept either signal's shell form, keeping the decision and dropping the arbitrary
part — removes the discriminator that produced 100% of those failures, so the same push had to
add axis 9 or the task would have been genuinely thin. Generalises: **when a gate passes, read
why. A pass earned by an ambiguity is a reviewer rejection with a delay on it.**

**(f) Two stale calibration mutants nearly produced two wrong conclusions.** One removed a
reader thread but left its `reader.join()`, dying with a `NameError` and "failing" everything —
indistinguishable from a caught trap. Another was built against a superseded reference and
failed for an unrelated reason. Every variant is now checked to **compile *and* start cleanly**
before its number is believed. This is `nfs4-access-audit` §4.3 confirmed in a second form.

**(g) A `re.sub` replacement mangled the mutation table.** `\n` in the replacement string was
interpreted, producing an unparsable audit script. Build such tables with `json.dumps` or a
lambda replacement, and assert **every anchor is present in the reference** before running.

---

## 4. What the model actually did (pass@5, 0/5)

Five good valid failures, avg@5 = 0.000. The pass@2 trials on the accepted design are the
clearest record of the mechanism: the axes that gated were the ones living in platform
behaviour, and the agents that failed had *correctly implemented the protocol as written*.

Worth recording from the earlier round: one agent **correctly diagnosed the per-process lock
problem at step 12 and ran out of budget before it could land the fix**, having spent ~35
minutes inside a single generation step. Difficulty that arrives late in a long rewrite is
partly a budget race, which is a reason to keep the *visible* repair surface small.

---

## 5. Gate log

| Push | Gate | Result |
|---|---|---|
| `ae60760` | static, rubric 31/31, duplicate UNIQUE, validation, similarity (fingerprint 0.7939) | pass |
| `ae60760` | `pass2` | **FAIL — 2/2 solved.** Cruxes deducible from the spec |
| `e926a4a` | rubric (zero notes), similarity 0.8028, validation | pass |
| `e926a4a` | `pass2`, `deep_review`, `ava_review`, `tier1`, `qc_eval`, `qc_exec` | pass |
| `e926a4a` | `qc_gate` | **FAIL — 2 findings** (E3 harness exploit, C3 coverage) |
| `07bb447` | rubric, validation | pass |
| `07bb447` | `pass2` | **FAIL — 2/2 solved.** Variance, same design |
| `4d17657` | every gate incl. `qc_gate` | pass |
| `4d17657` | `pass2` → `trials` | **0/2** → **pass@5 0/5, avg@5 0.000, 5 good valid** → `accepted` |

### The two `qc_gate` findings, both real

- **E3 — Reward / harness plumbing exploit.** `test.sh` ran pytest from `/`, and `python3 -m`
  **prepends the working directory to `sys.path`**, so a module the agent leaves at `/ctrf.py`
  shadows the report plugin. Measured with a worthless `scanhand.py` in place: **reward 1.**
  Fixed by running pytest from a fresh `mktemp -d` under `-P`; the same attack then scores 0.
  Both halves performed, not reasoned about. `-E -s -B` and `PYTEST_DISABLE_PLUGIN_AUTOLOAD`
  were already set and did **not** close this — the cwd is the hole.
- **C3 — Narrow held-out coverage.** Taking the captured count from `batch.json` instead of the
  driver's report passed every graded case, because no case had a driver that finished cleanly
  after a **short feed**. My own mutation audit had missed it: my version of that mutation was
  unconditional, QC's was conditional on exit code. **A mutation that is easy to catch is not
  the mutation a solver would write.**

Two further QC checks reported "probe crashed — timed out after 300 s". Not crashes: a stub
submission sat out every gate deadline. Waits now abort the moment the worker process exits,
and a stub fails the whole suite in **1.5 s**.

---

## 6. Error → what to do

| Symptom | Do |
|---|---|
| pass@2 **2/2 solved** and your spec is precise and complete | Suspect the spec's own precision. Ask whether each axis is *derived from the spec* or *imposed by the platform*. Only the second kind held here |
| The analysis says the agents converged on your golden approach unaided | Your cruxes are deducible. Do not add more of the same kind — change the **kind** |
| pass@2 passes on push N and fails on strictly-harder push N+1 | Variance at a ~50% solve rate. Read the fail reasons, not the verdict. Do not redesign on one sample |
| A gate **passes** | Read why anyway. Ours passed on a failure mode (SIGKILL vs SIGTERM) that a human reviewer would have called invalid |
| Your instruction states a scope and then enumerates it | Delete the enumeration. A trial went straight to the enumerated case |
| Your shipped self-check has an obvious untested area | It is advertising it. Add a check there that stays green under every wrong repair |
| A rule leaves a representation free (which signal, which order) | Grade the **decision**, not the representation, and prove both readings pass |
| `qc_gate` E3 naming `sys.path` | The **cwd** is the hole. `-m` prepends it. Run pytest from a fresh `mktemp -d` under `-P`, and perform the exploit both before and after |
| `qc_gate` C3 after you already ran a mutation audit | Your mutation was probably cruder than a real solver's. Make each mutation the *plausible* wrong implementation, conditionals included |
| A QC probe "crashed — timed out" | Check whether a stub submission waits out your deadlines. Abort every wait on worker exit |
| A calibration variant fails everything | Confirm it **compiles and starts** before believing it. A dangling reference reads exactly like a caught trap |
| Building a mutation table programmatically | `json.dumps` or a lambda replacement — `re.sub` interprets `\n` in the replacement. Assert every anchor is present in the reference first |
| pass@5 returns **0/5** and you hold a validated improvement | Do not push it. 0/5 is the ceiling; park it. Sixth confirmation |
| Trials is in flight and you want to fix something | Let it finish. Cancelling does not refund the slot, so the result is free information |

---

## 7. Process rules confirmed here

- **Probe the platform before designing around it.** Every axis was confirmed in a throwaway
  container first: `lockf` versus an unrelated `open`/`close`, thread-versus-process exclusion,
  the 64 KiB pipe boundary (works at 200 sheets, deadlocks at 4000), umask masking a create
  mode, `-15` versus the shell's `143`, and an orphaned grandchild holding a pipe open. Cheap,
  and one candidate died on contact.
- **Measure flake rate; do not argue it.** The rubric reviewer flagged that it could not execute
  the suite. Five runs with every core saturated: 16/16 each time, 36.3–36.7 s wall.
- **Never push while a run is in flight.** Parked the push-5 work in a stash; `submission` stayed
  byte-identical to origin while pass@5 ran.
- **Read the sticky comment's commit footer.** A stale pass@2 sticky from push 1 was still the
  newest such comment on the PR and describes a design two revisions old.
- Never `git add -A`; one push per round of work; update the root `README.md` in the same commit.

---

## 8. Reusable checklist

- [ ] For every candidate axis, ask: *derived from my spec*, or *imposed by the platform*?
      Prefer the second. Write the answer down before building.
- [ ] Probe each axis in a container before designing around it.
- [ ] Ship a self-check that is complete-looking and green on every wrong repair — then
      **measure that it is**, one row per wrong repair.
- [ ] Build the sample so both readings **agree**, rather than omitting the case.
- [ ] Write at least two *correct but differently shaped* implementations; both must pass.
- [ ] Grade decisions, not representations. If a rule leaves a choice free, accept every choice.
- [ ] Verify every calibration variant compiles and starts before believing its score.
- [ ] Run the harness exploit yourself, before and after the fix.
- [ ] Abort every wait on worker exit so a stub cannot exhaust a QC probe's budget.
- [ ] Re-read the fail reasons of a **passing** gate.
- [ ] `.dockerignore` in `environment/` from the first commit.
- [ ] Root `README.md` updated in the same commit as every `task/` change.

---

## 9. One paragraph

A scanning depot's workers share a spool and coordinate through POSIX record locks; the agent
repairs the worker and is graded by running it against spools the shipped acceptance checks
never build, judged on driver start logs and out-of-process lock observations. The first design
put the difficulty in lock semantics that a careful reading of the shipped protocol yields, and
the benchmarked model read it and solved the task 2/2 — the grader noting the spec was
"sufficiently precise that the bugs were deducible from the spec alone". What finally worked was
keeping that machinery as the substrate and moving the deciding rules to platform behaviour no
spec-reading produces: a umask silently masking the mode a file is created with, a signalled
death that only Python calls `-15`, and a helper process that outlives the attempt that started
it and holds its output stream open forever. Six wrong repairs each score 12/12 on the agent's
own acceptance checks and still fail. The most expensive mistakes were enumerating the graded
scenarios in the instruction — one trial went straight to the listed case — and letting an
ambiguity (which signal stops a wedged driver) supply 100% of the failures on a gate that
*passed*, which was found only by reading a green gate's detail.
