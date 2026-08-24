HANDOFF: dynamo-0cfa37b-data-science-and-reporting (PR #1)
=========================================================
Last updated: after pushing commit `87b9559` (2026-08-24), which was the fifth
distinct design and the fourth empirical pass@2 "too easy" confirmation.

-----------------------------------------------------------------------
STATUS IN ONE SENTENCE: five distinct crux designs across nine commits, all
passing every mechanical gate (oracle 1.0, nop 0.0, mutation battery clean,
static rubric clean once scope was adequate) — but pass@2 has returned 2/2
solved on FOUR separate designs, the last of which matched the exact proven
"real external convention, premise-only disclosure" pattern used by every
accepted task in this category. This is a decision point, not a bug to fix.
-----------------------------------------------------------------------

## Repo / PR pointers

- Local clone: `C:\Users\chara\Downloads\Handshake\dynamo-0cfa37b-data-science-and-reporting`
- Branch: `submission`, currently at commit `87b9559` (nothing uncommitted)
- PR: https://github.com/handshake-project-dynamo/dynamo-0cfa37b-data-science-and-reporting/pull/1
- Category/subcategory (fixed, do not edit): Data Science and Reporting / Exploratory data analysis
- Model/agent under test: Opus-4.8 / Terminus-2
- Root `README.md` describes the current (5th) design in full.

## The five designs, in order, and exactly why each failed

**Design 1 (`d902e38`) — column-profiler, 2 axes.** Rebuild a retired EDA
column profiler: Tukey five-number-summary hinges (latent via odd/even n
parity — mathematically exact, verified over 300k random trials) + modified
z-score outlier screen (latent via masking — small-n plain-z can't exceed the
3.5 threshold). Both real, named, textbook EDA/statistics conventions.
**Result: pass@2 2/2 solved.** Both agents recalled Tukey's method and the
modified z-score directly from training and implemented them correctly —
the sample's inertness never mattered because they never took the naive
shortcut in the first place. This is pure formula recall, not reasoning.

**Design 2 (`e00468d`→`a1f282d`) — same shell, 5→4 axes.** Added boxplot
whisker construction, fence-boundary strictness, and (briefly) a
MAD-zero-fallback formula. `deep_review` correctly blocked the MAD-fallback
axis as genuinely undisclosed/underivable (a defensible sound-alternative
existed); removed it. **Result: pass@2 2/2 solved again, 16/16 tests, zero
verifier issues.** Every axis, however many, was a named statistics
convention whose full mechanical consequence I had spelled out in
`instruction.md` prose. Same root cause as design 1: recall, not derivation.

**Design 3 (`20f25b1`) — session-reconstructor, 2 axes.** Completely
different mechanism: rebuild a retired analytics pipeline reconstructing
per-session summaries from a raw event log. Axis 1 = a session_id can recur
after an inactivity gap (must re-segment, not just group-by-id). Axis 2 =
valueless events count toward event_count but not the value aggregates.
Matches the PROVEN shape used by this category's accepted precedents
(`rebuild-uptime-rollups`, `experiment-analysis-frame`, `rebuild-readout-builder`).
**Result: static rubric REJECTED before pass@2 even ran** —
`essential_difficulty`/`code_dependent` FAIL: "~50 lines, both rules spelled
out verbatim, an undergraduate solves this in under an hour." A legitimate
complaint — my reference implementation was genuinely much smaller than any
comparable accepted precedent (`resolve-unit-config`, `filer-access-audit`,
`cron-window-counts` all have 100+ line references with 5-9+ mechanisms).

**Design 4 (`430803e`→`193e570`) — 3→4 axes.** Added an entangled end-marker
rule (Pattern H: an explicit "end" event closes a session independent of the
timeout, and both triggers feed one shared "closed" state) to satisfy the
rubric's breadth complaint; that alone still failed the rubric a second time
("even with one entangled interaction... lack of BREADTH"). Added a fourth
mechanism: each session_type carries its own inactivity threshold, joined
from a second CSV file. **Rubric then PASSED** (breadth was sufficient).
**But pass@2 came back 2/2 solved** — both agents correctly implemented all
four mechanisms including their interactions. Diagnosis: the rubric's bar
(breadth/LOC) and the model's actual weakness (recall vs. derivation) are
different axes entirely. I had satisfied the first without touching the
second — all four rules were still author-invented and fully spelled out as
complete procedures in `instruction.md`. This model transcribes any number
of fully-specified procedural rules, however many, however entangled.

**Design 5 (`87b9559`) — 5 axes, the "did everything right" attempt.** Added
a fifth rule grounded in a REAL external technical convention rather than
another invented procedure: a session also closes at local calendar
midnight in its session_type's own IANA timezone (a real, documented
web-analytics session-boundary convention). Premise stated outright
("a session never spans a local calendar day"); the correct implementation
genuinely requires `zoneinfo`-based conversion, not a fixed UTC offset,
because the offset changes across a DST transition. Validated locally
before push: an agent that gets the first four rules exactly right but
hardcodes a hemisphere-appropriate-but-DST-unaware UTC offset per timezone
name scores 0.0 through the real verifier. This is the *exact* pattern used
by every accepted precedent in this category (`experiment-analysis-frame`'s
ISO 8601 nominal-vs-exact duration split across DST, `rebuild-uptime-rollups`'s
stale-authority convention, `filer-access-audit`'s RFC 8881).
**Result: pass@2 2/2 solved, 16/16 tests, both agents correctly used
zoneinfo/real DST handling and solved in 5-8 minutes.** This is the load-
bearing result — the one design that followed the proven playbook formula
to the letter still fell to recall/transcription.

## What this pattern actually shows

Four designs, four "2/2 solved" verdicts, spanning two structurally
different crux families (statistics-formula recall AND real-convention
procedural reconstruction). The common thread across ALL of them, stated
precisely: **whenever every deciding rule is fully and unambiguously stated
in `instruction.md` — however many rules, however entangled, however
grounded in a real external standard with genuine domain nuance (DST) — this
specific benchmarked model (Opus-4.8 via Terminus-2) correctly transcribes
it, every time, in under 10 minutes.** This held even when I deliberately
built the fifth design to match the exact shape (real standard, premise-only
disclosure, latent-until-DST-season edge case) that produced 0/5 in
`experiment-analysis-frame` (the closest same-category precedent) and 0/5 in
several other corpus tasks.

The one thing NOT tried: leaving a rule's premise **undisclosed** and
requiring the agent to infer/derive it from evidence in the sample data
(Pattern D). This is deliberately avoided per
`dynamo_enumeration_defeats_evidence_inference` (memory), which documents
**three independent confirmed instances** of this exact model/agent pairing
defeating "arbitrary convention inferable from small evidence" via
systematic hypothesis enumeration — not derivation, but trying the small set
of natural candidate readings against the shown evidence and picking
whichever matches. Given the session-reconstruction domain has a genuinely
small candidate space per axis (2-3 natural readings each), Pattern D would
very likely reproduce that exact wall rather than solve the problem.

## The decision this handoff exists to get

Two live options, neither of which I should pick alone at this point:

**Option A — relax the design constraint, accept enumeration risk.**
Attempt a 6th design using Pattern D (an ambiguous convention resolved only
by evidence in the sample, never stated in prose) despite it being the one
approach with three independent documented failures against this exact
model/agent pairing. This is not "trying harder," it's knowingly walking
into a wall that has already been mapped three times on different domains.
Low expected value unless there's a way to make the candidate space large
enough that enumeration itself becomes infeasible (hard to construct
credibly — most real conventions have 2-4 natural readings, not dozens).

**Option B — reconsider whether pure "Exploratory data analysis" is the
right subcategory shape for this task, and discuss with the user whether an
inference-flavored crux belonging to a sibling subcategory (e.g. "Statistical
analysis and inference" or "Experiment and metrics analysis") would be
acceptable, accepting the category/subcategory-mismatch risk this carries
(per doc 40/41: a task whose category doesn't match what the PR implements
is still Accept-able at a 3/5 quality score, logging the mismatch for the
platform to correct — NOT an automatic Reject). This is explicitly a
judgment call the user should make, not one to assume.

**Option C — accept more iteration cycles are worth it and try a genuinely
different EDA mechanism family** not yet attempted (e.g., something in
dataset-preparation/data-quality territory rather than statistics or
session-log reconstruction — schema inference, duplicate/near-duplicate
detection with a real fuzzy-matching convention, etc.) The risk: nothing
guarantees a 6th mechanism avoids the same "fully disclosed procedural rule
gets transcribed" wall — three of the four failures so far were exactly
that, regardless of domain.

## What is NOT the problem (ruled out, don't re-litigate)

- **Mechanical soundness.** Every design cleared oracle=1.0, nop=0.0, a full
  mutation battery (4-10 mutants per design, all killed with redundancy),
  and the exact "agent behavior that would have solved the prior design"
  test run through the real verifier and confirmed at 0.0 before every push.
- **Disclosure fairness.** No `qc_gate`/`deep_review`/`ava_review` block has
  ever fired on this PR — every failure has been pass@2 (too easy) or the
  static rubric (too small in scope, fixed by design 4).
- **CI/infra hygiene.** `.dockerignore`, LF line endings (verified via
  direct blob byte-inspection, not `grep -c` which is unreliable on Git
  Bash), no AI attribution, README/task.toml synced every commit — all
  clean throughout.
- **The instruction suffix line.** Correctly omitted throughout per the
  corpus's unanimous finding (confirmed nowhere in this PR's history either).

## Mandatory rules to keep following if iteration resumes

- `harbor run -p . --agent oracle` must show reward 1.0 and `--agent nop`
  must show reward < 1.0 before every push.
- Before every push, build the exact "agent behavior that solved the prior
  design" as a real mutant and confirm 0.0 through the real (harbor) verifier
  — this has caught real gaps every single time it's been done.
- `README.md` sync is mandatory on every commit touching
  instruction/solution/verifier/difficulty/gate behavior — diff against it
  before every `git commit`.
- Strip CR bytes and verify LF-clean via direct blob inspection
  (`git show :path | grep -c $'\r'` is unreliable — use a Python byte check)
  before every commit; this repo's working tree defaults to CRLF.
- Per the user's standing instruction for this session: iterate
  autonomously, do not wait for responses, fix/redesign within category and
  subcategory. This handoff exists because the pattern has now repeated
  four times on genuinely different mechanisms — per
  `dynamo_pause_on_failure_after_long_iteration`, that is exactly the signal
  to stop and let the user weigh in on strategy rather than attempt a sixth
  guess alone.

## When the task finishes (accepted, or the user decides on a genuine dead end)

Write a case-study markdown into
`C:\Users\chara\Downloads\Handshake\dynamo-task-playbook\` (see other files
there for format), folding in this handoff's content and the final outcome,
then `git add`/`commit`/`git pull --rebase`/`git push` to `origin main` from
inside that folder — delete this handoff file in the same commit.
