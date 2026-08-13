# dynamo/recover-zip-headers — a validating-scanner near-miss, and how the decoy header was hardened

Repo: `dynamo-e4cc57f-file-and-media-operations`, PR #1, branch `submission`, fork `charan-sr`.
Category: **File and Media Operations** / Sub-category: **Recovery and repair** — the first
playbook entry for this category (the only prior File and Media Operations touchpoint was the
`legacy-formatter-clone` live example in doc 34, subcategory Text editing and manipulation).
Benchmarked against Opus-4.8 via Terminus-2. Accepted 2026-08-13 at commit `58ece5e`.

**Final result: pass@5 = 2/5 solved, avg@5 = 0.400, 3 good valid failures, 0 soft-timeout,
0 task/verifier issues, 0 reward hacking.** Comfortably inside the acceptance band. Four pushes
total: initial submission, two QC-driven soundness fixes, and one pass@5-driven hardening fix
after landing at 3/5 (one short of the bar) on the third push.

---

## 1. The task

A ZIP archive's central directory and end-of-central-directory record are gone (a truncated
copy, a partially overwritten disk region, a crashed backup job) — the same condition that makes
Python's own `zipfile` module refuse to open the file at all, since it locates the EOCD by
seeking from the end. What survives is the sequence of local file header records and their data,
exactly as the original writer laid them out.

- **Agent sees:** `/app/data/sample.zip` (six entries, ASCII names, mixed Stored/Deflate, no
  streaming-mode entries) plus `/app/data/expected/` as an end-to-end self-check.
- **Agent produces:** `/app/recover.py`, invoked as `python3 /app/recover.py <archive_path>
  <output_dir>`, recovering every entry it can directly from local file header records per
  PKWARE's ZIP File Format Specification (APPNOTE.TXT), writing each entry's exact original
  bytes to `<output_dir>/<name>`.
- **Graded on:** the sample plus eight held-out archives, never shipped, each isolating one
  mechanism (or a composition of several).
- **Constraint:** Python standard library only; no subprocess, network, or native library —
  enforced by a runtime `sys.addaudithook` guard, not source scanning.

---

## 2. The crux

> **A writer that knows an entry's size in advance records it directly in the local header, and
> reading that field is not just the "obvious" approach — it is completely correct, everywhere an
> engineer is likely to test it by hand.** The ZIP specification separately allows an entry to be
> written in *streaming* mode (general-purpose bit 3), where the writer didn't know the
> compressed size at header-write time. The header's size fields are then zero, and the entry's
> true boundary can only be recovered by decoding its raw DEFLATE stream until the decompressor
> itself reports the stream complete (Python's `zlib.decompressobj` exposes this via
> `unused_data`), then skipping a fixed-size trailing data descriptor.

Independently-gradable consequences, several added iteratively as gates and pass@ found gaps:

| Mechanism | What the naive/wrong approach gets |
|---|---|
| Streaming-mode boundary detection | Trusting the header's zeroed size field, or crashing on `zlib.decompress(b'')` |
| Signature-collision inside a streaming entry's own compressed payload | A bare byte-scan for the next `PK\x03\x04` stops early, mid-entry |
| **Hardened**: a fully plausible, internally-consistent *decoy* local file header (correct method/size/CRC-32/filename fields) embedded the same way | Defeats a scanner that validates a candidate header's fields before trusting it, not just one that trusts a bare 4-byte match |
| Data-descriptor length via genuine CRC-32 collision | An implementation that gets the DEFLATE boundary right but then scans forward for the next header (instead of skipping a fixed 16 bytes) lands inside its own descriptor |
| Filename encoding (UTF-8 vs. CP437, general-purpose bit 11) | Assuming one encoding regardless of the flag |
| Path traversal (`..`, leading separators, backslashes) | Writing outside `<output_dir>` — a real filesystem escape, not just a wrong answer |

### The invariants that make it work

1. **The shipped sample never collides with any mechanism.** All six sample entries are
   non-streaming, ASCII-named, ordinary paths — a diligent-looking implementation that only
   handles what the sample shows reproduces it exactly.
2. **`instruction.md` names the premise (cite APPNOTE.TXT, name the two general-purpose bits'
   *meaning*) and states two genuinely arbitrary conventions explicitly (CP437 as the legacy
   codepage; drop `.`/`..` segments rather than navigate them) — never the mechanism an agent must
   discover (the `zlib.decompressobj`/`unused_data` technique, the fixed 16-byte descriptor
   skip).** This is the fifth-plus confirmed instance of "disclose the raw fact, name the
   authority, never the consequence" (after `fir-boundary-metrics`, `dynamo-093d3d6`,
   `dynamo-a4b5561`, `rebuild-release-tarballs`, `dynamo-37ba44d`, `dynamo-e768ee6`).
3. **Held-out archives exist only under `tests/data/`, never in `environment/`.** Ground truth
   for every case — sample included — is simply the original plaintext used to build the archive
   at authoring time. Recovery is definitionally reproducing it, so there is no second reference
   implementation that could itself drift or contain a bug (see §5).

---

## 3. The methodology that mattered, confirmed again

**Write the plausible-wrong implementation(s) first, and measure, before writing any task
files.** Before designing anything, a from-scratch `recover_correct()` plus three deliberately
naive variants (trust-header-only, magic-byte-scan, scan-after-correct-boundary) were run against
every planned fixture. The divergence table was exactly the design:

```
                          correct  magic-scan  trust-header  scan-after
sample                      OK        OK          OK            OK
streaming_basic              OK        OK          FAIL          OK
streaming_collision           OK        FAIL          FAIL          OK
filename_encoding             OK        FAIL          FAIL          OK
mixed_composition             OK        FAIL          FAIL          OK
general_diverse                OK        OK          OK            OK
```

This is the single most repeated finding across the whole playbook, and it held again: every
naive prototype reproduced the sample and general_diverse exactly, and diverged sharply and only
on its intended target fixture — before a single line of `instruction.md` was written.

**What this methodology did *not* catch, and why:** all three original naive prototypes were
*unvalidated* — none of them sanity-checked a candidate header's fields before trusting it. Real
agent trials (§4) revealed a fourth class of "plausible-wrong" implementation — signature-scan
*plus field validation* — that the original three prototypes never modeled. See §5.4 for the fix
and the lesson.

---

## 4. Gate-by-gate log

Static checks, rubric review (31/31, never failed), duplicate check (UNIQUE), and validation
passed clean on every one of the four pushes. Every real block came from `qc_gate`, the pass@2
difficulty suggestion, or pass@5 itself — never the spec or instruction wording.

### 4.1 — `qc_gate` cycle 1 (`4ff26fe` → `4196216`): a genuine oracle bug in an inherently ambiguous heuristic

QC constructed a valid streaming entry (2 entries, DEFLATE, bit 3 set, *unsigned* 12-byte data
descriptor) whose content's CRC-32 was forged via a real preimage search to equal the data
descriptor's own optional signature bytes (`PK\x07\x08`) — so the oracle's "detect whether the
next 4 bytes are the DD signature, else assume 12 bytes" heuristic misread an unsigned descriptor
as signed, skipping 4 bytes too many.

**This is a real, inherent ambiguity of the ZIP format's optional-signature design** — any
implementation that tries to auto-detect signature-*absence* from 4 bytes alone has the same
flaw for a colliding CRC-32; it is not fixable by patching the heuristic. Fixing the *fixture*
(and leaving the same heuristic in the oracle) would not have been a real fix either — QC
constructs its own adversarial inputs independent of the shipped fixtures, so the same class of
finding would very likely recur.

**Fix:** committed the task's own archives to *always* write the optional DD signature (the one
entry that previously omitted it, for coverage, now includes it too — see §5.1 for why that
coverage still matters), and removed the ambiguous detection from `solve.py` entirely: it now
unconditionally treats the descriptor as 16 bytes. This is not "hiding" the bug — it eliminates
the heuristic that had the bug, and doing so is externally verifiable as correct for every
archive the task actually grades.

### 4.2 — pass@2 (`4196216`): 2/2 solved after the QC fix — a genuine variance signal, not a design regression

The very next push (touching only `solution/solve.py` and one never-agent-visible test fixture)
came back 2/2 solved, having been 0/2 the push before. **The fix could not possibly have taught
the agent anything** — neither file is ever shipped to the agent. This is the sharpest
confirmation yet in this playbook that **pass@2 is stochastic per push, not deterministic given
unchanged agent-visible content** (`rebuild-release-tarballs` §5.2 and `mirror-retention-plan`'s
own docs-only-push finding both said this; here the swing was the full range, 0/2 → 2/2, on
literally zero agent-visible change).

The automated **Pass@2 Difficulty Suggestion** read the two trials' traces precisely: both
agents independently derived the `zlib.decompressobj`/`unused_data` technique, and the one real
approach divergence between them (one scanned forward for the next header after correctly finding
the DEFLATE boundary, instead of skipping the fixed 16-byte descriptor) was **not exposed by any
held-out fixture** — a concrete, actionable, non-answer-revealing suggestion.

### 4.3 — Acting on the suggestion (`4196216` → `d297e92`)

Built `streaming_descriptor_collision.zip`: a streaming entry whose *real, self-consistent*
content CRC-32 (forced via a from-scratch CRC-32 append-suffix solver — see §5.2 — not a
fabricated field) equals the LFH signature as a little-endian uint32, so its data descriptor's
own crc field literally reads `PK\x03\x04`. A dedicated new naive prototype
(`recover_naive_scan_after_correct_boundary`) confirmed the new fixture — and only the new
fixture — killed exactly that mutation before pushing. `qc_gate` passed clean on this push; pass@2
came back 1/2 (the intended crux now firing on the previously-unexposed axis).

### 4.4 — pass@5 (`d297e92`): 3/5 solved, one short of the bar

Both `avg@5` failure clusters were exactly as designed (one agent deliberately chose not to
implement streaming mode after correctly identifying it; the other had two independent, precisely
spec-traceable errors — descriptor-skip method and `..`-navigation instead of drop-semantics on
`path_traversal.zip`, added the same push per a QC finding described in §4.5 below, out of
publication order because both fixes shipped together). But **2 of the 3 solving trials used a
signature scanner with secondary field validation** (compression method ∈ {0,8}, size bounds, a
plausible version, a decodable short name) — and correctly rejected the collision fixtures' bare
signature matches as implausible, then correctly found the true boundary beyond them. This
defeated the intended trap for those trials even though they never did real DEFLATE decoding.

### 4.5 — `qc_gate` cycle 2 (concurrent, folded into the same push): an unexercised security defense

QC mutated `solve.py`'s path-sanitization (dropping `.`/`..` segments and leading separators)
down to a plain `os.path.join(output_dir, name)`, and the verifier still scored reward=1 — no
fixture used a traversal-shaped filename, so the mutant's real ability to escape `output_dir`
(demonstrated with `../../../../tmp/PWNED.txt`) went undetected.

**This one needed an instruction change, not just a fixture.** Unlike most findings in this
playbook, "sanitize and still recover the entry" versus "refuse the entry outright" are both
defensible responses to a traversal-shaped name, and they diverge on a graded case — a genuine
sound-alternative ambiguity, not something derivable from domain knowledge alone. `instruction.md`
now states the exact rule (drop every `.`/`..` segment and any leading separator; treat
backslashes as `/`), and `path_traversal.zip` grades it. Verified end to end (not just at the
`recover()`-function level, since sanitization only happens in `solve.py`'s `main()`): the real
`solve.py` matches exactly, and QC's precise mutation — reproduced faithfully as a syntactically
valid (not merely broken) variant — fails cleanly, with 4 of 5 files missing (landing outside
`output_dir` instead of inside it).

### 4.6 — Hardening against the validating scanner (`d297e92` → `58ece5e`)

The fix precisely targeted what pass@5's own analysis named: task__4bD9PUK's boundary detection
(`data.find(SIGNATURE)` + `valid_local_header_at()`, checking method ∈ {0,8}, `fn_len > 0`,
decodable filename, size bounds) correctly rejected a bare-signature decoy but would accept one
whose fields all look genuinely plausible.

Replaced the bare 4-byte signature inside both `streaming_collision.zip`'s and
`mixed_composition.zip`'s trap entries with a **complete, internally-consistent decoy local file
header** — correct version, method=Stored (so no decompression attempt can ever raise and reveal
the fakery), a *genuinely correct* CRC-32 of its own decoy payload, plausible sizes, a short
decodable filename — embedded via the same level-0 near-literal DEFLATE trick used throughout.
A fourth naive prototype, `recover_naive_magic_scan_validated`, simulating exactly this
validate-before-trust strategy, was added to the local test matrix specifically to close the gap
the first three prototypes never modeled, and confirmed locally that it now fails on both hardened
fixtures (and *only* those two — it still correctly passes `streaming_descriptor_collision.zip`,
a different mechanism it was never meant to catch, and the sample).

**Result:** pass@5 landed 2/5 solved, avg@5=0.400, 3 good valid failures. The final trial
breakdown named the exact mechanism back: *"an approach that sanity-checks a candidate header
before trusting it is still misled, not only one that trusts a bare signature match"* — quoting
almost verbatim from the fixture's own design rationale in `task.toml`.

---

## 5. What actually worked

### 5.1 Ground truth as "the original plaintext," not a second reference implementation

Since the task's own premise is reconstructing a corrupted archive from known-good source
material, the expected recovered bytes for every fixture — sample and held-out alike — are simply
the plaintext content used to *build* that archive at authoring time. There is no
`tests/reference.py` that could itself have a bug independent of `solution/solve.py`'s bug, no
oracle/reference-drift risk, and no "which one is right" ambiguity when a QC finding surfaces —
only one implementation (`solve.py`) needs to be correct at all, and correctness is externally,
trivially checkable (byte-for-byte equality with known plaintext). This sidesteps an entire class
of finding (`hos-trip-scheduling`, `container-dependency-resolver` and others in this playbook
lost real cycles to a reference implementation that was *itself* subtly wrong). Worth reusing
whenever a task's own domain is "reconstruct X from a corruption/loss of X" — the very nature of
the problem gives you bulletproof ground truth for free.

### 5.2 A from-scratch CRC-32 append-forcer, implemented correctly via linear algebra over GF(2)

`crc32(prefix + suffix)` is an *affine* function of the 32-bit suffix, for any fixed prefix,
because CRC-32 is XOR/shift-linear. Evaluating the function at the zero suffix and at each of the
32 unit-bit suffixes gives the constant term and a 32×32 bit matrix; Gaussian elimination over
GF(2) then solves for the suffix that forces any target CRC-32 exactly. This is worth keeping as
reusable tooling — it is what let the `streaming_descriptor_collision` fixture use *real,
self-consistent* content (an implementation that legitimately validates the recovered bytes'
CRC-32 against the descriptor would find them matching, not fabricated) rather than a forged
field, which would have been a much weaker and more fragile fixture.

### 5.3 The `.dockerignore` and category-addendum checks, done proactively

No `44-stump-techniques-file-and-media-operations.md` exists (only the software-engineering/
scripting addendum does) — matched `fir-boundary-metrics`'s precedent of applying the general
patterns (docs 31–34) directly when no category-specific addendum exists. `.dockerignore` was
added to `environment/` from the first commit, on the strength of the repeated "non-trivial build
context has a .dockerignore" finding — never had to learn it from CI.

### 5.4 The generalizable lesson: your naive prototypes need a validating variant too

The single biggest miss of this task's design process: three naive-but-plausible implementations
were written and measured before the first push, and none of them modeled a scanner that
*validates a candidate header's fields* before trusting a signature match. Real agent trials found
this gap in the very first pass@5 measurement. **The fix generalizes past this task:** whenever a
design's trap relies on a byte-pattern coincidence (a magic-number collision, a sentinel value,
anything a "careful" implementer might defensively double-check before trusting), write a naive
prototype that *also* does that defensive double-check, not just prototypes that trust the
pattern blindly or never look for it at all. A model that reaches for the "obviously wrong"
shortcut is one failure mode; a model that reaches for a *slightly more careful* version of the
same shortcut is a different, easy-to-miss one, and only the second one showed up in real trials
here.

---

## 6. Process rules confirmed (nothing new, but worth re-confirming)

- **Never push while a run is in flight** — checked `gh pr checks 1` before every one of the four
  pushes.
- **Batch fixes into one push, always.** Every cycle bundled the code/fixture fix,
  `task.toml` prose sync, and README sync into a single commit — confirmed cheap and correct
  every time.
- **Recalibrate locally before every push** — `harbor run -p task --agent oracle/nop`, plus a
  fresh local mutation sweep whenever `solve.py` or a fixture changed, every time, including on
  pushes that "obviously" wouldn't break anything.
- **When a gate flags an ambiguous/buggy heuristic, ask whether the heuristic itself is
  fixable, or whether the ambiguity is inherent to the format** — confirmed a second axis of the
  established "delete a decoy field/behavior rather than defend it" pattern: here, the fix was
  neither deleting nor documenting a field, but *committing the task's own data to a convention
  that makes the ambiguous case genuinely never arise*, and removing the now-unneeded ambiguous
  code path entirely.
- **A pass@2 difficulty suggestion is worth reading closely and acting on literally** — it named
  the exact missing fixture, at the right level of detail (mechanism, not literal code), and the
  fix it suggested is what actually closed the gap.
- **`pass@5` landing one short of the bar (3/5 solved, need ≤2/5) is not a "the task failed"
  signal — read which specific trial(s) solved it and how.** Here, the trial breakdown named the
  exact algorithmic shortcut (validated signature-scan) that beat the design, which turned a
  potential dead end into a single, precisely-targeted fixture hardening.

---

## 7. Reusable checklist for the next task

- [ ] Write the plausible-wrong implementation(s) first, and measure divergence against every
      planned fixture, before writing any task files.
- [ ] **If a trap relies on a byte-pattern/value coincidence, write a prototype that validates
      candidates before trusting them, not just one that trusts blindly and one that never
      looks.** This is the gap that cost this task a full pass@5 cycle.
- [ ] Check whether ground truth can simply be "the known-good input the corruption/loss was
      applied to," rather than a second reference implementation — it is often free and
      bulletproof for reconstruction-shaped tasks.
- [ ] When a gate finds a heuristic that is wrong on a constructible adversarial input, ask
      whether the ambiguity is inherent to the format/problem (not just to your code) before
      trying to patch the heuristic — the real fix may be committing your own data to a
      convention that makes the ambiguous case never arise, and simplifying the code to match.
- [ ] `.dockerignore` in `environment/` from the first commit.
- [ ] No category-specific `44-*` addendum existing is not a blocker — apply the general
      patterns (docs 31–34) directly, as this task and `fir-boundary-metrics` both did.
- [ ] Read the pass@2 difficulty suggestion and the pass@5 trial breakdown closely — both named
      the exact fix needed, at exactly the right level of detail, on every cycle of this task.

---

## 8. Final state

- **PR HEAD: `58ece5e`** — the commit pass@5 was measured on, and the commit that got the
  `accepted` label.
- Commits: `4ff26fe` initial submission · `4196216` QC fix (DD-signature ambiguity) ·
  `d297e92` descriptor-collision fixture (pass@2 suggestion) + path-traversal fixture (QC fix,
  folded into the same push) · `58ece5e` hardened decoy headers against a validating scanner
  (accepted).
- Fixture-authoring tooling (`ziplib.py`, `build_fixtures.py`, `crc_force.py`,
  `mutate_sweep.py`, `verify_solve.py`, `verify_path_traversal.py`) lived only in the session
  scratchpad, never committed.
- Nine held-out mechanisms total by the end: streaming boundary detection, a bare-signature
  payload collision (hardened to a validated decoy), a data-descriptor CRC collision, consecutive
  streaming entries, an unsigned-vs-signed descriptor length distinction, CP437 filenames, UTF-8
  filenames, path traversal, and a composition archive combining several at once.

### One-paragraph version for future me

Build the crux as "the header-trusting shortcut is completely correct everywhere an engineer is
likely to test it by hand, and silently wrong only where the format's own streaming-mode escape
hatch applies" — write the naive prototypes and measure the sample/held-out divergence before any
task files exist, and make sure at least one prototype *validates* a candidate match before
trusting it if the trap depends on a byte-pattern coincidence, since real agents in this task
did exactly that and it beat two of three otherwise-un-decoding trials. When ground truth is "the
original input before the corruption the task is about," use it directly instead of writing a
second reference implementation — it removes a whole class of oracle-drift finding for free. When
a gate finds a genuinely ambiguous heuristic (not just a bug), check whether the ambiguity is
inherent to the domain; if so, commit your own data to a convention that makes it never arise and
delete the now-unneeded ambiguous code, rather than trying to patch unpatchable logic. A CRC-32
append-forcer (an affine map over GF(2), solved by Gaussian elimination) is cheap, reusable
tooling for constructing *real, self-consistent* adversarial content rather than a forged field.
And a pass@5 landing one short of the bar names, in its own trial breakdown, exactly which
implementation strategy beat the design — read it closely before assuming a redesign is needed;
here it was one precisely-targeted fixture hardening away from accepted.
