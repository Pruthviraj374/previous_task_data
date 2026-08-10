# dynamo/target-abi-audit — gate failures, fixes, and what finally worked

Repo: `dynamo-093d3d6-build-dependency-and-release-management`, PR #1, branch `submission`,
fork `charan-sr`.
Category: **Build Dependency and Release Management** / Sub-category: **Cross Compilation and
platform targeting**. Same subcategory as `dynamo-37ba44d-cross-link-closure`, worked in
parallel this session — read that case study too once it lands.
Benchmarked against Opus-4.8 via Terminus-2. Accepted by every automated gate on 2026-08-05
at commit `64d6f3b`.

**Final result: pass@5 = 0/5 solved, avg@5 = 0.000, 5 good valid failures, 0 soft-timeout,
0 task/verifier issues, 0 reward hacking.** Best possible outcome. Every gate green on the
third pipeline cycle; `qc_gate` blocked the first two.

This is a same-day, same-category companion to `dynamo-37ba44d-cross-link-closure`
(dynamic-loader search-order resolution). The two share a design family — "identity is not
what the obvious field says it is" — but this task's crux is deliberately different in kind:
several independent per-format facts rather than one generalizing algorithmic insight. Both
worked. Section 4 explains why that distinction matters less than the playbook previously
thought.

---

## 1. The task

A cross-build stages every artifact it produces — for however many targets are in a run's
matrix — into one content-addressed pool. The record of which target build produced which
staged file has been lost for older releases. The agent reconstructs it.

- **Agent sees:** `/app/data/pools/<name>.json` (two shipped pools: `nimbus-2.9.0` covering
  Linux/Windows/MIPS, `nimbus-2.9.0-apple` covering macOS/iOS-sim/RISC-V) — each a `matrix`
  of target triples, a `root`, and a `files` list — plus the real staged ELF/Mach-O/PE
  binaries themselves, plus `/app/data/expected/*.csv` as an end-to-end self-check.
- **Agent produces:** `/app/audit.py`, invoked as
  `python3 /app/audit.py <pool_json> <out_csv>`, writing `path,target` rows (`target` is a
  literal matrix entry or the literal `none`), plus reports for both shipped pools at
  `/app/output/`.
- **Graded on:** eight *held-out* pools, never shipped, each isolating one ABI-disambiguation
  mechanism (or several at once).
- **Constraint:** Python standard library only; must not start another process, execute code
  dynamically, or load a native library.

---

## 2. The crux

> **An image's target is not just its processor.** Container format, processor, operating
> system, and the C runtime/ABI the toolchain was configured for all have to agree with a
> matrix entry — and the last two are not always sitting in whatever field of the image names
> its processor. Sometimes they follow from something else the image carries instead, and the
> same processor and format can come from more than one toolchain in a matrix.

Six-to-seven independent, differently-shaped consequences, none of them a single atomic fact:

| Mechanism | What "processor only" misses |
|---|---|
| ARM float ABI | `EF_ARM_ABI_FLOAT_HARD` bit in `e_flags` — `eabihf` vs `eabi`, same machine value |
| x32 ABI | `ELFCLASS32` + `EM_X86_64` together — a distinct ABI, not "32-bit x86" |
| MIPS o32/n32/n64 | `EF_MIPS_ABI2` + ELF class, same `e_machine`, same endianness for two of the three |
| libc identity | `PT_INTERP` leaf name, or `DT_NEEDED` soname when there's no interpreter (shared libs) |
| Android bionic | Same ARM/AArch64 machine + flags as a glibc build; only the interpreter path differs |
| Apple platform | macOS / iOS / iOS-sim / **Mac Catalyst** share the identical Mach-O cputype pair; only `LC_BUILD_VERSION` (or the older `LC_VERSION_MIN_*`) distinguishes them |
| Windows runtime | MSVC vs MinGW share the COFF machine value; only the import table's DLL names (`vcruntime*`/`api-ms-win-crt-*` vs `libgcc_s*`/`libwinpthread*`) tell them apart |

### The three invariants that make it work

1. **The two shipped pools never collide on format+processor.** Every target in each shipped
   matrix is already unique by `(format, processor)` alone, so a resolver that stops there
   reproduces both shipped reports exactly.
2. **`instruction.md` states the premise, never the mechanism.** It says format/processor/OS/
   ABI must all agree with a matrix entry, and that the last two "are not always sitting in
   whatever field... names its processor" — but never names `e_flags`, `PT_INTERP`,
   `LC_BUILD_VERSION`, or any DLL name. This is the same "raw premise, not consequence" move
   validated on `fir-boundary-metrics` and the same "architectural mechanism, disclosed
   outright" move validated on `rebuild-release-tarballs` and `copybook-extract-decoder` — see
   §4 for why this shape tolerates that disclosure.
3. **Held-out pools exist only in `tests/`**, materialized from a declarative pool spec
   (`bundles.py` + `artifacts.py`, byte-level ELF/Mach-O/PE writers) at authoring time, never
   shipped as generation tooling — only their output (binaries + manifests) is committed.

---

## 3. Gate-by-gate failure log

Every gate up through `deep_review`/`adversarial_review`/`ava_review`/`tier1` passed clean on
**all three** pipeline cycles — the entire cost of this task was two `qc_gate` cycles.

### 3.1 — `qc_gate`, cycle 1 (`80eafca` → `b75bfca`): Oracle Edge-Case or Logic Bug

QC constructed `matrix=["x86_64-apple-ios-macabi"]` against a real Mac Catalyst Mach-O
(`LC_BUILD_VERSION` platform=6) and found `identify()` and `target_key()` **disagreed**:
`identify()` correctly read platform 6 as `"maccatalyst"` via its own `MACHO_PLATFORM` table,
but `target_key()` derived the platform from the triple's leading path component (`"ios"`),
never checking for a trailing `-macabi` suffix. A real, generalizable input where my own two
derivation paths gave two different answers — QC probes for exactly this kind of internal
inconsistency, not just held-out coverage.

**Fix:** one `if rest and rest[-1] == "macabi": platform = "maccatalyst"` branch in
`target_key()`, applied identically to `solution/audit.py` and `tests/reference.py`. Added a
Mac Catalyst row to the held-out `handoff-apple` pool so the fix is pinned by a fixture rather
than left as an unexercised branch (the exact class of gap that bit `copybook-extract-decoder`
on `OCCURS`).

**Generalizable:** QC doesn't only mutate your reference or probe the verifier — it also
constructs valid inputs your own helper functions were never tested against and checks your
functions agree with *themselves*. A local mutation sweep only tests inputs drawn from your
own fixtures; it cannot find a generality bug in a branch no fixture ever reaches.

### 3.2 — `qc_gate`, cycle 2 (`b75bfca` → `64d6f3b`): two findings

**C3 — Narrow / Hardcodable Held-Out Coverage.** QC noticed `test_outputs.py` always built the
manifest handed to the graded program with `"files": sorted(blobs)` — meaning the input file
order was *already* the correct output order on every single fixture, sample and held-out
alike. Deleting the reference's own `rows.sort(...)` call still passed everything, because
nothing ever exercised "the program must actively sort, not just preserve input order."

> Fixed by reordering rows in three pools (the shipped `nimbus-2.9.0` sample plus held-out
> `handoff-libc` and `handoff-mips`) to genuinely not be pre-sorted, and removing the
> force-sort in `test_outputs.py`'s `_report_for` helper (`sorted(blobs)` → `list(blobs)`,
> which now preserves whatever order the committed manifest declares). A fourth pool
> (`handoff-windows`) turned out to already be unsorted from authoring and started pinning the
> requirement for free once the harness stopped erasing that signal.

**B4 — Undocumented Requirement Enforced.** The AST check bans `eval`, `exec`, `__import__`,
`import_module`, `load_module`, `CDLL`, `cdll`, `LoadLibrary` as *calls* — none of which read as
"start another process" under `instruction.md`'s literal wording ("must be self-contained,
import only from the Python standard library, and must not start another process").

> Fixed by extending the instruction's closing sentence: "...and must not start another
> process, execute code dynamically (`eval`, `exec`, `__import__` or equivalent), or load a
> native library." Chose documentation over narrowing the check, because narrowing it would
> have reopened a real bypass — `eval("__import__('subprocess')...")` defeats a static
> import-only scan without ever writing a static `import subprocess` line, so the ban is
> load-bearing for the "stdlib only" promise, not overreach. Same resolution as
> `fir-boundary-metrics` §6.4.3's identical finding: when a check enforces something real that
> the instruction never said, prefer stating it over loosening the check, *unless* loosening
> is actually safe.

Both fixes verified with a 14-mutation sweep (13 content mutations plus a dedicated
"delete `rows.sort()`" mutation, checked against row *order* not just row content) before
pushing — zero survivors both times.

### 3.3 — Everything else, every cycle

Static checks, rubric review (31/31), duplicate check (UNIQUE — nearest neighbor
`cobol-modernization` at 0.113 lexical similarity, correctly distinguished as reimplementing a
business program vs. parsing three binary container formats), validation, `pass@2`,
`deep_review`, `adversarial_review`, `ava_review`, and `tier1` all passed clean on every one
of the three pipeline runs. `pass@2` independently measured **0/2 genuine analytical fails**
three separate times (initial, post-cycle-1, post-cycle-2) — strong evidence the difficulty
was robust to the QC fixes rather than an artifact of one lucky roll.

`adversarial_review` (advisory) flagged that `/app/data/expected/*.csv` remain on disk at
grade time and a cheating submission could `cp` them into `/app/output/` — correctly assessed
as passing only 2 of 14 tests, since `test_sample_pool_recomputed` re-runs the program on
pristine copies and the 8 held-out tests can't be satisfied that way. Left as-is; the
adversarial reviewer's own analysis confirmed no real bypass existed.

---

## 4. What the pass@5 trials actually showed

All five trials `approach_validity: PASS`; `difficulty_crux` failed in exactly the one trial
that never reached the parsing challenge at all (see below). Two failure clusters:

**1. Terminal-wedge execution failure (1/5, `task__qgpe7oR`).** Agent tried to write a ~10 KB
`audit.py` via a single bash heredoc; the heredoc got truncated mid-write, left the shell stuck
at a `>` continuation prompt, and every recovery attempt failed for the remaining ~46 minutes.
No file was ever created. Unrelated to the task's design — an execution-mechanism failure, not
an analytical one — but still counted as a good valid failure per the graders' own
classification (reward 0, no verifier/task defect).

**2. Format+processor-only analytical failure (4/5).** Every one of the four converged on the
identical partial implementation: correctly read `e_machine`/`cputype`/COFF machine, correctly
handled `PT_INTERP` for the *executable* libc case, then stopped. Specific, quotable details
from the graders' analysis:

- **`e_flags` was read into a variable in some trials and then never used.** Not "forgot the
  field exists" — extracted it, discarded it.
- One trial explicitly captured `LC_BUILD_VERSION`'s platform field into a variable, then
  still unconditionally emitted `*-apple-darwin` for every Mach-O file regardless of what that
  variable held.
- Every trial got the MinGW **triple convention** wrong even where MinGW detection itself
  half-worked — emitting `x86_64-pc-windows-gnu` instead of `x86_64-w64-mingw32`, so even a
  correct *runtime* classification failed to match any real matrix entry.
- All four verified against the two shipped pools, confirmed clean diffs, and voluntarily
  declared completion in 16–32 minutes of a 60-minute budget — the exact "overconfidence
  early-quit" pattern doc 34 describes, reproduced independently four times.

Grader's own framing: *"agents know how to extract `e_machine` and `cputype` as the canonical
processor identifiers but do not routinely proceed to `e_flags` or load-command iteration for
ABI disambiguation."* That's the crux, stated back almost verbatim from the design rationale.

### Why this shape survived disclosure — reconciling with the playbook's §9 finding

The existing playbook (`fir-boundary-metrics` §9) frames the choice as "architectural crux
with one generalizing insight" (survives disclosure) vs. "atomic fact" (doesn't). This task
complicates that framing: the crux here is **not** one generalizing insight — knowing "ABI
lives outside the processor field" does not tell you *which* bit, field, or table for any
specific format. It really is closer to "several independent facts." Yet it survived
disclosure of the raw premise across three independent pass@2 measurements and a clean 0/5 on
pass@5.

**Revised hypothesis:** what actually matters is not "one insight vs. many facts" but **how
many independently-checkable consequences the crux has, regardless of whether they share a
generating principle.** `copybook-extract-decoder` (also many-independent-facts in shape:
`OCCURS`, `SIGN SEPARATE`, `REDEFINES`, level-88, continuation, reference format) also survived
outright mechanism disclosure. What both share with `rebuild-release-tarballs`'s single-insight
crux is *breadth of independently-graded consequence*, not the number of underlying principles.
A single atomic fact (`fir-boundary-metrics`'s antimeridian rule) has exactly one consequence
shape; once salient, applying it correctly is not hard. A crux with 6–8 independently-tested
consequences remains hard even once its *existence* is granted, because getting all of them
right in one pass is still real, uncollapsed work — whether or not those consequences descend
from one clever idea or a checklist of format-specific conventions.

---

## 5. Process rules confirmed (nothing new, but worth re-confirming)

- **Never push while a run is in flight** — checked `gh pr checks 1` before every one of the
  three pushes; zero wasted cycles from this on this task.
- **Batch fixes into one push, always.** Both QC cycles bundled the code fix, the fixture
  addition/reordering, `task.toml` prose sync, and `README.md` sync into a single commit.
- **Recalibrate locally before every push** — `harbor run -p task --agent oracle/nop` plus a
  fresh mutation sweep, every time, including after fixes that "obviously" wouldn't break
  anything (the sort-order fix touched fixture content that the ABI-detection difficulty
  didn't depend on, but recalibrating anyway is what confirms that rather than assumes it).
- **Every push re-rolls pass@2 fully** (took 41 min, 50 min, and 1h8m across the three cycles)
  — expect roughly an hour of wall-clock pipeline time per QC fix cycle before you know whether
  it held.
- **Fixture-generation tooling (`bundles.py`, `artifacts.py`) stays out of `tests/` entirely**
  — used only from the local scratchpad at authoring time; only their *output* (committed
  binaries + manifests) ships in the repo. Matches `copybook-extract-decoder`'s
  "never shipped" rule for the same category of tool.
- **`tests/reference.py` and `solution/audit.py` must be fixed identically, every time.** Both
  QC-driven fixes touched both files; a mismatch between them would silently make the oracle
  and the held-out expectations disagree.

---

## 6. Verifier-hardening / design checklist additions for the next task

Everything from the prior playbook entries still held (never grade against `/app`, delete
ground truth + reference from `/tests` before the first invocation and assert absence, isolate
each held-out input in its own directory, run the graded program as an unprivileged user with
`RLIMIT_NPROC` floored, mutation-sweep the reference before every push). New this task:

- [ ] **A mutation sweep on your own reference only tests inputs your own fixtures already
      cover.** It cannot find a case where two of your own helper functions (e.g. a byte-level
      decoder and a triple-string decoder meant to agree) disagree on an input neither of your
      fixtures happens to construct. QC will construct exactly that input. If your design has
      two independent code paths that are supposed to derive the same value, write a
      standalone property check — "for every target string in a plausible matrix, does
      `identify(artifact(target))` equal `target_key(target)`?" — over a wider input space than
      your shipped/held-out fixtures, not just over the fixtures themselves.
- [ ] **Check whether your verifier accidentally erases the signal for a stated requirement.**
      A requirement like "sort your output" is only tested if at least one fixture's *input*
      isn't already in the desired output order. It's easy to build fixtures in a way (ascending
      hex prefixes, alphabetically-named rows) that accidentally pre-sorts everything, and easy
      for a "helper" in the test harness (`sorted(blobs)`, here) to force sorted order even when
      the fixture author didn't intend it. Audit test-harness helpers for accidental sorts,
      dedup, or normalization that could mask an unenforced requirement.
- [ ] **Every AST/static enforcement check needs a literal trace to instruction wording.** If a
      check bans more call names or import names than the instruction states, either the
      instruction is under-stated or the check is over-reaching — QC catches this specific
      mismatch by name (`Undocumented Requirement Enforced`) and it is cheap to audit for
      directly: read every entry in your deny-list, and confirm the instruction's prose covers
      it, before your first push.

---

## 7. Final state

- **PR HEAD: `64d6f3b`** — the commit pass@5 was measured on. Do not push over it.
- Commits: `80eafca` initial submission · `b75bfca` Mac Catalyst oracle-consistency fix ·
  `64d6f3b` sort-coverage + documented-constraint fix (accepted).
- Fixture-generation tooling (`build_fixtures.py`, `artifacts.py`, `bundles.py`,
  `naive_audit.py`) lived only in the session scratchpad, never committed.

### What stumped the agents, in their own words (from the graders' pass@5 analysis)

> "Agents know how to extract `e_machine` and `cputype` as the canonical processor identifiers
> but do not routinely proceed to `e_flags` or load-command iteration for ABI disambiguation."

Four of five trials converged on the identical partial parser — correct format/processor
detection, correct `PT_INTERP`-based libc for the executable case, and a silent stop there.
One trial captured `LC_BUILD_VERSION`'s platform field into a variable and never used it. All
four verified cleanly against the two shipped pools and quit with most of a 60-minute budget
unused — the design's core bet (samples homogeneous exactly where the ABI axis would need to
disambiguate) held on every independently-measured trial, across three separate pipeline runs.
