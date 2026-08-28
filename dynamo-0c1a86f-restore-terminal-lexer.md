# dynamo-0c1a86f — restore-terminal-lexer

| | |
|---|---|
| **Outcome** | **ACCEPTED** — every gate green on the first push, `accepted` label |
| **Repo** | `dynamo-0c1a86f-games-puzzles-and-interactive-simulation`, PR #2 |
| **Category / sub** | Games Puzzles and Interactive Simulation / **Interactive text games** (pre-seeded) |
| **Final commit** | `56d110a` (1 push, zero revisions) |
| **Headline** | **pass@5 = 0/5 solved, avg@5 = 0.000**, 4 good-valid-fail, 1 in-progress-timeout. `pass@2` 0/2 (1 valid-fail, 1 in-progress-timeout). `qc_gate` **37/37 clean on the first cycle**. Every rubric criterion PASS. Zero platform faults |

Rebuild a retired public story terminal's Z-machine lexical analyser as
`/app/lexer.py`, graded on 14 held-back sessions across four titles, three of
which are never shipped.

---

## 0. Why this repo, and what killed the predecessor PR

This repo already carried a closed PR (#1, `sub-basement-protocol`, 33 commits,
2026-08-24 to 2026-08-27, never merged). Read it in full before designing —
`previous-task-data.md`'s standing rule to check a repo's own closed PRs, not
just sibling repos (`replay-run-histories` §4). It never reached `trials`:

- **`qc_gate` blocked with 12 "Major" findings, every single one's evidence
  field literally `(no evidence recorded)`.** The task was a compiled,
  XOR-string-obfuscated interactive binary the agent had to reverse-engineer
  live over ~60 turns. QC's probes — which need to *execute* claims about
  oracle derivation, fixture validity, determinism — could not evaluate a
  black-box binary at all, so every check that needed evidence came back
  empty and the gate failed closed on all twelve at once.
- Its one pass@2 valid failure was **Pattern F** (an agent tried ~35 candidate
  strings for an undiscoverable command, `examine monitor`, and never wrote
  `solve.py`) — a guessing-game failure, not the reasoning trap the design
  intended. `00-ATTEMPTER-SPEC.md` §7 calls this pattern the riskiest for
  exactly this reason: if the string is truly unguessable, it's luck.
- The 33-commit log is one long log of **dialing the same lever harder**:
  turn-budget tightening (35→75→180→65), string obfuscation, symbol
  stripping, secret rotation, "eliminate static salt" — every commit tunes
  difficulty *up* on a shape that had already produced an unevaluable QC
  gate, never changes the *kind* of difficulty. `00-ATTEMPTER-SPEC.md` §5
  names exactly this failure mode: "reject by fixing metadata... never by
  shortening the timeout or adding busywork — reviewers catch it."

**The design decision this drove:** build something QC's probes can actually
execute claims against — a deterministic pure-Python program graded against a
computed reference, not an opaque compiled binary. Every soundness property
(oracle derivation, mutation coverage, bypass resistance) had to be something
`tools/probe.py` could *measure through the real verifier*, not something I
had to assert in `verification_explanation` and hope QC could confirm. That
is the single reason this task cleared 37/37 QC checks with zero findings on
cycle one, where the predecessor blocked on 12 unevaluable ones.

---

## 1. The crux: one misreading in five places

`environment/data/CABINET.md` names the **Z-Machine Standards Document 1.1**
as normative for the story images and for lexical analysis, and restates none
of it — the `replay-run-histories` §4 / `serve-thesaurus-lookups` §4.1
pattern, now in a third category: name the authority, enumerate nothing.

The one released title (`bellrock.z3`) is a 1988 V3 file with the built-in
alphabet. Its audited session (`bellrock-0417.log`, 13 typed lines) was
selected **by measurement**, not by eye — `tools/generate.py` refuses to write
the archive unless it is reproduced identically by every latent wrong
reading — so that it happens to exercise only the parts of the standard
common to every version. Five real, conditional provisions are therefore
inert on everything the agent can see:

| # | Provision | Inert because |
|---|---|---|
| 1 | §13.6.1 — a word separator divides words **and is a word in its own right** | the audited session types no `.` `,` `;` |
| 2 | `read` opcode — typed text is reduced to lower case before matching | the audited session is entirely lower case |
| 3 | §3.7 — dictionary resolution is 6 Z-characters through V3, 9 from V4 | the released title is V3 |
| 4 | `read` opcode — text buffer starts at byte 1 through V4, byte 2 from V5; the recorded position is a *buffer* position | V3 makes base 1 look like a property of the format — the V4 title (base 1, but 9-Z-char resolution) is the deliberate decoupler, so "V4+ means base 2" also fails |
| 5 | §3.5.5/3.5.5.1 — from V5 a title's own alphabet table still reserves A2's first two slots for the escape and newline, however the bytes are filled in | V3 has no such header field |

Provision 5 pulls in §3.4 (the four-Z-char ZSCII escape for anything no
alphabet reaches) and §3.7's parenthetical (an incomplete multi-Z-char
construction is left incomplete, not dropped). **These are one misreading
wearing five coats**: *the released title's configuration is the format*.
This is `serve-thesaurus-lookups` §2's finding — "prefer axes that are the
same root misreading in different places over independent rules" — applied to
a format-versioning domain instead of an RDF vocabulary. Every wrong answer
is a well-formed result of the right shape with plausible addresses in it;
nothing crashes, nothing looks wrong. Textbook silent-failure amplifier.

The two sharpest provisions (4 and part of 2) live in the `read` opcode's own
spec section, not in §13 (the dictionary section) — a solver who reads "the
dictionary" and stops has no structural reason to open the entry describing
how typed input is captured. `pass@5`'s own analysis independently named this:
*"The only trial reaching a single-bug near-miss... correctly implemented
separator-as-word and V4+ key width, but missed the V5 buffer offset."*

The audited session **refutes** three cheap readings outright (line offsets
used as buffer positions; matched length reported instead of typed length;
words never truncated to resolution) by containing a word longer than the
resolution that still matches (`lanterns`→`lantern`), a word absent from the
dictionary (`bosun`), leading spaces, and a punctuation character inside a
word (`sou'wester`) — so an engineer holding one of those three fails while
still working, per the spec's fairness line, rather than shipping a confident
wrong answer.

---

## 2. Built for QC to execute, not for me to assert

Every claim in `verification_explanation` has a corresponding script that
performs it against the real verifier:

- **`tools/generate.py`** plants the archive and *refuses to write* unless ten
  invariants hold — well-formed dictionaries; the audited session reproduced
  identically by all eleven latent wrong readings; the audited session
  refutes the three cheap ones; every latent reading caught by ≥2 held-back
  sessions (measured minimum 3); no dead-weight fixture; every disclosed
  behaviour (long word, absent word, leading space, punctuation, empty-word
  line) pinned in the sample; no character reachable through two alphabet
  rows; no session ending in an empty line. This is
  `serve-thesaurus-lookups` §2's "encode invariants at generation time,
  refuse to write on failure" pattern, extended from 5 invariants to 10.
- **`tools/probe.py mutants`** installs each of the 14 wrong readings as the
  shipped solution and runs `harbor run -p . --agent oracle` — the *real*
  pipeline, not a standalone comparison script — reporting the pytest node
  IDs each fails. All 14 score 0.000.
- **`tools/probe.py bypasses`** performs six attacks through the same real
  pipeline, with the correct program scored in the same run: echo the
  published audit, import the sealed reference off `/tests`, walk the sealed
  tree, symlink the result path at a root-only file, answer from a table
  keyed on the handed-over file name, emit a well-formed empty result. All
  six score 0.000; the correct program scores 1.000 in the same measurement.
- **`tools/calibrate.py`** cross-checks `solution/lexer.py` against
  `tests/_reference.py` — two independently written decompositions (one
  builds a single dict keyed on packed encoding, the other keeps an entry
  list and searches linearly) — over all 15 sessions with no Docker, so
  `oracle=1.000` is not vacuous (`experiment-analysis-frame` §7's concern,
  answered structurally rather than argued).

`deep_review`'s only two advisory notes (non-blocking) were things exactly
this measurement discipline surfaces on its own: one pass@2 trial's failure
was a pure wall-clock near-miss unrelated to the crux (flagged, not acted on
— `rebuild-vestra-systems`/`experiment-analysis-frame` precedent: a timeout
artifact isn't evidence to redesign against), and a latent precedence
divergence between the oracle's overwrite-assignment alphabet map and the
reference's first-match `.find()` that never fires on any shipped title
(left as documented, since acting on it would mean building a fixture for a
divergence that doesn't exist in the four real titles).

---

## 3. What made the released image safe to ship at all

Only `bellrock.z3` (the audited title) is released under
`environment/data/titles/`; the other three (`graveldyke.z4`, `orrerydeep.z5`,
`ciphergate.z5`) live only in `tests/graded/titles/`, overlaid at `/tests`
only at verify time. `CABINET.md` says the library "ran to several dozen
titles" and `titles/` holds only "the ones released with the batch" — true
and non-misleading, without disclosing that three more exist specifically to
carry the crux.

All four images are **archival records, not runnable programs** — the
Reading Room's licence only covered a title's tables (header, alphabet table
where present, dictionary), so code/strings/objects/grammar are zero-filled.
This closes two things at once: it is realistic (public terminal archives
really do have use restrictions like this), and it means a real Z-machine
interpreter is never a shortcut — nothing runs. The header itself is honestly
described: fields pointing at a discarded region read zero and the size/
checksum fields are recomputed over the retained bytes, stated as such in
`CABINET.md` so a reviewer can tell what the bytes mean.

---

## 4. Gate-by-gate log

| Gate | Verdict |
|---|---|
| `changes`, `ratelimit`, `cosine_similarity`, `similarity`, `validation` | pass |
| `review` (rubric) | **PASS, all 31 criteria** first cycle |
| `pass2` | **0/2** — 1 valid-fail (V5 buffer-offset trap, the intended crux, hit clean), 1 in-progress-timeout (agent had a working prototype in `/tmp`, cut off ~55s before the 3600s cap mid-final-write) |
| `deep_review`, `ava_review`, `tier1` | pass, 2 non-blocking advisories only |
| `qc_eval`, `qc_exec`, `qc_gate` | **37/37 checks clean, zero findings, first cycle** |
| `trials` (pass@5) | **pass — 0/5 solved, 4 good-valid-fail, 1 in-progress-timeout, avg@5 = 0.000** |
| `gate` | pass → `accepted` |

One push, zero revisions, ~1h10m total (`pass2` and `trials` each ran
~1h7–1h8m as the long poles). No platform faults, no outages, no re-triggers.

---

## 5. pass@5, and what the model actually did — every designed axis gated

0 solved · 4 good-valid-fail · 1 in-progress-timeout · avg@5 = 0.000. All
`task_specification`/`reward_hacking`/`approach_validity` PASS 5/5 — the
analysis explicitly separated crux failures from the one timeout artifact.

| Failure mode | Trials | Root cause |
|---|---|---|
| Idle-research timeout | 1/5 | 56 steps reading Frotz source, working snippets at step 42, never wrote the deliverable before the cap |
| Separator-as-word not implemented (axis 1) | 3/5 | separators discarded (`continue`) instead of emitted as their own block |
| V5 buffer-byte-2 offset missed (axis 4) | 4/5 | `start + 1` used universally; invisible on the V3 sample |
| V4+ dictionary key width wrong (axis 3) | 2/5 | 4 bytes read for all versions; one trial IndexErrors on a V4/V5 lookup |
| Custom alphabet encoding failure (axis 5) | 2/5 | A1→A0 remapping or A2 slots 0–1 not reserved |

**"No two trials converge on the same exact bug set"** — the pass@5 analysis's
own words — is the direct payoff of building one misreading into five
independent-looking surface symptoms: agents that read different amounts of
the standard fail on different subsets, but nobody who skips the standard
gets more than one or two axes right by luck. The one near-single-bug trial
(`task__6PYdmg9`) got axes 1 and 3 right and missed only axis 4 — exactly the
provision buried in the `read` opcode entry rather than the dictionary
section, confirming that placement (not just conditionality) mattered.

---

## 6. Reusable checklist

1. **Read a repo's own closed PRs before designing**, not just sibling
   repos — `replay-run-histories` §4, now confirmed a second time. A closed
   PR's `qc_gate` transcript tells you exactly what shape of task that
   category's QC probes cannot evaluate.
2. If a predecessor blocked on QC findings with `(no evidence recorded)`,
   the fix is not tighter difficulty on the same shape — it's a shape QC's
   probes *can execute claims against*: deterministic, pure-computation,
   graded by an independently-written reference.
3. Pick a crux that is **one real, conditional, published misreading
   surfacing in several structurally different places**, not several
   independent rules — concentrates the failure rate instead of
   distributing it, and other agents' bug reports will show non-overlapping
   subsets even though there's only one thing to actually understand.
4. Bury the sharpest provision in the section of the named standard the
   solver has the least structural reason to open (here: the `read` opcode
   entry, not the dictionary section the task's own framing points at).
5. Select the shipped sample **by measurement** — a generator that refuses
   to write unless it's provably inert under every latent wrong reading and
   provably refutes the cheap ones — never by hand-picking lines that look
   representative.
6. Build a probe script that performs every soundness claim (mutation sweep,
   bypass attempts, accept-side check) **through the real `harbor` pipeline
   in the same run**, not a standalone comparison. This is what QC actually
   confirms against, and it's what let this task clear 37/37 with zero
   findings on cycle one.
7. Ship only the titles the audited claims need; keep the rest sealed until
   verify time. Describe honestly what was retained and why (a licence/
   preservation constraint reads as realistic and doesn't need to name which
   titles exist beyond what's released).
8. A pass@2 in-progress-timeout with a genuinely working near-complete
   solution is not evidence to redesign against — flag it, don't chase it.

---

## 7. One-paragraph version for future me

The prior PR on this repo (`sub-basement-protocol`) blocked on `qc_gate` with
twelve findings, every evidence field empty, because it graded a compiled,
obfuscated interactive binary that QC's probes could not execute claims
against — and thirty-three commits of tightening turn budgets and obfuscating
strings never changed that. The fix was to change the *kind* of task
entirely: a deterministic pure-Python program (`/app/lexer.py`, a Z-machine
lexical analyser) graded by an independently-written reference, with every
soundness claim backed by a script that performs it through the real `harbor`
pipeline — `tools/generate.py` refusing to write the archive unless ten
invariants hold, `tools/probe.py` scoring 14 wrong readings and 6 bypass
attempts against the actual verifier. The crux itself is one real,
conditional Z-Machine Standards Document provision — "the released title's
own configuration is the format" — surfacing in five structurally different
places (separator-as-word, lower-casing, version-dependent dictionary
resolution, version-dependent text-buffer base, and a custom alphabet table's
reserved slots), selected by measurement so the one released V3 title's
audited session is provably inert under all five while still refuting three
cheaper readings outright. Accepted on the first push: rubric PASS 31/31,
`qc_gate` 37/37 clean with zero findings on cycle one (versus twelve blocking
on the predecessor), `pass@5` landed at the ceiling — 0/5 solved, avg@5 =
0.000, four good-valid-fails each hitting a different subset of the five
axes and one honest timeout — with the pass@5 analysis itself confirming "no
two trials converge on the same exact bug set."
