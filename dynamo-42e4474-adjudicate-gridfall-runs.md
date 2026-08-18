# dynamo-42e4474 — adjudicate-gridfall-runs

| | |
|---|---|
| **Outcome** | **ACCEPTED** — every gate green, `accepted` label |
| **Repo** | `dynamo-42e4474-games-puzzles-and-interactive-simulation`, PR #2 |
| **Category / sub** | Games Puzzles and Interactive Simulation / **Puzzle solving** (pre-seeded) |
| **Final commit** | `251d160` |
| **Headline** | **pass@5 = 2/5 solved, avg@5 = 0.400**, 3 good valid fails, 0 soft-timeout. pass@2 was 0/2 then 1/2 |

Rebuild a scrapped falling-block puzzle cabinet's replay adjudicator as
`/app/adjudicate.py` from an invented container note, graded exactly on 28 shipped
and 52 held-out attempts.

---

## 1. The design, and why it worked

Straight application of `dynamo-81613d4-rebuild-lumenp-plates`' rule:

> **The container is invented and fully specified. The deciding behaviour is real,
> external, publicly documented, and deliberately not restated.**

`GRIDFALL.md` is normative for everything the cabinet's designers invented — pack
schema, 22x10 well and coordinate order, per-piece spawn cells and rotation-box side,
the quarter-turn mapping, feed position, seven control characters, hard-drop locking,
line clearing, the three ways an attempt ends. It names two things and restates
neither: **the Super Rotation System's wall kicks** and **Guideline hold semantics**.

Five wrong readings survive the shipped pack, each producing a well-formed result
with no crash:

| # | Reading | Fires only when |
|---|---|---|
| 1 | published kick offsets are `(x, y)` with **y up**; applied to a top-down row index without negating | a kick with non-zero vertical component resolves |
| 2 | reusing the JLSTZ kick table for `I`, which has its own | an `I` rotation is blocked in its basic position |
| 3 | a banked piece re-enters as banked, not in spawn state at the feed position | hold pressed after the piece turned or shifted |
| 4 | hold usable more than once before the next lock | hold pressed twice for one piece |
| 5 | kick tests scanned in the opposite order | a kick past the first test resolves |

**The y-sign one is the most transferable idea in this file.** The authoritative
tables are published with y increasing *upwards*; any array-indexed board runs
downwards. That is a real, unavoidable conversion the published source does not do
for you, and it is invisible until a kick displaces vertically. pass@2 caught an
agent making exactly it.

## 2. What made the shipped pack safe — measured, never assumed

Candidate attempts were generated in bulk, every wrong reading run over each one, and
only attempts where **all five agree with the reference** were kept. Measured profile
by kick test index (the table that drove every later decision):

| cell | kills |
|---|---|
| non-I, test 1 | nothing — fully inert |
| non-I, test 2 | `nokick`, sometimes `lastkick` — **never** `ysign`/`itable` |
| non-I, test 3-4 | `ysign` heavily |
| I, test 2+ | `itable` |

So the shipped pack may contain non-I kicks resolving at test 2 (pure horizontal) and
**no I kicks at all**. That is what let it hold 5 real wall kicks and 3 rejected
rotations — visibly not an empty sample — while staying inert on the crux.

Two cheaper readings are **actively refuted** by the shipped pack ("no wall kicks at
all", "hold never swaps"), so an agent stopping at either fails before submitting
rather than producing an *unfinished* run. That is the `celstage` §1 requirement:
the failure must be confident-and-wrong, not mid-search.

## 3. The three real defects found, in order

Each was found by a *different* mechanism. None by local oracle/nop.

### 3.1 A fairness defect the rubric only flagged as a note

`review` passed 30/31 but noted it could not execute the packs to check whether any
held-out attempt hinged on the single kick entry where PyPI `tetris` disagrees with
the published table (I `2->R` test 5). **I executed it: one did (`h1-03`).** An expert
who took the table from that library rather than the wiki would have failed on which
source they consulted, not on skill.

Fixed as an *enforced invariant*, not a one-off: every candidate is re-scored with the
library variant substituted and rejected if its result changes.

> **Lesson: when a reviewer says "I could not confirm X by execution", that is a task
> to run, not a note to file.** It was a real defect.

### 3.2 The sealed answers were readable at verify time

Found by pre-auditing against `qc_gate` findings while blocked on an outage. The
re-run executes in the same container `/tests` is mounted into, so a program that
globbed `/tests/**/*.expected.json` passed **all four held-out packs**. Closed by
chmod'ing `tests/packs` to root-only in an autouse fixture.

### 3.3 `qc_gate` E3 — and why the fix in 3.2 did not cover it

**The single most valuable finding here.** The verifier read the re-run's output file
*following symlinks*. The graded program symlinks its own output at the sealed answer
key; root follows it.

> **Permissions on the target are not a defence. Creating a symlink needs no access to
> its target, and the verifier reads as root, so root walks straight through your
> chmod. Refusing to follow is the only defence.**

Reproduced first as `exploit_outlink`: **against the then-current code it scored
1.000**, passing all seven tests while replaying nothing. Fixed with
`open_no_symlinks`, walking the path component by component with `O_NOFOLLOW` — which
also closes QC's related E5 note about a symlinked *parent* directory (`exploit_parentlink`
would have passed a leaf-only `islink` check).

## 4. Gate-by-gate log

| Cycle | Commit | Result |
|---|---|---|
| 1 | `f16a5b8` | static 25/25, rubric **30 PASS / 0 FAIL**, similarity unique, validation, **pass@2 0/2 with 2 valid fails** — all first time. `ava_review`/`deep_review` died on an upstream 503 |
| 2-4 | `d89a96d`, `a8df157`, `cd13405` | **platform outage**, no task verdict. The 503 moved along the pipeline as the service recovered: ava/deep, then `cosine_similarity` twice, then `validation` |
| 5 | `ae262a7` | first full traverse. Everything green through `qc_exec`; **`qc_gate` BLOCK on E3** |
| 6 | `251d160` | **every gate green.** `qc_gate` 37/37 clean, `trials` **pass@5 2/5, avg@5 0.400**, `gate` → `accepted` |

Notes:
- `pass2` is **skipped** when an earlier gate fails, so outage re-triggers cost **zero**
  rate-limited slots. I initially warned the opposite — check before rationing.
- `qc_gate` **early-exits**: cycle 5 ran 17 checks and deferred 21. A first-cycle QC
  pass tells you much less than a second-cycle one; cycle 6 ran all 37.
- pass@2 moved 0/2 → 1/2 across cycles with **no crux change** (the diff was verifier
  hardening). Treat pass@2 as noisy; do not tune the design on one sample.

## 5. Dead ends and judgment calls

- **Did not reuse the accepted-but-unsubmitted `pr4-embercross` task.** It was rejected
  once for subcategory mismatch; it is a card-game scoring formula, which reads as
  `board_and_card_games`, and this repo is seeded `puzzle_solving`. Reusing it repeats
  the rejection. It also violates the "needs outside knowledge, not derivation from
  given evidence" criterion, and is the `celstage` stamp-trilemma shape.
- **Held the design at the `near_miss` flag.** One pass@2 trial failed only 1 of 7
  tests. Tempting to tighten; `lumenp` says hold at 0/2-with-valid-failures and spend
  the cycle on gate fixes. Held, and it was accepted.
- **Did not push a README update after acceptance.** A push re-rolls all rubric
  criteria plus deep/ava/QC and re-runs pass@5. Accepted is accepted.

## 6. Reusable checklist

1. Deciding rule **real, external, published**; instruction names the system and
   enumerates nothing. Invented container fully specified.
2. Prefer a crux that is a **unit/axis conversion the published source does not do for
   you** (y-up table vs. y-down array). Invisible until a specific sub-case fires.
3. Build the inertness table **by measurement** — which cell of the input space kills
   which reading — then select shipped attempts from the inert cells only.
4. Ship attempts that **actively refute** the cheap readings, so failures are confident,
   not unfinished.
5. Write every exploit **before** trusting the fix, and measure it against the *current*
   code. `exploit_outlink` scored 1.000 before the fix; without building it I would have
   believed the chmod was sufficient.
6. Never let permissions be your only defence against a path the verifier reads as root
   — walk every component with `O_NOFOLLOW`.
7. A reviewer's "could not verify by execution" note is a task to execute.
8. `.dockerignore` in `task/environment/` from the first commit.
9. README and `task.toml` prose in the **same commit** as the change; diff test names and
   re-derive every count from the committed files.

## 7. One-paragraph version for future me

Take the accepted `lumenp` shape — invented container fully specified, deciding rules
moved outside to a real published standard the note names but does not restate — and
pick as the crux a **conversion the published source leaves to you**: SRS wall-kick
tables are published with y increasing upwards while any board array indexes downwards,
so the offsets must be negated, and nothing reveals the error until a kick displaces
vertically. Add the separate I-piece table and two Guideline hold rules, then select
the 28-attempt shipped pack by *measuring* which region of the input space leaves all
five wrong readings inert (non-I kicks resolving at test 2, no I kicks at all) while
still visibly containing real kicks, and make it refute the two cheap readings outright.
That reached **pass@5 2/5, avg@5 0.400, accepted**. The three defects that actually
mattered were all found off the happy path: a fairness hole the rubric could only flag
as an unverifiable note (one held-out attempt hinged on the one kick entry where a
public library disagrees with the wiki), sealed answers readable from the re-run, and
`qc_gate`'s E3 — where my own chmod fix was useless because creating a symlink needs no
access to its target and the verifier reads as root. Build the exploit before believing
the fix; that one scored 1.000 against code I had already pushed.
