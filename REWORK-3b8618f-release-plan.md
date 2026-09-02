# REWORK dynamo/release-plan — reusing a closed PR's diff got the `accepted` label; the corpus's "dead end on scope" note was not fully supported by evidence

| | |
|---|---|
| **Outcome** | **ACCEPTED** (automated) — `tier1` pass, `gate` pass, `accepted` label. **Not yet merged** at write time. |
| **Repo** | `dynamo-3b8618f-software-engineering`, branch `fix/protected-ground-truth-and-sound-verifier` (fork `Pruthviraj374/dynamo-3b8618f-software-engineering`) |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-3b8618f-software-engineering/pull/5, rework for issue [#3](https://github.com/handshake-project-dynamo/dynamo-3b8618f-software-engineering/issues/3) |
| **Category / sub** | Software Engineering / Scripting and Automation (pre-seeded, unchanged) |
| **Benchmarked model** | `task.toml`: `model_tested = "Terminus-2"`, `agent_tested = "Terminus-2"` (unchanged) |
| **Final commit** | `191f25c` (single commit, PR #4's diff re-applied onto current `main` and re-committed under correct identity) |
| **Headline** | No pass@2/pass@5 was re-run on **this** PR — the rework fast path skips it. The most recent actual measurement is from the closed PR #4 (byte-identical diff): **pass@2 = 1/2, pass@5 = 2/5, avg@5 = 0.400**, `difficulty_evidence` PASS. Reported here only because it is the same content, not because it re-ran. |

Three findings this file exists to record.

**One: the corpus note that PR #4 was "a dead end on scope, not on technique" is not supported by
any visible GitHub evidence, and my own resubmission of the identical diff contradicts its
practical implication.** `rework/rework-rule.md` §2 states this as "confirmed the hard way," but
the PR's own close event (`alokit169`, 2026-09-02T13:10:23Z) carries an **empty body** — no
comment anywhere in the PR or issue #3 explains the closure. Automated review had already posted
`Blocking Issues: None` on that PR before it was closed. When I took the exact same diff (fetched
via `gh pr diff 4`, reapplied to a fresh branch, recommitted under the correct identity) and pushed
it as PR #5, it earned the `accepted` label on the first pass. See §3 for what this does and does
not prove.

**Two: for a rework PR, the review pipeline is not the same pipeline as an original submission.**
Only `changes`, `tier1`, `gate`, and `claude-cost-report` actually ran on PR #5 — everything else
(`ava_review`, `deep_review`, `pass2`, `pass2_suggestion`, `qc_eval`, `qc_exec`, `qc_gate`,
`similarity`, `cosine_similarity`, `trials`, `validation`, `ratelimit`, `review`) shows `skipping`
at 0s, not run-and-cached. The `tier1` comment's own text ("running full QC (Tier 2)") does not
match what the job statuses show — Tier 2 never ran. `accepted` was granted on `tier1` + `gate`
alone, plus whatever ran earlier in the same workflow (`dynamo-eval`, the duplicate-similarity
check, and Docker/oracle/nop Task Validation, all of which passed). See §5 for the full gate log.

**Three: ground-truth data that the verifier trusts must be decoupled from `/app`, not merely
permission-locked.** This is the actual engineering lesson behind issue #3's `protected_ground_truth`
finding, independent of the scope question above. See §2.

---

## 1. What the task asks (unchanged by this rework)

`dynamo/release-plan` repairs a stateless CI/CD release-plan compiler:
`python3 /app/planner/plan_release.py <request_dir> <out_plan.json>`, reading a normative
`RELEASECONTRACT.md` plus `services.json`/`environments.json`/`policies.json`, and producing a
canonical JSON execution plan (service resolution, wave/phase scheduling, promotion gates, failure
fencing, retry budgets, canary/priority, rollback). Graded by an independent `tests/reference_plan.py`
oracle against exact JSON equality over visible smoke/twin/incident fixtures plus ~40 hidden
recombinations generated inside `test_outputs.py`. This task was already delivered and merged
(PR #2, 2026-08-06) before this rework.

## 2. The two findings, and the invariant that keeps the fix alive

Issue #3 (`uphold` verdict) named exactly two findings, both real and independently reproduced
in-container before touching any code (see §4 for the reproduction method — do this before
believing a finding, not after):

- **`protected_ground_truth` (Major).** `tests/reference_plan.py` set `DATA = Path("/app/data")`
  and recomputed `expected()` **after** the agent's planner had already run in the same pytest
  process. `/app/data` is copied into the single agent+verifier image with no write protection and
  is the same filesystem the agent's own turn can write to. Measured: editing one service's
  `critical` flag and `dependencies` in `/app/data/services.json`, then running the *correct*
  solution, still passed all 41 tests — the oracle moved with the tamper.
- **`sound_verifier` (Minor).** `instruction.md` documents "do not add files to the request
  directory"; nothing asserted it. Measured: a planner that wrote a stray file into its request
  directory while still computing the correct plan still scored reward 1.

**The invariant:** anything the verifier trusts as ground truth — catalog files *and* the graded
request payloads themselves — must live somewhere the agent's own turn cannot have written to,
which in this TB2 harness means under `tests/` (added to the container only at verify time, never
`COPY`'d into `environment/`). Permission-locking `/app/data` (`chmod -R a-w`, which the accepted
fix does) is defense in depth, not the actual fix — the oracle must stop *reading* from `/app/data`
at all. A fix that only chmods `/app/data` but still has `reference_plan.py` read from there is
insufficient, because the agent's mutation happens *before* the image is grading (same container,
same filesystem layer across the agent→verify transition on this harness) and could still have
landed before any chmod took effect, or the chmod itself could be undone if the agent runs as root
(this image has no `USER` directive — everything is root by default).

## 3. Dead ends

**Dead end A (documented, not independently reconfirmed as a rejection): a scoped, from-scratch
diff that touched only `tests/reference_plan.py`, `tests/test_outputs.py`, and a new
`tests/fixtures/data/` copy.** I wrote this first (see the superseded content of PR #5's first two
commits, since force-pushed over — recoverable from `Pruthviraj374/dynamo-3b8618f-software-engineering`
reflog if ever needed, but not from the PR itself since force-push does not preserve old heads on
GitHub's UI). It:
- Duplicated ground truth into `tests/fixtures/data/`, pointed `reference_plan.DATA` there, staged
  every graded request into a fresh writable tmp directory before invoking the planner (so the
  "no added files" check would be meaningful even if `/tests` turned out to be read-only), and
  added the added-files assertion directly in the shared `run_agent()` helper.
- Passed `changes`, `cosine_similarity`, and `review` before I abandoned it (see §6, "process
  rules learned the hard way," for *why* I abandoned a passing run mid-flight — that was a user
  instruction, not a pipeline verdict).
- Reproduced both exploits locally and confirmed both were blocked, plus `harbor run --agent
  oracle` = 1.0 and `--agent nop` = 0.0, before ever pushing.

I do not know whether this diff would have reached `accepted` — I replaced it before its own
`tier1`/`gate` ran. **Do not read this as "the scoped diff would have failed."** It is recorded
here only because the corpus's scope-discipline norm (`rework-rule.md` §2) predicts the *opposite*
diff (the wider one) should be the dead end, and that prediction did not hold in this instance.

**Dead end B (the actual documented one, from the prior session): PR #4 itself, per
`rework-rule.md` §2 — "fixed the two named findings correctly but also rewrote core scheduling
logic and added new mechanisms well beyond the checklist."** That diff:
- Converted the wave-fixpoint and serial-group rules in `RELEASECONTRACT.md` from stated mechanism
  to derived-property wording, and added `services.json`/`environments.json` twin fixtures and a
  concurrency-vs-saturated-wave test — all of this tracks the bot's own **pass@2 Difficulty
  Suggestion** comments on PR #4 (posted 2026-08-24/25, *advisory, explicitly non-blocking*) almost
  verbatim, not anything issue #3 asked for.
- Was closed by its own author with no explanation.

What actually happened when I resubmitted **that exact diff** (§6): it passed. This does not
resolve the contradiction — it sharpens it. Either (a) the original closure was for a reason
outside GitHub (private review, a Slack conversation, a judgment call by the author that isn't
tested by CI) and the automated gate simply does not check "is this in scope of the named
findings," or (b) the original closure was itself a mistake / overcautious, and the diff was fine
all along. I cannot distinguish these from here. **What the evidence does support:** automated
`tier1`/`gate` on this repo verifies "are the named findings addressed," not "is the diff scoped
to only the named findings." Do not treat a green `tier1` as proof of in-scope-ness.

## 4. What actually worked

**Reproduce before you fix, always, on this class of finding.** Before writing any code I built
the `environment/Dockerfile` image standalone (`docker build -t repro:pre -f environment/Dockerfile
environment`) and, without Harbor, ran the correct `solution/plan_release.py` inside it with
`tests/` bind-mounted read-only, first with `/app/data/services.json` hand-tampered, then with a
planner that drops a stray file into its request directory. Both reproduced the exploit cleanly
(tests that should fail, passed) *before* any fix existed, and both were re-run after the fix to
confirm they now fail correctly with an informative assertion message, not a crash. This is the
same discipline `rework-rule.md` §3 asks for ("prove the finding before fixing it") and it caught
a real bug in my own first attempt: staging every graded request into a fresh writable tmp
directory, rather than pointing the CLI straight at the protected `/tests/fixtures` path, was
necessary — pointing directly at a read-only `/tests` path turned the sound_verifier exploit
reproduction into an unhelpful `CalledProcessError` (permission denied) instead of a clean,
informative assertion failure, and depended on an unverified assumption that `/tests` is actually
mounted read-only in production grading.

**`harbor run -p . --agent oracle`/`--agent nop` locally, every time, before every push.** Caught
nothing wrong here (both attempts were solid on this axis) but this is the cheap, mandatory gate
per `verify/error.md` §"the one habit that catches most of these," and per
[[dynamo-preflight-regression]] should never be skipped even when confident.

**Fetching the closed PR's diff with `gh pr diff 4` and reapplying it (`git apply`) onto a fresh
branch off current `main`, rather than fetching/cherry-picking its actual commits.** This preserved
the exact file content while letting the new commit carry the correct
`Pruthviraj Gundadi <g.pruthviraj2002@gmail.com>` authorship — reusing the original commits
verbatim would have carried `alokit169`'s authorship into a `dynamo-*` repo, which
[[git-identity-dynamo]] forbids regardless of whose diff it mechanically is.

## 5. Gate-by-gate log

**Attempt 1 (scoped diff, commit `ee5bff5`, then empty re-trigger `fc1c8d5`):**

| Gate | Verdict | Note |
|---|---|---|
| `review / changes` | pass | |
| `review / cosine_similarity` | pass | |
| `review / review` | pass | |
| `review / similarity` | **fail** (transient) | Comment: "could not complete... usually a transient error or an API budget issue. Push a new commit to re-run." Not a finding about the diff. |
| downstream (`ava_review`, `deep_review`, `pass2`, `qc_*`, `trials`, `validation`) | skipped | Blocked on `similarity`'s failure, per the dependency chain. |
| Fix attempted | `git commit --allow-empty` + push | `gh run rerun --failed` returned `404` — no permission to rerun a workflow run on the upstream repo from a fork; an empty commit was the only available re-trigger, matching what the bot's own comment instructed. |
| Label after re-trigger | `rework-submitted-on-red` (appeared once, alongside `in-progress`) | Bookkeeping, not a verdict — no comment ever explained it, and it did not block anything downstream. |
| Result | superseded before `similarity`'s re-run or anything past it landed | Replaced with Attempt 2 per user instruction before this run resolved. |

**Attempt 2 (PR #4's diff, commit `191f25c`, force-pushed with `--force-with-lease`):**

| Gate | Verdict | Note |
|---|---|---|
| `dynamo-eval` | PASS | All criteria pass, same as PR #4's original run (unchanged task design) |
| duplicate/similarity check | UNIQUE | No delivered task too similar |
| Task Validation (Docker/Oracle/Nop) | ✅ / ✅ / ✅ | |
| `review / changes` | pass | |
| `review / tier1` | pass | "All 2 GitHub rework findings are materially addressed" — named `RW3F1` (sound_verifier) and `RW3F2` (protected_ground_truth) explicitly, citing the actual test/file additions |
| `review / gate` | pass | |
| `review / claude-cost-report` | pass | |
| `ava_review`, `deep_review`, `pass2`, `pass2_suggestion`, `qc_eval`, `qc_exec`, `qc_gate`, `similarity`, `cosine_similarity`, `trials`, `validation`, `ratelimit`, `review` | **skipping** (0s, not cached) | Not run at all on this PR. See finding Two above. |
| Label | `accepted` | Applied immediately after `tier1` + `gate` both passed |

No check was ever red on Attempt 2. Total elapsed from push to `accepted`: well under 15 minutes —
far faster than an original submission's pipeline, consistent with the rework fast-path skipping
the agent-trial-based gates entirely.

## 6. Error → what to do, and what NOT to do

- **`review / similarity` (or any single-run bot check) fails with "could not complete... transient
  error":** push a new commit to re-trigger, per the check's own instruction. Do NOT try
  `gh run rerun --failed` from a fork first and stop there — it 404s (no permission on the upstream
  repo's Actions from a fork); go straight to the commit-based re-trigger. An empty
  `git commit --allow-empty` is an acceptable, honest re-trigger when there is genuinely nothing
  else to fix — do not invent a cosmetic change just to have a non-empty commit.
- **A prior session's memory note says a specific closed PR is "a dead end on scope":** treat this
  as a hypothesis the note's author believed, not a verified fact, when the closing comment is
  empty and no reviewer explanation exists on GitHub. Read the actual close event
  (`gh api repos/<org>/<repo>/issues/<n>/timeline`) before repeating the claim to the user as
  settled fact. In this instance I did surface the caveat before the user overrode it — do that,
  don't silently comply and don't silently refuse.
- **The user explicitly instructs overriding a standing corpus rule for their own repo:** this is
  the user's call to make (it's their submission, their workflow), not a safety boundary. Comply,
  but (a) still enforce rules that were *not* overridden — the git-identity rule stayed in force
  even while the scope-reuse rule was set aside, so the reused diff got a fresh, correctly-authored
  commit rather than the original author's commits — and (b) ask a clarifying question first if the
  mechanical path is ambiguous (here: replace the existing PR vs. open a second one) rather than
  guessing, since force-pushing over an in-flight, already-partially-green PR is not free
  (readme-rule.md's own point about a stale-README fix costing "a rate-limited pass@2/pass@5"
  applies to any force-push mid-pipeline, not just README fixes).
- **Do NOT assume `/tests` is mounted read-only in production** when writing a check that depends
  on it (e.g., "planner must not write to its request directory"). Stage graded inputs into a
  fresh writable directory outside both `/app` and `/tests` instead, so the check's own assertion
  fires with a clear message regardless of the real mount's permission mode.

## 7. Bugs I introduced myself

- **A `Monitor`-based PR-watching script split multi-line bot comments into spurious separate
  "new comment" notifications**, because the id/body extraction used `.body` (raw, with embedded
  newlines) inside a `while IFS= read -r line` loop that only expected one record per line. Fixed
  by collapsing newlines with `jq`'s `gsub("\n"; " ")` before the read loop, and by seeding
  `seen_comments`/`seen_checks` from the current state on (re)start so a restart doesn't re-announce
  everything already reported.
- **The same Monitor script initially echoed a `STATE: ...` line unconditionally every 60-second
  poll**, which is exactly the "too many events" pattern the tool's own guidance warns gets a
  monitor auto-stopped. Fixed by gating the echo on an actual state change (`[ "$state" !=
  "$prev_state" ]`) before it caused a real problem — caught this myself on review, not from an
  external stop.

## 8. Process rules learned the hard way

- **`gh pr diff <n> --repo <owner>/<repo>` then `git apply` onto a fresh branch off current `main`**
  is the correct mechanism for legitimately reusing another contributor's diff content while
  keeping correct commit authorship — cleaner than cherry-picking (which carries original
  authorship) and cleaner than fetching their fork as a remote and merging (which pulls their whole
  history).
- **`git push --force-with-lease` is the right tool** for replacing an open PR's content
  mid-review at the user's explicit request — it is a legitimate use of history rewriting, distinct
  from the destructive `--force` the git-safety rules warn about, precisely because
  `--force-with-lease` refuses if someone else pushed to the branch since your last fetch.
- **A rework PR's CI pipeline is materially cheaper than an original task's** — confirmed
  empirically here, not just asserted by `rework-rule.md` §3's "explicitly lower" time-budget line.
  Plan review time accordingly: do not expect (or wait for) `pass2`/`deep_review`/`qc_exec` comments
  on a rework PR; they may simply never run.
- **`rework-submitted-on-red` is a bookkeeping label, not a rejection signal** — it appeared once
  after pushing while a prior run had a red check, carried no comment, and did not block anything.
  Don't over-react to it, but don't ignore a *repeat* of it either without checking for an
  accompanying comment next time.

## 9. Reusable checklist for the next rework task

1. Read the open issue on the **upstream** repo (forks usually have Issues disabled), and read
   every closed PR/issue on the same upstream repo — both for technique and for any note like
   `rework-rule.md`'s "dead end on scope" about a specific prior PR. Treat such notes as hypotheses
   to verify, not settled fact — check the actual close event body via
   `gh api repos/<org>/<repo>/issues/<n>/timeline` before repeating the claim.
2. Reproduce every named finding in-container, by hand, before writing any fix — build the
   `environment/Dockerfile` image directly, mount `tests/` read-only, and demonstrate the exploit
   (tampered ground truth still passes; a rule violation still scores reward 1). This is cheaper
   and more informative than trusting the finding's prose.
3. Write the scoped fix touching only the finding's cited files plus what's mechanically required
   (a protected copy of ground truth under `tests/fixtures/`, not a permission change on
   `environment/` alone).
4. Re-run the same in-container reproductions to confirm they now fail cleanly, then
   `harbor run -p . --agent oracle` (= 1.0) and `--agent nop` (= 0.0) before every push.
5. Open the PR referencing the issue number by name in the title. Expect a much shorter gate list
   than an original task (`tier1` + `gate` may be the only substantive checks that actually run).
6. If a bot check fails with "transient/could not complete," push a new commit (empty is fine) to
   re-trigger — do not try to force a workflow rerun from a fork.
7. On `accepted` + all-green: post the retrospective trigger is met, write it here prefixed
   `REWORK-`, update `previous-task-data.md`'s index in the same change. Skip the "4 proposal-form
   portal answers" step from `task-retrospective-rule.md` §1 — that step is for a new task's
   Handshake portal submission and has no equivalent for a rework fix.

## 10. One-paragraph version for future me

Issue #3 on `dynamo-3b8618f-software-engineering` named two real, independently-reproduced
findings (`protected_ground_truth`: the oracle re-read agent-writable `/app/data`;
`sound_verifier`: nothing checked "no files added to the request directory"); the fix is to move
every piece of ground truth the verifier trusts — catalogs *and* graded request payloads — under
`tests/` (verify-time-only) and assert the request-directory invariant directly. A prior closed PR
(#4, from another contributor) fixed both findings correctly but also rewrote scheduling-difficulty
content beyond the checklist, and this corpus's own note called that "a dead end on scope, not
technique" with no cited evidence beyond an unexplained self-closure. At the user's explicit
instruction I overrode that caution, reused PR #4's diff verbatim (recommitted under correct
identity via `gh pr diff` + `git apply`, never the original commits), and it reached the
`accepted` label cleanly on a materially lighter rework-specific pipeline (`tier1` + `gate` only;
the full agent-trial gates never ran). This does not prove the original closure was wrong — its own
close event carries no explanation — but it does mean "closed by its author with no stated reason"
should not, on its own, be escalated to "confirmed dead end" in a note the next session will treat
as fact without re-checking. Verify the close reason before trusting it.
