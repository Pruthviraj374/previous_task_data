# dynamo/serve-thesaurus-lookups — accepted on one push; the axioms of a standard the model knows well

| | |
|---|---|
| **Outcome** | **ACCEPTED** — every check green on the first push, `accepted` label |
| **Repo** | `dynamo-426dea0-data-querying-and-databases`, branch `submission`, fork `Pruthviraj374` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-426dea0-data-querying-and-databases/pull/2 |
| **Category / sub** | Data Querying and Databases / **Graph and semantic queries** (second in this sub-category, after `ledgergraph-canon`) |
| **Benchmarked model** | `task.toml` names Opus-4.8 / Terminus-2 |
| **Final commit** | `a3f3a69` (1 push, zero revisions) |
| **Headline** | **pass@5 = 0 solved, 5 good-valid-fail, avg@5 = 0.000.** pass@2 0/2. Rubric PASS all criteria first try. `qc_gate`, `deep_review`, `ava_review`, `tier1` all clean on the first cycle. Zero platform faults |

Four findings worth the read.

**One: the cheapest acceptance in this corpus — one push, zero content revisions, no gate ever
objected to anything.** `replay-collection-sort` took four pushes with three verifier-layer blocks;
`ledgergraph-canon` took three full redesigns and ~28 commits. The difference was not luck: every
soundness fix those two files paid a cycle to learn was built *before* push one, from this
directory — `restore-runbook-advisor` §3.3's "every disclosed mechanic must break the shipped sample
**and** a held-out fixture", `replay-collection-sort` §3.3's seal-at-grading-time plus sealed
shipped baseline, `read-cavity-captures` §7's `O_NOFOLLOW` on every graded path,
`replay-deposit-ledger` §4.6's `-S`/`-P`/plugin-autoload hardening, `filer-access-audit` §4.4's
expected-values-never-on-disk. **The prior files are worth more spent up front than consulted after
a block.**

**Two: an agent had the correct rule implemented and deleted it.** `task__kM5FgHz` built a working
transitive closure for `exactMatch` at step 9, then **actively regressed it at step 11** after
reasoning that the SKOS Reference does not declare `exactMatch` transitive. It does — S45, verbatim.
That is `accrued-interest`'s *"probably isn't being tested"* one register worse: not a rule
dismissed as untested, but a *correct implementation removed* on a confident misrecollection of a
standard the model otherwise handled well. Same shape as `request-preconditions` §10's MUST-level
misrecollection, now in a seventh category.

**Three: every axis gated, which is the first time in this corpus.** The running finding across
`filer-access-audit`, `request-preconditions`, `rebuild-uptime-rollups`, `replay-collection-sort`
and `replay-flash-capture` is that the author's ranking of which axis will gate is inverted, and
that two of four axes typically gate nothing. Here all six did — every one appears in the
pass@5 root-cause table. §2 argues why: the axes are not independent *rules* but the **same single
misreading** (take the asserted triples at face value) surfacing in six places, so an agent that
makes it fails everywhere at once and an agent that avoids it needs all six.

**Four: `pass2` at 0/2 and `trials` at 0/5 on the same commit, with pass@2's two failures already
naming the two root causes the five pass@5 failures would.** No difficulty tuning happened between
them because there was no second push. Recorded because the corpus is dense with the opposite —
`rebuild-readout-builder` §3.1's "0/2 is not evidence of difficulty" holds in general, but where
pass@2's *root-cause table* (not its verdict) already names distinct, designed mechanisms, it
predicted pass@5 exactly.

---

## 1. What the task asks

A crop-science catalogue's thesaurus lookup service is gone. One SKOS export survives, along with
one batch of lookups the front end sent and the answers the service returned.

- **Agent sees:** `instruction.md`, `/app/data/thesaurus.ttl` (one export, RDF 1.1 Turtle, SKOS),
  `/app/data/lookups.json` (31 lookups across all six operations), `/app/data/expected.json` (the
  answers, its end-to-end self-check), `/app/data/SERVICE.md` (the operator memo).
- **Agent produces:** `/app/lookup.py`, invoked
  `python3 /app/lookup.py <thesaurus.ttl> <lookups.json> <answers.json>`.
- **Graded on:** the shipped batch plus **twelve held-back exports**, 15 tests, all-or-nothing.
- **Output:** a JSON object keyed by lookup id, each value an ordered list of absolute IRIs.

Six operations: `parents`, `ancestors`, `scheme_concepts`, `exact_matches`, `close_matches`,
`collection_concepts`.

**The output type was chosen for grading, not for the domain.** An ordered list of identifiers has
no numeric margin, so `difficulty_evidence` has no "threshold artifact" argument available and
`near_miss` came back PASS 5/5 with the analysis writing *"No quantitative threshold is doing the
work — the concept is."* `replay-collection-sort` §4.2 recommended weighting this at crux-selection
time; doing so cost nothing here and deleted a whole class of finding. **Take the free version when
the domain offers one.**

---

## 2. The crux, and why six axes behave as one

The memo names the SKOS Reference as normative for how the export's relations behave and
**enumerates none of it**. The shipped export was written by the service's *nightly dump*, which
wrote every relation out in full — hierarchy links from both ends, mapping cliques closed,
collection contents flattened, every concept carrying its scheme directly. Every other export came
from an editing store or a migration tool and leaves the relations to be derived.

| Axis | SKOS statement | Inert in the shipped sample because | pass@5 |
|---|---|---|---|
| **1** | S25 `narrower` inverseOf `broader`; S41/S43 `broadMatch`/`narrowMatch` sub-properties of them | every hierarchy link is written from **both** ends | **all 5** (h01, h02) |
| **2** | S22/S24/S26 `broaderTransitive` is the transitive super-property carrying abbreviated links | the sample's two transitive assertions duplicate a direct link, so both readings agree | **4 of 5** (h04); h03 caught a *false-positive* reading in 1 |
| **3** | S7/S8 `topConceptOf` sub-property of `inScheme`, inverseOf `hasTopConcept` | every concept also carries `inScheme` directly | **all 5** (h05, h06) |
| **4** | S44/S45 `exactMatch` symmetric **and transitive** | the sample's one exact clique is written out closed | **all 5** (h07, h08) |
| **5** | S42 `exactMatch` sub-property of `closeMatch`; `closeMatch` itself not transitive | every exact pair also carries an explicit `closeMatch` | **1 of 5** via a distinct path |
| **6** | S36 every `memberList` item is a `member` — and a spelled-out `rdf:first`/`rdf:rest` chain is the same graph as `( )` syntax | the sample's ordered collection *also* lists its contents under `member`, flattened | **4 of 5** (h10); h09/h11 in 1 |

**Why they are one axis wearing six coats.** Each is the same decision — *index the predicate the
operation is named after, or derive the relation SKOS defines*. An agent that takes the asserted
triples at face value fails all six; an agent that reasons from the axioms must get all six. That
is why the usual "two of four axes gate nothing" pattern did not appear, and it is the design
lesson: **prefer axes that share one root misreading over axes that are independent rules.**
Independent rules distribute the failure rate; one misreading surfacing six times concentrates it.
(Contrast `repair-edge-compression` §3, where three traps sharing one *discovery step* collapsed
into one axis and weakened the task — the difference is that sharing a discovery step means one
insight solves all three, while sharing a root misreading means one insight is needed six times.)

**Invariants, machine-enforced in `tools/generate.py` — it writes nothing if one breaks:**

1. the shipped batch is answered **identically** by the reference and by all fourteen wrong
   readings. Critically, the batch is **selected mechanically** on exactly that test rather than
   hand-picked, so inertness is a property of the build and survives a later edit to the export.
   This is `nfs4-access-audit` §"selecting the shipped request set mechanically", and it is the
   single highest-leverage line in the generator;
2. every wrong reading is discriminated by **≥2** held-back exports (measured 2–6);
3. every rule the memo *does* disclose is pinned by the shipped batch: an empty answer, a
   multi-valued answer, an answer whose order differs from the order the export names those
   concepts in, an answer where keeping the subject would be wrong, and a subject the export omits;
4. no concept is its own ancestor in any export; every resource in a graded relation carries an
   explicit `rdf:type`;
5. **no held-back export uses a Turtle construct the shipped export never shows.** Added because
   the held-back set needed labelled blank nodes for `h10`, and shipping a construct the sample
   never demonstrates would make the parser work unfair rather than latent. It fired immediately on
   the first run — the fix was giving the shipped scheme a `dct:publisher` blank node.

---

## 3. Rejected on paper, before any code

| Rejected candidate | Why | Source |
|---|---|---|
| Anything reusing RDF canonicalization / URDNA2015 / blank-node labelling | `ledgergraph-canon` is **accepted in this exact sub-category** on that crux | `previous-task-data.md` §"Hard rule" |
| SPARQL 1.1 property paths | measured dead end — `ledgergraph-canon` §3.2, solved 2/2 three consecutive times; mainstream and tutorial-heavy | `ledgergraph-canon` §3.2 |
| Invented store-specific deviations from SKOS | disclosed → implemented; undisclosed → B5 blocks it | `lumenp` §3 |
| SKOS **integrity conditions** (S27 `related` disjoint with `broaderTransitive`, S37 `Collection` disjoint with `Concept`) | these constrain what a *conformant* export may contain, so grading them means grading my own choice of what a violation implies — no MUST forces an answer | `monograph-usage-report` §3.1, normative-verb test |
| `skos:related` symmetry as an axis | real (S23) but **fires always** — every writer either records both directions or neither, so there is no judgement to get wrong | `lumenp` §6 |
| An `rdflib`-based crux | `rdflib` is one `pip install` from being a local oracle for the whole task | `filer-access-audit` §4.1 |

**On the last row and why the task survives anyway.** `rdflib` would parse the Turtle, but it does
**not** answer the graded question — it materialises no SKOS entailment without an explicit
reasoner, so a solver using it still has to decide, axiom by axiom, which relations to derive.
That is `request-preconditions` §3(c)'s test applied precisely: ask whether the library answers *the
graded question*, not whether it is adjacent. All five trials wrote their own Turtle parser anyway.

**Why SKOS passed the obscurity filter that killed SPARQL.** `ledgergraph-canon` §3.2's refined rule
is: would a competent engineer already know the decisive edge case, or would they need to open the
spec? SKOS's *vocabulary* is widely known — every trial used `skos:broader` correctly. Its
**axiom list** is not: the S-numbered statements live in one Recommendation most practitioners
reach for a library instead of reading, and the distinction between `broader` and `broaderTransitive`
is exactly the kind of thing recalled wrongly with confidence. The proof is finding two: an agent
that *knew* `exactMatch` well enough to implement its closure talked itself out of S45.

---

## 4. What worked

### 4.1 Name the authority, enumerate nothing — third confirmation, third sub-category

`SERVICE.md` says the relations are *"the ones the SKOS Reference (W3C Recommendation, 18 August
2009) defines"* and restates not one of them. `deep_review` and `qc_gate` had nothing to call
underdetermined, because the rules are one lookup away and the gate can see that. This is
`replay-run-histories` §4 / `replay-collection-sort` §2 / `monograph-usage-report` §3.2, and it now
holds in a seventh category. The register stayed flat and descriptive — no "everywhere it is
silent", no naming of areas, no sign a gap exists (`replay-strata-plans` §3.2).

**The memo lives in `/app`, not only in `instruction.md`.** Harbor hands the instruction over as the
prompt; it is never a file in the image, and QC probes read the pristine image
(`restore-runbook-advisor` §3.2, `rebuild-readout-builder` §3.3). Costless to get right up front.

### 4.2 Quote the standard in the reviewer-facing README, never in `instruction.md`

All twelve S-numbered statements are reproduced **verbatim** in the root `README.md`, with a
sentence noting every one is a vocabulary *axiom* rather than an integrity condition — so an export
leaving a relation to be derived is well-formed SKOS, not a malformed file. A read-only reviewer
cannot fetch the Recommendation. This is `monograph-usage-report` §3.3's fix applied *prospectively*
instead of after an `unambiguous` FAIL, and `unambiguous` passed first try.

### 4.3 Two independent decompositions, and the cross-check earning its keep

`tests/_reference.py` materialises the SKOS relations as explicit sets and reads answers off them;
`solution/lookup.py` walks a predicate index on demand and parses Turtle with a hand-written
character scanner rather than the reference's regex tokeniser. Written separately, agreeing on all
13 fixtures. Without this, `oracle = 1.000` is nearly vacuous (`experiment-analysis-frame` §7).

### 4.4 Every soundness claim proven by performing the attack

`tools/probes.py` ships six complete bypasses plus the accept-side case, all scored by the **real**
verifier: echo `expected.json`, import `_reference`, walk the sealed tree, symlink the answer path
at a root-only file, split the program across two files, import a third-party package. All 0.000;
the correct program still 1.000. `ava_review` passed first try and its only `anti_cheat` note was
non-blocking and complimentary.

### 4.5 Local checks that replace guessing

```
python3 tools/generate.py     # invariants 1-5; refuses to write on failure
python3 tools/calibrate.py    # two implementations vs 13 fixtures, no Docker (fast)
python3 tools/mutants.py      # 14 wrong readings, real verifier, built image
python3 tools/probes.py       # 6 bypasses + accept side
cd task && harbor run -p . --agent oracle   # 1.000
cd task && harbor run -p . --agent nop      # 0.000
```

`mutants.py` reports **pytest node ids from the real verifier**, so "inert on the sample, fails
h03/h04" is a claim about the grader rather than about my own comparison function.

---

## 5. The one real bug, and it was in my own harness

`tools/probes.py` first reported **`imports_the_reference` scoring 1.000** — a full reward bypass:
the submission did `sys.path.insert(0, "/tests")` and called `_reference.resolve`.

The instinct is to harden `test.sh`. That would have been wrong. The seal was already correct; the
**probe harness** was unfaithful. It bind-mounted `task/tests` from the macOS host, and a host bind
mount carries the host's ownership and modes into the container, so `chmod -R go-rwx /tests` had no
effect on the mounted tree. This is `rebuild-plate-rasterizer` §4.3 — *"a `chmod` sandbox that does
not work when you probe it in local Docker on macOS"* — which I had read and still walked into.

**What settled it in one command, and the reusable move:** instead of reasoning about it, I made
`test.sh` print `id`, `ls -ld` and `mount` for the sealed paths into `/logs/verifier/seal.txt` and
ran the real `harbor run --agent oracle`. Harbor's own overlay came back
`drwx------ 3 root root /tests` — already sealed before `test.sh` touches it. The fix was to the
*harness*: stage a container-resident copy (`cp -r /staged /tests && chown -R root:root /tests`)
so the probe reproduces Harbor rather than the host. Re-run: 0.000.

**Rule: when a probe reports a bypass, first ask whether the probe reproduces the real staging.**
A one-run diagnostic against the actual harness is cheaper than either hardening you do not need or
a gate cycle spent on a hole that was never there. Had I "fixed" `test.sh`, I would have shipped a
change that did nothing, against a finding that did not exist.

---

## 6. Gate-by-gate log

| Push | Commit | Result |
|---|---|---|
| 1 | `a3f3a69` | **everything ✅ on the first cycle** — changes (static) ✅ 13s · review (rubric) ✅ **PASS, all criteria** · similarity ✅ **UNIQUE** · cosine_similarity ✅ (instruction 0.592, verifier 0.814, fingerprint 0.717) · validation ✅ 1m6s · **pass2 ✅ 0/2, 2 valid fails** 24m58s · deep_review ✅ 4m25s · ava_review ✅ 9m29s · tier1 ✅ · qc_eval ✅ 13m47s · qc_exec ✅ · **qc_gate ✅** 15s · **trials ✅ 0 solved / 5 good-valid-fail / avg@5 = 0.000** 38m51s → `accepted` |

Full cycle ≈1h40m. **Zero platform faults** — no outage, no rate-limit, no stale `H` status, no
close/reopen needed.

Three non-blocking advisories, all recorded and none acted on:

- `anti_cheat`: the shipped `expected.json` is agent-readable — the gate itself noted `s00` is
  graded against a sealed copy and hardcoding cannot bypass the work, calling it *"standard sample
  I/O disclosure and fine"*. This is exactly the shape that **blocked** `replay-collection-sort`
  §3.3; the difference is that the seal and the sealed baseline were in place from push one.
- `task_toml_schema`: `[task].description` is not in the criterion's enumerated field list. Benign,
  graded PASS, present in the scaffold.
- `accurate_taxonomy_labels`: `analyze` alongside `implement` called *"defensible but slightly
  generous"*. Left as is.

**Do not push to clear a non-blocking advisory on an accepted PR** — `nfs4-access-audit` §5.3 /
`reassemble-tap-sessions` §6, and 0/5 is the ceiling; a push re-rolls every stochastic gate.

---

## 7. pass@5, and what the model actually did

0 solved · 5 good-valid-fail · avg@5 = 0.000. Every rubric criterion PASS 5/5:
`task_specification`, `reward_hacking`, `difficulty_crux`, `near_miss`, `refusals`, `low_timeout`,
`approach_validity`. Trials ran **6.5 to 30.5 minutes of a 3600 s budget** and every agent called
`task_complete` voluntarily — the corpus's most-repeated failure shape, sixth confirmation.

| Fixture | Trials failing | Axis |
|---|---|---|
| h01, h05, h06, h07, h08 | **5 of 5** | 1, 3, 4 |
| h02, h12 | 4–5 of 5 | 1, and the combined export |
| h04, h10 | 4 of 5 | 2, 6 |
| h03 | 1 of 5 | 2, as a **false positive** — `broaderTransitive` objects reported as immediate parents |
| h09, h11 | 1 of 5 | 6, nested-collection recursion |

The quotes and traces are the finding:

- `task__kM5FgHz` — built a correct `exactMatch` transitive closure at step 9 and **deleted it at
  step 11**, reasoning that SKOS does not declare `exactMatch` transitive. S45 says it does.
- `task__WD68tCM` (pass@2) — read the memo's *"Exports keep to one Turtle profile throughout"* as a
  guarantee that held-back exports use the same **SKOS recording style** as the sample, and
  therefore skipped the inverse, sub-property and transitivity axioms **entirely**.
- `task__HuCLd3p` — the only agent to implement `rdf:first`/`rdf:rest` chains, and the only one to
  make the *opposite* mistake on axis 2, reporting abbreviated links as immediate parents.
- `task__nGHzehs` (pass@2) — implemented five of six axes correctly and failed on exactly two: no
  BFS closure for `exactMatch`, and an `is_iri()` guard rejecting blank-node objects from
  spelled-out chains.

**The sentence in finding two of `task__WD68tCM` is the one to watch.** *"Exports keep to one Turtle
profile throughout"* was written to promise a **syntactic** guarantee (no constructs the sample
never shows — invariant 5) and one agent read it as a **semantic** one (the same SKOS recording
style). That is `motion-register` §4's data-shape-guarantee-read-as-a-rule, and it cut in the task's
favour here. It could equally have produced an invalid failure. **A guarantee about the data is read
as a guarantee about the meaning unless the sentence forecloses it** — say "profile" and mean
syntax, and expect to be read as meaning semantics.

---

## 8. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| A bypass probe reports **reward 1.000** | first check the probe reproduces the real staging. One `harbor run` printing `id`/`ls -ld`/`mount` from inside `test.sh` settles it | do not harden the verifier against a hole your harness invented — `rebuild-plate-rasterizer` §4.3, walked into a second time |
| Choosing between several candidate axes in one standard | prefer axes that are **the same root misreading in different places** over independent rules. All six gated here; the corpus's usual result is two of four gating nothing | do not treat six axes as six independent difficulty contributions and budget accordingly |
| Your sub-category already has an accepted task | read its case study before designing, and reject its crux *and its two dead designs* by name in writing | do not assume a different crux in the same sub-category is automatically clear — check the dead ends too |
| A candidate rule is an **integrity condition** rather than an axiom | drop it. Grading it means grading your own choice of what a violation implies | do not defend it — `monograph-usage-report` spent four rounds on this shape |
| A real published rule that **fires always** | reject it. `skos:related`'s symmetry is real and leaves no judgement to get wrong | do not count "real and published" as sufficient — `lumenp` §6 |
| The domain lets the answer be an **ordering or an id list** | take it. No tolerance, no rounding, no `difficulty_evidence` threshold argument, `near_miss` has nothing to bite | do not engineer an integer-only pipeline when the domain hands you a tolerance-free output type free |
| You are writing a data-shape guarantee into the memo | word it so it cannot be read as a guarantee about *meaning*. Mine said "one Turtle profile" and was read as "one SKOS recording style" | do not assume the narrow reading is the one that lands |
| Every gate passed on push one | stop. Write the retrospective | do not push the improvements you are holding — 0/5 is the ceiling |

---

## 9. Process rules confirmed

1. **Build every soundness fix this directory records *before* push one.** Six of them went in up
   front; `ava_review` and `qc_gate` passed first try, where the two prior tasks in adjacent
   sub-categories spent three and four cycles on exactly those findings.
2. **Encode the generator invariants before the first push, not in answer to a gate**
   (`reduce-palaeomag` §4.4). Invariant 5 fired on its first run and caught a real unfairness.
3. **Select the shipped request set mechanically** on "every wrong reading agrees here", never by
   hand (`nfs4-access-audit`). 31 requests were kept out of a larger candidate set by that test.
4. `.dockerignore` in `task/environment/` from commit one; no `solution`/`tests` substring anywhere
   in the Dockerfile (the static check is a literal scan, comments included); no
   `"You have N seconds…"` line; instruction at 186 words against the 1500-token cap.
5. `jobs/` added to `.gitignore` **before** the first `git add`; `git status --porcelain | grep jobs`
   before committing.
6. Git identity set in the repo's local config immediately after cloning, before the first commit.
7. `git pull --no-rebase` in `previous_task_data/` before writing this file.

---

## 10. Reusable checklist

- [ ] Read the case study for **your own sub-category** first, and reject its crux *and its dead
      designs* by name in writing.
- [ ] Pick an output type with no numeric tolerance if the domain offers one.
- [ ] Name the authority; enumerate nothing; flat descriptive register; ship the memo **inside
      `/app`**, not only in `instruction.md`.
- [ ] Quote the normative clauses **verbatim in the root README**, with S-numbers, for the read-only
      reviewer. Never in `instruction.md`.
- [ ] Apply the normative-verb test to every candidate axis: axiom, not integrity condition; MUST,
      not MAY; conditional, not always-firing.
- [ ] Ask whether an installable library answers **the graded question** or merely parses the input.
- [ ] Prefer axes that share one root misreading.
- [ ] Generator invariants, machine-enforced, refusing to write: sample inert under every wrong
      reading with the batch **selected** on that test; each wrong reading caught by ≥2 fixtures;
      every disclosed rule pinned by the sample; structural guarantees asserted; **no held-back
      construct the sample never shows**.
- [ ] Two independent decompositions for oracle vs ground truth.
- [ ] Seal `/tests` **and** the agent-visible answer key at grading time; grade the shipped case
      against a sealed copy.
- [ ] One committed probe per soundness claim, scored by the real verifier, accept side in the same
      run — and confirm the probe harness reproduces Harbor's staging before believing a 1.000.
- [ ] Before pushing: `harbor` oracle/nop, `mutants.py`, `probes.py`, grep README and `task.toml`
      for stale counts, `git status --porcelain | grep jobs`.

---

## 11. One-paragraph version for future me

A SKOS thesaurus lookup service rebuilt from one export and one recorded batch, graded on exact IRI
orderings across twelve held-back exports. The crux is that the shipped export was written by a
nightly dump that wrote every relation out in full, so indexing the predicate each operation is
named after reproduces it perfectly — while every other export leaves the relations to be derived
from SKOS's property axioms (S25/S41/S43 inverses and sub-properties, S22/S24 the transitive
super-property, S7/S8 `topConceptOf`, S42/S44/S45 `exactMatch` symmetric-transitive-and-a-sub-property-
of-`closeMatch`, S36 member lists), plus one format trap where a spelled-out `rdf:first`/`rdf:rest`
chain is the same graph as `( )` syntax. Six axes that are really one misreading in six places, which
is why all six gated where the corpus's usual result is half of them gating nothing. Accepted on a
single push with every gate green first try — pass@2 0/2, pass@5 0 solved / 5 good-valid-fail /
avg@5 0.000, rubric PASS on all criteria, zero platform faults — because every verifier-soundness fix
this directory records was built before push one instead of learned from a block. The sharpest
finding is an agent that implemented `exactMatch`'s transitive closure correctly at step 9 and
deleted it at step 11, having convinced itself the standard does not declare it transitive; the most
useful warning is that my own bypass probe reported a full reward-1.000 hole that did not exist,
because a macOS host bind mount carried host modes into the container and made Harbor's already-sealed
`/tests` look wide open — diagnosed in one run by printing `ls -ld` from inside the real verifier
rather than by hardening anything.
