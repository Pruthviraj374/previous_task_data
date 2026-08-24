# dynamo/session-reconstructor — case study

**Status:** Accepted 2026-08-24 at commit `dd1fdb8`. PR labeled `accepted`.
**PR:** https://github.com/handshake-project-dynamo/dynamo-0cfa37b-data-science-and-reporting/pull/1
**Repo:** `handshake-project-dynamo/dynamo-0cfa37b-data-science-and-reporting`, branch `submission`.
**Category / Sub-category (pre-seeded):** Data Science and Reporting / **Exploratory data analysis**.
Benchmarked against Opus-4.8 via Terminus-2.

**Final result: pass@5 = 0/5 solved, avg@5 = 0.000, five good valid failures.** Every
verifier-soundness gate (`ava_review`, `deep_review`, `qc_eval`, `qc_exec`, `qc_gate`,
`tier1`) passed clean on the very first push of the winning design — zero findings, zero
iteration cycles. This is the best outcome the spec defines, and it followed **five
consecutive too-easy results** on the same task repo across two completely different
mechanism families. The finding worth carrying forward is in §5.

Twelve commits total, six of them distinct design attempts. Read §4 before starting a new
task in this category — pure descriptive-statistics EDA is a near-dead end for this
model/agent pairing, and the mechanism that finally worked wasn't a new stump technique, it
was fixing the oracle to honor a word already sitting in the instruction.

---

## 1. The task

A retired web-analytics pipeline reconstructed per-session summaries from a raw event log
and a per-session-type policy table (inactivity-gap timeout, IANA time zone). The pipeline is
gone; its output for one archived log survives.

- **Agent sees:** `instruction.md`, `/app/data/events.csv`, `/app/data/session_types.csv`,
  and `/app/data/expected_sessions.json` (the pipeline's own reconstruction, as an
  end-to-end self-check).
- **Agent produces:** `/app/sessionize.py`, invoked as
  `python3 /app/sessionize.py <events_csv> <session_types_csv> <output_json>`, plus the run
  over the shipped inputs at `/app/output/sessions.json`.
- **Graded on:** the shipped log plus **twenty-one held-out logs**, each with its own
  session-type table, never shipped, re-run through the agent's own program. All-or-nothing.
- **Constraint:** Python standard library only, no network.

---

## 2. The design that worked: six real operational conventions, one of them a self-inflicted latent bug

Six rules decide the answer, all stated in `instruction.md`:

1. **Per-session_type gap threshold**, joined from a second CSV by key.
2. **A `session_id` is not a session** — recurrence after any close starts a new one.
3. **A valueless event still counts** in `event_count` but not in the value aggregates.
4. **An explicit `end` event closes a session immediately**, independent of the timeout.
5. **A session never spans a local calendar day** in its session_type's own time zone —
   requires real IANA/DST-aware conversion (`zoneinfo`), not a fixed UTC offset.
6. **A same-timestamp tie is not "later."** `event_ts` has whole-second resolution, so two
   events sharing a `session_id` — including an `end` and an ordinary event, or two `end`
   events — can legitimately carry the identical timestamp. Rule 4's own wording already says
   a *later* event starts a brand-new session; a tied event isn't later, so it stays in the
   segment being closed. **This needed zero new words in `instruction.md`** — the reference
   implementation itself had never actually honored "later" for ties, because no fixture had
   ever exercised one. Fixing the oracle to match its own already-stated rule, and adding
   fixtures that exercise the gap, was the entire change.

The shipped sample is fully inert on all six axes (single time zone, no ties, no nulls, no
end markers, one session per id, all mid-afternoon local time). Twenty-one held-out logs
isolate each rule and combine them, including logs requiring four or five mechanisms in one
reconstruction.

---

## 3. Gate log for the winning design (commit `dd1fdb8`)

Every gate on the single push:

| Gate | Result |
|---|---|
| static / rubric | PASS |
| duplicate / similarity / cosine_similarity | PASS |
| validation (oracle=1.0, nop=0.0) | PASS |
| **pass@2** | **0/2 solved, 2 valid failures** — both trials hit rule 6 identically |
| `pass2_suggestion` | skipped (not needed — pass@2 already failed) |
| `ava_review` | PASS, no findings |
| `deep_review` | PASS, no findings |
| `qc_eval` / `qc_exec` / `qc_gate` | PASS, no findings |
| `tier1` | PASS |
| **pass@5 (`trials`)** | **0/5 solved, 5 good valid failures, avg@5=0.000** |

Zero QC or AVA findings, zero fix cycles. `approach_validity` and `difficulty_crux` PASS
unanimously across all seven trials (2 + 5) — the reviewers explicitly confirmed the rule is
fair: *"'later' in instruction.md unambiguously encodes strict ordering... a competent reader
could and should implement the guard... no task/verifier defect."*

`near_miss` FAILed on 6 of 7 trials (19/24 or 23/24 tests passing, one missing boolean
clause) — flagged explicitly by reviewers as informational, not a task defect: *"the
all-or-nothing verifier threshold is doing significant work here... conceptually the agents
implemented ~96% of the solution... this does not indicate the task should be made easier."*
Both pass@2 agents independently wrote the identical buggy pattern (`if closed: split`, no
timestamp guard); across pass@5, one trial (`task__sGZhzZc`) even quoted the word "later"
from `instruction.md` in its own reasoning and explicitly dismissed the tie case as "likely
not tested" — then failed on exactly that case.

---

## 4. The five failed attempts before this — what a dead end looks like in this category

**Attempts 1–2 (column-profiler, Tukey hinges + modified z-score):** pass@2 solved 2/2
*twice*, on two different disclosure/breadth variants. Both axes were "pick the right named
statistical method from the instruction's own vocabulary" — this model recalls named
textbook conventions (Tukey hinges, modified z-score, IQR fences) from training and
implements them correctly regardless of how the axes are worded or how many are stacked.

**Attempt 3 (session-reconstruction, 2 rules):** rejected by the static rubric for
insufficient breadth (`essential_difficulty`/`code_dependent`) even with one entangled
end-marker interaction — confirms `dynamo-2bb7b69-sweep-replay`'s finding that breadth
requires real additional LOC, not just an additional interaction between two existing rules.

**Attempt 4 (4 disclosed procedural rules, breadth added):** pass@2 solved 2/2 a third time.
Confirms this model transcribes **any number** of fully-specified procedural rules correctly,
however entangled, as long as each is stated outright — matching the pattern this playbook
has already documented on `resolve-unit-config` and `iban-batch-validate`, except in reverse:
those tasks' *procedural* layers were also freely disclosable, but their *domain-algorithm*
layers had real residual research depth once disclosed. A session-reconstruction procedural
rule has no such residual depth — once you're told the rule, implementing it is trivial.

**Attempt 5 (5th rule: DST/IANA time zone, real external convention):** pass@2 solved 2/2 a
fourth time even with the exact stdlib tool (`zoneinfo`) named in the instruction. A
follow-up push removing that tool name — testing whether naming the tool was the reason it
solved — **also** solved 2/2 (5th consecutive too-easy result). The pass@2 analysis was
explicit: *"IANA time zone name" plus "Python standard library" is enough on its own for this
model to dispatch straight to `zoneinfo` and reason about DST correctly* — its prior on that
specific pairing is strong enough that naming the tool was never load-bearing. This cleanly
falsified the "it's just the tool-naming" hypothesis and confirmed the deeper one: **DST/IANA
timezone handling is squarely inside this model's confident training prior, not a genuine
derivation gap, for this domain.**

**What this rules out for future Data Science / EDA tasks against this model:** (a) named
statistical conventions, however many are stacked; (b) disclosed procedural business rules
with no residual algorithmic depth, however entangled or numerous; (c) real external
technical conventions that are themselves extremely well-known and single-call to implement
(DST via `zoneinfo` specifically — a domain convention requiring genuine multi-step research
per instance, the way IBAN's national domestic-check algorithms did, would likely behave
differently, but plain DST-awareness does not).

---

## 5. The finding worth carrying forward: check existing instruction wording before inventing a new axis

The instinct after 5 failures was to invent a 6th disclosed axis (a same-timestamp
`end`-vs-`activity` tie-break). Pre-mortem analysis before writing any code surfaced a
structural problem with that instinct directly: **unlike IBAN/systemd/COBOL, a bare tie-break
rule has no residual algorithmic depth once disclosed** — implementing "end wins the tie" is
one extra sort-key comparison, not a researchable multi-step algorithm. That meant the two
obvious paths were both bad:

- **Disclose the resolution explicitly** → certain 6th "too easy" result, no depth to survive
  disclosure.
- **Leave it fully undisclosed with no real external authority** → real risk of a QC
  "Ambiguous Rule, No Disambiguation" rejection (the same category IBAN hit), since there was
  no genuine outside convention to point to, only an author-invented pick.

**The way out was neither.** Re-reading `instruction.md`'s existing rule 4 — *"any **later**
event sharing that `session_id` starts a brand-new session"* — showed the disclosure already
existed, implicitly, in wording written for attempt 3/4 and never revisited. The reference
implementation had simply never been checked against its own stated word for the
same-timestamp case, because no fixture had ever forced the question. This was a real latent
oracle bug (self-inflicted, not a reviewer-planted trap), not a designed stump — fixing it and
adding fixtures cost zero new instruction text and produced a clean pass@2/pass@5 fail on the
first try.

**Practical rule for next time:** before inventing a new disclosed-vs-undisclosed axis from
scratch, grep your own `instruction.md` for load-bearing words in already-shipped rules
("later," "each," "its own," "any," "only") and ask whether the reference actually honors
every reading of that word. A rule that's already textually present but not yet mechanically
enforced sidesteps the disclose-and-lose / hide-and-be-unfair dilemma entirely, because the
fairness authority was never in question — only the oracle's own correctness was.

---

## 6. Process notes

- **CR/LF discipline on Windows Git Bash:** `grep -c '\r'` gives false positives (matches
  every line). Verify with direct Python byte-level checks
  (`b'\r' in open(f,'rb').read()`) on both working-tree files and staged git blobs
  (`git show :path`) before every commit.
- **Verify the exact prior-design behavior scores 0 on the new fixtures before pushing.**
  Built the pre-fix reference (identical to what shipped in `91d0440` and solved 2/2 five
  times) as a literal file swap, ran it through the real `harbor run -p . --agent oracle`,
  confirmed 0.0. This is the single highest-value pre-push step across this whole task and
  every prior case study in this playbook.
- **Regression-check the fix against every existing fixture, not just the new ones.**
  Exhaustively scanned all 22 `DATASETS` entries for accidental duplicate timestamps before
  claiming the fix was a true no-op on everything except the five new tie fixtures.
- **A reviewer explicitly validating a rule as "fair" because it's textually present, however
  subtly, is strong evidence for the checklist rule in §5** — `task_specification` PASS was
  unanimous across all 7 trials specifically because the word "later" already existed.
- **Background `sleep`-loop polling for CI status got killed twice by the runtime** mid-task;
  `ScheduleWakeup` (checking back on a timer rather than blocking in a long-running shell
  loop) proved more reliable for monitoring an open PR across gate cycles.
- **False-positive static rubric finding on a pinned Docker digest:** a reviewer flagged
  `python:3.13-slim-bookworm` as lacking system `tzdata`, while explicitly noting it "could
  not execute Docker to confirm." Verified directly with `docker run <digest> python3 -c
  "from zoneinfo import ZoneInfo; ZoneInfo('America/New_York')"` — resolved cleanly. Added
  explicit `apt-get install tzdata` anyway (zero-cost, removes doubt) rather than arguing.

---

## 7. Pointers

| Thing | Where |
|---|---|
| Reference reconstructor | `task/solution/sessionize.py` (+ `solve.sh`) |
| Verifier | `task/tests/test_outputs.py` — 21 held-out `DATASETS` entries, in-process reference reconstructor, unprivileged sandboxed execution |
| Sample fixtures | `task/environment/data/` — `events.csv`, `session_types.csv`, `expected_sessions.json` |
| Mid-task handoff (pre-6th-axis pause point) | `HANDOFF-dynamo-0cfa37b-column-profiler.md` in this folder |
| Commits | `d902e38` initial (column-profiler) · `e00468d`/`a1f282d` stats breadth attempts · `20f25b1` pivot to session-reconstruction · `430803e`/`193e570`/`87b9559` breadth + DST · `be471e1` tool-naming test · `91d0440` tzdata fix · `dd1fdb8` sixth axis (accepted) |

---

## 8. One-paragraph version for future me

On Data Science / EDA tasks against this model, expect named statistics conventions and
fully-disclosed procedural rules — however numerous, entangled, or dressed in real external
authority — to get solved, because this model transcribes stated rules and recalls textbook
conventions regardless of wording; five consecutive pass@2 solves across two mechanism
families confirmed this before anything worked. What finally produced a clean 0/5 was not a
new stump technique, it was auditing the task's own already-shipped instruction for a
load-bearing word ("later") that the reference implementation had never actually been checked
against — a same-timestamp tie was legal under the data model but no fixture had ever forced
the reference to prove it honored its own rule. Fixing the oracle to match its own spec, and
adding fixtures that exercise the gap, required zero new disclosure and produced a
first-try, zero-finding, unanimous-approach-validity accept. Before inventing a new axis from
scratch — especially one with no residual algorithmic depth once disclosed, which makes it
vulnerable on both the disclose-and-lose and hide-and-be-unfair sides at once — check whether
your own prior wording already implies a rule your reference hasn't lived up to yet.
