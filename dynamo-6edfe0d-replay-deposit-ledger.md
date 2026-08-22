# dynamo/replay-deposit-ledger — rebuilding a deposit gateway's ledger from an HFS Plus volume's journals

**Systems Infrastructure and Operations / Storage and filesystem administration.**
Accepted on push 18 (`9b50941`), every check green, `accepted` label.
**pass@5 0/5 — 5 good-valid-fail, avg@5 = 0.000.** pass@2 returned 0/2 on twelve
consecutive runs.

---

## 1. The task

A university library is shutting down the deposit gateway that stood in front of its HOLLIS
preservation volume, an HFS Plus volume. The gateway took each deposit — a new file, a new
folder, a move, a removal — decided whether the volume would accept it, and wrote the outcome
to a ledger. The gateway is gone; the journals and the ledgers survived, and the ledgers are
what the provenance records cite. The agent writes `/app/gateway.py`, invoked as
`python3 /app/gateway.py <journal> <ledger>`, which replays one journal and writes the ledger
the gateway wrote for it, and leaves its run over the shipped journal at
`/app/output/HOLLIS.ledger`.

`/app/data/GATEWAY.md` specifies both file formats, the seven outcome codes, the object
numbering and the order in which each record is tested. It leaves name storage and name
comparison to the volume format itself, naming Apple Technical Note TN1150 as the authority
and saying it does not restate them.

Grading is exact string equality over categorical outcome codes and hex-encoded names, so
there is no tolerance anywhere and no rounding or formatting near-miss is possible.

---

## 2. The crux, and the invariants that hold it up

Two rules, both real, both conditional, both left to TN1150:

- **The stored form.** HFS Plus stores names fully decomposed and in canonical order,
  *except* code points in U+2000–U+2FFF, U+F900–U+FAFF and U+2F800–U+2FAFF — the singletons
  legacy Mac encodings round-trip through. `unicodedata.normalize("NFD", name)` decomposes
  them anyway, so a compatibility ideograph and its unified counterpart collapse onto one
  another and the accept/refuse decisions invert.
- **The comparison.** The case-insensitive comparison folds through `gLowerCaseTable`, in
  which sixteen code points map to zero and are skipped entirely: U+200C–U+200F,
  U+202A–U+202E, U+206A–U+206F and U+FEFF. Two names differing only by a zero-width joiner
  are the same name to the volume, and different names to any ordinary comparison.

Both interact with the *disclosed* 255 UTF-16 code-unit key limit, because it is the stored
form that has to fit.

Invariants that make it work:

1. **The shipped archive is bit-identical under every wrong reading** of either rule and of
   the key-length unit. An implementation can reproduce `HOLLIS.ledger` line for line and be
   wrong throughout. `tools/calibrate.py` asserts this, with a divergence count per reading.
2. **The archive teaches the wrong generalisation on purpose.** It uses U+200B, U+00AD and
   U+2060 — invisible but *not* skipped — and characters from the excluded blocks that have
   nothing to decompose. So the blocks are present and inert, which is what makes an agent
   confident rather than merely uninformed (`rebuild-plate-rasterizer` §4.2 applied literally).
3. **One graded journal exists nowhere on disk.** `_reference.synthesise()` builds 88 records
   at verify time from a self-contained PRNG, so no amount of guessing at the fixture set
   reaches reward 1.
4. **Single reading only.** The character repertoire is restricted to code points where the
   tables printed in TN1150 and modern Unicode agree, checked against `tools/tn1150.json`
   parsed from the note itself. This is what killed U+212B and U+2126 as trap characters —
   see §3.
5. **No local oracle.** HFS Plus name semantics cannot be materialised on Linux: `mount`
   needs privileges a container lacks, and the kernel's `hfsplus` driver does not implement
   Apple's normalisation. Verified `iconv` has no `UTF-8-MAC` on the base image.

---

## 3. Dead ends

**U+212B ANGSTROM SIGN and U+2126 OHM SIGN as the trap characters.** The most natural,
most readable choice — Å-the-unit versus Å-the-letter — and it had to go. `str.lower()`
maps U+212B → U+00E5 and U+2126 → U+03C9, while TN1150's `gLowerCaseTable` maps both to
themselves. So "case-insensitive" would have had two defensible readings, and an agent using
`.lower()` would fail for a reason the note does not support. Caught at design time by
computing the fold table from the published source rather than assuming. Replaced with
U+2329/U+232A, U+2260, the U+F900 block and the U+2F800 block, where table and `.lower()`
agree. **Check the fold, not just the decomposition, before choosing a trap character.**

**Nudging the agent toward TN1150.** `ava_review` advised adding "a one-line nudge that the
stored-form/comparison rules *require* consulting the cited TN1150", since both pass@2 agents
inferred the rules from the sample instead. Declined deliberately: the deferral is already
stated outright in `GATEWAY.md`, so a nudge adds emphasis, not information — and emphasis is
the difficulty. `replay-strata-plans` §3.2 records the same move swinging a task from 0/2 to
2/2 on register alone. The advisory itself granted the task was fair as written. Decision
recorded in the README so a reviewer sees judgement rather than oversight.

**Believing a mutant that scores 0.000.** The first `third-party-import` mutant was a stub
that wrote an empty ledger. It scored 0.000 and proved nothing — it would have scored 0.000
whether or not the import screen worked. A mutant testing an *enforcement* must be an
otherwise-correct solver that differs only by crossing the line.

**A cross-implementation check that only compares half the output.** The first fuzz compared
`stored_form` across all three implementations and passed 69,888 strings. It never compared
the comparison key or the key length, which is exactly how the final-sigma divergence reached
`qc_gate` instead of me. Compare *every* graded quantity.

---

## 4. What worked

### 4.1 The coverage audit — the thing that ended the C3 loop

`qc_gate` raised "Narrow / Hardcodable Held-Out Coverage" three times. Every instance was the
same shape: a rule that was **implemented and documented but not graded**, because no fixture
made the two readings diverge. Patching the named case each round is a loop; the exit is
`tools/coverage_audit.py`, which replays every journal under each single-decision mutation and
reports any that no journal distinguishes. It builds no image, so it runs in seconds and can
be exhaustive where the real-verifier sweep must be selective.

It found, unprompted, two gaps no gate had reported: **no fixture used Hangul at all** (the
solution's arithmetic jamo branch was never exercised), and two refusal-order pairs.

**Build this on the next task before the first push, not after the second block.**

### 4.2 Fixtures for the *order* of checks, not just the rules

The audit's first version covered naming rules only. `qc_gate` then found that swapping
`create`'s `exists` check ahead of `toolong` still scored reward=1, because no record failed
both ways at once. The decision space is larger than the rule list: ordering pairs, where ids
start, whether they are reused, the rename self-exclusion. LODESTAR supplies records that fail
two ways simultaneously — a name at once over the key limit and a duplicate (skipped code
points do not count in the comparison but *are* counted in the length), and a rename at once a
loop and too long.

### 4.3 Recognising an equivalent mutation instead of papering over it

"Test `notdir` before `noent`" showed as uncaught. It is *provably equivalent*: `notdir` is
only reachable when the parent exists, so the swap cannot change an outcome. It was removed
from the audit list with a comment, not given a fixture that would have tested nothing.
Separately, "ids are reused after a delete" looked uncaught until I noticed **my own mutation
never freed an id**; once fixed, five journals already caught it. Analyse every survivor
(`audit-build-context` §4.3) — some are equivalent, some are broken probes, and only the rest
are gaps.

### 4.4 Three independent implementations, cross-checked on every graded quantity

`tools/hfsspec.py` (generator), `task/solution/gateway.py` (expands the character database by
hand, bubble-sorts the reorder) and `task/tests/_reference.py` (normalises the runs between
left-alone code points, sorts by combining class, takes length from a UTF-16 encode). They
agree on 168,400 adversarial strings across stored form, comparison key **and** key length.
Two real divergences were found this way or by QC, both of which the oracle got right and the
reference got wrong — see §5.

### 4.5 Fixtures asserted at generation time

`Builder` in `tools/genfixtures.py` replays the journal as it is built, assigns ids the way the
gateway does, and asserts the outcome the author intended for every record. A fixture that
stops testing what it was written to test fails at generation rather than silently becoming
filler. This caught several id-prediction errors immediately; an earlier hand-numbered draft
had a whole journal's CJK half silently dead as `noent`.

### 4.6 Verifier hardening, each step proven by performing the attack

Everything below was measured in the built image, both sides, never assumed:

| Route | Closed by | Proven by |
|---|---|---|
| import the reference from `/tests` | seal `chmod 0700` + drop to `nobody` | `_prove_seal()` runs the tamper before grading |
| third-party package / second file | `-E -s -S -P` on the graded program | `_prove_stdlib_only()` checks all three sides |
| symlinked output *parent* | walk every path component to root + realpath | `symlinked-output-exploit` mutant |
| expectations from an agent-writable file | pristine journal copy in the sealed tree | — |
| cwd on `sys.path` via `-m` | `-P` on the verifier | planted module imports without it, not with |
| planted `pytest11` plugin | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` + `-p ctrf.main` | `planted-pytest-plugin` mutant |
| planted `conftest.py` | `--noconftest` | same probe |
| planted `sitecustomize.py` | `-S` via `tests/run_pytest.py` launcher | `planted-sitecustomize` mutant |
| pinned `reward.txt` symlink | `rm -f` before writing | `pinned-reward-symlink` mutant |

Final ledger: **21 wrong readings and exploits, all 0.000 through the real verifier.**

---

## 5. Gate-by-gate log

18 commits. Roughly half the rounds were genuine findings, half were platform failures, and
three were my own errors.

| Push | Gate that blocked | What it actually was |
|---|---|---|
| `e7ec425` | — | static 25/25, rubric **31/31**, duplicate UNIQUE, validation green, pass@2 0/2 on the first try |
| `68ca7af` | `ava_review` | one real claim (import the oracle from `/tests`) among six garbled bullets; hardened the seal, added the verify-time journal |
| `66cb776` | `qc_gate` | **3 real findings**, incl. a bug in my own reference (U+20D0) |
| `0f9d24d` | `qc_exec` | infra — `actions/checkout` HTTP 429 |
| `8e14121` | `cosine_similarity` | infra — same 429 |
| `367f9e7` | `pass2` | infra — pass@k status not published inside the job's 60-min wait |
| `6821cce` | `deep_review`, `ava_review` | infra — artifact download hit the CI identity's API rate limit |
| `92eb3b4` | `qc_gate` | **final sigma** — reference wrong, oracle right |
| `60a82e1` | `ava_review` | stdlib-only promised but not enforced |
| `e37e919` | `ava_review` | contract said "stdlib only", enforcement allowed sibling files |
| `321369d` | `qc_gate` | **4 findings**: range bounds ungraded, `-m` cwd hijack, agent-writable expectations, symlink parents |
| `c178f59` | `qc_gate` | pytest plugin autoload |
| `5d2148e` | `deep_review` | infra — review returned **no verdict**, fail-closed |
| `e6aacc1` | `qc_gate` | **C3 again** — sigma implemented but not graded |
| `f34293d` | `qc_gate` | **C3 again** — refusal order not graded |
| `9b50941` | — | **all green, `accepted`, pass@5 0/5** |

### 5.1 The two reference bugs QC found that I had not

Both had the same shape — the shipped solution was right, the verifier's reference was wrong,
and only the restricted fixture repertoire hid the disagreement:

- **U+20D0.** `_reference.stored_form` normalised the runs *between* left-alone code points,
  assuming every left-alone code point is a starter. U+20D0 and its neighbours are combining
  marks inside U+2000–U+2FFF, so canonical ordering broke across them. Decomposition stops at
  a left-alone code point; **ordering does not.**
- **Final sigma.** `_reference.compare_key` lowercased the whole stored name at once, invoking
  Python's context-dependent rule, so a trailing U+03A3 folded to U+03C2 instead of U+03C3.
  `gLowerCaseTable` is a plain per-code-point map with no notion of word position.

---

## 6. Error → what to do

| Symptom | Do this |
|---|---|
| `qc_gate` "Narrow / Hardcodable Held-Out Coverage" (C3) | Do **not** patch the named case. Build `coverage_audit.py`: replay every journal under every single-decision mutation, fix everything it reports. It found two gaps no gate had named |
| C3 again after you built the audit | The decision space is bigger than the rule list. Cover **refusal order**, id policy, self-exclusion — not just the domain rules |
| A mutation shows as uncaught | Three possibilities, and only one needs a fixture: it is a real gap, it is *provably equivalent* (remove it with a comment), or **your mutation is broken** (mine never freed an id) |
| A mutant scores 0.000 and you are pleased | Check it fails for the right reason. A stub that writes empty output scores 0.000 regardless. Enforcement mutants must be otherwise-correct solvers |
| `qc_gate` blocks and the comment shows one finding | It **early-exits**: "22 further checks were deferred". You get one per round by design. Decode `<!-- QC-FIXES-B64:… -->` for the exact pending finding rather than guessing |
| You want "stdlib only" enforced | `-I` is **not** enough: it isolates env, user-site and the script dir, but `site.py` still adds site-packages, so `import pytest` succeeds. `-S` removes site-packages; `-P` removes the script dir. Measure in the image |
| Verifier runs `python3 -m pytest` | `-m` puts cwd on `sys.path`. Add `-P`. Then also disable plugin autoload — pytest auto-loads any `pytest11` distribution the root agent planted in site-packages, and it runs *inside* the grading process |
| You added `-P` and think the verifier is sealed | `site.py` still imports `sitecustomize.py` from site-packages. Only `-S` stops it, and `-S` hides pytest — launch through a small script in `/tests` that adds site-packages back by hand |
| Verifier writes `reward.txt` with a redirect | The agent can leave a symlink there pointing at an unwritable file, so a pinned value survives. `rm -f` first |
| Choosing a trap character | Check the **fold** as well as the decomposition. U+212B/U+2126 diverge between `gLowerCaseTable` and `str.lower()`, which would have made "case-insensitive" ambiguous |
| Writing a final-sigma fixture | Python's rule only fires when the sigma **ends the string**. `ΛΟΓΟΣ.txt` discriminates nothing; `ΛΟΓΟΣ` does |
| An `ava_review` bullet's evidence describes correct behaviour | Inconclusive probe (`rebuild-plate-rasterizer` §3.3). Six such bullets appeared in one BLOCK here alongside one real advisory. Read every bullet; act on the real one |
| An advisory contradicts what you measured | Check it. The U+0130 advisory was wrong — U+0130 decomposes to `I`+U+0307 in `stored_form`, so `compare_key` never sees it. Do not change code for a claim you have disproved |
| A gate fails in seconds, or with no verdict | Infra. Read the job log first. Five rounds here died on: codeload 429 ×2, a pass@k status published after its 60-min wait, an artifact download hitting the CI identity's API limit, and a review returning nothing. None reached the task |
| Repeated infra failures | Probe the failing surface directly; the status banner said "All Systems Operational" while codeload threw 429 on 3 of 4 requests. Do not re-push into a live incident |

---

## 7. Process rules learned the hard way

- **A shell heredoc collision can make an edit silently not happen.** A `cat > test.sh <<'EOF'`
  nested inside another heredoc failed at parse time, so the whole command — including the
  write — never ran. `git status` showed only one file modified, which is how I caught it. The
  mutant sweep then running was validating the *unhardened* harness and would have "confirmed"
  a fix that did not exist. **Read the diff, not the command's exit code.**
- **`str.replace` matches inside other definitions.** Patching `mutants.py` clobbered
  `SYMLINK_EXPLOIT` because one exploit's source is a substring of another's. Anchor on unique
  text and assert the count first.
- **Assert substitution counts before writing**, and write the file only after every assertion
  passes — three patches failed their assertion mid-script and left the file untouched, which
  was correct but easy to mistake for success.
- **Count what the gate counts.** I held a push for ~40 minutes to protect a "scarce" pass@2
  slot, having inferred 5 of 6 were used by counting my own pushes. The `ratelimit` job log
  said `pass@2 executions … in last 24h: 0 (limit 6)`. Read the number, don't infer it.
- **Once every check is green, stop pushing.** A push re-rolls all rubric criteria plus
  `deep_review`/`ava_review`/QC and burns a rate-limited trial. Improvements stay on a local
  branch (`nfs4-access-audit` §5.3, confirmed again here).

---

## 8. Checklist for the next task

1. Pick the crux; check the **fold and the decomposition** of every character it turns on.
2. Confirm no local oracle: can the container answer the graded question? (`iconv`, kernel
   drivers, a pip package.)
3. Restrict the repertoire so exactly one reading survives; assert it against the standard's
   own published tables, parsed rather than recalled.
4. Build the sample **inert** under every wrong reading, and make it teach the wrong
   generalisation with near-equivalent cases.
5. Write `coverage_audit.py` **before the first push**: every single-decision mutation over
   naming rules, structural rules **and refusal order**, replayed against every fixture.
6. Write the fixture builder so it asserts each record's intended outcome at generation time.
7. Three independent implementations; cross-check **every graded quantity**, not just the
   first one.
8. Harden the verifier and prove each control by performing the attack: `/tests` seal, drop
   privileges, `-E -s -S -P` for the graded program, `-P` + no plugin autoload + `--noconftest`
   + `-S` launcher for the verifier, `rm -f` the reward file, realpath-check every graded path.
9. Enforcement mutants must be otherwise-correct solvers.
10. `.dockerignore` from the first commit; no `solution`/`tests` substrings in the Dockerfile;
    no `"You have N seconds"` line; instruction well under 1,500 tokens.
11. README updated in the **same commit** as the code, verified against the final diff.
12. On any red run, read the job log before changing anything — half the rounds here were
    platform failures that never reached the task.
