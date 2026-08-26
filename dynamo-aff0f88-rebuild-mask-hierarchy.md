# dynamo/rebuild-mask-hierarchy — three formula-based designs died 2/2, a real arbitrary lookup table won 0/5

| | |
|---|---|
| **Outcome** | **ACCEPTED** — `pass@5 = 0/5`, `avg@5 = 0.000` (maximum difficulty: all 5 trials genuine valid fails, none solved) |
| **Repo** | `dynamo-aff0f88-machine-learning-and-ai`, branch `submission`, fork `charan-sr` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-aff0f88-machine-learning-and-ai/pull/1 |
| **Category / sub** | Machine Learning and AI / Computer vision (pre-seeded; first task in this exact subcategory besides `dynamo-04fda1d-read-cavity-captures`) |
| **Final commit** | `cdaed06` (design 3, `rebuild-mask-hierarchy` / FITS+JWST-DQ) |
| **Total iterations** | ~28 commits across 3 fundamentally different container designs over 2 days |
| **Headline** | Two structurally different containers (multi-tap sensor reconstruction, then binary-mask connected-component analysis) died repeatedly to the same wall: any axis disclosed enough to be fair gets solved cleanly, no matter how numerically intricate. The winning design swapped the crux from a *formula* (however obscure) to a *real, external, arbitrary lookup table* — the same shape that won `dynamo-20141f7`'s MDL/CTfile precedent — and only succeeded once that table was picked to resist a fetch-based bypass. |

---

## 1. The three designs

| # | Design | Crux | Result |
|---|---|---|---|
| 1 | `rebuild-tap-frames` | Multi-tap sensor frame reconstruction (GenICam `TapGeometry`, later a fully-general strided rule + Overscan×Reversed interaction) | 0/2 (unfair — GenICam enum) → 2/2 (fully disclosed) → 2/2 (entangled rule also disclosed) → abandoned |
| 2 | `rebuild-mask-hierarchy` v1 (PGM) | Connectivity duality, then PGM header robustness, then Benkrid-Crookes perimeter + diamond-hull solidity formulas | 2/2 each time a fix satisfied fairness — five consecutive "too easy" verdicts across 2 days |
| 3 | `rebuild-mask-hierarchy` v2 (TIFF) | TIFF `PhotometricInterpretation`/`FillOrder` tags | 0/2 (undisclosed) → 2/2 (disclosed) — mainstream tags, model recalled them cold once cued |
| 4 | `rebuild-mask-hierarchy` v3 (FITS + JWST DQ) | Real STScI `stdatamodels.jwst.datamodels.dqflags.pixel` bit table | 0/2 → 2/2 (fetched from GitHub!) → 0/2 → 0/2 → 0/2 → **0/5 pass@5 — ACCEPTED** |

---

## 2. Design 1 — multi-tap sensor reconstruction (abandoned)

Invented an archival `.tap` + `.job.json` frame-grabber format and asked the agent to
reconstruct a true frame from a multi-tap sensor's raw interleaved byte stream, per a
`TapGeometry` field using the real GenICam SFNC enum (`Geometry_2X`, `Geometry_2XE`,
etc.).

- **First push**: undisclosed geometry → 0/2, but `deep_review` correctly flagged it
  unfair. Both trials converged on the *same* wrong "block-split" reading — not
  because it was hard, but because block-split is itself a reasonable engineering
  default, indistinguishable from the real (column-interleave) answer without either
  prior knowledge or a working internet lookup. Critically, **both trials reported no
  working internet access despite `allow_internet=true`** in that specific harness
  configuration — an important, non-obvious platform behavior (see §6).
- **Second push**: replaced the opaque enum with a fully-general, fully-disclosed
  strided-coordinate rule (avoiding the enum-lookup-table shape entirely) → 2/2,
  solved cleanly in ~5 minutes by both trials.
- **Third push**: added a genuinely entangled second rule (`Overscan` field interacting
  with `Reversed`) → 2/2 again, including one trial that caught and fixed its own bug
  before submitting.
- **Conclusion**: every rule in this container was an *author-invented convention*,
  merely flavored with real GenICam vocabulary. Disclosed enough to be fair → cleanly
  transcribed, every time, regardless of how many mechanisms or how entangled the
  interaction. Abandoned; pivoted to a completely different container.

---

## 3. Design 2 — binary mask connected-component analysis, v1 (PGM)

Read a binary PGM mask, count foreground objects / enclosed background holes.

- **Connectivity duality** (foreground 8-connected / background 4-connected, a real
  axis where OpenCV/MATLAB and `scipy.ndimage` genuinely disagree): left undisclosed
  → `deep_review` flagged it as undiscoverable (both trials split on principled-but-
  opposite guesses). Disclosed → 2/2, solved instantly.
- **PGM header robustness** (the real Netpbm grammar permits `#`-comment lines and
  irregular whitespace, which every shipped mask's plain header omits): first sample
  gave a genuine 1/2 (one trial's parser crashed on a comment line) — a real, fair
  crux. Strengthened with a second comment position → 2/2 clean, both trials
  correctly implemented full comment/whitespace handling unprompted.
- **Perimeter/solidity formulas** (`perimeter`: a real Benkrid & Crookes
  border-erosion + weighted-convolution FPGA estimator; `solidity`: `area /
  convex_hull_area` using scikit-image's diamond-footprint pixel convention instead
  of the "obvious" square-corner one) — both independently verified byte-for-byte
  against real `scikit-image` on hundreds of random masks before shipping. Fully
  disclosed step-by-step in `MASKFMT.md` → 2/2, both trials transcribed the
  documented procedures exactly.
- **Foreground threshold boundary** (`>= 128` vs. `> 128`, exercised via a pixel
  written with the literal byte value 128) — added specifically because a `qc_gate`
  mutation found the boundary untested; also solved cleanly once disclosed.

**Five consecutive "too easy" outcomes across two days and multiple redesign
attempts**, all sharing the same shape: *any rule, however numerically intricate,
that is disclosed precisely enough to satisfy fairness review gets transcribed
correctly by this model, regardless of how many such rules are combined.* This
matches `dynamo-20141f7`'s own finding almost exactly (see that case study): volume
of cruxes does not help if every crux is a formula forced by a disclosed definition.

---

## 4. Design 3 — TIFF `PhotometricInterpretation`/`FillOrder` (abandoned)

Pivoted the mask container from PGM to a hand-rolled, byte-verified baseline TIFF
(bilevel, uncompressed) image. The two chosen axes are real TIFF 6.0 tag
conventions, not author-invented: `PhotometricInterpretation` (0=WhiteIsZero vs.
1=BlackIsZero — which raw sample renders black) and `FillOrder` (1=MSB-first vs.
2=LSB-first bit packing). Both are documented, recurring real-world bug classes
(WhiteIsZero images silently rendering inverted; bit-packed images reading garbled
under the wrong fill order).

- **Undisclosed**: a genuine, non-stratified 0/2 — one trial missed
  `PhotometricInterpretation`, the other missed `FillOrder`, each correctly handling
  the other.
- **Once disclosed** (one sentence: "this axis of variation exists, resolve it
  per-file" — no values restated, per `deep_review`'s own suggested fix): 2/2, both
  trials correctly implemented *both* real tag conventions from scratch, unprompted.

**Conclusion: TIFF's core tags are too mainstream/well-documented in this model's
training data.** Once merely cued to "check thoroughly," it already knew the exact
values — a qualitatively different outcome from the JWST table below, where cued
recall was still frequently wrong. This is the key lesson of this whole task: *real
and externally-checkable is necessary but not sufficient — the fact must also be
niche enough that the model hasn't memorized it precisely.* Verified for future
reference that RDKit (a real, pip-installable cheminformatics library implementing
MDL/CTfile V2000 parsing — the winning precedent's domain) is a **compiled C++
extension** with no locally-readable Python source, while `stdatamodels` (this
task's JWST library) is pure Python with the exact table sitting in one plainly
readable file — very likely why the two precedents diverged in what happened next.

---

## 5. Design 4 — FITS + JWST calibration-pipeline DQ bit table (accepted)

Pivoted again: masks are minimal, hand-rolled, byte-verified FITS files (80-byte
ASCII header cards, 2880-byte block padding, big-endian int32 data — verified
against real `astropy.io.fits` round-tripping across 180+ random arrays, 0
mismatches). Each file's integer data array is a per-pixel Data-Quality (DQ)
bitmask, using the *exact* real bit convention from STScI's `stdatamodels` package
(`stdatamodels.jwst.datamodels.dqflags.pixel` — independently verified against the
actual installed package before use, not recalled from memory: `AD_FLOOR`=bit 6,
`CHARGELOSS`=bit 7, `RC`=bit 14, 32 entries total, a genuine external committee
decision). Each FITS file's header names, via a `DQFLAG` keyword, exactly one
condition that defines foreground for that file. All six shipped masks use
`DO_NOT_USE` (bit 0 — deliberately the single most prominent, foundational-sounding
flag, i.e. the one a solver without the real table would most plausibly guess by
default); held-out masks use `AD_FLOOR`/`CHARGELOSS`/`RC` — markedly less prominent
real flags from the same table.

### 5a. First hurdle: mission ambiguity (fixed)

Initial disclosure said only "the mission's real DQ bit convention" without naming
JWST specifically. `deep_review` correctly flagged this as undiscoverable: multiple
real missions (JWST, HST/ACS, HST/WFC3) have genuinely *different* bit tables for
similarly-named flags, so an agent had no way to know which convention applied —
confirmed directly by a failing trial whose own `decisive_rule_disclosed` trace said
its wrong answer was "a fully defensible inference from all observable evidence."
Compounding this, the "retired space telescope" framing actively misdirected, since
JWST is operational, not retired. **Fix**: name JWST and
`stdatamodels.jwst.datamodels.dqflags.pixel` explicitly in `instruction.md` and
`MASKFMT.md`; drop "retired."

### 5b. Second hurdle: the fetch-based bypass (the central finding of this task)

Once fairly disclosed, pass@2 flipped to a clean 2/2 — but not from mastery. Trace
inspection showed one trial ran `pip install stdatamodels` and read the installed
package directly; the other fetched the package's raw source file straight from
`raw.githubusercontent.com/spacetelescope/stdatamodels` via stdlib `urllib.request`
— no `import` statement needed at all, so the runtime audit-hook guard never even
saw it. **A real, externally-checkable, disprovably-wrong fact is not safe if it is
the literal internal data of an actively-maintained, open-source, PyPI/GitHub-hosted
package, when internet access is available**: `allow_internet=true` turns it into a
single trivial, error-free fetch, unrelated to whether the model actually knows the
convention.

Attempted the obvious fix (`allow_internet=false`) — **rejected outright by the
platform's own static check**: this benchmark requires `allow_internet=true`,
non-negotiably. Disabling internet is not always an available lever; check before
assuming it is.

Reverted, and instead accepted the real, evidenced variance: **five separate pass@2
samples on this exact crux, all with internet available, produced four genuine 0/2s
(wrong recall — different fabricated flag names/bit positions each time) and only
one 2/2 (legitimate fetch)**. `deep_review`'s own reasoning already treated
consulting the real, named source as a fair strategy, not a bypass, for a real fact
— the task does not need to structurally prevent lookup, only remain fair, which it
already was. Pass@2 is a 2-sample pre-check; pass@5 (5 samples) is the gate that
actually matters, and the observed ~80% genuine-failure rate predicted it would
clear the ≤2/5-solved acceptance bar. **It did — 0/5, the maximum possible
difficulty outcome.**

### 5c. Automated reviewer self-inflicted false positive

`ava_review` once blocked on a claim that the real `stdatamodels` package has bit 8
named `UNRELIABLE_ERROR`, not `RESERVED`. Independently re-verified directly against
the actual installed package (`stdatamodels==6.0.0`, confirmed the latest release)
before touching anything: bit 8 *is* `RESERVED`; no `UNRELIABLE_ERROR` entry exists
anywhere in the real package (checked the full dict and grepped the installed
source tree). **The automated reviewer had confabulated a fact — the exact failure
mode this task's own crux is built to catch, now demonstrated in the review tooling
itself.** Left the (already-correct) table unchanged and added an explicit,
reproducible verification citation (exact package version, exact command, exact
result) directly above the table; the next `ava_review` pass accepted it. Lesson:
never "fix" a value to match an automated finding without independently
re-verifying the finding's factual claim first, especially on a task whose entire
point is that confident-sounding wrong recall is easy to produce.

### 5d. Two ordinary `qc_gate` mutation findings (both narrow, both fixed in one push each)

1. **Border-adjacency coverage**: a mutant that checked only `r==0 or cc==0` (top
   row OR left column, dropping bottom row and right column) still passed every
   test, because the one existing "isolated edge" fixture only isolated the *left*
   edge — a mutant that keeps that same edge's check is invisible to it. Fixed by
   adding one fixture per remaining edge (top-only, right-only, bottom-only),
   completing full 4-edge coverage.
2. **Point-in-hull boundary inclusion**: a mutant changing the tolerance check from
   `< -tol` (correct: reject only if clearly outside) to `<= tol` (incorrectly
   rejecting points exactly ON a hull edge) passed every test, because no existing
   fixture had a pixel center landing exactly on a hull edge (cross-product exactly
   0) — ordinary blocky/rectangular shapes rarely produce this by accident. Fixed
   with a fixture of two blocks touching only diagonally, whose combined hull does
   put several pixel centers exactly on an edge (verified: correct solidity 0.75,
   mutant 0.86 — a large, non-hairline margin).

---

## 6. The rules this task establishes

> **A real, external, disprovably-wrong fact beats a formula, however obscure or
> numerically intricate the formula is — but it must also be niche enough that the
> model hasn't memorized it precisely, AND resistant to a trivial internet
> fetch-and-parse if `allow_internet=true` (which may be a mandatory platform
> constraint you cannot opt out of).**

Corollaries, in the order they bit this task:

1. **"Disprovably wrong, not just a different reasonable choice" is necessary but
   not sufficient.** GenICam's `TapGeometry` failed because the wrong reading was
   itself a defensible engineering default. TIFF's tags and JWST's DQ table both
   passed this test (real committee decisions, not two equally-valid conventions) —
   but only one of them survived contact with the model's training data.
2. **"Real and disprovably-wrong" is *also* not sufficient — obscurity to the model
   matters independently of obscurity to a human practitioner.** TIFF's
   `PhotometricInterpretation`/`FillOrder` are technically real, external, and
   arbitrary, exactly like JWST's DQ table — but TIFF is such a ubiquitous,
   thoroughly-documented format that the model's recall of its core tags was
   precise, not just approximate. A format's *headline* fields should be assumed
   already mastered before testing; look instead at genuinely niche
   scientific/instrument-specific conventions.
3. **A structural clue for picking a resistant source: check whether the real
   library implementing the convention is compiled/binary (no locally-readable
   Python source after `pip install`) rather than pure Python.** This is very
   likely why the accepted MDL/CTfile precedent (RDKit, a C++ extension) and this
   task's JWST design (originally `stdatamodels`, pure Python) diverged on the
   fetch-based bypass specifically.
4. **`allow_internet=false` is not always an available fix — some benchmark
   configurations require `allow_internet=true` as a hard, non-negotiable static
   check.** Verify this before planning around disabling it.
5. **One pass@2 sample choosing to verify against a real, legitimately-named source
   is expected variance, not proof the crux is broken.** Before redesigning off a
   single "2/2 solved," pull the raw job log of the *previous* run that showed a
   valid failure (the sticky PR comment is overwritten every run; the GitHub
   Actions job log is not) and check whether the same crux, unchanged, already
   produced a genuine failure. Only repeated, *identical-strategy* 2/2s are real
   evidence of saturation.
6. **`task.toml`'s difficulty/solution/verification explanations must argue a
   priori why the task is hard — citing actual pass@2/pass@5 trial outcomes is an
   explicitly, mechanically-checked prohibited framing**, even when factually
   accurate.
7. **Never "fix" a fact to match an automated reviewer's finding without
   independently re-verifying the finding's claim first** — reviewers can
   confabulate too, and blindly complying would have introduced a real bug into an
   already-correct reference table.
8. **A held-out fixture that isolates one instance of a symmetric-N-way rule (e.g.
   one of 4 border edges) does not cover a mutant that only breaks a *different*
   instance.** Build one isolating fixture per instance, not one representative
   sample.
9. **"Inside or exactly on the boundary" language needs a fixture with a real
   lattice point landing exactly on the boundary (cross-product/distance exactly
   zero), not just near it** — ordinary axis-aligned shapes rarely produce this
   without deliberate construction.

---

## 7. Verification discipline that paid off

Every fact used as ground truth in the final design was independently verified
against a real, running implementation *before* being shipped, never assumed from
memory:

- The FITS reader was verified byte-for-byte against real `astropy.io.fits`
  round-tripping across 180+ random arrays (0 mismatches), including the
  FillOrder/PhotometricInterpretation-analogous edge case of an omitted optional
  tag defaulting correctly.
- The `DQ_BITS` table was independently re-derived from the actual installed
  `stdatamodels` package (not copied from a prior memory or a web search) and
  cross-checked entry-by-entry (0/32 mismatches) before use — this is exactly what
  let the false `ava_review` finding be confidently rejected rather than
  "corrected" into a bug.
- The perimeter (Benkrid-Crookes) and solidity (diamond-offset convex hull)
  formulas, carried over from the PGM/TIFF designs, were verified against real
  `scikit-image` across hundreds of random masks before ever being written into
  `solve.py`.
- Every mutant considered during design (wrong bit, wrong connectivity, wrong
  border-edge check, wrong point-in-hull tolerance, "any bit set" instead of the
  named one) was run against every shipped *and* held-out fixture to confirm
  dormant-on-shipped / caught-on-held-out before being trusted as evidence the
  design was sound.

---

## 8. Distilled summary

Three structurally different task containers were built against Opus-4.8/Terminus-2
in Machine Learning and AI / Computer Vision over two days: multi-tap sensor frame
reconstruction, binary-mask connected-component analysis (twice, with two different
file formats). Every formula-based crux — however real, however numerically
intricate, however many were combined — was solved cleanly the moment it was
disclosed precisely enough to satisfy fairness review, producing five consecutive
"too easy" verdicts. The winning design instead used a real, external, *arbitrary
lookup table* (a space telescope's calibration-pipeline data-quality bit
convention) rather than a formula — the same shape that won a different accepted
task's MDL/CTfile precedent — but only succeeded once two further lessons were
absorbed: the specific convention must be niche enough that the model hasn't
memorized it exactly (TIFF's mainstream tags failed this test; JWST's DQ table
initially didn't either, until a fetch-based bypass was identified and accepted as
unavoidable-but-tolerable variance rather than "fixed" by disabling internet, which
the platform doesn't allow), and an automated reviewer's own findings must be
independently re-verified before being trusted, since reviewers can confabulate
facts exactly the way the tested agents do. Final result: `pass@5 = 0/5`,
`avg@5 = 0.000` — the maximum possible difficulty outcome, and the task's
acceptance.
