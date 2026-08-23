HANDOFF: dynamo-57f22b3-machine-learning-and-ai (PR #1)
=========================================================
Last updated: after pushing `38e95c0` (2026-08-24). See "Round D" below --
the design is now well-posed and fair, and the open question is no longer
fairness but whether it is HARD ENOUGH. Read Round D before doing anything.

-----------------------------------------------------------------------
STATUS IN ONE SENTENCE: the crux redesign fixed the VALIDITY problem for good
(rubric + deep_review's discoverability concern have not been raised since),
but the redesigned task was then solved 2/2 by pass2, so the shell itself was
rebuilt to grade a script against held-out batches with a concealed
pseudoreplication axis — that rebuild is `8dc1215`, pushed and awaiting gates.
Read "Where this stands now" below before anything else.
-----------------------------------------------------------------------

## Repo / PR pointers

- Local clone: `C:\Users\chara\Downloads\Handshake\dynamo-57f22b3-machine-learning-and-ai`
- Branch: `submission`, currently at commit `38e95c0` (nothing uncommitted)
- PR: https://github.com/handshake-project-dynamo/dynamo-57f22b3-machine-learning-and-ai/pull/1
- Category/subcategory (fixed, do not edit): Machine Learning and AI / NLP and language models
- Model/agent under test: Opus-4.8 / Terminus-2
- `README.md` (repo root) has the full prose history of all designs and every
  gate iteration, including this redesign — read it for anything this handoff
  compresses.

## Round A background: why the crux was redesigned

`deep_review` blocked `c87e4a9` on the **validity of the golden answer**, not
on disclosure wording: *"two competent experts can reasonably disagree on
t-test-via-CLT vs. Wilcoxon for coarse symmetric non-normal paired data, so
the decisive value is not uniquely derivable from agent-visible material."*
No wording fixes a golden answer that is arguably wrong, and that was the
sixth round of the same disclosure-vs-difficulty flip-flop on one crux.
Both of `deep_review`'s own suggested fixes were dead ends (one was the clause
`instruction_concision` had already failed twice; the other deletes the crux).

## Round A: what the crux redesign changed

**Kept, untouched:** the task shell (rebuild a retired significance script),
the JSON I/O format, `task.toml`'s metadata fields, and **comparisons 1–5,
byte-for-byte**. None of these has ever been flagged by any reviewer.

**Replaced:** comparisons 6 and 7, and the disclosure sentence tied to them.

The task now turns on **two independent judgments**, each stated as a fact
about how the retired script was used, neither named as a technique:

1. **Per-comparison test selection** — now with *uncontested* ground truth.
   With the coarse-precision mechanism gone, every comparison's Shapiro-Wilk
   result has exactly one honest reading: genuine outlier → Wilcoxon
   (cmp_01, cmp_05), clean → t-test (everything else).
2. **The batch-level error budget** — "if in truth no candidate in the batch
   differed from the baseline, the script had to have at most a 0.05 chance of
   returning any candidate at all." cmp_02 (a real small effect, unadjusted
   p≈0.026) and cmp_07 (a **true null**, p≈0.034) both read significant
   against a per-comparison 0.05 and neither survives the batch budget.

**cmp_06 couples the two** so neither can be got right in isolation: clean
normal differences where the t-test reaches p≈0.0043 and Wilcoxon only
p≈0.0155 — the test choice is invisible against 0.05 and decisive against
0.05/7 ≈ 0.00714.

The contested "the team's internal notes recorded that a normality check can
fail for more than one underlying reason…" sentence is **deleted**, not
rewritten. The replacement states a *requirement on the answer* rather than
telling the agent what to look for in the data.

**Two playbook findings shaped this** (both worth re-reading before any
further change here):
- `dynamo-83cfbd9` §3.3 — a *memorised* standard technique gets solved on its
  own; "real and external is necessary, not sufficient." Multiple-comparison
  correction is exactly such a technique, so it could not carry the task alone.
- `dynamo-93acae6` and `dynamo-09b4f4b` — what works is **several independent
  required corrections, each stated as a fact about the system, none named as
  a technique**, graded all-or-nothing. "One axis is a coin flip, two axes are
  a task."

## Round A: ground truth is uniquely determined — verified, not asserted

This is the specific property the old design lacked and the whole point of the
redesign. On this batch, **Bonferroni, Šidák, Holm and Holm-Šidák all return
the identical set** of significant comparisons (`cmp_01`, `cmp_03`, `cmp_05`,
`cmp_06`), so no part of the answer depends on which equivalent procedure a
solver picks. Benjamini-Hochberg returns a different set, but it controls the
false discovery rate rather than the batch-level quantity the instruction
states, so it is a genuine methodological error against the stated budget, not
an equivalent reading. All three scipy Wilcoxon variants agree on every
comparison (spread < 0.005).

Golden p-values: cmp_01 0.0 (T), cmp_02 0.0261 (F), cmp_03 0.0 (T),
cmp_04 0.3333 (F), cmp_05 0.0 (T), cmp_06 0.0043 (T), cmp_07 0.0338 (F).

## Round A: local verification done before that push

- `harbor run -p task --agent oracle` = **1.0**; `--agent nop` = **0.0**.
- **Five mutants, each confirmed to score 0.0**: no batch correction
  (per-comparison 0.05); always t-test with the correction kept; always
  Wilcoxon with the correction kept; Benjamini-Hochberg substituted for a
  batch-level procedure; correct booleans with fabricated p-values.
- `solve.py` restored afterwards and the oracle **reconfirmed at 1.0**.
- Golden re-derived by a separate script that read the shipped data, not
  copied from the oracle's output.
- `README.md` synced in the same commit.

## Where this stands now (read this first)

Two rounds have landed since the previous handoff:

**Round A — `7c0c604`** (originally `8dc9d80`; force-pushed only to strip a
`Co-Authored-By: Claude` trailer, content byte-identical). Replaced the
contested ties-vs-outlier crux with two axes: per-comparison test selection
(now uncontested) and a batch-level error budget. **Result: rubric review,
`validation`, `similarity`, `cosine_similarity` all PASS — the validity fix
held and discoverability was never raised again. `pass2` returned 2/2 SOLVED.**
Too easy.

Why, from the traces: both agents opened with **exhaustive enumeration**
("computing Shapiro-Wilk, paired t, Wilcoxon, and sign test for all 7
comparisons") and then "correctly inferred Bonferroni correction from the FWER
constraint". That is `dynamo-83cfbd9` §3.3 for the third time in this PR — a
**memorised** technique gets solved on its own.

Also recorded: both agents used the **sign test** rather than Wilcoxon on the
outlier comparisons and still passed, because both p-values round to 0.0000.
Those comparisons discriminate mean-based from rank-based, not one rank-based
test from another.

**Round B — `8dc1215`** (current). The structural diagnosis: **there was no
held-out data**, so every diagnostic the agent could run, it ran on the graded
data — nothing could be concealed. Every accepted task in this family
(`dynamo-93acae6`, `dynamo-83cfbd9`, `dynamo-09b4f4b`) grades a *script*
against held-out inputs.

New shell: the agent writes `/app/decide.py`, sees one sample batch (input
only, no expected output), graded **all-or-nothing** on that sample plus
**four held-out batches** of 6/7/8/9 comparisons. The two prior axes are kept
as necessary-but-not-sufficient, and a third is added that the sample
**structurally cannot reveal**: the corpus is the independent unit of analysis,
because the documents of one corpus were scored as a block. In the sample every
document is its own corpus, so the collapse is the identity and a solver
ignoring the labels reproduces the sample exactly; in the held-out batches
documents cluster 8x4 and ignoring the labels inflates the effective sample
size fourfold. Textbook pseudoreplication, stated as a premise about data
collection, never as a technique.

**A real hole was found and closed while building this:** `/tests` is mounted
at verify time, which is also when the agent's script runs, so ground truth
would have been readable to a submission that echoed it. The verifier now loads
every golden into memory and removes them from disk before invoking the script.
Confirmed with a mutant that does no statistics and just copies the matching
golden file: scores 0.0.

## Local verification on `8dc1215`

- `harbor oracle` = 1.0, `nop` = 0.0.
- Five wrong strategies each run through the full verifier at 0.0: ignoring
  `corpus` (the concealed axis), per-comparison 0.05, always t-test, always
  Wilcoxon, fabricated p-values. Reference script restored, reconfirmed 1.0.
- The generator asserts per batch: Bonferroni/Sidak/Holm/Holm-Sidak all agree;
  no p-value within 25% of its threshold; the sample is inert under the corpus
  axis to 1e-12; every held-out batch flips on it.

## If this round also comes back solved

Do **not** reach for a fourth statistical axis inside the same shell. The
pattern across three rounds is that this model defeats anything computable on
visible data. What is left untried and has playbook support:
- Make the outlier comparisons discriminate *between rank-based tests* (the
  sign-test near-miss above) so they stop being free.
- Add a second concealed axis in the held-out batches only — e.g. a batch where
  a corpus contributes a single document, or where corpora are unbalanced, so
  a naive equal-weight collapse is wrong.

Deliberately **not** used, and worth knowing why: a "significant degradation is
not an improvement" direction axis was designed and rejected — the outlier
comparisons have a negative mean but positive median, so direction there would
be a mean-vs-median judgment call, the exact class of contestable ground truth
that blocked `c87e4a9`.


## Round C — `1178fc5` (current)

`8dc1215` cleared every upstream gate again and `pass2` returned **2/2 solved**
a second time. The analysis is explicit: both agents did the **corpus-level
aggregation** — one trace names it "pseudoreplication fix" — then applied the
batch correction. One trial hit `AgentTimeoutError` mid-inference but only
after its working script was on disk, so it counted as a pass.

**The lesson, now confirmed three ways:** state a premise clearly enough to be
fair and this model derives the standard consequence from it.
Convention-plus-evidence fell to enumeration; the batch budget fell because
Bonferroni is memorised; pseudoreplication fell because "scored as a block" is
signpost enough. Held-out grading is *necessary* — it is what makes a silent
failure possible at all — but it is **not sufficient** on its own.

Per `dynamo-83cfbd9`, the one axis that survived there was real, external and
**counterintuitive**, where the natural implementation is confidently wrong and
the sample never exercises it. Round C keeps all three existing axes as
necessary-but-not-sufficient and adds a fourth of that kind.

**The new axis.** Once a corpus must be reduced to one figure, that figure is a
*perplexity*, and perplexity is `exp(total NLL / total tokens)` — so pooling
weights each document by the tokens it contributed. `np.mean(ppl)` is what a
solver naturally writes, and it silently reweights the corpus toward its
shortest documents. The held-out batches put the candidate's apparent gains
precisely there (3-4x divergence in effect size) and include the **mirror
case**, where the real gain is in the long documents and the naive mean
*understates* it — so neither direction is a shortcut.

**Concealment is structural:** in the sample every document is the only member
of its corpus, so pooling is the identity and *no pooling rule is
distinguishable from any other*. Token counts still vary across the sample, so
the field looks used without ever being testable.

**A fairness edge was found and closed.** Pooling as a token-weighted
*arithmetic* mean rather than in log space got every boolean right but drifted
past the 0.02 p-value tolerance — on comparisons whose p-values sat near 0.47,
where the drift decides nothing. Rather than rely on that near-miss (this PR was
blocked once already on contestable ground truth), the p-value check is now
**banded**: within 0.02, or both values above 0.15. The discriminating fact is
now purely *whether token counts are used at all*, which is not disputable.
Anti-fabrication is unaffected — a constant is still caught by every significant
comparison and by the near-0.05 lure.

### Local verification on `1178fc5`

- `harbor oracle` = 1.0, `nop` = 0.0.
- **Seven** wrong strategies each 0.0 through the full verifier: arithmetic-mean
  pooling, unweighted geometric pooling, ignoring `corpus`, per-comparison 0.05,
  always t-test, always Wilcoxon, fabricated p-values.
- The legitimate near-equivalent (token-weighted *arithmetic* pooling) confirmed
  still at **1.0** — this is a required check, not an optional one.
- Reference script restored, reconfirmed at 1.0.
- Generator asserts per batch: FWER variants agree; the two pooling means agree;
  no p-value within 25% of its threshold; the sample is inert under all four
  pooling rules grouped and ungrouped to 1e-12; every held-out batch flips on
  BOTH concealed axes.

### If Round C also comes back solved

The evidence would then say this model derives *any* consequence from a stated
premise, however counterintuitive, when the domain is standard statistics. At
that point stop adding statistical axes. Options, roughly in order:
- Make the concealed axis one where the sample actively *misleads* rather than
  merely being inert (the `dynamo-83cfbd9` DST shape), e.g. a sample whose
  corpora are single-document AND whose token counts are constant, so the naive
  reading is positively reinforced.
- Reconsider whether this category/subcategory can stump this model at all
  within the remaining push budget, and say so plainly rather than iterating
  further.


## Round D — `23caadd` then `38e95c0` (current). READ THIS FIRST.

`1178fc5` (the token-pooling axis) was the **high-water mark of this PR**:
`pass2` passed as a genuine failure for the first time, and `ava_review`,
`deep_review`, `tier1`, `qc_eval` and `qc_exec` all cleared. Only `qc_gate`
blocked, on two findings that were **real defects in my instruction wording**,
both fixed in `23caadd`:

- **B5.** The error budget was stated *only over the complete null* ("if in
  truth no candidate differed"). Under the complete null the false discovery
  rate *equals* the chance of any false return, so Benjamini-Hochberg genuinely
  satisfied the sentence as written while diverging from golden. The budget now
  binds whichever candidates do or do not truly differ, so BH no longer
  satisfies it and rejecting it is correct. (BH still diverges on every batch.)
- **B1.** "Verify that your test's assumptions hold" never said to prefer the
  more powerful valid test, so always-Wilcoxon was a defensible reading the
  verifier rejected. The instruction now states two ordered rules: assumptions
  must hold for the data the test is applied to; among valid tests, use the most
  powerful. Neither names a test.

`23caadd` then returned **`pass2` 0/2 — but with TASK FIX SUGGESTED**, and the
analysis was right. Both agents got **every significance boolean correct on all
five batches**, including the four held-out ones. They failed only the p-value
fidelity check, and my own B1 wording had invited both divergences: one agent
used a **sign test** after a symmetry pre-check (symmetry *is* a Wilcoxon
assumption), the other a **precision-weighted t-test** using corpus token totals
(invited by "token counts" + "most powerful valid test").

Measured across all five batches: those legitimate variants spread the
unadjusted p-value by up to **0.42** and flip **zero** decisions. So `38e95c0`
stops grading the p-value against golden. It must still be a finite probability
in [0,1] and agree with the submission's own decision at that batch's threshold.
Anti-fabrication now rests on 34 booleans across five batches, four unseen --
verified by two new self-consistent fabrication mutants that satisfy the p-value
check and still score 0.0.

### Mutation suite as of `38e95c0`

Nine must-fail (all 0.0): arithmetic-mean pooling, unweighted geometric pooling,
ignoring `corpus`, per-comparison 0.05, always t-test, always Wilcoxon, constant
fabricated p-value, and two self-consistent fabrications. Two must-pass (both
1.0): token-weighted *arithmetic* pooling, and the sign-test variant -- the two
the trials actually used. `harbor oracle` = 1.0, `nop` = 0.0.

### THE ACTUAL SITUATION — the honest read

**Four independent mechanisms have now been tried and this model has solved
every one:** convention-plus-evidence (defeated by enumeration), the batch error
budget (Bonferroni is memorised), pseudoreplication ("scored as a block" is
signpost enough), and token-weighted pooling. On the last run both agents
produced a **fully correct decision set on four batches they had never seen**.

The task is now well-posed, fair and thoroughly verified. Every remaining
failure was a verifier artifact, and fixing those removes the only thing that
was failing anyone. **The realistic expectation for the next `trials` run is a
"not hard enough" block, not an acceptance.**

The recurring lesson, now confirmed four ways: *state a premise clearly enough
to be fair and this model derives the standard consequence from it.* Held-out
grading is necessary but not sufficient. Concealment via an inert sample did not
help either, because the agents re-derived the rule from the instruction's
premise rather than from the sample.

**Recommendation if `trials` blocks on difficulty:** do NOT add a fifth
statistical axis -- that has now failed four times in a row and each attempt
costs a full pipeline cycle. Either (a) take the design to a different crux
family within Machine Learning and AI / NLP and language models, accepting that
this is effectively a sixth design, or (b) report a genuine dead end for this
category-model pairing and write the case study. Option (b) is defensible on the
evidence and should be put to the user rather than decided unilaterally.

## Mandatory rules to keep following

- `harbor run -p task --agent oracle` must show reward 1.0 and `--agent nop`
  must show reward < 1.0 before every push (≈20-25s each locally).
- `README.md` (repo root) sync is mandatory on every commit touching
  instruction/solution/verifier/difficulty/gate behavior — diff against it
  before every `git commit`.
- `.dockerignore` already exists at `task/environment/.dockerignore` — no
  action needed unless the build-context directory structure changes.
- `jobs/` (harbor's local run output at repo root) is gitignored — `rm -rf
  jobs/` if it reappears untracked; never commit it.
- Full narrative history lives in the PR's own `README.md` — read it before
  re-deriving anything from `git log`.
- **Per the current standing instruction from the user**: on the NEXT failure,
  do not autonomously commit/push a fix — update this handoff, give a clear
  resume prompt, and stop for input. Only resume autonomous
  commit-and-push iteration if/when the user explicitly says to.

## When the task finishes (accepted, or the user decides on a genuine dead end)

Write a case-study markdown into `C:\Users\chara\Downloads\Handshake\dynamo-task-playbook\`
(see other files there for format), folding in this handoff's content and the
final outcome, then `git add`/`commit`/`git pull --rebase`/`git push` to
`origin main` from inside that folder — delete this handoff file in the same
commit. Also delete the recurring 15-minute PR-check cron job at that point.
