# dynamo/rebuild-motion-register — a board secretary's motion register under RONR

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 16 gates pass, PR labelled `accepted` |
| **Repo** | `handshake-project-dynamo/dynamo-0b74904-regulated-knowledge-work-and-business-operations` |
| **PR** | #1 |
| **Category / sub-category** | Regulated Knowledge Work and Business Operations / **Personal Assistant Productivity** (pre-seeded, not editable) |
| **Benchmarked model / agent** | Opus-4.8 / Terminus-2 |
| **Final commit** | `da843bc` |
| **Headline** | **pass@5 = 0/5** (every trial reward 0.0), avg@5 = 0.0 — the best available outcome |
| **Cost** | 11 pushes, 6 abandoned crux designs, ~14 hours of gate cycles |

The single most valuable thing in this file is §3. Five of the six abandoned designs failed for
**the same reason**, and the reason is not obvious: this model recalls published conventions
essentially perfectly, so a task whose difficulty is "know a convention" is not difficult.

---

## 1. What the task asks

A board secretary kept the minute book with an in-house program. It read the minutes and wrote
the motion register — how each motion was disposed of, and per-meeting and archive-wide counts.
The program is lost; the minutes and one register survived. Rebuild it.

The agent writes `/app/register.py`, invoked `python3 /app/register.py <archive_dir> <out_json>`.

An archive is two files:

- `body.json` — `{"name", "members": [...], "quorum": <int>}`. `members` is the **entire**
  membership, present or not.
- `meetings.json` — meetings in date order, each with `present`, `notices` (given *during* this
  meeting), `call_notices` (carried in the call *for* this meeting), and `motions` in the order
  taken up. A `main` motion carries a `subject`; a `rescind` / `amend_previous` carries a
  `targets` naming the main motion it acts on.

Output is `{"motions": {id: {meeting_id, status, yes, no, abstain}}, "by_meeting": {...},
"totals": {...}}`, `status` ∈ `adopted` / `lost` / `out_of_order`.

The agent sees the shipped archive at `/app/data/archive/` and the register produced for it at
`/app/data/register.json`. Graded on nine archives — the shipped one plus eight held out — with
exact integer comparison and no partial credit.

---

## 2. The crux, and the invariants that keep it alive

**Two independent rules, each invisible on the shipped archive, each individually sufficient to
fail the whole task.** That independence is the entire design; see §4.

**Crux 1 — a target's standing is dynamic.** Under RONR, Rescind / Amend Something Previously
Adopted is in order only while the motion it targets *still stands*. Acting on something that was
lost, that never reached a vote (inquorate meeting), or that a **carried rescission has already
struck**, is `out_of_order` and never reaches a vote. The natural wrong build records each
motion's disposition once and reads it back — `motions[target]['status'] == 'adopted'` — which is
right for "never adopted" and wrong for "adopted then struck".

**Crux 2 — renewal.** A question the assembly has rejected cannot be moved again in the **same
session**; it may be renewed at any later one. Each meeting in an archive is its own session.

**Invariants that must never be broken** (all are one careless commit from dying):

1. **Every rescission in the shipped archive acts on a target adopted earlier and still
   standing.** Break this and crux 1 becomes loud, the agent self-corrects, difficulty collapses.
2. **No `subject` repeats within a single meeting in the shipped archive**, but at least two
   repeat at *later* meetings (one after a loss, one after an adoption). The permissive half of
   crux 2 is demonstrated; only the restrictive half is withheld.
3. **Every shipped rescission is disposed of identically under all four competing readings of the
   threshold**, and every shipped notice comes from the immediately preceding meeting or the call.
4. **The shipped archive contains a *lost* rescission followed by a successful one against the
   same target** (`MO-503` fails → `MO-501` stands → `MO-502` carries). This refutes the
   "one motion per target per meeting" intuition. Added late, and it is what converted a
   near-miss into a valid failure — see §3(g).
5. Machinery that is *not* the crux is pinned loudly in the shipped archive: a motion adopted 4–2
   with three abstentions, a motion tied 3–3, a meeting at exactly quorum, and the two renewals
   above.

A one-line audit script re-derives 1, 2 and 4 from the shipped tree before every push. Do not
trust the generator; read the laid-down files.

---

## 3. Dead ends — every design that failed, with the grader's wording

### (a) RFC 5545 recurrence — `WKST` and invalid-date skipping · `647934e` · pass@2 2/2 solved

Withheld that `WKST` shifts weekly intervals and that RFC 5545 *skips* invalid dates rather than
clamping. Verdict:

> all standard RFC 5545 that the agent implemented correctly using stdlib `zoneinfo`; nothing in
> the current held-out set separates a correct build from a plausible-but-wrong one beyond what a
> competent solver already knows.

### (b) Wall-clock footing across DST · `6914f72` · pass@2 2/2 solved

> Both agents independently reached for `zoneinfo.ZoneInfo` and the same per-occurrence
> localization pattern.

### (c) Per-diem, **two** withheld conventions · `31c1ad1` · pass@2 **PASSED (0/2)**, `deep_review` **FAIL**

The only pre-crux design that ever produced failures — and it was blocked as unfair:

> the data schema actively points the other way: each `days[]` entry carries its own `locality`,
> making `day["locality"]` the obvious referent

> **difficulty_evidence** — The task's entire difficulty is this undisclosed-convention/ambiguity
> artifact, not a genuine reasoning crux… the held-out fails are spec defects, not difficulty
> evidence.

**The lesson that cost the most:** removing the contradicting field fixed fairness *and dissolved
the difficulty* (design d). Fair-and-withheld is a very narrow target; withheld-and-contradicted
is a spec defect.

### (d) Per-diem, **one** withheld convention · `48f3f4c` · pass@2 2/2 solved

Agents applied the full-value part-day meal deduction unprompted.

### (e) RONR thresholds + notice scoping · `82fbc19` · pass@2 2/2 solved

Same domain as the accepted task, difficulty on *recalling* RONR §35's three bases and the notice
window:

> Both agents independently derived all three RONR bases for rescind/amend_previous and the
> immediately-preceding-meeting constraint for previous notice — matching the golden solution —
> without access to solution files. The consistency across two independent agents suggests **the
> RONR rules are well-represented in training data rather than requiring first-principles
> parliamentary research.**

**Five designs, one cause.** (a), (b), (d), (e) all withheld a real published convention. The
model recalls conventions. `task_specification` and `difficulty_crux` were PASS every time — the
tasks were *fair and easy*. Do not spend a cycle on a sixth convention.

### (f) Entangled rules, but only one axis discriminating · `a949911` → `48d8281` · `trials` **2/5**, then pass@2 **0/2**

Crux 1 alone. `trials` verdict:

> Both failing trials implemented a static target-status check instead of a dynamic `in_force`
> set… validated exclusively against the shipped archive… and declared `task_complete` without
> probing further. The three passing trials all built the correct `in_force` state machine, with
> two doing so **through explicit iterative self-correction**.

I then added a held-out archive (`contingent-strikes`) and pass@2 came back **0/2 solved**. The
agent-visible material was **byte-identical** — only held-out fixtures changed.

**The structural fact this proves, and it is the most transferable thing here:**
**held-out fixtures cannot change the failure rate.** They decide only whether a wrong build is
*caught*; a wrong build already failed five archives. The rate is fixed by (i) what the agent
sees and (ii) how many independent things it must get right. Adding coverage of an axis you
already cover is wasted cycles.

### (g) One invisible rule + one *un-refuted* neighbouring reading · `f1e8742` · pass@2 **FAIL with a failing trial**

A trial *did* fail — and the gate still failed, because the failure was graded a near-miss:

> task__Erk4Byi is a clear near-miss: 7/10 tests passed, one wrong rule drove all 3 failures…
> the "no repeat rescission" intuition is a recurring conceptual trap that **a clearer worked
> example in the spec (showing a lost rescission followed by a successful one against the same
> target) might preempt.**

The agent invented "a target may be moved against only once per meeting" — in neither the
instruction nor RONR. `approach_validity` was PASS, so no verifier defect. A failure caused by a
rule the agent invented and the sample never refutes **does not count**.

---

## 4. What actually worked

Two things, in this order.

**(1) Move the difficulty from *knowing* to *noticing*, via pattern H (entangled rules).**
`32-stump-the-model-strategies.md`: "the rules aren't independent — they reach back and change
each other… fixing 'one more rule' never converges: the difficulty is the coupling, not the
count." Decisively, H is **fair by construction** — "every rule and interaction is fully
determined by the data and the spec" — so it needs nothing withheld, which is what dissolved the
disclose-vs-difficulty deadlock that killed designs (a)–(e).

Live example 2 (`accrued-interest`, Opus-4.8 **8/8 fail**, same category) showed the other half:
a recalled convention *can* stump, but only when applying it costs machinery the sample gives no
evidence is needed. Its agents **named the UK ex-dividend rule and dropped it** — *"probably isn't
being tested"*, *"likely beyond the scope"*. Design (e) failed because applying RONR's three bases
costs three cheap conditions on data the sample is full of; there was no scope judgement to get
wrong. Crux 1 costs a state machine over the whole archive, on an archive that never shows it
mattering. The trial transcripts reproduced the pattern exactly:

> *"Our code would check target_status from original MO-201: that status remains 'adopted' because
> we don't update target status after it is rescinded. So we'd incorrectly allow later rescind.
> **Need implement a 'currently in force' state?**"* — then dropped it, "no such case" in the sample.

**(2) Add a *second independent* invisible rule (pattern G under all-or-nothing).** One axis gave
~46% failure against a 60% bar (6 failures in 13 trials, sequence 1/2, 2/2, 1/2, 2/5, 0/2) —
agents that had the one insight passed. Pattern G requires the fixes be *genuinely independent* so
the agent cannot get them all from one realization. Renewal is unrelated to target standing:
finding one does not lead to the other, and with no partial credit either omission fails outright.

**This is what produced 0/5.** Four of five trials failed on renewal, the newest axis:

> All four agents correctly identified the RONR same-session renewal prohibition and built an
> explicit tracking structure for previously-seen subjects within a meeting, but each **implemented
> the guard condition backwards**… instruction.md's data-constraint sentence was parsed as a
> permission rule rather than as a structural invariant about the dataset. The agent's self-tests
> validated against the shipped archive, which contains no same-meeting subject repeat, so the
> inversion went undetected.

The fifth failed on a spurious cross-meeting blocking rule that "adds state contamination that
propagates, making it a non-near-miss failure".

**Note the accident worth reusing:** the data-guarantee sentence *"Within a single meeting a
`subject` appears more than once only after a motion on it was lost"* — added to close an
ambiguity — became the strongest trap in the task, because agents read a structural invariant as a
permission rule. A sentence describing the *shape of the data* is not a sentence describing the
*rule*, and agents conflate the two.

---

## 5. Gate-by-gate log, in the order things broke

| Gate | First verdict | Fix | Commit |
|---|---|---|---|
| `changes`, `cosine_similarity`, `ratelimit`, `similarity` | **pass, every push** | — | — |
| `review` (static) | **pass, every push** — incl. after `instruction.md` edits | — | — |
| `validation` (docker/oracle/nop) | **pass, every push** | — | — |
| `pass2` | fail ×5 (2/2 solved) | five crux redesigns; finally pattern H | `616c291` |
| `deep_review` | FAIL once, on the withheld-convention design | delete the contradicting schema field; stop withholding | `48f3f4c` |
| `ava_review` | pass; one advisory: `{'trips': 2.0} == {'trips': 2}` accepted a float | `isinstance(int) and not isinstance(bool)` guards on every numeric field | `82fbc19` |
| `tier1`, `qc_eval`, `qc_exec` | **pass, first time reached** | — | — |
| `qc_gate` | FAIL — no fixture had `present == quorum` | boundary meetings in 3 archives incl. shipped | `7608454` |
| `qc_gate` | FAIL again — `yes*2 > len(members)` vs `>=`, unreachable with only odd rolls | **enumerate all five comparisons**, add an 8-member body + `threshold-boundaries` | `a949911` |
| `trials` | FAIL 2/5 | second independent axis (renewal) | `f1e8742` |
| `pass2` | FAIL — the one failure graded a near-miss | shipped archive refutes the invented restriction | `da843bc` |
| `gate` | **pass** | — | `da843bc` |

---

## 6. Error → what to do, and what NOT to do

**pass@2 "2/2 solved" on a withheld published convention.**
Do: change the *kind* of difficulty — coupling (H), or a convention whose application costs
machinery the sample never demands (`accrued-interest`).
**Do not** withhold a different convention. Four attempts, four identical verdicts. Do not make
the convention more obscure — that trades difficulty for unfairness and `deep_review` catches it.

**`deep_review` `decisive_answer_discoverable` / `traceable_requirements` FAIL.**
Do: check whether the *schema* contradicts the withheld rule; if so the design is defective, not
under-documented.
**Do not** answer by disclosing the rule — that dissolved the difficulty in one push here, and
`retired-normalizer` §3.2 records three cycles lost the same way.

**`trials` short of 3/5 while `pass2` passes.**
Do: add a **second independent** invisible rule. Verify independence — finding one must not lead
to the other.
**Do not** add held-out fixtures for the axis you already have. Measured here: agent-visible
material byte-identical, pass@2 went 2/2-failing → 0/2-failing. Coverage ≠ rate.

**`qc_gate` "Narrow / Hardcodable Held-Out Coverage".**
Do: enumerate **every comparison** in the reference and assert each has a fixture exactly on its
boundary; audit from the laid-down tree.
**Do not** patch the one boundary QC names. It found one per round for two rounds; enumerating
found a third (`notice_tie`) it had not yet reached.

**A failing trial that does not count (`near_miss` FAIL).**
Do: find the wrong rule the agent invented and **refute it in the shipped archive**. Verify the
refutation breaks the *shipped* archive, not just held-out ones — that is what makes the agent
self-correct instead of failing invalidly.
**Do not** state the real rule in `instruction.md` to "remove ambiguity"; that kills the crux.
**Do not** raise difficulty in response — the concept was mostly right, one spurious gate was wrong.

**General anti-recommendations.** Never shorten `[agent].timeout_sec` to add difficulty (agents
finished in 17–22 min of 60). Never add busywork. Never build the crux from an undocumented
function (`celstage` §2).

---

## 7. Bugs I introduced myself

- **A `.replace()` that silently no-oped.** Patching the renewal rule into the second
  implementation matched nothing, because its branch order is quorate → acts_on → main, not
  quorate → main → acts_on. Caught only because the two implementations then disagreed on exactly
  the three archives I had touched. **Assert every `replace` actually changed the text.**
- **Claims in README that were simply wrong.** "two archives carry a below-quorum meeting" (four
  did); "7, 9, 11 and 13 members" after I had removed the 7-member body from the fixture set.
  Both caught by the programmatic pre-push check, neither by reading.
- **`grep -c` broke a push chain** — exits 1 on zero matches, so `… && git push` never ran. Use
  `PEND=$(… || true)` then an explicit numeric test.
- **`ugrep` rejects `^\│`** in this environment; read rewards from `jobs/*/result.json` instead of
  grepping harbor's table.
- **A regex that swept up the parametrize argument name.** `re.findall(r'"([a-z0-9-]+)",')` over
  the parametrize block returns `fixture` alongside the fixture names; subtract it explicitly.

---

## 8. Process rules learned the hard way

- **Never push while a run is in flight.** Check `gh pr checks 1` for `pending` first; a push
  cancels the run and wastes an hour.
- **`trials` outruns a 60-minute monitor.** Arm it `persistent: true`.
- **QC stickies go stale by construction** — a `pass2` failure skips `qc_*` entirely. Always check
  `<!-- QC-BASE:… -->` against `git rev-parse HEAD` before acting. Here it always matched, but the
  check costs nothing.
- **QC findings arrive base64 in `<!-- QC-FIXES-B64:… -->`**; decode it, the visible comment body
  is empty.
- **`tomllib` is absent on the local Python 3.9** — fall back to `tomli` when validating
  `task.toml`.
- **Add `jobs/` to `.gitignore`** before the first local harbor run, or it lands in the diff.
- Regenerate fixtures *and re-verify from the laid-down tree*; a stale generator produced
  hours of wrong scoring in an earlier task and nearly did again here.

---

## 9. Reusable checklist for the next task

1. Read §3 and §4 of every file in `previous_task_data/` **before** designing.
2. Ask first: is the crux *knowing* something, or *noticing* something? If knowing — stop.
3. Prefer pattern H (entangled rules): fair by construction, nothing withheld.
4. Require **two independent** invisible rules if the bar is pass@5 ≥ 3/5. One is not enough:
   measured at ~46% here.
5. Write the inertness audit **before** the first push, and run it off the laid-down tree.
6. Enumerate every comparison in the reference; give each a fixture exactly on its boundary.
7. Pin non-crux machinery loudly in the shipped archive so it can never be blamed for a failure.
8. For each plausible wrong reading *adjacent* to the crux, refute it in the shipped archive.
9. Two independent implementations, structurally different, agreeing on every archive.
10. Score every mutant end to end through the real verifier, not just the scratchpad model.
11. Verify every README number programmatically against the staged tree before pushing.

---

## 10. One-paragraph version for future me

Six crux designs died before this one was accepted, and five died the same way: the benchmarked
model recalls published conventions — RFC 5545, `zoneinfo`, GSA per-diem, RONR §35 — essentially
perfectly, so "the agent must know convention X" is not difficulty, and the one variant that did
produce failures was blocked as unfair because the schema contradicted the withheld rule.
What worked was pattern H from `32-stump-the-model-strategies.md`: make the rules *entangled* so
that motions rewrite each other's meaning, which needs nothing withheld and is therefore fair by
construction. One entangled rule gave ~46% failure against a 60% bar, and the decisive discovery
was that **held-out fixtures cannot move the failure rate** — proved by a push where the
agent-visible bytes were identical and pass@2 swung 2/2-failing to 0/2-failing. The rate is set by
what the agent sees and by how many *independent* invisible rules it must find, so I added a
second (RONR renewal: a rejected question cannot be moved again in the same session), and pass@5
went to **0/5**, four of five trials inverting the renewal guard. Two smaller lessons paid for
themselves: `qc_gate` will find one uncovered comparison boundary per round forever unless you
enumerate all of them at once, and a failing trial does not count if the agent's wrong rule was
self-invented and your sample never refutes it — put the refutation in the shipped archive, and
check it breaks the *shipped* archive rather than only the held-out ones.
