# dynamo-202f139 — a task that died at pass@2 four times, and the rebuild that was accepted

| | |
|---|---|
| **Outcome** | **ACCEPTED 2026-08-30** at commit `c047280`, as `dynamo/repair-standby-mirror`. **pass@5 = 0/5 solved, avg@5 = 0.000, 3 good valid failures.** Every gate green |
| **Repo** | `dynamo-202f139-debugging-and-repair`, branch `submission`, fork `charan-sr` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-202f139-debugging-and-repair/pull/2 |
| **Category / sub** | Debugging and Repair / Performance Debugging (pre-seeded) |
| **Benchmarked model** | `task.toml` names Opus-4.8 / Terminus-2; stickies call it `Model A` |
| **Two tasks, one PR** | Part One `dynamo/repair-shift-tally` (seven `sh`/`awk` gaps) died at `pass@2` **four times**, last head `4338bde`. Part Two `dynamo/repair-standby-mirror` (rsync) was accepted in **two pushes** |
| **Headline** | The awk task's seven gaps were all *logically forced* consequences of rules its spec stated outright, so a careful reader derived every one. The rebuild moved the difficulty into **a real tool's defaults**, and made **the performance fix itself the thing that hands the decision to the tool**. `pass@2` went 2/2-solved (x4) -> 0/2-solved (x2), `pass@5` 5/5-solved -> **0/5** |

**Read Part Two first if you are picking a new task.** Part One is the failure and is still worth
reading, because it is *why* Part Two looks the way it does — but the transferable rule is in
§11-§16.

---

# PART ONE — `dynamo/repair-shift-tally`, the task that died

Everything in §1-§10 describes the design that was abandoned. It is kept in full because the
null result is the evidence base for Part Two.

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
- **No AI attribution anywhere** in commits, PR body, or task files.
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

---

# PART TWO — `dynamo/repair-standby-mirror`, the rebuild that was accepted

Two pushes, 2026-08-29/30. `pass@2` 0/2 twice, `qc_gate` clean in one round, `pass@5` **0/5,
avg@5 0.000**, accepted at `c047280`.

---

## 11. Path (a) first: probing the old appliance's remaining tools, and why it is dead

Before rebuilding, the cheap option was searched honestly: find a real, silent, non-mainstream
behaviour in the tools the awk task's appliance already carried. **25 probes** were run against
the pinned image (gawk 5.2.1 / coreutils 9.1 / Debian 12, `sh` = dash). Real behaviours were
found, and all of them are useless here:

| behaviour | verified |
|---|---|
| `sort -n` silently reads a leading-`+` number as 0 (`+2` sorts as 0); awk reads it as 2 | yes |
| `sort -V` uses Debian `filevercmp`: `a~1 < a < a.b < a1 < a.1 < b` | yes |
| `sort -h`: `1k` before `1K`; `sort -g` parses `0x10` as 16, orders `nan` first and `inf` last | yes |
| GNU `sort` is unstable by default — the last-resort whole-line compare reorders equal keys | yes |
| `sort -k1,1 -u` deduplicates on the **key**, silently dropping lines differing elsewhere | yes |
| gawk `OFMT`/`CONVFMT` = `%.6g`: `print 12345678.5` gives `1.23457e+07` | yes |
| gawk `printf "%d"` truncates (3.5 to 3) while `%.0f` rounds half-to-even (3.5 to 4) | yes |
| dash's `echo` expands backslash escapes in data; dash's `printf %d` reads `010` as octal 8 | yes |
| `uniq -c` pads its count to a fixed width; `substr` rounds fractional indices; `RS=""` puts newline in `FS` | yes |

**Why none of it works, and this is the transferable part:**

> **A tool's silent behaviour can only be a crux if the correct solution is FORCED TO DELEGATE
> to it.** All four `pass@2` traces on the awk task showed the same shape — buffer the whole
> journal into gawk arrays, decide in `END`, emit. Such a program never invokes `sort -n`,
> `sort -V`, `uniq -c`, `join` or `comm`, so no quirk of those tools can ever fire against it.
> gawk is a general-purpose imperative language: it **delegates nothing**. Every rule gets
> written out explicitly, so nothing can be silently wrong.

This is the missing conjunct in `dynamo_engine_choice_for_performance_debugging`'s filter (1).
"The engine is installed and has silent behaviours" is not enough. Contrast the engines that
have won in this subcategory — SQL (`LOWER()`, integer division, `COUNT(col)`, `SUM` over no
rows), nginx (`gzip_types`, `gzip_proxied`), rsync (`-H`, `-S`, `-c`) — every one is
**declarative or configuration-driven**, so the decision cannot be avoided.

**Do not re-probe the coreutils/awk toolset.** It is settled.

---

## 12. The design rule that produced the accepted task

Two accepted precedents in this exact subcategory (`statement-rollup-repair`,
`repair-edge-compression`) plus `repair-portal-dispatch` next door all share one shape:

> **Grade a real tool's deterministic output, never wall-clock. The crux is the tool's silent
> DEFAULTS. The spec states a universal and never names the case that makes it bite.**

The rebuild adds one thing to that, and it is the part worth stealing:

> **Make the performance fix itself be the delegation.** The shipped `mirror.sh` starts three
> child processes per archived file — 41s against a 12s window. A per-record loop *decides
> everything itself*. The repair that fits the window is one tree-level `rsync`, and that single
> act is exactly what hands five decisions to rsync's defaults. The engine cannot be routed
> around, because routing around it is what misses the window.

Five deciding properties, none named in any agent-visible file (verified by grep):

| | universal the spec states | what one pass does by default |
|---|---|---|
| A | the standby occupies no more than the archive | names sharing one file arrive as separate files |
| B | same | a file written with holes is written back solid |
| C | every file present with the same contents | a record changed under the same length and stamp is skipped |
| D | the standby holds nothing the archive does not | a dropped record stays on the standby |
| E | `scratch` *at the root of the volume* is not archived | an unanchored exclusion also drops a year's own `scratch/` of real records |

Measured before the first push: `-a --delete` fails 9 of 13 volumes; **`-aHAX --delete
--exclude=scratch` — the answer a competent engineer writes reflexively — fails 8 and passes all
three ordinary volumes.**

---

## 13. Engine selection: probe, don't reason

Three candidates were probed in a real Debian image before committing to one. Two probe runs
killed the alternatives in about twenty minutes.

- **rsync — chosen.** `-a` alone: 104,857,600 B transferred, destination **101 MB**, hardlink
  count 9 collapsing to **1**. `-aHS`: 71,303,168 B, destination **5 MB**. A same-size and
  same-mtime content change is **silently skipped**. Five independent silent defaults,
  deterministic observables (byte counts, link partition, allocated blocks, file bytes), no
  timing needed.
- **git packfiles** — viable but thinner: default `core.bigFileThreshold` gives a 696 KB pack,
  delta-disabled 4112 KB. Fewer genuinely independent axes.
- **DuckDB N+1 to single scan** — strongest raw precedent but structurally *the same task* as the
  SQLite sibling already in the dataset. Rejected on similarity risk. **This judgement was
  confirmed**: `similarity` and `cosine_similarity` both passed for rsync.

---

## 14. Two defects the process caught that would otherwise have shipped

**(a) The mutation battery found that two of the five axes were testing nothing.**
`m5_no_hardlinks` and `m6_no_sparse` both scored **reward 1.000** on the first battery run. The
fixture model declared the shared names and the sparse images in *both* the primary and last
night's standby, so rsync found them already present and matching and skipped them — leaving the
correct link topology and hole layout in place **by accident**. Fixed by making both the night's
own work, declared in the primary only, so the run is what has to lay them down.

> `statement-rollup-repair`'s rule, confirmed again: **a mutant that produces an identical answer
> is a coverage hole, not a dead trap.** Without the battery this ships with its two headline
> axes inert.

**(b) `harbor run --agent nop` caught a verifier defect that local calibration could not.**
The first nop run returned `RewardFileNotFoundError` while calibration was clean.
`subprocess.run(..., timeout=)` kills only the direct child. The shipped broken script is a
`while read` loop starting three processes per record, so at the window the loop's subshell and
its `rsync`/`dirname`/`mkdir` grandchildren **survived as orphans** — thirteen runaways at once.
The authoring host has many cores and never showed it; `task.toml` sets **`cpus = 1`**, so under
harbor they starved the verifier itself. Fixed with `Popen(start_new_session=True)` plus
`os.killpg` at the window and again in a `finally`.

> **Local calibration on a many-core host does not reproduce `cpus = 1`.** Reproduce the real
> constraint directly — `docker run --cpus 1 --memory 2048m` — before trusting any timing- or
> process-related result. And never wave `--agent nop` through as "obviously 0.000": it is the
> only check that caught this.

---

## 15. The one `qc_gate` finding, and how to fix a fairness gap without giving the crux away

`qc_gate` blocked the first push on exactly one Major finding (B5, Underdetermined /
Hidden-Knowledge Mapping); 36 of 37 checks passed.

> *MIRROR.md never defines whether a file is 'unchanged' by content or by metadata; the endurance
> clause says 'leave alone any file whose archived copy the standby already holds unchanged', and
> the disclosed sample has 0 files where size+mtime match [but contents differ].*

**The finding was legitimate, not a nitpick.** As written, the clause could be read as
*licensing* the size+mtime quick check — which is precisely the judgement axis C punishes. An
agent could be failed for doing what the spec appeared to allow.

The obvious fix — saying that size and mtime can match while contents differ — **discloses axis C
outright**, which is exactly how this same task's Part One push 6 turned a fairness fix into the
hint that removed its own difficulty. QC also suggested "or examples"; adding a sample file with
that property would have destroyed the sample's inertness, the invariant the whole design rests
on.

**What worked: define the ambiguous term by pointing back at requirements already stated.**

> "A file the standby already holds the way the list above requires — the archive's contents,
> under the archive's permissions, at the archive's modification time — is a file this night did
> not change, and a run must leave it where it is rather than laying it down again."

Contents are explicitly part of the test, so the clause can no longer be read as permission to
trust the surface; it still never says *how* a file could look the same and not be. It matched
the verifier's existing comparison exactly, so no verifier change was needed and the calibration
table came back byte-identical. `qc_gate` passed on the next push.

> **Rule: when a gate calls a term underdetermined, define it by reference to what the spec
> already requires — not by explaining the failure mode. The first is a fairness fix; the second
> is a hint.**

---

## 16. What the graders said, and the numbers

`pass@2` on **both** pushes: **0/2 solved, 2 valid-fail, "Rerun Recommended: NO"**. On the second
push every rubric column passed on both trials.

`pass@5`: **0/5 solved, avg@5 = 0.000, 3 good valid failures.** All five trials failed the same
seven volumes; nine tests passed in every trial, including the timing test and all three ordinary
volumes (v01, v02, v13). All five missed the same three flags — `-H`, `-S`, `-c` — while every
agent got `--delete` and the anchored exclude right.

Measured overshoot on the standby, from the grader's own table:

| volume | archive | agent standby | off by |
|---|---|---|---|
| v03-held | 13.3 MiB | 53.3 MiB | 4x, 10 hardlink groups lost |
| v04-images | 3.8 MiB | 99.3 MiB | **26x** |
| v11-images-carry | 3.7 MiB | 59.3 MiB | 16x |
| v12-full | 8.7 MiB | 86.3 MiB | 10x, plus 8 files with wrong contents |

The grader named the design invariant directly:

> "The proximate cause of all five early-quit completions is the **false-positive acceptance
> signal**: the sample volume was deliberately constructed with none of the five failure
> mechanisms, so run-checks.sh returned all-green for every agent's incomplete script. **No agent
> had any in-band signal that its solution was deficient.**"

That invariant was measured before pushing, not assumed: all seven wrong repairs (`m1` through
`m7`) run the shipped self-check and get "all checks passed".

---

## 17. Reusable checklist (Part Two)

Design:
- [ ] Ask not "does this tool have silent behaviours?" but **"does the correct solution have to
      let this tool decide?"** A general-purpose language delegates nothing.
- [ ] Prefer a design where **the performance fix and the delegation are the same act** — then the
      engine cannot be routed around.
- [ ] Write out the answer you most expect the model to produce (here `rsync -aHAX --delete`) and
      **score it** before pushing. If it passes, there is no task.
- [ ] Check the shortlisted engine against what is already in the dataset; a same-shape rebuild on
      a different engine is a `similarity` risk.
- [ ] State universals; never name the deciding case. Grep the agent-visible files for the
      vocabulary of every mechanism and require zero hits.

Verify:
- [ ] Run a mutant per stated rule. **Any mutant scoring 1.000 is a coverage hole** — check
      whether the fixture lets the right answer survive *by accident*.
- [ ] Require single-mistake mutants to fail **disjoint** sets and to pass every ordinary volume.
- [ ] Measure that the shipped self-check is **green under every wrong repair**; assert it, don't
      assume it.
- [ ] Reproduce the environment's real limits (`--cpus 1`) before trusting timing or process
      behaviour; kill the whole process group, not just the child.
- [ ] Time the verifier against the **broken** program (149s here, against a 300s probe cap).
- [ ] Run reward-hack probes: replicate nothing, empty the target, stand a link in front of the
      source, and share the source's own files via `--link-dest`.

---

## 18. One paragraph

A seven-gap `sh`/`awk` repair task cleared every gate except difficulty and died at `pass@2`
four consecutive times, because all seven of its gaps were logically forced consequences of rules
its own spec stated outright. Twenty-five probes of the appliance's remaining tools found several
real silent behaviours and no usable one, for a reason worth keeping: the solution shape agents
converge on — one buffered `awk` pass — never invokes any of those tools, and awk delegates
nothing. The rebuild kept the category and the gate-hardened verifier skeleton and changed the
engine to rsync, arranging things so that **the performance fix is the delegation**: a per-record
loop that misses a 12-second window by 29 seconds, whose only fix that fits is one tree-level
rsync, which is precisely what hands five decisions to rsync's defaults. The spec states
universals and never names a deciding case; the sample volumes are inert on all five and the
fixture builder refuses to write a set where that stops being true. Two defects were caught before
they could cost a cycle — a mutation battery showing two headline axes were inert because the
fixtures let the right answer survive by accident, and `--agent nop` exposing that orphaned
grandchildren of a killed run starve a single-core verifier. One `qc_gate` finding was fixed by
defining an ambiguous term through requirements already stated rather than by explaining the
failure mode. Accepted at `pass@5` 0/5, avg@5 0.000.
