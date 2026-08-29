# dynamo/card-escheat-report — a stored-value card program's quarterly escheatment exposure

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all gates pass, PR labelled `accepted` |
| **Repo** | `handshake-project-dynamo/dynamo-5b35da5-regulated-knowledge-work-and-business-operations` |
| **PR** | #2, final commit `afaf95c` |
| **Category / sub-category** | Regulated Knowledge Work and Business Operations / **Business Operations** |
| **Benchmarked model / agent** | Terminus-2 (pass@2 trials ran DeepSeek-v4-pro; pass@5 "Model A") |
| **Headline** | **pass@5 = 0/5** (every trial a genuine valid failure), avg@5 = 0.000 — the best available outcome |
| **Cost** | 3 pushes, 1 real redesign, same-day turnaround |

The single most important thing in this file is §2. The first design died at `pass@2` for
almost exactly the reason `dynamo-0b74904` (same category) had already proven: a domain
principle stated with concrete per-item examples is a lookup table, not a principle, and
this model transcribes lookup tables perfectly. The fix was not a harder or more obscure
rule — it was a rule whose natural bug is architectural (the obvious data-grouping
choice is wrong), not a missing classification.

---

## 1. What the task asks

A retailer's stored-value ("gift card") program must file a quarterly unclaimed-property
report. The agent is given `/app/data/card_ledger.jsonl` (every posting ever made to
every card number, one JSON object per line), `/app/data/report_date.txt` (the report
cutoff), and `/app/data/card_program_terms.md` (the cardholder agreement — the sole
authority for how postings are classified and what is reportable). It writes
`/app/solve.py`, invoked with no arguments, producing
`/app/output/escheat_report.json`: per-account purchased/promotional balances, the last
qualifying-activity date, a dormancy verdict, and an escheatable amount, plus portfolio
totals. The verifier reruns the agent's own `/app/solve.py` unmodified after swapping
`/app/data/card_ledger.jsonl` and `report_date.txt` for a larger held-out portfolio.

---

## 2. The crux, in its final (accepted) form

**Three governing rules, stated only as principles in `card_program_terms.md`, never as
a per-posting-type table:**

1. **Affirmative-act classification** — only a posting the cardholder makes happen at
   that moment (load, redeem, balance inquiry) restarts the dormancy clock. Anything
   automatic, scheduled, or administrative does not — *even where it moves the
   cardholder's own money or exists only because of an authorization the cardholder
   gave earlier* (`promo_credit`, `auto_replenish`, `refund_to_card`, `reissue`).
2. **Two-balance bookkeeping** — a redemption draws promotional balance before
   purchased; a return restores only purchased balance, capped against the specific
   original purchase it corrects.
3. **Reissue = account continuity, not a new account** — a reissued card's balances,
   history, and dormancy standing all carry forward under the new card number, across
   chains of any length. The natural implementation (group postings by the literal
   `card_id` field, process each group independently) is architecturally wrong the
   moment any card is reissued — not because a rule was missed, but because the whole
   representation is wrong.

The accepted crux that actually decided pass@5 was rule 1 applied to `refund_to_card`
specifically: every one of 5 trials independently classified a processed-return credit
as owner activity, because a return is *initiated* by the cardholder even though it is
*posted* by the merchant's system — the terms doc's principle ("a posting that occurs
automatically… is not the cardholder's own affirmative act, even where it moves the
cardholder's own money") directly forecloses this reading, but every trial made the same
intuitive mistake anyway.

---

## 3. Dead end — design 1, disclosed-as-lookup-table · PR push 1 (`721988c`) · pass@2 2/2 solved

The first `card_program_terms.md` stated the same affirmative-act principle but backed
it with a worked example for *every* posting type: "a purchase load, a redemption at
point of sale, or a request to check the card's balance" (owner) vs. "a promotional
credit our marketing system applies… a scheduled top-up… a credit our system posts
back… when it processes a return" (system) — a 1:1 prose mapping to the six event-type
names. The shipped sample also included a card (`GC-1003`) whose only postings were an
owner `load` and a later system `promo_credit`, with a full `expected_report.json`
self-check shipped alongside — so an agent diffing its own output against the shipped
expected values got **direct field-level confirmation** that `promo_credit` doesn't
reset the clock, for free, before ever touching held-out data.

Both pass@2 trials solved in 5–6.5 minutes, independently converging on
identifier-for-identifier matches to the golden implementation (`AFFIRMATIVE_TYPES`,
the same per-event `uncredited` dict, the same promo-first order). The pass@2 difficulty
suggestion diagnosed it precisely:

> `card_program_terms.md` states every governing rule as a near-procedure… so the agent
> transcribes the terms into code rather than reasoning from a principle. `expected_report.json`
> then lets the agent reverse-engineer and confirm every rule on the shipped sample.

This is the exact same wall `dynamo-0b74904` hit five times in this category before
finding pattern H: **a disclosed rule that is fully procedural once stated has no
residual reasoning depth, however many of them you stack.**

---

## 4. What actually worked — design 2 (`637ce06` + `afaf95c`)

Three changes, in order of how much they mattered:

1. **Reworded the terms doc to state only the abstract principle** — no per-type
   examples, no table. The agent must apply "the cardholder's own affirmative act,
   right then" to seven event-type names on its own.
2. **Rebuilt the sample to be genuinely safe** — removed `GC-1003` entirely; every
   remaining sample card's most recent event is always owner-type, no redemption ever
   exceeds the promotional balance, and `expected_report.json` (kept, since it's needed
   for the agent's own end-to-end self-check) now leaks nothing because every wrong
   reading of every rule produces the *same* output as the correct reading on every
   sample card.
3. **Added reissue-chain account continuity as a third, structurally different rule.**
   This is the one that mattered architecturally: instead of "one more classification
   to get right," it breaks the *obvious* per-card-id grouping design itself. A
   single-hop-only or no-merge implementation doesn't produce a slightly-wrong number —
   it produces a stray extra entry in the output (a superseded card number reported on
   its own) or crashes/loses the account's real history outright. This is the same
   family as `dynamo-0b74904`'s "the natural static-status check is wrong because the
   real answer needs a dynamically-updated representation" — the bug is in the
   *architecture* an agent reaches for first, not in a fact it forgot to look up.

pass@2 on this design: **2/2 failed**, both trials on the identical single axis
(`refund_to_card` misclassified), `difficulty_crux` PASS in both, no ambiguity or
verifier-defect flags. pass@5: **0/5**, all five valid, all the same failure, avg@5 =
0.000.

**Why the reissue axis itself was never what stumped the model, and that's fine.** All
four reissue-chain held-out cases (single-hop, two-hop chain, promo-pooling across a
reissue, a system posting after reissue) passed in every trial — the model correctly
derived and implemented account-continuity merging from the bare principle sentence
every time. What stumped it was the narrower, more intuitive-feeling classification
mistake on `refund_to_card`. This matches the corpus pattern: adding a second,
*architecturally* different axis didn't need to be individually the hardest thing in
the task — its job was to force a genuine from-scratch implementation (no
draft-engine-to-patch, no procedural table to transcribe) so that the remaining,
narrower classification trap had nowhere to hide.

---

## 5. Gate-by-gate log

| Gate | Design 1 (`721988c`) | Design 2 (`637ce06`/`afaf95c`) |
|---|---|---|
| `changes`/static | pass, once `engine.py` renamed to `solve.py` (see §6) | pass |
| `review` (rubric, 31-ish criteria) | PASS both times | PASS |
| `similarity`/`cosine_similarity` | pass (~0.80 fingerprint, below 0.9) | pass (~0.80) |
| `validation` (oracle/nop) | oracle 1.0, nop 0.0 | oracle 1.0, nop 0.0 |
| `pass2` | **BLOCKED — 2/2 solved, no valid fail** | **PASS — 2/2 failed, same axis, valid** |
| `deep_review` | n/a (pass2 blocked first) | PASS — oracle-derivation clean, full requirement↔assertion map, only 4 minor advisories |
| `ava_review` | n/a | PASS — 2 non-blocking advisories (ordering wording overclaim; theoretical `/tests` import bypass, unexploited since decisive expecteds are hard-coded in the trusted test file) |
| `tier1` | n/a | PASS first cycle |
| `qc_eval`/`qc_exec`/`qc_gate` | n/a | **PASS — 37 checks clean**, 3 minor advisories all pointing at the same thing: the oracle crashes (`TypeError`) on a probe-constructed account with zero owner-type events ever (`last_owner_date is None` is asserted unreachable by the "every account has a load" instruction guarantee, but the guard isn't defensive) |
| `trials`/pass@5 | n/a | **0/5, avg@5 = 0.000, all 5 valid** — accepted |

**Held, not pushed, per the "0/5 accepted → stop" rule**: the crash-on-`None` guard, a
precise ordering-wording fix in `instruction.md` (it currently overclaims pure
file-order when the code is actually date-primary with file-order as the same-day
tie-break — harmless today since no fixture exercises the divergence, but imprecise),
and hardening `test_outputs.py` to run the agent's `/app/solve.py` as an unprivileged
user with `/tests` locked down during that specific subprocess call (currently nothing
stops a malicious solve.py from importing the verifier's own `reference_engine.py` at
verify-time re-execution — unexploited only because the decisive held-out expected
values are hard-coded directly in the trusted test file, not derived solely from that
import). All three were fully designed and QC/AVA never escalated them past advisory,
so per policy they were left on record here instead of risking a re-roll.

---

## 6. Errors along the way

- **`solve.sh` referencing `/solution/engine.py` failed the static check** (`expected
  output files are documented in instruction.md`) — the checker flags any `.py`
  filename mentioned in `solution/`+`tests/` files that isn't literally named in
  `instruction.md`. Renaming `solution/engine.py` → `solution/solve.py` (matching the
  one filename that *is* documented, the deliverable itself) cleared it in one push;
  no behavior change, confirmed via oracle=1.0/nop=0.0 unchanged, so no README update
  was needed for that specific push.
- **The reissue-chain merge is fragile to get the direction right.** `replaces_by`
  should map *new → old* semantically, but the resolution walk needs *old → new*
  (`superseded_by[old] = new`, then follow forward from an old id to find its live
  id). A first draft of a standalone mutant-check script had this backwards and
  silently returned "no discrimination" on every reissue fixture until caught by
  checking the resolved key set directly (a `resolve()` that never advances also
  never raises — it just quietly returns the wrong thing).

---

## 7. Reusable checklist for the next task in this category

1. **A principle with worked per-item examples is a table.** If your "principle" sentence
   could be mechanically turned into a lookup table by grep-ing your own text for the
   entities you also grep in the data, it will be transcribed. State the underlying
   rule; make the agent apply it to entity names it has never seen classified anywhere.
2. **Never ship a full self-check `expected_report.json` next to a sample that
   contains even one card whose fields differ under a right vs. wrong reading of the
   crux.** A diff-based self-check is an oracle for anyone who thinks to build the
   wrong-reading variant and compare. Build the sample so *every* plausible wrong
   reading of every withheld rule is output-identical to the correct reading, on every
   field, for every sample record — not just on the field you think matters.
2b. Corollary confirmed here and independently in `dynamo-cb3afdd`-adjacent designs:
   the *dormant boolean* looking safe is not enough if a *sibling field* (here,
   `last_owner_activity_date`) still leaks the discriminator on the visible sample.
3. **Prefer a crux that breaks the obvious architecture over one more classification
   rule.** Adding "rule 7 of 7 to classify correctly" compounds linearly and this model
   handles compounding fine once nothing is hidden. Adding a rule whose natural
   implementation requires *changing the data model itself* (here: grouping by a
   resolved live-account id instead of a literal foreign-key field) is qualitatively
   different — a partial or lazy implementation doesn't produce a slightly-wrong
   number, it produces a structurally wrong shape (extra/missing keys), which is also a
   much stronger verifier assertion to write (`"GC-9100" not in cards` is airtight in a
   way a numeric near-miss never is).
4. **A same-category precedent (`dynamo-0b74904`) predicted this exact failure before
   it happened** — read for the fully-disclosed-procedural-rule wall specifically, not
   just for the accepted design's shape, when a new task in this category is a "repair
   a draft" or "implement a policy doc" shape. This task's own repo's prior closed PR
   (ASC 606 revenue recognition, 49 commits, landed 3/5) is the same wall a third time,
   confirming it's not a one-off: **do not build another "fully-specified accounting
   policy doc" task in this category without an architecturally-different axis from
   the start.**
5. Build the mutant battery through the **real Harbor pipeline**, not just a standalone
   Python simulation — the standalone simulation caught the reissue-direction bug only
   after a manual audit; a docker-run mutant that silently reports "no discrimination"
   is easy to misread as "this fixture doesn't matter" instead of "my mutant is broken."

---

## 8. One-paragraph version for future me

A first design in this category died the standard way — `card_program_terms.md` stated
its two rules with concrete per-posting-type examples, which is a lookup table by
another name, and both pass@2 trials transcribed it identifier-for-identifier in under
seven minutes; the shipped `expected_report.json` self-check made it worse by directly
confirming the withheld rule on one sample card whose date field leaked it even though
its dormancy boolean didn't. The fix wasn't a harder or more obscure classification
rule — this model handles arbitrary compounding of fully-disclosed procedural rules
fine, as this exact repo's prior closed PR (a 49-commit ASC 606 task that also landed
3/5) had already proven. It was adding a rule that breaks the *architecture* an agent
reaches for by default: card reissue as account continuity, where the natural
"group by literal card number" implementation produces a structurally wrong output
(stray or missing keys, lost history) rather than a numerically-close one. Every
reissue-chain held-out case was solved correctly in every trial — that axis was never
the stump — but building the whole engine from scratch around it left the narrower,
more intuitive classification trap (a processed return "feels" cardholder-initiated
even though it's system-posted) with nowhere to hide behind a draft to patch. Result:
pass@5 0/5, all five trials failing on the identical single axis, avg@5 = 0.000,
accepted same day.
