# Dynamo playbook — `dynamo/decode-contact-export`

**Outcome:** accepted. Every automated gate green, **pass@5 0/5, avg@5 = 0.000, all five good valid failures**.
**Repo:** `handshake-project-dynamo/dynamo-c7f0196-data-processing-and-etl`, PR #1
**Category / Sub-category (pre-seeded):** Data Processing and ETL / Text processing
**Benchmarked model:** Model A (Opus-4.8 via Terminus-2), Daytona, 3000s agent budget
**Final commit:** `6d6bf35`
**Headline:** pass@2 0/2 (twice) → pass@5 **0/5**, every per-trial criterion PASS on every trial

This file lives **outside** any git repo on purpose — the parent folder is not a repository, so it
can never be committed into a task or shipped to an agent. It is written for the *next* task.

**Sections 3 and 5 are the expensive ones.** Five pushes reached acceptance; four of them were
spent on a single piece of anti-cheat plumbing that had nothing to do with the difficulty. If you
read only one thing, read §3.2 — *a static source scan cannot keep an absolute promise*.

**A provenance note.** Dynamo's sticky PR comments **update in place**. By the time the task was
accepted, the `ava_review` and `deep_review` stickies read PASS and their earlier BLOCK text was
gone. Quotes in §3 marked *(contemporaneous)* were recorded in the session handoff at the moment
each block landed; everything in §5 marked *(observed)* was read back off the final PR after
acceptance. Nothing here is reconstructed from intent.

---

## 1. What the task asks

A contact directory is decommissioned. Its nightly exports are **vCard 4.0** (RFC 6350, parameter
values per RFC 6868) and must become JSON Lines.

The agent writes `/app/decode.py`, invoked `python3 /app/decode.py <export.vcf> <out.jsonl>`, one
JSON object per vCard in file order, and also leaves `/app/output/{staff,vendors,alumni,board}.jsonl`.

- **Agent sees:** four exports in `/app/data/samples/` **and the retired server's own conversion of
  each** in `/app/data/expected/`. That second directory is the whole game — see §2.
- **Graded on:** eight held-out exports never shipped in the image.
- **Constraint:** stdlib only, no network. Load-bearing: PyPI has vCard parsers that would bypass
  the entire task.

Output schema per property — exactly four keys: `group` (upper, or `null`), `name` (upper),
`params` (upper-cased name → ordered list of values), `value` (list of components, each a list of
values). Only `N, ADR, ORG, NICKNAME, CATEGORIES, GENDER` split into components/values; everything
else is one component, one value.

---

## 2. The crux, and the invariants that keep it alive

**RFC 6350 places line folds by _octet_ count, so a fold can land inside a multi-octet UTF-8
sequence. Unfolding must run on raw bytes, before any character decoding.**

RFC 6350 §3.2 warns about exactly this — it is the "very simple implementation" the standard calls
out. All four shipped exports are **pure ASCII**, so the case never arises in anything the agent can
see. A naive `open(..., encoding='utf-8')` raises `UnicodeDecodeError` on the held-out data.

Seven further constructs sit alongside it, which is what makes the crux **architectural** rather
than a single fact — and why disclosing any one mechanism for fairness does not collapse it:

| Held-out export | Construct withheld | Discriminated in pass@5? |
|---|---|---|
| `intl` | folds inside multi-octet UTF-8 sequences (3 of them) | **5/5 fail** |
| `combined` | the same (2) plus groups, carets, quoted params, escaped separators | **5/5 fail** |
| `quoting` | quoted parameter values carrying `:` `;` `,` | **5/5 fail** |
| `multiparam` | a parameter name repeated on one property; `\\` and `\N` | **5/5 fail** |
| `caret` | RFC 6868 `^n` `^^` `^'` in parameter values | **5/5 fail** |
| `spacing` | continuation whose *second* whitespace character is data | 2/5 fail |
| `mixedcase` | lower/mixed-case property and parameter names | 1/5 fail |
| `grouping` | group prefixes on property names | **0/5 — never discriminated** |

That last row is a real finding, not a defect: see §9 item 4.

### The disclosure line

The instruction **cites RFC 6350 and RFC 6868 by name** and specifies the output schema
exhaustively — which necessarily discloses the *mechanisms* of groups, parameter lists and
structured values. It **never states the consequence**: the words *fold*, *octet*, *encoding*,
*quoting* and *caret* appear nowhere the agent can read.

> This is `fir-boundary-metrics` §6.3 applied literally: **disclose the raw premise (which standards
> apply), never the consequence.**

`deep_review` confirmed the split was fair rather than merely lucky *(observed)*:

> decisive_answer_discoverable — **PASS**: decisive rules are RFC 6350/6868 behavior, both RFCs
> cited (`instruction.md:1`); both trials `decisive_rule_disclosed: pass`.

### Invariants — one commit away from being broken by accident

1. **No shipped sample may contain a non-ASCII byte.** If one ever does, the crux is gone and the
   task is trivially solvable.
2. No shipped sample may contain a group prefix, a quoted param value, a caret escape, or a
   lower-case name.
3. Held-out fixtures must never be copied into `task/environment/`.
4. `instruction.md` must never gain a sentence naming folding, octets, or encoding.

Verify invariant 1 before every push:

```bash
cd <task>
for f in environment/data/samples/*.vcf environment/data/expected/*.jsonl; do
  LC_ALL=C grep -c '[^ -~\r]' "$f"; done          # every count must be 0
```

And invariant 1's converse — `intl` and `combined` must still raise `UnicodeDecodeError` on a
whole-file `.decode('utf-8')`, while every sample decodes clean.

---

## 3. Dead ends — what failed, with the grader's own wording

### 3.1 A rule stated in `instruction.md` but witnessed by no fixture *(contemporaneous, push 1)*

`deep_review` FAILed on `complete_test_coverage`: the repeated-parameter merge rule was *stated* in
`instruction.md` but exercised by no fixture, so **a last-wins implementation would have passed all
eleven fixtures**. Advisories flagged `\\` and `\N` as likewise unwitnessed.

This is the mirror image of the `freight` lesson. `freight` §3 says *anything written in an
agent-visible spec gets implemented* — so writing a rule down is not enough to make it a trap. This
task learned the other half: writing a rule down and **not** pinning it with a fixture is a
`deep_review` failure. Both must be true — the rule is disclosed **and** a held-out fixture
witnesses it.

Fix: a new held-out `multiparam.vcf` where `TEL;TYPE=work;TYPE=voice;TYPE=text` must yield
`["work","voice","text"]`, with repeats deliberately separated by another parameter so ordering
across the whole parameter section is pinned, plus `\\` and `\N` and an escaped backslash
immediately before a real separator.

### 3.2 THE LESSON: a static AST screen cannot keep an absolute promise

`ava_review` BLOCKed **three consecutive pushes**, every time on `sound_verifier`, every time about
the stdlib-only dependency screen, and **never once about the crux, the fixtures, or the
difficulty**. Each fix invited the next bypass:

| Push | Bypass AVA constructed | Why the source scan missed it |
|---|---|---|
| 1 | `import socket` parked in `/app/netstuff.py`, imported by `decode.py` | screen read `decode.py` only |
| 1 | `_e = eval` | only direct calls matched |
| 3 | `import mypkg.sub`, `subprocess` in `mypkg/sub.py`, empty `__init__.py` | a package was screened through `__init__.py` alone |
| 3 | `import pkg` whose `__init__.py` does `from . import base64`, `subprocess` in `pkg/base64.py` | the relative import resolved against `/app`, found nothing, and `base64` passed as stdlib |
| 3 | `getattr(builtins, "exec")`, `builtins.__dict__["eval"]` *(advisory)* | the name was a string; no `Name`/`Attribute` node carried it |
| 4 | **`os.system("curl …")`** | imports no banned root, so **no source scan can ever see it** |
| 4 | **`__builtins__["__imp" + "ort__"]("soc" + "ket")`** *(advisory)* | the name exists only at run time |

The push-4 block was the one that mattered, and its wording named the real fault *(contemporaneous)*:
the **instruction promised "no network access"**, and `os.system` reaches the network without
importing anything the screen could match.

**Patching the AST screen a fourth time would have failed the same way.** Syntax cannot see
behaviour. The root cause was never the screen — it was an `instruction.md` that made an absolute
promise only a runtime mechanism can keep.

> **Never restore an absolute claim the checks cannot enforce.** That is what AVA blocks on.

### 3.3 The false positives that mattered more than the bypasses

Two separate drafts of the tightened screen **rejected a correct solver**, and both were caught only
because accept-side cases were already in the probes:

1. Per-import resolution failed a decoder split into `/app/vcard/` wired with `from . import core` —
   `core` resolved against `/app`, wasn't found, wasn't stdlib, so it was reported as a third-party
   import. A legitimate submission went **1.000 → 0.000**.
2. The first audit-hook draft blocked `import helper` — a module the submission wrote itself.

**A false rejection burns a real trial and is strictly worse than any bypass.** Always probe the
accept side before shipping any tightening.

### 3.4 A rubric criterion that passed twice, then failed on identical text *(contemporaneous, push 4)*

`review` scored **30/31**, and because gates are a chain, everything downstream — including the
`ava_review` re-check of the new guard — was **skipped**. A whole cycle bought nothing.

The single failure was `difficulty_explanation_quality` (#17), a `task.toml` field untouched for
three pushes and passed on pushes 1 and 3. The rubric requires it to state **data provenance** and
**real-world audience**; it had neither. The grader's own note *(contemporaneous)*:

> a borderline call — a lenient reviewer could pass it

Criterion 11 in the same run *credited* the new design — *"the AST scan is a supplementary anti-cheat
check backed by a runtime audit hook"* — so the guard read correctly to the grader; only the metadata
field failed.

**Do not re-push hoping for a lenient re-roll.** Satisfy the criterion. `metadata.difficulty_explanation`
was rewritten to open with the fixtures being synthetic purpose-built vCard 4.0 (generator folds at
75 octets per RFC 6350, invented contacts, hard because of the standard's subtleties rather than
malformed input) and to name the practitioner (data-migration / integration engineer). `README.md`
took the same two facts in the same commit.

### 3.5 Not tried, because prior art already priced it

Per `freight` §3 and `cron` §3.1–3.3, none of these were attempted: shortening `[agent].timeout_sec`
to manufacture difficulty; adding busywork; adding more held-out *shapes of a rule the samples
already teach*; or shipping a "witnessed example" of the trap. `freight` measured the third as having
no effect and the fourth as being as strong a hint as prose.

---

## 4. What actually worked

**Enforce behaviour, not syntax.** A `sys.addaudithook` guard is installed into the decoder's
interpreter via `PYTHONPATH`, written to a root-owned `0444` file inside a `0755` temp dir, so it is
in place before any submitted code runs and the unprivileged `grader` user cannot replace it. It
refuses any import outside the standard library, any import of the named modules, and the
capabilities themselves (`os.system`, `os.exec*`, `os.fork`, `subprocess.Popen`, `socket.*`). A hook
observes the *attempt*, so **how the name was spelled stops mattering** — which kills the entire
class of bypass in §3.2 at once rather than one at a time.

**The AST screen stays.** A hook only sees code that *runs*; a banned import in a branch no export
takes would go unremarked. The two cover opposite failures. Say exactly that when a reviewer asks
why there are two.

**`instruction.md` was rewritten to promise exactly what is enforced and no more.** Import, network
and subprocess limits hold *however the name is reached* (hook). The `__import__`/`eval`/`exec`/`compile`
restriction is stated against the program's **source**, which is what the AST walk reads. The
instruction and the enforcement are now 1:1.

**Three details that each broke something before they were right:**

1. `dataclasses` → `inspect` → `importlib`. Banning modules globally breaks legitimate stdlib. The
   banned-module rule is attributed to its caller and applies only when *the program* is asking.
2. The frame walk must step over the guard's own frames **and** `<frozen importlib…>`, but **not**
   `<string>` — code inside `exec` is the program.
3. **A module the submission wrote under `/app` is the program, not a third-party package.**

Every bypass was **written as a working submission and measured 1.000 before / 0.000 after.** No
fix was shipped on the strength of reading the code.

---

## 5. Gate-by-gate log, in the order things actually broke

| Push | Commit | Outcome |
|---|---|---|
| 1 | `caaca95` | static 25/25 ✅ · rubric 31/31 ✅ · duplicate UNIQUE ✅ · **pass@2 0/2 both valid** · `deep_review` **FAIL** (§3.1) · `ava_review` **BLOCK** (2 bypasses) |
| 2 | `b340a65` | both fixed; then a 5-hour pipeline-side outage (`startup_failure`, not ours) |
| 3 | `52f95ae` | rubric 31/31 · `deep_review` **PASS** · `pass2` **PASS 0/2** · `ava_review` **BLOCK** — module-resolution holes |
| 4 | `f0cd5c4` | rubric **FAIL 30/31** (§3.4) → everything downstream **skipped**; `ava_review` never ran |
| 5 | `6d6bf35` | **all green, `accepted`** |

### Final state, read off the PR after acceptance *(observed)*

| Gate | Verdict | Note |
|---|---|---|
| `review` (rubric) | pass, 3m39s | 31/31 |
| `deep_review` | pass, 5m57s | "coverage is complete both directions, the Oracle derives everything from the cited RFCs, and both pass@2 trials fail on the intended crux" |
| `ava_review` | **pass**, 9m46s | first pass after three BLOCKs; "I could not construct a viable reward path without a working decoder" |
| `qc_eval` / `qc_exec` / `qc_gate` | **pass** | **first contact** — "44 checks + probes ran clean", zero required fixes |
| `tier1` | pass | first cycle → Tier 2 bypass, no QC sticky to address |
| `pass2` | pass, 25m55s | 0/2, both valid |
| `trials` (pass@5) | **pass**, 30m49s | **0/5 solved · 5 good-valid-fail · avg@5 = 0.000** |
| `adversarial_review` | pass | |
| `similarity` | pass | **shadow mode — cannot block.** Observed verdict: clear |
| `cosine_similarity` | pass | UNIQUE; closest TB2 neighbour `write-compressor` at 0.108 |
| `validation`, `ratelimit`, `gate`, `claude-cost-report` | pass | |
| `pass2_suggestion` | skipping | only fires when pass@2 indicates a problem |

### pass@5 — every criterion PASS on every trial *(observed)*

| Trial | Reward | task_specification | reward_hacking | difficulty_crux | near_miss | refusals | low_timeout | approach_validity |
|---|---|---|---|---|---|---|---|---|
| task__XwjRmQY | 0 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| task__JwE5wwF | 0 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| task__FegaTUp | 0 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| task__BwMGdvu | 0 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |
| task__eGsn8bp | 0 | PASS | PASS | PASS | PASS | PASS | PASS | PASS |

> No criterion produced a single FAIL across five trials.

### What the benchmarked model actually did — four root causes, two of them unpredicted

**A — text-mode file open before byte-level unfolding (all 5 trials).** Every agent used
`open(path, 'r', encoding='utf-8')`. Python decodes before control returns, so a fold inside a
multi-octet sequence raises `UnicodeDecodeError` and there is no output at all. This is the designed
crux, and it landed on every trial.

**B — no double-quote-aware parameter splitting (all 5 trials).** Every agent split parameter values
on raw commas without tracking DQUOTE spans. `SORT-AS="Halvorsen, Ingrid"` decoded as
`['"Halvorsen', ' Ingrid"']` instead of `['Halvorsen, Ingrid']` — one value became two *and* kept the
quote characters.

**C — `^'` mapped to a single quote (3 trials: XwjRmQY, JwE5wwF, BwMGdvu).** RFC 6868 mandates
`^'` → `"` (U+0022). Three agents produced `'` (U+0027). **Not predicted during design.** One trial
also dropped the caret from an unrecognised `^x`, which RFC 6868 requires be preserved verbatim.

**D — `lstrip(' \t')` instead of removing exactly one octet (2 trials: FegaTUp, eGsn8bp).** Stripping
*all* leading whitespace from a continuation collapses data whitespace that follows the fold marker.
**Not predicted during design** — this is what the `spacing` fixture was for, and it is the only
reason that fixture earned its place.

The grader's synthesis *(observed)*:

> All failures are coherent with a single overarching pattern: agents verified exclusively against
> four shipped samples that are pure ASCII with no multi-byte UTF-8 folds, no quoted parameter
> values, and no tricky caret sequences, and then over-generalized.

and, on why the convergence is structural rather than incidental:

> The strong convergence on text-mode file open and non-quote-aware splitting across all five
> independently-seeded trials is consistent with these being the natural default approach a language
> model trained on common Python file-I/O patterns would produce, without careful consulting of
> RFC 6350's byte-level folding and DQUOTE parameter-value sections.

**Nobody ran out of time.** In pass@2 both agents quit voluntarily at ~12 and ~18 minutes of a 50-minute
budget, having diffed against the shipped `expected/` and declared done. `low_timeout: PASS` on all
seven graded trials. This is the shape §9 item 1 is about.

---

## 6. Error → what to do, and what NOT to do

| Symptom | Do | Do NOT |
|---|---|---|
| `ava_review` `sound_verifier` on a **dependency screen** (happened 3×) | Ask first whether a *source* check can keep the promise. If not, enforce behaviour with a `sys.addaudithook` guard and keep the AST screen only for code that never runs. Then make `instruction.md` promise exactly that split. Add the named bypass to the probes **and** the legitimate shape it resembles | ❌ patch the AST screen again — three pushes proved it invites the next bypass · ❌ leave an absolute claim ("no network access") only a hook can keep · ❌ ship a tightening without probing the accept side |
| AVA "verifier accepts something the instruction forbids" | Prefer **aligning the instruction to the lenient verifier**. If tightening, write the exploit first and measure 1.0 → 0.0 | ❌ tighten in a way that could fail a *correct* solver |
| `deep_review` `complete_test_coverage` | Pin every stated rule with a held-out fixture. A rule the spec states and no fixture witnesses is a coverage hole | ❌ delete the rule from the spec instead — that trades a `deep_review` fail for an `approach_validity` fail |
| Rubric `review` FAIL on a `task.toml` metadata field | Read the per-criterion table; it names the criterion and the fix. Satisfy it | ❌ re-push hoping for a lenient re-roll — identical text passed twice before failing (§3.4) |
| Any gate FAIL at all | Assume everything downstream **skipped** and bought nothing. Batch every known fix into the next push | ❌ push a partial fix "to see what happens" |
| pass@2 "too easy" (2/2 solved) | Find what made the crux **salient** — almost always the samples, not the prose | ❌ shorten `timeout_sec` · ❌ add busywork · ❌ add more held-out shapes of a rule the samples already teach (`freight` measured: no effect) |
| pass@2 `approach_validity` FAIL | Disclose the **mechanism** in agent-visible material; withhold only the shapes | ❌ leave the deciding rule out of everything the agent can see |
| `startup_failure` at 0–1s | Pipeline-side. Re-trigger with `gh pr close 1 && gh pr reopen 1`, which re-resolves the reusable workflow's `@main` | ❌ change the task · ❌ raise timeouts |
| Static check names `.dockerignore` | It is **required**, not optional — the build context has a `data/` subdir | ❌ delete it as "unnecessary" |
| Rubric flags the missing `"You have N seconds…"` line | It is **deliberately absent**; the live rubric calls it a TB3 artifact even though the cached docs mandate it. `instruction_concision` passed all five runs without it | ❌ re-add it from the cached docs |

---

## 7. Bugs I introduced myself

1. **Rejected a correct solver, twice** (§3.3). Both were tightenings of the dependency screen that
   looked obviously right and were caught only by accept-side probe cases. This is the most dangerous
   class of self-inflicted bug in this program: it costs a real trial and produces a *valid-looking*
   failure that nothing flags as a task defect.
2. **Left `metadata.difficulty_explanation` alone for three pushes** because it had already passed
   twice. Cost a full cycle (§3.4). Fields that pass are not fields that are correct.
3. **Wrote the guard's banned-module list without attributing imports to their caller.** `dataclasses`
   reaches `importlib` via `inspect`; a global ban broke legitimate stdlib inside the interpreter's
   own startup.
4. **The `grouping` fixture never discriminated** — 0/5 trials failed it. Not harmful, but it was
   built on the assumption that group prefixes were a trap, and they are not: every agent handled
   them. Design effort spent on it was wasted (§9 item 4).

---

## 8. Process rules learned the hard way

- **Never push while a run is in flight** — `concurrency: cancel-in-progress: true` kills it. Check
  `gh pr checks 1 | grep -cE "pending|queued"` is `0`. Careful: `grep -c` exits **non-zero** when the
  count is 0, so do not chain it with `&&`.
- **Gates are a chain.** Any failure skips everything downstream. This is why `qc_*` and `trials` did
  not run until push 5.
- **Batch every fix into one push.** pass@2 is capped around 6 runs/day and each push re-rolls the
  entire pipeline.
- **Sticky comments update in place.** A verdict on the PR may belong to an earlier run — match the
  run's head SHA against your latest commit before reacting, and copy any BLOCK text you will want
  later into a file outside the repo, because it will be overwritten.
- **`similarity` runs in shadow mode and cannot block**; `cosine_similarity` is the one that gates.
- **`tier1` bypasses to Tier 2 on the first cycle** when no QC sticky exists yet.
- **The host `python3` was 3.9.6 — too old.** `sys.stdlib_module_names` is 3.10+, so any tool touching
  the dependency screen or the guard must run on the task's own 3.13 base image.
- `timeout` (GNU coreutils) is **not** on macOS by default — do not use it in helper scripts.
- **`rm -rf task/jobs` after every local `harbor run`** — an untracked `jobs/` trips the
  `no_extraneous_files` static criterion.
- Never `git add -A`; stage explicitly. Never touch `.dynamo/`, `.github/`, `.harbor/`.
- Update the repo-root `README.md` in the **same commit** as any `task/` change, and re-measure
  numbers rather than carrying them forward.
- **No AI/Claude attribution anywhere.** Watch out: `git diff | grep -i "generated by"` legitimately
  matches the phrase "generated by a script" in `task.toml`; that is not attribution.

---

## 9. Reusable checklist for the next task

1. **Ship the agent a self-check oracle that is complete-looking and silent on the trap.** This is
   the engine, and it is what beat a model that self-verifies. `/app/data/expected/` let every agent
   confirm its build at 100% and quit early — at ~12 and ~18 minutes of a 50-minute budget. Absent
   the oracle they would have kept probing; with a *complete* oracle they would have found the trap.
   An incomplete oracle is strictly stronger than either.
2. **Make the trap a property of the DATA, not a rule in the spec.** Every rule here is disclosed.
   The agents implemented the spec correctly and still failed, because the shipped samples contain no
   byte over 0x7F. A spec-level trap gets read and implemented (`freight` §3); a data-level absence
   cannot be read at all.
3. **Disclose the premise, withhold the consequence.** Name the standards; never name what follows
   from them.
4. **Expect a third of your held-out constructs to do no work.** `grouping` discriminated 0/5,
   `mixedcase` 1/5, `spacing` 2/5. Five of eight carried the whole result. Build more constructs than
   you think you need — you cannot tell in advance which ones the model already knows, and `spacing`
   (which looked marginal) caught a root cause nobody predicted.
5. **Two mechanisms beat one.** The single-mechanism version of this crux would have been beaten by
   the three trials that got byte-mode reading conceptually right and still lost on quoting.
6. **Write every exploit as a working submission and measure 1.000 → 0.000.** Never fix from reading.
7. **Probe the accept side in the same file as the reject side.** `guard_probe.py` carries 21 reject
   cases and **15 accept** cases; `audit_probe.py` carries 11 and 7. The accept halves caught two
   would-be trial-burning false rejections.
8. **Run the mutation sweep every time.** One wrong-in-exactly-one-way variant per rule; each must be
   killed by ≥1 held-out and by **no** sample. A mutant a sample kills is a rule the samples teach,
   which means it is not part of the trap.
9. **Never let an `instruction.md` promise exceed what the checks enforce.** This single sentence
   would have saved three of the five pushes.
10. **Verify the crux invariant mechanically before every push**, not by memory.

### The tooling that produced this (preserved, reusable)

`/Users/gundadiprudwiraj/dev/handshake/session/decode-contact-export-tools/`

| Script | Purpose |
|---|---|
| `build_fixtures.py` | generates every `.vcf` and expected `.jsonl`, folding at 75 octets like the retired server. **Edit fixtures here, never by hand.** |
| `naive_decode.py` + `calibrate.py` | the build the benchmarked model actually writes; must pass all samples and fail held-out. Measured 7/8 held-out failures — pass@5 then produced 5–7 of 8, so this predicted the real result closely |
| `mutate.py` | 15 single-rule mutations, 14 killed. The survivor ("group after the last dot") is *provably inert*: RFC 6350 admits no dot in a group or property name, so first-dot and last-dot splits are identical on well-formed input. Do not chase it |
| `indep_decode.py` + `fuzz.py` | a second implementation using a different strategy (sentinel masking vs. flag scanning), cross-checked over 5,000 generated exports: 0 crashes, 0 disagreements |
| `audit_probe.py` | 18 cases against the AST screen (11 reject, 7 accept) |
| `guard_probe.py` | 36 cases against the runtime audit guard (21 reject, 15 accept) |

Both probes need Python 3.13; run them in the task's own base image. `guard_probe.py` keeps its own
copy of the guard source — **re-sync it whenever the guard in `tests/test_outputs.py` changes** (the
probe's copy reads `APP` from `$PROBE_APP_DIR` instead of hard-coding `/app`; that is the only
intended difference).

---

## 10. One paragraph for future me

This task reached **pass@5 0/5, avg@5 = 0.000** with every per-trial criterion PASS on every trial,
and QC's 44 checks clean on first contact — but it took five pushes, and **four of them were spent on
anti-cheat plumbing that had nothing to do with the difficulty**. The design was never faulted by any
gate. The crux worked because the shipped samples are pure ASCII while RFC 6350 folds by octet, so
every agent's `open(..., encoding='utf-8')` crashed on held-out data it had no way to anticipate —
and because the agent's own self-check oracle in `/app/data/expected/` confirmed its wrong build at
100% and sent it home early. The transferable engine is that pairing: **give the model a complete-looking
oracle that is silent on the trap, and put the trap in the data rather than the spec.** The expensive
lesson is separate and structural: `ava_review` blocked three times because `instruction.md` promised
"no network access" while a static AST screen enforced it, and syntax cannot see behaviour —
`os.system("curl …")` imports nothing. A `sys.addaudithook` guard killed that whole class at once.
**Never write a promise the checks cannot keep.** The single most fragile thing in the finished task
is that no shipped sample contains a non-ASCII byte; if that ever breaks, the crux is gone.
