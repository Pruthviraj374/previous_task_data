# dynamo/collate-modpool-batches — the axis I nearly cut was the axis that worked, and "read the spec" did not save anyone

| | |
|---|---|
| **Outcome** | **ACCEPTED** — 17 checks pass, 0 fail, `accepted` label |
| **Repo** | `dynamo-03da6c3-mathematics-and-formal-reasoning`, branch `submission`, fork `charan-sr` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-03da6c3-mathematics-and-formal-reasoning/pull/1 |
| **Category / sub** | Mathematics and Formal Reasoning / **Number theory and exact arithmetic** (pre-seeded) — **first task in this category in the corpus** |
| **Benchmarked model** | `task.toml` names Opus-4.8 / Terminus-2; trials logged `Model A` on Daytona |
| **Final commit** | `67100e2` (**two pushes total**) |
| **Headline** | **pass@2 = 0/2 both valid fails, pass@5 = 2/5, avg@5 = 0.400, 3 good valid fails.** `qc_gate` clean first try. Push 1 failed exactly one rubric criterion and nothing else |

Two pushes, no redesign. That is the cheapest acceptance in this corpus alongside
`replay-rulepack-scores`, and it happened because the corpus's own rule — **in a
category where every fact is derivable, the crux cannot live in the domain** — was
applied *before* the first line of code instead of being rediscovered over four
pass@2 rounds. What this file adds is three things the corpus did not already know.

**One: requiring the agent to read a format spec does not kill a latent crux.**
I nearly abandoned this design over that worry. See §3.

**Two: my ranking of my own axes was inverted for the sixth time — and this time my
own mutant battery is what misled me.** See §4. The fix is a change to how mutants
are built, not to how axes are chosen.

**Three: the `You have N seconds…` line is a rubric FAIL condition.**
`00-ATTEMPTER-SPEC.md` §3 says CI enforces it. That is stale. Second confirmation.

---

## 1. What the task asks

MODPOOL was a distributed exact-arithmetic service. A job's value was never computed
directly: each worker node got a distinct prime modulus and reported only the value
modulo that prime. The collator that combined the shards is gone; the archives are not.

- **Agent sees:** `instruction.md`, `/app/data/ARCHIVE.md` (what a batch holds, in
  Erlang term syntax, plus the sentence that the format is the one Erlang documents
  with no MODPOOL extensions), and `/app/data/example/` — one archive `BQ-2214.bin`
  next to `BQ-2214.json`, the report the real collator wrote for it.
- **Agent produces:** `/app/collate.py`, invoked
  `python3 /app/collate.py <archive.bin> <report.json>`.
- **Graded on:** **20 held-out archives**, none under `/app`; 22 tests, all-or-nothing.
- **Output per job:** `job_id`, `numerator`, `denominator`; plus the batch's exact sum.
  **Exact integer equality everywhere** — no tolerance exists anywhere in the verifier,
  so no `difficulty_evidence` "threshold artifact" argument is available to anyone.
- **Constraint:** Python standard library only, no network, no input beyond the archive
  path. Enforced at run time by an audit hook, never by scanning source.

---

## 2. The design decision, made before any code

Number theory is the most hostile possible category for a derivable-crux design,
because mathematics is derivable by construction. `sdf-registration-qc` established
the rule as an accidental controlled experiment; `replay-fleet-survival` re-confirmed
it four rounds running in statistics. Applied here prospectively:

> **The arithmetic is the ninety percent the model gets right, so name it outright and
> spend nothing on it. Put the crux in the archive's encoding.**

So `instruction.md` states the whole algorithm — drop the voided shards, CRT the rest,
rational-reconstruct against `B = floor(sqrt((M-1)/2))`, sum exactly. All five trials
implemented that correctly. `approach_validity` PASS 5/5. It cost nothing and it
removed every ambiguity objection: `unambiguous` PASS, `task_specification` PASS 5/5.

The crux is that an archive is one Erlang term from `term_to_binary/2`, and that format
encodes the *same value* differently depending on its width and contents:

| Axis | Naive reading | Truth | Held-out witnesses |
|---|---|---|---|
| **A1** bignum digits | big-endian, as `INTEGER_EXT` is | **least significant byte first**, sign-and-magnitude | 8 |
| **A2** list of ints all in 0..255 | a list (`LIST_EXT`) | **`STRING_EXT`** (tag 107), a byte array | 6 |
| **A3** whole term | plain | may be **zlib-wrapped** (tag 80) | 4 |
| **A4** atoms | UTF-8 tag (119) | older releases emit **`ATOM_EXT`** (100) | 4 |

A1 is the shape `restore-runbook-advisor` §6 found strongest — **a rule with an
exception, punishing over-application**. The shipped example *teaches* big-endian via
32-bit integers, and that generalisation is wrong for wider ones.

The example is inert on all four: moduli fit in 32 bits, every void list names a node
above 255, it is uncompressed, and it came from a modern node. Every one of those is
covered by a plausible in-world reason stated in `ARCHIVE.md` without ever naming the
consequence ("node numbering was never reset… both generations stayed in service";
"moduli were sized per batch to the width of the values that batch was after").

---

## 3. The worry that nearly killed the design, and why it was wrong

Half the design time went into this objection:

> The agent **cannot decode anything at all** without looking up the ETF tag table.
> Unlike `sdf`'s fixed-width CTfile columns or a `.dbf` header, there is no way to
> parse the file by inspection. It *must* fetch the spec — and "digits are stored with
> the least significant byte stored first" and the compressed-term section are on that
> same page. So the crux dies on the first search.

**That reasoning is wrong, and the corpus already contained the counter-evidence I
failed to weigh: `replay-fleet-survival`'s dBase deleted-record flag is documented in
every dBase format reference and still took 4 of 5 trials.** The trial analysis here
says it outright:

> *"Both agents stopped reading the specification once they could parse `BQ-2214`,
> missing the documented COMPRESSED and STRING_EXT tags."*

and again at pass@5:

> *"the three failing agents validated only against BQ-2214 and shipped without testing
> STRING_EXT or compressed archives independently."*

**The rule that generalises:**

> **"The agent must consult the spec" is not the same as "the agent will read the whole
> spec."** It reads until the shipped sample parses, then stops. A crux living in a
> section the sample gives it no reason to reach is as latent as one that is not written
> down at all — and it is strictly *fairer*, because `decisive_answer_discoverable`
> passes on the public standard with internet left on.

Corollary worth keeping: this makes documented-but-large binary formats a **renewable**
crux source. The bigger the spec, the more of it the sample can leave unreached.

---

## 4. The axis ranking was inverted, and my own mutant battery caused it

Sixth confirmation of `restore-runbook-advisor`'s finding, and the second time the axis
I nearly cut did all the work.

| Axis | My rating before pushing | What actually happened |
|---|---|---|
| **A1** bignum LSB-first | **flagship**, 8 witnesses | **5/5 trials got it right.** Gated nothing, ever |
| **A2** `STRING_EXT` | **weakest; nearly cut** | **2 of 3 pass@5 failures**, 1 of 2 pass@2 failures |
| **A3** compressed term | weak "implement the whole spec" filler | **both** pass@2 failures, 1 of 3 pass@5 failures |
| **A4** legacy atoms | filler | never gated |

### 4.1 The specific mistake: I modelled the wrong mutant

I built `byte_list_as_bytes` (tag 107 decoded to `bytes` instead of `list[int]`),
watched it score **1.0** through the real verifier — because in Python `bytes` iterate
as integers, so `node not in dead` still works — and downgraded A2 to a footnote in
`tools/mutants.py` and the PR body.

Both real A2 failures were something else entirely:

- `task__mwQp5QB` decoded tag 107 with `.decode('latin-1')` → a `str` → `TypeError:
  int not in str`.
- `task__7AXHvTk` **never implemented tag 107 at all** → `ValueError: Unknown ETF tag:
  107`.

I had built the first (`byte_list_as_text`, which correctly failed 6 batches) and then
let the *harmless* variant set my confidence. And I had **not built the second at all**.

> **Rule: build the "branch absent entirely" mutant, not only the "branch wrong"
> mutant.** For any latent tag/opcode/record type, an agent that never implements it is
> a more common failure than one that implements it wrongly, and it is a *different*
> mutant. `tools/mutants.py` here modelled `no_compressed_term` and `no_legacy_atom`
> that way and modelled A2 only as a misread. The one I skipped is the one that fired.

> **Rule: a mutant scoring 1.0 tells you that reading survives. It does not tell you the
> axis is weak.** `statement-rollup-repair` §5 says a mutant producing an identical
> answer is a coverage hole; the sharper version is that it is a hole *in the mutant
> set*, and the fix is more mutants, not a lower opinion of the axis.

### 4.2 A failure mode the corpus had not recorded: the cursor bug

`task__qFFcUCV` **knew** about tag 80, detected it correctly, and still failed — it
called `_uint32()` with the reader still on the `0x50` tag byte, absorbing `0x50` as the
size field's MSB and starting the zlib stream one byte early. Four batches, one missing
`pos += 1`.

> **A latent case that requires *repositioning a cursor* gives two independent chances
> to fail: knowing the rule, and landing the offset.** Prefer latent forms with a header
> the decoder has to step over to ones that are a pure value reinterpretation. The
> analysis called it out as a distinct root cause from A2, which is why pass@5 came back
> **stratified** (2 causes across 3 failures) rather than as one shared bug.

### 4.3 Combining two axes in one fixture is worth doing deliberately

`BQ-2316` is compressed **and** has small node numbers. It failed in **all three**
failing trials, for two different reasons. Every other batch failed in at most two.
One fixture per axis proves coverage; one fixture carrying two axes raises the floor.

---

## 5. Gate-by-gate log

| Push | Commit | What it did | Result |
|---|---|---|---|
| 1 | `985d8b2` | initial submission, 4 axes | `changes` ✅ · `cosine_similarity` ✅ · **`review` ⛔ 30/31** — `instruction_concision` only |
| 2 | `67100e2` | dropped the time-budget line; named the real-world audience in `difficulty_explanation` | **all 17 ✅** — `review`, `similarity`, `validation`, **`pass2` 0/2 both valid**, `deep_review`, `ava_review`, `tier1`, `qc_eval`, `qc_exec`, **`qc_gate` first try**, `trials` **2/5** → `accepted` |

Gates that never failed: everything except `review` on push 1.

### 5.1 `instruction_concision` — the stale-spec trap

> *"`instruction.md:47` ends with "You have 3600 seconds to complete this task. Do not
> cheat by using online solutions or hints specific to this task." This is the exact
> TB3-format time-budget/anti-cheat boilerplate the criterion enumerates as a FAIL…
> The contributor must delete this line."*

`00-ATTEMPTER-SPEC.md` §3 states the line is mandatory and "CI enforces this
(`check-instruction-suffix`)". `restore-runbook-advisor` §10 already recorded the
opposite from live evidence and I overrode it in favour of the doc. **Trust the corpus
over the spec pages on this one; that is now two independent confirmations.** It cost a
whole push, on an otherwise-perfect 30/31.

### 5.2 Why `qc_gate` passed first try

The corpus warns `qc_gate` finds one issue per round by design. What pre-empted it was
the generator invariant, asserted at write time, in **both** directions:

- every **latent** misreading must reproduce the shipped example *bit-identically*;
- every **stated** rule must **fail** the shipped example, and also fail ≥1 held-out
  batch;
- each latent misreading exposed by **≥3** held-out batches (actual: 8 / 6 / 4 / 4);
- every documented output shape witnessed (negative numerator, zero value, denominator
  1, denominator > 1, a void entry naming a node that filed nothing).

`tools/generate.py` writes nothing if any of these breaks, so re-shaping the fixture mix
cannot silently rot them. This is `restore-runbook-advisor` §2 and
`replay-fleet-survival` §2 applied preventively, and it is the third task in a row where
doing so cleared `qc_gate` on the first attempt.

### 5.3 The two borderline advisory notes

The rubric graded PASS on both but flagged them; I fixed one and left one:

- `difficulty_explanation_quality` — *"never states who in the real world would solve
  this"*. Fixed in push 2 with one sentence. **Cheap; do it pre-emptively next time** —
  the field needs an audience, not just a mechanism.
- `no_extraneous_files` on `task/tools/` — graded PASS because `task/README.md`
  documents it as reviewer tooling. `restore-runbook-advisor` §3.4's fix works and is
  worth doing from push 1.

---

## 6. Verification discipline that paid off

Everything below happened **before** the first push.

- **Verified the format against a real OTP node, not from documentation.**
  `tools/check_against_otp.py` encodes 256 generated terms with the fixture writer and
  diffs them byte-for-byte against `docker run erlang:26-slim`. 0 mismatches. This is
  `keepcase-restore` §3's rule (a doc summary is a hypothesis; the runtime is the
  experiment) applied to a wire format instead of a syscall. It also confirmed the
  boundaries that make the sample inert — `255`→tag 97, `256`→tag 98, `2^31`→tag 110,
  `[1,2,3]`→tag 107, `[1,2,300]`→tag 108 — which is exactly what the design rests on.
- **Ran every mutant and every cheat probe through the *real* verifier**, not just
  in-process: `tools/mutants.sh` builds the image, drops each candidate at
  `/app/collate.py` with `tests/` overlaid, and runs `tests/test.sh` as Harbor does.
  Reference 1, ten flawed collators 0, three probes 0.
- **Three cheat probes written out as files** (read the sealed reports, echo the shipped
  example, open a socket). `ava_review` passed first time it ran.
- **The graded archives ship no answer.** `/app/data/example/` carries a *different*
  archive with its report, so the end-to-end self-check survives with nothing to diff
  against what is scored (`merge-lora` §4.1, `replay-fleet-survival` invariant 3).
- **The verifier seals its own ground truth two ways**: it reads the 20 expected reports
  into memory and `rmtree`s them before any agent code runs, *and* `run_collator.py`
  installs a `sys.addaudithook` denying network, subprocesses and any path under
  `/tests`. Runtime enforcement, never a source scan (`keepcase-restore` §5.8).
- **Timed the verifier against the broken program, not the oracle**
  (`statement-rollup-repair` §4a). 21 runs × `RUN_TIMEOUT` must stay under the 300 s
  `qc` probe cap, so `RUN_TIMEOUT = 12` (60× the reference's actual 0.2 s), worst case
  252 s. All three failing trials crashed immediately, so the real suite never
  approached it.

---

## 7. Bugs I introduced myself

1. **Rewrote atoms by scanning raw bytes for `0x77`.** The first `legacy_atoms`
   implementation post-processed the encoded term looking for tag 119; it matched byte
   119 *inside binaries and integers* and produced corrupt archives. Caught in seconds
   because `tags_present()` threw `unsupported term tag 0` on `BQ-2318` — a
   structural walker over the fixtures is worth having for its own sake. Fixed by
   threading the option through the encoder instead of patching its output.
2. **Included the time-budget line against the corpus's recorded advice.** §5.1.
3. **Let a harmless mutant set my confidence in an axis.** §4.1.
4. **Never modelled "tag absent entirely" for A2.** §4.1.

---

## 8. Reusable checklist

Design:
- [ ] In a category whose facts are derivable (mathematics, statistics, physics), **name
      the algorithm outright** and put the crux in a format or engine. It costs nothing
      and buys `unambiguous` + `approach_validity` outright.
- [ ] Prefer a **large, real, public** binary format. Needing the spec is fine — agents
      stop reading it once the sample parses. The bigger the spec, the more of it the
      sample leaves unreached.
- [ ] Prefer latent forms that require **stepping a cursor over a header** to pure value
      reinterpretations: two chances to fail instead of one.
- [ ] Give at least one held-out fixture **two axes at once**.
- [ ] Give every inertness property an in-world reason stated in the data note, never
      the consequence.

Mutants:
- [ ] For every latent tag/opcode/record type, build **both** mutants: *branch wrong*
      **and** *branch missing entirely*.
- [ ] A mutant scoring 1.0 is a hole in the mutant set, not evidence the axis is weak.
- [ ] Run them through the **real** verifier in the built image, plus cheat probes.

Format fidelity:
- [ ] Cross-check any fixture writer **byte-for-byte against the real implementation**
      in a container before designing around it.
- [ ] Include the boundary values the inertness argument depends on in that cross-check.

Packaging:
- [ ] **Omit the "You have N seconds…" line.** `00-ATTEMPTER-SPEC.md` §3 is stale; the
      rubric FAILs it. Two confirmations now.
- [ ] `difficulty_explanation` must name **who in the real world does this work**, not
      only what makes it hard.
- [ ] `task/README.md` indexing `task/tools/` from push 1.
- [ ] `.gitattributes` with `* text=auto eol=lf` and `*.bin binary`; verify staged blob
      hashes match the working tree before committing binary fixtures.

---

## 9. One-paragraph version for future me

The first Mathematics and Formal Reasoning task in this corpus, accepted in **two
pushes** at **pass@5 2/5, avg@5 0.400**, by applying the corpus's own derivability rule
prospectively instead of rediscovering it: the number theory — CRT over per-node prime
residues, rational reconstruction at `floor(sqrt((M-1)/2))`, exact rational summation —
is stated in full in `instruction.md` and was implemented correctly by 5/5 trials, while
the crux sits entirely in the archives being Erlang external terms, whose encoding of a
value changes with its width and contents in four ways the shipped example is
constructed to leave inert. The design worry that nearly killed it — that ETF is
undecodable without fetching the spec, so the crux is one search away — was simply
wrong, and the analysis says why in the model's own behaviour: *"both agents stopped
reading the specification once they could parse BQ-2214."* Needing the spec is not
reading the spec, which makes big documented binary formats a renewable crux source.
The expensive lesson is that **my own mutant battery inverted my axis ranking**: I built
a harmless variant of the `STRING_EXT` axis, watched it score 1.0 because Python bytes
iterate as integers, downgraded the axis to a footnote — and it then caused two of three
pass@5 failures, one as a `str` decode and one as *a tag never implemented at all*, a
mutant I had not built. Build the branch-missing mutant alongside the branch-wrong one,
and never let a surviving mutant lower your opinion of an axis. Also confirmed for the
second time in this corpus: the `You have N seconds…` line is a rubric **FAIL**
condition and `00-ATTEMPTER-SPEC.md` is stale on it — that single line was the only
thing wrong with push 1's otherwise-clean 30/31.
