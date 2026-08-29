HANDOFF: dynamo-6b21614-software-engineering (PR #3)
=====================================================
Last updated: after pushing commit `d07d273` (2026-08-29). No new commit
made after this result — this handoff exists instead of a further guess.

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
