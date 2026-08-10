# Dynamo playbook — `dynamo/decode-freight-interchange`

**Outcome:** accepted. Every automated gate green, **pass@5 0/5, avg@5 = 0.000, all five valid failures**.
**Repo:** `handshake-project-dynamo/dynamo-ed51da6-data-processing-and-etl`, PR #1
**Category / Sub-category (pre-seeded):** Data Processing and ETL / Text processing
**Final commit:** `46c0122`

This file lives **outside** any git repo on purpose — the parent folder is not a repository, so
it can never be committed into a task or shipped to an agent. It is a retrospective written for
the *next* task. Section 3 is the one that matters most; the rest is the evidence.

---

## 1. What the task asks

A freight gateway was decommissioned and its reader went with it. Its archived traffic is
written in **TCX-A**, an invented delimiter-declaring interchange dialect. The agent writes
`/app/decode.py`, invoked `python3 /app/decode.py <archive> <out_jsonl>`, decoding an archive
into JSON Lines — one object per message that survives the archive, six keys each. Graded on
17 held-out archives it never sees.

Agent-visible material: `instruction.md`, a normative memo `FORMAT.md`, and six sample archives
each paired with the decoding the retired reader produced.

**The dialect's decisive properties.** Each *interchange* declares its own five special
characters in an 8-character header (element / component / repetition separators, release
character, segment terminator). The release character strips the special meaning from any of
them. An archive holds one or more interchanges laid end to end. Retransmission and withdrawal
are settled across the whole archive, not per interchange.

---

## 2. Final shape of the difficulty (what actually worked)

Three independent mechanisms, **none of which the shipped samples diagnose**:

1. **Release state must survive the whole scan.** Split-then-unescape, or resolving releases at
   each split level, loses which separators were ever real.
2. **An archive is a batch of interchanges**, each with its own delimiters. Reading the header
   once and running to EOF swallows the next header as segment data.
3. **Cancellation is settled, not replayed.** A withdrawal on a copy later superseded was never
   issued; an incremental pass cannot un-apply it.

**The amplifier that makes it bite:** a mis-lexed segment changes a message's segment count, so
its trailer disagrees, the message is classified damaged, and it *silently disappears*. No crash.

Measured, each wrong in exactly one way:

| Wrong in one way | Samples | Held-out |
|---|---|---|
| Releases resolved per split level | **all pass** | fails 12 of 17 |
| Single interchange assumed | **all pass** | fails 4 of 17 |
| Withdrawal applied while streaming | **all pass** | fails 3 of 17 |

---

## 3. THE LESSON: samples must **validate**, not **diagnose**

This is the single most transferable finding, and it cost three redesigns to learn.

> Shipped samples must let a **correct** implementation confirm itself, while giving an
> **incorrect** implementation no signal about *what* is wrong.

### The iteration log

| # | Design | pass@2 | Why |
|---|---|---|---|
| 1 | Released terminator held back; samples released element/component/repetition separators | 1/2 (1 solved, 1 infra-truncated) | agent debugged out via sample diffs |
| 2 | + 4 more held-out archives, timeout 2400→3000 | **2/2 solved** | more *shapes of a rule the samples teach* changes nothing |
| 3 | + archives are batches of interchanges (new latent crux) | **2/2 solved** | **anything written in the spec gets implemented** — both agents built the loop from one sentence |
| 4 | **Removed every released separator + released release-char from the samples.** Rule still stated in `FORMAT.md` §3; all coverage moved to held-out | **0/2, both valid** → **pass@5 0/5** | ✅ the naive build now has no feedback loop |

### Why 2 and 3 failed, stated precisely

- **Adding held-out shapes of a rule the samples already teach is wasted effort.** The agents
  wrote the naive splitter, `s02`/`s03`/`s06` told them exactly which archives broke, they
  diagnosed and rewrote. Their words in the analysis: *"agents can find their way out given the
  shipped sample feedback signal."*
- **A disclosed-but-unexercised clause is not automatically a stump.** This is where I was
  wrong. I assumed the accrued-interest precedent (doc 34) transferred — model knows the rule,
  sample never fires it, model skips it. It does **not** transfer when the rule is written in a
  spec file the agent reads end to end. There, reading and implementing is mechanical. In
  accrued-interest the rule was *outside domain knowledge absent from the task entirely*.

### The rule to apply next time

> Suppression comes from the sample never making the case **salient**, not from the model
> lacking the fact. Frontier models possess the domain fact cold. The moment *anything* —
> prose, a witnessed sample, a failing diff — makes it salient, the suppression is gone.

Corollary from the `fir-boundary-metrics` playbook, independently confirmed here: **disclose the
raw premise, never the consequence.** State the definition/range/convention; let deriving its
implication for the specific computation be the skill under test.

---

## 4. Error → what to do, and what NOT to do

### pass@2 says "both solved, too easy"

- ✅ **Find what makes the crux salient and remove it.** Usually the samples, not the prose.
- ✅ Ask: *does a correct implementation confirm itself while an incorrect one learns nothing?*
- ❌ **Do not shorten `[agent].timeout_sec`.** Explicitly called out as gaming; reviewers catch it.
- ❌ **Do not add busywork or volume.** Difficulty must come from reasoning.
- ❌ **Do not add more held-out shapes of a rule the samples already expose.** Measured: no effect.
- ❌ **Do not add a "witnessed example" when a reviewer suggests disclosure.** The friend's log
  shows this is *as strong a hint as prose* and destroyed difficulty (their attempt 4).

### pass@2 says "blocked — approach_validity / undisclosed rule"

- ✅ Disclose the **mechanism** in an agent-visible normative file. Withhold only *shapes*.
- ✅ Consider letting the samples punish the naive build for *some* instances — but see §3, this
  is exactly the trade-off that makes it too easy. Prefer: state the rule, ship no instance.
- ❌ Do not leave the deciding rule out of all agent-visible material. That is the one thing
  that hard-blocks (`dynamo-d5a485c` stalled here for weeks).

### pass@2 says "infra/setup-timeout" or "AgentSetupTimeoutError"

- ✅ Re-run. The gate says outright *"not a problem with your task."*
- ✅ `/rerun` is admin-only; an **empty commit** is the only re-trigger a contributor has.
- ❌ Do not change the task. Do not raise the timeout in response to an allocation failure.

### QC finding: "Ambiguous Rule" / "Oracle Edge-Case or Logic Bug" on wording

- ✅ Read their **cited input** and run it through your reference. They construct real
  counter-examples.
- ✅ Rewrite the sentence so a competent reader cannot land on the other reading, **and** add a
  fixture that pins it. Both, not either.
- ❌ Do not argue the reading was unreasonable. Mine — *"read as a single component"* — genuinely
  admitted "whole element is one value", which is what their decoder did.

### QC finding: "Narrow / Hardcodable Held-Out Coverage"

- ✅ Reproduce their exact mutant, confirm it survives, add fixtures until it dies, then keep the
  mutant as a **permanent probe**.
- ❌ Do not just add more archives of the same shape.

### QC finding: "Reward / Harness Plumbing Exploit"

- ✅ **Drop privileges for the graded program.** `useradd grader` in the Dockerfile,
  `subprocess.run(..., user="grader")`. This closes reward-file writes, harness signalling, and
  tampering with `/app/data` in one move.
- ✅ Isolate each held-out input in a directory containing nothing else.
- ✅ Derive expectations up front, hold in memory, **unlink the reference module** before grading.
- ❌ Do not assume "there's no answer file on disk, so there's nothing to steal." The exploit
  here didn't steal anything — it *wrote its own reward and killed the harness*.
- ❌ Do not fix only the specific instance the playbook mentions. I matched their finding to the
  sibling-file issue, fixed that, and stopped — without asking the broader question *"what else
  can agent code reach while running as root?"* That cost a whole cycle.

### AVA advisory: verifier accepts something the instruction forbids

- ✅ Prefer **aligning the instruction to the lenient verifier** over tightening the verifier.
  Formatting checks should never decide a run.
- ❌ Do not tighten the test if doing so could fail a *correct* solver (trailing newline, BOM).

---

## 5. Bugs I introduced myself (and how to avoid them)

- **Fixing one thing silently removed coverage of another.** Adding the withdrawal mechanism to
  `s05` made `TC-7002` withdrawn — and `TC-7002` was the *only* record whose surviving position
  differed from its first appearance. The output-ordering rule became pinned by nothing.
  → **After every fixture change, re-run the full mutation suite, not just the new case.**
- **A probe silently stopped matching.** Changing the digit check left one mutation's `old`
  pattern unfound, so it was skipped rather than failing loudly.
  → **Treat "PATTERN NOT FOUND" as an error, not a warning.**
- **Stale docs.** `README.md` claimed *"the samples already punish that"* long after that stopped
  being true, and a calibration table survived two fixture changes.
  → `readme-rule.md` exists for this. Update README in the **same commit** as any `task/` change,
  and re-measure numbers rather than carrying them forward.
- **Claimed work was committed when it was only staged.** Check `git status`, don't assume.
- **Left `task/jobs/` (harbor output) untracked in the tree.** Would have tripped
  `no_extraneous_files`. → `rm -rf jobs` after every local `harbor run`.

---

## 6. Build these BEFORE the first push

Local `harbor run --agent oracle/nop` only proves the verifier accepts the correct answer and
rejects doing nothing. It says nothing about the axes QC actually probes. All four of these are
cheap and would have caught most of what cost a cycle:

1. **Independent second implementation.** Write the decoder twice, using a *different strategy*
   (mine: released-flag per character vs. masking releases to private-use sentinels then plain
   `str.split`). Diff on every archive. Caught nothing here — which is itself the point: it makes
   "the whole task rests on one reference implementation" defensible to a reviewer.
2. **Mutation probing.** ~20 targeted one-rule changes to the reference; each must be killed by at
   least one fixture. Ended at **22/23** (the survivor is inert on well-formed input).
3. **Rule-coverage sweep.** For *every rule in the spec*, does at least one fixture fail a decoder
   that ignores it? Found a real gap nothing else did: no message had 2+ `FTX` segments, so a
   decoder reading only the first passed all 23 archives.
4. **Hostile-input fuzz.** ~4,500 archives — adversarial counts/refs/names, random 5-delimiter
   sets — asserting the oracle never crashes and agrees with the independent implementation.
   This is the axis mutation testing does *not* cover.

**And write every exploit before fixing it.** Each of the four bypasses was confirmed by measuring
1.0-before / 0.0-after with the genuine oracle still at 1.0. Without that you cannot tell a real
fix from a placebo.

---

## 7. Python traps that bit here

- **`str.isdigit()` is true for `²`, `³`, `¹`, `٣`, `⁵`.** `int("²")` raises `ValueError`;
  `int("٣")` returns 3. If a spec says "written in decimal", test explicitly against
  `"0123456789"`. Never `isdigit()`, and `isdecimal()` is not enough either.
- **Universal newlines.** Reading with `open(path, encoding="utf-8")` converts a lone `\r` to
  `\n`. Keep `\r` out of fixture data entirely so the ambiguity never arises.
- **Read agent output with `utf-8-sig`** so a BOM cannot fail a correct solver.
- **`tempfile.mkdtemp()` is 0700 and root-owned** — chmod it if an unprivileged process must write
  there.

---

## 8. Process notes

- **Never push while a run is in flight.** `concurrency: cancel-in-progress: true` kills it.
  Check `gh pr checks 1 | grep -cE "pending|queued"` → must be `0`. I lost one advisory comment
  by pushing while `pass2_suggestion` was still going.
- **Batch fixes into one push.** pass@2 is capped at 6 runs/day and every push restarts the
  *whole* pipeline including a fresh pass@2.
- **Gates are a chain.** Any failure skips everything downstream. `qc_gate` never ran for three
  cycles — twice blocked by pass@2, once by an infra flake — so its fixes sat ungraded.
- **Sticky comments update in place.** A verdict on the PR may be from the *previous* run. Check
  the job list for the current run ID before reacting.
- **The "Pass@2 Difficulty Suggestion" is advisory but excellent.** It diagnosed the sample-
  feedback problem correctly *and* proposed the fix that worked, better than my own plan (I was
  about to build a reverse-engineered check value). Rate-limited 2/day. Read it.
- **The `"You have N seconds…"` instruction suffix must be OMITTED.** The local doc set mandates
  it; the live rubric flags it as a TB3 artifact. Trust the live pipeline over cached docs.

---

## 9. Timeline

~10 pipeline runs over roughly 2 days. Roughly: 3 difficulty redesigns (each ~1.5h of pipeline),
4 QC/AVA security fixes, 1 infra flake costing a full cycle, 1 self-inflicted coverage regression.

**Where the time actually went:** not the code. The decoder is ~200 lines and was right early.
It went into discovering that *samples teach*, which only agent trials can tell you — and into
three QC findings that local correctness testing structurally cannot find.

---

## 10. One-paragraph version for future me

Design a Pattern-A/B trap where the deciding rule is **stated in an agent-visible normative spec
but exercised by no shipped sample** — samples validate a correct build and diagnose nothing.
Verify numerically *before writing any task files* that each single-mistake variant passes 100%
of samples and fails held-out. Build the verifier's anti-cheat in from the start: unlink the
oracle before grading, isolate every held-out input in its own directory, and run the graded
program as an unprivileged user — then prove each by writing the exploit and measuring
1.0-before/0.0-after. Ship four local checks (independent second implementation, mutation probes,
rule-coverage sweep, hostile-input fuzz) before the first push, because `oracle=1.0 / nop=0.0`
proves almost nothing. Update `README.md` in the same commit as any `task/` change and re-measure
every number rather than carrying it forward. Never push while a run is pending; batch fixes.
When a gate says "too easy", remove what made the crux salient — never shorten the timeout, never
add busywork, and never add more held-out shapes of a rule the samples already expose.
