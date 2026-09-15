# Rework: dynamo-e979213-hopper-lot-mend, issue #7 (second rework round)

**Task:** Repair a torn HOPPER interchange landing area in place. Parse two big-endian binary
grammars, replay a write-ahead log, rebuild a parcel lineage, re-serialise crate containers, and
write two JSON deliverables. See `REWORK-dynamo-e979213-hopper-lot-mend.md` for the first rework
round (issue #3, case-fold on `origin`/`recasts` references).

**Issue #7 verdict:** rating Minor, one finding.

## The finding

### `sound_verifier` — Minor

**Claim:** All generated loose parcel filenames use lowercase SHA-256 ids; mixed casing is
applied only to references (the issue #3 fix). A materially case-sensitive implementation like
the Oracle can pass every differential corpus.

**Root cause:** CONTRACT.md §2.3 states a loose file's parcel id is read off its *filename*
(`<hopper>/parcels/<hex>.json`), and §3's case-insensitive-compare rule applies to every hex
digest, filenames included. Issue #3's fix folded `origin`/`recasts` *references to* a parcel id,
but never the id a loose file names *itself* after — a second, independent gap in the same
family of bug. Since the corpus never spelled a loose filename in anything but lower case, this
gap was invisible to every differential seed.

**Evidence:** `solution/hopmend.py` line 297 (pre-fix): `card[node[:-5]] = fold_ids(json.load(fp))`
— the roster key came straight from the filename, unfolded. `tests/reference.py` line 294 had the
identical pattern. Reproduced directly: on the unmodified oracle, renaming a handled loose
parcel's file to an upper-case spelling changed `restore-plan.json`'s computed `roots` (one
parcel dropped, a different one appeared) and leaked the upper-case spelling into the plan
itself, which CONTRACT.md requires stay lower case.

## The fix

### Fold the filename-derived id, not just references to it

- `solution/hopmend.py`: `pid = node[:-5].lower()` before the id becomes a roster key
  (`card[pid]`, `raw_total`).
- `tests/reference.py`: same fold, `pid = item.name[:-5].lower()`, kept an independent
  implementation from the oracle (per the standing rule for this task's differential design).

### Introduce a case-bearing loose-filename fixture

- `tests/gen_hopper.py`: the handled loose parcel `old_handled` is now written to disk with an
  upper-case filename (`tid.upper() + ".json"`) on every seed — deterministic (keyed to a fixed
  witness tag, not a per-seed hash), so both mutation-sweep probe seeds exercise it without
  relying on chance.
- `_self_check()` gained an assertion that the on-disk file is actually spelled upper case,
  guarding the coverage against future edits.

### Downstream fallout from making a loose filename legitimately non-lowercase

This is the part the finding's own citations didn't flag, but became load-bearing once a single
cased loose filename existed in the corpus:

- `tests/case_roster.py` opened three parcels directly by `p["id"] + ".json"` (always lower
  case) — broke with `FileNotFoundError` on the newly-cased file. Fixed by building one
  `{lower: actual}` spelling map per seed and reading through it, mirroring the pattern this file
  already used for frame filenames.
- `tests/gen_hopper.py`'s `_all_cards()` self-check helper keyed its dict by the raw (unfolded)
  filename stem — any self-check indexing `card_by_id[p["id"]]` for the cased witness would
  `KeyError`. Fixed by folding that dict's keys to lower case too.
- `tests/test_outputs.py`'s `surviving_ids()` — reads the *candidate's own output* directory —
  needed the same fold: nothing renames a loose file on repair (only frames get that treatment,
  per CONTRACT.md's explicit step-2 rule), so a live cased parcel keeps its spelling in the
  output tree, and the ids `surviving_ids()` returns must fold to compare against the (correctly
  folded, lower-case) ids the candidate's `restore-plan.json` reports.

**Lesson:** a `sound_verifier` fix that makes a previously-constant fixture property vary for the
first time (here: loose filename casing) needs a search across every place that property was
silently assumed constant, not just the two-or-three files the issue cited. Grep every direct
`os.listdir(...)`/filename-as-id use in the test suite once the fixture stops being uniform.

### Add a mutation to the sweep

- `loose-id-not-folded`: reverts `pid = item.name[:-5].lower()` → `pid = item.name[:-5]` in
  `tests/reference.py`. Measured caught on both probe seeds. Sweep count: 209 → 210.

### Mechanically required

- `environment/data/hopper/`: the shipped fixture's now-cased loose parcel file renamed
  (`git mv`) to match the generator's new output — confirmed via `diff -rq` against a freshly
  built corpus that this was the *only* delta.
- `tests/reference_pins.json`: regenerated for all 8 seeds. The fold is unconditional (the cased
  witness ships on every seed), so every pin changed, not just the touched seed.
- `README.md`, `task.toml`'s `verification_explanation`: mutation count and case-folding
  description updated to 210 and to mention the loose-filename axis. The `task.toml` fix went out
  as a **second, small push** after `deep_review`'s advisory note caught the 209→210 drift I'd
  missed on the first push (see Gate history below).

## Regenerating pinned digests correctly — a trap that cost one wasted iteration

`tests/test_outputs.py::tree_digest()` excludes the two deliverable files
(`mend-report.json`, `restore-plan.json`) from the tree-shape hash — they're compared parsed,
separately. My first hand-rolled digest-regeneration script omitted that `DELIVERABLES` exclusion
and produced wrong pins for every seed; `harbor run --agent oracle` failed at
`test_golden_outcomes_match_their_authoring_digests` even though the actual repair logic was
correct. **Fix:** copy the exact `tree_digest`/`parse_object`/`outcome_of`/`digest_outcome`
helper bodies from `test_outputs.py` verbatim into any offline pin-regeneration script — don't
reimplement from memory of what they probably do.

## Gate history

1. **Push 1** (`solution/`, `tests/*.py`, fixture rename, pins): `changes`, `cosine_similarity`,
   `review`, `similarity`, `ratelimit`, `validation`, `pass2` (2/2 solved — expected, a
   verifier-only fix on an already-accepted task) and `deep_review` all passed. `ava_review`
   **blocked**: `routing=block, confirmed_major=0, supported_major=0, potential_major=7, gaps=6,
   parse_failures=1`. The one listed item was labelled **Advisory (non-blocking)** for
   `verifier_coverage`, with garbled, non-specific text ("verifier imports its oracle module...
   the verifier would instead bypass earns reward=1") that named no concrete exploit.
   `deep_review`'s own trajectory analysis on the same push explicitly attempted a constructed
   bypass and found none ("no feasible leakage vector surfaced"), and its `trivial_bypasses_blocked`
   criterion PASSed. Per `rework-rule.md` §6.F this reads as an AVA-side parse/aggregation flake,
   not a real finding — `confirmed_major`/`supported_major` both zero, and the sole "finding" is
   advisory-only, self-contradicting the BLOCK verdict.
   `deep_review`'s PASS comment also carried a genuine, small advisory: `task.toml`'s
   `verification_explanation` still said "209 single-rule rewrites" against the new 210-entry
   sweep — missed on the first push despite my own README update catching the same drift.
2. **Push 2** (`task.toml` count fix only): forced a fresh AVA run on a new runner (no
   close/reopen needed — a real, small content change was available anyway). `ava_review` passed
   clean this time with identical case-fold logic, confirming the push-1 block was the flake
   §6.F predicts. Full pipeline then ran to completion: `tier1` (fix-addressal), `qc_exec`,
   `qc_eval`, `qc_gate`, and finally `trials` (pass@5) all passed. `pass2` re-ran too (2/2 solved
   again — the task.toml prose edit doesn't touch `solution/`/`instruction.md`, so this matches
   `platform-rework-docs.md`'s repeated finding that pass@ is not reliably skipped even for a
   narrow fix).

## Verification outcome

- **Oracle and nop:** 1.0 and 0.0 locally, matching the CI validation gate.
- **Direct exploit reproduction:** confirmed before/after — renaming a handled loose parcel's
  file to upper case broke the unfixed oracle's roster (`restore-plan.json` roots changed) and
  is fixed post-patch (canonical lower-case id, unchanged roots, upper-case spelling never
  leaks into the plan).
- **pass@2:** 2/2 solved (verifier-only fix on an already-accepted, previously-hardened task —
  expected, not a difficulty regression).
- **pass@5:** 3 good-valid-fail + 0 soft-timeout of 5 (avg@5 = 0.200) — comfortably clears the
  `>=3 total with >=1 good valid` bar, no borderline margin to worry about.
- **All 17 checks green**, PR labelled `accepted`.
- **No regression:** `coherent_contract`, `correct_reference_solution`, `protected_ground_truth`,
  `deterministic_execution`, `runnable_realistic_task` all still pass; issue #3's case-fold on
  `origin`/`recasts` untouched.

## Timeline

- 2026-08-01: Delivery PR #2 merged, task accepted.
- 2026-09-02/03: Issue #3 (case-insensitive parcel-id references) opened and closed via PR #6,
  merged 2026-09-10.
- 2026-09-13: Issue #7 opened (loose-filename case-fold gap, a second bug in the same family
  issue #3 didn't cover).
- 2026-09-15: Rework PR #8 opened against `main`. Push 1 blocked on an AVA flake (§6.F). Push 2
  (task.toml count fix, incidentally forcing a fresh AVA run) cleared every gate; PR labelled
  `accepted` with pass@5 = 3 good-valid-fail/5.

## Lessons

1. **A `sound_verifier` fix that makes a fixture property vary for the first time needs a
   grep across the whole test suite, not just the finding's cited lines.** Every direct
   `os.listdir`/filename-as-id assumption that held while the property was constant becomes a
   live bug the moment it stops being constant. Budget time for this search on any fix that
   introduces a new axis of variation into previously-uniform fixtures.
2. **Copy verifier helper functions verbatim when regenerating pins offline** — don't
   reimplement `tree_digest`/`outcome_of` from memory. A single omitted exclusion
   (`DELIVERABLES`) produced digests that were wrong in a way indistinguishable from a real bug
   until traced back to the helper itself.
3. **An AVA block with `confirmed_major=0, supported_major=0` and only an advisory-labelled,
   non-specific "finding" is a real, cheap flake signal** (`rework-rule.md` §6.F) — especially
   when the same push's `deep_review` explicitly attempted and failed to construct a bypass. A
   routine content push (even an unrelated one-line prose fix) is enough to get a fresh runner
   and confirm it; no `gh pr close`/`reopen` ceremony needed if a legitimate small fix is already
   pending.
4. **`task.toml`'s `verification_explanation` is a graded surface that drifts silently whenever
   the mutation-sweep count changes** — re-grep it (and `README.md`) for the old count in the
   same push that adds or removes a mutation, not after a reviewer catches it.
