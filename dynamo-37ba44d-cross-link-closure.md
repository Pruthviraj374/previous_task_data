# dynamo/cross-link-closure — gate failures, an infrastructure saga, and what finally worked

Repo: `dynamo-37ba44d-build-dependency-and-release-management`, PR #1, branch `submission`,
fork `charan-sr`.
Category: **Build Dependency and Release Management** / Sub-category: **Cross Compilation and
platform targeting**. Same subcategory as `dynamo-093d3d6-target-abi-audit`, worked in parallel —
read that case study too.
Benchmarked against Opus-4.8 via Terminus-2. Accepted 2026-08-07 at commit `da8b685`.

**Final result: pass@5 = 0/5 solved, avg@5 = 0.000, 5 good valid failures, 0 soft-timeout,
0 task/verifier issues, 0 reward hacking.** Best possible outcome. Every gate green on the
final pipeline cycle.

This task took the longest wall-clock time of any task in the playbook so far — not because the
design was hard to land (it cleared rubric 31/31 and pass@2 0/2 on the very first push), but
because of roughly 24 hours split between a genuine multi-hour CI infrastructure outage and a
separately-flaky internal similarity-check service, both entirely outside contributor control.
Section 5 is the part worth reading closely if a future task hits either symptom.

---

## 1. The task

A product is cross-built for three targets — `linux-gnu` (ELF), `macos` (Mach-O), `windows` (PE)
— and each build is staged into a *bundle*: a JSON description of everything that will exist on
the target at launch, plus the dynamic-linking metadata an extractor read out of each staged
image.

- **Agent sees:** three shipped bundles under `/app/data/bundles/` (`mesh-linux`, `mesh-macos`,
  `mesh-windows`) with their correct reports under `/app/data/expected/` as an end-to-end
  self-check.
- **Agent produces:** `/app/resolve.py`, invoked as `python3 /app/resolve.py <bundle_json>
  <out_csv>`, emitting the bundle's **link closure**: for every image the process loads, one row
  per dependency, naming the file the target's loader would actually bind it to, or `MISSING`.
- **Graded on:** twenty-two held-out bundles, never shipped, each isolating one platform-loader
  rule the flat samples cannot demonstrate.
- **Constraint:** Python standard library only; must not start another process.

---

## 2. The crux

> **The three loaders look interchangeable and are not.** The shipped samples are deliberately
> flat — every staged library sits beside or one level under the executable, only `DT_RPATH`/
> `LC_RPATH` are used, no environment directories are set, no library name occurs twice. In that
> shape all three loaders genuinely agree, so the obvious implementation (one global search list,
> origin placeholders expanded against the executable, each dependency resolved independently)
> reproduces all three shipped reports exactly.

Seven independently-observable, independently-wrong-able consequences:

| Mechanism | What the obvious implementation gets wrong |
|---|---|
| ELF RPATH inheritance | `DT_RPATH` is inherited by an object's dependencies; `DT_RUNPATH` is not |
| RUNPATH suppression | an object carrying `DT_RUNPATH` has its own `DT_RPATH` ignored outright |
| `$ORIGIN`/`@loader_path` ownership | follow the object that *declared* the entry holding them, not the executable |
| macOS `@rpath` chain-gathering | draws on `LC_RPATH` entries gathered along the *whole* load chain, not just the requester and the entry |
| `@executable_path` anchoring | anchored on the entry even when declared by a deeper image |
| Windows search order | anchored on the application directory, never the importing module's; case-blind; default directories before `PATH` |
| Process-wide identity binding | a name already mapped into the process binds again without a fresh search, on every platform |

### The three invariants that make it work

1. **The shipped samples never collide with any of the seven mechanisms.** Two independently
   written plausible-wrong resolvers were measured against the shipped bundles *before the first
   push*: both matched all three, byte for byte, and both produced full, well-formed, silently
   wrong reports on held-out.
2. **`instruction.md` states the premise, never the mechanism.** It says format/processor/OS/ABI
   must all agree and that the loader's own documented behavior governs — it never names
   `DT_RUNPATH`, `LC_RPATH` chain-gathering, or any specific search-order rule.
3. **Held-out bundles exist only in `tests/data/heldout/`**, read into the pytest process at
   verify time, then deleted from disk before the graded program runs even once.

---

## 3. Gate-by-gate log

Rubric (31/31 PASS), duplicate check (UNIQUE), validation, and pass@2 (0/2, genuine, on *every*
run across the whole task) all passed clean from the very first push and stayed that way. Every
real block came from the verifier-soundness gates — AVA and QC — never from difficulty or the
spec. In order:

### 3.1 — `ava_review`, five consecutive cycles on the same underlying theme

1. Resolved path re-canonicalised instead of echoed verbatim from `files` → echo the exact
   spelling; added `spool-verbatim-spelling` (a redundant `//`).
2. `/tests` reachability only assumed, never proven → `_harden_tests_directory()` chmods `/tests`
   0700 and empirically probes it as the grader account.
3. `@executable_path` as a *direct* dependency reference never exercised → added
   `brace-executable-path-direct`.
4. macOS identity-already-mapped never exercised → added `bay-already-mapped-macos`.
5. Identity binding under-pinned generally → added `wharf-already-mapped` (RPATH-shaped, vs
   `relay`'s RUNPATH-shaped).

**Then the real blocker, persisting five runs:** "verifier imports its oracle module." AVA kept
flagging that `tests/reference.py` existed as an importable module, even though nothing under
`/app` could reach it. Arguing the point did nothing across five cycles. **Fix: deleted
`tests/reference.py` entirely** and inlined the reference into `test_outputs.py` between
`# --- BEGIN REFERENCE ---` / `# --- END REFERENCE ---` markers, spliced in by a build script from
`solution/resolve.py` (the single source of truth) with an equality assertion. There is now no
importable oracle anywhere under `/tests` for anything to import. This cleared it on the next run.

**Generalisable, and the single most expensive lesson from this task's early phase:** when AVA
repeats the *same* finding across several cycles despite fixes that address its literal wording,
the fix that actually works is usually structural (remove the class of thing entirely), not
incremental (harden the existing shape of it).

### 3.2 — `qc_gate`: one finding, cheaply resolved

**"Underdetermined / Hidden-Knowledge Mapping"** — the macOS bundle schema advertised an
`install_name` field the reference never read, leaving its meaning underdetermined from the
agent's point of view.

**Fix: deleted the unread field** rather than implementing it. Implementing it would have added an
oracle branch no fixture exercises — exactly the "unexercised code path" defect QC hunts for.
Verified behaviour-neutral: expected reports were byte-identical before and after removal.

**Reusable rule (matches `dynamo-a4b5561`'s finding independently):** when a gate flags a decoy or
unused field, deleting it is usually cheaper and safer than implementing it — implementing adds
exactly the kind of unpinned branch the next QC cycle will find.

### 3.3 — `qc_gate` cycle 2 (this session): "Ambiguous Rule, No Disambiguation"

The instruction's line *"what the loader ends up binding, not merely where a file of that name
could be found"* had two readings that diverge on graded inputs. QC quoted our own intended
reading back at us and confirmed nothing agent-visible ruled out the other one (a plain per-image
fresh search, never reusing an earlier resolution).

**Fixed by adding one sentence stating the already-mapped premise directly**: *"Loading is a
single process-wide activity, not an independent lookup per image: once a reference has been
resolved anywhere in it, a later reference naming the same thing binds to that same image, not to
a fresh search."* Per the playbook's established pattern (§9 of `fir-boundary-metrics`, reconfirmed
on `dynamo-093d3d6` and `dynamo-a4b5561`), an architectural crux with several other independent
consequences tolerates disclosing one mechanism outright — six other rules still carried the rest
of the difficulty. **Confirmed empirically: pass@2 stayed 0/2 after the disclosure, and the final
pass@5 came back 0/5** — the disclosure cost nothing, matching the pattern's prediction exactly.

### 3.4 — `ava_review`, final cycle (this session): a real finding filed as "advisory"

After the infrastructure saga (§5) finally cleared, the very next real run blocked at
`ava_review` with `routing=block confirmed_major=0 supported_major=2 potential_major=5 gaps=7
parse_failures=1`. The rendered "Blocking Issues" section was just the generic union-gate
placeholder pointing at deep_review — and deep_review itself said **PASS, "Blocking Issues:
None."** Per the AVA-counter-table heuristic this playbook already carried (from
`dynamo-a4b5561` §6), `confirmed_major=0` does not mean nothing is wrong — `supported_major=2`
meant there was a real, concrete finding, just filed under "Advisory (non-blocking)" while the
overall verdict was still BLOCK.

The actual finding, `sound_verifier`: `build_report()`'s already-mapped bind
(`if key in mapped: rows.append((image, ref, mapped[key]))`) is written *unconditionally*, but
every one of the three existing already-mapped fixtures (`relay`, `wharf`, `bay-macos`) only
exercised the case where the second requester's own fresh search **also succeeds**, just to a
different, decoy file. None of them covered the case where a fresh search on the second
requester's own terms finds **nothing at all** — so a subtly wrong implementation that only trusts
the mapped value when an independent search would also have succeeded was never ruled out by any
fixture.

**Fix:** traced the exact resolver mechanics (`resolve_elf`'s per-owner RPATH/RUNPATH handling) to
construct a fourth fixture, `pier-already-mapped-unreachable`, where the entry resolves its direct
dependencies through its own `DT_RUNPATH` (not inherited to children), and a second requester with
no rpath/runpath of its own and no matching default path would get `None` from a from-scratch
search. Added a matching mutation (`gate the already-mapped bind on a fresh search also
succeeding`) to the local mutation sweep — it survived on every other fixture and was killed only
by the new one, which is the exact confirmation the fixture adds real, previously-uncovered
coverage rather than incidental padding. README and `task.toml`'s `verification_explanation` were
updated in the same commit (test count 29→30, held-out count 21→22, the already-mapped paragraph
extended from three fixtures to four). This run reached `qc_gate`, `ava_review`, and `trials`
cleanly and the PR was accepted the same cycle.

**Generalisable — this is the fourth independent confirmation of a pattern this playbook already
had (from `dynamo-a4b5561` §6):** *"An advisory-labelled finding under a BLOCK verdict is not
optional."* Read the counters (`supported_major`), not just which section a finding is rendered
under. And: a fixture that proves "a fresh search would find something different" is not the same
proof as "a fresh search would find nothing" — a design with an *unconditional* short-circuit rule
needs a fixture for both shapes of divergence, not just one.

---

## 4. The final pass@5 result, in the graders' own words

All five trials: `approach_validity` PASS, `reward_hacking` PASS, `task_specification` PASS,
`refusals` PASS, `low_timeout` PASS. Failures were **stratified by root cause, not uniform** — four
independent bugs, each hitting a different subset of trials:

- **`os.path.normpath()` destroys verbatim paths [5/5 trials].** Every agent normalised lookup
  candidates before matching, collapsing a non-canonical double-slash (`/srv/spool/lib//`) so it
  no longer matched the raw `files` entry. Universal — "a standard Python idiom, suggesting
  training-data convergence rather than first-principles reasoning" (graders' words).
- **Windows DLL lookup compared names case-sensitively [5/5 trials].** Every agent built a plain
  `set(files)` and checked membership with exact-case string equality; none folded names for
  Windows.
- **macOS `@rpath` search truncated to `[current_image, entry_executable]` [4/5 trials].** Skipped
  every intermediate image in the load chain — one trial's own trajectory explicitly recorded a
  deliberate regression: *"Updated the macOS resolver to only use executable's rpaths (not all
  ancestors)."*
- **ELF RPATH chain accumulation errors [2–3 trials, two different shapes]:** effective RPATH
  *replaced* rather than *accumulated* down the chain in two trials; one trial used a global
  append model that additionally broke RUNPATH non-inheritance and chain ordering.

Notably, **no trial failed on the already-mapped rule** — the mechanism this session spent the
most gate-cycles defending (§3.3, §3.4) turned out not to be what actually stumped the benchmarked
model in the final measurement. The crux held on other axes instead. This is a useful reminder:
gate cycles chase verifier *soundness*, not necessarily the same rule that ends up deciding
difficulty — both matter, but they are not the same axis, and a task can be fully defended on one
while succeeding for reasons that sit elsewhere in the design.

`near_miss` FAILed on 4/5 trials — every failing trial passed 27+ of 30 checks. Graders' own
framing: *"the near-miss pattern also explains how agents over-confirm: they pass all visible
samples and quit."* All five finished in 15–28 minutes of a 60-minute budget — nobody ran out of
time; they chose to stop after clean sample diffs, the exact overconfidence-early-quit pattern
this playbook has now seen on every task that used this design shape.

---

## 5. The infrastructure saga — read this before assuming a red gate means anything

This is the part of the task that actually consumed the wall-clock time, and it is worth recording
in detail because it is a *process* lesson, not a design lesson.

### 5.1 — What looked like a total outage was a severe, variable backlog

Per-push monitors that gave up after ~1 hour each concluded "no run triggered at all" — wrong.
Checking the full run history after the fact (`gh run list --limit 20`) showed every retrigger
commit eventually got a real run; actual queue delay was often 1–4+ hours, not the ~1 hour any
single monitor waited. **Lesson: a monitor that gives up after N minutes and concludes "nothing
happened" is measuring its own patience, not the pipeline's state.** Check the full run history,
not just what appeared inside one wait window, before concluding an outage is total.

Two genuinely distinct problems were tangled together in what looked like one outage:

1. **Runner/queue backlog** — the `cancelled`/0-steps signature (never acquiring a runner). Purely
   infra-side, cleared on its own after roughly 3.5–9 hours of accumulating delay, with no change
   on the contributor's side.
2. **A separately flaky internal service, `cosine_similarity`.** It calls an internal
   task-similarity check (referred to as "Joinera" in the workflow script) that returns
   `flag`/`clear`; a `flag` in enforced mode exits 1 with *"This task is too similar to a
   delivered Dynamo task and cannot advance."* **On completely unchanged content, this flipped
   `clear` → `flag` → `clear` across consecutive runs**, and flagged byte-identical content again
   on a second, freshly-opened PR with no shared history. A stable genuine duplicate does not pass
   three times first. This was never a real finding — the separate, older `similarity`/"Duplicate
   check" gate independently said "no duplicate found" on every single run.

### 5.2 — Testing "is it PR-specific" is worth doing once, not worth repeating

On a report that other contributors got unstuck by opening a fresh PR, branched a
content-identical `submission-2` off the current HEAD and opened PR #2 with zero changes. It hit
the identical failure signature within the same 15-minute window. **This ruled out anything keyed
to PR #1's specific history** (sticky QC/tier1 comment state, a wedged concurrency group scoped to
that PR) — the issue was repo/workflow-wide. PR #2 was closed immediately once that was
established; don't re-run this experiment unless there's fresh evidence the failure has become
PR-scoped again.

### 5.3 — A Slack "resolved" report is not confirmation; treat it as a hypothesis to test once

The task received a Slack report that `cosine_similarity` was fixed. **The first test of that
report was itself premature** — a retrigger pushed to confirm it hit the identical failure. The
right response to a secondhand "it's fixed" report is: push exactly one retrigger to test it,
read the real result, and do not push again on a second such report without the same discipline.
When the *second* report came in this session, it was treated the same way — one retrigger, then
read the actual gate result rather than trusting the report — and this time `cosine_similarity`
genuinely passed. **Two reports of the same claim do not deserve more trust than one; the test is
what earns the trust, not the report.**

### 5.4 — Escalating retrigger cadence, and stepping it back down

While the backlog was severe, retrigger cadence was deliberately dropped from the normal
15-minutes-between-checks pace to hourly, then to every 2 hours, specifically because pushing into
a pipeline that isn't queuing at all burns nothing but adds noise commits — there is no cost to
waiting longer between attempts when the earlier attempts prove nothing queued at all. **The
moment a run cleanly reached deep into the pipeline again** (this session: past `cosine_similarity`
and into real gate evaluation), cadence was restored to normal. Don't keep an emergency cadence
running past the point its justification (nothing is queuing) stops being true.

### 5.5 — Retrigger commits are functionally harmless; do not rewrite history to remove them

The task accumulated roughly 20 empty `git commit --allow-empty` retrigger commits across the
outage. Asked whether these could be squashed out of history: **declined**, for three durable
reasons, worth restating for the next task that asks the same question:

1. Removing them requires a rebase + force-push, which is itself a push — risks colliding with an
   in-flight run or a standing "do not push" instruction.
2. QC and Tier-1 key their sticky PR comments to specific base commit SHAs (`QC-BASE:`,
   `TIER1-BASE:` markers); rewriting history changes those SHAs and risks disrupting state that a
   close/reopen was *already* avoided for, earlier in the same task.
3. They are functionally harmless — nothing about grading, the diff, or reviewer evaluation reads
   the intermediate commit history.

**Leave retrigger commits in place.** A verbose, honest commit log documenting an outage is a
feature for a future reader trying to understand what happened, not a defect to clean up.

### 5.6 — Monitor tooling: verify your JSON tool is actually on `PATH` before trusting silence

A background poll loop using external `jq` (`gh run list ... | jq -r '...'`) silently produced
empty results for 45+ minutes on this machine — **`jq` is not installed on this environment's
`PATH`**, so every pipe through it failed silently (`2>/dev/null` swallowed the "command not
found" error, leaving an empty variable that looked like "still waiting" instead of "broken").
`gh`'s own built-in `--jq` flag (`gh run view ID --json status --jq '.status'`) works without any
external dependency and should be preferred over piping to a standalone `jq` binary on any new
machine until its presence is confirmed. **A monitor that "hasn't found anything yet" for several
polls in a row is worth a direct manual check** — don't assume the absence of a signal means the
absence of an event.

Separately: for a single "tell me when this finishes" wait, `Bash` with `run_in_background` and an
`until`-loop that exits on the terminal condition is the right tool — it gives exactly one
notification on completion. A persistent `Monitor` that echoes on every poll is the wrong shape
for this and produces one notification per tick regardless of whether anything changed, which is
noisy for a wait whose only interesting event is "done."

---

## 6. Process rules confirmed (nothing new, but worth re-confirming)

- **Never push while a run is in flight** — checked `gh pr checks 1` before every push.
- **Batch fixes into one push, always.** The final AVA fix bundled the new fixture, the matching
  mutation, README sync, and `task.toml` prose sync into a single commit.
- **Recalibrate locally before every push** — `harbor run -p . --agent oracle/nop`, full mutation
  sweep, every time.
- **`tests/reference.py` must not exist as an importable module at all** — this task confirms the
  stronger version of the "no separate oracle file" rule: even a *correctly-isolated* importable
  oracle module drew five straight AVA blocks. Define the reference inline in the verifier file
  from the start on the next task in this category, rather than as an importable module that has
  to be deleted later.
- **A deleted decoy field is cheaper than an implemented one.** Confirmed independently on two
  tasks now (`dynamo-a4b5561`, this one).
- **An architectural crux with several independent consequences tolerates outright disclosure of
  one mechanism.** Confirmed a fifth time (after `fir-boundary-metrics`, `dynamo-093d3d6`,
  `dynamo-a4b5561`, `rebuild-release-tarballs`): the already-mapped sentence was disclosed
  outright and pass@2/pass@5 were unaffected.

---

## 7. Final state

- **PR HEAD: `da8b685`** — the commit pass@5 was measured on, and the commit that got the
  `accepted` label. Do not push over it without reason.
- Fixture-generation tooling (`build_fixtures.py`, `calibrate.py`, `mutate.py`) lived only in
  `dynamo-37ba44d-tools/` outside the repo, never committed.
- Thirty pytest checks, twenty-two held-out bundles, four already-mapped fixtures
  (`relay`, `wharf`, `bay-already-mapped-macos`, `pier-already-mapped-unreachable`) covering three
  structurally distinct ways a fresh search can diverge from the correct already-mapped bind.

### One-paragraph version for future me

Build the crux as "N loaders that look interchangeable and are not," with the samples flat exactly
where the loaders would need to disagree, and measure two independently-written plausible-wrong
resolvers against the samples *before writing any task files* — both should match every sample
byte-for-byte and diverge sharply on held-out. When AVA repeats the same finding across several
cycles despite literal fixes, stop patching the symptom and remove the structural cause (here: an
importable oracle module, deleted entirely rather than hardened). When a gate files a concrete
finding under "Advisory" while the verdict is still BLOCK, read the counters
(`supported_major`/`confirmed_major`), not just which section rendered it — an advisory-labelled
real finding is still a real finding. For a design with an unconditional short-circuit rule (like
process-wide identity binding), a fixture proving "a fresh search would find something different"
is not equivalent to one proving "a fresh search would find nothing" — cover both shapes of
divergence, and confirm each fixture's necessity with a matching mutation that only it kills.
Expect an architectural crux with several independent consequences to tolerate outright disclosure
of any one mechanism — this is now confirmed on five separate tasks. And separately from all of
that: when CI infrastructure genuinely breaks for hours, the discipline that matters is patience,
not workarounds — check the full run history rather than trusting one monitor's limited wait
window, test a secondhand "it's fixed" report with exactly one retrigger before believing it,
step retrigger cadence down as soon as the pipeline is queuing again, and never rewrite the commit
history that documents what happened. The task that took the longest wall-clock time in this
playbook was not hard to design — it was blocked, twice, by systems entirely outside the design's
control, and the lesson that transfers is how to tell the difference between "the task is wrong"
and "the world is temporarily broken" without ever confusing the two.
