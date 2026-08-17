# dynamo/request-preconditions — HTTP conditional-request and range evaluation

| | |
|---|---|
| **Outcome** | **Accepted** — every gate green, `accepted` label |
| **Headline** | **pass@5 = 0/5, avg@5 = 0.000**, 5 of 5 good valid failures, 0 timeouts, 0 verifier issues |
| Repo | `handshake-project-dynamo/dynamo-300f2a9-software-engineering` |
| PR | https://github.com/handshake-project-dynamo/dynamo-300f2a9-software-engineering/pull/2 |
| Category / sub-category | Software Engineering / Feature Implementation (pre-seeded) |
| Benchmarked model | Opus-4.8 via Terminus-2 |
| Final commit | `7cb3726` (second and last push) |
| Pushes to acceptance | **2** — first push cleared everything except `qc_gate`; second cleared `qc_gate` and ran pass@5 |

Two pushes, one gate failure, no redesign. The design was taken almost entirely from this
directory rather than rediscovered, which is why. Read §"What actually worked" for the parts
that were decided on paper before any code was written.

---

## 1. What the task asks

`/app` holds `edgecache`, a small HTTP/1.1 origin server for static assets. Storage, routing
and response assembly ship working; one module is a stub. The agent implements

```python
edgecache.preconditions.evaluate(request, resource)
    -> {"outcome": str, "first": int|None, "last": int|None}
```

deciding, per request against one resource, between `OK` (whole representation), `PARTIAL`
(with inclusive byte offsets), `NOT_MODIFIED`, `PRECONDITION_FAILED` and
`RANGE_NOT_SATISFIABLE`.

What the agent can see:

- `/app/docs/CONTRACT.md` — both argument shapes, every guarantee the front end makes about
  their contents, the exact return dict, and **one flat sentence** naming RFC 9110 as the
  standard the server speaks. It enumerates none of the RFC's rules.
- `/app/samples/cases.json` + `expected.json` — 33 recorded request/resource pairs *with their
  answers*, and `/app/check_samples.py` to replay them.
- `/app/edgecache/{dispatch,http_date}.py` — the shipped halves that call `evaluate()` and parse
  IMF-fixdates, so neither response assembly nor date parsing is part of the problem.

Graded on: the 33 shipped pairs plus **28 held-out pairs** from the same server that are not in
the image. Every graded value is categorical.

---

## 2. The crux, and the invariants that keep it alive

Four rules, all **MUST**-level in RFC 9110, all conditional, all silent when wrong:

| # | Rule | The plain reading |
|---|---|---|
| A | comparison function differs by field — `If-None-Match` weak, `If-Match` and `If-Range` strong (§8.8.3.2, §13.1.1/2/5) | one comparison written for all three fields |
| B | `If-Modified-Since` ignored when `If-None-Match` present; `If-Unmodified-Since` ignored when `If-Match` present (§13.1.3/4, §13.2.2) | sequential `if` instead of `if/elif` |
| C | an `If-Range` validator is compared for **exact equality, dates included** (§13.1.5) | `<=`, by analogy to every other date header |
| D | a satisfied `If-None-Match` → 304 for GET/HEAD, **412** otherwise; `If-Modified-Since` does not apply outside GET/HEAD (§13.1.2/3) | outcome chosen without reference to method |

**The invariants. Break any of these and the task stops working:**

1. **Every rule is inert on all 33 shipped pairs.** Not "absent" — *equivalent*. Two pairs sit
   deliberately on the boundary and are the load-bearing ones:
   - `inm-matching-weak-pair`: `If-None-Match: W/"b8e402"` against stored `W/"b8e402"`. Weak
     comparison and naive string equality both match. This case also **refutes** "use strong
     comparison everywhere", so an agent that tries that reading gets a red light *before*
     grading rather than becoming an invalid failure.
   - `ifrange-date-equal`: an `If-Range` date exactly equal to `Last-Modified`. `==` and `<=`
     agree here. The held-out "later" sub-case is the only discriminator, and pass@5 confirmed
     it: 4 of 5 trials died on exactly it.
2. **The four rules are never named** anywhere the agent can read — instruction, CONTRACT.md,
   code comments, variable names, sample case names. Verified by grep over every agent-visible
   file: the only hit for `weak|strong|precede|exact match|ignore|rfc 9110` in the whole image is
   the single sentence "It speaks HTTP/1.1 as specified in RFC 9110."
3. **Every graded case satisfies every guarantee CONTRACT.md makes.** Enforced by an audit in the
   case builder (added after `qc_gate` caught the one violation — see §5).
4. **Held-out expectations are hand-planted from the RFC first**, then the reference is *required*
   to agree with all 28 independently. There is no `_reference.py` computing expectations at
   verify time, so `oracle = 1.000` is a real cross-check rather than the tautology
   `experiment-analysis-frame` §7 warns about.
5. **Categorical grading throughout.** An outcome name plus two integer offsets. No tolerance,
   no near-miss band, and `difficulty_evidence` can never call a failure a formatting artifact
   (`filer-access-audit` §1, generalised).

---

## 3. Dead ends — designs rejected on paper, with the reason

None of these cost a pipeline cycle. All were killed during design using this directory and one
RFC read. That is the whole point of the section: **rejecting on paper is free, rejecting at
pass@2 costs an hour.**

**a) HTTP caching (RFC 9111) — killed by MAY-level rules.**
The first design was a cache-decision function with cruxes on the qualified `no-cache="Set-Cookie"`
and `private="Authorization"` forms. Fetching the RFC killed it: both qualified forms say a cache
**MAY** reuse the response with the listed fields removed. Grading one of two legal behaviours is
ambiguity, not difficulty — exactly what `filer-access-audit` §3 says to drop ("Your candidate
rule is a **SHOULD** with escape clauses"). RFC 9111 turns out to be full of MAYs; RFC 9110 §13 is
almost entirely MUST. **If a candidate crux lives in a caching/heuristics section, check the
normative verb before designing around it.**

**b) A quoted `max-age="600"` being invalid — killed by reading the grammar.**
Was going to be a lovely syntactic crux. RFC 9111 §5.2 explicitly says recipients **MUST** accept
both the token and the quoted-string form. The rule I was about to grade was simply wrong. Cost:
ten minutes, because I checked before writing it. Would have cost a full cycle and an
"uncorrectable lie" fairness failure otherwise.

**c) Terminal emulator (DEC deferred wrap / DECSTBM) — killed by the local-oracle test.**
Genuinely excellent crux material: the last-column pending-wrap flag is real, published,
conditional, and normalised away by every naive `if col >= width: col = 0; row += 1`. Killed by
`filer-access-audit` §4.1 — **ask whether the environment can answer it for the agent.** Terminal
emulation has many local oracles one `apt-get` away (`tmux`, `screen`) plus `pyte` on PyPI. An
agent can drive tmux and diff. Rejected.

**d) JSON Patch / JSON Pointer (RFC 6902/6901) — same test.**
The `~01` decode-ordering trap is a beautiful latent crux. `pip install jsonpatch` is an exact
oracle. Rejected. Same for semver ranges (`semver`, npm), unified diff (`git apply`, `patch`),
and URI resolution (`urllib.parse.urljoin` — in the *stdlib*).

**e) Adding a fifth axis after pass@2 — deliberately not done.**
pass@2 returned 0/2 with two distinct valid causes on the first push. `rebuild-readout-builder`
§3.1 warns 0/2 on a single axis is a coin flip, but this task had four axes with two already
demonstrated live. `lumenp` §3 warns that piling on mechanisms is the classic wrong response.
Held the design and spent the cycle on the QC fixes instead. pass@5 came back 0/5.

**f) The local-oracle test applied to the winning design.** `nginx`/`apache` implement RFC 9110
§13 exactly and are one `apt-get` away — but neither can be made to emit an arbitrary weak ETag
against an arbitrary `Last-Modified`, so they cannot answer the graded question. This is the line
`filer-access-audit` §4.1 draws: *"not findable online" is not the same as "no local oracle"* —
and equally, "a tool exists that does something similar" is not the same as "the tool answers
this". `reassemble-tap-sessions` was accepted with `tshark` one apt-get away.

---

## 4. What actually worked

**The winning shape, stated once:** a real published standard the instruction names *once and
only as a locator*, whose deciding rules are MUST-level, conditional on input shapes the sample
suite renders equivalent rather than absent, in a domain where no installable tool answers the
graded question.

Specific decisions that carried it, each traceable to a prior file:

- **Named the standard, enumerated nothing.** One flat descriptive sentence, no "where this
  document is silent", no naming the areas, no gap-hunting cues. This is `replay-strata-plans`
  §3.2 word for word — that task went 0/2 → 2/2 purely on the *register* of the same sentence.
  `qc_gate` B5 never fired here.
- **Equivalence, not omission** (`rebuild-plate-rasterizer` §4.2). Omission leaves the agent
  uncertain and invites a B5 block; a boundary case where both readings agree makes it
  *confident*. pass@5's own words: "The 33-case sample suite was intentionally designed so both
  bugs produce identical outcomes to the golden solution on all shipped examples, leaving held-out
  cases as the only discriminator."
- **Shipped a complete-looking self-check that is silent on the trap** (`contact-export` §9,
  `merge-lora` §2). All five pass@5 agents ran `check_samples.py`, saw 33/33, and quit "typically
  in 8–16 minutes of a 50-minute budget."
- **Four axes, not one** (`rebuild-readout-builder` §3.1). Two fired in pass@5 (C in 4 trials, B
  in 2, one trial hit both). A and D never gated — and per `filer-access-audit` §4.2 /
  `reduce-palaeomag` §4.2 / `replay-strata-plans` §4.3, that is *not* a reason to cut them; three
  prior tasks record the axis rated weakest being the one that gated.
- **Calibration written before the first push, not in answer to a block** (`reduce-palaeomag`
  §4.4). Six wrong implementations, each asserted sample-inert *and* caught by held-out cases;
  one rival reading asserted refuted by the shipped suite. `qc_gate` still found two things — but
  neither was a B5/coverage finding, which is what that discipline buys.
- **Ground truth planted, not derived** (`reassemble-tap-sessions` §4). Hand-wrote all 28 held-out
  answers from the RFC, then required the reference to agree. `deep_review` independently
  re-derived every one and reported "No off-by-ones, wrong units, or copy-paste echoes."

---

## 5. Gate-by-gate log

### Push 1 — `382334a`

| Gate | Verdict | Note |
|---|---|---|
| `changes` (static) | **pass** first time | all 25 checks, incl. `.dockerignore` and the literal `COPY solution/ or tests/` scan |
| `review` (rubric) | **pass** first time | 30 PASS, 1 N/A, 0 FAIL |
| `similarity` / `cosine_similarity` | **pass** | UNIQUE; highest lexical match `llm-inference-batching-scheduler` at 0.117 |
| `validation` | **pass** | docker / oracle / nop |
| `pass2` | **pass** | 0/2, 2/2 valid failures |
| `deep_review` | **pass** | 3 advisories, no blocking issues |
| `ava_review` | **pass** | 1 advisory (`sound_verifier`) |
| `tier1` | **pass** | |
| **`qc_gate`** | **FAIL** | 2 blocking findings; early-exit deferred 21 further checks; `trials` skipped |

**qc_gate finding 1 — "Undocumented Requirement Enforced" (B4).** Held-out case
`ho-head-range-ignored` sent `Range` on a `HEAD` request. `CONTRACT.md` guarantees `range` is
only ever sent with `GET`. Verdict text: *"The verifier enforces an outcome for an input its own
agent-visible contract guarantees can never occur, and the required outcome is undocumented (and
contradicts the contract)."* `deep_review` flagged the same case as advisory note 2 and called it
"harmless" — QC blocked on it. **Believe the blocker, not the advisory.**

Fix: dropped the case (no wrong implementation was caught by it — calibration proved that in
advance), and added an `audit()` pass in the case builder that asserts every graded case against
every guarantee CONTRACT.md makes: method in the stated set, header names lowercased and in the
stated set, `range` only on GET, `if-range` only with `range`, dates parse, entity-tags properly
quoted, single range spec in one of the three forms, resource fields well formed.

**qc_gate finding 2 — "Reward / Harness Plumbing Exploit" (E3).** The Dockerfile baked
`ENV PYTHONPATH=/app`; `test.sh` never cleared it and invoked the **console script** `pytest`.
So an agent-written `/app/sitecustomize.py` or `/app/pytest.py` would be imported by the
verifier's interpreter **as root**. Fix: dropped `ENV PYTHONPATH`; `test.sh` now unsets
`PYTHONPATH PYTHONHOME PYTHONSTARTUP PYTHONUSERBASE`, exports `PYTHONNOUSERSITE=1`, and runs
`python3 -E -s -B -m pytest` from the sealed grading directory (so `-m`'s cwd insertion lands on
a root-only path).

**`ava_review` advisory (`sound_verifier`), non-blocking but real.** *"The sample suite is baked
into the image under /app, i.e. the same tree the agent edits… test_sample_suite_reproduced
passes because it compares against the edited expected.json."* Fixed in the same push by the
change below.

**QC "Symlinked Output Path" (E5), flagged for human review.** The verifier read
`/app/samples/*.json` and `os.path.isfile('/app/edgecache/preconditions.py')` with no symlink
guard. Rather than add guards, **deleted the class**: all 61 graded cases *and* their expectations
now come from one sealed `tests/cases.json`, and the verifier reads nothing under `/app` at all.
This also closes the AVA advisory above. The recursive `chown -R`/`chmod -R` on `/app/samples`
was removed too (a symlink left in its place would have redirected a recursive operation as root);
replaced with a guarded, non-recursive `chmod 700` skipped entirely if the path is a symlink.

### Push 2 — `7cb3726`

Every gate above **pass**, plus:

| Gate | Verdict |
|---|---|
| `qc_eval` / `qc_exec` / **`qc_gate`** | **pass** — "37 checks + probes ran clean", `QC-FIXES-B64:W10=` (empty) |
| `pass2` | pass — 0/2 again, both valid |
| **`trials` (pass@5)** | **pass — 0/5, avg@5 = 0.000, 5/5 good valid failures** |
| `gate` | **pass** |
| label | **`accepted`** |

**pass@5 breakdown** (all `approach_validity` PASS, all `reward_hacking` PASS, `difficulty_crux`
PASS on all five — nobody lacked the knowledge):

- **Bug C — If-Range date, 4 of 5 trials.** Agents wrote `last_modified <= if_range_date`
  (If-Unmodified-Since semantics) instead of `==`. Failing: `test_if_range_condition` (2 cases)
  and `test_combined_conditions` (1 case) per trial.
- **Bug B — cascade ordering, 2 of 5 trials.** Sequential `if` instead of `if/elif`. Failing:
  `test_precondition_precedence`, 1 case in one trial and 3 in the other.
- One trial (`zWHRjGh`) hit **both**; `xkaZebP` hit only B and passed the If-Range group.
- The most useful single line in the whole run — trial `Q4cLVX7` reasoned explicitly at step 8
  that *"a server MUST evaluate an If-Range precondition containing an HTTP-date using the same
  rules as If-Unmodified-Since"*. That is **a direct misrecollection of RFC 9110 stated with
  MUST-level confidence**, not an implementation slip. See §10.
- All five ran `check_samples.py`, confirmed 33/33, and stopped — "typically in 8–16 minutes of a
  50-minute budget." `bytecode-vm-debug` from `34-*.md`, reproduced exactly.

---

## 6. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| `qc_gate` **"Undocumented Requirement Enforced" (B4)** on a case your own agent-visible contract excludes | Drop the case if calibration shows nothing is caught by it, and add a build-time audit asserting **every** graded case against **every** guarantee the contract makes | Do **not** "document the requirement" by widening the contract — that adds an unvalidated rule and needs fresh accept-side coverage. Do **not** trust a `deep_review` advisory calling the same case "harmless"; QC blocks on it |
| `qc_gate` **"Reward / Harness Plumbing Exploit" (E3)** naming `PYTHONPATH` and the `pytest` console script | Remove the `ENV`, unset every `PYTHON*` var in `test.sh`, run `python3 -E -s -B -m pytest` **from a root-only cwd** (`-m` inserts cwd on `sys.path`), then write the exploit as a probe and confirm 0.000 | Do **not** just `chmod` the planted paths or add them to a deny-list — `contact-export` §3.2 records three consecutive blocks from patching screens instead of closing the mechanism |
| QC **"Symlinked Output Path" (E5)** listing `/app` paths your verifier reads | Stop reading `/app` entirely — move every case *and* expectation into the sealed tests tree. Deleting the read deletes the finding | Do **not** bolt on `O_NOFOLLOW`/realpath guards if you can simply not read the path. And never leave a `chown -R`/`chmod -R` pointed at an agent-writable directory |
| A `deep_review`/`ava_review` **advisory** while the gate says PASS | Fix it in the same push as the real blocker. The AVA `sound_verifier` advisory here was closed for free by the E5 fix | Do **not** defer it — `sweep-replay` §7: "fixing it cost minutes, finding out later costs a cycle" |
| Candidate crux is a real published rule | Check the **normative verb first** (MUST vs SHOULD/MAY), then check whether **any installable tool answers the graded question** | Do **not** design around a MAY. Do **not** assume a library's existence disqualifies the domain — ask whether it answers *this* question |
| `pass2` **0/2** with two *distinct* valid causes and four axes built | Hold the design; spend the cycle on gate fixes | Do **not** add a fifth axis (`lumenp` §3), and do **not** restore concealment |
| Two axes gated at pass@5, two did not | Keep all four | Do **not** cut the silent ones — fourth confirmation now, after `reduce-palaeomag` §4.2, `replay-strata-plans` §4.3 and `filer-access-audit` §4.2 |
| Task **accepted at pass@5 0/5** and you hold a README improvement | Hold it. 0/5 is the ceiling | Do **not** push. A push re-rolls all 31 rubric criteria plus `deep_review`/`ava_review`/QC and burns a rate-limited slot. Fourth confirmation after `nfs4-access-audit` §5.3, `merge-lora` §7, `reassemble-tap-sessions` §6 |

---

## 7. Bugs I introduced myself

1. **Graded an input my own contract said could never arrive** (`ho-head-range-ignored`, HEAD +
   Range). Written before the contract text was finalised, never re-checked afterwards. The
   general lesson: **the agent-visible contract and the graded case set are two artifacts that
   drift**, and nothing catches the drift but an explicit audit. Now enforced in the builder.
2. **`ENV PYTHONPATH=/app` for agent ergonomics, forgetting the verifier inherits the image.**
   The convenience was worth ~zero (`check_samples.py` already does `sys.path.insert`, and `/app`
   is `WORKDIR`); the cost was a root-level code-execution hijack. **Any `ENV` in the task image
   is also an `ENV` for the verifier.**
3. **Wrote the runner to a predictable `/tmp/edgecache_runner.py`** — an agent-writable path the
   root verifier opens for write. Not flagged by any gate; found while fixing E3. Replaced with
   `tempfile.mkdtemp()`.
4. **Miscounted my own mutants in `task.toml`** on the first draft ("five deliberately-wrong
   implementations" listing six; catch-counts starting `3,` when the first was 5). Caught by
   re-reading against the calibration output before pushing. Numbers in `difficulty_explanation`
   are graded prose — `sweep-replay` §6 warns they restate the design independently of the README
   and drift silently.
5. **A stray duplicated sentence in the README** after a scripted edit inserted a note the table
   header already made. Scripted `README` edits need a read-back of the surrounding paragraph,
   not just an assertion that the pattern matched once.

---

## 8. Process rules confirmed

- **`gh repo fork <repo> --clone --remote` fails with a usage dump** ("the `--remote` flag is
  unsupported when a repository argument is provided"). `gh repo fork <repo> --clone` works.
  Second confirmation after `reassemble-tap-sessions` §8.
- **Set `user.name`/`user.email` in the repo's local config at clone time.** Done here before the
  first commit; no rewrite needed. `gh api user --jq .login` for the name.
- **Never push while a run is in flight.** Checked `gh run list` immediately before the second
  push.
- **One commit per round of work**, README included in the same commit — never `git add -A` at
  the repo root without reading `git status --porcelain` first.
- **`jobs/` is in the repo `.gitignore`**, so local `harbor run` output never stages. Verify it
  is there before the first run.
- **A `qc_gate` early-exit defers most checks.** The first push's QC ran 17 of 38 and deferred 21;
  the second ran all 37 clean. A first-cycle QC pass tells you much less than a second-cycle one.
- **`pass2_suggestion` shows `skipping` when `pass2` passes.** That is normal, not a broken job.

---

## 9. Reusable checklist for the next task

Before writing any code:

- [ ] List every task in `previous-task-data.md` and write down why this design is not one of
      them — artifact, governing authority, and scenario-shape-plus-crux-family.
- [ ] For each candidate crux: **normative verb** (drop SHOULD/MAY with escape clauses), and
      **local-oracle test** (can `apt-get`/`pip` answer the graded question, not merely something
      adjacent?).
- [ ] Confirm the deciding case needs outside knowledge or a real convention — not something
      recoverable by careful reasoning over the stated spec alone. Pure logic traps do not stump.
- [ ] Confirm the crux is **noticed** (a property of the input) rather than **memorised** (a table
      or a list). Both C and B here are prose exceptions to an otherwise uniform pattern.
- [ ] Plan **at least three axes**, reached by different questions.

Before the first push:

- [ ] Write the calibration mutants *first*: each asserted sample-inert, each caught by held-out
      cases, plus at least one rival reading the shipped sample **refutes**.
- [ ] Hand-plant held-out expectations from the source, then require the reference to agree.
- [ ] Audit every graded case against every guarantee the agent-visible contract makes.
- [ ] Grep every agent-visible file for the crux vocabulary; the only hit should be the locator.
- [ ] Dockerfile: no `ENV` you would not hand the verifier; `.dockerignore` present; no literal
      `solution/` or `tests/` anywhere including comments.
- [ ] `test.sh`: clear `PYTHON*`, `python3 -E -s -B -m pytest` from a root-only cwd, no recursive
      `chown`/`chmod` at an agent-writable path, no predictable temp path opened for write.
- [ ] Verifier reads nothing under `/app`.
- [ ] Probes run end to end through the real verifier: naive mutant → 0.000 with the *expected*
      failure profile; sealed-material reader → 0.000; harness hijack → 0.000. Confirm each probe
      actually **ran** (grep the agent log for its own marker).
- [ ] `oracle = 1.000`, `nop = 0.000`.
- [ ] README diffed against the code: test names, every count, every calibration number.
- [ ] Numbers in `task.toml`'s three explanations re-read against the same source.

---

## 10. One-paragraph version for future me

Pick a real published standard whose rules are **MUST**-level, whose deciding branches are
**conditional on a property of the input**, and which **no installable tool can answer for the
agent** — then name the standard exactly once, as a locator, and enumerate nothing. Ship a large,
complete-*looking* sample suite *with its answers* and a replay script, and construct it so every
deciding rule is not merely absent but **equivalent** on every shipped case: the wrong reading
must reproduce the sample byte for byte, and at least one shipped case should actively refute a
rival reading so it never becomes an invalid failure. Build four such axes even though only two
will fire. The single most encouraging thing this run produced is trial `Q4cLVX7` asserting, in
its own reasoning, that *"a server MUST evaluate an If-Range precondition containing an HTTP-date
using the same rules as If-Unmodified-Since"* — a confident, MUST-level misrecollection of a
standard the model plainly knows well. That is the real target: not a rule the model has never
heard of, but **a conditional exception inside a rule it is sure it already knows**, placed where
the sample suite will never punish getting it wrong. All five agents confirmed 33/33 on the
shipped samples and quit with three quarters of their budget unspent.
