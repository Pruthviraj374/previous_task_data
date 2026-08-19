# dynamo/repair-portal-dispatch — the tool's own defaults as the crux

Repo: `dynamo-0444752-debugging-and-repair`, PR #3, branch `submission`, fork `Pruthviraj374`.
Category: **Debugging and Repair** / Sub-category: **Configuration Repair**.
Benchmarked against `Model A` via Terminus-2.

**Accepted 2026-08-19 at commit `55f5d65`. pass@5 = 0/5 solved, avg@5 = 0.000, 5 good
valid failures, 0 soft-timeout, 0 task/verifier issues, 0 reward hacking.** Every gate
green; `qc_gate`, `deep_review` and `ava_review` all passed on their first cycle.

Three pushes, about two hours. The first task in this playbook for *Debugging and Repair*.

Commits: `6e0620c` initial (later squashed) · `2f9e7b9` three more mechanisms after pass@2
showed only one axis gating · `55f5d65` re-skin after the similarity gate blocked (accepted).

---

## 1. The task

A records portal is fronted by one nginx server dispatching to three back-end programs.
Since a service split it misroutes and loses parts of what callers send. The agent repairs
the configuration in place.

- **Agent sees:** `/app/frontend/frontend.conf` (broken, and the only graded artifact),
  `/app/frontend/DISPATCH.md` (the complete normative specification),
  `/app/frontend/upstreams.conf`, and a runnable eleven-case check under `/app/checks/`.
- **Agent produces:** the repaired `/app/frontend/frontend.conf`.
- **Graded on:** 46 requests replayed through the agent's own file under a **real nginx**,
  with a recording stand-in behind each of the three back-end names — 35 held out, plus the
  11 shipped check cases re-judged against the whole specification.
- **Graded values:** which stand-in recorded the request, the request target and protocol
  version it saw, the method, body and header fields it saw, and the status the caller got.
  All categorical. No tolerance, no near-miss band.

---

## 2. The crux — a shape worth reusing

> **Disclose every rule. Let the tool's own defaults silently defeat a faithful
> transcription of them.**

This inverts the usual latent-crux design and it dissolves the disclose-vs-difficulty
deadlock that cost `retired-normalizer` three cycles and `lumenp` seven rounds. There is
nothing withheld, so `qc_gate` B5 ("a rival reading reproduces every shipped sample") and
the whole discoverability family have no purchase — and the task was still 0/5.

Eight mechanisms, all real documented nginx behaviour, all silent (`nginx -t` passes, the
server starts, every wrong request still returns 200 from a real back end):

1. a regex location is evaluated after the longest matching prefix location and wins, so
   rule order in the spec is not the order nginx picks a location in — only `^~` suppresses
   the regex pass;
2. `location /records/v2/` does not match the bare `/records/v2`, and because it proxies,
   nginx answers that path with a **301** rather than proxying it;
3. patching (2) with a no-slash prefix also swallows `/records/v20` and `/records/v2x` —
   the two holes need an exact-match location *beside* the prefix one, so one edit cannot
   close both;
4. **`proxy_set_header` replaces rather than merges** — adding one per-back-end field
   inside a location silently strips all four server-level fields from that back end;
5. `~` vs `~*`, and `$remote_addr` vs `$proxy_add_x_forwarded_for`;
6. nginx proxies as **HTTP/1.0** unless `proxy_http_version 1.1`;
7. **`underscores_in_headers` defaults off** — the natural implementation of "pass every
   client field through" is to write nothing at all, and writing nothing is wrong;
8. `client_max_body_size` defaults to 1 MB.

### Invariants that make it work

1. **Grade by running the real tool.** The verifier starts an actual nginx over the agent's
   file. There is no reference reimplementation to disagree with, so `qc_gate` B1
   ("ambiguous rule") has almost nothing to bite on — the rubric passed 31/31 twice.
2. **Behavioural grading kills the sound-alternative objection by construction.** A
   structurally different correct build (regex ordering + `rewrite` + `if` instead of
   exact-match + `^~`) was measured to pass all 35. Any configuration meeting the spec
   passes.
3. **A shipped self-check that is complete-looking and silent on every trap.** Eleven cases
   the agent can run, green on every wrong repair measured. This is `contact-export` §9 and
   `merge-lora` §2 applied to a config task, and pass@2 caught an agent quitting **in under
   three minutes** on the strength of 11/11.
4. **The check samples fields, not just requests.** It verifies the four common fields only
   on the back end that has no per-back-end field of its own, and each back end's own field
   on its own rows. That reads as ordinary QA sampling and is exactly blind to mechanism 4.
5. **Grade what the stand-in recorded, never the response body.** A configuration that
   synthesises a reply with `return` reaches no stand-in and fails.
6. **Upstream ports chosen at verify time.** Defeats both a hardcoded address and any
   process the agent might leave listening.

---

## 3. Dead ends and corrections

**(a) Four of the first five mechanisms gated nothing.** pass@2 on the first push returned
1 pass / 1 fail, and the analysis was blunt: *"Both agents independently arrived at the same
structural decisions... the nginx location-matching semantics are well-represented in
training data."* Mechanisms 1, 2, 3 and 5 — all the clever routing ones — discriminated
zero. The single failure rested entirely on mechanism 4.

**One deciding axis at a 50% solve rate is a coin flip against the ≤2/5 bar, and pass@2
passing does not make it safe.** Adding mechanisms 6–8 *before* spending the trials slot is
what turned 1/2 into 0/2 and then 0/5. `rebuild-readout-builder` §3.1 generalises: act on
the axis count, not on the gate verdict.

**(b) My ranking of the new axes was partly inverted — again.** Of the three added, only
mechanism 7 caused pass@5 failures. Mechanisms 6 and 8 gated nothing. Adding the *trio* is
what worked; picking one would have been a gamble. Fifth confirmation of the
`filer-access-audit` / `request-preconditions` / `rebuild-uptime-rollups` finding.

**(c) Pinning the protocol version on every case was a design error, caught locally.**
Asserting HTTP/1.1 on all 35 held-out requests made one missing directive fail everything —
swamping every other axis and reducing the task to a one-line directive. Narrowed to a
three-case group so it weighs the same as every other axis. **Any rule asserted on every
case is a global multiplier, not an axis.**

**(d) The similarity gate blocked push 2, and the margin was always the problem.** Push 1
scored **0.8967** on the task fingerprint against a **0.9** threshold and passed. Modest
edits to `instruction.md` and `task.toml` crossed it. Paraphrase cannot buy 0.0033.

The fix was to move off the framing, not reword it: new scenario, back-end names, paths,
header fields, file names and task name, with both prose pages rewritten from scratch and
the specification's emphasis moved from "gateway routing" to "what the back end must find
on arrival". Result: instruction 0.8033 → **0.6868**, fingerprint 0.8967 → **0.8767**. The
prose rewrite did the work; the nginx mechanisms were never the collision.

**Treat a passing similarity score above ~0.87 as a standing constraint on every later
edit,** not as a one-time clearance. This is the cheapest gate to re-test (it runs in ~100 s
and blocks before `pass2`, so a retry costs no rate-limited trial slots) and the most
expensive to ignore — the blocked push wasted a banked pass@2.

**(e) A case-sensitive rename silently disarmed two fixtures.** Renaming `/api/v1` →
`/records/v2` left the case-sensitivity fixtures at `/API/v1/users` and `/api/V1/users`,
which no longer resembled the new prefix at all. The mutant that should fail them went from
2 failures to 0. Only re-running the **whole** mutant table after the rename caught it.
`experiment-analysis-frame` §7 confirmed in a new form: after any rename, re-measure every
mutant rather than assuming behaviour-preserving edits preserved discrimination.

---

## 4. What the model actually did (pass@5, 0/5)

Two independent clusters, neither a timeout, reward-hack or verifier defect:

- **Cluster A — `underscores_in_headers` (3/5).** All three repeated `proxy_set_header`
  correctly in every location (mechanism 4 solved) and omitted the one directive. **All
  three explicitly named it during reasoning and then dismissed it as unlikely to be
  tested.** The shipped check gave no signal because its pass-through case uses
  `X-Trace-Id` (hyphen); the held-out case sends `x_trace_id` (underscore).
- **Cluster B — `proxy_set_header` replacement (2/5).** Both set the four common fields at
  server level and added only per-back-end fields inside locations, *explicitly reasoning
  that server-level directives would be inherited*. Confident, wrong, silent.

The Cluster A wording is `accrued-interest` in `34-*.md` verbatim — the model names the
risk and drops it. **A rule the model can name and dismiss is worth more than one it has
never heard of**, because the dismissal is what the sample data has to earn: ship a
near-equivalent case where both readings agree (hyphen), and hold back the one where they
diverge (underscore).

---

## 5. Gate log

| Push | Gate | Result |
|---|---|---|
| `6e0620c` | static, rubric (31/31), duplicate UNIQUE, validation, `deep_review`, `ava_review`, `tier1`, `qc_exec` | all pass first cycle |
| `6e0620c` | `pass2` | **1 pass / 1 fail** — passed the gate, but only one axis gating |
| `2f9e7b9` | `cosine_similarity` | **FAIL** — everything downstream skipped |
| `55f5d65` | every gate incl. `qc_gate` | pass |
| `55f5d65` | `pass2` → `trials` | **0/2** → **pass@5 0/5, avg@5 0.000** → `accepted` |

Advisories worth recording: the rubric twice flagged `[task].description` as possibly
outside Harbor's `[task]` schema and passed it both times — it ships with the repo scaffold
and every accepted sibling carries it, so it was left alone. It also caught three stale
docstring literals the case-sensitive rename had missed (`v1`/`shared` for `r2`/`bulk`, "ten
cases" for eleven); the assertions were correct, only the prose was stale, which is why no
calibration caught them.

---

## 6. Error → what to do

| Symptom | Do |
|---|---|
| `pass2` passes but one axis carries the whole result | Add axes **before** the trials slot. A gate verdict is not an axis count |
| Choosing a crux in a domain the model knows well | Prefer **the tool's silent defaults** over clever use of its features. Location-matching semantics are memorised; `underscores_in_headers` is not |
| Similarity passed at ≥0.87 | Treat it as a live constraint on every later edit to `instruction.md`, the spec page or `task.toml`. Re-check before pushing content |
| Similarity blocked | Re-skin the **framing**, not the wording — scenario, names, paths, file names, and rewrite the prose from scratch. Mechanisms are rarely the collision |
| You renamed identifiers across the tree | Re-run the **entire** mutant table. A case-sensitive rename disarms fixtures silently |
| A rule you assert on every graded case | Don't. One missing directive then fails everything and swamps every other axis |
| Grading a configuration file | Run the real tool over it and assert on what a recording stand-in received. Near-zero ambiguity, and B1 has nothing to bite |
| Your verifier runs the agent's artifact | Make a refused request record as a graded miss, not an exception — otherwise a wrong config becomes a *verifier error* |

---

## 7. Reusable checklist

- [ ] Probe the real tool **before** designing. Six of eight mechanisms were confirmed
      against a live nginx in two throwaway containers before a line of task code existed;
      one candidate (a `//` double-slash trap) was **disproved** that way and dropped.
- [ ] Grade by running the real implementation; assert on observed effects, never on source.
- [ ] Build the shipped self-check to be complete-looking and green on every wrong repair —
      then measure that it is, for each wrong repair.
- [ ] Write one mutant per mechanism plus one whole-task naive build, and one **correct
      build of a different shape** that must pass everything.
- [ ] Check no single assertion spans every case.
- [ ] Generate the shipped sample data *from* the sealed case set (`tools/gen-check-cases.py`)
      so the two cannot drift.
- [ ] Re-measure the full mutant table after any rename.
- [ ] Record the similarity fingerprint and treat it as a budget.
- [ ] Never `git add -A`; one push per round; never push while a run is in flight.

---

## 8. One paragraph

A records portal's nginx front end has drifted from its written specification; the agent
repairs the configuration and is graded by running it under a real nginx with recording
stand-ins behind each back end. Every rule is disclosed — the difficulty is that eight
nginx defaults silently defeat a faithful transcription, which sidesteps the
disclose-versus-difficulty deadlock entirely and still produced pass@5 0/5. The first
revision failed to be hard because four of five mechanisms lived in nginx's
location-matching semantics, which the model knows cold; what actually stumped it was
`underscores_in_headers` (3/5, each agent naming the risk and dismissing it) and
`proxy_set_header` replacing rather than merging (2/5, each agent confidently reasoning the
opposite). The expensive mistake was pushing content into a 0.0033-wide similarity margin
without re-checking it, which cost a banked pass@2; the cheap fix was re-skinning the
framing rather than paraphrasing it.
