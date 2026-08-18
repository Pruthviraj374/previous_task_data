# dynamo/filer-access-audit — accepted on the third push, and the axis I nearly cut carried the whole result

| | |
|---|---|
| **Outcome** | **ACCEPTED** — every check green, `accepted` label |
| **Repo** | `dynamo-831b96e-systems-infrastructure-and-operations`, branch `submission`, fork `Pruthviraj374` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-831b96e-systems-infrastructure-and-operations/pull/2 |
| **Category / sub** | Systems Infrastructure and Operations / Users Permission and Access control (pre-seeded) |
| **Benchmarked model** | reported as `Model A` (`task.toml` names Opus-4.8 / Terminus-2 — fixed dataset fields) |
| **Final commit** | `e01ba33` |
| **Headline** | **pass@2 = 0/2, pass@5 = 0/5, avg@5 = 0.000, 3 good valid fails, 2 in-progress timeouts.** `qc_gate`, `ava_review`, `deep_review` and `tier1` all passed **first time** |

Three pushes, three pipeline runs, zero redesigns. Both failures were prose-level, neither
touched the design. The design itself was assembled entirely out of this directory —
`reduce-palaeomag`'s method applied to a different standard — and the single most valuable
finding is in §4.2: **the axis I rated weakest and nearly cut before building is the one that
failed every trial.** That is now the third category in which that has happened.

---

## 1. What the task asks

A NAS filer is decommissioned. Its ACL state is gone; a per-tenant archive survived.

- **Agent sees:** `instruction.md`, `/app/data/FORMAT.md` (archive syntax + the statement that
  the filer implemented NFSv4.1 ACLs per RFC 8881 §6), and one archive at
  `/app/data/exports/HELIOS/` — `principals.txt` (7 users, 5 groups), `journal.txt` (23 records,
  17 objects), `requests.txt` (35 requests), and `report.json`, the decisions the filer returned.
- **Agent produces:** `/app/audit.py`, invoked
  `python3 /app/audit.py <export_dir> <out_json>`, plus its run over the shipped archive at
  `/app/output/report.json`.
- **Graded on:** the shipped archive (staged without its answer file) plus **seven held-out
  archives** in `tests/exports/`, all-or-nothing across 10 tests. 141 requests total.
- Decisions are the strings `ALLOW`/`DENY` — **categorical, so no tolerance exists anywhere in
  the task.** This is `lumenp` §6 / `reassemble-tap-sessions` §2 taken to its conclusion: if the
  graded quantity can be made non-numeric, the whole rounding/threshold class disappears and
  `difficulty_evidence` can never call a failure a formatting near-miss.

The journal replays `mkdir`/`create`/`setacl`/`chown`; creation derives an ACL from the parent
by inheritance; a request is decided by the ACL the object ended up with.

---

## 2. The crux, and the invariants that keep it alive

Five conditional clauses of **RFC 8881 §6**, all real and published, all decided by a
**structural property of the input** rather than by recalling a table, all normalised away by
the natural implementation.

| Axis | Rule | Natural mistake | Fires when |
|---|---|---|---|
| **A1** | §6.2.1 — a permission stops being considered once an ACE allows it, so a later DENY of it does not bite | group all DENYs ahead of all ALLOWs ("deny wins") | an ALLOW precedes a DENY for the same principal and bit |
| **A2** | the path is resolved from the export root, so every ancestor directory must grant traverse | evaluate the named object's ACL alone | an ancestor withholds or denies `x` |
| **A3** | §6.2.1.4.1 / §6.2.1.5 — `ACE4_IDENTIFIER_GROUP` decides whether a who value is a group; without it the value is a **user** | resolve the who value by name against users *and* groups | a name exists in both namespaces |
| **A4** | §6.4.3.1 — a file-inheritable but not directory-inheritable ACE MUST be inherit-only on a subdirectory it is inherited into | copy inheritance flags verbatim | a file-inherit-only ACE reaches a subdirectory that is a request target |
| **A5** | §6.2.1.5.1 — `EVERYONE@` includes the owner and owning group; it is **not** the POSIX "other" class | map `EVERYONE@` onto "other" | an `EVERYONE@` ACE is decisive for an owner or owning-group member |

**Invariants that must never break** (all asserted by `tools/calibrate.py`, all measured before
the first push):

1. **HELIOS is bit-inert under every one of the five wrong readings** — 0 of 35 decisions change.
   Not assumed; each wrong reading is an actual mutant and the diff count is printed.
2. **HELIOS pins every machinery step it is supposed to teach**, each with a divergence number:
   no inheritance 15, inherit-only treated as effective 3, no-propagate ignored 2, `GROUP@` read
   as a named group 2, group membership ignored 7, every ACE inherited 2, `OWNER@` frozen at
   creation 2. Without these the withheld rules would be underdetermined and B5 would have
   blocked — `retired-normalizer` §4.1 applied preventively, exactly as `reduce-palaeomag` §4.4
   prescribes.
3. **Every HELIOS ACL lists its DENY entries before its ALLOW entries** (A1 inert), **no HELIOS
   DENY covers `x`** (A2 inert), **no name is in both namespaces** (A3 inert), **no request asks
   for `w`/`a` on a directory under the file-inherit-only ACE** (A4 inert), and **every
   `EVERYONE@` mask is a subset of the `GROUP@` mask that precedes it, with no `D::EVERYONE@` at
   all** (A5 inert). The last one is the general form worth stealing: *`EVERYONE@` can never
   decide anything for an owner or owning-group member if an earlier `OWNER@`/`GROUP@` entry
   already grants a superset.* `sample_invariants()` re-checks all of these on every run, so a
   later data edit cannot quietly un-inert the sample.
4. **Constructs the RFC leaves under-specified are refused in every archive** — no-propagate
   without directory-inherit, inherit-only with no inheritance flag. See §7.2.
5. **Nothing in the agent-visible surface names ACE order, traversal, namespace collisions, the
   inherit-only fixup, or `EVERYONE@`'s scope.** Grepped before every push.

**The fairness half.** `FORMAT.md` names RFC 8881 §6 as the model and **stops at the locator** —
`rebuild-readout-builder` §3.3. It specifies the container exhaustively (every flag letter,
every permission letter, every record type) and states the facts that remove ambiguity without
disclosing anything: automatic inheritance was never used, no POSIX mode/sticky bits, no
AUDIT/ALARM ACEs, user and group names come from separate namespaces. `allow_internet = true`,
so the RFC is reachable. Every graded rule is derivable; none is stated.

---

## 3. Dead ends

**There were none at the design stage.** Like `reduce-palaeomag`, every dead end had already
been paid for by an earlier file, and the candidates were rejected on paper before any code:

| Rejected candidate | Rejected because | Corpus source |
|---|---|---|
| POSIX.1e ACLs (mask semantics, default ACLs, umask suppression) | **replayable** — the agent has root and open internet, can `apt-get install acl` and let the kernel be the oracle. A crux the environment can answer for you is not a crux | new finding, §6 |
| §6.2.1.3.2 `ACE4_DELETE` vs `ACE4_DELETE_CHILD` ("allow unlink if *either* is permitted, **even if the other explicitly denies**") | the most counterintuitive rule in the whole RFC and it hurt to drop, but it is a **SHOULD** with a sticky-bit escape clause and an under-specified fallback → defensible either way → ambiguity | rubric `unambiguous`; `sweep-replay` §3 (single published definition) |
| sudoers last-match-wins, Kubernetes RBAC, AWS IAM evaluation | memorised — the model recalls published conventions essentially perfectly | `motion-register` §3, `experiment-analysis-frame` §3.3 |
| Linux capability transition formula on execve | it is a *table*, i.e. recall, not a property of the input to be noticed | `reduce-palaeomag` §4.1 |
| Grading the reconstructed ACL text | §6.4.3.1 permits a server to split one inheritable-and-effective ACE into two, so the ACL *representation* is genuinely non-unique while the *decisions* are not | `reduce-palaeomag` invariant 5 — grade only the quantity invariant to the convention |

**The one thing I got wrong** was not a dead end but a misjudgement of ranking, corrected only
by the trial tables. See §4.2.

---

## 4. What worked

### 4.1 Unreplayable by construction

The single design constraint that shaped everything: **the agent must not be able to obtain
ground truth by running something.** POSIX ACLs fail this — the kernel is a free oracle. NFSv4.1
ACLs cannot be materialised on ext4/overlayfs without an NFSv4 server, so there is no local
authority; the RFC is the only source, and reading it correctly is the task. Add this question
to the design checklist: *can the environment answer this for the agent?*

### 4.2 Keep the axis you think is weakest — third confirmation, and the strongest yet

I rated the five axes at design time. **A2 (ancestor traverse) I rated weakest** — a famous rule,
"everyone knows you need `+x` on the directory", surely the model implements it. I kept it only
because `reduce-palaeomag` §4.2 and `replay-strata-plans` §4.3 both say to. The trial tables:

- **A2 failed all 5 trials.** `test_boreal` and `test_fulcrum` are the only two tests that fail
  **uniformly across every trial**. The grader: *"No trial implemented an equivalent function.
  All five wrong-direction errors in BOREAL (b01/b06/b07) and FULCRUM (f03/f10) trace to this
  single missing step."*
- **A4 failed 2 trials**, **A1 failed 1**.
- **A3 and A5 never gated at all.** `test_ember` (A5's isolating fixture) passed in **all five**
  trials; `test_cinder` (A3's) passed in four of five, and the fifth failed it for an unrelated
  algorithm bug.

So the two axes I considered cleverest — the ones chosen precisely because they are *noticed
rather than recalled* — discriminated nothing, and the plainest, most famous rule in the set
carried the entire result. **The lesson is not "prefer famous rules".** It is that a designer's
ranking of which rule the model will miss is close to worthless, and the only defence is to ship
several independent axes and let the trials decide. Had I cut A2 as redundant, this task would
have gone to `trials` resting on A1 and A4 — a 3/5 at best.

Corollary worth stating plainly: **"the model surely knows this" is not evidence it will
implement it.** Every failing agent *knew* about traverse permission; none wrote the loop,
because nothing in its only validation set ever punished the omission.

### 4.3 A complete-looking self-check that is silent on the trap

`report.json` lets an agent validate end to end and reach 35/35 while wrong on all five axes.
The graders described the consequence unprompted:

> "the HELIOS validation archive — the only ground-truth the agents had access to — was
> deliberately constructed so that every traversed ancestor directory grants EXECUTE to all
> relevant users. This made the omission invisible during self-testing. After achieving a clean
> HELIOS diff, both agents declared success without seeking additional test coverage."

and

> "This convergence on both the approach and the single-dataset validation strategy suggests a
> shared training-data prior rather than first-principles derivation."

Three of five trials produced a **fully working evaluator that matched HELIOS 35/35** and shipped
without the traverse loop. `contact-export` §9 items 1–2 and `reduce-palaeomag` §4.3, reproduced
exactly. The amplifier is the sample, not the spec.

The `merge-lora` §3.1 exposure (a graded artifact whose answer ships under `/app`) is defused by
grading a **program** against archives whose answers exist nowhere in the image. `ava_review`
noted the residual path and scored it harmless itself: *"an agent could read the shipped
report.json and hard-code those 35 answers… Because reward is all-or-nothing across 10 tests and
the 7 held-out archives are absent from the agent image, this earns at most 2/10 and never
reward=1 — coverage of unseen tenants closes it. No hardening required."*

### 4.4 Ground truth that is computed, never stored

There is no expected-value file anywhere, at any point. `tests/_reference.py` computes the
expected decisions **inside the pytest process** at verify time. This deletes the entire class of
failure that cost `cron-window-counts` two `adversarial_review` rounds and two `ava_review`
blocks (§5.4/§5.5 there) — "the solver shares a filesystem with the answers" — because there is
nothing on the filesystem to share. What remains is one exploit path: importing `_reference.py`
itself. That is closed by chmod-sealing `/tests` and dropping to `nobody`, and **the exploit was
written and run** (§4.6).

### 4.5 Two independently-written implementations

`solution/audit.py` uses letter sets and subtracts from a `remaining` set; `tests/_reference.py`
uses integer RFC 8881 bitmasks and accumulates `granted`. They agree on all 141 requests.
`experiment-analysis-frame` §7 warns that `oracle = 1.000` is nearly vacuous when the two are the
same code. The eval cited this unprompted under `reviewable`: *"Two independently-formulated
implementations agree."*

Second return, unplanned: I hand-derived all 35 HELIOS decisions from the RFC **before** running
the oracle, and the two agreed on 34. The one disagreement was a real bug of mine (§7.1).

### 4.6 Every wrong reading run through the real verifier, not just the model

`tools/mutants.py` builds each wrong reading by substitution and **asserts the substitution
matched exactly once** — `experiment-analysis-frame` §7's silent-no-op trap. All five were then
run through `harbor run --agent oracle`:

| Wrong reading | Reward | Tests failed | HELIOS |
|---|---|---|---|
| A1 deny-wins | 0.000 | `test_atlas`, `test_fulcrum`, `test_granite` | passes |
| A2 target-only | 0.000 | `test_boreal`, `test_fulcrum` | passes |
| A3 who resolved by name | 0.000 | `test_cinder`, `test_granite` | passes |
| A4 flags verbatim | 0.000 | `test_deltav`, `test_granite` | passes |
| A5 `EVERYONE@` as "other" | 0.000 | `test_boreal`, `test_deltav`, `test_ember`, `test_fulcrum` | passes |

Plus an **answer-key exploit** — glob `/tests/**/*.json`, then `sys.path.insert("/tests")` and
import `_reference` — which scored **0.000** with `ModuleNotFoundError` on every archive. `cron`
§7's methodology: reproduce the exploit as a local mutant rather than learn it from a gate three
hours later. Note the seal worked in local Docker on macOS because the fixture tree is
container-resident, not a host bind mount (`rebuild-plate-rasterizer` §4.3's caveat did not bite).

### 4.7 Fixtures that combine, not only isolate

Seven held-out archives: one isolating each axis (ATLAS/BOREAL/CINDER/DELTAV/EMBER) and two
combining (FULCRUM = A1+A2+A5, GRANITE = A1+A3+A4) — `lumenp` §4. FULCRUM is one of the two tests
that failed in **every** trial. Isolating fixtures alone would still have caught A2, but the
combining ones are what make a partially-fixed submission fail too.

---

## 5. Gate-by-gate log

### Push 1 — `8e08c7a`

| Gate | Verdict |
|---|---|
| `changes`, `cosine_similarity` | pass |
| `similarity` (duplicate) | **UNIQUE** — instruction 0.734, verifier 0.811, task fingerprint **0.842** against a 0.9 block threshold |
| static (`review`) | **FAIL — 1 blocking** (§5.1) |
| everything downstream | skipped |

### 5.1 Static: "Dockerfile does not COPY solution/ or tests/" — on a **comment**

> `FAIL submission/task/environment/Dockerfile: contains reference to tests/test.sh (Dockerfiles
> must not COPY solution or test files)`

The Dockerfile COPYs only `data`. The offending line was the comment
`# Verifier dependencies are baked in; tests/test.sh installs nothing.` **The check is a literal
string scan over the file, not a parse of COPY directives.** I had already verified the built
image was clean (`find / -name 'test*.sh' -o -name 'audit.py'` → nothing but `/app/data`), which
is exactly why the failure was confusing for a moment.

Fixed in `27dc5f6` by rewording the comment. Cost: one full cycle for a comment. **Never write
`tests/` or `solution/` anywhere in a Dockerfile, including comments.**

### Push 2 — `27dc5f6`

| Gate | Verdict |
|---|---|
| static (`review`) | **pass, all 25 checks** |
| `review` (rubric eval) | **FAIL — 30 of 31 PASS, one failure** (§5.2) |
| everything downstream | skipped |

### 5.2 `difficulty_explanation_quality` — missing provenance and audience

The only failing criterion, and the grader called it borderline itself:

> "The field is an excellent account of *why the problem is hard*… but it omits two elements the
> criterion explicitly requires. It never states the **data provenance** — the archives are
> clearly synthetic/hand-authored… yet the explanation reads as if the archives are real
> recovered artifacts. It also never names **who in the real world** would solve this and why."

> "This FAIL is borderline: the difficulty content itself is strong… The concrete, defensible fix
> is small (two added sentences), which is why it is graded FAIL rather than treated as fatal."

`reduce-palaeomag` §5.2 hit the same criterion as a *note* and fixed it pre-emptively; here it
was a hard FAIL. **`difficulty_explanation` must contain, explicitly: (a) the data is synthetic
and how it was constructed, (b) which profession does this work and why it matters.** Explaining
the trap brilliantly does not satisfy either. Fixed in `e01ba33`, mirrored into the README.

Two notes the eval raised that I deliberately did **not** act on, both correct calls:

- `[task].description` is not in the Harbor `[task]` schema the grader was given; it graded PASS
  but flagged that a reviewer should confirm it. **It ships in this repo's own scaffold** with the
  comment "one-line summary of the task", and doc `20` lists it as a field Dynamo adds. Removing
  it would contradict the scaffold. Left alone; accepted.
- `task_readme` graded **N/A** — "No development README present" — because the rubric looks for
  `task/README.md` while `readme-rule.md` puts the reviewer-facing README at the repo root. N/A is
  not a failure and every accepted task in this corpus does it the same way. Left alone; accepted.

### Push 3 — `e01ba33`, everything green

| Gate | Verdict |
|---|---|
| static | pass |
| `review` (rubric eval) | **PASS — all criteria, zero failures** |
| `similarity` / `cosine_similarity` / `ratelimit` | pass |
| `validation` | docker ✅ oracle ✅ nop ✅ |
| **`pass2`** | **PASS — 0/2 solved, 2 valid fails**, identical root cause. Ran **49m34s** |
| `deep_review` | **PASS**, no blocking issues, 3 advisory notes |
| **`ava_review`** | **PASS, first time** — no blocking findings |
| `tier1`, `qc_eval`, `qc_exec`, **`qc_gate`** | **PASS, first time** |
| `pass2_suggestion` | **skipping** (no difficulty suggestion needed) |
| **`trials`** | **pass@5 0/5, avg@5 = 0.000**, 3 good valid fails, 2 in-progress timeouts |
| `gate` | pass → **`accepted`** |

`qc_gate` clearing first time is the payoff from §2's assertions: four rounds on
`experiment-analysis-frame`, three on `retired-normalizer`, zero here and zero on
`reduce-palaeomag`. `ava_review` passing first time is new — it blocked twice on `cron`, three
times on `contact-export`, once on `merge-lora` and `reduce-palaeomag`. The difference is §4.4:
with no answer file on disk there is almost no verifier-soundness surface to attack.

### 5.3 `deep_review` advisories (none blocking, none acted on)

1. `instruction.md`'s "Do not modify anything under `/app/data`" is not asserted. Judged
   immaterial by the reviewer itself: the held-out archives live in the sealed verifier image and
   `EXPECTED["HELIOS"]` is recomputed from the current inputs, so tampering cannot buy a pass.
2. The HELIOS hard-code path, bounded at 2/10 (quoted in §4.3).
3. `pytest` in the shared image; `no_solution_only_deps_in_agent_image` still passes because it
   does not telegraph a stdlib-only approach.

### 5.4 pass@5 detail

| Trial | Reward | near_miss | low_timeout | Root cause |
|---|---|---|---|---|
| `task__XjxHzpt` | 0.0 | FAIL (is a near-miss) | PASS | A2 only — matched HELIOS 35/35, shipped |
| `task__NdGdEBy` | 0.0 | FAIL | PASS | A2 only |
| `task__FsCfRvv` | 0.0 | FAIL | PASS | A2 only |
| `task__sXKt9cY` | 0.0 | FAIL | FAIL | A2 + A4; had identified its own h20 bug when the 3600 s cap hit |
| `task__Fu4gigx` | 0.0 | PASS (wide miss) | FAIL | A2 + A4 + A1 (`issubset` on a single ACE instead of accumulation) |

All five: `task_specification` PASS, `reward_hacking` PASS, `difficulty_crux` PASS, `refusals`
PASS, **`approach_validity` PASS**. The two `low_timeout` FAILs are the 2 in-progress timeouts;
they did not cost acceptance because 3 good valid fails already met the bar, but see §8.

---

## 6. Error → what to do, and what NOT to do

| Symptom | Do | Do **not** |
|---|---|---|
| Static check "Dockerfile does not COPY solution/ or tests/" while the Dockerfile plainly COPYs neither | Grep the Dockerfile for the literal strings `tests/` and `solution/` — **comments count**. Reword | Do not go looking for a real COPY, and do not conclude the check is broken. Verifying the built image is clean does not clear it |
| `difficulty_explanation_quality` FAIL | Add one sentence stating the data is synthetic and how it was built, and one naming the profession that does this work. Mirror both into the README | Do not answer it with more detail about the trap — depth of trap analysis is not what the criterion measures |
| Choosing a real convention as the crux | Ask first whether **the environment can answer it for the agent**. POSIX ACLs are one `apt-get install acl` from a kernel oracle; NFSv4 ACLs cannot be materialised without a server | Do not assume "no network answer exists" is the same as "no local oracle exists" |
| A candidate rule is a **SHOULD** with escape clauses (e.g. §6.2.1.3.2 delete-vs-delete-child) | Drop it, however delicious. Or confine the data so the under-specified branch is never reached, and assert that | Do not grade a rule two competent implementers could read differently — that is ambiguity, not difficulty |
| Your reconstruction has a representation the standard leaves free (ACE splitting, ordering of derived entries) | Grade only the **decisions**, which are invariant to it | Do not grade the reconstructed artifact text and then argue the standard permits only your form |
| Ranking your axes by "which will the model miss" | Ship them all and let `trials` rank them. Mine was inverted: the axis I called weakest failed 5/5, the two I called cleverest failed 0/5 | **Do not cut an axis because it looks too well known.** Third confirmation, after `reduce-palaeomag` §4.2 and `replay-strata-plans` §4.3 |
| Wondering whether a famous rule is "too easy" to be a crux | Ask instead whether the sample ever **punishes omitting it**. Every failing agent knew about traverse permission; none wrote the loop | Do not equate the model knowing a rule with the model implementing it |
| Deciding how to grade a quantity | Ask whether it can be made **categorical**. `ALLOW`/`DENY` has no tolerance, no rounding, no near-miss band | Do not reach for a tolerance until you have ruled out a non-numeric encoding (`lumenp` §6 generalised) |
| Verifier hardening for a "run the agent's program" task | Compute expected values **in-process** and never write them to disk; seal `/tests`; drop to `nobody`. Then write the import-the-reference exploit and confirm 0.000 | Do not rely on staging alone — the reference module is itself an answer key |

---

## 7. Bugs I introduced myself

1. **A missing `g` flag turned a group entry into a phantom user.** `A:fdi:imaging@corp.example:rt`
   should have been `A:fdig:…`. Without the flag it names a *user* called `imaging`, which does not
   exist, so the entry matched nobody. Caught because I had hand-derived all 35 decisions from the
   RFC before running the oracle and one disagreed. **My own A3 trap caught me while I was building
   it** — which is the best possible evidence the axis is fair, and an argument for hand-deriving
   the sample rather than trusting the reference you just wrote.
2. **`f` + `n` without `d` is a contradiction and I shipped it into a fixture.** §6.4.3.1 says a
   file-inherit-only ACE inherited into a directory MUST become inherit-only; NO_PROPAGATE says the
   inherited copy loses its inheritance flags. Together they specify an entry that is inherit-only
   with nothing to inherit to — which §6.2.1.4.1 says a server SHOULD reject. Removed, and
   `calibrate.py` now **refuses the combination in every archive** so it cannot come back.
   *Generalisable: when composing flag semantics from a standard, enumerate the combinations and
   check each is actually defined — not just the ones your data happens to use.*
3. **Ran `harbor run -p .` from the repo root instead of `task/`.** It produced a `jobs/` directory
   and a 0.000 reward that looked like a failing probe. Always `cd task` first; check which
   directory the run wrote to before believing a reward.
4. **`task.toml` claimed 14 tests when there are 10.** Caught by counting `def test_` before the
   first push. `sweep-replay` §6 — the `[metadata]` prose restates the design independently of the
   README and drifts on its own.

---

## 8. Process rules

- **Never push while a check is pending.** Verified with `gh pr checks 2 | grep -c pending` before
  every push, `|| true` on the grep (`reduce-palaeomag` §7.3 — `grep -c` exits 1 on zero matches
  and breaks `&&` chains).
- **Never `git add -A`.** `task/jobs/` is Harbor output; `task/.gitignore` carries `jobs/` and
  paths were staged explicitly (39 files, counted).
- **Set the commit identity at clone time** from `gh api user`.
- **A long `pass2` is not a stall.** Mine ran **49m34s** against a corpus expectation of 11–12 min.
  The corpus timings came from tasks where agents quit early — which is what *solved* looks like. A
  slow `pass2` is weakly good news.
- **2 of 5 trials hit in-progress timeouts at the 3600 s cap.** They did not cost acceptance
  (3 good valid fails cleared the bar) and 3600 s is the pipeline's hard ceiling, so the lever
  cannot be pulled again. Worth knowing that a task of this size runs agents right up to the cap.
- **Another contributor's PR sat open on the same repo** (`#1`, "Multi-role access control — PAM,
  sudoers, ACLs, and capabilities"). Repos are shared across attempters and the pre-seeded
  sub-category is the same for everyone working it, so **check the repo's open PRs before choosing
  a crux**. Mine stayed disjoint by construction — NFSv4.1 server-side evaluation, with POSIX mode
  bits, sticky bit, umask and sudo explicitly stated as not in use — but that was luck, not
  process, since I only noticed PR #1 after opening mine.
- **`similarity` returned UNIQUE at fingerprint 0.842 against a 0.9 threshold.** Comfortable but
  the closest margin recorded in this corpus. Worth watching if another task reuses the
  "reconstruct a retired system's outputs from an archive plus one worked example" shape — it is
  now used by a large fraction of these files, and the fingerprint is drifting up.
- **Timings:** whole run ≈ 3 h. `review` (rubric) 3 min, `validation` 47 s, `pass2` 50 min,
  `deep_review` 4 min, `ava_review` 8 min, `qc_eval` 19 min, `qc_exec` 5 min, `trials` the rest.

---

## 9. Reusable checklist

Design:
- [ ] Is the deciding rule **real, external, published**, with a **single** definition (no SHOULDs
      with escape clauses)?
- [ ] **Can the environment answer it for the agent?** Kernel, library, or installable tool → reject.
- [ ] Is it **conditional**, firing only on inputs the sample does not contain?
- [ ] Can the graded quantity be made **categorical**? If so, every tolerance question vanishes.
- [ ] Are there **several independent** axes? Ship them all — your ranking of which will fire is
      probably wrong.
- [ ] Does the standard leave any **representation** free? Grade only what is invariant to it.
- [ ] Check the repo's **other open PRs** before settling on a crux.

Data:
- [ ] Sample **bit-inert** under every wrong reading — asserted with real mutants and printed counts.
- [ ] Sample **pins** every machinery step — asserted, with a divergence number each.
- [ ] The inertness invariants themselves re-checked programmatically, so a later data edit cannot
      silently break them.
- [ ] Flag/enum **combinations** enumerated and each confirmed defined by the standard.
- [ ] Fixtures that **combine** axes, not only isolate them.
- [ ] Hand-derive the sample's expected values from the standard **before** running your own oracle.

Verifier:
- [ ] Expected values computed **in-process**, never written to disk.
- [ ] `/tests` sealed, graded program dropped to `nobody`, output read `O_NOFOLLOW`.
- [ ] The import-the-reference exploit actually **written and run** → 0.000.
- [ ] Reference written from a **different formulation** than the oracle; agreement measured.
- [ ] Types checked explicitly (`True == 1` in Python).

Before every push:
- [ ] `gh pr checks N | grep -c pending || true` → 0.
- [ ] Dockerfile contains the strings `tests/`/`solution/` **nowhere, comments included**.
- [ ] `difficulty_explanation` states data provenance **and** the real-world audience.
- [ ] Oracle 1.0, nop 0.0, calibration harness green.
- [ ] Crux vocabulary absent from the agent-visible surface.
- [ ] Root `README.md` re-read against the **complete** diff; test-name list diffed both ways.
- [ ] No AI attribution in any commit message or file.

---

## 10. One-paragraph version for future me

Accepted in three pushes with **pass@5 = 0/5, avg@5 = 0.000**, and with `qc_gate`, `ava_review`,
`deep_review` and `tier1` all clearing first time — the cleanest gate run in this corpus so far.
The design was `reduce-palaeomag`'s method transplanted onto RFC 8881 §6: put the machinery where
the shipped archive pins it, put the deciding rules in a real published standard, and construct
the sample so every wrong reading reproduces it bit for bit. Two things generalise beyond the
domain. First, **choose a standard the environment cannot execute for the agent** — POSIX ACLs
were rejected because the agent has root and could let the kernel be its oracle, while NFSv4.1
ACLs have no local authority at all. Second, and more valuable: **I ranked my five axes and the
ranking was inverted.** The axis I rated weakest and nearly cut — "every ancestor directory must
grant traverse", a rule every engineer knows — failed all five trials and was the sole cause in
three of them, while the two axes chosen precisely because they were *noticed rather than
recalled* never gated at all. Three of five agents built a fully working evaluator, matched the
shipped archive 35/35, and shipped without the traverse loop. Knowing a rule and implementing it
are different things, and nothing in a sample that never punishes an omission will tell the model
which it did. Both gate failures were prose, not design: a Dockerfile **comment** containing the
string `tests/test.sh` tripped the build-context scan, and `difficulty_explanation` needed an
explicit sentence of data provenance and one naming the profession — neither of which the quality
of the trap analysis substitutes for.
