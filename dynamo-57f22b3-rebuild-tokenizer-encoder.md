# dynamo/rebuild-tokenizer-encoder — a named real library beats a stated statistical premise

| | |
|---|---|
| **Outcome** | **ACCEPTED** — `accepted` label, all gates green |
| **Repo** | `dynamo-57f22b3-machine-learning-and-ai`, branch `submission` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-57f22b3-machine-learning-and-ai/pull/1 |
| **Category / sub** | Machine Learning and AI / NLP and language models |
| **Benchmarked model** | `task.toml` names Opus-4.8 / Terminus-2; stickies call it "Model A" |
| **Final commit** | `98d90f1` |
| **Headline** | **This was the SIXTH design on this PR.** Five statistical-hypothesis-testing designs (~32 commits) were each individually defeated. The sixth, a full pivot to a real-library-behavior crux, cleared every gate on its first content push and was **accepted at pass@5 = 0/5, avg@5 = 0.000** (best possible outcome) two pushes later. |

---

## 1. The five designs that failed, and why (compressed — full detail in `git log` on the repo, and in the now-deleted `HANDOFF-dynamo-57f22b3-in-progress.md` if it resurfaces in history)

All five were built around a retired significance-testing script for paired
LM perplexity comparisons: test selection (t-test vs Wilcoxon), a
batch-level FWER budget, corpus-level pseudoreplication, token-weighted
perplexity pooling, and power-dominance between Wilcoxon and the sign test.
Each axis was **stated as a fact about the data/system, never named as a
technique** — the exact register `dynamo-83cfbd9` and `dynamo-93acae6`
established as necessary. It was not sufficient here.

**The recurring lesson, confirmed five independent ways on one PR:**
*state a premise clearly enough to satisfy rubric review's fairness bar, and
this model reliably derives the standard statistical consequence of that
premise.* Convention-plus-evidence fell to exhaustive enumeration. The batch
budget fell because Bonferroni is memorized. Pseudoreplication fell because
"scored as a block" is signpost enough. Token-weighted pooling fell the same
way. Power-dominance (Wilcoxon over the sign test) fell a fifth time, with
both trials producing **fully correct decisions on four held-out batches
they had never seen**, comfortably inside budget — not a near-miss, not a
timeout artifact, a clean solve.

Held-out grading (never shown the graded data) was necessary — it is what
makes a silent failure structurally possible — but it was not sufficient
against this model in this domain. Every one of the five statistical axes
was real, externally motivated, and individually verified un-guessable from
the sample alone; none of that mattered once the premise was stated fairly
enough for a human reviewer to call it fair.

**One genuine confound recurred too, worth separating from the real signal:**
Round G on the old design hit a soft-timeout (`low_timeout` FAIL, 1/2
solved + 1 cut off mid-revision). Raising `[agent].timeout_sec` 1800→3600
did **not** reveal hidden difficulty — it revealed the task was too easy
(the next run: 2/2 solved cleanly). On this PR specifically, removing a
timeout confound has, so far, always pointed the same direction: don't
assume a soft-timeout is masking real difficulty just because it looks like
one.

## 2. The pivot: what actually worked

Following two already-accepted precedents in this exact category
(`dynamo-658c4fa`, PMML rulepack scoring; `dynamo-ca30fed`, LoRA adapter
merging), the sixth design abandoned the "stated statistical premise" shell
entirely and moved to: **name a real, external, public library outright as
the authority, disclose the container format exhaustively, and put the
difficulty in several independently real, documented behaviors of that
library that a naive reimplementation gets wrong** — verified by actually
running the library at authoring time, never by reasoning about a stated
premise.

**Task:** rebuild a tokenizer-encoding script (`/app/encode.py`) from
archived Hugging Face `tokenizers` library configs (`tokenizer.json`).
instruction.md names the library and file format as the authority for
correct output and states nothing else — no field's semantics are
restated. The submitted script must be stdlib-only (no `tokenizers`,
`transformers`, `sentencepiece`, `tiktoken`, no network, no subprocess),
enforced by a `sys.addaudithook` launcher (`tests/run_agent.py`), verified
directly against a probe script rather than assumed from the image's
contents.

**Why this removes the disclosure-vs-difficulty tension that killed all
five statistical designs:** there is no judgment call to calibrate wording
around. Correctness is simply "does this match what the named, real library
actually produces" — an empirical fact, not a defensible-vs-indefensible
statistical reading. `deep_review`/`qc_gate`'s repeated "two competent
experts could disagree" objection has no foothold when the answer is
whatever `Tokenizer.from_file(path).encode(line).ids` returns.

**The shipped sample is a genuinely ordinary config, not a contrived one:**
a plain byte-level BPE `tokenizer.json` with no normalizer, no
post-processor, every optional model field at a default that changes
nothing observable — exactly what a real GPT-2-era model export looks like.
Seven held-out configs, never shown, each exercise one real, documented
library mechanism the standard "byte-level BPE recipe" silently gets wrong:
model type (WordPiece vs BPE — a different algorithm, not a variant),
`ignore_merges`, `fuse_unk`, `byte_fallback`, `continuing_subword_prefix`/
`end_of_word_suffix`, `add_prefix_space`, and `TemplateProcessing` (combined
with a normalizer sequence, so it requires two mechanisms at once).

**Every axis was verified against the real library (`tokenizers==0.23.1`)
before any task code was written**, not reasoned about from documentation —
including one axis (`continuing_subword_prefix`/`end_of_word_suffix`) that
panicked on a hand-built vocab and had to be regenerated via the library's
own `BpeTrainer` instead, which then made the on-disk merge/vocab
representation legible enough to reverse-engineer the true position-based
decoration rule directly from the JSON the library itself produced, rather
than guessing at Rust internals.

## 3. Verification built before the first push

- A pure-Python reference (`solution/encode.py`) reproduces all 8 configs'
  real-library output exactly (23 lines, byte-for-byte) — cross-checked
  against golden files that were themselves produced by calling the real
  library directly, never by running the reference and trusting its own
  output.
- A naive implementation covering only standard byte-level BPE (no handling
  of any of the seven mechanisms) was run through the full local check:
  reproduces the sample exactly (3/3) and fails all seven held-out configs.
- `harbor oracle` = 1.0, `nop` = 0.0, reconfirmed after the later
  timeout-only config change.
- The audit-hook sandbox was verified from both sides: a probe script
  importing the always-available stdlib `socket` module (deliberately
  blocklisted, to test the mechanism itself rather than relying on a
  third-party library happening to be absent from the image) is blocked; a
  correct stdlib-only submission is unaffected.

## 4. Gate-by-gate log

### Push 1 (`d3832e5`) — everything green except pass2

`changes`, rubric `review`, `similarity`, `cosine_similarity`, `validation`
all passed **clean on the first push of a brand-new design**. `pass2`
blocked 0/2, but as a soft-timeout, not a design defect: both trials built a
sound, correctly-structured stdlib-only reimplementation (both
independently ran differential testing against the real library during
their own development, confirming that internet access does not trivially
solve the task even though it's allowed) and were still actively debugging
**exactly the intended traps** (`byte_fallback`'s `<0xXX>` vocab-key format;
`TemplateProcessing`'s id-vs-string-name lookup) when the 3600s wall hit.
`approach_validity` and `difficulty_crux` PASS for both trials; the reviewer
found no evidence of a spec or verifier defect and explicitly recommended
raising the timeout to 5400–7200s.

Per this PR's own standing instruction (accumulated after the first five
designs), this result was checked against the failure pattern before any
fix was proposed: it is *not* a repeat of the old "model derives the
standard consequence once a premise is stated fairly" pattern — it's
agents hitting genuine, single-line implementation bugs and running out of
clock, structurally different from every prior failure on this PR. The one
open question flagged honestly at the time: Round G on the *old* design had
this identical soft-timeout shape, and raising the timeout there revealed
the task was too easy, not genuinely hard — so this fix was presented as
the right next step to get a clean read, not oversold as a guaranteed
solution.

**Fix (`98d90f1`):** `[agent].timeout_sec` 3600 → 7200, a pure config
change. `harbor oracle`/`nop` reconfirmed unaffected (1.0/0.0).

### Push 2 (`98d90f1`) — accepted

`pass2` returned **1/2 valid-fail** (proceeding to pass@5) rather than
another soft-timeout — the extra budget resolved the ambiguity. `ava_review`
found "no blocking gap-rubric failures... the intended crux (`byte_fallback`
`<0xNN>` reserved-token lookup) is confirmed genuine by both pass@2 trials,"
while flagging (advisory, not blocking) that one pass@2 trial was a
single-token near-miss cut off by what looked like a harness override
against a 3600s sub-budget inside the 7200s ceiling — worth watching, not
acting on unilaterally. `tier1`/QC cleared with zero required fixes
(`QC-FIXES-B64: W10=`, i.e. an empty fix list).

`trials` (pass@5): **0/5 solved, avg@5 = 0.000, 4 good valid fails, 1
in-progress-timeout** — the best possible outcome. `approach_validity`,
`difficulty_crux`, `reward_hacking`, `task_specification` all PASS across
every trial. Failures **stratified into two independent root causes**,
confirming the held-out design rather than one dominant mechanism:

- **`byte_fallback` misimplementation (4/5 trials).** One agent explicitly
  gave up on it and submitted anyway ("we don't implement byte_fallback").
  Others looked the raw Unicode character up in the BPE vocab (crashing
  with `KeyError`), or returned `unk_id` instead of the byte-specific
  reserved token, or were one token short at a word boundary.
- **`TemplateProcessing` special-token id resolution (2/5 trials).** Both
  tried to use the SpecialToken's string `id` field directly instead of
  resolving it through the post-processor's own `special_tokens` map — one
  crashed on `int("<s>")`, one emitted a mixed string/int array.

No trial shared both root causes fully; the pattern is exactly what
"several independent required corrections" is supposed to produce, and the
reviewer stated explicitly there was no evidence of a task/verifier defect.

## 5. Reusable checklist

- [ ] If a statistical/algorithmic-premise design keeps getting solved once
      disclosure satisfies fairness review, stop re-wording the same crux.
      Check whether a **real, named, external library or spec** could carry
      the same category instead — correctness becomes an empirical fact
      ("does this match the real tool"), not a judgment call, which removes
      the entire disclosure-vs-difficulty axis of failure.
- [ ] Verify every candidate axis against the **real library**, hands-on,
      before writing any task code — not from memory of its documentation.
      A hand-built fixture that panics is a signal to construct it the way
      the library itself would (e.g. via its own trainer), which also
      teaches you the true on-disk representation directly.
- [ ] Ship a self-check sample that is *genuinely ordinary* for the domain
      (here: a real GPT-2-era config), not visibly contrived — it should
      look like something that would exist regardless of the task.
- [ ] When the submitted artifact must not shortcut through the very
      library it's reimplementing, and internet/pip-install is otherwise
      allowed, enforce the constraint at runtime (audit hook blocking
      import/network/subprocess) and **verify the block itself** with a
      probe importing something always-available (e.g. stdlib `socket`),
      not just confirm the target library happens to be absent from the
      image.
- [ ] On a `pass2` soft-timeout, don't assume more time will reveal hidden
      difficulty — check whether removing an earlier timeout confound on
      the *same* PR ever did. If it previously revealed "too easy," say so
      plainly when recommending the fix rather than presenting it as a sure
      thing.
- [ ] A stratified pass@5 failure (multiple trials failing on *different*
      independent mechanisms, not all on the same one) is itself evidence
      the multi-axis design is working as intended — call this out
      explicitly when reading the trial analysis.

## 6. One-paragraph version

Five designs built around a retired significance-testing script were each
individually defeated across ~32 commits by the same mechanism: state a
statistical premise clearly enough to satisfy fairness review, and this
model reliably derives the standard consequence, no matter how many
independent axes get stacked onto it or how well the sample conceals them.
The fix was not a sixth statistical axis but a different crux *family*
entirely — name a real, external, public library (Hugging Face
`tokenizers`) outright as the authority, disclose the file format
exhaustively, and put the difficulty in seven independently real, documented
library behaviors (WordPiece vs BPE, `ignore_merges`, `fuse_unk`,
`byte_fallback`, position-dependent subword decoration, `add_prefix_space`,
`TemplateProcessing`) that a naive "standard recipe" implementation gets
silently wrong on configs the shipped, genuinely-ordinary sample never
exercises. Because correctness is simply "does this match the real
library's output," there was no disclosure-vs-difficulty judgment call left
for any reviewer to contest — the design cleared every gate on its first
content push except a soft-timeout, and reached the best possible outcome
(pass@5 0/5, avg@5 = 0.000, stratified across two independent root causes)
two pushes later, once the timeout was raised from 3600s to 7200s.
