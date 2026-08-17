# dynamo/nfs4-access-audit — Systems Infrastructure and Operations / Users Permissions and Access Control

**Accepted on push 2 (`a50aabf`). pass@2 0/2, pass@5 0/5 (five good valid fails, avg@5 = 0.000),
`qc_gate` clean on its first cycle with an empty fix list.** Three pushes total, one of which
(axis E) was built, validated and then deliberately **never pushed**.

> ## ⚠ Overlap with `dynamo-831b96e-filer-access-audit` — read before reusing this design
>
> That task is **also accepted**, in the **same category and the same sub-category**, from the
> same fork. It is also a decommissioned-filer ACL audit producing a per-request `ALLOW`/`DENY`
> from an archive, graded on held-out exports, with its crux in conditional clauses of the NFSv4
> ACL standard (RFC 8881 §6; this task uses RFC 7530 §6 — the same family, same section).
> Its axis **A1** (ordered ACE evaluation, an ALLOW before an overlapping DENY) is this task's
> axis **A**, and its axis **A5** (`EVERYONE@` includes the owner and owning group, not the POSIX
> other class) is this task's axis **B** — the same rules, not merely the same shape.
>
> By the "reuse the machinery, never the task idea" rule this pairing shares all three
> disqualifiers at once: the same artifact, the same governing authority, and the same scenario
> shape plus crux family. Both cleared `similarity`/`cosine_similarity` because those gates
> compare against TB2/TB3, **not against sibling Dynamo submissions** — mine returned UNIQUE at
> 0.156. Human review is where this surfaces.
>
> **Why it was missed:** the sibling's write-up was created at 04:06 by a concurrent session,
> after this task's survey of `previous_task_data/` and while its design was already being built.
> The directory listing is not a snapshot you can take once. **Re-check it, and the repo's open
> and merged PRs, immediately before opening the PR — not only at design time.**

---

## 1. The task

A filer is being decommissioned. `/app/export/` holds the access-control export from one of its
volumes: NFSv4 ACLs in `nfs4_acl(5)` textual notation, object kinds, a user-to-group map, a set
of access checks, and the decisions the filer itself returned for them. The agent writes
`/app/solve.py <export_dir> <requests_tsv> <out_tsv>`, emitting `PERMIT`/`DENY` per request, and
is graded on two further volumes it never sees plus unseen checks against the shipped one.

The whole task is one question repeated: would an NFSv4 server enforcing RFC 7530's `acl`
attribute have granted every permission in the requested mask? The instruction names RFC 7530 as
the governing model and enumerates none of its rules.

---

## 2. The crux, and the invariants that keep it alive

Four axes shipped, all real published RFC 7530 clauses, all conditional, all silent when wrong.

| Axis | Rule | Natural mistake | Gated in pass@5? |
|---|---|---|---|
| **A. Stored ACE order** | §6.2.1 — processed in stored order; a DENY bites only on bits an earlier ALLOW has not granted | order-agnostic "any matching deny wins" | **yes, 1 of 5** |
| **B. Special identifiers** | §6.2.1.5.1 — `EVERYONE@` is literally everyone incl. owner and owning group | map onto POSIX group/other classes | no |
| **C. Removal spans two objects** | §6.2.1.3.2 — an explicit grant of `d` on the object **or** `D` on the parent stands, even against an explicit denial on the other side | treat `d` as an ordinary bit on the target | **yes, 5 of 5** |
| **D. Audit/alarm entries** | §6.2.1 — AUDIT/ALARM share the list but do not affect access | let the first matching entry decide whatever its type | no — see §3 |

**The invariants, each asserted by `tools/calibrate.py` on every push:**

1. **The shipped sample is inert under every wrong reading.** 0/51 wrong under all nine (later
   ten) mutants. Not curated by hand — `build_fixtures.py` *draws* the shipped request set only
   from checks where the correct model and every mutant agree. Inertness is a property of the
   construction, not of my judgement.
2. **Every held-out set discriminates every wrong reading**, with a per-set count.
3. **The shipped sample pins the disclosed machinery.** Machinery mutants (`ignore_everyone`
   16/51, `default_allow` 12/51, `ignore_owner_at` 7/51, `ignore_group_aces` 2/51) must all
   *fail* the sample, so nothing disclosed is underdetermined by what the agent sees.
4. **No graded request reaches a shape two defensible readings would split.** Two exclusions:
   the §6.2.1.3.2 branch where neither side is explicit (falls to a mode attribute the export
   does not carry), and read questions where §6.3.1.1 could be argued to reach a directory.
5. **The reference reproduces every `expected.tsv` exactly** — added late, after I noticed I had
   been *inferring* this from the oracle run rather than checking it.
6. **`instruction.md` names no deciding case** — a grep for the giveaway vocabulary.
7. **Two independently-written implementations agree on every question either volume can pose**
   (2660–3178 across versions). `solve.py` walks a running mask; `_reference.py` resolves each
   letter independently. `oracle = 1.000` is a cross-check, not an echo.

---

## 3. Dead ends

### 3.1 A disclosed-format axis is not a crux (axis D — measured, cost one push)

After pass@2 round 1 showed the task resting on axis C alone, I added AUDIT/ALARM (`U`/`L`)
entries, reasoning that the first-match-per-bit walk both agents wrote would read a `U` entry as
"not an allow" and deny. **Wrong.** In round 2 both agents skipped `U`/`L` correctly, unprompted,
and in pass@5 all five did. The analysis says so verbatim: *"Skip ACEs of type AUDIT (`U`) and
ALARM (`L`)."*

**Why it failed:** `nfs4_acl(5)` labels the types `Audit` and `Alarm` in the same table that
defines `A` and `D`. Once the *format* is disclosed the right call is obvious — an entry named
"audit" plainly is not an access decision. This is `experiment-analysis-frame` §3.3's
memorised-vs-noticed test in a new costume: a **type label the agent can read off the format** is
memorised; a **behavioural exception buried in prose** must be noticed.

**Transferable rule:** an axis that lives in the *vocabulary of the format* will be solved. An
axis that lives in a *prose exception to the algorithm* will not. Axes C and E are both the
second kind; D was the first.

### 3.2 Things rejected on paper, before any code

- **NTFS/SDDL effective-access evaluation** — same crux family, but no way to generate ground
  truth by running the real thing, and the sibling merged task in this repo is Windows-adjacent
  in flavour.
- **PAM stack replay** (`include` vs `substack` jump confinement) — genuinely excellent crux, but
  the environment can host real libpam, so an agent could write stub modules and *execute* the
  answer. Rejected for having an escape hatch, not for being weak.
- **NFSv4 ACL inheritance** (`f`/`d`/`i`/`n` flag propagation) — the strongest remaining axis, and
  I dropped it deliberately: the already-merged task in this same repo is *POSIX default-ACL
  inheritance on a shared directory*. Same subcategory, same "permission inheritance" mechanism.
  A human reviewer would read them as one idea. Cost me an axis; worth it.

---

## 4. What worked

### 4.1 Mechanical inertness beats curated inertness

The single highest-value decision. I did **not** hand-pick sample requests that happened to avoid
the crux; I wrote the wrong readings first, then had the builder select only from the agreeing
set. Consequences:

- adding an axis later could not silently break inertness — the builder re-derived it;
- adding a mutant automatically shrank the eligible pool, so the sample got *safer* as I thought
  of more wrong readings;
- pass@5 confirmed it end to end: all five trials passed `test_shipped_audit_written` **and**
  `test_shipped_recomputed`, then failed all three held-out tests.

The analysis names this as the mechanism: *"The shipped data contains no `d`-requests whose
correct outcome depends on the parent `D` check, so validation against expected.tsv was always
clean — no ground-truth signal existed to reveal the gap."*

### 4.2 Keep the axis that "did not gate" — now confirmed a third time

Axis A (stored ACE order) was solved by both pass@2 agents in both rounds. By the reasoning that
killed axis D, it looked like dead weight. I kept it because `reduce-palaeomag` §4.2 says to, and
in pass@5 **one trial of five failed on exactly it** — an order-agnostic accumulator, 24/36/24
wrong decisions, a far worse failure than the near-misses.

The pass@2 signal was a two-sample estimate and it was wrong about A. `rebuild-readout-builder`
§3.1's "0/2 is not evidence" cuts both ways: it is also not evidence that an axis is *inert*.

### 4.3 Scoring mutants through the real verifier, not through arithmetic

`tools/probe_verifier.py` builds the image, drops a mutant in as `/app/solve.py`, and runs
`tests/test.sh` exactly as Harbor does. The target shape — *passes every shipped test, fails
every held-out test* — is the amplifier stated as an executable assertion. It caught two things
arithmetic could not:

- the **tamper bypass** AVA flagged (see §5.1), proven closed by executing the attack;
- my own probe silently producing **no output at all**, which I nearly read as a pass. A `re.sub`
  replacement-escaping bug (`\n` in the replacement string is interpreted) had made the generated
  mutant invalid Python. *A mutant that scores 0 because it never ran looks identical to a mutant
  that scores 0 because the trap fired.* Assert the mutant compiles.

### 4.4 Answering an advisory by declining it, in writing

`ava_review` advisory: assert "stdlib-only" directly, e.g. run the solver under `-I`/`-S`. I
declined. `-I` strips the script's own directory from `sys.path`, so a solver that split itself
across two files would fail — the corpus records *two tightenings that rejected a correct
solver*, and `contact-export` §3.2 records three pushes proving source scans cannot keep this
promise. The reviewer's own words were "adequate" and "Optional."

I put the reasoning in the README rather than leaving it looking like an oversight. Cost: four
lines. It converts a silent omission into a visible decision for the human reviewer.

---

## 5. Gate-by-gate log

### Push 1 — `3c6f9fd` (three axes: A, B, C)

Static ✅ (25/25 first time) · rubric ✅ 30 PASS / 1 N/A · similarity ✅ UNIQUE (closest 0.156) ·
validation ✅ · `deep_review` ✅ PASS · **pass@2 0/2, both valid** · `ava_review` ❌ **BLOCK**.

### 5.1 The only blocking finding in the whole task

`sound_verifier`: `test_shipped_audit_written` read ground truth from `/app/export/expected.tsv`
— **agent-writable, never sealed** — with a bare `open()`, and the artifact itself was read
without the `O_NOFOLLOW`/link/containment guard the held-out runs already used. `deep_review`
raised the same thing as non-blocking Advisory #2, judging it non-exploitable because the
held-out tests still fail. AVA blocked anyway, and was right to: the defect is real regardless of
whether another test outvotes it.

**Fix:** every graded input and every expected file moved to `tests/shipped/`, a trusted copy
inside the sealed tree. `/app` is now consulted for exactly two things — the program, and the
artifact it was told to leave. Proven by `tamper_expected`, which rewrites
`/app/export/expected.tsv` and emits a matching forgery: before, it passed the artifact test;
after, it fails both shipped tests.

**Lesson:** *nothing under `/app` may be ground truth or graded input.* Not "nothing exploitable"
— nothing at all. Half the tests were already correct on this; the inconsistency is what got
flagged.

### Push 2 — `a50aabf` (axis D added, AVA fix) — **accepted**

Static ✅ · rubric ✅ · similarity ✅ · validation ✅ · `deep_review` ✅ · `ava_review` ✅ ·
**`qc_gate` ✅ 37 checks and probes, `QC-FIXES-B64:W10=` (empty)** · `tier1` ✅ ·
**pass@2 0/2** · **pass@5 0/5**.

`qc_gate` clean on the first cycle — against four rounds on `experiment-analysis-frame` and three
on `retired-normalizer`. The invariants in §2 were written *before* push 1, which is
`reduce-palaeomag` §4.4 applied preventively and it worked again.

### 5.2 pass@5 value table (`a50aabf`, 178/202/196 held-out)

| Trial | Root cause | Errors (alpha/bravo/charlie) | near_miss |
|---|---|---|---|
| TGBC4Ac, LJ4nUgJ, Nehrq7G, ADDBAos | **C** — no parent `D` lookup | 6 / 12 / 10 | IS a near-miss |
| VxxjCVt | **A** — order-agnostic accumulator (+C) | 24 / 36 / 24 | not a near-miss |

Every wrong decision in every trial was `DENY` where `PERMIT` was correct. `approach_validity`
PASS 5/5, `difficulty_crux` PASS 5/5, `reward_hacking` PASS 5/5, `low_timeout` PASS 5/5 (agents
finished in 4–40 min of 3600 s). Grader's verdict: *"the task design — using a shipped sample
that deliberately avoids the crux — functions exactly as intended."*

### Push 3 — `1dd75d4` (axis E) — **built, validated, never pushed**

RFC 7530 §6.3.1.1: *"All servers **will** allow a user the ability to read the data of the file
when only the execute permission is granted."* A second behavioural exception to the uniform
per-bit walk, reached by a different question from C, and an agent that finds §6.2.1.3.2 and
stops still fails it. Discriminates 16/20/22. Calibration clean, oracle 1.000, mutant verified
end to end.

Then pass@5 came back 0/5 and the insurance was not needed. **Held, not pushed** — a push
re-rolls all 31 rubric criteria plus `deep_review`/`ava_review`/QC and burns a rate-limited
slot, to improve a task already at the ceiling. `reassemble-tap-sessions` §6 and `merge-lora` §7,
followed literally.

---

## 6. Error → what to do, and what not to do

| Situation | Do | Do **not** |
|---|---|---|
| An axis you added was solved by every agent | Ask whether it lives in the **format's vocabulary** (memorised) or in a **prose exception to the algorithm** (noticed). Only the second gates | Make the same kind of axis stranger |
| An axis "did not gate" in pass@2 | **Keep it.** Two trials cannot see a ~20% failure mode; ours failed a fifth-trial agent | Cut it as dead weight |
| Any verifier read of a path under `/app` | Move ground truth and graded inputs into the sealed tests tree; guard every read with `O_NOFOLLOW` + nlink + realpath | Argue it is non-exploitable because other tests outvote it |
| An advisory tells you to tighten anti-cheat | Check whether the tightening can fail a *correct* solver. `-I` strips the script dir from `sys.path` | Add a source/AST screen — three pushes elsewhere proved each fix invites the next bypass |
| A mutant scores 0 | Confirm it **ran**. Compile it; check the probe produced test output | Read an empty result as a caught trap |
| A rule in your chosen clause is a `MAY` | Make it unobservable — here, `c`/`C` were dropped from the requestable letters entirely | Grade a decision a `MAY` could legitimately flip |
| Your task is accepted and you hold an improvement | Keep it on the local branch, validated | Push it |

---

## 7. Process notes

- **Never push while a run is in flight.** pass@5 took 49 minutes; a push during it cancels a
  rate-limited slot. Two loop iterations did nothing but confirm `trials` was pending — correct
  behaviour, not idleness.
- **`.dockerignore` from the first commit** (build context has `data/`). Static passed 25/25 on
  push 1.
- **No `"You have N seconds"` line.** Rubric `instruction_concision` PASS; instruction measured
  487 cl100k tokens against the 1500 cap.
- **Fold the metadata rewrite into the same commit as a mechanism change.** `difficulty_
  explanation` / `solution_explanation` / `verification_explanation` restate the design
  independently of the README and are graded separately. Both mechanism pushes rewrote all three.
- **The README pre-push gate caught a real drift**: the shipped `requests.tsv` changed while
  `expected.tsv` did not, which looked like a bug. It was genuine — but I had been inferring it
  from `oracle = 1.000` rather than checking, which is how invariant 7 got written.
- **The banned-word grep needs precision.** Banning `"audit"` false-positived on the
  instruction's own phrase "effective-access audit". Ban `"audit ace"` / `"audit entr"`, not the
  bare noun.

---

## 8. Reusable checklist

- [ ] Category/subcategory pre-seeded — check whether the repo already holds a **merged** task,
      and design away from its mechanism, not just its nouns.
- [ ] Crux is a **prose exception to an algorithm** in a named standard, not a label in the
      format's own vocabulary.
- [ ] At least **two** such axes, reached by different questions, before spending a `trials` slot.
- [ ] Sample request set selected **mechanically** from checks where every wrong reading agrees.
- [ ] One mutant per mechanism; each asserted to compile and to actually run.
- [ ] Machinery mutants must **fail** the sample — nothing disclosed left underdetermined.
- [ ] Every shape two defensible readings would split is excluded from all request sets, asserted.
- [ ] Any `MAY` in the chosen clause made unobservable by construction.
- [ ] Two independently-formulated implementations, agreeing on every question the data can pose.
- [ ] Reference reproduces every `expected.tsv` — asserted, not inferred from the oracle.
- [ ] Nothing under `/app` is ground truth or graded input; every verifier read guarded.
- [ ] `.dockerignore` present; no `"You have N seconds"` line; instruction ≥20 tokens under cap.
- [ ] README and all three `task.toml` explanations rewritten in the same commit as any mechanism
      change.

---

## 9. One-paragraph version for future me

Pick a real standard the instruction can *name* without enumerating, then hide the **occasion**
rather than the rule: ship data exhibiting every deciding shape, and select the sample request
set mechanically so no visible question turns on any of them. Write the wrong readings before the
fixtures and let the builder enforce inertness, so the sample gets safer every time you think of
a new way to be wrong. Prefer axes that are prose exceptions to an algorithm — a type label in
the format's own table (`Audit`, `Alarm`) will be read correctly by every agent, while a clause
saying "consult the parent directory too" or "execute carries read" will not. Keep the axis that
pass@2 says is inert; two trials cannot see a 20% failure mode, and ours took down a fifth-trial
agent. Never let the verifier read anything from `/app`. And when it is accepted at 0/5, stop
pushing.
