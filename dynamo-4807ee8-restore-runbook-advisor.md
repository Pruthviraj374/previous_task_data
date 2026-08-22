# dynamo/restore-runbook-advisor — QC blocked the same axis three times, and data answered it where prose could not

| | |
|---|---|
| **Outcome** | **ACCEPTED** — 16 checks pass, 0 fail, `accepted` label |
| **Repo** | `dynamo-4807ee8-data-querying-and-databases`, branch `submission-2` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-4807ee8-data-querying-and-databases/pull/7 (supersedes #5 and #6, both closed by me during a platform fault) |
| **Category / sub** | Data Querying and Databases / Database administration (pre-seeded) |
| **Benchmarked model** | `task.toml`: `model_tested = "Opus-4.8"`, `agent_tested = "Terminus-2"`; trials logged `Model A` on Daytona |
| **Final commit** | `9a59ac5` (5 substantive commits + 2 empty, across 3 PRs) |
| **Headline** | **pass@5 = 1/5 solved, 4 good valid fails, avg@5 = 0.200.** All four failures on **one** axis, and it is the axis I nearly cut |

Three findings this file exists to record.

**One: `qc_gate` B5 on a latent-crux task can be answered with *data* instead of prose.**
It blocked three times on the copy-only convention family. The corpus's standard answer — the
flat "standard practice governs" sentence — was already present and did not clear it. What
cleared it was putting a shipped objective *on* the rival reading, so the sample refutes it on
the agent's own self-check. That cost no concealment and **strengthened** the remaining trap,
because the precedent it teaches is the wrong generalisation for the axes still withheld.

**Two: the pass@k harness moved out of GitHub, and the failure modes are new.**
Grading now runs on Handshake's own runners and reports back as a commit status (`harbor /
pass@k`). GitHub only waits 60 minutes. Five distinct infra signatures cost roughly two days.
None of them was a verdict on the task. §8 has the full table — read it before diagnosing
anything.

**Three: my ranking of my own axes was inverted again — fifth confirmation.**
The axis I nearly cut as a redundant restatement caused **4 of 4** failures. The axis I
believed was primary gated nothing.

---

## 1. What the task asks

ORPHIC is a retired in-house tool that turned a SQL Server backup-catalog export into a restore
runbook: per registered recovery objective, which backup sets to restore, in order, to land as
close as possible to a requested instant without overshooting.

- **Agent sees:** `instruction.md`, `/app/catalog/sample_catalog.json` (one database's `msdb`-shaped
  backup history plus its objectives), `/app/catalog/CATALOG.md` (field list), and
  `/app/catalog/sample_report.json` (ORPHIC's runbook for that catalog — the self-check).
- **Agent produces:** `/app/advise.py`, invoked `python3 /app/advise.py <catalog.json> <report.json>`.
- **Graded on:** the shipped catalog plus **eight held-out catalogs**, 49 objectives, `tests/`
  overlaid at verify time, all-or-nothing across 14 tests.
- **Output per objective:** `objective_id`, `stop_at` (`YYYY-MM-DDTHH:MM:SSZ`), `plan` (ordered
  `backup_set_id` list).
- **Exact equality everywhere** — ordered integer lists and an instant to the second. No tolerance
  exists, so no `difficulty_evidence` "threshold artifact" argument is available to anyone.

---

## 2. The crux, and the invariants that keep it alive

Two real, published, **conditional** Microsoft-documented conventions, neither stated:

| Axis | Convention | Inert in the shipped catalog because |
|---|---|---|
| **A** | A full taken with `COPY_ONLY` cannot serve as a differential base and does not affect the differential base ([Copy-Only Backups](https://learn.microsoft.com/en-us/sql/relational-databases/backup-restore/copy-only-backups-sql-server)) | no shipped copy-only full stands between a full and a differential that any objective selects |
| **B** | `COPY_ONLY` **has no effect when specified with `DIFFERENTIAL`** (same page, T-SQL note), so a differential carrying the flag is an ordinary differential | each shipped copy-only differential is superseded by a later ordinary one before any objective reaches it |

**B did all the work.** Four of five trials wrote a single filter expression excluding copy-only
differentials, in four textually different forms, and each failed the same five held-out
catalogs.

A third convention — a log backup carrying bulk-logged changes is applied whole or not at all —
started withheld and is now **stated** (see §3.1). A fourth reading, *copy-only fulls are not
valid restore bases*, is now **taught by the sample** (§3.2).

**Invariants, machine-enforced in `tools/generate.py` — it writes nothing if one breaks:**

1. shipped catalog **bit-identical** under both crux misreadings;
2. each crux misreading broken by **≥3 held-out catalogs** (actual: 5 each);
3. every reading of *disclosed* machinery breaks the shipped catalog **and ≥1 held-out catalog**
   — the held-out half was added only after `qc_gate` C3, and it was the missing half;
4. every comparison in the reference has a fixture **exactly on its boundary**;
5. three rival readings left unstated are **moot on all nine catalogs**;
6. two independently decomposed implementations agree everywhere (`solution/advise.py` filters
   the catalog; `tools/planmodel.py` walks it once and builds a timeline);
7. LSN order never disagrees with clock order — which is what makes the `logs_by_clock` rival
   provably moot.

---

## 3. Dead ends and gate fights, with the grader's own wording

### 3.1 `qc_gate` B5 #1 — the bulk-logged rule (disclosed, correctly)

> *"its lone bulk-logged log (id 40) is targeted exactly at its finish, so the
> has_bulk_logged_data partial-log rule is never exercised. Rival rule 'ignore
> has_bulk_logged_data, always recover to target when a covering log exists'…"*

I had built the inert witness deliberately, as an *equivalence* (target exactly on the backup's
finish, where both readings agree) rather than an omission — the shape `rebuild-readout-builder`
§2 recommends. QC still called it underdetermined: an equivalence witness proves the shape is
visible, not that the rule is derivable.

**Resolution: state it.** The rule decides `stop_at`, which is an *output field*, so it was owed
to the agent under `rebuild-uptime-rollups` §7's output-definition-vs-field-convention test.
Disclosed in `instruction.md`, pinned by a shipped objective landing strictly inside such a
backup, and its two variants moved crux → machinery. **This cost no measurable difficulty**:
pass@2 was 2/2 genuine before and 2/2 genuine after.

### 3.2 `qc_gate` B5 #2 and #3 — the copy-only restore base. The expensive one.

> *#2: "CATALOG.md documents only data format (no algorithm); the sole disclosed example is
> sample_report.json where the copy_only full (id 22) is never the base. Rival rule 'exclude
> COPY_ONLY fulls from restore-base eligibility' reproduces sample exactly (SAMPLE match: True)
> but diverges on held-out…"*

**First attempt — relocate the discoverability sentence. Necessary, insufficient.**
The finding's *location* was `CATALOG.md`, and that was the clue: my flat "ORPHIC followed
standard SQL Server backup and restore practice throughout…" sentence lived only in
`instruction.md`. **Harbor hands `instruction.md` to the agent as the prompt; it is not a file in
the image, and the QC probe reads the pristine image.** So the probe had never seen it. This is
`rebuild-readout-builder` §3.3 in a second category. I repeated the sentence in `CATALOG.md`.

QC re-blocked on the same axis:

> *#3: "in all 8 disclosed sample objectives the restore base is always a NON-copy-only full
> (copy_only full id22 never used as base). Rival rule 'restore base = latest NON-copy-only full
> <= point' …"*

**What I did not do: disclose it.** The pass@5 analysis on an earlier commit had shown *this
exact reading* caused 4 of 4 failures. Disclosing would have spent the difficulty to satisfy a
gate — the `lumenp` §3 death spiral, one convention per round until nothing is left.

**Resolution: refute the rival in the shipped data.** `obj-03`'s base *is* the copy-only full.
The rival dies on the agent's own self-check, with no new prose. This is `motion-register` §3(g)
("refute the invented rule in the shipped archive") applied to a QC finding rather than to a
pass@2 artifact.

**It strengthened the task.** The precedent `obj-03` teaches — *copy-only is just a label, treat
these backups normally* — is exactly the wrong generalisation for axes A and B, which stayed
withheld. `rebuild-plate-rasterizer` §4.2's "equivalence makes it confident" with the sign
flipped: here the sample makes the agent confident in a rule that is true in the case shown and
false in the two cases hidden.

### 3.3 `qc_gate` C3 — boundary coverage

> *"Verifier does exact match against only 9 fixtures, none with a full/diff finishing exactly at
> a recovery point. Mutation: change base selection `<=point` to `<point` … passes everything"*

`replay-deposit-ledger` §4.1 says do not patch the case QC names. I enumerated every comparison
in the reference and gave each a boundary fixture, adding `base_finish_strict`,
`diff_finish_strict` and `chain_anchor_inclusive`. Four schedules gained a long-running full or
differential finishing exactly on a log-backup boundary.

**The real defect was in my invariant, not my fixtures.** `check()` required each disclosed
reading to move a *shipped* objective; it never required a *held-out* catalog to catch it. Adding
that assertion immediately exposed `base_by_start` as having no held-out witness either — a
second gap QC had not yet reached.

The instruction's data-shape guarantee was relaxed in the same commit (a `target_time` may now sit
on a data backup's *finish*, still not its *start*), because the stated rule already resolves it:
*"the most recent full-type backup set that **finished at or before** `stop_at`."* Fixtures that
contradict a guarantee the instruction makes are their own gate failure (`request-preconditions` §7.1).

### 3.4 `review` rubric — `no_extraneous_files` on `task/tools/`

> *"the contributor should either remove `tools/` … or document it as reviewer tooling via a
> `README.md` that references it (the `task_readme` criterion explicitly permits linking such
> tracing/verification tools), so it is no longer unreferenced."*

The tooling **was** documented — in the **root** `README.md`, which sits outside `task/`, so the
criterion never saw it. Two earlier runs graded this PASS with an explicit "borderline" note; the
third flipped it to FAIL on unchanged files. `contact-export` §3.4 exactly: satisfy the criterion,
do not re-push hoping for a lenient re-roll — every downstream gate skips while it is red.

**Fix: `task/README.md`** indexing each tool, stating that none is shipped or invoked at grading
time, with the reproduction commands. Kept deliberately free of `instruction.md` / solution /
`task.toml` content, which `task_readme` fails from the other side.

### 3.5 Rejected on paper, before any code

| Rejected candidate | Why |
|---|---|
| Copy-only **log** backups as an axis | a copy-only log preserves the archive point, so it overlaps the next ordinary log and **both chains restore legally** — genuine ambiguity, not a crux. `generate.py` asserts no log carries the flag |
| "First log backup is the one containing the data backup's `last_lsn`" (time-vs-LSN) | measured before building: log backups partition LSN space contiguously, so the first log finishing after a data backup *is* the one containing its `last_lsn`. Zero divergence. `sweep-replay` §3 — measure before writing the test |
| Shipping `database_backup_lsn` / `differential_base_guid` | would make the differential's lineage a lookup rather than a question about backup semantics |
| PostgreSQL MVCC / heap decoding, schema repair | four **closed** PRs on this same repo had already used them (§8.4) |

---

## 4. What worked

### 4.1 Reading the closed PRs on the repo before designing

`filer-access-audit` §8 says check the repo's other PRs. This repo had **four closed PRs**, all
PostgreSQL (heap/MVCC recovery ×1, schema repair ×3). That ruled out the entire obvious direction
for "Database administration" and pushed the design to SQL Server backup-chain semantics. PR #4's
transcript also supplied the acceptance arithmetic — **≥3 of 5 must fail, and an in-progress
timeout does not count** — which is why the agent budget was set to the full 3600 s.

### 4.2 Probing the real documentation before writing task code

`replay-rulepack-scores` §3.1. Every axis was checked against Microsoft Learn *first*. This killed
the copy-only-log axis (ambiguous) and confirmed the exact asymmetry that became axis B —
`COPY_ONLY` "has no effect" on a differential — which is the sentence the whole task ended up
resting on.

### 4.3 Searching for objectives instead of placing them

`generate.py` profiles **every candidate instant** in a catalog against the reference and every
rival, then selects: the shipped catalog takes only instants no crux misreading can tell apart,
each held-out catalog takes instants that expose the misreadings it is responsible for. When the
axis set changed three times, re-selection was automatic and the inertness invariant could not
silently rot.

### 4.4 Mutants through the real verifier, with the probe list read from the code

`tools/mutants.sh` builds the image, drops each advisor at `/app/advise.py` with `tests/` overlaid,
and runs the real `tests/test.sh`. Its probe list is read from `variants.py`, so it cannot drift
from the readings the invariants assert — the fix for `rebuild-uptime-rollups` §8's README-drift
bug, applied at the source rather than by re-transcribing.

### 4.5 Two exploit probes written out as files

`tools/exploits/copy_shipped_report.py` and `read_sealed_expectations.py` both score 0.000 in the
harness. `ava_review` passed first time it ran and never returned — contrast the three consecutive
`ava_review` blocks the corpus records elsewhere.

---

## 5. Gate-by-gate log

| Push | Commit | What it did | Result |
|---|---|---|---|
| 1 | `c24ce3b` | initial (PR #5) | static ✅ 25/25 · similarity **UNIQUE** · rubric ✅ **31/31 "Failures: None"** · validation ✅ · **pass2 died in the platform (§8)** |
| 2 | `590a080` | three more rival readings asserted; `mutants.sh` reads its probe list from the code | all pre-gates ✅ · **pass2 1/2 genuine → pass** · pass@5 **0/5 solved, 4 genuine** · deep_review ✅ · ava_review ✅ · tier1 ✅ · **qc_gate ⛔ B5 (bulk-logged)** |
| 3 | `c7e23db` | discoverability sentence repeated inside `/app/catalog/CATALOG.md` | platform fault; never evaluated |
| 4 | `8949595`, `7e82d1a` | empty commits, new PR (#6) then new branch + new PR (#7) | platform fault; §8 |
| 5 | `47d2954` | build/verifier timeout headroom | **rubric ⛔ `no_extraneous_files`** (§3.4) |
| 6 | `7cca78c` | `task/README.md` documenting the tooling | rubric ✅ · pass2 ✅ · deep_review ✅ · ava_review ✅ · tier1 ✅ · **qc_gate ⛔ C3** |
| 7 | `7c3a551` | boundary fixture on every comparison; held-out assertion | all ✅ except **qc_gate ⛔ B5 #3 (copy-only base)** |
| 8 | `9a59ac5` | `obj-03` based on the copy-only full | **everything ✅ · trials 1/5, 4 good valid fails, avg@5 = 0.200** → `accepted` |

Gates that **never** failed: `changes` (static), `cosine_similarity`, `similarity` (UNIQUE every
run), `validation`, `deep_review`, `ava_review`, `tier1`, `qc_eval`, `qc_exec`.

Similarity margins stayed comfortable: instruction 0.733, verifier 0.737, fingerprint 0.790–0.809
against a 0.9 block.

---

## 6. pass@5, and what the model actually did

**1/5 solved · 4 good valid fails · avg@5 = 0.200.** `task_specification`, `reward_hacking`,
`difficulty_crux`, `refusals`, `low_timeout` and `approach_validity` PASS on every trial;
`near_miss` FAIL on one of four.

> *"All four failing trials share the identical root cause: incorrectly excluding copy-only
> differentials from the differential candidate set by applying the COPY_ONLY filter (which
> legitimately governs whether a full can anchor a differential chain) to differential backups
> themselves."*

Four textually different spellings of one bug:

| Trial | The line |
|---|---|
| `task__Qgyyr6t` | `[bs for bs in backup_sets if bs['backup_type'] == 'differential' and bs['is_copy_only'] == 0]` |
| `task__c923q2z` | `if b['is_copy_only'] == 1: continue` inside `choose_differential()` |
| `task__U5Ku6a9` | `non_copy_diffs = [b for b in diffs if b['is_copy_only'] == 0]` |
| `task__wmy2QTh` | `not b['is_copy_only']` inside `diff_candidates` |

> *"The sample catalog was deliberately constructed to contain no copy-only differentials in any
> decisive position … so all four agents validated 'Values match: True' against the sample and
> submitted. The held-out catalogs h02, h04, h05, h06, h08 each place a copy-only differential as
> the only valid differential candidate."*

The solving trial *"succeeded specifically by constructing a synthetic copy-only edge-case test —
the correct generalization."* That is the fair-trap gut check passing: the winning move was
available and one agent in five made it.

**Three things worth carrying.**

1. **The over-application direction is the strong one.** Axis B punishes applying a real rule too
   broadly. Every agent knew `COPY_ONLY` mattered; none knew it stops mattering on a differential.
   A rule with an *exception* beats a rule that is simply unknown.
2. **`obj-03` — added to satisfy QC — probably raised the failure rate.** It teaches "copy-only is
   just a label," which is exactly the generalisation axis B punishes. The gate fix and the
   difficulty pulled the same direction, which is rare and worth looking for.
3. **All four failures were the same bug, not stratified.** An earlier commit's pass@5 (0/5 solved)
   failed on the *other* copy-only axis. Different commits, different dominant axis — keep both.

---

## 7. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| `qc_gate` B5, and your discoverability sentence is only in `instruction.md` | Repeat it inside `/app`. Harbor hands `instruction.md` over as the **prompt**; it is never a file in the image, and the QC probe reads the pristine image | Do not assume the probe sees the instruction. Check the finding's `loc` — it names the file the probe *can* read |
| `qc_gate` B5 on an axis your trials proved load-bearing | **Refute the rival with data**: ship an objective that lands *on* the rival reading, so the sample kills it on the agent's own self-check | Do not disclose the rule. That spends the axis to satisfy a gate, and QC will raise the next one anyway |
| You are about to add a sample case to satisfy B5 | Check what **precedent** it sets. Ours taught "copy-only is just a label," which is the wrong generalisation for the axes still hidden — the fix strengthened the trap | Do not pick the case that teaches the *right* generalisation; that concedes the neighbouring axes too |
| `qc_gate` B5 answered with an **equivalence** witness (target exactly on a boundary where readings agree) | Expect it to be insufficient on its own. An equivalence proves the shape is visible, not that the rule is derivable | Do not assume `rebuild-readout-builder` §2's "equivalence beats omission" clears B5. It clears *pass@2*; B5 is a different question |
| `qc_gate` C3 "none with X exactly at Y" | Enumerate **every** comparison in the reference and give each a boundary fixture — then check your **invariant**, not just your data. Ours never required a held-out witness | Do not patch only the comparison named. Adding the assertion exposed a second gap QC had not reached |
| Rubric `no_extraneous_files` on a `tools/` directory | Add **`task/README.md`** indexing them. The criterion looks inside `task/`; a root README does not count | Do not delete the tooling — `verification_explanation` depends on it, and `task_readme` explicitly permits linking it. Do not re-push unchanged hoping for a lenient re-roll |
| A rubric criterion that passed twice with a "borderline" note now FAILs | Satisfy it | Do not treat the earlier PASSes as precedent. Every downstream gate skips while it is red |
| `pass@2` reports `0 of N runs failed genuinely` | Read the sticky comment. **`0 of 2` with `NOT EVALUATED` and `0/2 analyzed` means the trials never produced results** — not that agents solved it | Do not read the gate's error text as a difficulty verdict. I nearly strengthened a task that had not been measured |
| pass@5 reports `5 completed · 0 failed` but `5 analyzer failures` | Platform. The trials ran; the write-up stage died. Re-run | Do not change the task. `0 solved` was correct; only the certification was missing |
| A candidate axis is a "real published convention" | Check whether it has an **exception**. Over-application beat non-knowledge 4:0 here | Do not assume the model's ignorance. All five trials knew `COPY_ONLY`; four misapplied it |
| Two conforming readings of your axis both restore legally | Cut it and assert the case cannot occur | Do not pick a side. Copy-only log backups were cut for exactly this |

---

## 8. The pass@k harness moved — read this before diagnosing any trial failure

GitHub no longer grades. It runs the reviews (structure, rubric, similarity, validation) and then
**waits** for Handshake's own runner, which reports back as a commit status, `harbor / pass@k`
(pass@2) and `harbor / pass@k (gate 2)` (pass@5). This is not described anywhere else in the corpus.

**The rules that follow from it:**

- **The result belongs to a commit, not a PR.** A new commit is a whole new evaluation; the same
  commit can replay a cached result.
- **GitHub waits 60 minutes and no longer.** Past that, `review / pass2` fails with *"the platform's
  'harbor / pass@k' status did not finish within 60 minutes"* and `0 of 0 runs failed genuinely`.
  **That is not a verdict.** Every downstream gate then shows `skipping`, which reads like a
  rejection and is not one.
- **`gh pr close` then `gh pr reopen` makes GitHub re-read a result that already finished.** Job
  `e8a0d333` was still "pending" when the gate gave up; a close/reopen 36 minutes later surfaced
  that same job id as `success`. The lab had finished; only the front desk had stopped listening.
- **Never push while the H status is spinning.** Per the project team: it kills the run and the PR
  stops being tested at all — no empty commit or close/reopen recovers it, only a brand-new PR.
- **The platform auto-retries a failed evaluation.** A single workflow run produced job `8aaffa6c`
  (failed) and then `9feef5ba`; on PR #7, `2975f71c` was a retry that *succeeded* where the first
  attempt had not. Do not assume a second job id means a duplicate-dispatch race — I diagnosed that
  wrongly and had to withdraw it.
- **`pass2` can pass with no H status on the commit at all** — a persisted result from the previous
  green run (the workflow has a "sanctioned skips" step). Seeing `H count=0` next to `pass2: pass`
  is normal, not a bug.

### 8.1 The five signatures, all platform, none a task defect

| # | Signature | Distinguishing evidence |
|---|---|---|
| 1 | H status **never created** | commit's status list empty for the full 60 min; `0 of 0 runs` |
| 2 | H status created then **went stale** | last `updated_at` 69 minutes before the gate gave up |
| 3 | `error — The evaluation did not finish. Re-run it.` | terminal error state on the status |
| 4 | Trials **failed to start** | `0 completed · 2 failed`, `0/2 analyzed`, header **NOT EVALUATED** |
| 5 | Trials ran, **analyzer** died | `5 completed · 0 failed`, `0/5 analyzed`, `5 analyzer failures`; the analyzer's own text: *"all five trial blocks are completely empty … I cannot fabricate trial data"* |

### 8.2 How to tell platform from task in one command

```bash
gh api repos/$R/commits/$SHA/status --jq '.statuses[]|"\(.context): \(.state) — \(.description) | \(.updated_at)"'
```

Empty list → never dispatched. `pending` with a stale `updated_at` → wedged. `error` → died.
Compare `updated_at` against now; a status that has not moved in an hour is a corpse.

### 8.3 What I wasted time on

- **Diagnosed a build-timeout cause that was wrong.** `build_timeout_sec = 600` versus a passing
  sibling task's `1800` looked decisive, and the timeline fit (the last completed evaluation was
  the last commit whose `environment/` was unchanged). Then the platform's own retry succeeded on
  the *same commit with the same 600 s budget*. The headroom commit stayed (600 → 1800, verifier
  300 → 900) as reasonable insurance, but it fixed nothing. **A correlation across commits is not
  a cause when a retry is in play.**
- **Diagnosed a duplicate-dispatch race that was wrong.** Two workflow runs 15 s apart on PR #6
  each dispatched a job; on PR #7 a *single* run also produced two jobs, which is auto-retry.
- **Compare against a sibling repo's PR.** The decisive evidence that the platform was healthy was
  another attempter's PR on a different repo passing `pass2` nine seconds after mine was created.

### 8.4 Check the repo's other PRs before designing

Four closed PRs here, all PostgreSQL. PR #4 (`pg-heap-recovery`) reached pass@5 **2/5 and was still
blocked** — the gate needs **≥3 of 5 failing**, and its fifth trial was an in-progress timeout,
which does not count. Read that arithmetic off a sibling PR rather than from the docs.

---

## 9. Bugs I introduced myself

1. **Docstrings in the reference stated the crux rules.** Harmless — `solution/` is never shipped —
   but worth checking, since the same text pasted into `environment/` would have ended the task.
2. **A `str.replace()` in a patch script silently matched nothing**, leaving one differential at
   9 minutes instead of 200. Caught only because the generator's boundary witness count came back
   zero. **Assert that every generated edit actually applied** (`experiment-analysis-frame` §7).
3. **`pick_heldout` had no "already covered" guard** where `pick_shipped` did, so a flag whose only
   witness was already chosen for an earlier flag asserted out.
4. **`calibrate.py` kept a `%d` format** after `coverage[flag]` became a string. Cosmetic, but it
   crashed the pre-push check.
5. **The first PR body was reused verbatim on the replacement PR** and described three withheld
   conventions after one had been disclosed. Rewrite the PR body when the design changes; reviewers
   read it.

---

## 10. Process rules confirmed or learned

- **Never `git add -A`.** `harbor` writes `task/jobs/`; `task/.gitignore` carries `jobs/`, `build/`,
  `__pycache__/`, and every push staged explicit paths.
- **`gh repo fork <repo> --clone` clones into the current directory**, not the one you meant.
- **Set commit identity at clone time** from `gh api user`; the email is empty for a private
  account, so use `<id>+<login>@users.noreply.github.com`.
- **`.dockerignore` in `environment/` before the first push** — `environment/` has a `data/`
  subdirectory, so the static check requires it. Five tasks have now hit this.
- **Keep the literal strings `solution/` and `tests/` out of the Dockerfile**, comments included —
  that static check is a string scan (`filer-access-audit` §5.1).
- **Omit the "You have N seconds…" line.** Confirmed again; `instruction_concision` PASS without it.
- **`ctrf.json` carried 14 individually named tests** — no `parametrize` collapsing, so graders got
  per-fixture resolution. Worth the explicit test functions (`replay-strata-plans` §6.1).
- **A push to a closed PR lands on the branch but triggers nothing.** PR #6 had gone CLOSED without
  my closing it; the head stayed on the old commit until I reopened it, making the push look inert.
- **GitHub cannot delete a PR, only close it.** "Delete the PR and make a new one" means close + new.
- **Re-grep the agent-visible surface before every push:**
  `grep -rinE 'copy.only|bulk|convention|standard practice' task/instruction.md task/environment/`.
- **Diff the README's numbers against a fresh harness run**, never transcribe
  (`rebuild-uptime-rollups` §8).

---

## 11. Reusable checklist

Design:
- [ ] Read the repo's **closed and open PRs** first — they rule out whole directions and carry the
      current acceptance arithmetic.
- [ ] Probe the real documentation before writing code; cut any axis where two readings are both legal.
- [ ] Prefer a convention with an **exception** over one the model may not know. Over-application is
      the stronger trap.
- [ ] Keep the axis you think is weakest. Fifth confirmation.

Data and invariants:
- [ ] Sample bit-inert under every crux misreading, asserted at generation time.
- [ ] Each crux misreading broken by ≥3 held-out catalogs.
- [ ] Every disclosed reading breaks the shipped catalog **and ≥1 held-out catalog** — assert both.
- [ ] Every comparison in the reference has a fixture exactly on its boundary.
- [ ] Every rival reading left unstated is asserted moot on every fixture.
- [ ] Objectives **searched** against the variant table, not hand-placed, so re-selection survives a
      design change.

Disclosure:
- [ ] The flat "standard practice governs" sentence exists **inside `/app`**, not only in
      `instruction.md` — the QC probe reads the image.
- [ ] Anything the output schema depends on is stated, not withheld.
- [ ] When B5 blocks an axis you cannot spend, refute the rival **with a shipped case**, and check
      what precedent that case sets.

Packaging:
- [ ] `task/README.md` documenting any `tools/` directory.
- [ ] Root `README.md` re-derived from a fresh harness run, in the same commit.
- [ ] PR body rewritten whenever the design changes.

Pipeline:
- [ ] Never push while the H status is spinning.
- [ ] Classify platform-vs-task from the commit status before touching `task/`.
- [ ] One push per round of work; hold improvements locally.

---

## 12. One-paragraph version for future me

A retired SQL Server restore-planning tool, rebuilt from one surviving `msdb`-shaped backup-catalog
export and the runbook it produced, graded on eight held-out catalogs with exact equality and no
tolerances; accepted at **pass@5 1/5, avg@5 0.200**, with all four failures on one withheld
convention — that `COPY_ONLY` **has no effect on a differential**, so a differential carrying the
flag is ordinary — which four agents independently got wrong by writing a single `is_copy_only == 0`
filter and which the shipped sample was built never to exercise. The design lesson is that a rule
with an *exception* beats a rule the model does not know: every trial knew what `COPY_ONLY` meant
and four applied it too broadly. The expensive fight was `qc_gate` B5, raised three times on the
copy-only family; the corpus's flat "standard practice governs" sentence did not clear it, first
because it lived only in `instruction.md` — which Harbor hands over as the *prompt* and never places
in the image the QC probe reads — and then because the sample still never exercised the rival. What
cleared it was **refuting the rival with data instead of prose**: one shipped objective whose base
*is* a copy-only full, which kills "skip COPY_ONLY fulls" on the agent's own self-check while
teaching the precedent *copy-only is just a label*, precisely the wrong generalisation for the two
axes still hidden — the gate fix and the difficulty pulled the same way. C3 was answered by
enumerating every comparison and discovering the real hole was my invariant, which never required a
held-out witness. And roughly two days went to a **new pass@k harness** that grades on Handshake's
runners and reports back as a commit status GitHub waits only 60 minutes for: five distinct infra
signatures, none a verdict on the task, one wrong build-timeout diagnosis and one wrong
duplicate-dispatch diagnosis on my part, and the single most useful check being another attempter's
PR on a different repo passing at the same minute.
