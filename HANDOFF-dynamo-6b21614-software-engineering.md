HANDOFF: dynamo-6b21614-software-engineering (PR #3)
=====================================================
Last updated: after pushing commit `cb29cda` (2026-08-30). Everything
below the first "UPDATE (2026-08-29)" marker is the original handoff as
it stood at `d07d273`, kept for full history; read the updates below
first, most recent first.

-----------------------------------------------------------------------
NINTH UPDATE (2026-08-30): c794dcb solved 2/2 with a saturation-adjacent
verdict across THREE mechanism types now -- added the one previously
flagged, never-built axis (nested validate-within-validate). Also: a
real TOML syntax bug caught before push, worth a standing process fix.
-----------------------------------------------------------------------
`c794dcb`'s pass@2 (~13-19 min, all 25 tests) solved 2/2 with a
qualitatively different verdict than the concurrency-verifier-gap
critique from the round before: both trials independently applied the
real Berkeley DB tag bytes from stated prior knowledge AND independently
reached correct (if differently shaped -- one `thread_local!`, the other
a `Mutex<HashMap<ThreadId, Box<CString>>>`) per-thread pointer isolation.
The trial report's own language: the task is "a genuine difficulty
filter for agents with strong prior knowledge." This is now THREE
independently-defeated mechanism types on this one design (derivability
of custom scope-stack logic; memorization of an obscure real fact;
derivability/pattern-recognition of a well-known thread-safety idiom) --
a materially stronger signal than any single round, approaching (not yet
using the exact words of) the "well-represented in training data"
saturation register that killed the three earlier designs on this PR.

Per the user's explicit standing instruction ("continue doing this till
the task gets accepted"), did not stop to re-litigate the decision --
implemented the one concrete, previously-flagged-but-never-built lead
still on the table: `journal_validate`'s own "may call back into any
journal_* function" clause was never tested with journal_validate calling
ITSELF (a callback opening a savepoint, writing to it, then recursively
validating that now-current scope) -- only single-level reentrancy
(set/begin/release/rollback from the callback) had been exercised. A
plausible implementation bug this catches: storing the entry-time
watermark as mutable state on the JournalHandle instead of a value local
to each `journal_validate` call -- a nested call then clobbers the outer
call's own watermark, so the outer call's later rejection-cleanup
silently fails to discard what it opened. Had to fix a real limitation in
the TEST HARNESS first: the line-scripted client's VALIDATE handling used
global variables that a genuinely nested (reentrant) VALIDATE call would
have corrupted -- now saved/restored around each VALIDATE invocation.
Confirmed the new test passes against the reference and is caught, only
by itself, by a purpose-built shared-watermark mutant (10th mutant total).

**A real process bug, worth keeping as a standing lesson:** the
`task.toml` edit for this round quoted the platform's own review language
verbatim (`describing the task as "a genuine difficulty filter..."`)
INSIDE an already-double-quoted TOML string field, with the inner quotes
left unescaped -- invalid TOML. This was NOT caught by the standard
`docker build` + pytest suite (which never reads `task.toml`'s prose
fields), only surfacing as a confusing, generic `harbor run` failure
(`ValueError: Either datasets or tasks must be provided`, from deep
inside harbor's task-discovery code, giving no hint it's a TOML parse
error). Found via `git worktree` bisection across recent commits, then
confirmed precisely via `cat task.toml | docker run ... python3 -c
"import tomllib; tomllib.loads(...)"`, which gave the exact line/column
in one shot. Fixed (removed the literal inner quotes) and amended into
the same still-unpushed commit (safe: it had never been pushed, so
amending was appropriate, unlike the standing no-amend rule for already-
public commits). **New standing memory:** [[dynamo_validate_toml_syntax_before_push]]
-- validate `task.toml` with a real TOML parser as an explicit, fast
pre-push step from now on, especially after any edit that quotes review
language verbatim into a prose field.

**Next steps:** watch `gh pr checks 3` for commit `cb29cda`. Given the
strength of the "three mechanism types defeated" signal, if `pass@2`
solves 2/2 again on this round too, seriously weigh whether this design
has reached a genuine, well-documented ceiling for this specific model
(Opus-4.8/Terminus-2) rather than continuing to bolt on more axes --
the user's standing instruction is to keep iterating until acceptance,
but each further round should be weighed on its own merits (is there a
concrete, specific, previously-unexplored lead, or is this now pure
trial-and-error against a wall). If a genuine valid fail lands, proceed
to `qc_gate` and `pass@5`.

-----------------------------------------------------------------------

-----------------------------------------------------------------------
EIGHTH UPDATE (2026-08-30): pass@2 on fdc33ef solved cleanly again, but
the critique targeted the VERIFIER (too weak a concurrency test), not
the mechanism -- strengthened and re-pushed.
-----------------------------------------------------------------------
`fdc33ef`'s pass@2 (~13-21 min, all 24 tests) came back 2/2 solved with a
notably different kind of critique than any prior round: "the shipped
concurrency test used only two keys and one journal_get per thread --
too weak to force a shared scratch buffer or a raw pointer into the
map's own storage to actually manifest a failure." This is NOT a
saturation or memorization signal -- it's a concrete, correct verifier
coverage gap the bot identified, the same "ordinary iteration, harden
the test" pattern as several earlier rounds, just applied to a test's
statistical power rather than its logical coverage.

Built `tests/clients/concurrent_stress_client.c`: 6 threads, 2 of which
("holders") each capture and hold one `journal_get` pointer exactly as
`concurrent_client.c` does, while 4 separate "volume" threads (holding no
pointer of their own) each run 300 `journal_set` calls interleaved with
`journal_get` reads of the holders' keys -- real concurrent traffic at
volume, still barrier-synchronized for a deterministic pass/fail outcome.

**Caught a real bug in my OWN first draft of this test, not the
reference**, worth recording as a general lesson: the first version had
EVERY thread both hold a pointer for later checking AND make further
`journal_get` calls itself during the volume phase -- this violates
`journal.h`'s own stated contract ("valid until the next `journal_get`
call on the same handle from the SAME thread"), so a thread's own later
`journal_get` legitimately invalidates its own earlier pointer. The
correct reference then failed this flawed test 20/20 times, which looked
at first like a reference regression but was actually a test bug -- a
useful reminder that a new concurrency test failing against an
already-proven-correct reference is itself a signal to re-read your own
disclosed contract before assuming the reference is wrong. Fixed by
strictly separating "holder" and "volume" roles so no thread that holds a
pointer for later checking ever calls `journal_get` again itself.

Confirmed: 30/30 clean runs against the reference (0 failures), 20/20
catch rate against the existing shared-scratch-buffer mutant, and the
full 25-test suite stable across 8 consecutive local runs. Recalibrated
from a fresh clone, pushed as `c794dcb`.

**Also worth noting for whoever resumes:** mid-session, a background
gate-status Monitor's notification from a prior push did not carry over
across what looked like a session/context boundary -- the user had to
ask "why did we stop?" after the pass@2 result for `fdc33ef` had already
been sitting complete for a while with nothing acted on. Practical
takeaway: after any apparent gap in activity on a long-running watched
PR, proactively `gh pr checks 3` directly rather than assuming the
monitor will always deliver, especially across compaction/session
boundaries.

**Next steps:** watch `gh pr checks 3` for commit `c794dcb`. If `pass@2`
produces a genuine valid fail, proceed to `qc_gate` and `pass@5`. If it
solves 2/2 again with the SAME kind of "verifier too weak" critique,
keep hardening the same concurrency mechanism (more threads, more
volume, more overlapping keys) -- this is still the "ordinary iteration"
branch, not a wall. If it instead shifts to derivability or memorization
language, treat that as the real signal per the sixth/seventh updates
above.

-----------------------------------------------------------------------

-----------------------------------------------------------------------
SEVENTH UPDATE (2026-08-30): journal_save/journal_load's Berkeley DB tag
values were MEMORIZED, not derived -- a real gap in the project's
obscurity filters. Pivoted to genuine multi-threaded concurrency per the
user's choice.
-----------------------------------------------------------------------
Commit `fdd343c`'s `pass@2` came back 2/2 solved (~13 and ~21 min, all 23
tests) with an unambiguous root cause, unlike every prior round on this
PR: *"it recalled P_BTREEMETA=9, P_LBTREE=5, P_OVERFLOW=7 from
training-data familiarity"* -- not derivation, not a live search, direct
recall. **This is a genuinely new, generalizable finding worth adding to
[[dynamo_enumeration_defeats_evidence_inference]]:** the existing
fetch-resistance filter (no indexed tutorial, no canonical spec page,
lives in a prose-free internal header) turned out to be necessary but not
sufficient -- Berkeley DB's `db_page.h` is still a real, long-lived,
actively-mirrored open-source C header, and large models train on raw
source-code text from public repositories, not just prose/tutorials. A
fact can fail every live-search-fetchability test this project has used
and still be memorized cold if its source file is common enough in that
raw training corpus. This is DIFFERENT from the "derivability" failure
mode of rounds 1-4 (logically-forced consequences of a disclosed
contract) -- it's a distinct, third failure mode: real + external +
arbitrary + fetch-resistant-by-search + still memorized. Worth a
dedicated new memory entry, not just a note here, once this task reaches
an outcome.

Put a three-way decision to the user (accept as documented result and
stop / try real concurrency despite the risk / try a different real
convention less likely to be in training-corpus source) -- **chosen: try
real concurrency**, per the pass2 bot's own suggestion (`journal_get`'s
same-handle lifetime guarantee under concurrent access forces real
aliasing/lifetime reasoning, distinct from the prior derivability wall
since there is no clean, unique, "correct-by-construction" answer a
sequential trace would reveal).

**What got built:** `journal.h` now states a `journal *` may be shared
and used concurrently across threads, and `journal_get`'s returned
pointer stays valid until the next `journal_get` on the same handle from
the SAME OS THREAD specifically -- a concurrent call from a different
thread must not invalidate it. This exposed a REAL pre-existing bug in
every earlier round's reference: the scratch buffer backing
`journal_get`'s pointer was a single field on the mutex-guarded handle
state, shared across all threads -- exactly the classic `strerror()`
defect that `strerror_r()`/thread-local storage exist to fix in real C
APIs. Fixed by moving it to Rust `thread_local!` storage (the shared base
scope/scope stack stays behind the same single mutex as always -- only
the scratch buffer moved out from behind it, since a mutex cannot make a
pointer a thread already holds remain valid once another thread's call
frees/overwrites the memory it points to).

**Verification, and why it's deterministic despite genuine concurrency:**
a new, separate, dedicated C program (`tests/clients/concurrent_client.c`,
linked with `-lpthread`, NOT the line-scripted `client.c`) spawns two
real OS threads sharing one handle. Thread A calls `journal_set` then
`journal_get` on its own key and holds the returned pointer; thread B
calls `journal_set` then `journal_get` on a *different* key on the *same
handle*, with a pair of `pthread_barrier`s forcing thread B's call to be
guaranteed complete before thread A re-checks its pointer. Neither
thread's assertion depends on finer-grained interleaving than that, so
the test's pass/fail outcome never depends on scheduling luck even though
the underlying execution has genuine thread interleaving -- confirmed via
30 consecutive local runs against the reference (0 failures) and 20/20
against a shared-scratch-buffer mutant (every single run caught, not
flaky). All 9 mutants (the prior 8 plus this new one) re-confirmed
against the current 24-test suite -- the 6 pre-existing mutants needed
patching first since they predated `journal_save`/`journal_load` and
failed to *link* against the now-updated `client.c`, not a real
regression; patched by appending the (unchanged) save/load functions,
then re-verified each still fails only its own targeted test(s), plus
(correctly, as a true positive) the new concurrency test, since they all
still carry the old shared-scratch bug too. oracle=1.0/nop=0.0 confirmed
from a fresh clone before push.

**Next steps:** watch `gh pr checks 3` for commit `fdc33ef`. If `pass@2`
produces a genuine valid fail here, this task is finally through the wall
this whole PR has been stuck at across four-plus rounds on this design --
proceed to `qc_gate` and `pass@5` as normal. If it still solves 2/2, this
would be a THIRD distinct failure mode confirmed on one task (after
derivability and memorization) -- read the trial trace closely (did both
agents independently reach for `thread_local`/equivalent per-thread
storage as the obvious textbook fix for a well-known problem class, the
same way `strerror_r` is well-known?) before deciding whether to keep
iterating or treat this as the final, well-documented dead end for this
specific design.

-----------------------------------------------------------------------

-----------------------------------------------------------------------
SIXTH UPDATE (2026-08-30): journal_save/journal_load pushed -- a real,
external, arbitrary convention (Berkeley DB's internal page-type byte
table) grafted onto binary snapshot persistence, after two research
passes.
-----------------------------------------------------------------------
Per the user's explicit choice ("bolt on an unrelated real mechanism")
after the first research fork found nothing usable within nested-
transaction semantics itself, a second, more targeted fork found and
verified a genuine candidate: Berkeley DB's real internal on-disk
page-type byte enum (`db_page.h`: `P_INVALID=0, P_IBTREE=3, P_IRECNO=4,
P_LBTREE=5, P_LRECNO=6, P_OVERFLOW=7, P_HASHMETA=8, P_BTREEMETA=9,
P_QAMMETA=10, P_QAMDATA=11, P_LDUP=12, P_HASH=13, P_HEAPMETA=14,
P_HEAP=15, P_IHEAP=16`) -- real, arbitrary (historical accretion, not a
designed scheme: `P_HASH`=13 sits far from its own `P_HASHMETA`=8; newer
Heap types tacked on at 14-16), disprovably-wrong (no principled engineer
reconstructs this numbering), non-mainstream (no tutorial blog found,
unlike a same-shape LevelDB WAL-record-type candidate that WAS rejected
for exactly that reason -- six independent tutorials walk through
LevelDB's enum line by line), and fetch-resistant with a moderate,
honestly-flagged caveat (the header IS on GitHub and found in one
targeted search, but lives in an internal `dbinc/` implementation header
with zero explanatory prose, not a documented spec page -- unlike
SQLite's WAL checksum, which was rejected for sitting on SQLite's own
canonical, prose-explained reference page). Independently re-verified
against the primary source (`db_page.h` on GitHub, via two independent
lookups) before use, not trusted from the fork's report alone or from
memory -- confirmed exact: `P_BTREEMETA=9, P_LBTREE=5, P_OVERFLOW=7`.

**Design**: `journal_save(j, path)`/`journal_load(j, path)`, added to
`journal.h`/`journal.rs`, persist/restore the base scope (only) as a
binary snapshot file: 4-byte magic `"JRN1"`, then a header record
(tag=9, u32 LE count), then one entry record per key in ascending byte
order -- inline (tag=5, u8 key_len, key, u8 val_len, value) for values
&le;64 bytes, overflow (tag=7, u8 key_len, key, u32 LE val_len, value)
otherwise. The whole record layout is author-designed and fully
disclosed (field widths, the 64-byte threshold, a byte-exact worked
example generated by actually running the reference, not hand-derived);
only the three tag-byte VALUES are the real, undisclosed-in-full fact --
`journal.h` names "a real, widely-deployed embedded database engine"
as a locator (matching the one proven pattern in this project's history,
MDL/CTfile's "name the standard, restate none of its rules") without
naming Berkeley DB specifically or restating the header's contents;
`instruction.md` deliberately does not repeat that name either, deferring
entirely to `journal.h` as the fairness anchor. The worked example shown
in `instruction.md` demonstrates only the header (9) and inline (5) tags
(a snapshot with no value over the 64-byte threshold); the overflow tag
(7) is exercised only by held-out verifier tests with a longer value --
this is the deliberate design lesson from all four earlier rounds: a
fact shown once in a disclosed sample is trivially copyable, so genuine
difficulty requires at least one instance of the SAME real convention
that is never directly shown, forcing either recall or a real lookup.

**Verification**: four new tests read the produced snapshot file's raw
bytes directly (`Path.read_bytes()` in `test_outputs.py`, not just
round-tripping through the API) -- byte-exact match against the worked
example (pins tags 9 and 5), byte-exact match against an independently
computed expected sequence for a value requiring the overflow encoding
(pins the held-out tag 7), a full save-then-load round trip including an
overflow-sized value, and that `journal_load` rejects a hand-constructed
file using a plausible-but-wrong sequential tag (1) instead of the real
one. **Why byte-exact, not just round-trip:** confirmed by building an
eighth mutant using a self-consistent-but-wrong sequential 0/1/2 tag
scheme -- it passed the round-trip test cleanly (self-consistency alone
proves nothing) and was caught only by the two byte-exact tests, exactly
as intended. All 23 tests (19 existing + 4 new) pass against the
reference; oracle=1.0/nop=0.0 confirmed from a fresh clone before push.

**Candidates already researched and rejected this round** (don't
re-litigate): LMDB/RocksDB nested-transaction rules (logically forced,
the exact wall already hit four times); SQLite's WAL frame checksum
(real and arbitrary, but sits on `sqlite.org/walformat.html`, a top-
ranked canonical reference page -- trivially fetchable); SQLite's b-tree
page-type byte (same fetch-resistance failure, `sqlite.org/fileformat2.html`
states it verbatim); LevelDB's WAL record-type enum (real and arbitrary,
but at least six independent tutorial blog posts walk through the exact
constant names -- fails non-mainstream); Berkeley DB status/error codes
as a candidate for a *different* slot (rejected earlier for having no
organic fit with a bespoke `0`/`-1`-based API -- superseded by using
Berkeley DB's *page-type* table instead, which has a natural, honest fit
as a "record type tag" for a persistence format).

**Next steps:** watch `gh pr checks 3` for commit `fdd343c`. This is a
structurally different crux than every previous round on this design --
genuinely un-derivable in principle, not just under-tested -- so a 2/2
solve here would be a much more informative and concerning signal than
any of the four previous ones (it would mean either the model has this
specific obscure fact memorized, or found and correctly read the
`db_page.h` header via search in a way that didn't require any real
reasoning to apply). If `pass@2` produces a genuine valid fail here, this
task is finally through the wall this whole PR has been stuck at across
four designs -- proceed to `qc_gate` and `pass@5` as normal. If it still
solves 2/2, read the trial trace closely for HOW the agents got it right
(memorized cold vs. searched-and-found) before deciding whether this
whole approach (obscure compiled-library binary format constant grafted
onto an author-designed wire format) is itself now exhausted for this
model, which would be a new, generalizable finding distinct from anything
in [[dynamo_enumeration_defeats_evidence_inference]] so far.

-----------------------------------------------------------------------

-----------------------------------------------------------------------
FIFTH UPDATE (2026-08-30): the fourth consecutive 2/2 finally hit the
real wall -- idiom convergence confirms this is the settled derivability
pattern, not "shallow coverage." Decision made, research in progress.
-----------------------------------------------------------------------
`1335a3e` (the validate snapshot-semantics disclosure) also came back
pass@2 2/2-solved. The automated pass2-difficulty-suggestion's daily quota
(2/2) was exhausted, so no fresh advisory posted -- but the ALWAYS-posted
trial-results comment gave the real signal: both agents independently
converged on IDENTICAL structure (`Vec<Scope>` stack, `BTreeMap` keys,
snapshot-then-truncate for validate, same fold direction, same rollback
semantics), and the reviewer's own words were "these design decisions
were derived from the normative spec... rather than memorized solution
patterns" and "the spec was sufficient to derive the correct
implementation from first principles." This is functionally the same
wall as the "well-represented in training data" language that killed the
three earlier designs on this PR -- just named more precisely, and it
matches this project's settled rule exactly (see
[[dynamo_enumeration_defeats_evidence_inference]]): obscurity is not the
filter, DERIVABILITY is. The real diagnosis: the four "compositions"
added across rounds 2-4 were never four independent axes -- they're all
downstream of ONE design decision (`Vec<Scope>` + depth-watermark
truncation) that the fairly-disclosed contract itself all but hands an
agent, exactly the "strengthening a saturated family" anti-pattern
[[dynamo_saturated_crux_families]] and [[dynamo_axes_are_decisions_not_rules]]
warn against. PR #2's real precedent escaped this specific wall via a
genuine LOCK-HOLD-ACROSS-CALLBACK deadlock risk plus a subtle errno
restoration order bug where "every sequential trace looks correct" --
properties my four compositions never had, since every one of mine is a
correctness rule with no plausible-but-wrong natural implementation that
survives a normal-order test trace.

Presented this analysis and three options to the user (add one real
arbitrary convention / pause and research fresh / accept as documented
result and stop) -- **chosen: add one real arbitrary convention**, reusing
the built and proven Rust/C-ABI/cdylib infrastructure rather than a full
redesign. A research fork is in progress applying the FULL 5-filter test
from [[dynamo_enumeration_defeats_evidence_inference]] (derivability,
disprovably-wrong-not-just-different, non-mainstream, fetch-resistance
given `allow_internet=true` is a confirmed hard platform constraint here
too, verify-against-primary-source) to real embedded/systems
transaction-log engines with COMPILED reference implementations (RocksDB
WriteBatchWithIndex SavePoint, LMDB nested transactions, LevelDB, Berkeley
DB) or an adjacent real C-ABI/systems convention -- explicitly steered
away from every candidate already killed on this PR (WHATWG MIME-sniffing,
git-config booleans, dpkg version compare, PE/COFF, CRC catalogs, Unicode
case-folding, COBOL COMP-3, ZIP bit flags, AppleSingle/AppleDouble) and
away from anything a build image would ship pre-installed (e.g. glibc's
errno.h, which fails fetch-resistance outright since it's sitting in the
agent's own container).

**Next steps:** wait for the research fork's report (verified fact +
5-filter verdict + build recommendation), then implement it as an
addition to the existing `journal.h`/`journal.rs` design -- keep the
Dockerfile/Makefile/C-client-harness/mutant-battery/fresh-clone-calibration
workflow, which has been reliable across all five rounds so far. If the
fork finds nothing that clears the bar, that itself is a real result:
report back to the user that this specific design (however well-built)
may be structurally capped, and revisit the three-option decision.

**Research fork result: nothing found that clears the bar, within the
savepoint/nested-transaction niche.** Two real candidates checked against
the full 5-filter test, both rejected with verified evidence:
- **LMDB/RocksDB nested-transaction rules** (child-abort-doesn't-affect-
  parent, parent-abort-cascades, rollback-with-no-savepoint returns
  NotFound) -- verified against LMDB's official manual and RocksDB's real
  `write_batch_with_index.h` source. REJECTED: logically forced, the same
  standard nested-transaction semantics any competent engineer derives
  from "nesting" itself -- exactly the wall already hit four times.
- **SQLite's WAL-mode frame checksum** (a real, bespoke, non-CRC
  "Fibonacci weighted" algorithm plus a real arbitrary magic-number/
  byte-order quirk) -- verified against `sqlite.org/walformat.html` and
  `wal.c`. Passes derivability/disprovably-wrong/non-mainstream, but
  REJECTED on fetch-resistance: it lives on SQLite's own canonical,
  top-ranked reference page, stated verbatim -- with `allow_internet=true`
  a confirmed hard platform constraint on this task, one search retrieves
  the complete answer with zero transcription risk. A worse version of
  the JWST DQ-flags failure (a live official spec page beats even a tidy
  GitHub data file).
- Berkeley DB's status-code numbering was a dead end for a different
  reason: even if verified, grafting BDB's specific numbering onto a
  bespoke `journal.h` that already uses plain `0`/`-1` has no organic
  justification -- risks an `interesting_realistic`/contrived-convention
  rejection on its own terms, independent of the 5-filter test.

The fork's own assessment, worth recording as a candidate new finding:
**"nested transaction/savepoint semantics" may be a structurally hostile
niche for this defeat pattern**, the same way Chemistry/Materials and
Computational Geometry are recorded as hostile in
[[dynamo_enumeration_defeats_evidence_inference]] -- every real embedded
engine's savepoint nesting rules converge on the same SQL-standard-derived
shape (no room for a committee-arbitrary axis), and the one genuinely
arbitrary fact adjacent to it (SQLite's WAL checksum) happens to live on
the single most heavily-indexed page for exactly that fact. This is
NOT yet confirmed as a durable finding (n=1 fork's search, not
exhaustive) but is worth flagging in memory as a lead for future
Software-Engineering/systems tasks.

**Decision point reached again, sooner than hoped.** Two live options the
fork itself named: (a) abandon the savepoint-semantics constraint and bolt
an unrelated real-arbitrary-fact mechanism onto the existing Rust/C-ABI
infrastructure (e.g. a binary persistence format using a real, obscure,
compiled-library-only encoding) -- reuses the proven Dockerfile/Makefile/
harness but risks reading as contrived/bolted-on; (b) treat this as
confirmation the mechanism space is exhausted for this specific design and
put the three-way decision (try something unrelated / pause and research
more broadly / accept as a documented result and stop) back to the user.
Put to the user; awaiting their read.

-----------------------------------------------------------------------

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
