HANDOFF: dynamo-6b21614-software-engineering (PR #3)
=====================================================
Last updated: after pushing commit `1335a3e` (2026-08-30). Everything
below the first "UPDATE (2026-08-29)" marker is the original handoff as
it stood at `d07d273`, kept for full history; read the updates below
first, most recent first.

-----------------------------------------------------------------------
FOURTH UPDATE (2026-08-30): pass@2 2/2-solved again on `b54c620` (the
composition-depth fix) -- but the bot's own language keeps confirming
this is ordinary iteration, not saturation.
-----------------------------------------------------------------------
`b54c620` also came back 2/2 solved (~9 and ~17 min, all 18 tests), but
critically the pass2-difficulty-suggestion's language SHARPENED, not
weakened: "The `Vec<Scope>` + per-scope `HashMap` with entry-depth
watermark truncation is the natural Rust idiom for the disclosed
contract, and both agents converged on it independently... The three
composition tests added after the prior round did not introduce a case
that breaks the natural implementation." This is a genuine "the natural
correct idiom already satisfies everything disclosed" result, not a
"training-data-memorized problem class" result -- there is still no
`saturated_crux_family`-style language anywhere across three consecutive
rounds on this specific design. The bot named one concrete, previously
undisclosed-but-fair edge instead: `journal_validate`'s snapshot-vs-live
semantics when the callback writes to the CURRENT scope during iteration
(adds a new key, or overwrites an already-snapshotted, not-yet-visited
key). The reference already implements snapshot-at-entry (captures
`Vec<(String,String)>` once before the callback loop even starts) but
never disclosed or tested it. Fixed: added one sentence to both
`instruction.md` and `journal.h`'s doc comment stating the snapshot rule
explicitly, and one new test (`test_validate_iterates_a_snapshot_of_the_current_scope`)
where the callback both adds a later key and overwrites an earlier one
mid-iteration -- asserting neither affects the in-flight visitation, but
both are real (visible via `GET`) once `validate` returns. A seventh
mutant (re-reading the live scope map on every step instead of
snapshotting at entry) confirmed caught. Recalibrated from a fresh clone,
pushed as `1335a3e`.

**Next steps:** watch `gh pr checks 3` for `1335a3e`. This is now the
FOURTH consecutive escalation round on the exact same crux family
(reentrant scope-stack bookkeeping) with the bot naming a real, specific,
fixable gap each time rather than declaring the shape saturated -- a
meaningfully different trajectory than every earlier design on this PR,
which hit "well-represented in training data" language on the FIRST or
SECOND attempt every time. If `pass@2` solves 2/2 a THIRD time on this
exact design with the bot again naming something concrete and fixable,
keep iterating -- this pattern (concrete, addressable gaps rather than
"whole shape is known") is itself evidence this is a genuinely richer
crux family than the earlier three designs, not a sign to give up. If the
bot's language ever shifts to saturation language ("well-represented in
training data for this class of problem", "no meaningful divergence from
the golden approach"), that's the actual signal to stop and consult
[[dynamo_saturated_crux_families]] / [[dynamo_problem_class_saturation]]
before continuing.

-----------------------------------------------------------------------

-----------------------------------------------------------------------
THIRD UPDATE (2026-08-30): pass@2 flipped to 2/2-solved on the id-fix
commit -- diagnosed as ordinary shallow-coverage escalation, not
saturation, fixed with three composition tests, re-pushed.
-----------------------------------------------------------------------
Commit `45b5b30` (the qc_gate id-uniqueness fix) re-rolled the whole
pipeline and `pass@2` came back 2/2 solved in ~16 min (both trials solved
all 15 tests in ~10-12 min each) -- a flip from the PASS on the immediately
preceding commit (`58ec4e7`, 52m34s). Per the standing rule to stop and
verify before reacting to a result like this
([[dynamo_stop_and_verify_on_next_failure]]), checked: nothing about the
crux itself changed between the two commits -- `journal_reference.rs`,
`journal.h`, and `instruction.md` were untouched; only the id-value
test/client-output fix changed. The `pass2-difficulty-suggestion` comment's
own root-cause language confirmed this is NOT the "whole shape is
saturated" pattern that killed the first three designs: it named a
specific, narrow, fixable gap -- `tests/test_outputs.py` only exercised
each disclosed rule in isolation with shallow scenarios (at most two
levels of nesting, one reentrant savepoint per callback, rollback/release
only of the outermost open scope) -- not "this problem class is
well-represented in training data" language. It gave three concrete,
well-reasoned composition suggestions, all still built from already-
disclosed rules (not new hidden facts): rollback of a *middle*, not
outermost, open savepoint; a three-level release with the same key
written at every level; and a validate rejection where the callback
commits one reentrant savepoint before abandoning a second. Implemented
all three verbatim as new tests, verified each by hand-tracing against the
reference (all correct on the first try, all 18 tests pass), and added a
sixth mutant (rollback ignoring which id was named, always closing only
the top frame -- the exact bug the suggestion's first point named) which
is caught only by the new middle-rollback test; the original five-mutant
battery re-confirmed clean. Recalibrated from a fresh clone (oracle=1.0,
nop=0.0) and pushed as `b54c620`. Also worth noting for calibrating
expectations: the ORIGINAL pass@2 PASS (`58ec4e7`) was itself weak
evidence of genuine crux difficulty -- one trial's fail was an off-crux
Rust `RefCell` borrow-checker compile error, which `deep_review` correctly
graded `difficulty_evidence = N/A`, not a positive confirmation. This new
2/2-solved result is, if anything, more informative than the PASS it
replaced.

**Next steps:** watch `gh pr checks 3` for the pipeline to complete on
`b54c620`, especially `pass@2` again. If this ALSO comes back 2/2 solved,
that would be the first real signal (two clean solves on genuinely
different scenario depths within the SAME crux family) that the
reentrant-scope-stack shape itself, not just shallow test coverage, may be
approaching saturation for this model -- worth writing up as a sharpening
of [[dynamo_saturated_crux_families]] if it happens. If it produces a
genuine valid fail, proceed to `qc_gate` (should be clean, but re-check)
and `pass@5` -- the actual target.

-----------------------------------------------------------------------
SECOND UPDATE (2026-08-30): pass@2 PASSED once, then qc_gate found a real
bug, fixed, re-pushed. (Superseded in part by the THIRD UPDATE above --
the pass@2 PASS described here did not survive the qc_gate-fix re-push.)
-----------------------------------------------------------------------

-----------------------------------------------------------------------
SECOND UPDATE (2026-08-30): pass@2 PASSED, then qc_gate found a real bug,
fixed, re-pushed.
-----------------------------------------------------------------------
Commit `58ec4e7` (journal-savepoints + the docstring fix from rubric
review) cleared `review`, `validation`, `pass@2` (52m34s), `deep_review`,
`qc_eval`, `qc_exec`, `ava_review`, `tier1` -- but `qc_gate` failed with
two linked MUST-FIX items, both really one root cause: `tests/test_outputs.py`
hardcoded the *exact numeric value* of every savepoint id (`BEGIN sp1 = 1`,
`BEGIN sp2 = 2`, ...), which `journal.h` never promises -- only "positive,
never reused" -- so (a) a length-based `id = scopes.len()+1` mutant (which
silently reuses an id after a release shrinks the stack, violating the
disclosed never-reused contract) passed all 14 tests, a narrow/hardcodable
coverage hole; and (b) the suite was simultaneously enforcing an
*undocumented* requirement (exact id numbering) in the other direction.
Fixed both at once, pushed as `45b5b30`: the C client's `BEGIN` op no
longer prints the id it was assigned (`= ok`, not `= <n>`), and a new
`DISTINCT label1 label2` op/test compares two labels' ids -- without ever
revealing either -- across a release and a rollback, directly pinning the
never-reused property. A fifth mutant (the literal one QC found,
`scopes.len()+1`) was built and confirmed caught only by the new test,
alongside a clean re-run of the original four-mutant battery. Both
`harbor run --agent oracle`/`--agent nop` were re-run from a **fresh git
clone** (see the separate note below on why that matters now) before this
push, not just the working directory.

Separately, between the first push of this design (`4dd3de9`) and the
pass@2 PASS, one more real bug surfaced and was fixed: the first push's
local `oracle=1.0` calibration turned out to be an artifact of my own
working directory, not the actual committed tree -- see
[[dynamo_local_calibration_needs_fresh_clone]] (new memory file) for the
full mechanism (an empty, git-untracked `environment/journal/src/`
directory existed locally from earlier testing but was never in any
commit, so a real checkout had no `src/` at all and the remote
`review / validation` oracle check failed with reward 0.000 despite two
clean local `harbor run` results). Fixed by committing a `.gitkeep` in that directory and having
`solution/solve.sh` `mkdir -p` it defensively -- this fix and the
docstring fix from rubric review both landed by commit `58ec4e7`, which is
the commit that then went on to pass `pass@2`.
**Practical upshot for whoever resumes:** from this point on in this task,
always validate `harbor run --agent oracle`/`--agent nop` from a fresh
`git clone`, not the working directory, before any push that adds new
files/directories.

**Next steps:** watch `gh pr checks 3` for `review`, `validation`, and
especially `pass@2` to reproduce on commit `45b5b30` (pushing re-rolls the
whole pipeline; the earlier PASS on `58ec4e7` does not carry over
automatically). If pass@2 passes again, the next real gate is `qc_gate`
again (should now be clean, but re-check for anything new) and then
`pass@5` -- the actual target this whole PR has been chasing. If pass@2
somehow flips to 2/2-solved on this commit despite passing on the last
one, that would be a genuinely strange result worth a full stop-and-verify
pass (re-read this whole file) before reacting, since nothing about the
crux itself changed between the two pushes, only test/verifier-side
bookkeeping.

-----------------------------------------------------------------------

-----------------------------------------------------------------------
UPDATE (2026-08-29): FOURTH DESIGN PUSHED, commit `4dd3de9`, awaiting
gates. User chose "try compound-breadth instead" over continuing to hunt
for a single obscure real-world convention (option A) or accepting a dead
end (option C). A fresh-domain research pass (three legacy-format
modernization candidates: COBOL COMP-3 packed decimal, ZIP general-purpose
bit flags, AppleSingle/AppleDouble) found no buildable candidate -- all
three died on the non-mainstream or fetch-resistance filters, same as six
earlier candidates on this PR. While checking git/PR state per
[[dynamo_verify_git_state_before_resuming]], found this exact task repo
already has a genuinely relevant CLOSED PR #2 by a different author
("Refactor reentrant relay ABI contract", `dynamo/reentrant-abi`): a Rust
cdylib preserving a C ABI with 7 coupled contracts (reentrant-frame errno
snapshotting across nested/re-entering callback invocations, cancellation-
consumption boundary, unwind containment, allocator ownership, a
destruction tombstone, context-local value computation, legacy-symbol
removal). It got real difficulty -- pass@2 1/2 (genuine valid fail),
pass@5 3/5 (avg@5=0.600) -- blocked only by the platform's specific gate
arithmetic (needed one more failure of a particular type) and two
pre-existing QC issues, not by being too easy. Both pass@5 failures shared
one root cause: mishandling errno state across nested/reentrant call
frames on frame-pop, EVEN THOUGH the governing rule was stated explicitly
in the instruction. This is a materially different difficulty source than
everything tried on this PR before: not "recall/derive a fact" but
"correctly thread state through nested/reentrant bookkeeping," which
survives disclosure in a way pure spec-transcription doesn't.

Fourth design, `dynamo/journal-savepoints`: a Rust cdylib reimplementing a
legacy key-value "journal" library with SAVEPOINT-style nested transaction
scopes against a fixed C header (`journal.h`), deliberately structured
around the SAME difficulty source (a scope stack manipulated by nested and
reentrant operations) but a different concrete scenario, mechanism set,
and story than PR #2's relay-ABI design (to avoid duplicate-similarity
risk and because it's independently authored content). Four coupled rules,
all stated precisely in instruction.md (fairness first, per this task's
whole prior history): layered read visibility across nested scopes;
`journal_savepoint_release(id)` folding not just `id`'s own writes but
every still-open nested child's into `id`'s parent, innermost-wins on a
shared key, closing everything folded; `journal_savepoint_rollback(id)`
discarding `id`'s own writes and everything nested inside it, but --
unlike release -- leaving `id` itself open afterward; and
`journal_validate`'s reentrant callback contract, where the callback may
call back into the same handle (including opening its own nested
savepoints) before accepting/rejecting a key, and a rejection must discard
exactly the savepoints opened during the call and left open when it
returns -- both directions graded: never leaking one the callback opened
and left open, and never undoing one the callback opened AND itself
already explicitly released (committing it into an ancestor) before the
rejection happened. That second direction is the sharpest test in the
suite -- it directly punishes the natural "just restore everything to how
it was on entry" shortcut a full-state-snapshot implementation would take.

Built and verified locally before push: Docker image built from a fresh
`ubuntu:24.04` base (rustc + build-essential + pytest baked in, matching
the proven-working precedent from PR #2's own Dockerfile, including
reusing its exact pinned base-image digest). Reference `journal.rs`
compiles and all 14 tests in `tests/test_outputs.py` pass against it (a
real `rustc`-built cdylib driven by a small hand-written C client,
`tests/clients/client.c`, that interprets a line-based op script -- not
Python calling into Rust, and not source inspection). A four-mutant
battery was built and run inside the same Docker image BEFORE pushing,
confirming each rule is independently load-bearing: (1) release that only
merges `id`'s own frame, ignoring a nested unreleased child -- caught by
`test_release_folds_nested_children`; (2) rollback that closes `id` like
release does instead of leaving it open -- caught by two tests
(`test_rollback_keeps_savepoint_open`, `test_rollback_discards_nested_children`);
(3) validate that never cleans up a leaked reentrant scope on rejection --
caught by `test_validate_reject_discards_unreleased_reentrant_work`; (4)
validate that over-rolls-back via a full-state snapshot/restore instead of
a depth-based truncate, wrongly undoing already-committed work -- caught
by `test_validate_reject_preserves_already_committed_reentrant_work`. None
of the four mutants scored a false 1.0. `harbor run -p . --agent oracle` =
1.0, `--agent nop` = 0.0, both confirmed locally right before push.
Pushed to `fork/submission` at commit `4dd3de9`; no run was in flight at
push time (checked `gh pr checks 3` first, per standing rule).

**Next steps for whoever picks this up:** watch `gh pr checks 3 --repo
handshake-project-dynamo/dynamo-6b21614-software-engineering` for the
rubric-review result first (fast, minutes) -- if it clears
`code_dependent`/`essential_difficulty` (should, per the CLI/real-build/
real-C-client-execution shape, matching the reasoning that already fixed
this exact gate on this exact PR twice), then watch for `pass2` (slow,
~25-30 min per PR #2's precedent). A genuine valid fail on pass2 is the
goal this time, unlike every prior design on this PR where 2/2-solved was
the actual failure mode. If pass2 comes back 2/2 solved anyway, read the
trial trace's root-cause language carefully before reacting -- distinguish
"the reentrant-bookkeeping shape itself is now also saturated for this
model" (a genuinely new, itself-interesting finding, worth its own memory
entry) from "this specific mechanism set was too easy relative to PR #2's"
(routine escalation, e.g. add a second reentrant crux or a third nesting
level) per [[dynamo_saturated_crux_families]]'s shortcut-vs-mastery
distinction. If it produces a genuine valid fail and clears qc_gate, this
is the strongest result this PR has had across four designs -- treat any
gate friction from there as normal iteration, not a redesign signal.

-----------------------------------------------------------------------
ORIGINAL HANDOFF (as of commit `d07d273`, kept for full history below)
-----------------------------------------------------------------------

-----------------------------------------------------------------------
STATUS IN ONE SENTENCE: three structurally different task designs across
ten commits, all eventually reaching a clean rubric-review pass and clean
oracle=1.0/nop=0.0 calibration — but `pass@2` has returned 2/2 solved on
every single attempt (7 total pass@2 runs), the last three in a row on the
current design with explicitly "None" approach-diff and the platform's own
language ("straightforwardly derivable... well-supported by training data
for this class of problem"). This is a decision point, not a bug to fix.
`pass@2` is a HARD GATE — it must show ≥1 genuine failure before `pass@5`
is even allowed to run, so this task cannot be submitted in its current
form no matter how sound everything else about it is.
-----------------------------------------------------------------------

## Repo / PR pointers

- Local clone: `C:\Users\chara\Downloads\Handshake\dynamo-6b21614-software-engineering`
- Fork remote: `fork` -> `https://github.com/charan-sr/dynamo-6b21614-software-engineering.git`
- Base remote: `origin` -> `https://github.com/handshake-project-dynamo/dynamo-6b21614-software-engineering.git`
- Branch: `submission`, currently at commit `d07d273` (nothing uncommitted)
- PR: https://github.com/handshake-project-dynamo/dynamo-6b21614-software-engineering/pull/3
- Category/subcategory (pre-seeded in `task/task.toml`, fixed — do not edit): **Software Engineering / Refactoring and Code Modernization**
- Model/agent under test (pre-seeded in `task/task.toml`, fixed — do not edit): `model_tested = "Opus-4.8"`, `agent_tested = "Terminus-2"`. (Note: `verify/project_dynamo/project_dynamo/26-...md` generically states the recorded score must come from GPT-5.4/Terminus-2 at `xhigh` effort — this specific dataset's pre-seeded `task.toml` says Opus-4.8 instead; trust `task.toml`, it is this task's ground truth, not the generic doc.)
- Root `README.md` and `task/task.toml`'s three explanation fields describe the *current* (third/CLI) design in full and are in sync with it as of `d07d273`.
- `pass@2` rate-limit counter (`review / ratelimit` job) has read "0 executions in the last 24h (limit 6)" on every check throughout this whole session, including after 7 real pass@2 runs — this counter does not appear to be incrementing correctly on the platform's side. Do not trust it as a live budget signal either way; it has never shown `over=true` regardless. If continuing, just don't push over an in-flight run, same as always — no evidence of being budget-blocked, but also no reliable confirmation of headroom from this specific counter.

## The three designs, in order, and exactly why each failed or was rejected

**Design 1 — `modernize-template-resolver` (commits `5bc9108`..`c8ecd04`, 6 commits).**
A custom `%{NAME}` / `%{NAME|DEFAULT}` placeholder-template resolver
(CLI, reads a template file + a JSON values file, writes resolved text),
extended with `%{?NAME}BODY%{/}` conditional sections. Fully-disclosed
grammar; instruction stated behavior only, not the parsing algorithm
(after an early revision — see below). Difficulty axes: escape-aware
nested-delimiter depth counting, no-rescan/injection-safety, absent-vs-empty
sentinel distinction, and (in the second escalation) block-nesting section
matching that must skip nested placeholders as opaque units.
- `5bc9108`/`7f7a381`: initial push. `06c2842`: fixed a static-check FAIL
  (Dockerfile comment literally contained the substring `tests/test.sh`,
  which the platform's static check bans anywhere in the Dockerfile,
  including comments — a known, easy-to-forget trap; grep the whole
  Dockerfile for `solution/`/`tests/` before every push).
- `6b6c43e`: **pass@2 came back 2/2 solved.** The pass@2 bot's own
  diagnosis: the instruction had explicitly named the depth-counter
  algorithm and stated "resolved text is never re-scanned" as an explicit
  rule — handing the reference architecture directly to the agent.
  Rewrote the grammar to state only observable behavior + a declarative
  "nests like matched brackets" delimiter rule, removing all algorithmic
  language.
- `c8ecd04`: **pass@2 came back 2/2 solved again**, even fully declarative.
  The bot's analysis: both agents independently reconstructed the exact
  escape-aware, no-rescan recursive-descent parser in 3-11 minutes,
  explicitly because "this specific crux is within the capability
  envelope of current frontier models... a standard placeholder-expansion
  problem well-represented in training data." This is Pattern-A/family
  saturation, not a wording problem. The bot's own suggested escalation
  (a second, structurally different construct — conditional sections,
  matched by block-nesting rather than simple bracket depth) was
  implemented.
- **Result after the section escalation: pass@2 2/2 solved a THIRD time.**
  Both agents correctly implemented sections too (skipped-body-still-
  syntax-checked, escaped-tag-in-body, undefined-name-in-skipped-body-not-
  an-error, nested-section-depth-matching — all four of the bot's named
  subtleties, applied correctly). Abandoned this design entirely at this
  point rather than add a third construct to the same parser-shaped task,
  per `dynamo_saturated_crux_families` (memory): the whole "recursive-
  descent parsing against a fully-disclosed formal grammar" *shape* is
  saturated for this model, independent of how much grammar complexity is
  piled on.

**Design 2a — `fix-memoize-decorator` (commit `af4b355`).**
Pivoted to a different reasoning domain entirely: fix a legacy
`memoize(fn)` decorator's keyword-argument cache-key bug (real, common:
`functools.lru_cache` has this exact same limitation, so it can't be used
as a shortcut oracle), plus add exception-caching and hashability-
rejection with careful ordering. Oracle=1.0/nop=0.0 confirmed locally.
**Result: REJECTED OUTRIGHT by automated rubric review, before pass@2 ever
ran.** `code_dependent` FAIL and `essential_difficulty` FAIL: "Solvable in
one generation... no genuine multi-step environment interaction/
exploration required... an average undergraduate solves it in an
afternoon." A single ~30-line pure-function decorator, verified by
importing and calling it directly from unit tests, structurally cannot
satisfy `code_dependent` no matter how many subtle interacting bugs it
composes — there is no environment to explore, nothing to run and observe,
just "read spec, write function."

**Design 2b — `fix-settings-merge` (commit `cfa87c1`).**
Same lesson not yet learned: a `settings.py` function library
(`coerce_env_value` / `deep_merge` / `resolve_settings`, three functions),
plus a shipped partial self-test script (`settings_selftest.py`) the agent
could run for feedback. **Result: REJECTED OUTRIGHT again, same two
criteria.** The reviewer's exact words: "a strong model one-shots the
module and optionally runs `settings_selftest.py` once." A shipped
*optional* self-test does not create genuine multi-step interaction if the
whole task is still knowable/solvable from the prose spec in one shot.

**Design 3 — `fix-settings-cli` (commits `7e63bec`..`d07d273`, the current
design).** Structural fix, not cosmetic: reverted to a CLI/file-I/O shape
— the exact shape Design 1 used, which *never once* failed rubric review
across all its commits (only pass@2 killed it, on different grounds).
`/app/resolve_settings.py` reads a defaults JSON file, zero or more layer
JSON files, and real `SETTING_<PATH>`-prefixed OS environment variables
(read via `os.environ`, genuine environment interaction a pure function
call cannot offer), and writes a resolved JSON output file. Same
underlying bug/logic content as design 2b (recursive deep-merge with
type-mismatch replacement, non-mutating/non-aliasing merge, type-directed
string coercion stricter than `int()`/`float()`), reframed as a CLI.
- `7e63bec`: **Rubric review PASSED immediately** — confirms the
  code_dependent/essential_difficulty fix was structural (CLI + real file
  + real env-var I/O), not about difficulty content.
  **pass@2 came back 2/2 solved.** Genuine, well-targeted gap found by the
  bot: two `SETTING_<PATH>` variables with *overlapping* paths (e.g.
  `SETTING_A` and `SETTING_A__B`, one a prefix of the other) were neither
  disclosed nor tested; both agents' naive `os.environ` iteration order
  happened to never matter against the shipped suite.
- `6d755fe`: Disclosed a deterministic fold order (ascending lexicographic
  by full variable name, each folded via the same type-mismatch rule) and
  added a test that inserts the two overlapping variables into the
  subprocess environment in the *reverse* of that order (so an
  iteration-order-dependent bug can't pass by accident). **pass@2 came
  back 2/2 solved again** — this time with explicitly **"None" approach
  diff** in both trials and the platform's language: "straightforwardly
  derivable from the specification rather than requiring unusual
  first-principles reasoning." Full saturation, zero gap, for this whole
  axis family (recursive merge + typed coercion + nested-key parsing +
  overlap-ordering all reduce to variations of one idiom: `deep_merge` +
  type-directed dispatch).
- `d07d273`: Deliberately added a mechanism from what looked like a
  genuinely *different* family, specifically to test whether "different
  idiom" (not just "different axis") would survive: every JSON input file
  must reject a duplicate key at any nesting depth. This cannot be
  detected by inspecting `json.load`'s *output* at all — Python's parser
  silently keeps only the last value on a duplicate key by default, so the
  duplicate is already gone by the time a post-parse dict could be
  checked; catching it requires a custom `object_pairs_hook` intercepting
  during parsing itself, which has nothing to do with merge/coercion
  logic. Verified locally: oracle=1.0/nop=0.0, legacy stub (plain
  `json.load`, silently accepts duplicates) fails 29/34 tests.
  **Result: pass@2 2/2 solved a THIRD consecutive time on this design**
  (18/18 tests, both trials), with the bot's diagnosis sharper than ever:
  both agents independently reproduced `object_pairs_hook` correctly too,
  and the platform's stated root cause is that `instruction.md`
  "pre-digests each difficulty crux into explicit implementation-level
  prose, so the agent can transcribe the rules rather than derive
  them... well-supported by training data for this class of
  config-merging problem." **No push made after this result** — this
  handoff was written instead.

## What this pattern actually shows (the load-bearing finding)

Ten commits, three structurally distinct task designs, **seven total
pass@2 runs, seven solved 2/2**, spanning two genuinely different reasoning
domains (string-grammar parsing, and dict-merging/type-coercion/JSON
parsing) and, within the second domain, four genuinely independent
mechanisms (recursive merge, string-to-type coercion, nested-key path
parsing, multi-variable fold-order determinism, and JSON duplicate-key
detection via `object_pairs_hook`). The common thread, confirmed
repeatedly and now sharpened past what the pre-existing memory files
already say:

**Old rule (`dynamo_enumeration_defeats_evidence_inference`, already in
memory): if a competent expert could derive the unique correct output
purely by reasoning from a disclosed definition, expect a clean 2/2 solve,
however obscure or complex it feels.** This held on every single design
here — every rule was fully, precisely disclosed (for fairness), and every
one was transcribed correctly.

**New, sharper finding from THIS task specifically, worth adding to
memory if not already captured:** it is not enough to make an added axis
mechanically *different* (parsing vs. merging vs. JSON-parsing-internals)
if the axis still lives inside the same **saturated tutorial problem
domain**. "Layered settings/config resolution" (defaults -> file config ->
env overrides) is itself an extremely common software-engineering
tutorial/blog-post/interview-question subject, in the same way "implement
a template engine" or "implement a placeholder resolver" is. The model
appears to recognize the *problem class* from training data, not just
individual mechanisms within it — so genuinely different *implementation
techniques* (recursive merge vs. `object_pairs_hook` vs. lexicographic
fold-ordering) still all get solved once the surrounding problem is
"config merging," because that whole class is well-covered. This is a
refinement of, not a contradiction of, `dynamo_saturated_crux_families`
(which frames saturation at the *mechanism family* level, e.g. "POSIX
archive restoration gotchas") — here the saturation appears to operate one
level up, at the *problem-class* level (e.g. "config/settings layering"),
which is a broader and more expensive-to-notice unit than a single
mechanism family. **Escaping likely requires changing the underlying
problem domain, not just the specific bug/mechanism within it — and this
task's placeholder-parser design (a different domain entirely) hit the
exact same wall, suggesting the effect isn't specific to config-merging
either; it may be that any "fully-disclosed, precisely-specified spec ->
implement it" task shape is capped for this model regardless of domain,
unless something genuinely arbitrary/external and non-fetchable is
injected.**

## Candidates already researched and ruled out this session (don't re-litigate)

Extensive real-world-convention research was done searching for a "real,
external, genuinely obscure, disprovably-specific, non-trivially-fetchable"
crux per the escape-route formula in `dynamo_enumeration_defeats_evidence_inference`.
All of the following were vetted and rejected, with reasons — do not
re-spend time re-discovering these:
- **WHATWG MIME-sniffing spec** (byte-signature table) — killed: at least
  three pip-installable pure-Python packages (`mimesniff`, `xtractmime`,
  `sniffpy`) implement it directly; trivial local oracle.
- **Real `git config --type=bool` boolean grammar** — actually verified
  empirically in the target image (`docker run debian:bookworm-slim`,
  installed real git, probed dozens of input strings): recognizes
  true/yes/on/1 and false/no/off/0/empty (case-insensitive), rejects
  whitespace AND single-letter abbreviations (t/f/y/n all rejected — a
  genuinely good "plausible guess is wrong" property), and a bare key with
  no value means true. Killed anyway: naming `git config --type=bool` as
  the target makes it a **trivial one-command CLI oracle** (`git
  config --type=bool <value>` directly answers the exact question for any
  input) — exactly the "local-oracle test" failure mode the playbook
  warns about. (`dulwich.config.ConfigDict.get_boolean`, a pure-Python
  pip-installable alternative, was also checked and found to be a
  dangerously *wrong* oracle — it only recognizes literal true/false and
  rejects everything else including yes/no/on/off/1/0 — interesting as a
  potential misdirection lever but not pursued further for time reasons.)
- **`dpkg --compare-versions` / Debian version ordering** — killed:
  `python-debian`'s `debian.debian_support.Version` is a pure-Python
  pip-installable reimplementation.
- **PE/COFF binary format parsing** — killed: `pefile` is a
  well-established pure-Python pip-installable parser.
- **CRC variant catalogs** (Modbus CRC-16, CRC-32/BZIP2, etc.) — killed on
  paper: Wikipedia's "Catalogue of parametrised CRC algorithms" is as
  complete and machine-readable a reference as any pip package; naming a
  specific variant makes its exact parameters trivially look-up-able.
- **Unicode case-folding subtleties** (e.g. German ß) applied to env-var
  name matching — killed on paper: contrived/unrealistic fit, since real
  POSIX env var names are conventionally ASCII-only; would fail
  `interesting_realistic`.
- **JSON array/list merge semantics** — this was the pass@2 bot's OWN
  suggested next axis (index-wise element merge with per-element
  coercion). Deliberately NOT pursued: it is still just one more variant
  of the same `deep_merge` idiom already shown saturated, matching the
  exact "strengthening a saturated family" anti-pattern
  `dynamo_saturated_crux_families` warns against.

## The decision this handoff exists to get

Three live options, per the user's own framing when this handoff was
requested:

**Option A — user points to a specific real, obscure convention or tool.**
The searches above were reasonably thorough but are bounded by what one
session could think of and verify quickly; the user's own domain
knowledge may surface something better than anything tried here. If given
one, verify it against the exact target Docker image (never trust memory/
training data for the exact behavior — see `dynamo_verify_os_behavior_in_image`),
confirm no pip-installable or single-CLI-command oracle exists for it,
and build around it using the now-proven-reliable CLI/file-I/O task shape
(reuse `task/environment/Dockerfile`, the general test-suite structure in
`task/tests/test_outputs.py`, and the calibration workflow below).

**Option B — try one more genuinely fresh problem domain**, on the
next session's own judgment, moving further from "config/settings/
parsing" than anything tried here (e.g. binary checksum computation,
compiler/linker-adjacent tooling, something in a real but rarely-
tutorialized corner of software engineering). Open-ended effort, no
guarantee — the "problem-class saturation" finding above means the new
domain must be checked for tutorial/blog-post density, not just mechanism
novelty, before investing in it. Genuinely verify a candidate is NOT
"config merging" or "template/parser" flavored, and sanity-check it isn't
itself a well-worn tutorial topic (a good gut check per the corpus: "would
a competent engineer already know the decisive edge case, or would they
need to open a spec/probe a real system?").

**Option C — accept this as a documented dead end for this PR** and move
the fellow's effort to a different task assignment. This handoff plus the
case study written alongside it (see below) already captures real,
generalizable value for the next task's design (the problem-class-
saturation finding is new and worth having in memory regardless of what
happens to this specific PR).

## What is NOT the problem (ruled out, don't re-litigate)

- **Mechanical soundness.** Every design that reached rubric review
  cleared it; the current design's oracle=1.0/nop=0.0 calibration and all
  34 local tests are clean and verified against real subprocess execution,
  not just unit-level function calls.
- **Static/CI hygiene.** `.dockerignore` present from the first commit of
  each Dockerfile revision, no `solution/`/`tests/` substrings anywhere in
  agent-visible files (grepped before every push), LF line endings
  (`.gitattributes` pins this), no AI/Claude attribution anywhere,
  README.md and `task.toml`'s three explanation fields kept in sync with
  every commit that touched instruction/solution/verifier/difficulty/gate
  behavior.
- **Disclosure fairness / `qc_gate`/`deep_review`/`ava_review` blocks.**
  None of these gates has ever fired on this PR — `pass@2` never gets far
  enough to reach them (it's blocked before `qc_gate` etc. even run), and
  the two rubric rejections were about scope/shape (`code_dependent`/
  `essential_difficulty`), not fairness/disclosure criteria.
- **The instruction-suffix line.** Correctly omitted throughout, per the
  corpus's finding that the "You have N seconds..." line is stale/
  prohibited boilerplate despite what an older doc claims.
- **Similarity/duplicate-check.** Every design has cleared `cosine_similarity`
  and the TB2/TB3 duplicate check cleanly; no risk identified there.

## Mandatory rules to keep following if iteration resumes

- `harbor run -p . --agent oracle` must show reward 1.0 and `--agent nop`
  must show reward < 1.0 before every push (run from `task/` inside the
  repo). Also directly verify via `docker build` + manual subprocess/pytest
  execution before trusting `harbor run` alone (this session's practice
  throughout).
- Grep the entire agent-visible surface (`task/environment/Dockerfile`,
  everything under `task/environment/data/`, `task/instruction.md`) for
  the literal substrings `solution/` and `tests/` before every push — this
  tripped the static gate once already in this PR (commit `06c2842` fixed
  it) and is easy to reintroduce accidentally in a comment.
- `README.md` and `task/task.toml`'s `difficulty_explanation`/
  `solution_explanation`/`verification_explanation` fields must be kept in
  sync with every commit that touches instruction/solution/verifier/
  difficulty/gate behavior — check the diff against current README content
  before every `git commit`, fold the update into the same commit.
- Never push while a run is in flight (`gh pr checks 3 --repo
  handshake-project-dynamo/dynamo-6b21614-software-engineering` — check
  for `pending`/`queued` first).
- Per the user's standing instruction for this session (given explicitly:
  "go ahead with your own judgement dont wait for me unless it is very
  important"): iterate autonomously on routine gate failures. This
  handoff exists because after seven straight `pass@2` 2/2 results across
  three structurally different designs, per `dynamo_pause_on_failure_after_long_iteration`,
  that pattern is exactly the signal to stop and let the user weigh
  strategy (which real-world domain/convention to try) rather than keep
  guessing alone — the same rule that produced the `dynamo-0cfa37b`
  handoff in this same playbook folder, which is worth reading for
  parallel structure (five designs, same "fully disclosed = transcribed"
  wall, in a completely different category).

## When the task finishes (accepted, or the user decides on a genuine dead end)

Write (or fold this handoff's content into) a case-study markdown into
`C:\Users\chara\Downloads\Handshake\dynamo-task-playbook\` (see other
files there, especially `dynamo-0cfa37b-...md`'s handoff-turned-case-study
pattern, for format), then from inside that folder: `git add`, `git
commit`, `git pull --rebase`, `git push` to `origin main` — delete this
handoff file in the same commit once its content has been folded into the
permanent case study.
