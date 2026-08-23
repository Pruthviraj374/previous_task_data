HANDOFF: dynamo-57f22b3-machine-learning-and-ai (PR #1)
=========================================================
Last updated: after pushing commit `8dc1215` (2026-08-23), the held-out
rebuild that answers `pass2` 2/2 on `7c0c604`. Pipeline run `32625014553`
was in flight at the time of writing.

-----------------------------------------------------------------------
STATUS IN ONE SENTENCE: the previous handoff's recommendation — REDESIGN the
crux rather than push a sixth disclosure-wording tweak — was taken; the
contested "ties vs. outlier" judgment is gone, replaced by two independent
judgments whose ground truth was verified to be uniquely determined, and the
result is pushed and awaiting gates.
-----------------------------------------------------------------------

## Repo / PR pointers

- Local clone: `C:\Users\chara\Downloads\Handshake\dynamo-57f22b3-machine-learning-and-ai`
- Branch: `submission`, currently at commit `8dc1215` (nothing uncommitted)
- PR: https://github.com/handshake-project-dynamo/dynamo-57f22b3-machine-learning-and-ai/pull/1
- Category/subcategory (fixed, do not edit): Machine Learning and AI / NLP and language models
- Model/agent under test: Opus-4.8 / Terminus-2
- `README.md` (repo root) has the full prose history of all designs and every
  gate iteration, including this redesign — read it for anything this handoff
  compresses.

## Why the redesign, in one paragraph

`deep_review` blocked `c87e4a9` on the **validity of the golden answer**, not
on disclosure wording: *"two competent experts can reasonably disagree on
t-test-via-CLT vs. Wilcoxon for coarse symmetric non-normal paired data, so
the decisive value is not uniquely derivable from agent-visible material."*
No wording fixes a golden answer that is arguably wrong, and that was the
sixth round of the same disclosure-vs-difficulty flip-flop on one crux.
Both of `deep_review`'s own suggested fixes were dead ends (one was the clause
`instruction_concision` had already failed twice; the other deletes the crux).

## What `8dc9d80` actually changed

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

## Ground truth is uniquely determined — verified, not asserted

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

## Local verification done before the push

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
