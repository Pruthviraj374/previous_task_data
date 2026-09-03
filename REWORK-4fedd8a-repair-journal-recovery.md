# REWORK dynamo/repair-journal-recovery — the two named findings cost one push; the gates then found three more verifier defects, and a local mutation sweep was the only cheap way to stay ahead of them

- **Outcome** — **ACCEPTED** (automated), `accepted` label, 16 checks pass / 1 `skipping` / 0 fail. Not merged at write time.
- **Repo** — `dynamo-4fedd8a-debugging-and-repair`, branch `fix/concurrency-safe-oracle-and-verifier` (fork `Pruthviraj374/...`)
- **PR** — upstream [#3](https://github.com/handshake-project-dynamo/dynamo-4fedd8a-debugging-and-repair/pull/3), rework for issue [#2](https://github.com/handshake-project-dynamo/dynamo-4fedd8a-debugging-and-repair/issues/2) (`correct_reference_solution`, `sound_verifier`, both Major, verdict `uphold`)
- **Category / sub** — Debugging and Repair / Test Failure Repair (unchanged)
- **Commits** — `c4eda58`, `9273ff0`, `75904f8`, `36b8b04`, `2518a8a` (5 pushes, one of them a history-restructuring force-push)
- **Final calibration** — oracle 1.0, nop 0.0, 64 tests; pass@2 0/2 on four consecutive cycles; **pass@5 0/5 solved, 5 good-valid-fail, avg@5 = 0.000** (best band)

Five things this file exists to record.

**One: the two findings on the issue took one push. The remaining four pushes were all defects
the gates found in the verifier I had just written.** Budget a rework by the gate cycles after
the fix, not by the fix.

**Two: `qc_gate` "Narrow / Hardcodable Held-Out Coverage" hands you exactly one mutation per
cycle.** It blocked twice, each time naming a different surviving mutation in a different file.
A local mutation sweep run between cycles found two more before QC could, and each cycle it
saved was a full pipeline including pass@2 and pass@5.

**Three: `ava_review` found a `sys.path` shadowing false-accept that no mutation sweep would
ever find**, because it is a packaging fault, not a logic one. Verifier-owned files installed
into `/tmp` let an agent shadow the graded artifact.

**Four: a gate advisory can simply be wrong.** `deep_review` twice claimed a SPEC clause was
uncovered. Running the mutation it proposed showed the coverage was already there. Verify an
advisory by mutation before spending a cycle on it.

**Five: a rework PR is not automatically fast-pathed, and the deciding factor is *what you
touch*.** `REWORK-3b8618f` saw everything but `tier1`+`gate` skip; `REWORK-e843ed4` saw the
whole pipeline run four times. Both are consistent with `platform-rework-docs.md`: a fix that
touches `solution/` or `instruction.md` changes difficulty and triggers the full pass@ re-run;
a verifier-only fix does not. Mine touched `solution/`, so all 16 checks ran every push.

---

## 1. The task and the two findings

An event-sourced bitemporal order store whose durability layer is broken; the agent repairs it
so a reopened store agrees with the writer. A journal directory may be shared by several open
stores.

**`correct_reference_solution`** — the Oracle appended each group as separate unlocked record
appends, so overlapping writers could interleave groups and violate the contract's contiguous
shared stream.

**`sound_verifier`** — shared-writer operations ran serially, so an unlocked implementation
passed; and candidate-written records were checked only for type order, headers and counts, so
a writer and its own decoder could agree on invalid checksums.

## 2. The finding was wider than its own citation

The issue cited `journal.py L44–51` (`append_group`) and `L127–132` (`_append_line`). Locking
only those makes each group contiguous but leaves the real hole: `ingest_batch` read the journal,
decided acceptance, then appended, all outside any critical section. Two writers could each read
a stale stream and **both accept the same identifier**. The lock has to span read-decide-append,
which means it lives in `store.py`, a file the finding never named.

`tier1` credited exactly that framing: *"store.py wraps read-decide-append in `ingest_batch`
inside that critical section"*. Read a finding as a symptom and grep for the shared path, the
same as any bug fix.

## 3. The lock could not be a lock file — and PR #1's own review said so

The obvious design (a `journal.lock` in the journal directory) fails: several tests assert the
directory's exact contents, and `SPEC.md` says the journal holds its durable stream *and nothing
else*. This was already written down in the **original PR #1's** automated-review advisory,
which noted a pass@2 trial had failed precisely this way.

The fix is `fcntl.flock` on the **journal directory's own file description** — `os.open(dir,
O_RDONLY)` then `LOCK_EX`, released by closing the fd. It serialises cross-process writers and
creates no file. Reading the *original* PR's gate transcripts before designing paid for itself
here.

## 4. Reproduce every finding before fixing it

Both findings were reproduced as deliberately broken Oracle variants, scored against the
verifier as it stood and again after the fix:

- lock removed from the store — **1.0 before, 0.0 after**, failing only the two new overlap
  tests, identical across 3 runs
- writer emitting checksums its own decoder tolerates — **1.0 before, 0.0 after**

Both scoring a *full pass* against the old verifier is the evidence that the finding was real
rather than a reviewer's inference. Posting that before/after on the PR also closed the
`deep_review` residual note asking for a live repeatability run.

## 5. Making a concurrency test deterministic

Two overlapping-writer tests, both asserting race-*invariant* quantities so the gate's
`deterministic_execution` criterion survives:

- 2 processes × 12 distinct ids → the total stream is `["BEGIN","EVENT","COMMIT"] * 24` under
  every interleaving
- 2 processes racing the same 12 ids → whichever store reaches an id first newly accepts it and
  the other's call is an idempotent replay appending nothing, so exactly 12 groups exist
  regardless of who wins any race

Genuine overlap needed a rendezvous: a `barrier` op in `runner.py` (peers register in a
`/tmp/dynamo-barrier/<name>` dir and spin until N arrive) plus `run_concurrently` in the suite
launching real separate unprivileged processes. **Feed every peer's stdin before waiting on any
of them**, or the barrier deadlocks against `communicate()`.

This also closed a standing AVA advisory from PR #1 — that all named stores lived in one
process's dict, so cross-store visibility could come from shared memory rather than a disk
re-read.

## 6. The three defects the gates found afterwards

**`qc_gate` #1 — leading-zero segment names (`75904f8`).** Deleting the no-leading-zero guard in
`_segment_number` changed behaviour and nothing noticed. *This exact gap had been an advisory on
the original PR #1 and was never closed.* Design note: the naive fixture (`segment-01.log` beside
`segment-1.log`) makes both map to key 1 under the mutation, so detection depends on `iterdir()`
order — a coin flip. Give the malformed files a number **no real segment claims** and the
mutation deterministically adds a segment to the stream.

**`qc_gate` #2 — returned projections shared with the cache (`36b8b04`).** `ProjectionCache.get`
returning its stored object instead of a copy survived. The *public* independence test mutates
the **freshly computed** answer, which `put` has already deep-copied, so it cannot see this.
Catching it needs a **second identical `project()`** — the cache hit — and mutation of *that*.

**`ava_review` BLOCK — `/tmp` shadowing the artifact (`2518a8a`).** The runner and the
verifier's copy of the public suite were installed into `/tmp`, which the agent can write. A
script's own directory leads `sys.path`, and pytest's prepend import mode adds the test file's
directory; both were `/tmp`. An agent leaving a working `order_projection` package there gets it
imported ahead of `/app` and scores reward without repairing anything. Fixed by installing both
into a root-owned `/opt/dynamo-verifier` (0755) and running every unprivileged subprocess from
there. A guard test plants such a package and requires the real store's answer; reverting **only**
the path config makes that test fail while the other 63 pass.

## 7. The mutation sweep — the single highest-value habit here

After the second `qc_gate` block it was clear QC would keep releasing one mutation per cycle. A
throwaway script (`cp` the task, apply one string replacement, `harbor run --agent oracle`,
reward 1.0 = uncovered) covering **16 mutations, each tied to a stated contract clause**, found
two more holes immediately:

- **`effective_at` exactly equal to `as_of`** — tested at 1, 2, 3 and 99 but never *at* the
  cutoff, so narrowing `<=` to `<` survived
- **a torn line followed by an intact later segment** — every torn-line test tore the **last**
  segment, where stopping at the tear and running out of segments are indistinguishable

Both are the same trap: a rule that *looks* covered because tests exist near it, but whose
deciding case is never exercised. **When a coverage gate blocks twice, stop fixing the named
case and sweep.** ~25s per mutation locally against 40+ minutes per pipeline cycle.

Caveat learned the hard way: the first sweep ran while the task was transiently broken (my own
new test was failing), so every mutation reported "caught" trivially. **Confirm oracle = 1.0
before trusting a sweep.**

## 8. Bugs I introduced myself

**The runner recorded live objects, not snapshots.** My first cache-independence test failed on
the *correct* oracle. `runner.py` appended the same dict into `results` that it handed back as
the projection, and `results` is JSON-dumped only at the end — so mutating the live projection
retroactively rewrote an answer already recorded. Fixed by `deepcopy` at append time. A test
harness that replays operations and serialises at the end must snapshot anything the operations
can mutate.

**Two monitors sharing one state file.** Duplicate notification bursts I first wrote off as
redelivery were two polling monitors racing on the same dedup file, each re-emitting what the
other had consumed. One watcher per state file.

## 9. Gate-by-gate

Every push ran the full pipeline (16 checks). Push-by-push: initial push green through
`deep_review`/`ava_review`/`tier1`/`qc_exec`, blocked at `qc_gate`; second blocked at `qc_gate`
again on a different mutation; third blocked at `ava_review` (with `qc_*`, `tier1`, `trials` all
`skipping`, since they gate behind AVA); fourth green throughout.

- `pass2` returned **0/2 with 2/2 valid failures, "Rerun Recommended: NO"** on all four cycles
- `deep_review` reported the trials as **42/44 near-misses whose single missing primitive is
  `fcntl.flock`** — i.e. the fix to finding 1 *created* the intended crux; before it there was
  nothing for a trial to miss
- `qc_gate` `skipping` is not "passed": it means an earlier gate blocked
- rubric review scored **31/31** with `deterministic_reproducible` explicitly crediting
  "concurrency serialized by flock with barriers, asserted order-independently"

## 10. Advisories are not findings

`deep_review` twice advised that `SPEC.md:25` ("a correction in a batch may name an event earlier
in that batch") had no test, and that a solution resolving `supersedes` only against committed
events would pass. Applying that exact mutation (`staged_events.get` → `self.events.get`) scored
**0.0**, caught by `test_replaying_an_accepted_batch_after_recovery_appends_nothing`, which
ingests `ingest_batch(p, q)` with `q` superseding `p`. The clause was covered; the test just is
not named for it. I posted the mutation evidence on the PR instead of adding a redundant test,
saving a cycle.

Also left alone: an advisory about unused imports in the **shipped agent-editable package**.
Changing those alters the task's starting state, not the verifier — out of scope for a rework.

## 11. Confirmed live, and one correction to the corpus

- The `instruction.md` "You have N seconds…" line is **not enforced** — second independent
  confirmation, on a different repo. Better: the rubric's `instruction_concision` note for this
  PR reads *"no TB3 time-budget string"*, so the grader treats its presence as a defect to check
  for. Recorded in `rework/platform-rework-docs.md`.
- `REWORK-3b8618f`'s headline ("only `tier1` + `gate` ran") should be read as *for a
  verifier-only fix*, not as a property of reworks. See finding Five above.

## 12. Checklist for the next rework

1. Read the **original** PR's gate transcripts before designing — PR #1 held both the lock-file
   trap and two of the coverage gaps that later blocked me.
2. Grep every caller of the function a finding names; the fix usually belongs one level up.
3. Reproduce each finding as a broken-Oracle control and record 1.0-before / 0.0-after.
4. After any verifier change, run a local mutation sweep before pushing. Confirm oracle = 1.0
   first, or every result is a false "caught".
5. Treat a coverage gate's block as a *class* of gap, not the one case it names.
6. Verify an advisory by mutation before acting; two of the three I received were already
   covered or out of scope.
7. `readme-rule.md` applies — the root `README.md` must move in the same commit, and pushing it
   late costs a whole rate-limited cycle.
8. Commit format `Fix <criterion> finding from #<n>: <desc>`, PR body `Fixes #<n>`, no AI
   attribution anywhere.
9. Do not edit the machine-posted issue body to tick its boxes; it carries `task_hash`/`upload`
   metadata. Comment instead and let the merge close it.

## 13. One-paragraph version

Two upheld Major findings on an accepted event-sourcing repair task: the Oracle's journal appends
were unlocked, and the verifier ran its shared-writer scenarios serially while checking written
records only structurally. The fix was an exclusive `flock` on the journal **directory's fd**
(never a lock file — the directory's contents are asserted byte-exactly) spanning
read-decide-append in `store.py`, plus real overlapping unprivileged processes behind a
rendezvous barrier and per-record CRC-32 recomputed with `zlib`. Both findings were reproduced
as broken-Oracle controls scoring 1.0 against the old verifier and 0.0 against the new. That was
push one of five; the other four were defects the gates found in the verifier I had just written
— two `qc_gate` coverage mutations and an `ava_review` false-accept where verifier files in
agent-writable `/tmp` let a planted package shadow the graded artifact via `sys.path`. A local
16-mutation sweep, run between cycles, caught two further holes before QC could and is the
habit worth keeping. Accepted at pass@5 0/5, avg@5 0.000, with the trials failing at 42/44 on
the very `flock` the first finding was about.
