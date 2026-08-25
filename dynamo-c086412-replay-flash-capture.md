# dynamo/replay-flash-capture — the QC fix that became the fifth axis, and a two-push 0/5

| | |
|---|---|
| **Outcome** | **ACCEPTED** — every gate green, `accepted` label |
| **Repo** | `dynamo-c086412-hardware-embedded-and-low-level-systems`, branch `submission`, fork `charan-sr` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-c086412-hardware-embedded-and-low-level-systems/pull/1 |
| **Category / sub** | Hardware, Embedded, and Low-Level Systems / **Embedded and firmware** (pre-seeded) — **first task in this subcategory in the corpus** |
| **Benchmarked model** | `task.toml` names Opus-4.8 / Terminus-2; stickies call it `Model A` on Daytona |
| **Final commit** | `775a3ff` (2 pushes) |
| **Headline** | **pass@5 = 0/5 solved, 5 good-valid-fails, avg@5 = 0.000**, every per-trial criterion PASS on all five. pass@2 was 1/2 on push 1 and **0/2** on push 2. Rubric **31/31 on both pushes**. Two pushes total; one blocking gate in the task's whole life. |

Three things worth the read: **§3** (the QC block whose correct fix *was* the difficulty fix — the
only axis added under gate pressure in this corpus that actually gated), **§4** (the axis-ranking
inversion measured three separate times on one task, in three different directions), and **§2**
(why "Embedded and firmware" has a fair-and-hidden middle that `decode-vibration-log` proved a
*fictional* decode format does not).

---

## 1. What the task asks

A production flash programmer's bus logger recorded the SPI traffic between the programmer head and
each board's serial NOR flash. The tool that turned a capture back into the resulting flash image is
gone. The agent writes `/app/replay.py`, invoked `python3 /app/replay.py <capture_path> <image_path>`,
which replays a capture and writes the part's 262144-byte memory array as raw binary.

- **Agent sees:** `instruction.md`, `/app/data/PROGRAMMER.md` (capture format + part geometry),
  `/app/data/sample/capture.txt` (75 transactions), and `/app/data/sample/image.bin` — the image
  that board was verified to hold, i.e. a complete end-to-end self-check on a known-good case.
- **Graded on:** the shipped capture (replayed from a sealed copy under `/tests`) plus **17 held-out
  captures**, exact bytes, all-or-nothing, 19 tests.
- **Capture format:** text. `# ` banner lines, then one line per chip-select interval:
  `<t_us>  <b0> <b1> ...` — the MOSI bytes in bus order, uppercase hex.

**No tolerance class exists anywhere** — the graded artifact is 262144 raw bytes compared for
equality. Same free win `replay-collection-sort` §4.2 got from grading a permutation: pick an output
type with no numeric margin and no gate can reach for a `difficulty_evidence` threshold argument.

---

## 2. The crux, and why this subcategory has a fair-and-hidden middle

`PROGRAMMER.md` documents the **fictional capture container** exhaustively and names the **real
device** as the authority for behaviour, restating none of it:

> "It is an ordinary JEDEC-compatible serial flash and answers the standard 25-series command set.
> The opcodes, the addressing, and the way the device treats each command are the usual ones for
> that family, and are not repeated here."

That is the `emulate-int8-accel` / `replay-collection-sort` shape — **name the authority, enumerate
nothing** — and it is now confirmed in a seventh category. `deep_review`'s oracle-derivation audit
came back *"clean — hard-codes only geometry constants that PROGRAMMER.md states verbatim, and uses
standard JEDEC 25-series opcodes the doc explicitly defers to; no decisive value is non-derivable."*
`qc_gate` B5 never fired once, on either push.

Five real device behaviours decide the answer. All five are ordinary serial-NOR behaviour, all five
are integer-exact, none is stated anywhere the agent can read:

| Axis | Real rule (named-not-restated) | Natural mistake | Inert on the sample because |
|---|---|---|---|
| **A** | a page program's payload goes into a 256-byte page buffer whose column counter increments **only within the page** | stream linearly into the array, running into the next page | every sample program starts page-aligned |
| **B** | programming drives cells **1→0 only**, so a write over live storage is a bitwise AND | `mem[addr] = value` | every sample program lands on freshly erased (0xFF) storage |
| **C** | each program/erase **consumes** the write-enable state | ignore the enable entirely; apply every operation | every sample write cycle carries its own enable |
| **D** | an erase applies to the **whole** sector/block containing the address | erase forward from the given address | every sample erase address is already at its region base |
| **E** | on a payload **longer than a page** the buffer wraps and the **last** byte clocked to a column is programmed | AND each payload byte into the array as it arrives (a "double AND" on wrapped columns) | no sample program exceeds 256 bytes |

**Generator invariants, machine-enforced — `build.py` refuses to write if one breaks:**

1. the shipped sample is **bit-identical** under all five naive readings (measured, not assumed);
2. each naive reading is caught by **≥2** held-out captures (measured 9/8/7/6/3) with a
   **non-hairline effect** (min 41 bytes — the `read-cavity-captures` §"effect size" rule encoded
   as an assertion, not a hope);
3. every **disclosed** mechanic (erase-to-0xFF, sector vs block size, 24-bit big-endian address,
   payload offset) breaks the shipped sample **and** ≥1 held-out capture — `replay-collection-sort`
   §9.1's conclusion encoded before push 1, which is why neither `ava_review` `verifier_coverage`
   nor a `qc_gate` C3 ever fired here;
4. the structural guarantees that keep each axis inert are asserted directly on the sample's
   transaction list (page-aligned, ≤1 page, enable present, erase aligned).

### Why the category matters

`decode-vibration-log` (same category, DSP sub) concluded that for a **fictional** decode format
every rule is either documented → transcribed, or undocumented → unfair, with no fair-and-hidden
middle, and that such a task tops out near one inferred axis ≈ pass@5 2/5. **A real part escapes
that entirely.** The behaviour is in every 25-series datasheet — discoverable, `allow_internet =
true`, and `deep_review` said so — but the agent never consults it because the sample never punishes
the omission. Five axes instead of one, and 0/5 instead of 2/5.

The selection rule that produced these five: **behaviours, not lookups.** Every capture uses only
opcodes the sample already exercises (`06`, `02`, `20`, `D8`, `05`), so there is no "recall a table"
axis anywhere — `experiment-analysis-frame` §3.3's "a table to look up = recalled, not noticed",
applied at fixture-design time.

---

## 3. The one blocking gate — and the fix that bought a fifth axis

Push 1 cleared **everything** except a single `qc_gate` A6:

> *"Oracle deviates from standard 25-series datasheet semantics on a valid page-program that clocks
> >256 data bytes (the part's page-buffer counter wraps and keeps the LAST byte written to each
> column, then programs once). Input: WEL enable (06), then `02 00 00 00` with payload = [0x00] +
> 255x0xFF + …"*

The finding was **correct and entirely self-inflicted.** My reference did `mem[target] &= value`
incrementally per payload byte. That is right for any payload of a page or less and wrong the moment
a column receives two bytes in one transaction — which is exactly the input class my fixtures never
contained. QC constructed it.

**The fix was the difficulty fix.** Modelling the page buffer properly (fill a 256-byte scratch,
last write per column wins, then AND the whole buffer in once) is what the datasheet says, costs
five lines, discloses nothing — and makes the *incremental-AND* implementation a fifth wrong
reading, gradeable by adding held-out captures with long payloads. So the same edit closed the
soundness hole and answered `deep_review`'s advisory in the same breath:

> *Advisory 1 — "Borderline difficulty for the pass@5 gate… the task may under-produce fails against
> the pass@5 ≥3/5 gate — worth watching so pass@5 spend isn't wasted."*

**And axis E took down a trial.** `task__JjkRzLp` implemented AND *and* the write-enable latch
correctly — it would have solved the push-1 task — and failed on h15/h16/h17 with the double-AND.
This is `emulate-int8-accel` §4's rounding-tie fixtures repeating: **closing a QC coverage hole can
buy real difficulty.** It is also the *first* case in this corpus of a gate-driven axis actually
gating, against `replay-collection-sort` §headline-2's "a gate-driven axis is coverage, not
difficulty." The distinction worth carrying: there, the gate-driven axes were *new rules bolted on
to satisfy a probe*; here, the gate found the reference **wrong about the mechanism the task was
already about**, so fixing it deepened the existing crux rather than adding a sibling.

**Three checks that made this a cheap fix rather than a redesign, all run before committing:**

- the new model is a **strict superset** for payloads ≤ 1 page — verified by `cmp` on the shipped
  image and all fourteen original held-out images, every one byte-identical. *Verified, not assumed*;
  had any changed, the fix would have silently rewritten ground truth the gates had already seen.
- the reference and the generator's independent model agree on all 18 captures (`calibrate.py`);
- all five naive readings plus a copy-the-answer probe score **0.000 through the real verifier**.

Folded into the same push, since a push was happening anyway: the rubric's one borderline note
(`solution_quality` — "`solve.py` carries the ~60-line `replay.py` as an embedded raw-string…
resembles a large file inlined as a heredoc"). `solution/replay.py` became a standalone file that
`solve.sh` copies into place. Rubric stayed 31/31.

---

## 4. The axis-ranking inversion, measured three times on one task

The corpus's most-repeated finding, and this task is the cleanest demonstration of it yet, because
the *same five axes* produced three different answers on three consecutive measurements:

| Measurement | What actually gated | What gated nothing |
|---|---|---|
| **pass@2, push 1** (1/2) | **C** (write-enable latch) — the sole cause, 6 fixtures | A, B, D — the passing trial got all three right |
| **pass@2, push 2** (0/2) | **B** (AND semantics) — both trials | C — both trials tracked the latch correctly |
| **pass@5, push 2** (0/5) | **B** (4 of 5), **C** (2 of 5), **E** (1 of 5) | **A and D never gated at all** |

Axes A (page wrap) and D (erase alignment) — the two I designed the task around first, and would
have called the strongest — **never took a single trial across nine independent agents.** Axis B,
which I nearly regarded as the obvious one every embedded engineer knows, took 4 of 5.

Do not try to predict this. Build every axis you can make inert and fair, ship them all, and read
the value tables afterwards. Two-trial `pass2` cannot see a 20% failure mode, and it named a
*different* sole cause on each of two consecutive pushes of nearly the same task.

### What the graders said the agents did

> *"All five agents validated only against the shipped sample capture, which the task authors
> deliberately constructed so that every program starts on a page boundary, fits in one page, lands
> on freshly erased storage, and carries its own write enable — exactly the conditions that render
> all three divergences invisible. Every agent confirmed a byte-for-byte match and declared the task
> complete without constructing or reasoning about synthetic edge cases."*

That is the design premise read back verbatim by the analysis, which is the strongest form of
`difficulty_crux: PASS` available. `near_miss` came back PASS on 4 of 5 (FAIL on the one trial that
missed only axis E) — structurally wrong, not marginal.

Failure stratification (`h16` failed in **all five**; `h01/h03/h04/h09/h12/h13/h14` in four;
`h17` in three; `h05/h06/h10/h11` in two; `h15` in one) is exactly the shape
`rebuild-lumenp-plates` §"build cruxes that compose" recommends — **the combined fixtures are the
ones that fail in every failing trial.** `[shipped]`, `[h02]`, `[h07]`, `[h08]` never failed:
single-axis fixtures for the axes nobody got wrong.

---

## 5. Gate-by-gate log

| Push | Commit | Result |
|---|---|---|
| 1 | `f3d3383` | static ✅ 25/25 · **rubric ✅ 31/31 first time** · cosine_similarity ✅ · similarity ✅ UNIQUE · validation ✅ · **pass2 ✅ 1/2** (1 solved · 1 valid-fail, Rerun NO) · deep_review ✅ (2 advisories) · ava_review ✅ · tier1 ✅ · qc_eval ✅ · qc_exec ✅ · **qc_gate ⛔ A6** (page-buffer semantics on a >256-byte program) → trials skipped |
| 2 | `775a3ff` | page-buffer model in reference + generator; h15/h16/h17 added; `solution/replay.py` standalone; README + `task.toml` synced. **Everything ✅** — rubric 31/31 again, **pass2 0/2 (2 valid-fail)**, deep_review ✅, ava_review ✅, qc_eval/qc_exec/**qc_gate ✅**, tier1 ✅, **trials ✅ pass@5 0/5, avg@5 = 0.000, 5 good-valid** → **`accepted`** |

Timings: pass2 13m, qc_eval ~11m, deep_review 4m, ava_review 6m, trials ~24m; a full cycle ≈ 1h.
**Zero platform faults across both pushes** — no 429, no outage, no stale sticky, no rerun needed.

---

## 6. What passed first time, and why

Everything except the one A6. The pre-push work that bought that, all done *before* submitting
rather than in response to a block:

- **Verifier soundness** (`ava_review` + `deep_review` PASS on both pushes, first time): expected
  images planted by the **generator**, never recomputed from the capture; `/tests` sealed 0700 and
  `/app/data` sealed `go-rwx` **at grading time** in `test.sh`; the graded program run as `nobody`
  (setgroups/setgid/setuid); each capture staged into a fresh scratch dir under a **neutral**
  filename (`input.txt`) so nothing identifies the sample; output read `O_NOFOLLOW` from a path
  created fresh per case; `/app/replay.py` copied root-owned before the run so the agent's own
  permissions can't stop it.
- **The copy-the-answer attack performed, not argued** — a probe that `shutil.copyfile`s
  `/app/data/sample/image.bin` scored 0.000 with a live `PermissionError` in the log. Sealing at
  *grading* time leaves the agent's development self-check untouched, which is what makes the green
  feel earned (`merge-lora-adapters` §4.5).
- **Invariant 3 encoded in the generator before push 1** — `replay-collection-sort` §9.1's exact
  parting advice. Two of that task's three gate blocks were this rule unencoded; here it cost zero
  cycles.
- **`difficulty_explanation` naming synthetic provenance and a real-world audience** in the first
  draft — `decode-vibration-log` and `filer-access-audit` both lost push 1 to this.
- **`.dockerignore` present from commit 1**, `.gitattributes` `* text=auto eol=lf` + `*.bin binary`,
  `jobs/` gitignored, **no `"You have N seconds"` line**, no `task/README.md`, instruction ~450
  tokens against the 1500 cap.

---

## 7. Bugs I introduced myself

1. **The A6 page-buffer bug** (§3) — the reference modelled programming as an incremental AND, which
   is indistinguishable from the truth on every payload ≤ 1 page. My own mutant battery never caught
   it because my mutants modelled *wrong implementations*, not *unmodelled input classes*. Same
   shape as `replay-rungear-runs`' "my mutants modelled wrong implementations nobody would write."
   **Enumerate the input space, not just the reading space.**
2. **First verifier run scored 0.000 for the oracle** — the scratch dir was root-owned 0755, so
   `nobody` could not create the output file. Fixed by `os.chown`ing the workdir to `nobody` and
   running a root-owned *copy* of the agent's program.
3. **A non-deterministic `render()`** — the capture renderer seeded its timestamp RNG from
   `self.rng.random()`, consuming generator state, so calling it twice produced different
   timestamps and the sealed `/tests` copy of the sample did not match the shipped one. Caught by
   `diff`ing the two copies; fixed with a seed derived from the session seed.
4. **`task.toml` kept a stale "fourteen held-out"** in `verification_explanation` after the count
   went to seventeen. Found by **grepping** for the stale numbers, not by re-reading the prose —
   `replay-collection-sort` §9.3, confirmed again.
5. **Nearly committed a mutant as the reference.** `mutants.sh` rewrites `solution/replay.py` in
   place and restores it in an `EXIT` trap; it ran in the background while I was editing README and
   `task.toml`. Re-checked `git diff` on the reference and re-ran the oracle *after* the sweep
   finished, before `git add`. `wetland-nitrate-effect` §"a mutant battery owns solve.py while it
   runs" — the trap is not a substitute for checking.

---

## 8. Reusable checklist

Design:
- [ ] For a hardware/firmware task, emulate a **real part** whose behaviour a benign session can
      hide, not a fictional one. A fictional format is transcribe-or-unfair
      (`decode-vibration-log` §6); a real part is *discoverable but dismissable*, which is the
      mechanism.
- [ ] Choose **behaviours, not lookups**. Restrict held-out captures to opcodes/fields the sample
      already exercises so no axis is "recall a table."
- [ ] Pick an output type with **no numeric tolerance** — raw bytes, an ordering, an id list.
- [ ] Name the standard in a file **inside `/app`** (satisfies B5 — `instruction.md` alone does not,
      Harbor hands it over as the prompt and the QC probe never sees it) and restate nothing.
- [ ] Machine-enforce, in the generator, refusing to write on failure: sample bit-identical under
      every naive reading · each caught by ≥2 held-out with a non-hairline effect · **every
      disclosed mechanic breaks the sample AND ≥1 held-out** · the structural property keeping each
      axis inert asserted directly.
- [ ] Build every fair inert axis you can and **do not budget on your ranking of them** — measured
      wrong three times on this task alone.

Verifier / QC:
- [ ] Ground truth **planted by the generator**, never recomputed from the input.
- [ ] Seal `/tests` *and* the agent-visible answer at **grading** time; grade the shipped case
      against a sealed copy; stage inputs under **neutral names**; run as `nobody`; `O_NOFOLLOW`.
- [ ] **Perform every attack as a committed probe** through the real verifier, don't argue it.
- [ ] Enumerate the **input space** your fixtures don't reach (payloads longer than a page, zero
      length, boundary addresses), not just the wrong readings. QC constructs those.
- [ ] Before believing a fix is a superset, `cmp` every previously-generated expected artifact.

Process:
- [ ] `.dockerignore` from commit 1; no `"You have N seconds"` line; no `task/README.md`;
      `difficulty_explanation` names provenance + audience.
- [ ] `git diff` the reference and re-run the oracle **after** any background mutant sweep, before
      `git add`.
- [ ] **Grep** README/`task.toml` for stale counts; never re-read prose to check numbers.
- [ ] Read `gh pr checks`, never the label — `needs-revision` persists through a green re-run until
      the cycle finishes.
- [ ] Fold cheap advisory fixes into the push a blocking finding forces; don't spend a push on them.

---

## 9. One-paragraph version for future me

First "Embedded and firmware" task in the corpus, **accepted in two pushes at pass@5 0/5, avg@5 =
0.000, 5 good-valid failures**, with the rubric at 31/31 on both pushes and exactly one blocking
gate in the task's entire life. The design is the proven recipe transplanted onto a **real serial
NOR flash**: replay a bench logger's SPI capture into the part's final image, document the
(fictional) capture container exhaustively, name the standard 25-series command set as the authority
for device behaviour and restate none of it, then build the shipped programming session so that
every place a NOR flash stops behaving like a writable byte array is inert — every program
page-aligned, inside one page, onto freshly erased storage, with its own write enable, and every
erase already at its region base. This is the escape from `decode-vibration-log`'s conclusion that a
*fictional* decode format has no fair-and-hidden middle: a **real part's** behaviour is one lookup
away and `deep_review` confirms it is derivable, yet all five agents matched the sample byte for
byte and quit without ever consulting it. The single `qc_gate` A6 was correct and self-inflicted —
the reference ANDed each payload byte into the array as it arrived, which is wrong the moment a page
program clocks more than 256 bytes and the buffer's column counter wraps — and the correct fix
(model the page buffer, last write per column wins) **was also the difficulty fix**, because it made
incremental-AND a fifth wrong reading and the three held-out captures added to grade it took down a
fifth-trial agent that had solved everything else. That is the first gate-driven axis in this corpus
to actually gate, and the reason it did is that the gate found the reference *wrong about the
mechanism the task was already about*, rather than demanding a new sibling rule. The most useful
data the task produced is the ranking inversion measured three separate times on one design: pass@2
push 1 said the write-enable latch was the sole cause, pass@2 push 2 said AND semantics was, and
pass@5 said AND (4/5), latch (2/5) and page-buffer (1/5) — while page-wrap and erase-alignment, the
two axes the whole task was designed around, never gated once across nine independent agents.
