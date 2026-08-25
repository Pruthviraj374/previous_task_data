# dynamo/rebuild-zone-delineator — three library-shaped facts plus one rule with no citation at all

Repo: `dynamo-f038ddf-machine-learning-and-ai`, PR #1, branch `submission`, fork `Pruthviraj374`.
Category: **Machine Learning and AI** / Sub-category: **Unsupervised and representation
learning**. Benchmarked against Opus-4.8 via Terminus-2. Accepted by every automated gate on
2026-08-25 at commit `ec41bf9`.

**Final result: pass@5 = 2/5 solved, avg@5 = 0.400, 3 good valid failures, 0 soft-timeout,
0 task/verifier issues, 0 reward hacking.** All three failing trials share one root cause named
in the grader's own words: missing Rousseeuw's (1987) lone-plot silhouette-width convention
(`s(i) = 0` for a singleton zone, not the algebraic `1.0` the unguarded formula produces). The
zone-numbering axis (added specifically to break an earlier 5/5-too-easy result) held up cleanly
across all five trials — every agent independently reasoned its way to "ascending order of lowest
plot id" from the six shipped catalogues, confirming it behaves as a derivable-not-recallable
crux rather than a coin flip.

---

## 1. The task

A retired precision-agriculture appliance clustered soil-probe survey plots into management
zones and published a catalogue for each survey. The supplier folded; the raw exports and the
appliance's own operating notes survive; the catalogues have to be reproduced.

- **Agent sees:** `instruction.md` and `/app/ZONEKIT.md` (the operating notes), plus six shipped
  survey exports under `/app/surveys/` and their six published catalogues under
  `/app/catalogues/`.
- **Agent produces:** `/app/delineate.py`, invoked as
  `python3 /app/delineate.py <survey_tsv> <catalogue_json>` under `python3 -E -s -S -B`
  (stdlib only, unprivileged, ≤3 min for 40 plots).
- **Graded on:** exact categorical match — zone count and the zone number of every plot — on
  seventeen held-out surveys, none shipped with the image, each staged into a private directory
  with a fresh survey id, a sort-order-preserving plot-id relabelling, and a uniform reading
  shift, so the graded bytes are never the committed fixture bytes (see §3.3).

## 2. The crux, and the invariants that keep it alive

Four independent axes, each withheld from `/app/ZONEKIT.md` for a different reason:

- **A1 — the lone-plot silhouette convention.** Rousseeuw (1987) §2.1 defines a plot alone in its
  zone as having silhouette width 0 by convention. The naive formula (`a(i)=0` when there's
  nothing else in the zone, `s(i) = (b-a)/max(a,b) = 1.0`) gives the *opposite* extreme — the
  maximum possible score — for exactly the plots the convention is designed to avoid rewarding.
  This is the axis that actually stumped the model: 3/5 trials missed it.
- **A1b — the silhouette ratio denominator.** `max(a, b)`, not `b` alone. Only diverges when a
  plot's own zone already fits it worse than some other zone — rare given the shipped surveys'
  score-margin guarantee (`h15` is the only held-out witness).
- **A1c — survey-level aggregation.** Flat mean of every plot's own width (Rousseeuw's ASW), not
  a mean of per-zone means. `scipy`/`sklearn` calls get complete linkage and the two silhouette
  conventions above right "for free"; this one has no library escape hatch, because it's a
  question about how the surrounding code aggregates the library's own output, not a question
  the library answers itself.
- **A2 — zone numbering.** Not a term of any published algorithm at all: an arbitrary,
  appliance-specific labelling choice ("ascending order of each zone's lowest plot id, plot ids
  compared as byte strings"). No citation exists to withhold or disclose. Added *after* A1/A1b/A1c
  alone produced a 5/5 (too easy) `trials` result — see §4.4.

Invariants that must never break, enforced by `tools/invariants.py`:

- The distance rule (scaled Euclidean over incomplete channel vectors) is **stated outright** in
  `ZONEKIT.md`, not withheld — see §3.1 for why.
- All three silhouette misreadings (RA, RB/RC, plus the aggregation misreading) are each caught
  by at least two held-out surveys and by *none* of the six shipped ones; A1b's rarity is
  intentional and documented in the invariants script rather than silently relaxed.
- Four plausible zone-numbering alternatives (descending size, ascending size, order of first
  appearance, descending plot id) are each ruled out by at least one shipped catalogue and each
  separately caught by at least five held-out surveys.
- `tools/mutation_matrix.py` runs eighteen wrong delineators through the real verifier in the
  built image (must all score 0) and four sound-but-differently-shaped ones (must all score 1).
- `tools/probe.py` runs eight harness-attack probes (lookup table, symlinked output, reading the
  expected file, forging the reward, planting a `sitecustomize.py`, third-party import, and a
  content-hardcode exploit built from the actual committed fixture bytes) — all must score 0.

## 3. Dead ends — every approach tried that failed, with the grader's own wording

### 3.1 The distance rule as a withheld term

First cut: the scaled-Euclidean distance formula for incomplete channel vectors was a fourth
withheld term, alongside the silhouette terms. `qc_gate` flagged it twice on the same clause —
first as **Hidden-Knowledge Mapping**, then, after the first fix was only a reworded disclosure
sentence, as **Ambiguous Rule**. Root cause: plain pairwise-deletion Euclidean distance (drop the
missing channels, don't rescale) is a real, separately published, defensible convention *under
the same name* — "Euclidean distance for incomplete observation vectors." A rival reading isn't a
mistake here, it's a competing citation. That fails the sound-alternative test the three
silhouette terms pass (none of them has a competing convention under the same name). Fix: stop
rewording, disclose the formula outright in `ZONEKIT.md` step 1. Lesson, stated generally: **when
the same axis gets flagged a second time in a new form after a wording fix, the axis itself is
the problem, not the prose** — stop rewording and disclose.

### 3.2 Three silhouette terms alone

After dropping the `(Rousseeuw, 1987)` citation from `ZONEKIT.md` (keeping the formula unstated,
naming only that it was "mean silhouette width"), `pass@2` first came back 2/2 solved — the
citation alone hadn't done enough. Removing the citation and rerunning got a genuine `pass@2`
failure and advanced to `trials`, which came back **4/5** (too easy) once, and **5/5** (too easy)
again after adding A1c and rerunning. The trial analysis's own words: *"the combination of a
well-specified reference document, six shipped self-check examples, and Rousseeuw's widely-known
ASW definition made the difficulty crux tractable."* A correct general implementation of the
formula handles every combination of the three terms uniformly, as both the 4/5 and 5/5 runs
demonstrated by passing `combined_survey`, the fixture built to exercise several at once. No
fourth silhouette-formula fact would have helped — the well was exhausted, and every remaining
uncovered term was still "recall a fact from the same citation," which the model was visibly good
at once it started looking for such facts at all.

### 3.3 The verifier's own content became a lookup key — four revisions to close it

1. First revision staged the fixture `.tsv` **verbatim**, rewriting only `#survey_id`.
   `ava_review` built and demonstrated the exploit directly: a submission that special-cases the
   committed fixture content, readable by anyone with repository access including the task
   author, passes without computing anything.
2. Second revision: a deterministic hash of the fixture's own name, closing `ava_review` but
   reopening it in a more direct form (the injected id became predictable from the public
   fixture name too), and drawing a fresh `ava_review` finding.
3. Third revision: genuine per-run randomness (`secrets`, then
   `random.Random(time.time_ns() ^ os.getpid())`). This closed `ava_review` — confirmed via a new
   `content-hardcode` probe built from the real committed `h01.tsv`/`h01.expected.json`, scoring
   0 — but `qc_gate` raised **D4 (nondeterminism)** on it: "still seeded from wall-clock/pid, not
   a fixed constant," regardless of five clean oracle runs each scoring 1.0.
4. Fourth revision, the one that stuck: `_rng_for(name)` seeds a fresh `random.Random` from
   `sha256(fixed_constant + ":" + name)` — a pure, reproducible function of a hardcoded constant
   and the fixture's own name. This is what "fixed constant" can do that (2)'s content-preserving
   hash could not: (2) kept the *graded content itself* byte-identical to the repository, which
   is what `ava_review` was actually objecting to; this transforms the content, deterministically,
   into something that is provably never that (verified by calling the transform twice in-process
   and confirming byte-identical output — satisfying D4 — while confirming it never equals the
   committed bytes — satisfying `ava_review`). D4 and `ava_review`'s findings looked contradictory
   at first read (deterministic vs. never-equal-to-committed-content) but aren't: the seed must be
   fixed, the *output of running it through the seed* must not equal the committed bytes. Any
   transform of committed content by a fixed-constant-seeded RNG satisfies both.

   One correctness trap inside this fix: the first attempt at plot-id relabelling assigned fresh
   ids in **arbitrary** (random) order, which silently broke the zone-numbering rule (then still
   stated) by scrambling which id was "lowest." The oracle failed its own verifier
   (`P-1518 in zone 4, published catalogue has 2`). Fix: assign fresh ids in the *same relative
   sort order* as the originals — `sorted(fresh) ↔ sorted(original)` — which preserves any rule
   keyed on relative ordering. A uniform shift added to every reading is unconditionally safe
   (proof: it changes no pairwise difference, hence no distance, cluster, or silhouette outcome)
   and needed no such care.

### 3.4 Zone numbering: disclosed nothing at all

Once A2 was added by deleting the numbering step from `ZONEKIT.md` outright (not rewording it —
removing it, so nothing says zone numbering follows any rule), `qc_gate` raised
**Hidden-Knowledge Mapping / B5**: "The graded output includes the exact zone number of every
plot... The rule that assigns zone numbers to zones is not disclosed anywhere in the
age[nt-visible spec]." `tools/invariants.py` already had a machinery-level proof that the rule is
uniquely forced by the six shipped catalogues (four alternatives, each ruled out by at least one
shipped survey, each caught by held-out surveys) — but that proof lives in authoring-time tooling
the agent never sees. A soundness proof the agent cannot read does not answer a disclosure finding
about what the agent *can* read. See §4.5 for the fix.

## 4. What actually worked

### 4.1 Disclose the formula, keep the convention withheld — know which one has a competing name

The distance rule needed disclosure because a rival reading of it was independently citable under
the same name. The silhouette terms didn't, because Rousseeuw's convention has no competing
convention under the same name — "mean silhouette width" only ever means one thing once you go
look it up, the disagreement is entirely about whether the agent *does* look it up (recall) versus
guesses (mistake). Test before withholding anything: does a plausible wrong answer represent a
*different, real, separately citable convention*, or just an omission? The former must be
disclosed; the latter is fair game to withhold.

### 4.2 A structurally different fourth axis, not a fourth fact under the same citation

Once three fair-to-withhold facts under one citation were exhausted (§3.2), the fix wasn't a
fourth fact — it was an axis with *no citation at all* to look up: an appliance-specific,
unpublished labelling convention, observable only by comparing an attempt's own output against
the six shipped catalogues. This is the `previous-task-data.md` "memorised vs. noticed" test
applied at the axis level, not just the fact level: a real published convention the model already
knows cold (more Rousseeuw facts) is not further difficulty once the model has learned to check
for it; only a structural property with **no citation to recall in the first place** reliably
discriminates further.

### 4.3 Prove uniqueness with tooling, then separately name that the proof exists, agent-side

The fix for §3.4's B5 finding was one sentence appended to `ZONEKIT.md`'s closing section:

> One thing here is not a quantity of any published method and is not spelled out: how a
> catalogue's zone numbers are handed out among its zones. That was a fixed, consistent choice
> the appliance made on every survey it ever ran, not a per-survey coin flip, and these notes do
> not restate it. The six shipped catalogues in /app/catalogues/ are the only record of it that
> exists.

This names that a rule exists, that it's fixed (not arbitrary per-survey), and where the only
evidence for it lives — without stating the rule itself. It closed `qc_gate` on the first retry
and `trials` subsequently confirmed the axis is still genuinely hard-in-the-right-way: every one
of five trials independently reasoned its way to the correct rule from the six shipped catalogues
(the trial analysis explicitly notes "this strong convergence... suggests the algorithm structure
is reliably derivable from ZONEKIT.md alone"), so disclosing *existence* without disclosing
*content* did not collapse the axis back into a freebie. The alternative — stating the rule
outright — was rejected up front as the move that would have made this the second recall-only
axis in the same task, reopening exactly the too-easy risk A2 was built to fix in the first place.

### 4.4 Adding A1c after 4/5 and 5/5 too-easy results

The per-trajectory analysis at 4/5 showed every trial got the distance rule and A1b exactly
right, and only one trial missed A1 — `scipy`/`sklearn` correctly implement complete linkage and
both silhouette numerator/denominator conventions as library calls, so a dev-time cross-check
against either library gets those two right without ever recalling Rousseeuw's footnotes from
memory. A1c (flat-ASW vs. cluster-then-average) has no such escape hatch: no library call
performs survey-level aggregation, since that's a question about the code *around* the library
call, not a step the library implements. This is the same category of insight as §4.1 applied one
level up: before adding a withheld fact, check whether a standard library call would give it away
for free regardless of whether the agent recalls the citation.

### 4.5 The rubric wording gate

`review`'s `difficulty_explanation_quality` criterion failed once on `task.toml` prose that cited
raw agent-trial pass rates (e.g. "4/5 trials got this wrong") as the justification for an axis.
The rubric forbids grounding difficulty claims in observed pass rates — rewritten to justify each
axis via the intrinsic structure of the problem (competing conventions, library escape hatches,
citation absence) instead. `README.md`'s similar pass-rate citations were a different,
already-passing criterion and were left alone.

## 5. Gate-by-gate log, in the order things actually broke

| Gate | First result | Fix | Commit |
|---|---|---|---|
| `qc_gate` (Hidden-Knowledge Mapping, distance rule) | FAIL | Reworded disclosure sentence (partial) | early |
| `qc_gate` (Ambiguous Rule, same clause) | FAIL | Disclosed the distance formula outright in `ZONEKIT.md` step 1 | mid-session |
| `trials` (pass@5, 3-term silhouette design) | 4/5 (too easy) | — diagnosis: A1/A1b library-escape-hatch, only A1 missed | — |
| `trials` (pass@5, after A1c added) | 5/5 (too easy) | — diagnosis: well of silhouette-formula facts exhausted | — |
| — (redesign) | — | Added A2 (zone numbering), a structurally different withheld axis | `c459583` |
| `ava_review` (hardcoded-lookup exploit, demonstrated) | FAIL | Shift + relabel content transform (§3.3, revision 3) | mid-session |
| `qc_gate` (D4, nondeterminism, on revision 3's transform) | FAIL | `_rng_for(name)`: sha256(fixed_constant + name)-seeded RNG (§3.3, revision 4) | mid-session |
| `tier1` (fix-addressal check on the D4 finding) | (verified fix, passed) | — | mid-session |
| `review` (rubric, `difficulty_explanation_quality`) | FAIL | Removed pass-rate citations from `task.toml`, justified axes structurally | `ba4f891` |
| `qc_gate` (Hidden-Knowledge Mapping, zone numbering / A2) | FAIL | One-sentence existence-disclosure appended to `ZONEKIT.md` (§4.3) | `ec41bf9` |
| `trials` (pass@5, final 4-axis design) | **2/5 (accepted)** | — | `ec41bf9` |
| `changes`, `cosine_similarity`, `similarity`, `validation`, `pass2`, `deep_review`, `ava_review` (final pass), `tier1` (final pass), `qc_exec`, `qc_eval`, `qc_gate` (final pass), `gate` | pass (final round) | — | `ec41bf9` |

Gates that never failed across the whole session: `changes`, `cosine_similarity`, `similarity`
(no duplicate found against TB2/TB3), `validation` (oracle=1.0/nop=0.0 held throughout), the
base-image digest pin check, and the `.dockerignore` content check (trivial, three glob lines,
never touched).

## 6. Error → what to do, and what NOT to do

- **`qc_gate` flags the same withheld clause twice, in different guises (Hidden-Knowledge Mapping,
  then Ambiguous Rule).** Do: check whether a *different, real, separately citable* convention
  produces the same wrong answer under the same name — if so, disclose the fact outright and move
  the difficulty elsewhere. Don't: reword the withholding prose a third time. If the axis keeps
  getting flagged in a new shape, the axis is the defect, not the sentence.
- **`trials` comes back 4/5 or 5/5 (too easy) on a single citation's worth of withheld facts.**
  Do: check whether a standard library call (here, `scipy`/`sklearn`) gives away the withheld
  fact for free regardless of recall, and if the well of same-citation facts is exhausted, add a
  *structurally different* axis (different citation, or better, no citation at all) rather than a
  fourth fact under the same one. Don't: shorten the timeout, add unrelated busywork, or increase
  the number of held-out surveys hoping quantity substitutes for a genuinely different mechanism
  — none of that changes what's derivable, only how much of it there is to check.
- **`qc_gate` raises Hidden-Knowledge Mapping on an axis with *no* published convention to gesture
  at (an arbitrary, appliance-specific rule).** Do: add one sentence naming that the rule exists,
  that it is fixed/consistent (not per-instance arbitrary), and pointing at the specific
  agent-visible evidence for it (the shipped samples) — without stating the rule. Don't: state the
  rule outright to make the finding go away trivially; that is very likely to convert a
  derivable-and-hard axis into a recall-and-easy one and reopen the too-easy risk this axis exists
  to prevent. A machinery-level uniqueness proof (in `tools/invariants.py`) is necessary but not
  sufficient by itself — it has to be paired with something the agent's own vantage point can see,
  because `qc_gate`'s check is about the agent's vantage point, not the author's.
- **`ava_review` demonstrates a hardcoded-lookup exploit against verifier fixture staging.** Do:
  make the graded content a provably answer-preserving transform of the fixture (uniform shift on
  numeric fields; a relative-order-preserving relabelling on any field an answer is keyed on) that
  is never byte-identical to the committed file. Don't: rewrite only the id/name field and leave
  the payload verbatim — that closes nothing, since the payload is still the lookup key.
- **`qc_gate` raises D4 (nondeterminism) on a content transform meant to fix `ava_review`.** Do:
  seed the RNG from a hash of a hardcoded constant plus the fixture's own name — reproducible
  across runs, never equal to committed bytes. Don't: seed from wall-clock time or PID, even if
  every oracle run scores 1.0 — "clean runs" doesn't satisfy a literal fixed-constant requirement,
  and don't mistake "D4 wants determinism" and "ava_review wants non-identity-with-committed-
  content" for a contradiction; they constrain different things (the seed vs. the seed's output).
- **A relabelling transform breaks a rule keyed on relative ordering.** Do: preserve relative sort
  position when assigning fresh values to a set that anything downstream compares in sorted order
  (`sorted(fresh) ↔ sorted(original)`). Don't: assign fresh values in arbitrary/random order and
  assume any ordering-dependent rule downstream survives it — it silently won't, and the failure
  shows up as the *oracle* failing its own verifier, which is confusing to debug from the reward
  number alone (check per-plot diffs, not just the aggregate reward).
- **`review` fails a rubric criterion on difficulty-explanation wording.** Do: justify each
  withheld axis by its intrinsic structure (competing conventions, library escape hatches, absence
  of a citable definition). Don't: cite raw pass/fail counts from prior agent trials as the
  justification — the rubric explicitly forbids grounding a *difficulty claim* in an *observed
  result*, even a true one.

## 7. Bugs I introduced myself

- Misattributed early commits to the wrong git identity by pulling from the session's ambient
  user-email context field instead of the repo's actual owner. Fixed via `git filter-branch`
  scoped to the commit range after the scaffold commits (so the bot-generated scaffold hashes
  stayed untouched), then `git push --force-with-lease`. The lesson generalizes past this task:
  **never use a session's ambient "who is the user" context field to set repo git identity** —
  that field identifies the person in conversation, not the account whose name belongs on a
  commit in a given tree. Check the repo's own CLAUDE.md / git config for the mandated identity
  before the first commit, every time, regardless of which account is driving the session.
- Repeatedly ran tooling commands (`tools/invariants.py`, `docker build`, `harbor run`) from the
  wrong working directory (`task/`, `task/tools/`, repo root) across the session, producing
  spurious "No such file or directory" errors. No lasting effect, just wasted tool calls each
  time — `pwd` before any relative-path command sequence would have caught it immediately.

## 8. Process rules learned the hard way

- **`gh pr view --json comments --jq` for reading sticky pipeline comments; `gh run view --job
  <id> --log` for raw job logs when no sticky comment exists for a job yet.** QC findings arrive
  as both a human-readable truncated bullet list *and* a full base64-encoded JSON blob
  (`<!-- QC-FIXES-B64:... -->`) in the same comment — decode it
  (`grep -oE 'QC-FIXES-B64:[A-Za-z0-9+/=]+' | sed 's/QC-FIXES-B64://' | base64 -d | python3 -m
  json.tool`) when the rendered bullet looks truncated. Caveat: the underlying `evidence` *string*
  itself can be truncated by QC's own system before encoding, not just by comment rendering — the
  base64 blob is not guaranteed to contain the full original text either.
- **Verify "it failed" against live `gh pr checks` state before reacting.** Several times a
  reported failure turned out to be a stale comment being re-read rather than a new failure on
  the current push. Always re-pull the live check state and the latest sticky comment timestamp
  before diagnosing.
- **Re-run the full local chain after any `ZONEKIT.md` or shipped-data change, not just the piece
  that changed:** `docker build`, `tools/invariants.py`, `tools/mutation_matrix.py`,
  `tools/probe.py`, then `harbor run --agent oracle` (expect 1.0) and `harbor run --agent nop`
  (expect <1.0). A memo-only change still needs the image rebuilt (`COPY data/ZONEKIT.md` bakes it
  in) and every downstream check re-run against the *rebuilt* image — nothing here is safe to skip
  because "it's just a sentence."
- **README.md pre-push gate is worth actually doing, not skimming.** On the final push, the
  ZONEKIT.md diff alone would have made `README.md`'s "A fourth axis" section actively wrong (it
  asserted "nothing says zone numbering follows any rule," which the new sentence in ZONEKIT.md
  directly contradicts) — caught only by re-reading the specific README section the change
  touches against the literal new wording, not by a general "does this look related" skim.
- **`pass2` (2-trial pre-check) needs at least one valid failure to unlock `trials` (pass@5).** A
  round where `pass2` comes back N/2 solved with N<2 is a genuine difficulty signal and advances
  the pipeline; 2/2 solved does not, and the pipeline stops there without reaching `trials` at
  all. Don't mistake "pass2 passed" (the check *ran* successfully) for "the design is too easy" —
  read the actual solved-count in the sticky comment, not just the checkmark.

## 9. A reusable checklist for the next task

1. Before withholding any fact, ask: does a plausible wrong answer represent a *different, real,
   citable convention under the same name*, or a *mistake*? Only the latter is fair to withhold.
2. Before adding a second/third/fourth fact under one citation, check whether a standard library
   call in the target language gives away any of them for free. If so, that fact doesn't add
   difficulty regardless of whether it's stated.
3. If `trials` comes back too easy after exhausting one citation's facts, the fix is a
   *structurally different* axis — ideally one with no citation to recall at all, observable only
   by comparing an attempt's own output against shipped self-check examples.
4. For a no-citation axis, `qc_gate`'s disclosure check needs to see, from the agent's own vantage
   point, that a rule *exists* and is *fixed* — even when the rule itself must stay unstated. A
   uniqueness proof that only lives in authoring-time tooling does not satisfy this by itself.
5. Any verifier-side transform of graded content must be simultaneously: (a) reproducible from a
   hardcoded constant (satisfies determinism checks), (b) never byte-identical to the committed
   fixture (satisfies exploit-of-committed-content checks), and (c) provably answer-preserving for
   every field it touches (uniform shifts; order-preserving relabellings for anything compared by
   relative position).
6. Re-run the *entire* local verification chain — not just the piece that changed — after any
   change to agent-visible content, and re-verify README.md against the literal new wording before
   every push, not against a general sense that "this doesn't look README-relevant."

## 10. One-paragraph version for future me

Three silhouette-formula facts under one citation (Rousseeuw's ASW) got the model to 5/5 solved
because two of the three are library-escape-hatched and the model, once primed to look for
citation footnotes, found the third too — the fix wasn't a fourth fact under the same citation but
a structurally different fourth axis with *no citation at all*: an arbitrary, appliance-specific
zone-numbering rule, observable only by diffing an attempt's own output against six shipped
samples. That axis drew its own `qc_gate` disclosure finding once withheld completely silently,
and the fix wasn't to state the rule (which would have collapsed the axis back to recall) but to
add one sentence saying a fixed rule exists and naming where its only evidence lives, leaving the
rule itself unstated — closed the gate and left the axis hard enough that pass@5 landed at 2/5,
entirely on the one term (the lone-plot silhouette convention) that has a real citation to forget.
