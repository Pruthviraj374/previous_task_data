# dynamo/repair-edge-compression — the disclosure IS the test

Repo: `dynamo-924fa9a-debugging-and-repair`, PR #1, branch `submission`, fork `Pruthviraj374`.
Category: **Debugging and Repair** / Sub-category: **Performance Debugging**.
Benchmarked against `Model A` via Terminus-2.

**Accepted 2026-08-26 at commit `ea31a64`. pass@5 = 0/5 solved, avg@5 = 0.000,
4 good-valid-fail, 1 task/verifier-issue, 0 soft-timeout, 0 reward hacking.**
pass@2 on the accepted commit: **0/2 solved, 2 valid-fail.**

**Twenty-one pushes. Nineteen of them scored `2/2 solved` at pass@2.** This file is
mostly about why, because the thing that finally worked is one sentence and the
nineteen failures are the transferable content.

---

## 1. The task

An nginx edge serves an ops console and JSON report feeds pulled over metered
links. A transfer-cost review already switched compression on — a single
`gzip on;`, the faithful reading of that requirement.

- **Agent sees:** `/app/edge/edge.conf` (broken, the only graded artifact),
  `/app/edge/EDGE.md` (the complete spec), `/app/edge/payloads/` (console
  144 KB, shipments feed 445 KB, depots 2.4 KB, status 12 B), and a runnable
  four-case self-check under `/app/edge/checks/`.
- **Agent produces:** the repaired `edge.conf`.
- **Graded on:** a real nginx started over the agent's own file on a port chosen
  at verify time, asserting on what a client actually receives — as a direct
  caller, as a caller arriving through a proxy, and as an HTTP/1.0 caller.

---

## 2. The crux — four nginx defaults, none of them named

`nginx -t` passes, the edge starts, every request returns 200, and **the console
visibly compresses**, which is what makes a spot check confirm "compression works".

1. **`gzip_types` defaults to `text/html` ALONE** → every JSON feed goes out in
   full. Measured: console 260,013 → 1,576 bytes while the feed stayed 229,780
   with no `Content-Encoding`.
2. **`gzip_vary` defaults off** → compressed responses carry no
   `Vary: Accept-Encoding`, so a shared cache serves gzip to clients that cannot
   read it.
3. **`gzip_proxied` defaults to `off`** → nginx refuses to compress any response
   to a request carrying `Via`, i.e. anything arriving through a proxy.
4. **`gzip_http_version` defaults to `1.1`** → HTTP/1.0 callers are never
   compressed. Measured with the other three set: HTTP/1.1 gets 18,650 bytes,
   HTTP/1.0 gets 145,780.

### Invariants that keep it alive

1. **Grade by running the real tool.** No reference reimplementation to disagree
   with, so `qc_gate` B1 has nothing to bite; any config meeting the spec passes.
2. **The self-check is complete-looking and blind on every axis.** Four cases the
   agent can run, measured **green under all three wrong configurations**. It
   issues plain HTTP/1.1 direct requests only.
3. **Payload ground truth is pinned in `tests/`, never read from `/app`.**
   Otherwise "do not edit or pre-compress the payloads" is unenforceable.
4. **nginx is invoked by absolute path under a scrubbed env.**
5. **The spec states a universal over callers, never a client kind.** See §3.

---

## 3. Dead ends — nineteen pushes of one mistake

**Every axis in pushes 1–20 had the same shape: state a requirement → the agent
reads it → the agent implements it. The disclosure WAS the test.**

Two entirely different task designs died of this before the third:

- **Pushes 1–7, SQLite loyalty feed-sync.** `INSERT OR REPLACE` firing
  `ON DELETE CASCADE`; a no-op write bumping a trigger-maintained `sync_version`;
  a progressive tier clamp. Grader: *"the CLAIMS/spec was sufficiently precise
  that the bugs were deducible from the spec alone"* in effect — 5 of 6 trials
  solved.
- **Pushes 8–17, Python then SQLite index repair.** A shared-mutable-cache
  aliasing bug; commercial rounding vs `round()`'s half-to-even; unpadded shard
  ordering; a storage allowance. All solved. The SQLite-index version's analysis
  was blunt: **both agents ran `EXPLAIN QUERY PLAN` at step 2–3.** Plan-checking
  is reflexive for this model, so the three "independent" index traps collapsed
  into **one** axis — *does the agent inspect plans?* — and 4/5 solved.

**The most expensive single lesson, push 20 → 21.** Push 20 had `gzip_types`,
`gzip_vary`, `gzip_proxied` and cleared every gate to `trials`, then scored
**4/5 solved**. The per-trial table said why:

| trial | found `gzip_proxied`? | wrote a `Via` harness? | outcome |
|---|---|---|---|
| 4 of 5 | Yes | **Yes — custom proxy-traffic test** | PASS |
| 1 of 5 | Dismissed it | No | FAIL |

They built a `Via` harness because **`EDGE.md` told them that traffic existed**:
*"every regional dashboard reaches it through that region's shared caching
proxy."* That is the deciding case, written down. `deep_review` had flagged it
one gate earlier as an advisory — *"pass@5 spend will be near-binary on that
single knowledge point"* — and I let `trials` spend anyway.

---

## 4. What actually worked

**State the general rule; never the case that makes it bite.**

`repair-portal-dispatch`'s winning axis said *"pass every client field through"*
and never *"clients send underscore headers"*. The deciding case was a **member
of the disclosed set**, not a disclosed fact.

Push 21 did exactly two things:

1. **Deleted the traffic topology from the spec.** `EDGE.md` now states a
   universal — compression is required *"for every client it serves, not for a
   convenient sample of them"* — and names no client kind, no proxy, no HTTP
   version, no directive. Verified mechanically: `gzip_proxied`,
   `gzip_http_version`, `Via`, `HTTP/1.0`, `caching prox` appear **zero times**
   in every agent-visible file. Fair by construction: a universal over callers
   covers proxied and HTTP/1.0 callers.
2. **Added a fourth axis** (`gzip_http_version`) so the task was no longer
   near-binary on one directive.

Result: **4/5 solved → 0/5 solved** in one push.

---

## 5. Gate log

| Push | Gate | Result |
|---|---|---|
| 1–17 | `pass2` | **2/2 solved** ×15 across two abandoned designs |
| 18 | every upstream gate incl. `validation`, `similarity` | pass — nginx in the verifier works, and reusing nginx cleared the duplicate check |
| 18 | `pass2` | **2/2 solved** — agents probed headers with a *plain* request |
| 19 | `pass2`, `deep_review` | **pass** — first clearance with the intended mechanism |
| 19 | `ava_review` | **FAIL — 2 × `sound_verifier`** (see §7) |
| 20 | `ava_review`, `qc_gate`, `qc_eval`, `qc_exec`, `tier1` | all pass, first time |
| 20 | `deep_review` | **failure — platform fault**, see §8 |
| 20 | `trials` | **4/5 solved** |
| 21 (`ea31a64`) | every gate | pass → **`accepted`**, pass@5 **0/5** |

Never failed once: `changes` (static), `cosine_similarity`, `similarity`,
`validation`, `ratelimit`, `review` (rubric) — from the first nginx push onward.

---

## 6. Error → what to do

| Symptom | Do | Do NOT |
|---|---|---|
| pass@2 `2/2 solved` and your spec is precise | Ask whether the deciding **case** is written down, not just the rule. Delete the case; keep the rule as a universal | Reword the requirement. Nineteen pushes of rewording moved nothing |
| Agents converge on the same fix in ~4 min of 60 | The knowledge is in training data. Change the **kind** of axis, not the wording | Add another axis of the same kind |
| Several traps, still one effective axis | Check whether they share a single discovery step (`EXPLAIN QUERY PLAN`, "inspect headers"). If so the axis count is 1 | Trust the axis count |
| `deep_review` posts a difficulty **advisory** | Act on it *before* `trials` spends. It predicted the 4/5 result exactly | Let trials run and read it afterwards |
| A gate "fails" with 0s duration | Cancelled/superseded job, not a verdict | Diagnose the task |
| `deep_review` fails but its comment says PASS | Check the failing **step**. Ours died on "Post Automated Review comment" — a platform fault. Cycle the PR | Change the task |
| `cosine_similarity` sits >5 min on "Extract task fingerprint" | Wedged LLM call. `gh pr close && gh pr reopen` | Wait it out; ours hung 33 min |

---

## 7. Bugs I introduced myself

- **Verifier read payload ground truth from `/app`.** `instruction.md` forbids
  editing the payloads, but the tests compared the served body to the file on
  disk — so an edited payload became its own expected value and scored reward 1.
  Fixed by pinning SHA-256 + size in `tests/`. Proven: tampering went from a
  clean pass to **5 failed**.
- **nginx resolved via `PATH`.** A shim planted earlier in `PATH` could answer
  for the config. Fixed with `/usr/sbin/nginx` + scrubbed env + version banner.
  Proven: hostile shim + broken config still **4 failed**.
- **PR title/body left describing a superseded task**, twice, after redesigns.
  Reviewer-facing.
- **A measurement loop with broken quoting** reported `0 PASS / 0 FAIL` and I
  nearly recorded it as green. A self-check that reports nothing has crashed.

---

## 8. Process rules confirmed here

- **Probe the real tool before designing.** Every mechanism was confirmed against
  a live nginx first, and **one candidate was disproved and dropped**
  (`gzip_min_length`: an 8-byte payload is correctly left uncompressed, so a trap
  on it would have gated nothing).
- **Keep a preflight regression script and run it before every push.** After a
  fix for one gate, re-verify: oracle/nop, the full mutant table *including the
  near-miss that must still fail*, self-check blindness, every closed attack,
  README/`task.toml` claims, and whether anything **agent-visible** changed. Ours
  caught a drifted README test table that would have cost a cycle.
- **If nothing agent-visible changed, a pass@2 swing is variance, not
  regression.** Diff `instruction.md` + `environment/` to know which you have.
- **A `deep_review` job can fail *after* returning PASS** (comment-writing step).
  Re-trigger; do not edit the task.
- Never `git add -A` blind; one push per round; never push while `pass2`/`trials`
  is live; `.dockerignore` from commit 1.

---

## 9. Reusable checklist

- [ ] Probe every candidate mechanism against the real tool; drop the ones that
      turn out to be correct behaviour.
- [ ] For each axis ask: *is the deciding CASE written anywhere the agent reads?*
      State the rule as a universal; never enumerate the cases.
- [ ] Ask whether the axes share one discovery step. If so, you have one axis.
- [ ] Ship a complete-looking self-check and **measure** it green on every wrong
      solution.
- [ ] Pin ground truth in `tests/`; never read it back from agent-writable paths.
- [ ] Invoke external binaries by absolute path under a scrubbed environment.
- [ ] Perform every verifier attack yourself, before and after the fix.
- [ ] Act on `deep_review` advisories *before* `trials` spends.
- [ ] Run the preflight script before every push.

---

## 10. One paragraph

An nginx edge's compression is switched on with a single `gzip on;` and four of
nginx's own defaults silently prevent it from reaching the traffic that costs
money; the agent repairs the config and is graded by running a real nginx and
watching what a client receives. Nineteen pushes across three task designs all
scored `2/2 solved` for one reason: every axis stated a requirement the agent
could satisfy by reading it carefully — the disclosure was the test — and this
model is superb at spec-following and at code review. The fix was not a better
mechanism but a change in what the spec says: state the rule as a universal over
callers and delete every mention of the cases (proxied clients, HTTP/1.0
clients) that make it bite, exactly as `repair-portal-dispatch` said "pass every
client field through" and never "clients send underscore headers". That single
edit, plus a fourth default so the task was not binary on one directive, took
pass@5 from **4/5 solved to 0/5** in one push. The most expensive mistake was
letting `trials` spend on a design whose own `deep_review` advisory had already
predicted the 4/5 result.
