# dynamo/decide-crossorigin-fetches — browser-side cross-origin access decisions

| | |
|---|---|
| **Outcome** | **Accepted** — every gate green, `accepted` label |
| **Headline** | **pass@5 = 0/5, avg@5 = 0.000**, 5 of 5 good valid failures, 0 timeouts, 0 verifier issues |
| Repo | `handshake-project-dynamo/dynamo-f3c06f2-software-engineering` |
| PR | https://github.com/handshake-project-dynamo/dynamo-f3c06f2-software-engineering/pull/2 |
| Category / sub-category | Software Engineering / Web API and networking software (pre-seeded) — **first task in this sub-category** |
| Benchmarked model | Opus-4.8 via Terminus-2 (reported as `Model A`) |
| Final commit | `4fb8372` (second and last push) |
| Pushes to acceptance | **2** — first push cleared everything except `qc_gate`; second cleared `qc_gate` and ran pass@5 |

Two pushes, one gate failure, no redesign. The design was lifted almost wholesale from
`dynamo-300f2a9-request-preconditions.md` §4 and §10 — a different standard, a different
artifact, the same machinery and the same shape of crux. Read §4 here for what transferred
and §3 for the candidate domains that were killed on paper first.

---

## 1. What the task asks

`/app` holds the surviving pieces of Crossline, a tool a web platform team used to triage
"the browser is blocking my request" reports. The agent writes

```
python3 /app/decide.py <traces.json> <verdicts.json>
```

which, for each recorded fetch, emits `{id, preflight, outcome, readable_headers}` —
whether the browser preflighted it, whether the response reached script
(`delivered` / `network_error`), and which response field names script could read.

What the agent can see:

- `/app/data/traces.json` — 40 recorded fetches: page origin, the request (URL, method,
  headers, credentials mode), the endpoint's `OPTIONS` response, and the response to the
  request itself as it came off the wire.
- `/app/data/recorded.json` — the verdicts the browser fleet recorded for that capture.
- `/app/data/TRACE.md` — the format note. Both schemas, every guarantee the capture makes,
  and **one flat sentence** naming the WHATWG Fetch Standard. It enumerates none of its rules.
- `/app/check.py` — replays the shipped capture and diffs it.

Graded on the shipped 40 plus **71 held-out records** across nine captures not in the image.
Every graded value is categorical.

---

## 2. The crux, and the invariants that keep it alive

Eight rules, all normative in the Fetch Standard, all conditional, all silent when wrong:

| # | Rule | The common reading |
|---|---|---|
| A | a wildcard `Access-Control-Allow-Headers` covers every request header **except** `Authorization`, which must be named literally | a wildcard covers everything |
| B | **every** wildcard grant — methods, header names, exposed fields — is inert against a fetch with `credentials_mode: include`, not only the origin grant | only the origin grant is special |
| C | a request header is safelisted on its **value** as well as its name: over-128-byte values, and values carrying bytes the safelist excludes, are not safelisted | the four safelisted names are always safe |
| D | a preflight is accepted on any status in the ok range | a preflight must answer 200 |
| E | the credential grant is the byte string `true`; the origin grant is compared byte for byte against the serialized page origin | either is compared leniently |
| F | exactly six method names are uppercased; every other method keeps the case the page wrote and is byte-compared against the declared methods | methods are matched case-insensitively |
| G | the seven safelisted response field names are readable whether or not the response exposed them; the two forbidden names never are | only what the response exposes is readable |
| H | an origin is *serialized* — scheme and host folded to lower case, a default port dropped, a non-default port kept — before comparison | the URL's text is compared as written |

**The invariants. Break any of these and the task stops working:**

1. **Every rule is inert on all 40 shipped records.** Not absent — *equivalent*. The shipped
   capture carries `Authorization` only alongside an explicit declaration, wildcards only on
   non-credentialed fetches, safelisted values only short and byte-clean, preflights only at
   200 and 204, credential grants only as lowercase `true`, methods only in a case that
   normalizes. Measured, not asserted: 13 distinct wrong readings reproduce all 40 verdicts
   exactly (`tools/calibrate.py`).
2. **Seven further readings are refuted by the shipped capture on purpose.** A credentialed
   fetch met with a wildcard *origin* grant, a preflight at 204, an unexposed but readable
   `Last-Modified`, a lowercase `put` that normalizes — each turns a rival reading into a red
   light *before* grading rather than an unexplained failure after it.
3. **No rule is named anywhere the agent can read.** Verified by grep over `instruction.md`,
   `TRACE.md` and `check.py` for `wildcard`, `128`, `safelist`, `normali`, `uppercase`,
   `essence`, `byte-case`, `ok status`, `CORS`: zero hits. The only hit for `lowercase` is the
   output-format sentence for `readable_headers`. The standard is named once, as a locator.
4. **Every graded record satisfies every guarantee `TRACE.md` makes** (unique field names per
   record, absolute https URL with a path and no userinfo, the three credentials modes).
5. **Held-out expectations are hand-planted from the standard**, then the reference is
   *required* to agree with all 111 of them; `tools/build_traces.py` stops the build on any
   disagreement. There is no `_reference.py` computing expectations at verify time.
6. **Categorical grading throughout** — a boolean, one of two names, a sorted list of lowercase
   strings. No tolerance, no near-miss band.

---

## 3. Dead ends — designs rejected on paper, with the reason

None cost a pipeline cycle. All were killed during design using this directory plus one read
of each candidate standard. **Rejecting on paper is free; rejecting at pass@2 costs an hour.**

**a) RFC 9110 conditional requests / content negotiation — killed by the sibling-task rule.**
The obvious first idea in this category. `dynamo-300f2a9-request-preconditions` already owns
RFC 9110 §13, and §"Hard rule" in `previous-task-data.md` treats *the same governing authority
supplying the crux* as the same task even in a different sub-category. Content negotiation
(§12) is the same authority. Dropped without writing anything.

**b) MQTT v5 broker semantics — killed by the local-oracle test.**
Genuinely excellent crux material (retain-handling options, no-local, retain-as-published, the
zero-byte retained publish that still gets delivered). Killed because `apt-get install mosquitto`
plus `paho-mqtt`'s `SubscribeOptions` is an *empirical* oracle: an agent can drive a real broker
and diff. `filer-access-audit` §4.1's test is not "does a library exist" but "can the environment
answer the graded question", and here it plainly can.

**c) HTTP/2 frame-level conformance (RFC 9113) — same test.** `h2` (hyper-h2) is a pure-Python
HTTP/2 state machine that answers exactly the graded question. Rejected.

**d) HPACK, JSON Patch, URI templates, structured fields — same test.** `hpack`, `jsonpatch`,
`uritemplate`, `http-sfv` are each an exact oracle one `pip install` away. Also `urljoin` and
`http.cookiejar` are in the **stdlib**, which kills URI resolution and cookie matching outright.

**e) WebSocket framing (RFC 6455) — same test, marginal.** `wsproto` and `websockets` parse
frame streams and raise specific protocol errors. Rejected, though less decisively than (b)–(d).

**f) The local-oracle test applied to the winning design.** No pip package implements the
*browser-side* CORS check. `flask-cors`, `django-cors-headers` and `starlette`'s middleware all
generate response headers server-side; none decides what script observes. Only a headless browser
could answer it, and driving one over arbitrary synthetic captures is not a 50-minute detour.
This is the line `filer-access-audit` §4.1 draws and `reassemble-tap-sessions` lives on: a tool
existing that does *something similar* is not the same as the tool answering *this*.

**g) The standard's aggregate-volume rule for safelisted request headers — killed by arithmetic.**
Was going to be a beautiful latent axis: exceed 1024 bytes of safelisted values and all of them
become undeclarable. Checked before building — a value over 128 bytes is *already* unsafelisted
individually, and there are only five safelisted names, so with unique field names per record the
total cannot exceed ~640. **The rule can never fire.** Had it shipped, it would have been an
untestable branch in the reference and a `qc_gate` C3 finding waiting to happen. Ten minutes of
arithmetic; would have cost a cycle.

---

## 4. What actually worked

**The winning shape, stated once:** a real published standard the instruction names *once and
only as a locator*, whose deciding rules are conditional exceptions inside rules the model is
sure it already knows, in a domain where no installable tool answers the graded question.

That sentence is `request-preconditions` §10 almost verbatim. What is new here is the evidence
that it **transfers across standards**: same shape, different authority (WHATWG Fetch vs RFC 9110),
different artifact (a browser networking layer vs an origin server), different sub-category —
and the same 0/5.

Specific decisions that carried it:

- **Picked a standard the model is *confident* about.** CORS is one of the most-written-about
  topics in web development, which is the point: the training data captures the common-case
  rules and skips the exceptions. pass@5's own words: *"agents are drawing on training-data
  knowledge of CORS (which captures the common-case rules) rather than carefully reading the
  full WHATWG Fetch Standard from first principles."*
- **Equivalence, not omission.** Every shipped record is one a wrong reading also gets right.
  All five agents hit **40/40 on `check.py`** and quit — 8.5 to 16 minutes of a 60-minute budget.
- **Eight axes, not one.** Four fired in every trial (A, B, C, F); three more fired in subsets
  (E in 3, H in 2, G in 1). **D never gated.** Per `filer-access-audit` §4.2 /
  `reduce-palaeomag` §4.2 / `replay-strata-plans` §4.3 / `request-preconditions` §6, that is not
  a reason to cut it — this is now the fifth task where a quiet axis was kept and the loud ones
  were not the ones predicted.
- **A shipped self-check that is complete-looking and silent on the trap.** `check.py` reports
  40/40 and is the last thing every trial ran before `mark_task_complete`.
- **Ground truth planted, not derived.** All 111 held-out verdicts hand-written from the
  standard, the reference then required to agree. `deep_review` independently re-derived h02,
  h03 and h05 and reported *"No copy-paste, off-by-one, or Oracle-quirk expecteds found."*

---

## 5. Gate-by-gate log

### Push 1 — `8b64115`

Everything green on the first attempt except one QC finding.

| Gate | Verdict | Note |
|---|---|---|
| `changes` (static) | PASS | all 25 checks, including **"non-trivial build context has a .dockerignore"** — present from the first commit because `previous-task-data.md`'s symptom index names it |
| `review` (rubric) | PASS | **31/31**, zero failures. Two advisory notes (below) |
| `similarity` / `cosine_similarity` | PASS | UNIQUE; top lexical match `write-compressor` at 0.079 |
| `validation` | PASS | docker / oracle / nop |
| `ava_review` | PASS | Oracle-Derivation clean |
| `deep_review` | PASS | no blocking issues; 2 advisory notes |
| `pass2` | **PASS** | **0/2, 2 valid failures**, all 7 trajectory axes PASS, *"Rerun Recommended: NO"* |
| `qc_exec` / `qc_eval` | PASS | 36 of 37 probes passed |
| **`qc_gate`** | **FAIL** | one Major finding — below |

**The blocker — C3 "Narrow / Hardcodable Held-Out Coverage":**

> *Mutation: removed 'host = host.lower()' in origin_of() (violates the stated origin
> serialization/comparison requirement). Held-out suite still passes all 11 tests, reward=1.
> Yet on valid input page_origin=https://a.example fetching https://A.example/x the mutant
> returns outcome=network_error while…*

### Push 2 — `4fb8372`

| Gate | Verdict |
|---|---|
| every gate above | PASS (rubric re-rolled 31/31; `pass2` again **0/2, 2 valid**) |
| **`qc_gate`** | **PASS** — 13s |
| **`trials`** | **PASS — pass@5 0/5, avg@5 0.000**, 5 good-valid-fail, 0 timeouts, 0 verifier issues |

Label went `in-progress, needs-revision` → **`accepted`**.

**pass@5 detail worth keeping.** Universal failures across all five trials:
`test_h01`, `test_h02`, `test_h03`, `test_h07`, `test_h08`. Subset failures: `h05` (3/5),
`h09` (2/5), `h06` (1/5). **Never failed: `test_h04`** (the preflight ok-status axis) — plus the
contract, archive and shipped-capture tests. One `near_miss` FAIL on trial `F7RwY2V`, which the
aggregate itself dismissed: *"an overly generous framing — the same five bugs present in F7RwY2V
are identical to those in the other trials… No corrective action is indicated."*

---

## 6. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| `qc_gate` **C3** naming one surviving mutant in your reference | **Build the sweep, not the patch.** Write a tool that mutates *every* decision the reference makes — case folds, strips, numeric bounds, comparisons, constant-set members, `and`/`or` operands, `if …: return` guards — replays every capture through each mutant, and fails on any survivor it cannot explain. The first run here found **22** uncovered decisions, not one | Do **not** add a fixture for the named case and re-push. `replay-deposit-ledger` §4.1 records that finding recurring; QC early-exits, so you get one per round and pay a cycle for each |
| A survivor your sweep finds | Sort it into three piles: a **real gap** → new fixture; a **provably redundant branch** → delete it from the reference; a **genuine equivalence** → keep it and record the reason in the tool, so the next run does not re-raise it | Do **not** add a fixture for a branch that cannot change an answer — you are shipping an untestable case to hide an untestable branch |
| A reference branch you cannot write a fixture for | Check whether it can fire **at all** given the format's guarantees. Five guards here (MIME slash-count, empty type, empty subtype, non-token characters, two name case-folds) were provably unable to change a verdict, and deleting them was correct | Do **not** keep it "for spec fidelity". A branch no capture decides is the same C3 finding waiting to be found |
| Constants written as arithmetic over code points | Write them as byte/character **literals** and add a build-time check that membership is unchanged | Do **not** leave `range(0x30, 0x3A)`-style constants in a graded reference. Each integer is a mutation site with no meaningful fixture; rewriting removed ~40 noise survivors here in one edit |
| A rubric criterion passed with an **advisory note** | Fold it into the same push as the real blocker. Both `deep_review` advisories (stage the capture under an opaque name; comment the byte-string intent) and the `instruction_concision` note went in with the C3 fix | Do **not** push a note-only fix on its own. It re-rolls all 31 rubric criteria and burns a rate-limited slot — `contact-export` §3.4 lost a cycle to exactly that |
| `pass2` **0/2** with several axes already firing | Hold the design and spend the cycle on the gate fix | Do **not** add another axis (`lumenp` §3), and do **not** restore concealment |
| Task **accepted at pass@5 0/5** and you hold a polish idea | Hold it. 0/5 is the ceiling | Do **not** push. Fifth confirmation after `nfs4-access-audit` §5.3, `merge-lora` §7, `reassemble-tap-sessions` §6, `request-preconditions` §6 |
| Candidate crux is a real published rule | Check the **normative verb**, then the **local-oracle test** — can `apt-get`/`pip` answer *this* question, not merely something adjacent? | Do **not** assume a library's existence disqualifies the domain, and do **not** assume its absence qualifies it. `mosquitto` is an apt-get away and killed MQTT; `flask-cors` exists and did not kill CORS, because it answers the server's question, not the browser's |
| A candidate rule that is real, published and latent | **Check it can fire at all** before designing around it. The 1024-byte volume rule is real, normative and perfectly latent — and unreachable given unique field names | Do **not** build the fixtures first and discover the arithmetic later |

---

## 7. Bugs I introduced myself

1. **Shipped `preflight_response: null` for fetches that were not preflighted** — in the first
   draft of the capture builder. That makes the graded `preflight` boolean *directly readable
   from the input*: null means no preflight. Caught only because a calibration mutant crashed on
   the missing key. Fixed by giving **every** record a recorded `OPTIONS` response and saying in
   `TRACE.md` that the harness captures it independently of what the browser did. **General
   lesson: any field you populate conditionally leaks the condition.**
2. **Added the `h09` fixture group and forgot the `test_h09` function.** The captures were built,
   the verdicts planted, the audit passed — and nothing graded them. Caught by counting
   `^def test_` against the fixture directory before committing. A held-out capture with no test
   is invisible to every gate *and* to pass@5.
3. **Nearly shipped the 1024-byte volume rule** as a live axis before doing the arithmetic
   (§3g). The fixture group was already sketched.
4. **Ran `harbor run` from the wrong working directory** and wrote a tool to a path that did not
   exist, silently. The heredoc failed, the follow-up `python3` failed loudly, no harm — but
   scripted file writes need an absolute path when the shell's cwd is not pinned.

---

## 8. Process rules confirmed

- **`gh repo fork <repo> --clone --remote` still fails with a usage dump.** `gh repo fork <repo>
  --clone` works. Third confirmation after `reassemble-tap-sessions` §8 and
  `request-preconditions` §8.
- **Set `user.name`/`user.email` in the repo's local config at clone time**, before the first
  commit. Done here; no rewrite needed.
- **`jobs/` is not in the scaffold `.gitignore`.** Add it before the first `harbor run` or the
  run artefacts stage.
- **Never push while a check is in flight.** `trials` held the lock for 25 minutes here.
- **Read job detail from the *current* run id.** `gh pr checks` aggregates, but `gh run view
  <id> --json jobs` against a stale run reports the *previous* cycle's outcome — here it showed
  `trials: skipped` from push 1 while push 2's `trials` was actually running. Get the id from
  `gh run list --json databaseId,headSha` first.
- **An empty `statuses` list on the commit is normal while `trials` runs.** The harbor `H`
  status only appears once grading dispatches; `restore-runbook-advisor` §8.2's "empty list →
  never dispatched" test applies to a *finished* gate, not a running one.
- **`pass2_suggestion` shows `skipping` when `pass2` passes.** Normal.
- **QC early-exits.** Push 1 reported one finding and *"36 checks passed"* of 37; push 2 ran
  clean. A first-cycle QC pass tells you much less than a second-cycle one.

---

## 9. Reusable checklist for the next task

Before writing any code:

- [ ] List every task in `previous-task-data.md` and write down why this design is not one of
      them — artifact, **governing authority**, and scenario-shape-plus-crux-family. RFC 9110 is
      spent; so is any near neighbour of it.
- [ ] For each candidate crux: **normative verb**, then the **local-oracle test** (can the
      environment answer *this* question?), then **can the rule fire at all** given the format's
      own guarantees.
- [ ] Confirm the deciding case needs outside knowledge or a real convention — not something
      recoverable by careful reasoning over the stated spec alone.
- [ ] Prefer a standard the model is **confident** about over one it has never seen. The target
      is a conditional exception inside a rule it is sure it already knows.
- [ ] Plan **at least four axes**, reached by different questions; expect half of them to be silent.

Before the first push:

- [ ] Write the calibration mutants first: each asserted sample-inert *and* caught by held-out
      records, plus several rival readings the shipped sample **refutes**.
- [ ] **Write the mechanical coverage sweep too, and run it before the first push, not after
      `qc_gate` says so.** This is the one thing that would have made this task a one-push
      acceptance.
- [ ] Hand-plant held-out expectations from the source, then require the reference to agree.
- [ ] Count `^def test_` against the held-out fixture directory.
- [ ] Audit every graded record against every guarantee the agent-visible contract makes, and
      check no field is populated *conditionally* in a way that leaks a graded value.
- [ ] Grep every agent-visible file for the crux vocabulary; the only hit should be the locator.
- [ ] Dockerfile: `.dockerignore` present, no `ENV` you would not hand the verifier, no literal
      `solution/` or `tests/`.
- [ ] Probes end to end through the real verifier: naive reading → 0.000 with the *expected*
      failure profile; sealed-material reader → 0.000; harness hijack → 0.000.
- [ ] `oracle = 1.000`, `nop = 0.000`.
- [ ] README diffed against the code — every count, every test name, every calibration number,
      checked programmatically rather than by eye.

---

## 10. One-paragraph version for future me

Pick a standard the model is **certain** it knows — CORS, not something obscure — and build the
crux out of the conditional exceptions inside it, the clauses that blog posts skip and the spec
states plainly. Name the standard once as a locator, enumerate nothing, ship a large
complete-*looking* sample suite with its answers and a replay script, and construct every shipped
record so that the common reading lands on the recorded verdict exactly; add a handful of records
that actively refute rival readings so a wrong rebuild gets a red light before grading. Build
eight such axes even though only four will fire in every trial. Then — and this is the part that
cost the one gate cycle here — **mutate your own reference mechanically before you push**: every
case fold, bound, comparison, constant member and guard, replayed through every capture, failing
on any survivor you cannot explain. `qc_gate` runs that sweep whether or not you do, and it found
one survivor where my own hand-written mutants found none; when I finally wrote the sweep it found
twenty-two, five of which turned out to be redundant branches that should never have shipped. All
five pass@5 agents wrote a correct-looking 224–265-line implementation, saw 40/40 on the shipped
capture, and quit with three quarters of their budget unspent. The grader's summary is the whole
design in one line: *"agents are drawing on training-data knowledge of CORS rather than carefully
reading the full WHATWG Fetch Standard from first principles."*
