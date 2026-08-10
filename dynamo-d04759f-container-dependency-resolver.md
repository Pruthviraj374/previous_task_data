# dynamo/container-dependency-resolver — buying difficulty without spending disclosure

Repo: `dynamo-d04759f-build-dependency-and-release-management`, PR #2, branch `submission`,
fork `Pruthviraj374`.
Category: **Build Dependency and Release Management** / Sub-category: **Container Builds**.
`task.toml` declares `model_tested = GPT-5.4`, `agent_tested = Terminus-2`; the pipeline
stickies report the benchmarked model only as `Model A`.

**Accepted on 2026-08-08 at commit `3c7b10a`. pass@5 = 1/5 solved, avg@5 = 0.200,
4 good valid failures, 0 soft-timeout, 0 in-progress-timeout, 0 task/verifier issues,
0 reward hacking.** 17 checks green, 1 skipped by design (`pass2_suggestion`).

The final round is the one worth studying: **four failures stratified across four distinct
traps, no shared root cause, and zero timeouts.** The round before it — same oracle, same
spec — returned 4/5 *solved* and was blocked. The delta between those two rounds is two
commits and is the entire content of §2 and §3.

Forty commits over many pipeline cycles. `qc_gate` blocked three times, all on the same rubric code
(**B1 Ambiguous Rule**) against a different sentence each time; `ava_review` blocked once;
`pass2` blocked once on timeout; `trials` blocked once on difficulty. Cycles before
`3c27fcc` are reconstructed from `git log` and sticky history rather than directly
observed — treat §5.1 as secondhand and §5.2 onward as firsthand.

Commits that mattered: `e0dd3c0` initial design · `d5482a8` thin the sample so it validates
but never diagnoses · `5f065cd` restore `/app/resolve` grading + harden oracle · `c623f65`
document bare-brace depth and dynamic cycles · `2216126` **delete** the QC-flagged rule
instead of documenting it · `945aff9` QC B1 escaped-brace · `567b611` timeout 900→1800 ·
`3c27fcc` AVA leak wording · `79fbe6b` QC B1 unreferenced-var + three new traps ·
`3c7b10a` adversarial compositions + timeout 1800→3600 (accepted).

---

## 1. The task

A container build manifest declares `variables` and `layers`; the resolver that expands
shell-style `${KEY}` / `${KEY:-default}` references into a deployable config is "lost". The
agent rebuilds it.

- **Agent sees:** `/app/source/manifest.json` and `/app/source/env.json` — deliberately
  thin (two layers, one nested reference, one env lookup, zero escapes).
- **Agent produces:** an executable `/app/resolve <manifest> <env> <output>`, plus the
  resolved config at `/app/release/resolved.json`.
- **Graded on:** 15 held-out pytest tests that invoke *the agent's own binary* against
  manifests materialised into temp dirs at verify time.
- **Exit contract:** `0` success · `2` cyclic dependency · `3` syntax error.
- **Constraint:** Python 3 stdlib only.

The rule surface: ASCII-only keys `[a-zA-Z_][a-zA-Z0-9_]*`; `:-` fires on unset *or empty*;
nested defaults; `\X`→`X` with `\}` a literal that does not close a construct; lone `$`,
`{`, `}` outside a construct are literals; manifest vars shadow env; dynamic cycle
detection; eager validation of *every declared* variable value including unreferenced ones.

---

## 2. The single most transferable finding: compositions are difficulty you don't pay for

The QC gate's **B1 Ambiguous Rule** finding has one prescribed fix: *"Disambiguate the rule
in instruction.md so exactly one output is correct."* That is a demand to **disclose**. And
on a parser task, the undisclosed semantic *is* the difficulty — so complying with B1 hands
the crux to the agent and the task drifts toward "everyone passes".

This task hit that loop three times. The third instance is the clean illustration: QC
demanded that eager validation of unreferenced variables be spelled out. Before disclosure,
that single behavior was the whole discriminator — the AVA sticky said so explicitly:

> "the entire pass/fail discrimination rests on a **single** test
> (`test_error_on_unreferenced_bad_variable`); both pass@2 agents pass the other 10/11."

So disclosure was going to cost the task its only trap. The escape:

> **Add adversarial *compositions* of rules that are already disclosed. Compositions carry
> no new disclosure surface, so `decisive_rule_disclosed` and `spec_consistency` stay PASS,
> yet they break hand-rolled scanners that pass every rule in isolation.**

`instruction.md` was not touched by the accepted commit at all. The nine cases added to
`test_adversarial_compositions` are each decided purely by Rules 1–6 — no new semantics —
and they produced three of the four final failures. The gates agreed: QC returned
`QC-FIXES-B64: W10=` (empty), deep_review returned "Blocking Issues — None".

Why this works: a spec rule is a statement about one construct, but a *parser* is a state
machine, and the bugs live in state transitions between constructs. `\$` inside a default,
a bare `{` inside a default, a suppressed construct adjacent to a live one — every one is
implied by the disclosed rules and none is directly stated, because stating pairwise
interactions of six rules is combinatorially absurd and no reviewer expects it.

The highest-yield single case, aimed at the most common architectural mistake:

```python
# ${A}${B} where A = "\${B}", B = "real"  ->  "${B}real"
("adjacent_constructs",
 {"RESCAN_A": "\\${RESCAN_B}", "RESCAN_B": "real"},
 "${RESCAN_A}${RESCAN_B}",
 "${RESCAN_B}real"),
```

Any repeat-until-stable / fix-point resolver collapses this to `realreal`. Fix-point loops
are what agents reach for when they hit a concatenation edge case, and this case makes that
instinct fatal. It caught a pass@2 agent that had *not* motivated it, which is the evidence
that it generalises rather than fitting one trajectory.

---

## 3. The timeout paradox: "soft timeouts can only fill, not anchor"

The `trials` gate blocked at `79fbe6b` with 4/5 solved. There *was* a reward-0 trial. It did
not count:

> ❌ **Blocked.** No anchor fail — need >=1 good valid fail (clean reward-0 or stuck-timeout
> with `approach_validity != FAIL`); got 0 soft-timeout fail(s) and 0 good valid of 5.
> **Soft timeouts can only fill, not anchor.**
> Breakdown: 4 solved · 0 good-valid-fail · **1 in-progress-timeout**

The failing agent introduced a fix-point loop, **correctly diagnosed its own bug at step
35**, and was mid-rewrite when the 1800 s budget fired. A reward-0 caused by the clock is
classified `in-progress-timeout` and is disqualified as an anchor. The analysis was blunt
about the cause:

> "The 1800 s budget is adequate for the core task (**all agents had correct solutions by
> ~minute 25**) but leaves very little slack for debugging late-introduced regressions."

This creates a squeeze where each knob alone makes things worse:

| Move | Consequence |
|---|---|
| Raise `timeout_sec` only | The near-miss agent finishes its fix and passes → 5/5 → still 0 anchors |
| Add difficulty only | More agents get cut off mid-debug → more `in-progress-timeout` → still 0 anchors |
| **Both together** | Failures become *analytical* and land inside budget → they anchor |

`3c7b10a` did both: nine composition traps and `timeout_sec` 1800 → 3600 (the documented
cap). The result was unambiguous — **`low_timeout` PASS on all 5 trials, 0
in-progress-timeouts, 4 good valid fails.**

The counter-intuitive lesson worth carrying: **raising the agent budget can make the
difficulty gate easier to pass.** More time converts clock casualties into clean failures,
and clean failures are the only ones that count. Do not treat `timeout_sec` as a difficulty
dial — it is a *classification* dial. Difficulty comes from the verifier.

Cost: pass@2 and trials both scale with `timeout_sec`, so a full round went from ~1h15m to
~2h30m. Budget accordingly before pushing.

---

## 4. What the benchmarked model actually gets wrong

Fourteen trials across the four directly observed rounds (pass@2 and pass@5 on `79fbe6b`,
then on `3c7b10a`) produced a stable taxonomy. Every item below is observed, not
hypothesised. **The core is never the problem** — single-pass scanning, brace
depth, nested defaults, transitive chains and dynamic cycles were implemented correctly in
essentially every trial. Failures are exclusively boundary conditions:

| # | Failure mode | Trials | Why it happens |
|---|---|---|---|
| 1 | Re-scanning resolved output (fix-point loop) | `rEn2TYG`, `ydS8XFP` | Reached for to fix a concatenation edge case; destroys escape suppression — `${RESCAN_B}real` → `realreal`, `\${NOT_A_VAR}` → `""` |
| 2 | `\$` inside a default treated as construct opener | `tNzzD2U`, `TUZHFP2` | Escape state not consulted before incrementing depth; or backslash stripped before recursive resolution, turning `\${X}` into unterminated `${X` |
| 3 | Bare `{` increments depth | `7mMndor` | `find_matching_brace` counts any `{`, not only `${`; `${U:-a{b}` declared unterminated |
| 4 | `str.isalpha()`/`isalnum()` for keys | `gBC5Jcn`, `J5snXTk`, `TUZHFP2` | Python's are Unicode-aware — `'é'.isalpha()` is `True`, so `${é}` wrongly resolves |
| 5 | Loose post-key grammar | `gBC5Jcn`, `TUZHFP2` | Invents a "suffix" concept so `${INVALID-KEY}` resolves key `INVALID`; only `}` or `:-` may follow a key |
| 6 | Lazy (resolution-time) validation | pre-`79fbe6b` trials | Skips the eager scan of declared-but-unreferenced variables |

Modes 2 and 3 are pure compositions — they cost nothing in disclosure and produced three of
the four accepted-round failures. Mode 4 is the cheapest trap in the whole task: one
Unicode key, and it fails agents across every round.

Note the shape of mode 1 versus the rest. Mode 1 is an *architectural* error the agent can
self-diagnose given time (which is exactly why it timed out rather than failed cleanly).
Modes 2–5 are *analytical* errors the agent does not know it has, so they fail inside
budget. **Analytical traps anchor the gate; architectural traps time out.** Prefer traps the
agent cannot discover by re-reading its own output.

---

## 5. Gate-by-gate log

### 5.1 — Early cycles (secondhand, reconstructed from `git log`)

- **`5f065cd`** — restore `/app/resolve` grading (tests had been grading the reference
  solution rather than the agent binary), add AVA fixtures, harden the oracle.
- **`c623f65` → `2216126`** — QC flagged a bare-brace depth rule as ambiguous. First
  response documented it; second **deleted the rule and its trap entirely**
  (`${UNSET:-{}` over-consumption). Worth noting as a live option: when QC calls a rule
  ambiguous, removing it can beat disambiguating it, if the trap is not load-bearing.
- **`945aff9`** — QC B1 again, on `\}` inside a construct. Disambiguated in Rule 3.
- **`567b611`** — `pass2` blocked on timeout; `timeout_sec` 900 → 1800. (Same failure mode
  as §3, one round earlier and one order of magnitude less subtle.)
- **`3c27fcc`** — `ava_review` blocked: the no-leak clause wording implied agents should
  create `/app/solution`. Aligned the wording with the actual check.

### 5.2 — `qc_gate` cycle: B1 on unreferenced-variable validation

QC quoted Rule 6 and objected that "nothing agent-visible states that variables which are
never referenced must still be validated". `79fbe6b` disclosed it **and** pre-emptively
added three new disclosed-but-subtle rules (nested object/array recursion, literal
`$`/`{`/`}`, unset-no-default→empty) to survive the disclosure. QC passed; the added rules
turned out to be too natural to discriminate (see §5.3).

### 5.3 — `trials` cycle: 4/5 solved, blocked

Covered in §3. The three rules added in `79fbe6b` were all things a competent agent gets
right by instinct — **disclosed-and-easy is not a substitute for disclosed-and-subtle.**
That is what pushed the design toward compositions.

### 5.4 — Accepted round (`3c7b10a`)

Every gate green, each verified against the correct base SHA rather than the checkmark:

| Gate | Verdict | Evidence |
|---|---|---|
| `pass2` | ✅ 1/2, 1 valid-fail | 0 in-progress-timeout; failure traced to a re-scan pass |
| `deep_review` | ✅ PASS | "Blocking Issues — None" |
| `ava_review` | ✅ PASS | advisory only |
| `tier1` | ✅ PASS | `head_sha: 3c7b10a`, `fixes: {}` |
| `qc_gate` | ✅ PASS | `QC-BASE: 3c7b10a`, `QC-FIXES-B64: W10=` |
| `trials` | ✅ Difficulty OK | 1/5 solved, 4 good valid, avg@5 = 0.200 |

---

## 6. Process notes

**Job conclusions lie.** `review / qc_exec` and `qc_eval` both report SUCCESS on rounds
where `qc_gate` says BLOCK. Read the sticky comment body, and check that `QC-BASE:` matches
your HEAD — a stale sticky from the previous base reads exactly like a fresh verdict. Same
for `TIER1-STATE`'s `head_sha`. `QC-FIXES-B64` decodes to the required-fix list; `W10=` is
`[]` and means clean.

**Never push while a check is pending** — the workflow uses cancel-in-progress, so a push
discards a round you have already paid for. `gh pr checks 2 -R <upstream>` before every push.

**Never `git add -A`** — `task/jobs/` accumulates transient pass@2 / trial artifacts.

**Verify locally before every push.** Copy `tests/test_outputs.py`, point `RESOLVE_BIN` at
`task/solution/solve.py`, stub the four `/app`-path tests
(`test_artifacts_exist`, `test_json_is_valid`, `test_sample_resolution`,
`test_no_leaked_helpers`), and run it. Catching a bad expected value locally costs seconds;
catching it in CI costs 2.5 hours.

**Probe the oracle before designing a trap.** Every composition in §2 was run against
`solve.py` first, so the accepted commit needed no parser change and carried zero risk of
oracle/test drift — the failure mode that historically triggers AVA and QC findings.

**Do not push cosmetic fixes onto a green run.** A stale test count in `README.md` sat
unfixed for two rounds on purpose; it rode along with the next substantive commit. Every
push re-rolls a stochastic pass@2 and pass@5.

---

## 7. If picking this up again

The design that survived: **a thin sample that validates but never diagnoses** (the shipped
manifest has no escapes and no nested defaults, so agents cannot reverse-engineer the hard
semantics by experiment), plus **held-out compositions of disclosed rules** as the
difficulty reservoir.

If a future round comes back too easy, the reservoir is not exhausted — these were verified
against the oracle and left unspent:

| Case | Oracle | Why it bites |
|---|---|---|
| `A = ${A:-fallback}`, layer `${A}` | **exit 2** | Self-reference is a live cycle; the default does *not* rescue it. Most implementations return `fallback` |
| `A = ${X:-${B}}`, `B = ${A}`, X unset | **exit 2** | Cycle through a *taken* default — the inverse of the existing untaken-branch test |
| `${U:-x\:-y}` | `x:-y` | Only the *first unescaped* `:-` separates key from default |

Spend these before touching `instruction.md`. Adding a rule re-opens the B1 ambiguity
surface that cost this task three QC cycles; adding a composition does not.

**One-paragraph version.** QC's B1 finding forces you to disclose the semantics that make a
parser task hard, and disclosure is what makes it easy. The way out is compositions of
already-disclosed rules — no new spec text, no new ambiguity surface, and they break the
state machine where the rules meet. Separately, a reward-0 trial that ran out of clock does
not count as a difficulty anchor, so raise `timeout_sec` until failures are analytical
rather than truncated, and get difficulty from the verifier instead. Do both in one commit,
because either alone makes the gate worse.
