# dynamo/rebuild-plate-rasterizer — the crux the model can look up vs the one it must notice

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 17 checks green, `accepted` label |
| **Repo** | `dynamo-5e2808b-file-and-media-operations`, branch `submission` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-5e2808b-file-and-media-operations/pull/1 |
| **Category / sub** | File and Media Operations / Image and design processing (pre-seeded) |
| **Benchmarked model** | reported as `Model A` (`task.toml` names Opus-4.8 / Terminus-2 — fixed dataset fields) |
| **Final commit** | `5a87949` |
| **Headline** | **pass@5 = 0/5 solved, 5 good valid fails, avg@5 = 0.000.** Four pushes. `qc_gate` passed first time; the rubric passed 31/31 on the *first* push and every push after |

The second File and Media Operations entry in this corpus (after
`dynamo-e4cc57f-recover-zip-headers`, sub-category Recovery and repair), and the first for
Image and design processing.

---

## 1. What the task asks

A trade shop rasterised press-ready CMYK separations with an in-house RIP, PLATEWRIGHT.
The program is gone; the spool archive survived.

- **Agent sees:** `instruction.md`, `/app/SPOOL.md` (the shop's note on the invented `SPL1`
  spool container and `PLT1` plate set) and `/app/samples/` — 16 archived jobs, each a
  `jNN.spl` spool plus the `jNN.plt` plate set the RIP produced from it.
- **Agent produces:** `/app/render.py` exposing `render(source: bytes) -> bytes`.
- **Graded on:** the 16 archived jobs plus **39 held-out spools** (`tests/fixtures`, never
  shipped), **byte-exact, all-or-nothing**, 55 pairs across 6 tests.

A spool is a flattened list of fill objects: a flags byte (bit 0 = overprint), a colour-space
byte (DeviceCMYK with four tints, or a Separation naming one of the four plates with one
tint), and a path of moveto/lineto/closepath/rect operators in 1/8-pixel integer units. The
header carries the plate size and the overprint mode (`OPM`).

---

## 2. The crux, and the invariants that keep it alive

**The design rule, stated once:**

> **The container is invented and specified exhaustively. The imaging model is real,
> named, and deliberately not restated — and the shipped archive is built to reward the
> wrong reading of it.**

ISO 32000-1 §11.7.4, verbatim (this sentence *is* the task):

> Painting an object causes some specific set of device colorants to be marked, **as
> determined by the current colour space** and current colour in the graphics state. The
> remaining colorants shall be either erased or left unchanged, depending on whether the
> overprint parameter is false or true. **When the current colour space is DeviceCMYK**, the
> overprint mode parameter additionally enables this selective marking of colorants to be
> applied to individual colour components according to whether the component value is zero
> or nonzero.

Because the plate set is CMYK, the obvious simplification is to **widen** a Separation into
a DeviceCMYK quadruple with zeros in the other three slots and run one unified ink model.
That reproduces **the entire 16-job archive**. It diverges on exactly two configurations,
neither of which the archive contains:

| Held-out configuration | Correct | Widened reading |
|---|---|---|
| overprinting Separation, tint 0 | marks its own plate with 0, leaves the other three | paints nothing at all |
| overprinting Separation, overprint mode 0 | still leaves the other three alone | erases the other three |

Two supporting axes: **overprint mode is a header field** (every archived spool where it
could matter carries mode 1, so hardcoding costs nothing there), and **`f` fills by
non-zero winding** where the reflex is ray-casting parity.

**Invariants, machine-enforced in `tools/generate_fixtures.py`, which refuses to write a
shipped job that breaks one:**

1. no archived overprinting Separation object has tint 0, **and** no spool carrying
   overprint mode 0 contains an overprinting Separation at all — the two divergent
   configurations. Separations with tint 0 *do* appear (`j10`, `j16`) under knockout, where
   both readings agree;
2. no archived overprinting DeviceCMYK object has a zero tint, so the exemption never
   fires — while archived objects that are **not** overprinting do carry zero tints and
   visibly knock out (`j04`, `j10`), teaching the wrong generalisation;
3. every archived object's winding number stays in {−1, 0, +1} at every pixel centre, so
   parity and non-zero winding paint identical pixels on all 16 plates. Negative rectangle
   extents appear (`j07`–`j09`) but never nested, so the direction they carry never shows;
4. no path edge passes through a pixel centre (exact integer check), so no graded pixel can
   turn on a tie;
5. a **corpus-witness** check requires the archive as a whole to exercise every non-crux
   feature: both colour spaces, all four colorants, overprint set and clear in each space,
   both overprint modes, a Separation carrying tint 0, all four opcodes, negative `w`/`h`/
   both, clipping at all four edges, multi-subpath objects, off-plate objects, a 12-object
   job, every separation.

---

## 3. Dead ends — with the graders' own wording

### 3.1 The first design: two real rules, both *named* in the spec. Solved 2/2.

Push 1 shipped a DeviceCMYK-only container whose note named the `f` operator and the `OPM`
parameter and said ISO 32000-1 governs them. Every gate passed — static 25/25, rubric
**31/31**, duplicate UNIQUE, validation — and then:

> **pass@2: 2/2 passed.** … "Correctly identified **nonzero winding rule** from the PDF `f`
> operator reference… Correctly implemented **OPM=1 overprint zero-tint suppression**."

The difficulty suggestion named the root cause exactly:

> `SPOOL.md` explicitly tells the agent "PLATEWRIGHT implemented ISO 32000-1 … the operator
> and graphics-state parameters named below behave exactly as that standard defines them."
> Both agents resolved both cruxes from training-data knowledge of PDF, not from
> reverse-engineering the archive; the 14 samples were never needed to disambiguate them.
> **The single highest-leverage move is making the decisive rule non-derivable from the
> standard** — right now both cruxes fail that test.

Agents finished in 9.5 and 26 minutes of a 60-minute budget.

**The generalisation this bought:** `experiment-analysis-frame` §3.3's memorised-vs-noticed
test applies to *pointers*, not just to content. A rule can be real, published and
conditional and still be pure recall if the spec names the parameter that indexes it. Naming
`f` and `OPM` turned the task into two lookups.

### 3.2 Candidates rejected on paper, using this corpus

| Rejected candidate | Rejected because | Corpus source |
|---|---|---|
| Invent a PLATEWRIGHT *deviation* from ISO 32000-1 (what the pass@2 suggestion proposed) | an invented rule must be disclosed or `qc_gate` B5 blocks it; disclosed, it gets implemented. And a deviation the archive *reveals* is one the agent iterates to fit | `lumenp` §3, `sweep-replay` §5.1 |
| DeviceGray overprint semantics (does a gray object mark only K, or all four?) | genuinely contested — a reviewer can defend either reading. Ambiguity, not difficulty | rubric `unambiguous` |
| DeviceRGB→CMYK conversion as an axis | the undercolour-removal formula is not single-valued across implementations | `sweep-replay` §3 |
| A non-standard tie-break on edges grazing a pixel centre | one pixel of divergence → `deep_review` "threshold artifact" | `experiment-analysis-frame` §3.5 |
| PBM/BMP-style row padding | conditional but reflexive — every writer pads without thinking | `lumenp` §6 |
| Removing the archive's expected plates to stop iteration | the plates *are* the container's specification; the task stops being solvable | — |

### 3.3 `ava_review` blocked twice on the same file, for two different reasons

**Round 1** — four blocking items. Three were `verifier_coverage` probes whose evidence lines
state expected and actual behaviour *identically* ("expected non-zero winding: inner region
stays filled… the verifier would instead winding accumulation keeps inner filled"). Those are
`reassemble-tap-sessions` §6's inconclusive probe: a report that the ambiguity was removed,
not that one exists. **Read the evidence line, not the headline** — they disappeared on the
next push with no change addressing them.

The fourth was real: the guard's `elif` chain named only process and network events, so
`os.listdir` / `os.scandir` / `os.walk` / `os.chdir` on the protected trees went through.
Enumeration was not refused, only reading.

**Round 2** — one blocking item, and my round-1 fix was the wrong *shape*:

> hook only raises on `event.startswith(<listed prefixes>)`; no 'ctypes' family and **no
> default-deny**. Any unlisted audit event (**or a C call that emits none**) is permitted.

Correct and unpatchable by adding names: `ctypes.CDLL("libc.so.6").open(...)` runs native
code that never enters the audit system. This is `contact-export` §3.2 in a new costume —
extending an enumeration invites the next bypass.

---

## 4. What worked

### 4.1 Move the deciding rule from a *named parameter* to a *property of the input*

The fix was not a new rule. It was making the ink model depend on **which colour space the
object used** — a syntactic field the agent must notice — while the rules themselves stayed
the same published ISO 32000-1 semantics that four gates had already approved.

That is `experiment-analysis-frame` §4(b) (`P2D` vs `PT48H`) and `reduce-palaeomag` §4.1
applied to a new domain: *an exponent table is recall; a structural property of the sample is
a distinction.* Here the distinction is "is this object DeviceCMYK or Separation?", and the
natural implementation — normalise to CMYK at parse time, then run one ink model — **destroys
that information before it is needed**. Every agent wrote exactly that.

### 4.2 Make the archive teach the wrong model, not merely fail to teach the right one

This is the part worth stealing. It is not enough for the crux to be absent from the sample;
the sample should make the wrong reading look *confirmed*:

- an overprinting Separation with a **non-zero** tint and its widened equivalent paint
  **identical** plates, because the exemption skips exactly the three zeros the Separation
  never specified. So the archive contains overprinting Separations and they all validate;
- archived **non**-overprinting objects carry zero tints and visibly knock out, teaching
  "zero tint means write 0" one paragraph before the case where it means the opposite.

The grader's own words on pass@5:

> Every agent independently converged on the "widened Separation" ink model simplification …
> This passes all 16 archived samples (**which the task author deliberately constructed to
> reward this approximation**) but diverges from ISO 32000-1 on held-out fixtures. … No
> archived sample contains a Separation + overprint + tint=0 configuration, so **no agent had
> an in-distribution signal to detect the error**.

### 4.3 Enforce the boundary with the kernel, not with an audit hook

The answer to AVA round 2 was to stop enumerating. `tests/_runner.py` now `chmod 0o700`s
`/app/samples` and `/tests` **while still root**, then drops to `nobody` — so the kernel
refuses the read whatever route the module takes, including native code. Verified inside the
built image: after the seal, a raw `libc.open` on a fixture returns `EACCES` **with no audit
hook installed at all**.

The hook stays as the reporting layer and as cover for a read-only mount, with two upgrades:
it refuses `ctypes.dlopen` with a real library name (falsy argument left alone so
`import ctypes` still works — `merge-lora` §4.5), and it scans **every** event's arguments for
a protected path rather than a listed family.

Sixteen reject-side probes pass in the image (`CDLL`, `getattr(ctypes,'C'+'DLL')`, `open`,
`os.open`, `pathlib.read_bytes`, relative open after `chdir`, `listdir`, `scandir`, `walk`,
`chdir`, `glob`, `Path.iterdir`, `subprocess`, `os.popen`, `__import__`, `socket`), and the
accept side still runs (`import ctypes`, lazy imports, `try/except ImportError` fallback,
`/tmp` writes).

**A macOS trap that nearly hid this:** the first seal verification appeared to *fail* on
`/tests`, because a Docker Desktop bind mount from the host maps ownership — `stat` showed
`/tests` as `nobody:nogroup`. On a container-resident tree, which is what the harness
actually provides, it blocks. **Check `stat -c %U:%G` before concluding a permission
mechanism does not work.**

### 4.4 Three renderers, one of them deliberately float

Ground truth comes from `tools/reference.py` (per-pixel), cross-checked byte for byte against
`solution/render.py` (a scanline sweep — the shipped oracle) and a third float-arithmetic
implementation in `calibrate.py`, over all 55 fixtures and 366 fuzzed spools. This answers
`experiment-analysis-frame` §7 (`oracle = 1.000` is vacuous when the solution is the
reference) *and* proves no graded pixel sits on an arithmetic tie — the float renderer
agreeing byte-for-byte is the evidence that the 0.011 px tightest clearance is not a hazard.

The fuzzer initially disagreed on 3 bytes of one seed; the cause was a fuzz spool with an
edge passing exactly through a pixel centre — **a confirmation the clearance invariant is
load-bearing**, not a bug. Fuzz spools are now filtered by the same predicate.

### 4.5 Two mutant tables, not one

`generate_fixtures.py` enforces both halves of `reduce-palaeomag` §4.4:

| Wrong reading | Reproduces whole archive | Held-out catches |
|---|---|---|
| Separation widened to a DeviceCMYK quadruple | yes | 13 |
| zero-tint exemption applied in every colour space | yes | 9 |
| overprint mode hardcoded to 1 | yes | 4 |
| overprint mode ignored (treated as 0) | yes | 5 |
| parity (even-odd) fill | yes | 15 |
| rectangle extents normalised | yes | 4 |
| subpaths unioned instead of accumulated | yes | 6 |

| Machinery the archive *does* teach | Archived jobs that catch it |
|---|---|
| objects painted in reverse order | 9 |
| overprint parameter ignored | 2 (`j05`, `j14`) |

The second table is the one people forget. A machinery mutant that the *archive* fails to
catch means a rule nothing pins — the `qc_gate` B5 shape. Both tables run before every push;
`qc_gate` passed first time.

---

## 5. Gate-by-gate log

| Push | Commit | Result |
|---|---|---|
| 1 | `90c98da` | static 25/25, rubric **31/31**, duplicate UNIQUE, validation pass → **pass@2 2/2 solved (too easy)**. Everything downstream skipped |
| 2 | `020d4a2` | the colour-space redesign. Rubric 31/31 again, **pass@2 0/2 both valid**, `deep_review` pass → `ava_review` **BLOCK** (3 inconclusive probes + enumeration gap) |
| 3 | `12b98cb` | guard matches audit-event families, scans every argument; 4 more combining fixtures. Rubric all-PASS, **pass@2 0/2**, `deep_review` pass → `ava_review` **BLOCK** (ctypes / no default-deny) |
| 4 | `5a87949` | filesystem seal + ctypes refusal. **Every gate green**: `pass2` 0/2, `deep_review`, `ava_review`, `tier1`, `qc_eval`, `qc_exec`, `qc_gate`, `trials` → **pass@5 0/5, avg@5 0.000** → `accepted` |

Three independent pass@2 measurements returned 0/2 before pass@5 returned 0/5.

---

## 6. What the five pass@5 agents actually did

> **All five trials share a single root cause: edge-case trap + overconfidence early-quit.**
> … all agents verified 16/16 archived samples, declared success, and submitted **without
> consulting ISO 32000-1, which is the explicitly named authority in `SPOOL.md`**.

`difficulty_crux` **PASS on all five** — as on `lumenp`, nobody failed for lack of knowledge.
The trap is structural. `task__2ryWbdY` additionally dropped `opm` from its `_parse()` return
entirely, hardcoding mode-1 behaviour, and so also failed `h18`/`h33`/`h34` — the fixtures
added specifically for that mutant.

The grader's note, worth carrying:

> The single-line fix that would have resolved 4 of 5 trials: add the `space==0` gate to the
> zero-tint exemption.

**One line, five failures, and not one agent found it** — because nothing they could run told
them to look. That is what "silent failure + no self-check" buys, and it is the strongest
argument in this corpus for putting the trap in the *data* rather than in the spec.

`near_miss` split 3 PASS / 2 FAIL across trials; the analysis says plainly this is reviewer
judgement about the same root cause, not task variation. **A split `near_miss` is not a
defect signal when the fail reasons are identical.**

---

## 7. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| pass@2 2/2 solved, and your spec *names* the standard's operator/parameter | Keep the rules; move the decision onto a **property of the input** that selects between them, and let the natural implementation normalise that property away | Do not invent a deviation from the standard — B5 blocks it, and an archive that reveals it is one the agent iterates to fit |
| You need the crux invisible but the sample must stay honest | Build the sample so the **wrong** reading is byte-identical there, not merely untested. Ship the near-equivalent case (non-zero tint) *and* the misleading precedent (zero tint under knockout) | Do not merely omit the case; omission alone leaves the agent uncertain, equivalence makes it confident |
| `ava_review` `sound_verifier` on a sandbox built from an event allowlist | Enforce with the **kernel** — `chmod 0o700` the protected trees as root, then `setuid`. Native code emits no audit event, so no hook can be the whole answer | Do not add the missing event names. Two pushes proved each fix invites the next |
| A permission mechanism "doesn't work" in local Docker on macOS | `stat -c "%n %U:%G %a"` first — a host bind mount maps ownership and will show `nobody:nogroup`. Re-test on a container-resident copy | Do not conclude the mechanism is unsound from a bind-mounted probe |
| An `ava_review` blocking bullet whose evidence line states expected and actual identically | Treat it as inconclusive and fix the items that have real content | Do not redesign around it; these vanished on the next push untouched |
| Your fuzzer disagrees with the oracle on a seed | Check whether the seed violates an invariant your fixtures enforce before suspecting the renderer | Do not "fix" the renderer to match a degenerate input the archive excludes |
| You cherry-pick a doc file across a redesign | Re-read every number in it against the new artefacts in the same commit | Do not assume a file you did not edit is still true — the eval caught 14→16 and 44→51 in exactly this way |

---

## 8. Process notes

- **Rubric passed 31/31 on the first push and stayed passing through three redesigns.** The
  machinery (container, verifier, oracle, explanations) was never the problem; only the
  location of the crux was. `experiment-analysis-frame` §4 says not to rebuild what four
  gates approve of — that held here and saved every cycle after the first.
- **`.dockerignore` from the first commit**, no `"You have N seconds"` line, instruction
  measured at ~320 tokens against the 1500 cap. Static checks passed 25/25 every push.
- **Two advisory notes were fixed pre-emptively** while a run was in flight and pushed with
  the next blocking fix (`merge-lora` §7): the `difficulty_explanation` audience sentence and
  a `task/README.md` documenting `tools/`. The latter turned `task_readme` from N/A into a
  scored PASS and answered the `no_extraneous_files` borderline note.
- **`tools/` under `task/` drew a borderline note on every eval run** ("a strict reading …
  could flag it as unreferenced") and was graded PASS every time, because it derives the
  fixtures and so is load-bearing for `reviewable`. Documented rather than relocated.
- Never `git add -A`; `task/jobs/` added to `.gitignore` at the start.

---

## 9. Reusable checklist

1. Is the deciding rule real, external and published? If you invented it, stop.
2. **Does your spec name the parameter that indexes it?** If yes, it is recall, not a stump —
   this task's first push proves it, at the cost of a full cycle.
3. Does the deciding factor turn on a **property of the input** an otherwise-correct
   implementation will normalise away before it is needed?
4. Does the archive make the **wrong** reading byte-identical, and does it contain a
   precedent that teaches the wrong generalisation?
5. Are the inertness invariants machine-enforced in the generator, so a future edit cannot
   quietly leak the trap?
6. Two mutant tables: crux mutants reproduce the whole archive and are caught by ≥3 held-out;
   machinery mutants are caught by the **archive**.
7. Corpus-witness check over every non-crux feature.
8. Can grading be byte-exact? Make the pipeline integer-only and it can.
9. Three structurally different implementations agree, one of them deliberately float, plus
   fuzz filtered by your own invariants.
10. Sandbox: enforce with the kernel, report with the hook, probe **both** sides in the built
    image.
11. Oracle 1.0 / nop 0.0, README current against the final diff, no AI attribution.

---

## 10. One-paragraph version for future me

The first push named `f` and `OPM` in the shop's note and was solved 2/2 in 9 and 26 minutes:
both rules were real, published and conditional, and both were one lookup away, because the
spec named the parameters that index them. The fix was not another rule but a different
**location** for the deciding one — objects gained a colour space, and ISO 32000-1 scopes the
zero-tint overprint exemption to DeviceCMYK alone while painting marks only the colorants the
space specifies. Widening a Separation into a CMYK quadruple reproduces the entire archive,
because the archive was built so it does: overprinting Separations appear with non-zero tints
where the two readings agree, and zero tints appear under knockout where they teach the
opposite lesson. It diverges only on an overprinting Separation with tint 0, or one under
overprint mode 0 — neither in the archive. That reached **pass@5 0/5, avg@5 0.000**, with
`difficulty_crux` PASS on all five: nobody lacked the knowledge, everybody wrote the
normalisation that discards it, and all five verified 16/16 archived plates and quit without
opening the standard their own spec named. The other two pushes went entirely to
`ava_review`, which was right twice: an audit hook built from an event allowlist cannot see
`ctypes`, and the fix is to let the kernel say no — `chmod 0o700` the protected trees before
dropping privileges, and keep the hook only to report.
