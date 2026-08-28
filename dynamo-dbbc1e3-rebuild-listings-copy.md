# dynamo/rebuild-listings-copy — the sample as an equivalence class, and the byte you must *not* grade

| | |
|---|---|
| **Outcome** | **ACCEPTED** — `pass@5 = 0/5`, `avg@5 = 0.000`, 5 good valid fails (maximum difficulty outcome) |
| **Repo** | `dynamo-dbbc1e3-file-and-media-operations`, PR #3, branch `submission`, fork `Pruthviraj374` |
| **Category / sub** | File and Media Operations / **Text editing and manipulation** (pre-seeded) |
| **Benchmarked model** | reported as `Model A` (`task.toml` names Opus-4.8 / Terminus-2) |
| **Final commit** | `4776a25`, after **3 pushes** |
| **Headline** | **Three pushes, no redesign.** `pass2` returned 0/2 on the *first* push and again on every later one, because the agent-visible bytes never changed after push 1. The two blocks were both verifier-side, and both were fixed by making the graded set *narrower* — deleting a contested byte, then grading a clause the instruction already stated. |

The fifth File and Media Operations entry (after `recover-zip-headers`, `rebuild-plate-rasterizer`,
`restore-stillwater-volumes`, `keepcase-restore`) and the first for **Text editing and
manipulation**. Disjoint from all four: no shared artifact (a DVB service-information feed vs. a
zip container, a prepress spool, a filesystem dump, an archival snapshot), no shared authority
(ETSI EN 300 468 / ISO/IEC 6937 vs. PKWARE APPNOTE, ISO 32000-1, POSIX), and the difficulty is
character-set decoding rather than replaying recorded state onto a filesystem.

---

## 1. The task

The listings desk at a regional broadcaster ran COPYFIT, which turned the nightly schedule feed
from the playout system into the page that went to the printer. The program is gone; the feed
archive and the desk's format note survived.

- **Agent sees:** `/app/data/FEEDFMT.md` (the invented `AGSF` container documented field by
  field, plus the page layout and the conditioning/filling rules), fifteen archived feeds under
  `/app/data/sample/`, and the page COPYFIT set from each under `/app/data/pages/` — a complete
  end-to-end self-check.
- **Agent produces:** `/app/copyfit.py`, run as `python3 /app/copyfit.py <feed_dir> <out_dir>`,
  plus a worked run left at `/app/output/sample`.
- **Graded on:** 39 held-out feeds staged under SHA-salted opaque names, byte for byte,
  all-or-nothing per page, as `nobody` with site-packages dropped.

The container, conditioning and filling are documented exhaustively. What the note does **not**
reproduce is how a text field's bytes become characters: it names ETSI EN 300 468 annex A and
stops, because the desk never re-coded the fields.

---

## 2. The crux, and the invariant that makes it work

Three consequences of the named annex decide the held-out pages:

1. A field with no leading selector is in the DVB default table (**ISO/IEC 6937**), *not*
   Latin-1.
2. A one-byte selector `N` selects **ISO 8859-(N+4)**, not part `N`; parts 1–4 are reachable
   only through the three-byte `0x10 0x00 nn` form, where `nn` *is* the part number.
3. Bytes `0xC1`–`0xCF` are diacritical marks coded **mark-first** — the accent byte precedes
   the letter it belongs to — and the pair composes to NFC.

**The invariant: every shipped field sits in the equivalence class where the right and wrong
readings agree.** High bytes in shipped default-table fields are drawn only from positions
ISO 6937 and Latin-1 share; shipped selector-introduced fields carry plain ASCII, which every
8859 part encodes identically. So all fifteen worked pages render byte-identically under all
three misreadings. The grader's own words:

> Both agents received a false-positive signal from the 15 shipped sample pages, which were
> engineered to reproduce identically under correct and incorrect (Latin-1) readings, giving no
> corrective gradient.

This is `rebuild-plate-rasterizer` §4.2 applied deliberately — *omission leaves the agent
uncertain; equivalence makes it confident*. The sample is not merely silent about the crux, it
actively certifies a wrong implementation as correct.

### Why a *recalled* table worked here, against the corpus's own advice

`experiment-analysis-frame` §3.3 and `nfs4-access-audit` §3.1 both say an axis in a format's own
vocabulary is **memorised** and will be solved, while a prose exception is **noticed**. A
character-set lookup table is about as memorised-looking as an axis gets, and I nearly cut it.
It held anyway, and the reason is worth recording: **the model's recall of ISO 6937 is
confidently wrong, not absent.** Across the five trials it produced `0xD0→U+2014` (correct:
U+2015) and `0xE2→U+00D0` (correct: U+0110) — plausible near-neighbours of the right answer,
emitted with no hesitation. `rebuild-mask-hierarchy` §6 corollary 2 predicts exactly this and is
the entry that should be read first: *a format's headline fields should be assumed mastered;
look at genuinely niche conventions.* ISO 6937 is ubiquitous in name and almost never
implemented from memory correctly.

The `+4` selector offset is the stronger half, and it is not a table at all — it is an
**arbitrary historical artifact** (the one-byte space starts at 8859-5 because 8859-1 through -4
predate it), so there is nothing to derive and the natural assumption, `N → part N`, is wrong.
It took down 3 of 5 trials. **A rule with no derivable logic behind it beats a rule the model
can reconstruct**, which is `collate-modpool-batches`'s derivability filter seen from the other
side.

---

## 3. Dead ends — killed on paper, before any code

Applying `request-preconditions` §3's local-oracle test up front cost about twenty minutes and
saved at least two cycles.

**a) Terminal emulator (DEC deferred wrap).** Already recorded as a dead end in
`request-preconditions` §3(c). Did not re-litigate.

**b) Anything with a pip-installable exact oracle.** `pip install jsonpatch`, `semver`,
`pyte` — `request-preconditions` §3(d). Checked this against my own design and it is the one
place the task is genuinely exposed: **`tsduck` implements exactly this decode**, and
`rebuild-mask-hierarchy` §5b records a trial that fetched a package's raw source from
`raw.githubusercontent.com` with no `import` at all, defeating every runtime guard. I accepted
the risk on the evidence in that same entry — four of five pass@2 samples there failed
genuinely — and it never fired: **no trial in seven (2 + 5) fetched a reference implementation.**
One trial (`task__YQbLPNE`) spent its entire budget on HTTP requests to ETSI, Wikipedia and
Unicode and still never wrote a line of code. *Internet access being available is not the same
as the model using it well.*

**c) Making the difficulty a *search*.** `celstage` §1. The decode is a lookup, not a search;
every trial finished confidently and wrong, which is the shape that yields valid failures.

---

## 4. What actually worked

| Decision | Source | Effect |
|---|---|---|
| Plant ground truth in the generator, never parse it back | `reassemble-tap-sessions` §4 | `oracle = 1.000` measures the decoder rather than restating it; the reference and the fixtures share no code path |
| Ship a *complete-looking* self-check that is silent on the crux | `contact-export` §9, `merge-lora` | 15 worked pages covering every container and layout rule, and nothing about the decode |
| Group the held-out feeds by axis | `repair-portal-dispatch` §3(c) | One wrong reading fails its own test, not all of them; a control group (h01–h06) passes under *every* misreading, so nothing is failed by shape alone |
| Build `calibrate.py` before the first push | `reduce-palaeomag` §4.4 | Asserts each misreading is invisible in all 15 shipped feeds and caught by 3–14 held-out ones — the assertion QC would otherwise make for me, a cycle later |
| Build `probe.py` — variants through the **real verifier** in the **real image** | `rebuild-uptime-rollups` §4.4 | Catches what page-diffing cannot: which *test* fails, and whether the run crashes. Directly produced two verifier fixes (§5) |
| Probe the **accept** side, not only the reject side | `contact-export` §3.3 | Became the fix for the one blocking QC finding (§5.1) |

---

## 5. Gate-by-gate log

### Push 1 — `0cc731d`: everything green except one QC probe

`changes`, `ratelimit`, `validation`, `tier1`, `similarity`, `cosine_similarity`, `review`
(31/31), `deep_review`, `ava_review`, `qc_exec`, `qc_eval`, **`pass2` (0/2, both valid)** — all
pass. `qc_gate` blocked on **1 of 37** probes.

Similarity headroom, for calibration: instruction **0.697**, verifier **0.786**, fingerprint
**0.780**; lexical vs TB2/TB3 topped out at **0.120** (`cobol-modernization`). Comfortably under
the ~0.87 budget `repair-portal-dispatch` §3(d) warns about.

### 5.1 `qc_gate` B5 — and why the fix was *deletion*, not disclosure

> Rival rule = plain ISO/IEC 6937 (0xA4→U+00A4 currency sign instead of DVB Euro U+20AC)
> reproduces all 15 sample pages byte-for-byte but is rejected on held-out: h07…

**The finding was narrower than it first read, and reading it precisely was the whole fix.** QC
had *already derived* ISO 6937 from the annex citation unaided — it never disputed the Latin-1
axis. It disputed one byte: DVB's amendment putting € at `0xA4` where plain ISO 6937 has a
currency/dollar sign.

The instinct is to answer B5 with prose or with a witness. Both are recorded failures —
`retired-normalizer` §3.2 lost three cycles to added prose, and `replay-strata-plans` §3.2 shows
a sentence naming the area flipping pass@2 to 2/2. Worse here: a `0xA4` witness in the sample
would show `€`, which teaches *both* the Euro rule **and** that the table is not Latin-1 — the
sample would have taught my strongest axis.

**So I deleted the position instead.** `replay-rungear-runs` §3.3: *if a mutation is provably
equivalent, delete the branch and assert the equivalence; do not argue it in prose.*

- `gen.py` now **refuses** to place `0xA4` in any default-table field (an assertion, not a
  convention I might forget).
- `calibrate.py` moved that reading from MUTANTS to a new **MOOT** class asserting it changes
  **zero** pages of 54 — the inverse assertion to every other variant.
- `probe.py` gained an **ACCEPTED** class: the plain-6937 reading must score **1** through the
  real verifier. Two tightenings in `contact-export` §3.3 rejected correct solvers; probing the
  accept side is how that is caught.

Cost: the weakest axis (3 held-out feeds). Kept: Latin-1 (14 feeds), marks (6), one-byte
selectors (8), three-byte (5). `0xA8` carries the same Latin-1 split while reading identically
under both 6937 variants, so h07 was rewritten around it and lost nothing.

`deep_review` later cited the fix approvingly, unprompted:

> the single genuinely-ambiguous position (0xA4) is excluded from grading and probed to accept
> both readings — the accept side is probed as carefully as the reject side.

**Generalisation: when a discoverability gate names one position, check whether that position can
simply stop being graded. "Both readings are correct here" is a stronger answer than any
sentence, and unlike disclosure it costs nothing that was load-bearing.**

### 5.2 Push 2 — `bb08aee`: `pass2` passes again, `ava_review` blocks

`pass2` **passed a second time**, 0/2, both valid, 43–48 min of 60. `review` and
`cosine_similarity` passed again, confirming the prose edits stayed inside budget.

Then: **`ava_review` BLOCK, `deep_review` PASS with zero blocking issues**, and AVA's only
blocking bullet reading *"see the deep-review comment"* — which contained nothing blocking.

This is `reduce-palaeomag` §5.1's routing quirk exactly, and the corpus entry is the only reason
it cost minutes instead of a cycle: **the `Routing: block · flagged by: AVA` footer is
authoritative, and the blocker is the finding printed under the *advisory* heading.**

Advisory 1 was a real hole, and an embarrassing one: `instruction.md` says *"ignore anything in
`<feed_dir>` that is not an `*.agsf` file"*, and **every graded directory contained only feeds.**
A disclosed rule with no fixture is this corpus's single most-repeated defect
(`replay-collection-sort` §3.2, `reassemble-tap-sessions` §6).

### 5.3 Push 3 — `4776a25`: witness the ignore clause

The held-out directory now carries `MANIFEST`, `notes.txt` and `s99.agsf.bak`; the run must skip
all three and still exit 0. A new probe variant drops the extension filter and fails that test
**and no other**, so the new assertion is itself witnessed.

**Deliberately not staged: a malformed `*.agsf` file.** The instruction never promises the
archive contains one, so failing a submission on it would be `request-preconditions` §5's B4 —
enforcing a requirement the agent's own contract never gave it.

**Deliberately not done: anything about Advisory 3.** `deep_review` flagged that the pass rate
"may sit at the margin" because reward is all-or-nothing over a recalled table.
`repair-edge-compression` §6 says act on difficulty advisories before `trials` spends — but
`lumenp` §3 and `request-preconditions` §3(e) say piling on mechanisms is the classic wrong
response, and any new mechanism meant editing `FEEDFMT.md`, changing the agent-visible surface
that had just produced 0/2 **twice**. I held the design. pass@5 came back 0/5, and
`pass2_suggestion` skipped — the pipeline saw no difficulty suggestion worth making.

### 5.4 Final

| Gate | Verdict |
|---|---|
| every static / similarity / rubric gate | pass |
| `pass2` | **pass — 0/2**, both valid |
| `qc_gate` | **pass** (37 probes) |
| `ava_review`, `deep_review` | pass |
| **`trials`** | **pass@5 0/5 · avg@5 = 0.000 · 5 good valid fails** |
| `gate` | pass → **`accepted`** |

`difficulty_crux`, `approach_validity`, `reward_hacking`, `task_specification`, `refusals`,
`low_timeout`: **PASS on all 5 trials.** `near_miss` FAIL on one trial (11/12 tests, two wrong
table constants) — per `rebuild-plate-rasterizer` §6 that is reviewer judgement, not a defect,
and the analysis says so itself: *"the 4 PASS judgments confirm most agents miss by conceptual
gaps rather than a threshold doing unfair work."*

---

## 6. What the five trials actually did

| Divergence | Correct | Agent | Trials |
|---|---|---|---|
| One-byte selector offset | `N` → 8859-(N+4) | `N` → 8859-N | **3 of 5** |
| ISO 6937 `0xD0`, `0xE2` | U+2015, U+0110 | U+2014, U+00D0 | **3 of 5** |
| `U+008A` in Unicode-coded fields | paragraph separator in *every* path | split on `\n` only | **3 of 5** |
| Default table | ISO 6937 | Latin-1 | 1 |
| Mark-first composition | compose with following byte | prefix emitted raw | 1 |
| Three-byte part 16 | 8859-16 supported | dict ends at `0x0F`, raises | 1 |

Two observations worth carrying forward:

1. **The axis I ranked weakest gated hardest.** I nearly cut the selector offset as "just a
   mapping"; it took down 3 of 5. `rebuild-uptime-rollups` §6 — *your ranking is probably
   inverted* — is now confirmed a fourth time. **Never cut an axis on your own ranking.**
2. **`U+008A` was never designed as an axis at all.** The break code is fully documented in
   `FEEDFMT.md`; what agents missed is that it must be handled in the *Unicode* decode paths
   too, not only the default table. It emerged from the interaction of two disclosed rules —
   `lumenp` §4's *build fixtures that combine cruxes* — and gated 3 of 5. **Cross-path coverage
   of a disclosed rule is free difficulty; add it deliberately next time.**

---

## 7. Reusable checklist

- [ ] Restrict every shipped fixture to the **equivalence class** where right and wrong readings
      agree, and *assert it* — not "the crux is absent" but "the sample certifies the wrong
      answer".
- [ ] Write `calibrate.py` (page-level: silent on sample, caught held-out) **and** `probe.py`
      (variants through the real verifier in the real image) **before** the first push.
- [ ] Give `probe.py` an **ACCEPTED** class from the start. A defensible alternative reading must
      score 1, and that is what answers a discoverability gate.
- [ ] When a gate names one byte/field/position, ask whether it can stop being graded before
      writing a word of defence.
- [ ] Grade every clause the instruction states, including the boring ones ("ignore files that
      are not X"). Un-witnessed disclosed clauses are the most-repeated finding in this corpus.
- [ ] Never stage an input shape the instruction does not promise exists (a malformed feed) — B4.
- [ ] Prefer an axis with **no derivable logic** (an arbitrary historical offset) over one the
      model can reconstruct.
- [ ] Cover a disclosed rule across **every code path** it applies to, not just the obvious one.
- [ ] Check `instruction.md` and `environment/` are byte-identical before each push after a green
      `pass2`; if they are, a swing is variance, not regression.
- [ ] Do not act on a "difficulty may be marginal" advisory by adding a mechanism that changes
      the agent-visible surface.

---

## 8. In one paragraph

A DVB service-information text decoder, accepted in three pushes at **pass@5 0/5, avg@5 0.000**,
with no redesign and with `pass2` returning 0/2 on the first push and every push after. The
design rule that carried it: **the sample is not silent about the crux, it is an equivalence
class that certifies the wrong reading** — all fifteen worked pages render identically under
Latin-1, under selector-as-part-number, and under mark-after-letter, so an agent that validates
end to end gets a green light for an implementation that fails 33 of 39 held-out feeds. Both
blocking findings were verifier-side and both were fixed by grading *less*: a QC B5 on the one
byte where DVB's table and plain ISO 6937 genuinely disagree was answered by **deleting that byte
from every graded field and proving the two readings interchangeable** — including a probe that
requires the alternative to score 1 — rather than by disclosing a rule or arguing in prose; and
an `ava_review` block (whose bullet pointed at a `deep_review` that had passed — read the routing
footer) was answered by finally grading a clause the instruction had stated all along. The axis I
ranked weakest, an arbitrary `+4` selector offset with no logic to derive, gated 3 of 5 trials,
while a rule I never counted as an axis at all — a documented line-break code that also applies
in the Unicode decode paths — gated another 3.
