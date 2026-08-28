# dynamo/convert-letterform-packs — six axes, six sections of one spec, and all six gated

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 16 checks green on the first push, zero revisions, `accepted` label |
| **Repo** | `dynamo-fd4f169-file-and-media-operations`, PR #2, branch `submission`, fork `charan-sr` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-fd4f169-file-and-media-operations/pull/2 |
| **Category / sub** | File and Media Operations / **File format conversion** (pre-seeded; first in this sub-category) |
| **Benchmarked model** | `task.toml` names Opus-4.8 / Terminus-2; stickies report `Model A` on Daytona |
| **Final commit** | `7e48aa4` (three commits, **one push**) |
| **Headline** | **pass@5 = 0/5 solved, 5 good-valid fails, avg@5 = 0.000.** pass@2 0/2. Rubric **31/31 first cycle**, `qc_gate` **clean first cycle, zero findings**, `deep_review`/`ava_review`/`tier1` all first-try. Zero platform faults |

Sixth File and Media Operations entry, after `recover-zip-headers`, `rebuild-plate-rasterizer`,
`restore-stillwater-volumes`, `keepcase-restore` and `rebuild-listings-copy`. Disjoint from all
five: no shared artifact (glyph programs vs. a zip container, a prepress spool, a filesystem
dump, an archival snapshot, a broadcast feed), no shared authority (Adobe TN #5177 vs. PKWARE
APPNOTE, ISO 32000-1, POSIX, ETSI EN 300 468), and the work is executing a stack language rather
than replaying recorded state or decoding characters.

Four things worth the read: **§0** (the repo's own closed PR ruled out an entire design family
before a line of code), **§2** (why all six axes gated, against this corpus's standing pattern
that half of them gate nothing), **§5.2** (the mutant battery ate an *untracked* reference and
`git checkout` could not save it), and **§6** (the axis ranking inverted for the seventh time).

---

## 0. The closed PR on this repo, and what it deleted from the search space

`00-ATTEMPTER-SPEC.md` and `restore-runbook-advisor` §4.1 both say read the repo's own PRs first.
This repo had one, closed unmerged: **PR #1, `dynamo/ebcdic-to-csv`** — 29 commits, ~20 design
revisions, an EBCDIC/COMP-3/RDW mainframe extract converted to CSV. Its author left two ledger
comments, and they are the single most valuable thing in this file:

> **12 reference solves, 0 valid fails** across six architectures of escalating derivation depth
> (dual schema revisions with lying headers → cycle-window filtering → withheld direction mapping
> → reporting-period convention as a candidate family → tombstone decoy blocks → digest-authority
> verifier). Reference solve times stayed at 14–32 minutes of 60 throughout.

> *"for single-dataset file-conversion tasks whose outputs are reconciled by an in-file control
> record, the pass@k bar is not reachable — withholding member values converts the crux into
> **constraint search** (solved), while withholding the search anchor itself makes the mapping
> undisclosed hidden knowledge (B5)."*

That is `sdf-registration-qc`'s derivability rule and `recover-index-codes`'s guess-vs-implement
rule arriving together, measured twelve times, in **this sub-category**. It deleted three things
from my search space before I wrote anything:

1. **EBCDIC / copybook / packed-decimal / mainframe extract conversion** — occupied and dead here.
2. **Rule-piling as the difficulty source.** Twenty revisions of "add another derivation layer"
   produced twelve solves.
3. **Reconciliation-anchored cruxes.** An in-file control total turns a withheld rule into a
   search the model runs happily.

Its other lesson was mechanical: high implementation breadth produced **in-progress timeouts**,
which do not count toward the ≥3 bar. So the deliverable had to stay small enough to finish. My
reference is ~290 lines; the pass@5 trials all completed.

---

## 1. What the task asks

A sign shop cut raised lettering on a router that read one file per typeface — a *letterform
pack*, written by a plate compiler the shop no longer has. The new CAM software wants outlines.

- **Agent sees:** `instruction.md`, `/app/data/PACKS.md` (the shop's note on the container),
  `/app/data/sample/alder.pack` **with** `/app/data/sample/alder.json` — the outline data the old
  reader produced for it, a complete end-to-end self-check — and `/app/data/birch.pack`, whose
  answer exists nowhere in the image.
- **Agent produces:** `/app/convert.py`, invoked `python3 /app/convert.py <pack> <out.json>`, plus
  its run over the shipped pack at `/app/output/birch.json`.
- **Graded on:** that artifact, a re-run over the shipped pack, **twenty held-out packs** that
  exist only in the verifier overlay, and the integrity of `/app/data`. Thirteen tests,
  all-or-nothing, 22 packs and 259 glyphs in total.
- **Output:** a JSON object of per-glyph `name` / `advance` / `contours`, every coordinate an
  absolute integer. **No tolerance exists anywhere in the task**, so no gate ever had a
  threshold-artifact argument available (`replay-collection-sort` §4.2, taken for free again).

---

## 2. The crux: six sections of one public spec, none of them derivable

`PACKS.md` documents the invented `WXLP` container byte for byte — a 32-byte header and four
indexes of identical shape — and then says the glyph programs are **Type 2 charstrings**, names
**Adobe's *The Type 2 Charstring Format*, Technical Note #5177, 16 March 2000** as the governing
format, and restates none of it. That is `replay-flash-capture` / `emulate-int8-accel` /
`replay-collection-sort`'s **name the authority, enumerate nothing**, now in an eighth category,
and `qc_gate` B5 never fired.

Six of that format's provisions are conditional, and the shipped pack is built so none fires:

| # | Provision (TN #5177) | The natural implementation does | Inert in the shipped pack because |
|---|---|---|---|
| 1 | The advance may ride as an extra **leading operand** on the first stack-clearing operator, and equals `nominal_width_x + w` — present iff the operand count exceeds that operator's arity | always reports `default_width_x`, and reads the extra operand as geometry | no shipped glyph carries one |
| 2 | A hint-mask operator is followed by **⌈stems/8⌉ mask bytes in the charstring** | hard-codes one byte and desynchronises | no shipped glyph declares more than eight stems |
| 3 | Arguments still on the stack at the first mask operator are an **implied vertical stem declaration** and count toward that total | counts too few stems, so the mask is read short | every shipped glyph declares its stems outright |
| 4 | A subroutine operand is an offset from a **bias of 107, 1131 or 32768** by array size | indexes the wrong subroutine | every shipped array is small, so 107 is right |
| 5 | `flex` / `hflex` / `hflex1` / `flex1` each pack their two curves differently, with coordinates **derived rather than read** | crashes on escape byte 12, or draws the wrong second curve | no shipped glyph uses them |
| 6 | `hhcurveto` / `vvcurveto` / `hvcurveto` / `vhcurveto` carry **one extra argument** when the operand count is odd | drops a coordinate | every shipped curve uses the plain form |

**Why these pass the derivability filter.** Every one is an arbitrary decision recorded in a
committee document — a parity rule, a byte count, a historical constant, an argument layout.
`sdf-registration-qc`'s test asks whether a competent expert could *derive* the value from the
disclosed inputs with no external fact to recall. For all six the answer is no; there is nothing
to derive, only something to read. Contrast the closed PR's cruxes, every one of which was
recoverable by fitting the shipped reconciliation.

**Why the naive first-recall model is wrong.** `replay-panel-capture`'s filter: does the model's
first-recall model of this thing give the wrong answer? For a charstring it is "a stack machine
whose operators pop their arguments" — which is wrong for the width, wrong for the mask bytes,
wrong for the subroutine bias. (A display controller fails this filter because its weird
addressing *is* its headline knowledge; a charstring's headline is the stack machine, and all six
axes live below it.)

**Machine-enforced generator invariants** — `tools/gen.py` writes nothing if one breaks:

1. the three inert packs (`alder`, `birch`, `h18`) carry **none** of the six forms;
2. every hint-mask byte is **≥ 0x20 and never 0x1C**, so a converter reading one byte short
   desynchronises onto an *operand* rather than an operator — a plausible wrong outline instead
   of a crash. This one fired on the first run and caught a `0x18` byte in `birch`;
3. the worked example witnesses **every** machinery operator, a two-byte operand, an outline-free
   glyph, and a contour that is never drawn from;
4. each latent form appears in **≥ 2** held-out packs.

**Silence by construction, twice more.** Subroutine arrays are padded to their size class with
well-formed one-segment fillers, so a wrong bias yields `subrs[idx - 1024]` — which Python
resolves by negative indexing onto a filler — and draws different but valid geometry. And the
graded output type is an integer coordinate list, so a wrong answer is never a near-miss on a
threshold.

---

## 3. Ground truth from someone else's implementation, before any task file existed

The single highest-value hour of the build, and the reason nothing about correctness was ever
argued:

- `tools/t2pack.py` **authors** each glyph's absolute outline and advance by hand and then encodes
  a charstring that draws it. The expected document therefore never passes through a charstring
  interpreter (`reassemble-tap-sessions` §4 — plant ground truth, never parse it back).
- `tools/check_fonttools.py` decodes the generated bytes with **fontTools** and requires it to
  reproduce all 22 answer documents. It does.
- Before that, a scratch harness ran **4,000 randomised charstrings** — every operator, both hint
  styles, one to three mask bytes, biases 107 and 1131, all four flex operators, all odd-count
  curve forms, negative nominal widths — through my interpreter and fontTools: **0 mismatches**.

That is `collate-modpool-batches` §6's "cross-check the fixture writer byte-for-byte against the
real implementation" and `keepcase-restore` §3's "a doc summary is a hypothesis, the runtime is
the experiment", applied to a wire format. It also answers `unambiguous`'s sound-alternative test
outright: a *different* conforming implementation produces exactly the shipped answers.

The library is pure Python and public, so an agent could in principle fetch and port it — the
`rebuild-mask-hierarchy` §5b fetch bypass. Accepted on that entry's own evidence (four of five
samples failed genuinely), and it never fired: no trial in seven reached for a reference
implementation, and stdlib-only is enforced at run time anyway.

---

## 4. Everything the corpus records, built before push one

This is why the first push was the only push. Nothing below was learned from a block:

| Built up front | Source |
|---|---|
| Name the authority inside `/app`, not only in `instruction.md` — the QC probe reads the pristine image | `rebuild-readout-builder` §3.3, `restore-runbook-advisor` §3.2 |
| Flat descriptive register; no "where this note is silent", no naming the areas | `replay-strata-plans` §3.2 |
| Answers read into memory and **deleted from disk** before any submitted code runs; `/tests` sealed | `filer-access-audit` §4.4 |
| Each pack staged under a **neutral name** (`input.pack`) in a fresh scratch dir | `replay-flash-capture` §6 |
| Graded program run as `nobody`, site packages dropped, runtime audit hook — never a source scan | `contact-export` §3.2, `audit-build-context` §4.2 |
| The hook raises `ImportError`, and the **accept side** is probed in the same battery | `audit-build-context` §4.2, `contact-export` §3.3 |
| Output read `O_NOFOLLOW`, must be a regular file with one link | `read-cavity-captures` §7 |
| **Never grade a case whose reference ships** — `alder` is the self-check and is not graded | `read-cavity-captures` §5 (E1) |
| The graded shipped artifact has no answer anywhere under `/app` | `merge-lora` §4.1 |
| Declared-immutable inputs pinned against sealed twins | `replay-panel-capture` §4 (tier1 E2) |
| Strict schema and type checks — `True == 1` and `1.0 == 1` in Python | `replay-strata-plans` §4.5, `cron-window-counts` §8 |
| Verifier timed against a **hanging** submission: 22 runs × 10 s = 220 s, inside QC's 300 s probe cap | `statement-rollup-repair` §4a |
| `.dockerignore` from commit one; no `solution`/`tests` substring in the Dockerfile; no `"You have N seconds"` line; no `task/README.md`; `tools/` at the repo root | six prior entries |
| `.gitattributes` `* text=auto eol=lf` + `*.pack binary`; staged blobs diffed against disk | `replay-fleet-survival` §8 |
| `difficulty_explanation` naming synthetic provenance **and** a real-world audience | `decode-vibration-log` §4 |

Rubric came back 31/31 with "Failures: None", `qc_gate` 37 checks clean with zero findings, and
`ava_review`/`deep_review`/`tier1` all passed first try.

---

## 5. Local batteries, and the one that bit me

### 5.1 The divergence matrix (`tools/calibrate.py`)

Ten plausible-wrong converters, each inert on all three shipped-shaped packs and each caught by
2–7 held-out packs; eight further misreadings of the *documented container* (no close on move, no
alternation, subroutines ignored, `rcurveline`/`rlinecurve` swapped, little-endian operands,
mask bytes not skipped, little-endian header, no bias at all) each required to **break the shipped
pack**. That second table is `replay-collection-sort` §9.1 encoded before push one, and it is
what kept `ava_review` `verifier_coverage` and `qc_gate` C3 from ever firing.

It also caught two real design defects while I was building:

- `bias_none` was inert nowhere — the sample *does* use subroutines, so it teaches that a bias
  exists. It is a machinery misreading, not a latent one; only the bias *value* is latent.
- `h07` originally discriminated nothing: the implied-vstem axis is observable **only** through
  the mask byte count, so the implied stems have to cross a multiple of eight. Both implied-vstem
  packs were rebuilt to cross one.

### 5.2 The mutant battery owns the reference — commit it first

`tools/probes.py` drops each variant in as `solution/convert.py` and runs the real
`harbor run --agent oracle`. The first battery **timed out at ten minutes** with a mutant in
place, and because `convert.py` was still **untracked**, `git checkout` had nothing to restore
from and I had to rewrite the reference from scratch.

> **Commit the reference before the first mutant battery, restore with `git checkout` rather than
> the harness's own backup, and re-run the calibration afterwards.** `merge-lora` §6 and
> `wetland-nitrate-effect` both record a battery poisoning a concurrent operation; this is the
> version where the harness's *own* restore is the thing that cannot be trusted.

A second effect of the same run: its baseline row reported reward 0.000 while a concurrent
`docker build` of the same context was running. The re-run reported 1.000. **Do not run anything
else against the Docker daemon while a probe battery is measuring.**

Final battery, on the shipped design: **17 of 17 as designed** — reference 1.000, nine
misreadings 0.000, six reward-hacking attempts 0.000 (echo the shipped answer, read the sealed
material, symlink the output path, write nothing, spawn a child, import a third-party package),
and a correct converter that tries an optional third-party import and falls back scoring 1.000.

### 5.3 Making the unreachable branch live rather than deleting it

`subr_bias`'s third step (32768, for arrays of 33,900 or more) was unreachable — textbook
`qc_gate` C3 (`consolidate-zero-checkpoints` §4). Deleting it would have removed a real behaviour
to satisfy a coverage metric. Instead I added two held-out packs with ~34,000 subroutine entries
each (~370 KB apiece, generated in seconds), which made the branch live **and** added a seventh
discriminating reading (`bias_second_step`, caught by exactly those two packs). Same trade as
that entry's bf16 buffers: the coverage fix bought difficulty.

---

## 6. What the model actually did — all six axes gated

**pass@5: 0 solved · 5 good-valid-fail · avg@5 = 0.000.** `task_specification`, `reward_hacking`,
`difficulty_crux`, `refusals`, `low_timeout` and `approach_validity` **PASS on all five**;
`near_miss` FAIL on 2 of 5 (those two were near-misses, which is healthy). Zero timeouts, zero
infra faults, zero verifier issues.

The analysis states the design premise back verbatim:

> *"the agent correctly identified the container format and the Type 2 charstring execution model,
> built a working interpreter for the 'plain' subset of the format, validated against the shipped
> alder/birch sample (which the task author explicitly designed to exercise none of the hard
> provisions), and declared completion before testing the conditional edge cases."*

| Provision | Trials failing |
|---|---|
| Flex operators (escape byte 12) | **5 of 5** |
| Curve extra-argument (odd operand count) | **5 of 5** |
| Optional advance-width operand | 3 of 5 |
| Implied vertical stems | 2 of 5 |
| Hint-mask byte width | 1 of 5 |
| Subroutine bias | 1 of 5 |

**Every one of the six gated.** The corpus's standing pattern — `filer-access-audit`,
`request-preconditions`, `rebuild-uptime-rollups`, `replay-collection-sort`,
`replay-flash-capture` — is that two of four axes gate nothing. `serve-thesaurus-lookups` §2 is
the only prior all-gated case, and its explanation was that six axes were *one root misreading in
six places*. This task is the **other** way to get there: six axes that are **six different
sections of one document**, each reachable only by reading further than the sample forces you to.
`collate-modpool-batches` §3's rule is what makes that work —

> *needing a spec is not reading a spec: the agent reads until the shipped sample parses, then
> stops.*

— and this is its second confirmation, in a second category, with the analysis naming the
mechanism itself: *"multiple agents explicitly noted uncertainty about flex operators, decided the
sample didn't use them, and marked the task complete."* That is `accrued-interest`'s *"probably
isn't being tested"* for the ninth time in this corpus.

**The ranking inverted again, seventh confirmation.** I rated the odd-argument curve form the
weakest of the six and nearly cut it as "just reading the operator table"; it took **5 of 5**. The
hint-mask byte width, which I built the most fixtures for and considered the sharpest, took **1 of
5**. Never cut an axis on your own ranking.

---

## 7. Gate-by-gate log

| Push | Commit | Result |
|---|---|---|
| 1 | `7e48aa4` (over `841c20c`, `b9811cf`) | `changes` ✅ 13s · `review` (rubric) ✅ **31/31, Failures: None** 2m37s · `similarity` ✅ **UNIQUE** (closest TB3 `rs-archive-clone` 0.129) · `cosine_similarity` ✅ 1m16s · `validation` ✅ 1m1s · **`pass2` ✅ 0/2** (1 valid-fail, 1 in-progress-timeout) 1h6m32s · `pass2_suggestion` skipping · `deep_review` ✅ 4m1s · `ava_review` ✅ 6m53s · `tier1` ✅ · `qc_eval` ✅ 8m41s · `qc_exec` ✅ 8m6s · **`qc_gate` ✅ zero findings** · **`trials` ✅ pass@5 0/5, avg@5 0.000, 5 good-valid** 1h4m37s · `gate` ✅ → **`accepted`** |

Full cycle ≈ **2h20m**. Zero platform faults — no outage, no rate limit, no stale sticky, no
close/reopen.

The rubric left one non-blocking note: `verification_explanation` credits `tools/` for the
fontTools cross-check and the calibration, but `tools/` lives at the repo root and is not under
`submission/task/`, so a read-only reviewer cannot re-run it. The eval answered itself — *"the
fixtures are independently checkable by running the provided `convert.py` over `tests/packs/*.pack`
and diffing against `tests/expected/*.json`, so I did not treat the absence as a defect"* — and
`no_extraneous_files` passed precisely because `tools/` is outside `task/`
(`rebuild-vestra-systems` §8). **Not acted on**: at 0/5 accepted, a push re-rolls everything.

---

## 8. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| Starting a task in a sub-category with a **closed** PR on the same repo | Read its ledger comments in full before designing. This one recorded 12 solves / 0 valid fails and named the dead family outright | Do not assume a closed PR failed for a fixable reason; it may have measured a whole design family dead |
| Choosing a crux for **file format conversion** | Take a large, real, public format and let the sample stop short of the sections that decide the answer | Do not build the difficulty from derivation depth or reconciliation — measured twelve times on this repo as constraint search the model runs happily |
| A latent axis can only be observed through a *quantised* quantity (a byte count, a size class) | Build the fixture so it **crosses the quantisation boundary**. Implied stems change nothing unless they cross a multiple of eight | Do not assume "the axis is present in the data" means "the axis discriminates"; measure it |
| Your reference has a branch no fixture reaches | Make it live if the real system does it — two packs of filler subroutines cost minutes and bought an axis | Do not delete a real behaviour to satisfy a coverage metric |
| Running a mutant battery that rewrites `solution/*` | **Commit the reference first**, restore with `git checkout`, re-run the calibration afterwards | Do not trust the harness's own backup-and-restore, and do not run other Docker work concurrently — both bit here |
| Choosing mask/padding bytes that a wrong reader will mis-consume | Pick values that decode as **operands**, so a desync produces a plausible outline rather than a crash; assert it in the generator | Do not leave it to chance — the first run caught a byte that would have decoded as an operator |
| A subroutine/table index computed with the wrong offset | Pad the array with valid entries so the wrong index still resolves to well-formed data | Do not let a wrong index raise; a crash is a weaker stump than a confident wrong answer |
| Every gate green on push one | Stop. Write the retrospective | Do not push the advisory note you are holding |

---

## 9. Reusable checklist

Design:
- [ ] Read the repo's **closed** PRs before designing; a ledger of measured solves deletes whole families.
- [ ] Prefer a **large, real, public** format whose sample can stop short of the deciding sections.
- [ ] Score every candidate axis on **arbitrary vs derivable**. A parity rule, a byte count, a historical constant and an argument layout are all arbitrary; a formula is not.
- [ ] Ask whether the model's **first-recall model** of the artifact gives the wrong answer.
- [ ] Keep the deliverable small enough to finish — the sibling PR lost trials to in-progress timeouts on a large one.
- [ ] Pick an output type with **no numeric tolerance** if the domain offers one.

Fixtures:
- [ ] Author the answer and encode the input **separately**, then have a third-party implementation reproduce every answer.
- [ ] Differential-test the reference against that implementation over **thousands of randomised inputs** before writing any task file.
- [ ] Generator invariants, machine-enforced, refusing to write: inert packs carry no latent form; every disclosed mechanic breaks the sample; each latent form in ≥2 held-out packs; desync bytes decode as operands.
- [ ] Make every wrong reading **silent** — pad arrays, choose bytes, avoid crash paths.

Verifier:
- [ ] Answers in memory, deleted from disk, `/tests` sealed, packs staged under neutral names.
- [ ] Unprivileged run, site packages dropped, runtime audit hook, `O_NOFOLLOW`, regular-file check.
- [ ] Strict schema **and type** checks — reject floats and booleans where whole numbers are required.
- [ ] Never grade a case whose reference ships; the graded artifact has no answer under `/app`.
- [ ] Time the suite against a **hanging** submission, and keep it inside QC's 300 s probe cap.

Before pushing:
- [ ] `gen.py`, `calibrate.py`, the third-party cross-check, `harbor` oracle/nop, and the full probe battery — reference 1.000, every misreading and bypass 0.000, **accept side 1.000**.
- [ ] Leak-scan the built image; grep the agent-visible surface for crux vocabulary; diff staged blobs against disk.
- [ ] README and all three `task.toml` explanations re-derived from a fresh run, in the same commit.

---

## 10. One-paragraph version for future me

The first task in File and Media Operations / File format conversion, **accepted on one push with
every gate green first try** — rubric 31/31, `qc_gate` clean with zero findings, pass@2 0/2, and
pass@5 **0/5 solved, avg@5 = 0.000, five good-valid failures**. The design came almost entirely
from this repo's own **closed** PR, whose author had recorded twelve reference solves across six
architectures of an EBCDIC conversion task and concluded that withholding member values just
converts the crux into a constraint search the model runs happily; that deleted derivation depth,
reconciliation anchors and the whole mainframe family before I wrote a line. What replaced it was
an invented container documented byte for byte, carrying **Type 2 charstrings** with Adobe TN
#5177 named as the authority and nothing restated — six of its conditional provisions (an
optional leading width operand, inline hint-mask bytes counted from the stem total, implied
vertical stems, a subroutine bias of 107/1131/32768 by array size, four flex operators with
derived coordinates, and the odd-count extra curve argument) all made inert in the worked example,
each an arbitrary committee decision with nothing to derive. **All six gated**, which this corpus
has only seen once before, and for the opposite reason: `serve-thesaurus-lookups` had one
misreading in six places, this had six different sections of one document, each reachable only by
reading further than the sample forces — `collate-modpool-batches`'s *needing a spec is not
reading a spec*, confirmed a second time, with the pass@5 analysis quoting agents who noted
uncertainty about the flex operators, decided the sample did not use them, and marked the task
complete. Ground truth was authored by hand and then verified by **fontTools** on all 22 packs and
4,000 randomised charstrings, which made correctness unarguable and answered the
sound-alternative test outright. Two process lessons: the mutant battery ate an **untracked**
reference and `git checkout` could not restore it — commit the reference before the first battery
and never run other Docker work beside it — and an axis observable only through a quantised
quantity (mask bytes per eight stems) discriminates nothing until the fixture crosses the
boundary. Seventh confirmation that the ranking inverts: the axis I nearly cut as "just reading
the operator table" took 5 of 5, and the one I built the most fixtures for took 1.
