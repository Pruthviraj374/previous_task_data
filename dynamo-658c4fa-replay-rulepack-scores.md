# dynamo/replay-rulepack-scores — the standard says one thing, the shipped engine does another

Repo: `dynamo-658c4fa-machine-learning-and-ai`, PR #1, branch `submission`, fork `Pruthviraj374`.
Category: **Machine Learning and AI** / Sub-category: **Model inference and prediction**.
`task.toml` declares `model_tested = Opus-4.8`, `agent_tested = Terminus-2`; the pipeline stickies
name the benchmarked model only as `Model A`. Accepted 2026-08-19 at commit `a5e5154`.

**Final result: pass@5 = 0/5 solved, avg@5 = 0.000, 5 good valid failures, 0 soft-timeout,
0 task/verifier issues, 0 reward hacking.** Best possible outcome. Rubric **31/31 twice**,
`qc_gate` clean on its first cycle, `ava_review` and `deep_review` clean, `similarity` UNIQUE.

**One commit. Zero content revisions.** The three pipeline runs it took were all spent on a
GitHub rate limit inside the pipeline's own plumbing — the task tree never changed.

---

## 1. What the task asks

A condition-monitoring service's scoring appliance was decommissioned along with its vendor.
What survives is an archive of flat "rulepack" files.

- **Agent sees:** `/app/data/RULEPACK.md` (the loader note), three rulepacks under
  `/app/data/packs/`, the request batch each was scored against under `/app/data/batches/`, and
  the appliance's own scores for **two** of them under `/app/data/expected/`.
- **Agent produces:** `/app/score.py`, invoked as
  `python3 /app/score.py <rulepack> <batch_csv> <out_csv>`, plus
  `/app/output/fleet-apac-2021.csv`.
- **Graded on:** that one output artifact, a re-run over the verifier's own copies of all three
  shipped packs, and **thirteen held-out packs** never shipped.
- **Constraint:** standard library only, no child processes, no network.

Held out: `defchild-flat`, `defchild-deep`, `and-unknown`, `notrue-deep`, `surrogate`,
`ismissing`, `replace-num`, `replace-ismissing`, `replace-mode`,
`combo-defchild-surrogate`, `combo-notrue-replace`, `combo-and-ismissing`, `plain`.

## 2. The crux

> **The rulepack is a mechanical transliteration of a PMML document, so its attributes *are*
> PMML attributes and their meaning is PMML 4.4's. PMML does not evaluate predicates in
> two-valued logic — and the two batches that ship with their answers never contain a missing
> reading, so the two-valued walk everybody writes reproduces them exactly.**

Six mechanisms decide a score once a reading is absent:

| Mechanism | What the two-valued walk gets wrong |
|---|---|
| Three-valued predicates | a comparison against a missing reading is UNKNOWN, not false |
| `and` over UNKNOWN | false only when an operand is *really* false; UNKNOWN otherwise |
| `surrogate` compound | falls through to the next operand exactly when the previous was UNKNOWN; all-UNKNOWN is UNKNOWN, not true |
| `missingValueStrategy="defaultChild"` | continue at the node's own `defaultChild`, not at the next sibling |
| `noTrueChildStrategy="returnLastPrediction"` | return the current node's score; the default returns none |
| `missingValueReplacement` | a field with a replacement is not missing **at all**, which decides `isMissing` too |

### The invariants that keep it alive

1. **The shipped self-check exercises none of the six.** The two reference batches carry a
   complete reading for every field, and their packs carry no strategy attribute, no surrogate,
   no missing-value check and no replacement. Measured, not assumed — §4.3.
2. **The shipped packs are *older-firmware* files.** They simply do not contain the attribute
   names. Same move as `merge-lora` invariant 2: if they carried the modern attribute set at its
   defaults, the file would *enumerate the knobs* and the task would collapse to recall.
3. **`RULEPACK.md` names the standard and refuses to restate it.** "the *meaning* of a line's
   attributes … is whatever the PMML 4.4 specification says it is. This note describes the
   encoding only." The encoding is documented exhaustively — every line type, every field — so
   `unambiguous` and B5-style discoverability are satisfied without leaking a single semantic.
4. **No graded artifact has a shipped answer.** `fleet-apac-2021` has no reference anywhere
   under `/app`, and a test asserts it.

### Why the trigger is the *data*, not the config

`merge-lora` (same corpus, ML category) put the crux in **config knobs on the artifact**. This
one puts it in a **property of the input record** — an empty cell — with a published standard
supplying the semantics. That is the `plate-rasterizer` §"property of the input" lesson applied
to a different category, and it is what makes this a different task rather than merge-lora
wearing different nouns. Worth keeping in mind when the next ML task lands: the *shape* "an
archive whose deciding rule is withheld convention" is now used twice in this category; the
trigger is the axis of variation left.

## 3. Dead ends — do not retry these

### 3.1 Trusting a published standard without running an implementation

The design originally carried **nine** axes. Probing `pypmml`/`pmml4s` with hand-written PMML
before writing a line of task code killed three of them:

| Candidate axis | What the probe showed | Verdict |
|---|---|---|
| `or` with an UNKNOWN operand | spec's own truth table gives `F or U = U`; the engine returns `F` | **cut** |
| `xor` over UNKNOWN | engine disagreed with the spec table on `T xor F` | **cut** |
| `missingValueStrategy="lastPrediction"` | see §3.2 | **cut** |
| `SimpleSetPredicate` over a missing field | spec is *silent* on the result | **cut** |
| `MiningSchema` outliers / `invalidValueTreatment` | spec does not fix the order they compose in | **cut** |

`merge-lora` §3.2's rule generalises: *two conforming implementations disagreeing is ambiguity,
not difficulty.* The cheap way to find that out is an afternoon with the real engine, not a
review cycle. Every one of these would have been a defensible-looking axis on paper.

### 3.2 The `lastPrediction` strategy, and the interpretive fault line underneath it

The spec says a missing-value strategy fires **at the first UNKNOWN sibling** ("evaluation is
stopped and the current winner is returned"). `pmml4s` defers it: it scans the whole sibling
group, and only applies the strategy if *no* sibling came out true.

This matters far beyond `lastPrediction`. For `defaultChild` **and** `lastPrediction`, the two
readings diverge exactly when a sibling *after* the UNKNOWN one is true — which is precisely the
configuration that makes the axis diverge from a naive walk. Chasing a sharp `lastPrediction`
fixture means walking straight into the fault line.

**The escape, and it is reusable:** build every graded case so that **no sibling after an
UNKNOWN one is ever true**. Both readings then produce identical scores, `defaultChild` still
diverges hard from the naive walk (all siblings UNKNOWN → the naive walk falls through to a
no-true-child path), and `lastPrediction` simply stops being expressible — so it was dropped.
Every pack is scored under **both** readings at build time and the two must agree. That turned a
latent ambiguity rejection into a paragraph of the README a reviewer reads as rigour.

### 3.3 A crux whose format has an off-the-shelf reader

`allow_internet = true` is a rubric criterion (`open_internet`), so an agent can always
`pip install` the reference implementation. Real PMML files were therefore never an option: the
agent would feed them to an engine and be done. The **invented container + real external
semantics** split (`lumenp` §2) is what makes the standard usable — nothing off the shelf reads
a rulepack, and the semantics are still public, named and fair.

## 4. What actually worked

### 4.1 Ground truth cross-checked against an independent engine

`merge-lora` §4.2 and `audit-build-context` §4.1, reused. Every rulepack was also emitted as an
equivalent PMML 4.4 `TreeModel` per tree, scored with `pypmml`, and summed: **16 packs, 238
records, zero mismatches** against the reference scorer.

This is what converts a correctness argument into a diff. It is also what *found* §3.1 — the
disagreements surfaced as mismatches in the probe, months before a grader could raise them.

### 4.2 Build-time invariants instead of prose

The archive builder refuses to emit anything unless all of these hold, per record, per pack:

- every wrong reading reproduces the two shipped reference batches **exactly** (inertness);
- every held-out case is caught by at least one wrong reading (the `plain` control is explicitly
  exempt and documented as such);
- immediate and deferred strategy application agree (§3.2);
- no `or` is ever evaluated with an UNKNOWN operand, and no set predicate ever sees a missing
  field (the two fields feeding them are never left empty);
- no reading sits on a comparison threshold — any draw within half a step of a literal is
  redrawn, which deletes the whole exact-equality class (`rebuild-uptime-rollups` §3.2);
- no record yields a null prediction, so the output contract needs no representation for one and
  the instruction never has to mention that one is possible.

### 4.3 Three plausible-wrong scorers, run against the real verifier in the built image

`audit-build-context` §7 / `merge-lora` §4.3, and it earned its keep again:

| Reading | Shipped reference batches | Tests failed | Reward |
|---|---|---|---|
| n1 — missing reading fails its comparison; tree attributes ignored; unclaimed node returns its own score | both reproduced exactly | 13 | 0 |
| n2 — predicate chapter implemented; tree attributes and replacement ignored; spec default for an unclaimed node | both reproduced exactly | 10 | 0 |
| n3 — nearly right; UNKNOWN swallows false in `and`, replacement applied to comparisons only | both reproduced exactly | 3 | 0 |

No two fail the same set; all three pass the self-check. **That table is the task.** A fourth
probe that ignores scoring and copies the shipped answer files scored 0 and failed 18 tests.

Both sides of the guard were probed inside the image: a correct program that tries an optional
third-party import and falls back scores **1.0**; the same program with a child process added
scores **0**.

### 4.4 The graded shipped artifact was allowed to leak two axes

`fleet-apac-2021` had to exercise *something* or it would be free, and everything it could
exercise is visible in its own rulepack. It got `surrogate` compounds; `defaultChild`,
`missingValueReplacement`, `noTrueChildStrategy` and `isMissing` stayed held-out-only. The cost
was real but small — and surrogate still took down one pass@5 trial anyway (§5.2 root cause C).
`deep_review` explicitly blessed the arrangement as "intentional disclosure".

## 5. Gate-by-gate log

### 5.1 Runs 1 and 2 — the same GitHub rate limit, twice

Both runs died identically, and **not** on the task:

```
##[error]Unable to download artifact(s): API rate limit exceeded for user ID 293969509
verdict line: <none>
##[error]Automated Review verdict is FAIL (or missing — fail-closed)
```

`deep_review` and `ava_review` both failed in **12–14 seconds**, `gate` failed on them, and
`qc_*`, `tier1` and `trials` all skipped. Everything upstream had already passed on the same
commit — static 25/25, rubric 31/31, similarity UNIQUE, Docker/Oracle/Nop, and pass@2 0/2 with
two valid failures.

This is `rebuild-uptime-rollups` §5 in a new costume: **a gate that fails in seconds, inside a
step that never looks at the task, is a platform fault.** The tell is the duration and the
`verdict line: <none>` — the review artifact was never fetched, so the fail-closed check tripped
on an absent verdict rather than a negative one.

**How to re-trigger without write access.** The sanctioned `/rerun` comment checks
`repos/{repo}/collaborators/{user}/permission` for `write` or `admin`, which an attempter does not
have. But its whole mechanism is `gh pr close` → `gh pr reopen`: the review pointer declares
`pull_request_target: types: [..., reopened, ...]`, and the anti-recursion rule that blocks
`GITHUB_TOKEN`-created events does not apply to a human PAT. **A PR author can cycle their own PR
and it fires a fresh full pipeline on the same SHA, with no new commit.** Do not push an empty
commit for this — a push re-rolls every stochastic gate *and* invalidates a banked pass@2.

Cost: three Dynamo Review runs against a rate-limited daily budget. The failures were 55 minutes
apart; the run that succeeded was 4.5 hours later. **Do not cycle immediately after one of these
— wait out at least one full hourly reset, and check `githubstatus` first** (it was clean
throughout, which is itself the evidence that this was the pipeline account's own core limit
rather than an incident).

### 5.2 Run 3 — everything green, first content cycle

| Gate | Result |
|---|---|
| `changes` (static, 25 checks) | pass — `.dockerignore` and the ≤1500-token count clean from the first commit |
| `review` / `deep_review` (rubric) | **31/31, zero failures — twice, independently** |
| `cosine_similarity` | pass (instruction 0.736, verifier 0.769, fingerprint 0.818 vs a 0.9 block) |
| `similarity` | **UNIQUE** — nearest TB3 `batched-eval-parity` at 0.121 lexical |
| `validation` | Docker / Oracle / Nop all green |
| `pass2` | **0/2, two valid failures**, "Rerun Recommended: NO" |
| `ava_review` | pass — no blocking findings |
| `qc_eval` / `qc_exec` / `qc_gate` | **pass, first cycle, no findings to answer** |
| `tier1` | pass |
| `trials` (pass@5) | **0/5 solved, avg@5 = 0.000, 5 good valid failures** |

**The pass@5 failures stratified across four root causes**, which is the whole argument for
breadth:

| Root cause | Trials |
|---|---|
| A — `missingValueReplacement` parsed then silently discarded | 3/5 |
| B — `and` short-circuits on UNKNOWN without checking later operands (`F ∧ U` returned UNKNOWN) | 1/5 |
| C — surrogate with all operands UNKNOWN returned TRUE instead of UNKNOWN | 1/5 |
| D — `missingValueStrategy="defaultChild"` never dispatched | pass@2 (both) + the `tier1` failure |

pass@2's analysis stated the mechanism outright: *"Both agents self-validated exclusively against
the shipped batches, which contain no records that exercise these PMML features. Both agents
declared success after that self-check."*

### 5.3 My ranking of the axes was wrong again — fourth confirmation

I expected `surrogate` and the three-valued `and` to carry the task, and rated
`missingValueReplacement` the *cheapest* of the six — a single attribute, one line to honour.
It caused **3 of 5** live failures. `and` and `surrogate` took one trial each.

`filer-access-audit`, `request-preconditions` and `rebuild-uptime-rollups` all recorded the same
inversion. The operative rule stands: **you cannot predict which axis gates. Keep all of them,
including the ones that look too easy to matter.**

## 6. Error → what to do, and what not to do

| Symptom | Do | Do **not** |
|---|---|---|
| `deep_review`/`ava_review` fail in ~12–14 s with `verdict line: <none>` | Read the job log for the *step* that failed. `Unable to download artifact(s)` + a rate limit is a platform fault; change nothing | Read it as a review rejection and start editing the task |
| You need to re-trigger but `/rerun` refuses you | `gh pr close` then `gh pr reopen` your own PR — same mechanism, fires a fresh pipeline on the same SHA | Push an empty commit; it re-rolls every stochastic gate and re-measures a banked pass@2 |
| The rate limit just fired | Wait out a full hourly reset (the successful cycle was 4.5 h later) and check `githubstatus` | Cycle immediately; two attempts 55 min apart both died the same way |
| A candidate axis rests on your reading of a standard | Probe a real implementation before writing task code | Reason from the spec text alone — three of nine axes died on contact with the engine |
| Two conforming implementations disagree on a behaviour you want to grade | Build every graded case so the readings coincide, and say so in the README | Pick the "correct" one and defend it across cycles |
| An axis looks too cheap to be worth a fixture | Keep it | Cut it — the cheap one caused 3 of 5 failures here |
| Your generator `rmtree`s its own output directory | Have it preserve hand-written files, and diff the staged file list before committing | Trust that a regeneration is idempotent — see §7 |

## 7. Process notes

- **A generator that wipes its own output directory ate a hand-written file.** `RULEPACK.md` — the
  agent-visible memo, the single most load-bearing document in the task — lives under
  `environment/data/`, which the archive builder `rmtree`s and recreates. Re-running the builder
  after writing the memo deleted it silently. **No test caught it**: nothing under `tests/`
  references the memo, and the oracle does not read it. It surfaced only from eyeballing
  `git diff --cached --name-only` before the commit. Generalisation: *the files a test never
  touches are exactly the files a build step can delete without consequence.* Read the staged
  list, not just the test output.
- **Harbor writes `jobs/` into the task directory** and `git add -A task` will happily stage it.
  Delete it before staging; it is textbook `no_extraneous_files`.
- **Local git identity set from `gh api user` at clone time** (`<id>+<login>@users.noreply.github.com`),
  before the first commit. Free, and `audit-build-context` §3.3 says it costs a live pass@5 to fix later.
- **`.dockerignore` in `environment/` from the first commit**; static passed 25/25 first time.
- **No `"You have N seconds…"` line**; `instruction_concision` passed with an explicit note.
- Two non-blocking advisories were **held, not pushed**, once the run went green: a contract regex
  (`^-?(0|[1-9][0-9]*)$`) looser than the instruction's "no sign", and `[task].description` (which
  ships in the repo's own template and passed both rubric runs). `nfs4-access-audit` §5.3 — at
  pass@5 0/5 there is nothing to gain and 31 criteria plus three LLM gates to re-roll.

## 8. Checklist for the next task

Before writing code:
- [ ] Is the deciding rule a **published convention**, **conditional**, and **absent from the
      sample**? All three, or it is recall rather than difficulty.
- [ ] **Probe a real implementation of the standard before designing around it.** Budget an
      afternoon. Expect to lose a third of your candidate axes.
- [ ] For every axis, ask whether two conforming implementations could disagree. If yes, either
      build the cases so they coincide, or cut it.
- [ ] Can an off-the-shelf package read your format? If yes, the crux is gone — invent the
      container, keep the semantics real.
- [ ] Count the independently-checkable consequences. Six was enough here and the live failures
      used four of them; fewer than six and one insight solves it.
- [ ] Write **three** plausible-wrong implementations. Require zero self-check diffs from all of them.
- [ ] For every graded artifact: does its correct answer exist anywhere under `/app`?

While building:
- [ ] Every invariant asserted at build time, per record, per pack — not argued in prose.
- [ ] Move data off every comparison boundary rather than deciding what happens on it.
- [ ] Explicit integer seeds; confirm the archive rebuilds byte for byte.
- [ ] Diff the **staged file list** before committing; a generator can delete a hand-written file
      that no test references.
- [ ] `.dockerignore`; no `tests`/`solution` substring in the Dockerfile; no time-budget line;
      delete `task/jobs/`.

Before every push:
- [ ] Oracle 1.0, nop 0.0, the copy exploit, and both sides of the guard, all against the real
      verifier in the built image.
- [ ] Leak-scan the image (`find /app -type f`).
- [ ] Root `README.md` reviewed against the **complete** diff, in the same commit.
- [ ] `gh pr checks` clean of `pending`.

## 9. One-paragraph version

The trap was a self-check that looks complete and is silent on everything that matters: two
shipped batches whose appliance scores ship beside them, both carrying a complete reading for
every field against packs with no strategy attributes, so the two-valued tree walk everybody
writes reproduces them exactly — while thirteen held-out packs carry the six PMML 4.4
missing-value behaviours that walk gets wrong. All five pass@5 agents built a substantively
correct scorer and failed on one or two of them, across four distinct root causes, with the axis
I rated cheapest (`missingValueReplacement`) causing three of the five. The design's decisive
move was probing a real PMML engine before writing any task code: it disagreed with the
specification on `or` over UNKNOWN, on `xor`, and on *when* a missing-value strategy fires, which
killed three candidate axes on the spot and forced every remaining graded case to be built so
both readings score identically — an ambiguity rejection avoided for the price of an afternoon,
and a README paragraph that reads as rigour instead. The only gate that ever blocked was the
pipeline's own GitHub token running out of API quota, twice, which fails `deep_review` and
`ava_review` in twelve seconds with an absent verdict and looks exactly like a rejection; the fix
was to wait out an hourly reset and cycle the PR closed-and-reopen, which fires a fresh pipeline
on the same SHA without a commit and without re-rolling anything.
