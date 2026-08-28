# dynamo/repair-shift-tally — four consecutive clean pass@2 solves, three genuinely different traps, one dead end

| | |
|---|---|
| **Outcome** | **DEAD END — handed back for human input.** PR left `OPEN`, labels `in-progress,needs-revision`. Not accepted; not abandoned either — see §7 for what a human reviewer should do with it |
| **Repo** | `dynamo-202f139-debugging-and-repair`, branch `submission`, fork `charan-sr` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-202f139-debugging-and-repair/pull/2 |
| **Category / sub** | Debugging and Repair / Performance Debugging (pre-seeded) |
| **Benchmarked model** | `task.toml` names Opus-4.8 / Terminus-2; pass@2 stickies call it `Model A` |
| **Final commit** | `4338bde` |
| **Headline** | Four consecutive `pass@2` runs came back **2/2 solved**, across three structurally different attempts to add difficulty (reworded vocabulary, an explicit disclosed rule, misdirection via a false comment). Two of those pushes also cost a `qc_gate`/`deep_review` near-miss before the difficulty question was even reachable. This is the first case study in this playbook that is **not** a happy ending — it is written to save whoever picks this up from re-trying what's already been tried |

This is the playbook's first non-`ACCEPTED` entry. Everything below is written the way the other
entries are, but the point of this one is different: it exists so the next person (human or
agent) does not spend another 4 pushes rediscovering that this task's difficulty ceiling has
already been found for this task **shape**.

---

## 1. What the task asks

A container terminal's yard concentrators turn one shift's move journal into the tally sheet
the yard office signs off. `/app/tally/tally.sh` is broken two ways: a per-record `cut` loop
that misses the ten-second budget, and sheets that disagree with the office's signed-off
copies. The agent repairs the script in place; `/app/tally/TALLY.md` is normative and states
every rule a sheet obeys — nothing is withheld.

- **Agent sees:** the broken `tally.sh`, `TALLY.md`, three journals (`shift-4471`/`4472`/`4488`),
  signed-off sheets for two of them, and `/app/checks/run-checks.sh` (a self-check over those
  two, which are deliberately inert on every difficulty axis).
- **Graded on:** 13 journals — the shipped journal whose sheet is withheld, plus 12 held-out —
  byte-exact, all-or-nothing, ten-second-per-run budget, 16 pytest functions.
- **Constraint:** `sh`/`awk`/coreutils only (the appliance's real toolset), no other interpreter.

Seven disclosed gaps (A–G) decide a sheet: byte-order sort vs. locale sort (A), numeric
coercion in grouping/dedup (B), tab/blank-delimiting (C), first-arrival dedup (D),
file-order vs. clock-order timestamps (E), a withdrawal that can retroactively cancel a
record already tallied — forcing a read-the-whole-journal architecture (F), and CRLF on the
older firmware (G). All seven are stated explicitly in `TALLY.md`; none fire on the three
shipped journals, which `tools/gen.py` mechanically verifies are inert on all seven before it
will write anything.

---

## 2. Before this session: two designs, one confirmed finding

**Design 1 (5 gaps, A–E).** Passed every gate on the first cycle, including `pass2`, then
failed `trials` at pass@5 = 5/5 solved, avg@5 = 1.000. The trial analysis was unambiguous: all
five agents wrote the identical idiomatic single-`awk`-pass-piped-to-`LC_ALL=C sort` idiom,
which happens to satisfy all five stated rules **simultaneously** — array subscripts are
byte-keyed (kills B), `LC_ALL=C sort` (kills A), `seen[unit SUBSEP seq]` (kills D), awk's
insertion order is file order (kills E). `deep_review` flagged this as an advisory *before*
`trials` spent the slot: *"only the awk numeric-coercion gap actually discriminated."*
**The rule this established, now in memory as
[`dynamo_axes_are_decisions_not_rules`](../dynamo_axes_are_decisions_not_rules.md): count axes
by how many independent implementation decisions they force, not by how many rules they are.**

**Design 2 (7 gaps, A–G).** Added F (withdrawal forces a read-everything-first architecture)
and G (CRLF). F was chosen specifically because it changes *what shape of program can be
correct at all* — a running-totals accumulator can bring a count back down but cannot un-write
a timestamp it already emitted. This design is the one that carried into the PR this session
picked up.

---

## 3. This session's gate-by-gate log

| Push | Commit | What changed | Result |
|---|---|---|---|
| 3 | `6d4fad5` | Disambiguated `void`'s case-sensitivity (rule 2 didn't say "read without regard to letter case" the way rule 4 does for `done`) + hardened `test_script_is_present` against a symlinked *parent* directory (an E5 advisory, not just the leaf) | `qc_gate` had blocked on three findings (B1/B4/B5) that all root-caused to the *same* undisclosed rule — one wording fix resolved all three. Next run: `qc_gate` blocked again, differently (C3) |
| 4 | `50d5ee6` | QC's C3 finding ("narrow / hardcodable held-out coverage"): reproduced QC's exact cited mutant (`m13_void_not_walked`) and built the fixture it was missing — a withdrawal that arrives *before* the record it names (naming nothing walked yet, which rule 2 already allowed), followed later by the genuine record under the same identity. Added to `h10-withdrawals`/`h12-oldfirmware-void` | `qc_gate` passed. Everything downstream ran clean too — `pass2` came back **2/2 solved**, task too easy |
| 5 | `ac87326` | Per §8's "don't add an eighth gap, change the *kind* of difficulty" rule: reworded `TALLY.md` rules 2/3/5/8 from implementation vocabulary ("raw bytes… unsigned value", "the same byte strings") into office-domain language ("match… character for character", an explicit character-rank table). Pure wording change, calibration byte-identical before/after | `pass2` **passed** (33 min, found a real failure) — looked like a win. But `deep_review` **failed**: the fixture from push 4 (void arriving before its target) directly contradicted `TALLY.md`'s own narrative claim that a withdrawal "reaches the concentrator some time after the record it withdraws." One trial read that claim literally and failed fairly, on an unfair spec |
| 6 | `cb7bdb3` | Fixed the contradiction: removed the "always after" claim, grounded early arrival in the *same* unreliable-radio-link mechanism already used to explain re-sends, and made rule 2 state outright that a withdrawal taking back nothing is still a walked record | `pass2` **failed again — 2/2 solved.** The sentence added to explain the fix ("that link can just as easily deliver a withdrawal … before the record it names as after it") was itself a giveaway hint. Confirmed independently by the automated `pass2_suggestion` tool |
| 7 | `f6b1e07` | Deleted that sentence outright, with **no replacement** — rules 2+3 (mechanical, with the explicit "still walked" clause from push 6) are already sufficient. The journal section is now simply silent on arrival order, which isn't a contradiction the way "always after" was | `pass2` **failed again — 2/2 solved**, third consecutive clean solve, this time on a genuinely fair, non-contradictory, non-leaking spec. Both trials implemented all seven gaps, F included, from the mechanical rules alone. **This is the load-bearing result: it disproves the "vocabulary redesign worked" read from push 5** — that one observed failure was the disclosure bug, not genuine difficulty from the reworded language |
| 8 | `4338bde` | Pivoted from Pattern G/explicit-rule tweaks to Pattern C (misdirection): added one comment to the broken, ungraded, unpinned shipped `tally.sh`, directly above the line that drops every non-`done` record, falsely reassuring the reader that a withdrawal needs "nothing further" once it fails that check. Zero calibration cost — touches no graded file | `pass2` **failed again — 2/2 solved**, fourth consecutive clean solve. Trial analysis: both agents' diagnosis phase explicitly flagged "missing withdrawal handling" as a bug, unfazed by the comment — they cross-checked the broken code against `TALLY.md` rather than trusting it |

Between pushes 7 and 8, `pass2_suggestion`'s two daily posts were both spent (quota resets at
UTC midnight); the second post was stale, still describing wording removed two pushes earlier,
and added nothing.

---

## 4. Why "deepen F" — the standing playbook fallback — doesn't apply here

The task's own handoff, and this playbook's general guidance for a `pass@2` clean solve, both
name *"deepen the crux (e.g. chained withdrawals)"* as the fallback when a reworded/composed
gap still gets solved. It was evaluated and rejected on paper, without spending a push:

Both agents that solved this task twice running converged on the same architecture — buffer
the **entire** journal into arrays, then compute `first_seen`/`last_seen` as `min()`/`max()`
over whatever survives filtering, once, at the very end. That shape is **structurally
insensitive** to *how many* withdrawals touch one group's edges or in what order — a group's
`first_seen` under a buffer-everything implementation is just "the earliest surviving
timestamp," regardless of whether one record or five were withdrawn from the front. Chaining
withdrawals adds more values to get right, not a harder *kind* of problem for this shape —
still Pattern G (breadth), not Pattern H (entanglement).

This generalizes the push-1 finding (`dynamo_axes_are_decisions_not_rules`) one level up: with
seven (now effectively more) *individually explicit, mechanically stated* rules, all resolved
by **one shape decision** — buffer-everything vs. streaming — and this model reliably makes
that decision correctly once it reads that a withdrawal can move a timestamp "already written."
No number of additional explicit rules escapes a single dominant shape decision; a genuinely
different *kind* of difficulty has to attack something the buffer-everything shape doesn't
already solve for free.

**A related idea, considered and set aside on the same reasoning:** the task carries a latent,
currently-inert ambiguity — nothing defines what a *second* withdrawal for the same identity
does (currently a no-op, idempotent set-membership, never exercised by any fixture). This could
be formalized as a disclosed "toggle/parity" rule (odd withdrawals strike, even restore) reusing
the existing `void` marker, no interface change. On review this was judged likely to suffer the
same fate as pushes 5–7: it is still *another explicit, mechanically stated rule* for the same
careful-reading agents to transcribe, just with a counter instead of a boolean. Not built.

---

## 5. What was tried instead, and why it still didn't work

Three genuinely different mechanisms were tried across pushes 5, 6–7, and 8 — not three
variations on the same idea:

1. **Reworded vocabulary** (push 5) — remove implementation-vocabulary phrases that map 1:1 to
   a training-data idiom ("raw bytes… unsigned value" → `LC_ALL=C`; "the same byte strings" →
   string-not-numeric comparison). *Result: inconclusive on its own terms* — the one failure
   this produced turned out to be a disclosure bug (§3, push 5→6), not evidence the reworded
   language itself added difficulty. Pushes 6–7 isolated and removed that confound, and the
   clean-spec result (push 7) was a clean solve. **The vocabulary-rewording theory, as tested
   here, did not survive its own confound being removed.**
2. **Explicit disclosed rule, deepened** (considered, not pushed) — toggle/parity on repeated
   withdrawals. Rejected in §4 before spending a push, on the same "buffer-everything defeats
   any explicit rule" reasoning that explains why pushes 5–7 all still solved.
3. **Misdirection** (push 8) — a false comment in the already-known-broken shipped script,
   explicitly endorsed as fair game by the general stump-technique taxonomy ("misleading
   in-code comments that flag the wrong bug"), grounded in `instruction.md` already calling the
   script broken and `TALLY.md` normative. *Result: also solved cleanly* — both agents
   cross-checked the comment against the spec during diagnosis rather than trusting it.

The one pattern from the general taxonomy not attempted is **D — evidence-forced reverse
engineering** (a rule inferable from data but not written down anywhere). It was not attempted
because it requires abandoning this task's foundational premise, stated in `instruction.md`,
`task.toml`'s `difficulty_explanation` ("nothing has to be guessed"), and `README.md` alike:
`TALLY.md` is complete and normative. Making some behavior inferable-but-undisclosed is not a
wording change on top of the existing design — it is a different task, and the two `qc_gate`
near-misses this session already had (pushes 3 and 6, both disclosure/contradiction findings on
*much* smaller changes) argue for not attempting it without deliberate, unhurried design and
explicit sign-off, which is exactly why this was handed back rather than attempted solo.

---

## 6. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| `pass2` returns 2/2 solved on a task built from several individually-disclosed, mechanically-precise rules | Ask what *shape decision* resolves all the rules at once (per `dynamo_axes_are_decisions_not_rules`); check whether a plausible redesign changes that shape or just adds more content under the same shape | Add an eighth (ninth, tenth…) rule of the same character, or reword the existing ones, and expect a different outcome without first identifying the dominant shape decision |
| A fixture is extended to close a `qc_gate` coverage finding | Before pushing, grep the spec's own narrative prose for any claim that fixture might now contradict (arrival order, cardinality, timing) — not just the numbered rules | Assume the numbered rules are the only place a contradiction can hide; the narrative/scene-setting prose is agent-visible too, and QC/`deep_review` read all of it |
| A spec fix needs an explanatory sentence to make a change fair | Ask whether the *mechanical* rule (the numbered list) is already sufficient without the sentence; if so, delete the narrative claim rather than replacing it with an explanation | Add a sentence that *explains why* the fix matters — an explanation of the mechanism is itself a hint, confirmed twice in this session's own history (push 6's own fix, then push 7 fixing push 6) |
| Considering a misdirection trap (false comment, decoy tool, stale doc) | Ground it in something the instruction already discloses (here: the script is already called broken, the spec already called normative) so a correct read of the instruction alone defeats it — it's the professional-skill test, not a gotcha | Expect it to work against an agent that reads the full normative spec before trusting anything in known-broken code; this session's evidence is that a careful agent does exactly that |
| Four consecutive `pass2` clean solves, three different mechanisms tried | Stop and write up what was learned, honestly, including the negative results — a null result across three genuinely different mechanisms is real evidence, not a failure to try hard enough | Keep trying variations on the same three mechanisms hoping for a different roll; `pass@2` is only 2 trials, but four independent 2/2s across three different levers is a pattern, not noise |

---

## 7. What a human reviewer (or the next session) should do with this

- **The task is genuinely solvable and the reference is sound** — every calibration run this
  session was clean, oracle=1.0/nop=0.0 every time, and the real verifier sweep passed
  correctly on both the broken and repaired script every push. Nothing here is a broken task;
  it's a task whose current design doesn't reliably stump this model.
- **If continuing:** the one untried lever is Pattern D (evidence-forced inference) — moving
  some piece of the specification from "stated in `TALLY.md`" to "inferable from the sample
  journal/sheet pair, but not written down." That is a different task, not a patch, and should
  be designed with the same rigor `dynamo-3779991-ledgergraph-canon.md`'s Design 3 used (verify
  the crux against a real, independent source; confirm a competent expert would need to look it
  up, not recall it) rather than attempted as an incremental push.
- **A `held-improvements` branch exists** (commits `570d39a`/`7cfb75f`/`c7042ef` per the prior
  session's handoff), parked, not merged, carrying pure coverage/discrimination additions
  unrelated to the difficulty question above. Still calibration-clean as of when it was parked;
  worth a fresh calibration pass before reusing, not worth merging blind.
- **Do not re-attempt** vocabulary rewording, an explicit deepened withdrawal rule, or
  misdirection via a broken-script comment without a genuinely new angle — all three were tried
  honestly this session and the evidence against them is now four data points deep.

---

## 8. Process rules confirmed

- **`qc_gate` findings that share a root cause get one fix, not three** — pushes 3's B1/B4/B5
  all traced to the same undisclosed case-sensitivity rule; fixing the rule closed all three.
- **A fixture extension must be checked against the spec's own narrative prose, not just its
  numbered rules** — the push-4→5→6 near-miss (void-before-target contradicting "always
  after") is the concrete cost of skipping this once.
- **An explanatory sentence added to fix a fairness gap can itself become the very hint that
  removes the difficulty it was meant to preserve** — confirmed directly, push 6 broke what
  push 7 then had to un-break, no wording change in between except deleting one sentence.
- **Recalibrate (`gen.py`, image rebuild, `calibrate.py`, `harbor oracle`=1.0/`nop`=0.0, the
  real verifier sweep on both accept and reject sides) before every single push**, including
  pure wording changes with zero logic behind them — every push this session ran the full
  ritual regardless of how small the diff looked.
- **`README.md` and `task.toml`'s explanation fields kept in sync every push**, including
  documenting *negative* results (the vocabulary-redesign confound, the rejected toggle/parity
  idea) so a future reader doesn't have to re-derive them from commit messages.
- **Never push while a check is pending; one push per round; batch every fix** — held to across
  all six pushes this session.
- **No AI/Claude attribution anywhere** in commits, PR body, or task files.
- **A repeated null result is itself the deliverable, not a reason to keep iterating alone** —
  after three different mechanisms and four clean solves, the responsible move was to stop and
  hand back with a clear account of what was tried, not to keep spending pushes on variations.

---

## 9. Reusable checklist

Design:
- [ ] Before adding another rule to an already-multi-gap task, identify the **shape decision**
      that currently resolves all of them at once. If a plausible new rule doesn't change that
      shape, it will likely be absorbed the same way.
- [ ] A fixture built to satisfy a `qc_gate` coverage finding must be checked against the
      spec's *narrative* prose (scene-setting sentences), not only its numbered/mechanical
      rules — both are agent-visible and both get read by `deep_review`/QC.
- [ ] When fixing a disclosure gap, ask whether the mechanical rule alone (once corrected) is
      sufficient — prefer deleting a now-false narrative claim over replacing it with an
      explanation of why it's false; the explanation is often itself the hint.
- [ ] A misdirection trap (false comment/tool/doc) needs to be grounded in something the
      instruction already discloses, so a correct reading of the instruction alone defeats it
      — that's what keeps it fair, and also what a careful agent will actually do.

Process:
- [ ] Group `qc_gate`/`deep_review` findings by root cause before fixing — several findings can
      trace to one undisclosed rule.
- [ ] Run the full local ritual before every push, including ones that look logic-neutral.
- [ ] After several consecutive clean-solve results across genuinely different fix attempts
      (not just repeated pushes of the same idea), stop and write up the null result rather
      than continuing to iterate solo — that's a real finding, and the honest move is to hand
      it back with the evidence, not to keep spending push budget alone.

---

## 10. One-paragraph version for future me

Picked up a two-design, seven-gap repair task mid-review with two `qc_gate` findings still
open; closed both (an undisclosed case-sensitivity rule, then a narrow-coverage gap that needed
a withdrawal arriving before its own target) in two clean pushes. That second fixture then
exposed the task's real ceiling: fixing it required disclosing that a withdrawal can arrive
early, and every way of disclosing that fact — narrative prose, an explanatory sentence, even
silence-plus-mechanical-rules — either contradicted the spec (one `deep_review` block) or
turned out sufficient for two agents running to solve cleanly (three consecutive `pass2`
2/2s). A fourth attempt, pivoting from "reword the rules" to "plant a misleading comment in the
already-broken script," also solved cleanly — both agents cross-checked the comment against the
normative spec instead of trusting it. The throughline across all of it: this task's seven gaps
are all individually explicit and mechanically precise, and both agents that solved it
converged on buffering the whole journal before deciding anything — a shape that is provably
insensitive to how many or how deep those explicit rules get, and immune (this session) to
misdirection too. The one lever not tried, moving a rule from disclosed-in-text to
inferable-from-data-only, is a different task, not a patch, and deserved a human decision
rather than a fifth solo push after two near-misses already cost real fairness bugs on much
smaller changes.
