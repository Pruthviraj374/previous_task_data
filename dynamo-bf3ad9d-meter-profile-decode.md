# dynamo/meter-profile-decode — eight designs to find a stump, then two verifier-tax gates to keep it

| | |
|---|---|
| **Outcome** | **ACCEPTED** — every gate green, `accepted` label |
| **Repo** | `dynamo-bf3ad9d-security`, branch `submission`, fork `charan-sr` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-bf3ad9d-security/pull/2 |
| **Category / sub** | Security / **Reverse Engineering** (pre-seeded) |
| **Benchmarked model** | `task.toml` names Opus-4.8 / Terminus-2; pipeline reports "Model A" |
| **Final commit** | `3173771` (task name `dynamo/meter-profile-decode`) |
| **Headline** | **pass@5 = 0/5 solved, avg@5 = 0.000, 5 good valid fails, rubric 7/7 clean on every trial.** The cleanest possible acceptance, reached only after 8 full design changes on this repo and then a 4-push tail of pure verifier-soundness fixes on the winning design. |

The two lessons worth the read: **§2 — for this model, a format-PARSE crux (however obscure the
encoding) is not a stump; it reads the named spec fully and implements it, so difficulty had to
move into a from-scratch non-linear arithmetic scheme recovered by algebra ("Pattern D"), and even
that class isn't automatically qc-fair — `qc_gate` scrutinized it as hard as any hidden-knowledge
scalar and had to be answered with an explicit uniqueness proof, not just a working reference.**
**§4 — `tier1` held twice on findings that were already fixed, because it is a diff-touch tracker,
not a state tracker: it requires every open red/yellow item to be visibly re-addressed in the
commit that claims to fix something else, or it holds the round regardless of whether the item is
actually handled.**

---

## 1. What the task ends as (accepted design)

A decommissioned electricity meter left `.mlp` load-profile captures: an 11-byte header
(`magic="MLP2"`, `startDay` u16, `intervalMin` u8, `baseReg` u32) followed by 7-byte records
(`minute` u16, `reg` u32, `flags` u8), all little-endian. Decoding the fields, timestamp and
energy is a one-line exercise. The crux is a per-record **integrity code** the capture never
stores: `code = h*(h+K) mod P`, where `h` is a Horner hash (base `B`) of the record's 7 raw bytes.
The shipped sample's 150 `(record, code)` pairs pin the formula **by algebra, not pattern-matching**
— completing the square, `4*code + K^2 = (2h+K)^2` is a quadratic residue mod `P` for every record,
which pins `P` and `K` from the codes alone (`P=6600053, K=90`); the Horner base (`B=167`) then
follows by fitting the hash. No named checksum (CRC/Adler/FNV/MD5/SHA) and no affine byte-weighting
fits it — both are asserted in `generate_data.py`, along with an exhaustive proof that no *other*
`(P, K)` pair in the same search space also explains every sample code (see §3).

Agent writes a self-contained `/app/solve.py`; graded behaviourally on the sample plus 4 held-out
captures, output compared line-for-line with no tolerance. One held-out capture (`weekday`) has a
deliberate register *decrease* between two records, exercising the literal, already-stated
"signed subtraction, no floor" energy rule so a decoder that clamps or `abs()`s the delta also
fails. The verifier restores `/app/data/profile.{mlp,txt}` from a sealed `tests/pristine/` copy
before every graded run (an agent that damaged its own sample mid-session is still graded clean),
and every verifier write goes through a helper that refuses to follow a symlinked leaf *or* a
symlinked parent directory.

---

## 2. Eight designs before a stump: the format-parse ceiling and the escape

This repo started from a **delivered** task (`itsakj`'s closed PR #1, a config-recovery/checksum
task) that could not simply be reused or re-themed — `cosine_similarity` treats "recover-a-
corrupted-config-via-per-line-integrity-checksum + engine-replay" as a delivered *concept*, not
wording, and blocked a verbatim reuse **and** a from-scratch rewrite on the same idea. The
escape (per doc 34's `gnss-log-decode` example) was to change genre entirely: reverse-engineer a
**binary format** instead of a config file.

What followed was a long search for a crux this model (Opus-4.8/Terminus-2) can't recall or
brute-force its way past:

1. **Fictional register-rollover modulus (undisclosed).** `energy = (reg-prev) mod 10^7`, sample
   never wraps. **pass@2 0/2 (stumps)** — but `qc_gate` B1/B4/B5 BLOCKED: "not inferable from the
   shipped sample = hidden knowledge."
2. **Same modulus, disclosed** (header carries `reg_digits`, instruction states the odometer
   wrap). `qc_gate` would now pass, but **pass@2 2/2 SOLVED** — both agents just quoted the
   disclosed sentence. **A single fictional-convention scalar has no fair-and-hidden middle for
   this model** — `deep_review`'s fairness bar and `qc_gate`'s are irreconcilable for it.
3. **ASN.1 DER (ITU-T X.690), long-form length as the latent trap**, sample all short-form.
   Similarity passed (named format ≠ the old concept) — but **pass@2 2/2**: the model implements
   DER long-form "in one shot," it's a famous encoding.
4. **Erlang External Term Format, `LARGE_TUPLE_EXT`** as the latent trap. Same story: **pass@2 2/2**
   — the model implements the tag proactively once told to "handle the full format" (required for
   fairness).
5. **ETF `SMALL_BIG_EXT` big-integer, little-endian magnitude** (reusing the crux family that
   stumped a *different* task, `collate-modpool-batches`, in this same corpus). Still **pass@2 2/2**
   here — one trial "covered atoms, maps, binaries, floats, compressed terms proactively" and got
   the little-endian magnitude right anyway.

**Conclusion, stated flatly for reuse:** for this model, *any* format-PARSE crux is too easy once
the format is named and the instruction says to handle the full spec (which fairness requires).
The model reads named specs thoroughly and implements every branch regardless of what the one
sample exercises — the "agent stops reading once the sample parses" escape that worked for other
tasks in this corpus (`needing_a_spec_is_not_reading_it`) is **dead** for this model on this
category.

6. **Pivot: Pattern D — a custom, non-linear integer code recovered from the sample by algebra**,
   not from any spec (there is no spec; it's proprietary and undocumented). This class had already
   been proven both hard (a similar crux family: `tracd`, pass@5 0/5) and, on paper, qc-fair
   (sample-inferable, which is exactly what `qc_gate`'s B-checks want) on a different repo. First
   try: **pass@2 0/2, genuine analytical failure** — both agents exhausted named-checksum and
   affine catalogues and never attempted the quadratic-residue derivation. This became the final
   design (commit `6bff08e`); everything after this point (§3–§4) is verifier-soundness hardening
   on the *same* crux, not a redesign.

---

## 3. `qc_gate` scrutinized the winning crux itself — Pattern D is not automatically qc-fair

Once past two rounds of `tier1` infra findings (§4), `qc_gate` finally reached the crux itself and
raised two **Major** findings that were new, not carried over:

- **C3 Narrow/Hardcodable Held-Out Coverage.** QC mutated the reference to
  `kwh = abs(reg-prev)/RAW_PER_KWH` (violating the stated "reg minus the previous reg" rule) and it
  still scored reward 1 on all 6 tests, because **no graded capture's register ever decreased**
  (`neg_advances=0` everywhere). The rule was already stated with no floor; nothing tested it.
- **B5 Underdetermined / Hidden-Knowledge Mapping**, pointed at the `code_of` line itself: *"the
  graded held-out codes are not forced by what the agent can observe... family undisclosed +
  finite samples over a huge domain."* This is the generic under-determination worry that applies
  to *any* "recoverable by algebra from N samples" crux — QC applied it to this design's core
  premise even though a structurally similar crux (`tracd`) had reportedly cleared 44 checks.
  **Do not assume "Pattern D is qc-fair" transfers automatically between tasks** — be ready to
  *prove* uniqueness, not just ship a working reference.

**Fix, in one push (`bec955d`), instruction.md left untouched (no new disclosure to the agent):**

- Grew the sample from 40 to **150** `(record, code)` pairs.
- Added `assert_scheme_unique()` to `generate_data.py`: it re-scans the exact same
  prime × K search space `solve.derive_scheme` uses, but instead of stopping at the first match it
  collects *every* `(P, K)` pair that satisfies the all-residue condition across all 150 sample
  codes, and asserts there is exactly one — the true one. This is a computational proof that the
  sample **forces** the scheme within the natural hypothesis space, not merely that the search
  happens to land there first.
- Added one deliberate register-decrease record (`dip_at` param on `profile_records`, forced
  `adv=-30`) to the `weekday` held-out capture. Verified by hand: reproduced QC's exact `abs()`
  mutant against the new data and confirmed it now diverges at that exact output line.

Both fixes are pure generator/verifier changes — the agent-visible instruction never changed, so
there was no risk of re-opening the disclosure-vs-difficulty wall from step 1–2 above. `qc_gate`
passed clean on the very next round.

---

## 4. `tier1` held twice on findings that were already fixed — it tracks the *diff*, not the *state*

`tier1` is a fix-addressal gate: before every round of `qc_eval`/`qc_exec`/`qc_gate`/`trials`, it
diffs the new commit against the *previous* `qc_gate` run's findings and requires the diff to
**touch every one** — red must-fix items *and* yellow "needs human review" advisories alike. It
does not re-verify that an item is fixed; it only checks whether the commit's diff overlaps the
location/class of each finding. This corpus has hit the pattern before
(`dynamo-6204d9b-pairing-token-bitflip` §6, `dynamo-32fad5e-replay-panel-capture` §4) and it hit
again here, twice:

- **Round 1 (`2ab61cf`).** The first Pattern-D commit's `tier1` compared against an *older*
  `qc_gate` run (from the discarded register-rollover design) and required its B1/B4/B5 findings
  be touched — 3 of 5 were resolved for free by the design pivot, but two verifier-infrastructure
  findings had never been addressed at all:
  - **E5 Symlinked Output Path** — `test_outputs.py` wrote to `/tmp/agent_solve.py` and
    `/tmp/capture.mlp` with plain `open(path, "wb")`, no guard against a pre-planted symlink at
    that exact spot redirecting the write.
  - **E2 Immutable-Input Integrity Not Enforced** — `instruction.md` promises "grading uses clean
    copies" of `/app/data/profile.{mlp,txt}`, but nothing in the verifier actually restored them.

  Fixed with a `_safe_write` helper (`unlink` the target, then `open(..., O_CREAT|O_EXCL|
  O_NOFOLLOW)`) used for every verifier write, plus a sealed `tests/pristine/profile.{mlp,txt}`
  (written by `generate_data.py`) that `test_outputs.py` restores `/app/data` from before every
  `_run_solver` call. **Verified for real, not just reasoned about**: built the environment Docker
  image by hand, deleted `profile.mlp` and overwrote `profile.txt` with garbage inside a running
  container, overlaid `/tests`, ran `tests/test.sh` — reward stayed 1 and `/app/data` came back
  byte-identical to the sealed copy.

- **Round 2 (`bec955d`).** The C3/B5 crux fix above (§3) landed clean on its *own* content, but
  `tier1` **held again** — this diff didn't touch the symlink/integrity code at all, so the two
  **yellow, non-blocking** advisories still sitting on the current `qc_gate` sticky from the E5/E2
  fix's own review (*"confirm the guard also rejects a symlinked PARENT directory, not just leaf
  files"*; *"confirm EVERY declared protected path is pinned"*) got counted as unattempted, even
  though the underlying mechanism already existed and worked. **This is the exact false-hold
  pattern documented in the two case studies above — it does not care that a yellow item is
  already effectively handled; it cares that the diff visibly touched it.**

  Fixed by making both guards **more explicit and provably correct**, in their own push
  (`3173771`), separate from any content change:
  - `_safe_write` now also checks `os.path.realpath(os.path.dirname(path)) == os.path.dirname(path)`
    before writing, refusing if the *parent* directory was itself replaced with a symlink. Verified
    for real: swapped `/app/data` for a symlink to an agent-writable directory inside a running
    container — the verifier refused with a `RuntimeError`, reward stayed 0, and the agent's own
    directory was never overwritten through the link.
  - A new build-time `assert_all_protected_paths_pinned()` in `generate_data.py` greps
    `instruction.md` for every `/app/data/*` path it names and asserts the set is *exactly*
    `{profile.mlp, profile.txt}` — the two paths the verifier restores — so a future edit that adds
    a third protected path without wiring its restore fails the build instead of going silently
    unenforced.

  `tier1` passed clean on the next round, and everything downstream (`qc_eval`, `qc_exec`,
  `qc_gate`, `trials`) passed clean in the same cycle.

**Transferable rule, now confirmed three times in this corpus:** when you fix any gate blocker, in
the *same push* also make a concrete, in-code, documented attempt at every co-listed item still
open on the current sticky — red or yellow — or budget one extra `tier1`-only round to do it
separately. Verifying "this is already handled" locally does not satisfy the gate; only a diff
that visibly touches the finding does.

---

## 5. Gate-by-gate log (final design only; §2 covers the 5 discarded designs)

| Commit | Change | Result |
|---|---|---|
| `6bff08e` | Pivot to Pattern D: `.mlp` fixed-width binary + `code=h*(h+K) mod P` integrity code, sample-inferable by algebra | static/similarity/rubric/validation ✅ · **pass2 ✅ 0/2, both valid analytical fails** · ava/deep ✅ · **tier1 ⛔ HOLD** (old B1/B4/B5 vs. leftover E5/E2, only E5/E2 unattempted) |
| `2ab61cf` | `_safe_write` (leaf `O_NOFOLLOW`+`O_EXCL`) for every verifier write; `tests/pristine/` restore of `/app/data` before every run; fixed a Windows-only CRLF regression in the generator's text-mode writes | tier1 ✅ (E5/E2 confirmed) · pass2 re-rolled ✅ 0/2 · ava/deep/qc_eval/qc_exec ✅ · **qc_gate ⛔** C3 (no held-out register decrease) + B5 (uniqueness not proven) |
| `bec955d` | Sample 40→150 records; `assert_scheme_unique()` proves no rival `(P,K)` fits; register-decrease record in `weekday`; `task.toml`/README updated (reviewer-only, not agent-visible) | qc_gate findings resolved · pass2 re-rolled ✅ 0/2 (3rd stump) · ava/deep ✅ · **tier1 ⛔ HOLD** (E5 parent-dir + E2 path-coverage yellow items never touched by this diff) |
| `3173771` | Explicit parent-directory containment check in `_safe_write`; build-time `assert_all_protected_paths_pinned()` | **everything ✅** · pass2 re-rolled ✅ 0/2 (4th stump) · ava/deep/tier1/qc_eval/qc_exec/qc_gate ✅ · **trials ✅ pass@5 0/5, avg@5 0.000, 5 good-valid, rubric 7/7 clean → `accepted`** |

pass@2 landed **0/2 with a genuine analytical fail on all four pushes** to this design — the crux
itself never needed to change once found; every remaining round was pure verifier-soundness tax.

---

## 6. Reusable checklist

Design (Security / Reverse Engineering, this model):
- [ ] **A format-PARSE crux is not a stump for this model**, however obscure the encoding, once the
      instruction names the format and (for fairness) says to handle it fully. It reads specs
      thoroughly and implements every branch proactively. Don't keep tuning which tag/branch is
      latent — change class entirely.
- [ ] **Pattern D (a custom, undocumented, non-linear scheme recovered from sample pairs by
      algebra) is the escape** once format-parse saturates — but it is not automatically qc-fair.
      Budget a round for `qc_gate` to scrutinize the crux's core premise (C3 coverage, B5
      uniqueness), even if a similar crux family cleared review on a different task.
- [ ] For any "recoverable from N samples" crux, **ship a computational uniqueness proof** in the
      generator's self-check (exhaustively confirm no rival parameter set also explains every
      sample point in the natural search space), not just a working reference solver. Answers B5
      directly.
- [ ] A **single fictional-convention scalar has no fair-and-hidden middle**: undisclosed fails
      `qc_gate` (hidden knowledge), disclosed gets solved outright (model just quotes the
      sentence). Don't spend a design cycle tuning disclosure on one scalar; change what kind of
      crux it is instead.
- [ ] `cosine_similarity` blocks a delivered **concept**, not wording — a verbatim reuse *and* a
      from-scratch reskin of the same idea both fail it. Change genre, not phrasing.

Verifier soundness (do this up front for any Security/RE task):
- [ ] Every verifier write (copied artifact, staged input) goes through a helper that refuses a
      pre-existing **leaf** symlink (`unlink` + `O_CREAT|O_EXCL|O_NOFOLLOW`) *and* a symlinked
      **parent directory** (`realpath(dirname(path)) == dirname(path)`) — the leaf-only guard is a
      known `qc_gate` E5 half-fix.
- [ ] If the instruction promises "grading uses clean copies" of any agent-writable input, the
      verifier must actually **restore** it from a sealed copy before every graded run, not merely
      claim it — `qc_gate` E2 checks for the restore, not the sentence.
- [ ] Machine-enforce path coverage: assert (at build time) that every protected path the
      instruction *names* has a matching restore in the verifier, so a future instruction edit
      can't silently add an unpinned path.
- [ ] When fixing any gate blocker, in the **same push** make a concrete, documented touch to
      every other co-listed item on the current sticky — red or yellow, already-handled or not —
      or expect `tier1` to hold a round regardless of whether it's actually fixed.

Process:
- [ ] On Windows dev machines with `core.autocrlf=true`, any regeneration through a Python
      **text-mode** write (`open(path, "w")`) silently reintroduces CRLF. Pass `newline="\n"`
      explicitly. Verify with a byte count on the **git blob** (`git show :<path> | count(b'\r')`)
      — a working-tree `grep -c $'\r'` run through a non-bash `sh -c` gives a false-clean result
      (`dash` doesn't support ANSI-C quoting).
- [ ] Recalibrate `harbor run --agent oracle` (1.0) / `--agent nop` (0.0) locally before every
      push; when a fix is a security/soundness claim (a symlink guard, an integrity restore),
      **also reproduce the actual attack in a hand-built Docker container** and confirm the
      verifier refuses it — local reasoning alone is not the same evidence as a real run.

---

## 7. One-paragraph version for future me

Accepted at the cleanest possible bar (pass@5 0/5, avg@5 0.000, 5 good valid fails, rubric 7/7 on
every trial) after **eight** full design changes on this repo: a delivered config-recovery PR
blocked both verbatim reuse and reskin under `cosine_similarity` (concept-level, not wording); a
fictional register-rollover modulus proved to have no fair-and-hidden middle (undisclosed fails
`qc_gate`, disclosed gets solved outright); and three successive named-format-parsing designs
(ASN.1 DER long-form length, ETF large-tuple, ETF little-endian big-integer) all landed pass@2 2/2
because this model reads a named spec fully and implements every branch once told to handle the
whole format — the "stop reading once the sample parses" escape other tasks in this corpus rely on
is dead for this model on format-parsing. The winning design pivoted entirely away from parsing a
spec into **Pattern D**: an undocumented, non-linear integrity code (`h*(h+K) mod P`, a Horner
hash) recoverable only by completing the square into a quadratic-residue test — genuinely hard
(pass@2 0/2 on all four pushes to this design) because the model exhausts named-checksum and
affine catalogues without ever attempting the number-theory step. But Pattern D is not
automatically qc-fair just because a similar crux family cleared review elsewhere: `qc_gate`
scrutinized this instance's own coverage (no held-out register ever decreased, so an `abs()`-
clamped decoder passed) and its own uniqueness (whether the sample's finite pairs truly force the
scheme, or merely happen to be the first fit found), both fixed with generator-side proofs and zero
new agent-visible disclosure. And `tier1` held twice on findings that were already functionally
fixed, because it tracks whether a diff *touches* every open item, not whether the item is
actually resolved — the fix both times was to make the existing guard more explicit and provably
correct in its own push, confirmed for real against hand-built Docker attacks (a symlinked leaf, a
symlinked parent directory, a deliberately corrupted sample) rather than trusted from local
reasoning. Carry forward: format-parse cruxes are exhausted for this model in this category, so any
future Security/RE task for it should start from Pattern D or a comparably from-scratch,
sample-inferable arithmetic scheme — and budget one extra round after the crux lands for `qc_gate`
to independently probe that scheme's coverage and uniqueness, plus one round of `tier1` housekeeping
per verifier-hardening push.
