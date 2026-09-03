# REWORK dynamo/vault-salvage — a rework PR *can* run the entire pipeline; and closing a verifier-coverage finding created two new gate blocks in a row

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 17 checks `SUCCESS`, `accepted` label, `pass@5 = 1/5 solved` (3 good valid fails, avg@5 = 0.200). Not merged at write time. |
| **Repo** | `dynamo-e843ed4-file-and-media-operations`, branch `fix-issue-3` (fork `Pruthviraj374/dynamo-e843ed4-file-and-media-operations`) |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-e843ed4-file-and-media-operations/pull/6, rework for issue [#3](https://github.com/handshake-project-dynamo/dynamo-e843ed4-file-and-media-operations/issues/3) |
| **Category / sub** | File and Media Operations / Recovery and repair (pre-seeded, unchanged) |
| **Benchmarked model** | `task.toml`: `model_tested = "Opus-4.8"`, `agent_tested = "Terminus-2"` (unchanged) |
| **Commits** | `459fcfd` (the three findings) → `e04c0ec` (empty re-trigger) → `727e723` (`qc_gate` B1) → `9054d13` (`qc_gate` E5) |
| **Files touched** | `task/solution/salvage.py`, `task/tests/test_outputs.py`, `task/environment/data/vault/FORMAT.md`, `task/task.toml`, `README.md`. **Never touched:** `instruction.md`, `tests/vaultgen.py`, `tests/expected/**`, the shipped vault's segments, either worked example. |

Four findings this file exists to record.

**One: the corpus's headline claim from the first REWORK file — "for a rework, only `tier1` + `gate`
run, everything else is skipped by design" — is not a property of reworks.** Every gate ran here:
`pass2`, `deep_review`, `ava_review`, `qc_eval`/`qc_exec`/`qc_gate`, `trials` (pass@5), `similarity`,
`cosine_similarity`, `validation`. Four full cycles of it, ~1h20m–3h each. The determinant is
visible in the `changes` job log: **`REPLAY_RUN_ID:` was empty** — the change gate had no donor run
from the *current* pipeline version to replay, so no surface could be skipped. See §3.

**Two: fixing a `sound_verifier` coverage gap can hand you a `coherent_contract`-shaped block one
gate later.** The issue asked for coverage of malformed six-column index candidates. Adding it made
the verifier grade a behaviour `FORMAT.md` had not pinned, and `qc_gate` B1 ("Ambiguous Rule, No
Disambiguation") blocked on exactly that. Cost one full cycle. **When a rework finding says "the
verifier does not cover X", check in the same push whether the agent-visible contract *states* X.**
See §4.

**Three: a `qc_gate` item under "🟡 Needs human review (not auto-passed)" is a required fix.** E5
(Symlinked Output Path) was not in the "🔴 Must fix" list, and I answered it with a reasoned PR
comment. The next round's `tier1` counted it `❌ … No change to /app/salvage.py or any verifier;
diff only touches FORMAT.md` and **held Tier 2 without running it**. Cost another full cycle. This
is the third independent confirmation in the corpus (`replay-rollout-gae` §5 step 7 saw the same
thing) — treat yellow as red. See §5.

**Four: the coverage the reviewer asked for became the task's most effective difficulty axis.** The
stale-output-tree check gated **3 of 5** pass@5 trials. A finding phrased as verifier hygiene was
worth more difficulty than anything in the original design's trap list. See §7.

---

## 1. What the task asks (unchanged by this rework)

`dynamo/vault-salvage` ships a damaged content-addressed backup vault (VSEG: binary segment files of
length-prefixed records, per-segment index, three payload codecs, row/column/diagonal parity, an
append-only journal, nested VNST containers, a prefix-scoped policy table) and asks for
`python3 /app/salvage.py <vault> <out> [<snapshot>]` producing `<out>/tree` and `<out>/report.json`.
`FORMAT.md` is normative for layout, parity algebra and journal ordering; the codec grammars, policy
resolution, EOL handling and container-expansion gate are pinned only by two worked examples that
ship their report and no tree. Already delivered and merged (PR #2, 2026-07-21) before this rework.

## 2. The three findings and what each fix actually was

Issue #3, verdict `revise`. The adjudication had already **struck one reviewer claim** (a
`runnable_realistic_task` penalty over snapshot-name collisions — impossible, the prefixes are
disjoint `release-*`/`stage-*`) and **added one the review missed** (malformed six-column index
handling). Read the adjudication paragraph, not just the checklist: it giveth and taketh away.

- **`deterministic_execution` (Major).** The three held-out cohorts drew seeds from
  `random.SystemRandom()`. A seed decides content, grid shape, segment count, damage placement, the
  codec-1 escape byte and snapshot names — i.e. it decides the truth the submission is graded
  against. Fix: `HELD_OUT_SEEDS` / `NAMED_SNAPSHOT_SEED` pinned in `tests/` (overlaid at verify time,
  never in the agent image). **The non-obvious half of this fix:** pinning can silently turn the
  held-out cohort into the shipped answer, which would destroy the anti-memorisation property the
  cohort exists for. Each held-out check now asserts `want["report"]["files"] != EXPECTED_REPORT["files"]`
  before running the tool. Verified determinism by building each seed twice **in separate processes
  under `PYTHONHASHSEED=random`** and comparing a SHA-256 over the vault bytes and over the derived
  truth — same process twice proves nothing, since set-iteration order is what would bite.
- **`correct_reference_solution` (Minor).** Two Oracle defects: `os.makedirs(out_root, exist_ok=True)`
  never cleared an existing `<out>/tree`, and `load_index()` ran `int(parts[1..5])` *outside* the
  `try` whose `except` already named `ValueError`. Fix: remove whatever stands at `<out>/tree` (tree,
  stray file, or link) then recreate it; move the column conversion inside the existing guard. The
  second fix is a two-line move, not new code — the guard was already correct, the statements were
  just in the wrong block.
- **`sound_verifier` (Minor).** Reusable CLI checks all started from a fresh output directory, and
  malformed-index coverage exercised only a failing checksum and a wrong column count. Fix: a new
  reused-directory check, a new six-column-bad-int check, and stale content seeded into the held-out
  named-snapshot run's output directory.

**Proof, not assertion, in both directions.** Before: the pre-fix Oracle left
`obsolete/deep/junk.bin` in the tree and exited non-zero when a plain file sat where a directory was
needed, and died with `ValueError: invalid literal for int()` on a spliced bad-int candidate. After:
the pre-fix Oracle run against the *new* verifier fails exactly 3 tests, the fixed one passes 40
(41 after the E5 test). That before/after pair is what the PR body was built on.

## 3. Why the whole pipeline ran, and how to tell in advance

`REWORK-3b8618f-release-plan` §5 recorded that a rework skips the agent-trial gates. That was true
*there* and false *here*, and the reason is legible in the `changes` job log before anything else
starts:

```bash
gh api repos/$R/actions/jobs/<changes-job-id>/logs | grep -v '36;1m' | grep -i 'REPLAY_RUN_ID'
#   REPLAY_RUN_ID:            ← empty ⇒ no donor, every surface re-runs
```

The change gate replays an earlier fully-green run *of the current pipeline version* per surface.
This task's only green baseline was the delivery-era PR #2 (2026-07-21) plus the closed rework PR #4
(2026-08-13/15), and neither qualified, so every surface flag came back false. Same shape as the
`fb5b374` note already in `platform-rework-docs.md`. **Plan the time budget off that log line, not
off the word "rework":** a fix touching only `tests/` still bought four ~2h cycles here.

## 4. `qc_gate` B1 — the fix that made the contract ambiguous

`FORMAT.md` §2 enumerated the disqualifiers for a kind-`2` candidate: payload CRC does not check
out, codec cannot be decoded, decoded payload "is not a six-column table". A record whose six
columns carry `not-an-int` **is** a six-column table under a literal reading, so adopting it and
skipping it were both defensible — and my new test graded one of them. B1 is precisely that.

Fix (documentation only): the enumeration now names the case — a line without six tab-separated
fields, *or one whose `<row>`, `<column>`, `<codec>`, `<payload-length>` or `<payload-crc32>` field
is not a decimal integer*, disqualifies the record and the search continues past it.

Two notes for next time:
- QC's boilerplate `Fix:` line said "Disambiguate the rule in **instruction.md**". The rule lived in
  `FORMAT.md`, which `instruction.md` designates as normative; fixing it there passed. Fix the rule
  where it lives and say so in a PR comment rather than duplicating spec text into `instruction.md`.
- Disclosing it cost no difficulty: the very next pass@2 still returned 0/2 with 2 valid fails, and
  the trial that had failed on this edge before was replaced by one failing on the journal
  seq-ordering crux. A rule that only ever produced a crash was never carrying difficulty.

## 5. `qc_gate` E5 — a yellow item that gates

E5 read: *"reads ['/app/out', '/app/salvage.py', '/app/vault'] with no symlink guard; exemption
pattern(s) present — LLM must confirm the symlink cannot reach truth"*, filed under **needs human
review**, not under must-fix. I confirmed it in a PR comment. `tier1` then reported
`❌ E5 … No change to /app/salvage.py or any verifier` and **held Tier 2 without running it** — the
whole QC suite deferred, one wasted cycle.

The vector is real, which is why arguing it was the wrong move: `/tests` is overlaid *after* the
agent phase, so a link left at `/app/out/tree` or `/app/out/report.json` resolves into the frozen
truth at verify time and the verifier reads the answer through it. Note `os.walk` does not protect
you — `followlinks=False` only stops it descending into symlinked *sub*directories; a symlinked
**root** is walked, and a symlinked regular file is `open()`ed straight through.

Fix, all verifier-side: `walk_tree()` refuses a symlinked root and surfaces a symlinked file or
directory inside the tree as a named path carrying a placeholder (`b"<symlink>"`) instead of
following it, so the existing exact path-set/byte comparisons reject it *and name it in the diff*;
`load_json()` and `run_cli()` assert the same for `report.json` and the tool; and one explicit
`test_graded_paths_are_not_symlinks` pins the whole set QC listed. Proved by building a temp tree
with a symlinked file, a symlinked directory and a symlinked root and checking each outcome.

## 6. Gate-by-gate log

| Run | Head | Result |
|---|---|---|
| `33656675549` | `459fcfd` | `changes` ✅ → **`cosine_similarity` cancelled after 41 min** in the fingerprint-extraction step ("The task fingerprint could not be extracted"), every downstream job cancelled, `gate` ❌, `needs-revision`. Platform fault, nothing to fix |
| `33661173526` | `e04c0ec` (empty commit) | static ✅ · rubric ✅ · duplicate ✅ · validation ✅ · **pass@2 0/2, 2 valid fails, 0 in-progress-timeout** · `deep_review` ✅ · `ava_review` ✅ · `tier1` ✅ (all 3 findings) · **`qc_gate` ⛔ B1**, early-exit deferring 21 checks |
| `33671509162` | `727e723` (B1) | same gates green again, pass@2 0/2 (2 valid fails) · `deep_review` ✅ · `ava_review` ✅ · **`tier1` ⏸️ HOLD on E5**, `qc_*` skipped entirely |
| `33679444483` | `9054d13` (E5) | everything ✅ · pass@2 0/2 (1 valid fail + 1 in-progress-timeout, "Rerun Recommended: NO") · `deep_review` ✅ · `ava_review` ✅ · `tier1` ✅ · **`qc_gate` ✅ 37 checks + probes clean** · **`trials` pass@5 1/5, "Difficulty OK"** · `accepted` |

Local calibration before every push: `harbor run -p . --agent oracle` = 1.0 (40 tests, 41 after E5)
and `--agent nop` = 0.0. Oracle run four consecutive times on the first push with identical verdicts.

## 7. What the added coverage did to difficulty (pass@5, run 4)

`1 solved · 3 good-valid-fail · 1 in-progress-timeout · avg@5 = 0.200`. The analyzer's own
stratification:

- **3 of 5 trials died on the stale-output-tree check** — all wrote additively with
  `os.makedirs(..., exist_ok=True)`, hit `FileExistsError` on the plain file planted where a
  directory was needed, and left a stale file behind. `task_specification: PASS` on every one of
  them: the graders read `instruction.md`'s "Nothing else may appear there" as adequate disclosure.
- 2 of 5 carried a silent EOL-on-`.bin` bug **invisible on the shipped vault** (its `tone.bin` holds
  no `0x0A`) and exposed only on held-out vaults — the held-out cohort earning its keep.
- 1 wedged its own terminal on a heredoc, 1 timed out mid-fix at exactly 3600 s.

So a verifier-hygiene finding produced the single most effective axis in the task. Worth remembering
when a rework issue looks like busywork: **"the verifier does not check X" often means "nobody has
ever measured whether agents get X right".**

## 8. Dead ends and roads not taken

- **Adding the bad-int record to the shipped vault.** The obvious way to cover the malformed-index
  case is to make `vaultgen` emit one. It changes `records_read` for that segment, so it moves
  `tests/expected/report.json`, the shipped segment bytes, and both worked examples — an
  agent-visible fixture change on a task whose two prior rework attempts died on pass@2. Instead the
  test **copies the shipped vault into a tempdir and splices the record in at verify time**
  (`raw[:16] + record + raw[16:]`, header CRC covers bytes 0..12 only and the declared record count
  is documented as advisory, so nothing else has to move), then asserts the full frozen report back
  with that one segment's `records_read` bumped by one. Zero fixture churn, full coverage.
- **Acting on the advisory notes.** `deep_review` asked three times to lower `run_cli`'s
  `timeout=900` below `[verifier].timeout_sec = 600`. Real and pre-existing — and a one-token change
  that would have cost another ~2h cycle including pass@2 and pass@5. Advisories never block; on a
  rework, leaving a pre-existing cosmetic advisory alone is the right call. Say so rather than
  silently ignoring it.
- **Touching difficulty at all.** The closed PR #4 on this same issue fixed the three findings and
  then spent six rounds tuning difficulty (raising `[agent].timeout_sec`, disclosing codec grammars,
  withholding `recovered_chunks` from both examples). It reached `accepted` and was closed unmerged
  anyway. Its rounds are worth reading for *mechanism*; the scope lesson is that none of it was
  asked for. This rework changed no difficulty knob and cleared the same gates.

## 9. Reusable checklist for the next rework

1. `gh issue view <n> --json body` — read the **adjudication paragraph**, not just the checklist. It
   can strike a finding (do not fix it) and add one the review missed (do fix it).
2. Reproduce every finding against the shipped artefacts before editing, and keep the reproduction
   script — it becomes the PR body's before/after table and the new test's justification.
3. Ask of each verifier-coverage finding: *does the agent-visible contract state the behaviour I am
   about to grade?* If not, disclose it in the **same** push (§4).
4. Fix every `qc_gate` item, including the 🟡 "needs human review" ones, in code (§5).
5. Cover a new case at verify time by splicing into a **copy** of the shipped fixture rather than
   regenerating it (§8) — no frozen expectation moves, no agent-visible change, no difficulty drift.
6. When pinning a seed that was previously random, assert the pinned vault still diverges from the
   shipped answer (§2).
7. Check `REPLAY_RUN_ID` in the `changes` job log to know whether you are buying a 10-minute
   re-check or four hours of agent trials (§3).
8. A transient stage failure (`cosine_similarity` fingerprint timeout here) is cleared by
   `git commit --allow-empty` and a push — second confirmation of `REWORK-3b8618f-release-plan` §6.
9. `.gitattributes` here marks `task/environment/data/**` and `task/tests/expected/**` as `binary`,
   so `git diff` shows `Bin` for a prose edit to `FORMAT.md`. Diff it with Python before trusting
   that the edit is clean.

## 10. One-paragraph version for future me

Three findings (unseeded held-out cohorts, an Oracle that never cleared its output tree and crashed
on a malformed index candidate, and the verifier coverage that would have caught both), fixed in one
scoped push touching five files and no fixture. The whole pipeline re-ran because the change gate
found no donor from the current pipeline version — so budget for pass@5, not for a fast path. Then
two more cycles, both self-inflicted and both avoidable: closing the coverage gap made the verifier
grade a rule `FORMAT.md` left ambiguous (`qc_gate` B1), and a QC item filed under "needs human
review" turned out to be a `tier1`-required fix that a PR comment does not satisfy (E5). Accepted on
the fourth cycle at pass@5 1/5, avg@5 0.200 — with three of the five trials failing on the very
check the `sound_verifier` finding asked for.
