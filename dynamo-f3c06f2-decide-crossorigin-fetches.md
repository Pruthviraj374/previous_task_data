# dynamo-f3c06f2-decide-crossorigin-fetches

| | |
|---|---|
| **Outcome** | **ACCEPTED** — every gate green, PR #2 labeled `accepted` |
| **Repo** | `dynamo-f3c06f2-software-engineering`, PR #2 |
| **Category / sub** | Software Engineering / Web API and networking software |
| **Final commit** | `4fb8372` (2 pushes: `8b64115` initial, `4fb8372` the qc_gate fix) |
| **Headline** | `pass2` 0/2 genuine fails on the shipped design (both agents converged on the same simplified CORS reading); one `qc_gate` cycle on "Narrow / Hardcodable Held-Out Coverage"; accepted on the second push |

## 1. What the task asks

Rebuild a browser-side cross-origin (CORS) triage tool as `/app/decide.py`: replay a capture
of recorded fetches (`page_origin`, `request`, `preflight_response`, `response`) and emit, per
record, whether a preflight was sent, whether the fetch was `delivered` or hit a
`network_error`, and which response header names script could read. Graded against 9 captures
(1 shipped + 8 held-back), byte/field-exact, no tolerance. Governing authority is the real
WHATWG Fetch Standard, named normative in `instruction.md`; the traffic itself (origins,
tokens, endpoints) is entirely synthetic so nothing is look-up-able.

## 2. The crux, and the invariants that keep it alive

Thirteen independent CORS nuances the "common reading" gets wrong, all silent (never throw,
always produce a plausible verdict): wildcard access-control grants going inert under
credentials; request-header safelisting by *value* (length + byte-content), not just name;
preflight acceptance on the whole 2xx range, not only 200; byte-string (not case-folded,
not stripped) comparison of the origin/credentials grant; case-normalization limited to six
method names with everything else byte-compared as written; and safelisted response fields
being readable regardless of whether the response named them in `Access-Control-Expose-Headers`.

Invariant that must never break: the shipped 40-record capture must remain **inert** under
every one of the 20 catalogued wrong readings (13 reproduce it byte-for-byte, 7 are refuted by
it outright) — see `tools/calibrate.py`. The held-out captures (h01–h09) are what actually
discriminate; the shipped one is intentionally uninformative by design, stated as such in
`task.toml`'s `difficulty_explanation`.

## 3. Dead ends / what nearly happened

Nothing was redesigned — this is a single-crux CORS spec task, not a category pivot. The one
real near-miss: after `pass2` correctly showed 0/2 genuine fails (both agents implemented a
plausible-but-simplified CORS reading and missed all five nuance families cleanly, per
`deep_review`'s own approach-diff table), `qc_gate` still blocked on a coverage hole
`pass2`/`deep_review`/`ava_review` had no way to see, because none of them mutate the reference
mechanically.

## 4. What actually worked

**`qc_gate` "Narrow / Hardcodable Held-Out Coverage"** fired on one named mutation: deleting
`host = host.lower()` inside `origin_of()` still passed the full held-out suite (reward 1),
because no fixture exercised a same-origin fetch whose request-URL host differed in case from
`page_origin`. Per `previous-task-data.md`'s standing advice for this exact finding
(`replay-deposit-ledger` §4.1, `motion-register` §5), the fix was **not** to patch the one
named case — it was to build `tools/coverage_audit.py`: an AST-level mutation sweep (drop every
`.lower()`/`.strip()`/`.join()` call, shift every boundary constant by ±1, flip every
comparison operator, drop every boolean-op operand and frozenset member, delete every early-
return guard) replayed against every held-out fixture. Run cold, it found **22 survivors**, not
just the 1 QC named. Most were equivalent (documented in the tool's `EQUIVALENT` dict with the
reason — e.g. dropping a `.join()` on a guaranteed-single-element list is the identity); the
real gaps got new/broadened fixtures (`h09` new; `h03`, `h04`, `h06`, `h08` broadened) covering
explicit-port origins, MIME-essence whitespace edge cases, `set-cookie2`, mixed-case `HEAD`/
`OPTIONS`, and the exact preflight-status upper boundary. One push after building the audit
tool, `qc_gate` passed clean.

## 5. Gate-by-gate log

| Push | Commit | What it did | Result |
|---|---|---|---|
| 1 | `8b64115` | initial submission | static/rubric/validation ✅ · `pass2` **0/2 genuine** (both agents: same simplified CORS reading, `approach_validity` PASS, failures on exactly the 13 catalogued nuances) · `deep_review`/`ava_review`/`tier1` ✅ · **`qc_gate` ⛔ "Narrow / Hardcodable Held-Out Coverage"** (`host.lower()` in `origin_of()` uncaught) |
| 2 | `4fb8372` | built `tools/coverage_audit.py`, broadened h03/h04/h06/h08, added h09, refactored `origin_of()` (removed dead userinfo-stripping, now handles an explicit non-default port) | all gates ✅ · **`accepted`** |

## 6. Error → what to do, and what NOT to do

- **`qc_gate` "Narrow / Hardcodable Held-Out Coverage"** → do not patch the single named
  mutation; it recurs (confirmed independently at `replay-deposit-ledger` §4.1/§4.2 and
  `motion-register` §5/§6). Build a standing AST mutation-coverage tool and fix everything it
  reports in one pass. Confirmed a third time here.
- Do **not** assume `pass2`'s `approach_validity: PASS` + wide-margin fails (6–7 of 9 tests)
  means the design is done. It proves the *crux* is genuine; it says nothing about whether the
  *coverage* is narrow enough to hardcode past. Those are different gates for a reason.
- A mutation survivor is not automatically a bug — audit each one before adding a fixture.
  Two of the tool's own `EQUIVALENT` entries here were dead code paths (`.join()` on a
  guaranteed-singleton, `.strip()` on values never carrying whitespace), correctly left
  unfixtured rather than papered over with a pointless test.

## 7. Bugs introduced

None self-inflicted this task — the `origin_of()` refactor during the fix (dropping the
userinfo-splitting branch) was a simplification enabled by a TRACE.md guarantee that was
already true before the fix, not a new behavior change; `tools/build_traces.py`'s asserted
agreement between planted and reference verdicts caught anything that would have mattered.

## 8. Process rules learned the hard way

- Run `tools/coverage_audit.py` (or build it) **before the first push**, not in response to
  `qc_gate` — it would have caught this in local calibration, saving a full ~50 minute gate
  cycle. This is now standing advice in `verify/CLAUDE.md`'s closed-PR/process chain — do it by
  default on any task with a hand-written reference implementation and a fixed fixture set.
- Working-tree state can persist across sessions on a `dynamo-*` clone (uncommitted fix in
  progress); always run `git status`/`git diff` before assuming a repo is at the last-pushed
  commit.

## 9. Reusable checklist for the next task

- [ ] Before the first push: build (or reuse a template of) an AST-level mutation-coverage
      sweep over the reference, replayed against every fixture; fix every non-equivalent
      survivor.
- [ ] Document every accepted-as-equivalent mutation with a one-line reason, not silence.
- [ ] Keep the shipped/sample capture provably inert under every catalogued wrong reading
      (`tools/calibrate.py`-style table); let the held-out set carry all discrimination.
- [ ] Re-run the mutation sweep after *any* change to the reference, not just at design time.

## 10. One-paragraph version for future me

A 13-nuance CORS spec task cleared the difficulty bar cleanly on the first push (0/2 genuine,
wide-margin, `approach_validity` PASS) but still cost a second push to a `qc_gate` coverage
finding that a mutation sweep would have caught locally in seconds — build that tool before
pushing, not after being told to.
