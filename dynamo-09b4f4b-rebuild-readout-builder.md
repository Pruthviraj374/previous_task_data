# dynamo/rebuild-readout-builder — one axis is a coin flip, two axes are a task

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 17 checks green, `accepted` label |
| **Repo** | `dynamo-09b4f4b-data-science-and-reporting`, branch `submission` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-09b4f4b-data-science-and-reporting/pull/1 |
| **Category / sub** | Data Science and Reporting / Experiment and metrics analysis (pre-seeded) |
| **Benchmarked model** | reported as `Model A` (`task.toml` names Opus-4.8 / Terminus-2 — fixed dataset fields) |
| **Final commit** | `1c57454` (5 pushes, 5 pipeline runs) |
| **Headline** | **pass@5 = 1/5 solved, avg@5 = 0.200, 3 good valid fails.** One run earlier the same task scored **pass@5 3/5** while `pass2` was **0/2 on that very commit** |

Five pushes. `pass2` returned **0/2 on every one of them** and told me almost nothing: the
only pass@5 those four identical readings produced was **3/5 — blocked**. The whole task turns
on what separates run 4 from run 5.

---

## 1. What the task asks

A reader app ran an A/B test; the platform that turned its archived client telemetry into a
readout was retired. The agent rebuilds it as `/app/readout.py`, invoked
`python3 /app/readout.py <archive_dir> <out_json>`.

- **Agent sees:** `instruction.md`, one archive at `/app/data/export/` (44 assigned units,
  3 silent, 3 stray installs, 1,121 data points), `/app/data/readout.json` — the correct
  readout for that archive — and `/app/data/ARCHIVE.md`, the platform's format note.
- **Archive:** `experiment.json` (id + the metric names the readout covers), `assignments.csv`
  (`unit_id,variant`), `metrics.json` (OTLP/JSON `ExportMetricsServiceRequest`; unit named in
  the `unit.id` resource attribute; every metric a `Sum`).
- **Readout:** per variant `units`; per metric `control`/`treatment` `{total, mean}`,
  `absolute_lift`, `standard_error`, `significant`.
- **Graded on:** the shipped archive plus **eight held-out archives** (312 units, 43,386 data
  points), all-or-nothing across 10 tests. `units`/`total` exact integers, `significant` an
  exact boolean, floats within 1e-9 relative.

---

## 2. The crux, and the invariants that keep it alive

A unit's figure for a metric is the sum of what each of its **accumulations** closed at, and an
accumulation is pinned by **two** things at once. Both are the OpenTelemetry metrics data
model, which `instruction.md` and `ARCHIVE.md` name and then stop.

| Axis | The rule | Wrong reading costs |
|---|---|---|
| **A. Accumulation identity** | a cumulative `Sum` point reports what it accumulated since the instant in its own `startTimeUnixNano`, so a series with several start instants is several accumulations | 1.4×–5.8× under |
| **B. Series identity** | the points a metric carries for one unit belong to as many series as there are distinct data point **attribute sets** | up to 3.2× under |

**Why B is not a variation on A.** A unit's series for a metric *begin together* — the
instruments start when the process does — so they share start instants. Collapse the attribute
sets and every series but one is dropped *per start instant*; collapse the start instants and
every accumulation but the last is dropped *per series*. Measured through the verifier, the two
readings fail **disjoint** held-out sets: 6 of 8 for collapsing attributes (missing `cinder`,
`ember`), 7 of 8 for collapsing start instants (missing `basalt`).

**Invariants:**

1. **The shipped archive witnesses every shape and discriminates none of them.** Every data
   point carries an attribute set, but only one distinct value per unit and metric; 48 streams
   carry a second start instant, on a run that opened and closed accumulating **nothing**; 56
   readings fall, always to **exactly zero**. All six wrong readings reproduce the shipped
   readout bit for bit. Omission would have left the mapping undeterminable — see §3.2.
2. **A leading blank run is the only inert split.** A run closing at zero costs nothing under
   any arithmetic; a middle or trailing one would not, so only leading blanks are generated.
3. **A fall from exactly zero is the only inert fall.** The rises-and-falls reading errs by
   exactly the previous reading on each fall, so a fall from `0` is free — the shipped
   non-monotonic metric dips below zero and returns, never falling from a non-zero value.
4. **Every run opens with a zero point stamped at its own start instant**, so "closing reading"
   and "closing minus opening" are the same number everywhere. Asserted moot on all nine
   archives; no rival arithmetic can produce a different answer.
5. **`significant` is pinned but never hairline.** Three metrics bracket the stated `1.96·SE`
   (t = 1.86, 2.03 and 1.40 equivalents), so substituting 1.30/1.64/2.15/2.58 is rejected —
   while the closest verdict is still **2.1 %** clear, ~13 orders of magnitude above float
   noise. Every wrong reading of the crux is also caught on an exact **integer total**, so no
   archive is ever decided by the boolean alone.
6. **The instruction never names the deciding vocabulary.** `restart`, `reset`, `epoch`,
   `monoton…`, `decreas…`, `unbroken`, `startTimeUnixNano`, `series`, `breakdown`, `dimension`,
   `data point attribute` — grepped over `instruction.md` and everything the Dockerfile copies,
   on every calibration run.

---

## 3. Dead ends, and what the gates actually said

### 3.1 One axis is a coin flip, and `pass2` cannot see it

Runs 1–4 shipped **axis A alone**. `pass2` came back **0/2 every time**, four runs running,
with the same root cause and zero variance. Run 4 reached `trials`:

> **pass@5: 3/5 passed** · avg@5 = 0.600 · ❌ **Blocked. Not hard enough.**

The two failures were textbook. The three passes were the finding:

> *"both passing agents that also initially tried a naive 'last point' approach
> (task__zDtvHGB at step 5; task__rx3B9GV during early exploration) **caught themselves and
> refined to group-by-`startTimeUnixNano`** before submitting."*

**A single axis does not fail agents, it fails coin flips.** Four consecutive 0/2 results were
not evidence of difficulty — they were four samples of a ~40 % per-trial solve rate. This is
`reduce-palaeomag` §4.2 and `experiment-analysis-frame` §4 confirmed from the other side: those
files say keep a second axis even when it looks inert. This one says **you cannot ship without
one**, and `pass2` will not tell you.

### 3.2 Answering B5 by omission — blocked twice, correctly

`qc_gate` raised **B5 Underdetermined / Hidden-Knowledge Mapping** on runs 1 and 2:

> *"Rival rule 'each stream = one accumulation, value = latest data point of stream' reproduces
> the disclosed example with NO differences… 0 multi-start streams and 0 falling sums."*

The first archive was *too* clean: nothing visible distinguished the two readings. Answering it
by **making the shipped archive witness both shapes inertly** (§2.1) was right and cost nothing
— `pass2` stayed 0/2 and the probe confirmed it saw them. But it did not clear B5, because the
witnesses all close at zero and so still do not discriminate. That half is unfixable by data: a
discriminating example *is* the answer.

### 3.3 The probe cannot read `instruction.md`

Both B5 findings opened with the same clause, which I nearly dismissed:

> *"**No instruction.md/spec exists anywhere**; pristine `/app` discloses only one archive +
> its `readout.json`."*

It is literally true and it is not a defect claim. **Harbor hands `instruction.md` to the agent
as the prompt; it is not a file in the image.** The static check, the rubric and `deep_review`
all read it fine — the QC probe reads the pristine image and cannot. So the fairness anchor
("the OpenTelemetry metrics data model governs") was invisible to the one gate that adjudicates
fairness.

**Fix: put the spec where the probe looks.** `/app/data/ARCHIVE.md` — the platform's own format
note, stating what the three files are, that `metrics.json` is OTLP/JSON
`ExportMetricsServiceRequest` (opentelemetry-proto v1.3.0), and that the published data model is
normative, with the URL. It names *where the rule is defined* and stops; it never mentions start
instants, attributes, runs or aggregation. **B5 cleared on the next run** and `pass2` stayed
0/2 in the same run.

This is the `rebuild-plate-rasterizer` §3.1 line — name the standard, never its parameter —
applied to a *locator* rather than to content.

### 3.4 The threshold I kept clear of the boundary was the threshold nobody pinned

`qc_gate` run 1, **C3 Narrow / Hardcodable Held-Out Coverage**:

> *"Mutated significance test from `abs(lift) > 1.96*se` to 1.64, 1.30, and 2.15; all still
> give reward=1."*

I had deliberately kept every verdict ≥40 % from its threshold, reasoning from
`experiment-analysis-frame` §3.5 that hairline margins are a `difficulty_evidence` risk. **That
was the wrong transfer.** `significant` is not a tolerance — it is a deterministic boolean from
a formula the instruction states exactly, so a correct solver computes the identical float. The
only margin that matters is one above double-precision noise: **2 %, not 40 %.** Three fixtures
were retuned to bracket 1.96, and `near_miss` came back explicitly PASS — *"the concept is
doing the work, not a threshold."*

### 3.5 A sealed directory does not seal the output path

`qc_gate` run 1, **E5 Symlinked Output Path**. `chmod 0700` on `tests/expected` stopped the
graded program *reading* the answers — but it could still point its own output path at one and
let the root verifier follow the link. Fixed with `O_NOFOLLOW` + realpath containment + a link
count check. **Probed both sides** (`contact-export` §3.3): symlink exploit → reward 0, hardlink
exploit → reward 0, reference solution → reward 1.000.

---

## 4. What worked

### 4.1 Raise difficulty; never restore concealment

`trials` said 3/5. The two available responses were to make the crux less visible again — which
re-opens B5 and loops — or to add real difficulty. The spec forbids the first and the corpus
says the second means **a second independent axis**. Attributes were already in the OTLP wire
format; making them load-bearing cost one field in the generator and one key in the reference,
and nothing was hidden to do it. Result: **3/5 → 1/5**.

### 4.2 Pick an axis reached by a different *question*

Axis B is in the same published document as axis A, which sounded too close until I framed it as
the question each answers: *"when does accumulation restart?"* versus *"what identifies a
series?"* Different sections, different instincts. The measurement bore it out immediately —
in run 5's `pass2` both agents **solved axis B and failed axis A**:

> *"group cumulative Sum data points by attribute set only, pick the globally-latest data point
> per group… This ignores `startTimeUnixNano` entirely."*

Run 4's agents had failed the opposite way. Same task, two runs, two different rules dropped.
That is what a second axis buys, and it is invisible to any single trial.

### 4.3 Plant ground truth; never parse it back

`tools/generate.py` chooses each run's closing values and derives the expected readout from
those numbers (`reassemble-tap-sessions` §4). There is no `_reference.py`, so `oracle = 1.000`
is a real cross-check: the shipped solution is an independent consumer that must recover the
figures from the OTLP document. The rubric cited it unprompted under `reviewable`.

### 4.4 Calibrate before pushing, not in answer to a block

`tools/calibrate.py` runs **47 assertions** every time: inertness of the shipped archive under
each of six wrong readings, pinning of every machinery step, threshold pinning from both sides,
integer-total coverage, archive shape, and the vocabulary grep. It caught the missing 2.15 pin
after the axis-B regeneration reshuffled every seed — a finding that would otherwise have cost
a full cycle.

---

## 5. Gate-by-gate log

| Push | Commit | Result |
|---|---|---|
| 1 | `d3f9a0c` | static ✅ 25/25 · rubric ✅ **31/31 first time** · duplicate ✅ UNIQUE · validation ✅ · **pass2 ✅ 0/2** · `deep_review` ✅ · `ava_review` ✅ · **`qc_gate` ⛔ C3 + E5** (42/44) |
| 2 | `6661824` | all of the above ✅ · `tier1` ✅ both fixes accepted · **`qc_gate` ⛔ B5** (42/44, 1 advisory) |
| 3 | `041ebf4` | **pass2 ✅ 0/2** · **`qc_gate` ⛔ B5 restated** (43/44) |
| 4 | `069d144` | **`qc_gate` ✅ first clear** · **`trials` ⛔ pass@5 3/5, avg@5 = 0.600 — not hard enough** |
| 5 | `1c57454` | everything ✅ · **`trials` ✅ pass@5 1/5, avg@5 = 0.200, 3 good valid fails** → `accepted` |

`pass2` was **0/2 on all five pushes**. `pass2_suggestion` skipped every time.

**Final pass@5 rubric:** all 7 criteria PASS on every analysed trial. `approach_validity`:

> *"The agent's approach is unsound per that spec — not a borderline interpretation… There is
> no task or verifier defect: the specification is unambiguous, the verifier is correct, and the
> tolerance is not doing the work (errors are 40–480 % off, not sub-percent)."*

Agents quit at **6–7 minutes of a 3600 s budget**, having matched the shipped archive exactly.

**Timings:** whole run ≈ 2 h. `pass2` 7–30 min, `deep_review` 4–7 min, `ava_review` 5–7 min,
`qc_eval` 6–13 min, `qc_exec` 3–5 min, `trials` 22 min–1 h 07 m.

---

## 6. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| `pass2` **0/2** and you have exactly **one** deciding axis | Add a second axis **before** spending a `trials` slot. 0/2 is two samples of a rate that can be 40 % | Do **not** read repeated 0/2 as difficulty. Four consecutive 0/2 runs preceded a 3/5 |
| `trials` **3/5 — not hard enough** on a latent-crux task | Add an independent axis reached by a *different question*, and check the two wrong readings fail **disjoint** archive sets | Do **not** make the crux less visible again — that re-opens the discoverability gate and loops |
| `qc_gate` **B5** whose evidence begins *"No instruction.md/spec exists anywhere"* | Believe it. Harbor delivers `instruction.md` as the **prompt**, not as a file — ship the format note **inside `/app`**, naming the standard and stopping | Do **not** dismiss it as a probe artifact and re-push unchanged; and do **not** state the rule to satisfy it |
| `qc_gate` **B5** *"a rival reading reproduces the disclosed example with NO differences"* | Two halves: make the sample **witness** every shape inertly, and make the governing standard **readable in the image**. The first alone will not clear it | Do **not** make the shipped example discriminate — that *is* handing over the crux |
| You are choosing how far from a stated threshold to keep your fixtures | Ask whether the quantity is a **tolerance** or a **deterministic boolean**. For a boolean from a stated formula, 2 % is enormous; leave fixtures on both sides so the threshold is pinned | Do **not** transfer "keep clear of hairline margins" from a *tolerance* to a *formula* — it caused C3 |
| You sealed the expected outputs with `chmod` and think the verifier is safe | Also guard the **output path**: `O_NOFOLLOW`, realpath containment, link count. Probe the exploit **and** the correct solver | Do **not** assume unreadable means unreachable — the root verifier will follow a link the program plants |
| You want a shape visible for fairness but inert for difficulty | Find the *one form* where every rival arithmetic agrees: a run closing at **zero**, a fall **from zero**, an attribute set with **one value** | Do **not** simply omit the shape — omission is what B5 blocks |
| Regenerating fixtures after a design change | Re-run every pinning assertion; seeds reshuffle and silently unpin things | Do **not** assume tuned margins survive an RNG change — the 2.15 pin was lost exactly this way |

---

## 7. Bugs I introduced myself

- **`cd task && …` in a shell whose cwd was already `task/`.** The `cd` failed, `&&`
  short-circuited, and a patch script silently did not run — while a *separate* command on the
  next line printed a success-looking message. Check the thing changed, not the exit line.
- **A `str.replace` that matched nothing.** A README edit keyed on `**Symlinked output path.**`
  when the file said `*Symlinked output path.*`; the script asserted and wrote nothing. Every
  patch now asserts `count == 1` before replacing — worth the two extra lines each time.
- **Claimed an assertion count from memory.** The README said 55, then 62, when
  `grep -c "^  ok"` said 37. Re-count generated numbers; never carry them forward.
- **Left a leading-blank-run draw ungated at first**, which would have consumed RNG for archives
  that do not use it and silently reshuffled every tuned seed. Guarded with `lead and
  rng.chance(lead)` so the draw is never taken when the flag is absent.

---

## 8. Reusable checklist

Design:
- [ ] **Two independent axes minimum.** One axis is a coin flip that `pass2` cannot measure.
- [ ] Are they reached by *different questions*, and do their wrong readings fail **disjoint**
      held-out sets? Measure it; do not assume it.
- [ ] Is each rule **real, external, published** — and **noticed** (a property of the input)
      rather than **recalled** (a table)?
- [ ] Does the shipped sample **witness** every shape in its inert form, rather than omit it?
- [ ] Is the error orders of magnitude on an **integer** field?

Discoverability:
- [ ] Is the governing standard named **inside `/app`**? `instruction.md` is not a file in the
      image and the QC probe cannot read it.
- [ ] Does the naming stop at the *locator*, never reaching the rule?

Verifier:
- [ ] Output path guarded against symlinks, escaping realpaths and extra links.
- [ ] Expected values **planted** by the generator, not recomputed from the solution.
- [ ] Every stated constant (threshold, tie-break) pinned by a fixture on **both** sides.
- [ ] Every tightening probed on the accept side in the same run.

Before every push:
- [ ] `python3 task/tools/calibrate.py` → 0 failing.
- [ ] Oracle 1.0, nop 0.0, re-run after **any** data change.
- [ ] Crux vocabulary absent from `instruction.md` and everything the Dockerfile copies.
- [ ] Instruction ≤1500 Qwen3 tokens, re-measured after the last edit.
- [ ] Root `README.md` re-read against the **complete** diff; every number re-derived.
- [ ] `gh pr checks 1 | grep -c pending` → 0.

---

## 9. One-paragraph version for future me

Five pushes, and `pass2` returned **0/2 on every single one** — including the commit whose
pass@5 was **3/5, blocked**. That is the lesson: with one deciding axis, four consecutive 0/2
results are four samples of a coin flip, and `pass2` is structurally unable to tell you.
`qc_gate` cost three of the five rounds, on findings that were all correct: a significance
threshold no fixture pinned (because I had transferred "avoid hairline margins" from a
*tolerance* to a *deterministic boolean*), an output path the graded program could symlink at
the sealed answers, and — twice — a discoverability block whose evidence opened *"No
instruction.md/spec exists anywhere"*. That last clause is literally true and easy to dismiss:
Harbor hands `instruction.md` to the agent as the **prompt**, so the probe reading the pristine
image never sees the sentence naming the standard. Shipping the archive's own format note at
`/app/data/ARCHIVE.md` — naming OTLP and the published data model, and stopping there — cleared
it without moving `pass2` off 0/2. What finally cleared `trials` was refusing to hide anything
and adding a **second** rule from the same standard reached by a different question: OTLP series
identity includes each data point's attribute set, and a unit's series begin together, so
collapsing them drops all but one closing value per start instant. The two wrong readings fail
disjoint archive sets, and the proof it works is that run 4's agents failed by ignoring start
instants while run 5's agents **solved attributes and failed start instants**. pass@5 went
3/5 → **1/5, avg@5 = 0.200**, with `approach_validity` PASS on every trial and agents quitting
at six minutes of an hour, having matched the shipped archive exactly.
