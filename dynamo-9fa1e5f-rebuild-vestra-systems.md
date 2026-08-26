# dynamo/rebuild-vestra-systems — a real LAPACK convention the sample is built never to exercise

| | |
|---|---|
| **Outcome** | **ACCEPTED** — every gate green, `accepted` label |
| **Repo** | `dynamo-9fa1e5f-mathematics-and-formal-reasoning`, branch `submission`, fork `Pruthviraj374` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-9fa1e5f-mathematics-and-formal-reasoning/pull/1 |
| **Category / sub** | Mathematics and Formal Reasoning / **Computational Linear algebra** (pre-seeded) — **first task in this category in the corpus** |
| **Benchmarked model** | `task.toml` names Opus-4.8 / Terminus-2; pipeline reports "Model A" on Daytona |
| **Final commit** | `ee1a7fd` (2 task commits) |
| **Headline** | **pass@5 = 0/5 solved, 3 good-valid fails, avg@5 = 0.000** — the best available outcome. **3 pushes total**, and the only two blocking findings were *verifier* defects, never the design. |

The most valuable things here: §3 (why a real, published, conditional LAPACK convention worked
where invented rules keep failing), §5 (both blocking findings and why neither was a redesign),
§7 (a self-inflicted guard bug that a probe caught and CI would not have), and §6's
anti-recommendations.

---

## 1. What the task asks

A decommissioned structural solver ("VESTRA-7") left an archive of factored linear systems; the
factorization kernel is gone. Each `.vsf` file holds the packed factor entries and the pivot
codes and nothing else. The agent writes `/app/reconstruct.py`, invoked
`python3 /app/reconstruct.py <archive_dir> <out_json>`, which reads every `*.vsf` in the
directory and emits a JSON object keyed by archive name, each value the full `n x n` original
matrix as rows of JSON integers. It also leaves its sample run at `/app/output/sample_out.json`.

- **Agent sees:** `instruction.md`, `/app/data/VSF.md` (the container documented byte for byte),
  9 sample archives, and `/app/data/sample_expected.json` — the answers for those 9, so it has a
  genuine end-to-end self-check.
- **Graded on:** 21 held-out archives, **exact integer equality**, all-or-nothing.

Integer-only grading was deliberate (`lumenp` §6 / `filer-audit` §1 generalised): every entry is
an integer, so no tolerance exists anywhere in the task, and `difficulty_evidence` can never call
a failure a threshold or formatting artifact. The rubric confirmed it — *"no tolerances used, so
none to calibrate."*

## 2. The crux, and the invariants that keep it alive

`ap` and `ipiv` are stored exactly as LAPACK's packed symmetric-indefinite factorization
(`?SPTRF`, Bunch-Kaufman diagonal pivoting) emits them. `VSF.md` **names that routine as the
locator and restates none of its rules** (`rebuild-readout-builder` §3.3 / `filer-audit` §2 —
name the standard, stop). Reconstruction is
`A = (prod_k P_k F_k) . D . (prod_k P_k F_k)^T`, walking pivot blocks in the kernel's own
processing order.

Most of that is pinned by the worked sample. **Two decisions are not:**

| Axis | Real rule (named-not-restated) | Natural mistake | Fires when |
|---|---|---|---|
| **A** | a **2x2 pivot block** records its interchange against the block's **off-corner** row (`k+1` for `L`, `k` for `U`), not the row whose index carries the code | target the row the code sits at | an archive contains a 2x2 block |
| **B** | a **`uplo='U'` archive** is processed **backward** from the last column, with the mirrored packed layout | hard-code the lower orientation the sample shows | an archive is upper-triangular |

**Invariants, all machine-checked in `tools/build_fixtures.py`, which fails the build if any breaks:**

1. **The sample is bit-inert under both axes** — 0 of 9 systems change under either wrong reading.
   Measured, not assumed.
2. **The sample pins every machinery decision** — each machinery mutant (row-major packing,
   transposed factor, no interchange, wrong direction) changes >= 8 of 9 sample systems. So an
   agent must get all the ordinary work right *to match the sample at all*, which keeps those
   from becoming accidental hidden axes.
3. **The two axes break disjoint held-out sets** (`rebuild-readout-builder` gold standard): axis A
   fails `h01-h04, h16-h17, h20-h21`; axis B fails `h05-h08`; both fail `h09-h12, h18-h19`.
4. **A sample-shaped control group** (`h13-h15`, lower + 1x1 only) passes under *either* misreading,
   so a submission is never failed by sample-shaped cases alone.
5. **No dud fixtures** — every held-out system is caught by some single-decision mutant
   (`lumenp` §7).
6. **No crux vocabulary anywhere agent-visible** — an automated grep over `instruction.md` and
   `/app/data/` rejects "off-corner", "backward", "opposite direction", "mirrored", "latent",
   "axis a/b". Run before every push.

**The reconstruction rule was validated against real LAPACK before any fixture existed**
(`tools/check_against_lapack.py`): 598 factorizations from `scipy.linalg.lapack.dsytrf`, both
`UPLO` values, repacked into VESTRA order, reconstructed, compared — 0 mismatches. This is
`merge-lora` §4.2 and `audit-build-context` §4.1 applied up front: generate/validate ground truth
by *running* the real thing, never by porting its source or reasoning from docs.

## 3. Why a real published convention worked here — and the one design choice that made it work

The corpus is emphatic that **invented rules are a dead end** (`lumenp` §3: disclosure and
dismissability are mutually exclusive — an invented rule must be disclosed or B5 blocks it, and a
disclosed rule gets implemented) and that **a recalled convention is usually solved 2/2**
(`motion-register` §3: the model recalls published conventions essentially perfectly). The
resolution the corpus already pointed at, and which held here, is `accrued-interest` in `34-*.md`:

> a recalled convention stumps only when **applying** it costs machinery the sample never demands.

That is exactly this task. The model knows `?SPTRF` exists and can find its documentation
(`allow_internet = true`). What it does not do is *fully reverse-engineer a named standard it
believes it already knows* when the shipped self-check goes green without it. The pass@5 analysis
said so directly:

> All four trials produced reconstruct.py and **passed the sample** (lower-only, 1x1-pivot-only)
> but failed test_heldout_reconstruction with large per-entry errors. […] These are the two
> complementary facets of a single edge-case trap crux explicitly designed by the task author.

And on fairness:

> No trial failed because the verifier applied an undisclosed tolerance, rejected a legitimate
> alternative algorithm, or enforced a rule absent from the agent-visible specification. […]
> **This is genuine task difficulty, not a task or verifier defect.**

**The decisive design choice: the sample contains no 2x2 pivot blocks at all, and only `uplo='L'`.**
I nearly did the opposite. `rebuild-plate-rasterizer` §4.2 argues that omission leaves the agent
*uncertain* while equivalence makes it *confident*, so I first tried to ship 2x2 blocks in an
identity-interchange configuration — visible but inert. **Measured: it does not work here.** With
an identity 2x2 (`p == k+1`), the correct reading performs no swap but the wrong reading swaps
rows `k` and `k+1`, so the shapes diverge — 39/40 systems changed. There is no configuration of a
2x2 block that is simultaneously visible and inert for axis A. Omission was forced, and it was
right. *Generalisation: check whether an "inert witness" is actually algebraically inert for your
axis before assuming the equivalence trick applies; for a permutation-valued rule it usually is not.*

To keep omission fair rather than a crash-generator, `VSF.md` states the *situation* without the
*resolution* (`replay-strata-plans` §3.2, `replay-rollout-gae` §3): it says a code may be negative
and that a negative code belongs to a block spanning two consecutive columns written once per
column. It never says which row the interchange targets. That one sentence converts "agent's
parser explodes on an unexpected negative" into "agent computes a confident wrong answer" —
the silent-failure amplifier (doc 33) — and it satisfied discoverability: `deep_review` graded
**`decisive_answer_discoverable` PASS**, re-graded from the agent's own field of view.

**Also worth recording: naming the real routine did NOT make it too easy.** Same finding as
`emulate-int8-accel` §3 in a second category. Naming `?SPTRF` satisfied B5/discoverability *and*
both axes still stumped 4 of 5 trials.

## 4. Dead ends

Fewer than usual, because the crux was measured before it was built rather than after a gate
rejected it. Recorded anyway — the measurements are the transferable part.

**(a) Visible-but-inert 2x2 blocks in the sample.** Covered in §3. Measured 39/40 systems diverge;
`rebuild-plate-rasterizer` §4.2's equivalence trick does not apply to a permutation-valued rule.
Cost: ~20 minutes of measurement, zero gate cycles, because it was measured at design time.

**(b) `?SPTRF`'s `info > 0` (singular factor) branch as a third axis.** Rejected at design time.
The routine's behaviour there is a *state*, not a computation, and the output contract for "what
does a singular archive reconstruct to" would have been my invention — exactly the
`filer-access-audit` §3 "SHOULD with an underspecified fallback" shape. Confined the data instead:
every archived system is non-singular, and the README says so. *Do not grade a branch of a standard
whose result the standard does not determine.*

**(c) Deriving fixtures by factoring real matrices with LAPACK.** Attractive for realism, but it
removes control over which shapes appear: I need the sample to contain *no* 2x2 blocks, and real
`dsytrf` emits them constantly (measured: 448 2x2 blocks across 600 random matrices, ~37% of them
with identity interchange). Generating well-formed factorizations directly and validating the
*conventions* against real LAPACK gives both realism and control. The rubric accepted this
explicitly under `difficulty_explanation_quality`.

## 5. Gate-by-gate log, in the order things actually broke

Three pushes. **Every gate that ran on a correct build passed first time**, including the ones that
historically cost this corpus the most cycles (`deep_review`, `ava_review`, `qc_eval`, `qc_exec`,
rubric 31/31).

| # | Commit | Gate | Verdict | Fix |
|---|---|---|---|---|
| 1 | `2c1f6ad` | `similarity`, `cosine_similarity` | PASS (0.70 / 0.79 / 0.79 vs 0.9 threshold) | — |
| 1 | `2c1f6ad` | **static checks** | **FAIL 1 of 25** | literal-path fix, below |
| 2 | `e187447` | rubric (`review`) | **PASS — 30 PASS, 1 N/A, 0 FAIL, first time it ran** | — |
| 2 | `e187447` | `validation` | PASS (Docker / oracle / nop) | — |
| 2 | `e187447` | `pass2` | **PASS**, ~84 min | — |
| 2 | `e187447` | `deep_review`, `ava_review`, `tier1`, `qc_eval`, `qc_exec` | PASS | — |
| 2 | `e187447` | **`qc_gate`** | **BLOCK — D4 nondeterminism** (+ E5 advisory) | determinism + guard fix, below |
| 3 | `ee1a7fd` | `qc_gate` | **PASS — 37 checks & probes clean, `QC-FIXES-B64: W10=` (zero findings)** | — |
| 3 | `ee1a7fd` | **`trials` (pass@5)** | **0/5 solved, 3 good-valid fails, avg@5 = 0.000** | — |
| 3 | `ee1a7fd` | `gate` | **PASS → `accepted`** | — |

### 5.1 Static check — "nothing writes /logs/verifier/reward.txt"

> FAIL submission/task/tests: nothing writes /logs/verifier/reward.txt — the verifier must write
> 1 (pass) or 0 (fail) there

`test.sh` **did** write it, correctly, on every path — but through `REWARD_FILE="$REWARD_DIR/reward.txt"`.
**The check greps the script text; it does not trace what the script does.** Third instance of this
class in the corpus after `filer-access-audit` §5.1 (a `tests/` mention *in a comment* failed
"Dockerfile does not COPY tests/") and `replay-run-histories` §5.2 (`test.sh` does not invoke
`test_outputs.py`).

**Fix:** spell `/logs/verifier/reward.txt` and `/logs/verifier/ctrf.json` out literally at every
use. No behavioural change. Verified in the built container that both files exist afterwards and
`reward.txt` contains `1`.

**Rule:** any path or filename a static check might look for goes in the script **literally**.
Never factor it into a variable, however much cleaner that reads.

### 5.2 `qc_gate` D4 — Nondeterminism (the one blocking finding)

> verifier/held-out generation uses os.urandom/secrets (unseedable CS-random) with no fixed seed
> — graded cohorts/verdicts vary across identical clean runs
> **Fix:** Seed every graded generation / solution / verification path with a fixed constant.

The held-out archives were staged under `secrets.token_hex(8)` names. That existed for a real
reason — `dynamo-a3ab813`'s `ava_review` finding that *"a table keyed on the case id would be
accepted"* — so the fix had to preserve the anti-lookup property while removing the randomness.

**Fix:** derive each staged name from a **fixed salt**,
`"q" + sha256(SALT + ":" + stem).hexdigest()[:16]`. Deterministic across runs; still not the
archive's real stem, so a keyed table has no key. **The insight that makes this safe: the
mapping's secrecy comes from `/tests` being unreadable to the graded program, never from
unpredictability.** Once that is true, pinning the names costs nothing.

**What I deliberately did NOT make deterministic:** the single `tempfile.mkdtemp()`. It names a
root-owned scratch directory holding no graded data, and a fixed path there is one the submission
could pre-create before the root verifier writes to it — `request-preconditions` §7.3 exactly.
Making it deterministic would have traded a QC finding for a real hole. Recorded in the README so
a reviewer sees judgement rather than an oversight.

### 5.3 `qc_gate` E5 — Symlinked Output Path (advisory, fixed in the same push)

> leaf symlink guard present but graded outputs live under an /app subdirectory — confirm the
> guard also rejects a symlinked PARENT directory / containment bypass, not just leaf files

Fixed in the same push as D4 because `replay-rollout-gae` §5 records an advisory becoming a
**`tier1` required fix on the very next push with no separate warning**. Cheap to do, expensive to
defer. See §7 for the bug I introduced doing it.

## 6. Error → what to do, and what NOT to do

| Symptom | Do | Do NOT |
|---|---|---|
| Static check says a path/file "is not written" or "is not invoked" and your script plainly does it | Spell the literal string out in the script | Verify the built image and re-push unchanged — the scan never looks there |
| `qc_gate` **D4 nondeterminism** on verify-time random names | Derive them from a **fixed salt**; the secrecy is the sealed tree, not the randomness | Delete the opaque naming to "simplify" — that re-opens the keyed-table bypass `dynamo-a3ab813` closed |
| D4 names *any* randomness in the verifier | Seed only what affects the **graded cohort or verdict** | Seed `mkdtemp` too — a predictable root-owned write path is a worse defect than the finding (`request-preconditions` §7.3) |
| `qc_gate` **E5 symlinked output path** | Walk every component **at or below the graded root**, plus `O_NOFOLLOW` + nlink + realpath containment | Walk from `/` — see §7; it rejects correct submissions on any platform that symlinks a system directory |
| A QC finding is filed as **advisory / "needs human review"** | Fix it in the same push as the blocking one | Defer it — it can return as a `tier1` **required** fix next push (`replay-rollout-gae` §5) |
| You want a latent axis and an "inert witness" in the sample | **Measure** whether the witness is algebraically inert for *that* axis | Assume `rebuild-plate-rasterizer` §4.2's equivalence trick generalises — for a permutation-valued rule it does not |
| Your crux is a real published convention and you fear it is memorised | Ask whether **applying** it costs machinery the sample never demands (`accrued-interest`) | Withhold a *different*, more obscure convention (`motion-register` §3 — four designs, four 2/2s) |
| A branch of the standard has an under-determined result | Confine the data so it is unreachable and say so in the README | Grade it — the output contract becomes your invention (`filer-access-audit` §3) |
| Gates show `SKIPPED` below a failure | Read it as **"never ran"** | Read it as that gate's objection |
| Zero workflows dispatch and nothing is wrong with the task | Check `githubstatus` **and** a measured probe (`actions/runs` `total_count`, commit `status`) | Push or close/reopen into a live incident — each push burns a rate-limited pass@2/pass@5 |

## 7. Bugs I introduced myself

**The symlink guard rejected the accept side.** Fixing E5, my first version walked *every* path
component from `/` and failed if any was a symlink. On macOS `/var` is a symlink to `/private/var`,
so the probe's accept-side case — a genuine regular file in a genuine directory — was **rejected**.
In-container `/app` has no symlinked ancestors, so **this would have passed CI and broken
elsewhere later.**

Caught only because the probe exercises the accept side in the same run as the reject side —
`contact-export` §3.3, where two anti-cheat tightenings rejected a correct solver (1.000 → 0.000).
**Fix:** anchor the walk at `/app`; components *above* the graded root are deliberately not checked,
because a platform may legitimately symlink a system directory and failing a correct submission for
that is a verifier bug, not a caught attack. Final probe covers four cases: real file **accepted**;
symlinked leaf, symlinked parent, and out-of-root path all **refused**.

**A no-op `shutil.copyfile(SOLVE, SOLVE)` crashed the exploit probe** with `SameFileError` after all
four attacks had already reported. The `finally:` block had restored the pristine solution, so the
tree was safe — but only because the restore was in `finally`. Park-and-restore-in-`finally` is what
made an otherwise sloppy crash harmless.

**My own README-verification script false-positived on `set -e`** — it matched the *comment*
explaining why `set -e` is not used. Fixed by stripping comments before scanning. Same literal-scan
trap as §5.1, on my own tooling, ten minutes after fixing it in the pipeline's.

## 8. Process rules confirmed

- **`.dockerignore` belongs in `task/environment/`**, beside the Dockerfile — the build context is
  `task/environment/`, not the repo root. I put it at the root first. `fir` §6.1 and `tarballs` §5.3
  both already said so; adding it up front cost 30 seconds and the check passed first time.
- **Omit the `"You have N seconds…"` line.** Confirmed again — `instruction_concision` PASS with the
  explicit note *"no time-budget string."* Sixth confirmation.
- **`tools/` at the repo root, not inside `task/`.** `no_extraneous_files` inspects `task/`;
  `restore-runbook-advisor` §3.4 hit this by putting tooling inside. Root `README.md` documents each
  tool. `no_extraneous_files` PASS, and `task_readme` **N/A** (absent = pass; a `task/README.md` that
  duplicates content FAILs).
- **`.gitattributes` with `*.vsf binary`** before committing binary fixtures
  (`replay-fleet-survival` §8). Confirmed `git diff --numstat` reports `-`/`-`.
- **Never push while a run is in flight.** Held through three multi-hour `pass2`/`trials` runs.
- **A long `pass2` is not a stall.** Ours ran ~84 min; `filer-access-audit` §8 recorded 49m34s. Short
  runs are what *solved* looks like — agents quitting early.
- **Platform-fault triage, live-fire.** A GitHub Actions `major_outage` ran through most of this
  task. `total_count: 0` runs plus an empty commit-status list meant *never dispatched*, not
  rejected. Holding was correct — the gates dispatched on their own once traffic un-throttled, and
  the close/reopen re-trigger was never needed. **A degraded Actions status does not reliably block
  dispatch**, so check the measured probe, not just the banner.

## 9. Checklist for the next task

- [ ] Validate the convention against the **real implementation** before building fixtures.
- [ ] Ask of the crux: does **applying** it cost machinery the sample never demands? If not, it will
      be recalled and solved.
- [ ] Measure sample-inertness of every latent axis, and sample-pinning of every machinery decision,
      as build-time assertions that fail the build.
- [ ] Verify an "inert witness" is algebraically inert **for that axis** — don't assume.
- [ ] Ship a control group shaped like the sample that passes under **every** wrong reading.
- [ ] Confirm the axes fail **disjoint** held-out sets.
- [ ] Grep the agent-visible surface for crux vocabulary, automatically, before every push.
- [ ] Grade something **integer or categorical** — no tolerance, no near-miss band.
- [ ] State the *situation* without the *resolution*, so a wrong reading computes rather than crashes.
- [ ] Run every mutant **and** every exploit through the **real verifier in the built image**, and
      always probe the **accept side in the same run** as the reject side.
- [ ] Literal paths in `test.sh` — never variables.
- [ ] `.dockerignore` in `task/environment/`; `.gitattributes` for binary fixtures; `tools/` outside
      `task/`.
- [ ] Fix advisory QC findings in the same push as blocking ones.

## 10. One-paragraph version for future me

Rebuilding matrices from a packed Bunch-Kaufman factorization got **0/5 at pass@5 in three pushes**,
and neither blocking finding touched the design — both were verifier defects. What made it work was
picking a crux that is **real, published, conditional, and expensive to apply**: LAPACK `?SPTRF`'s
2x2-block interchange target and its backward walk for `uplo='U'`. `VSF.md` names the routine and
restates none of its rules, and the shipped sample is lower-triangular with 1x1 blocks only, so both
wrong readings reproduce all nine sample systems **exactly** — agents matched the self-check, went
green, and shipped. Naming the real standard did not make it easy; the model does not fully
reverse-engineer a standard it thinks it knows. I could not use `rebuild-plate-rasterizer`'s
visible-but-inert witness because no 2x2 configuration is inert for a permutation-valued rule — I
measured that instead of assuming it, which saved a cycle. Everything decisive was **measured
through the real verifier in the built image** rather than reasoned about: every wrong reading and
every reward-hacking submission scored 0.000 while the correct solution scored 1.000, and probing
the **accept** side is what caught my own symlink guard rejecting valid submissions on macOS. The
two gate failures were both literal-mindedness in the pipeline — a static check that greps script
text rather than tracing it, and a QC determinism check that does not care why your randomness is
there — and both were fixed without weakening what the randomness protected.
