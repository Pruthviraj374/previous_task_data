# dynamo-81613d4 — rebuild-celstage-renderer

> **SUPERSEDED — this design was never accepted.** It went through **seven** pass@2
> rounds and was solved **2/2** in every one that was not an infrastructure failure,
> across eight successive stump mechanisms. It was replaced in the same repo by
> `dynamo/rebuild-lumenp-plates`, which was accepted at **pass@5 1/5 (avg@5 0.200)**.
> Read [`dynamo-81613d4-rebuild-lumenp-plates.md`](dynamo-81613d4-rebuild-lumenp-plates.md)
> for the rule that ended it: *disclosure and dismissability are mutually exclusive.*
> The sections below remain accurate about **why a search/discovery crux cannot yield a
> valid failure** (§1–§2) and about the verifier hardening (§5), all of which carried
> over intact. Treat §7's "more independent mechanisms" recommendation as **refuted** —
> two more were added after it was written and both were solved 2/2.

**Category:** Games Puzzles and Interactive Simulation / Rendering graphics
**Status at time of writing:** blocked by an upstream pipeline `startup_failure`, not by the task.
**Repo:** `dynamo-81613d4-games-puzzles-and-interactive-simulation`, PR #1.

Rebuild a retired studio 2D compositor (CELSTAGE) as `/app/render.py`, given a
normative memo and a set of scene/frame pairs, graded byte-close on held-out
scenes. Read this before designing any Pattern-D ("reverse engineer the
undocumented rule") task — the central finding is that a whole family of them
cannot pass this pipeline.

---

## 1. The single most transferable finding

**A stump must make the agent *finish confidently and be wrong*. It must not make
the agent *know it is unfinished*.**

The pipeline classifies a `reward 0` trial as a **valid** failure only when the
agent went idle, looped, or otherwise stopped. A trial that is still working when
the clock runs out is scored `low_timeout: FAIL` → *invalid* → pass@2 blocks.

A discovery/search crux (recover an undocumented function) produces exactly the
forbidden state: the agent always has one more hypothesis, so it is *always*
mid-progress at the cap, and the failure is *always* invalid. Measured three
times, at 3000 s and again at 3600 s (the pipeline's hard cap):

> "Both agents were still executing active stamp-search scripts at the moment the
> 3600-second hard timeout fired. **Neither was idle or stuck.**"

On the final such run, every other rubric column passed — `task_specification`,
`reward_hacking`, **`difficulty_crux`**, `near_miss`, `refusals`,
`approach_validity` — and the task still failed the gate. Getting the crux
*right* is not sufficient if the failure shape is a search.

The doc-34 examples that actually worked all have the opposite shape: the agent
quit early and confident (bytecode-vm quit in 77–137 s of a 900 s budget;
accrued-interest applied US conventions and stopped). Design for that.

---

## 2. The stamp trilemma — every configuration blocked by a different gate

The crux was a "build-audit stamp" in the frame's last pixel: three per-channel
rolling accumulators, `acc = (acc*M + b) mod 65536`, byte = `acc mod 256`.

| Configuration | Result | Gate |
|---|---|---|
| function withheld, stamp graded on held-out | agents search to the cap | pass@2 `low_timeout` — invalid (3×) |
| function disclosed (form + constants bounded) | 2/2 solved in 33 min | pass@2 too easy |
| stamp graded on shipped frames only | 17 readable stamps get tabled | rubric `anti_cheat` FAIL |
| (withheld, any grading) | — | `qc_gate` B5 "Underdetermined / Hidden-Knowledge Mapping" |

There is no fourth option. Notes on each:

- **Disclosing the form cannot be softened.** `(x mod 65536) mod 256 == x mod 256`,
  so the recurrence closes mod 256 and constants congruent mod 256 give identical
  stamps. The secret is **16 bits regardless of the modulus quoted**; once the
  form is known it is always a 65,536-case brute force. Verified numerically
  before spending a cycle on it.
- **`anti_cheat` caught the shipped-only grading**, correctly: an agent renders
  correctly (needed for held-out) and tables the 17 readable stamp triples keyed
  on its own render output. Confirmed by building the exploit: **1.0 against the
  broken grading, 0.0 against the fix**, oracle unaffected.
- **Short worked examples make the search tractable but do not change the
  outcome.** Adding 33/69/117-byte frames let a correct fit converge in ~0.9 s
  (verified), and the agents did reach fitting-style approaches ("LCG variants,
  linear regression") — they still never hit the right form, still ran to the cap,
  still scored invalid.

**Rule: never build the deciding crux out of an undocumented function.** `qc_gate`
blocks it as undetermined, and even when it survives that, the failure shape is
invalid by construction.

---

## 3. What the benchmarked model does and does not get wrong

Measured across ~8 pass@2 rounds on this task:

- **It implements any *stated* rule correctly**, including deliberately
  non-standard architecture. Four architectural cruxes (multi-polygon winding
  union, isolated-layer opacity, transform composition order, cut scoping) were
  solved 2/2 every single time. The analysis attributed this to "training-data
  knowledge of compositing theory," and `deep_review` said outright: *"the four
  architectural cruxes are not doing discriminating work."*
- **Softening the prose does not help.** Two full rounds were spent removing
  algorithmic phrasing from the spec ("the sum over every edge of every polygon",
  "taken together"). Both still solved 2/2. Standard compositing architecture is
  recalled, not derived, so concealment buys nothing — the same conclusion
  `dynamo-493df7d` reached for mathematical definitions.
- **It does fail to *discover* an unstated function** — but see §1 for why that
  cannot be converted into a passing task.

---

## 4. Gate-by-gate log

| Gate | What happened |
|---|---|
| static | passed first time; `.dockerignore` present from the start (see `fir` §6.1) |
| rubric (`review`) | 31/31 on the first push. Later FAILED once on `anti_cheat` (§2) |
| duplicate | UNIQUE throughout; closest lexical match 0.108 |
| validation | passed every push |
| pass@2 | the whole story: 2 passes, 3 invalid-timeout failures, 2 too-easy failures |
| `ava_review` | BLOCK — sample expectations were read from `/app/samples` (agent-writable). Fixed with a verifier-only `tests/samples/` copy |
| `adversarial_review` | passed; its own bypass attempt found nothing |
| `deep_review` | passed; flagged that the architectural cruxes were not discriminating |
| `qc_eval` / `qc_exec` / `tier1` | passed |
| `qc_gate` | BLOCK — B5 "Underdetermined / Hidden-Knowledge Mapping" on the withheld stamp |

Note the ordering: `qc_gate` runs **after** pass@2, so a task that cannot clear
pass@2 never learns what QC thinks. Two rounds were spent fixing a QC objection
that pass@2 then prevented from ever being re-tested.

---

## 5. Verifier hardening that this task needed

All of these were found by gates, not by local `oracle`/`nop`:

- **Never grade against anything under `/app`** — it is agent-writable. Keep a
  verifier-only copy under `tests/` and grade against that. (`ava_review`)
- **Grade every held-out byte.** Excluding any field from held-out grading opens
  memorisation of whatever is readable in the shipped set. (`anti_cheat`)
- **Make the sandbox non-optional** — `assert AS_ROOT` rather than silently
  skipping the privilege drop, so a misconfigured run fails loudly.
- **Size the per-call timeout against the fixture count**: N graded renders × the
  per-call cap must sit inside `[verifier].timeout_sec`.
- **Write every exploit before trusting the fix.** Both the reward-hijack and the
  stamp-tabling fixes were confirmed by measuring 1.0-before / 0.0-after with the
  oracle still at 1.0. One "fix" that measured 0.0 both ways turned out to be
  already-safe by accident, not by design.

---

## 6. Process notes

- `[agent].timeout_sec` caps at **3600 s**, and raising it is a one-shot lever.
  Spend it only on a confirmed `timeout_progress` classification.
- pass@2 is capped at **6 runs/day**; difficulty suggestions at **2/day**. Both
  reset at midnight UTC. Do not push speculatively.
- The `"You have N seconds…"` instruction suffix must **not** be included —
  confirmed again here (rubric passed 31/31 without it).
- An **upstream `startup_failure`** (1 s, zero jobs, "workflow file issue") is not
  yours to fix: these repos call a reusable workflow in
  `handshake-orchestration-tb2@main`. Verify `git diff upstream/main...HEAD --
  .github` is empty, re-trigger **once** with an empty commit, then contact the
  project team. Do not edit the task.

---

## 7. If picking this task up again

The four architectural mechanisms plus the anti-aliased `clip` mechanism are
sound, fully disclosed, un-memorisable, and calibrated — every cheaper reading
passes all 19 shipped scenes and fails 6–9 of 25 held-out. That part is reusable.

What is unresolved is whether five architectural mechanisms are *enough* to reach
≥3/5 valid failures, given four were reliably solved. If it comes back "too easy",
the next lever is **more independent mechanisms under all-or-nothing grading**
(Pattern G), not a harder single crux — and above all not a discovery puzzle.
