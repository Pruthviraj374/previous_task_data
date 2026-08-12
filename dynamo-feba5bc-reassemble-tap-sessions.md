# dynamo-feba5bc — reassemble-tap-sessions

| | |
|---|---|
| **Outcome** | **ACCEPTED** — all 17 checks green, `accepted` label, **on the first push** |
| **Repo** | `dynamo-feba5bc-security` |
| **PR** | https://github.com/handshake-project-dynamo/dynamo-feba5bc-security/pull/1 |
| **Category / sub** | Security / Network Forensics (pre-seeded) |
| **Benchmarked model** | reported as `Model A` (`task.toml` names Opus-4.8 / Terminus-2 — fixed dataset fields) |
| **Final commit** | `0f0e5c6` (run `31642881870`) |
| **Headline** | **pass@2 = 0/2 · pass@5 = 1/5 solved, 4 good valid fails, avg@5 = 0.200.** One commit, one pipeline run, zero gate failures |

The first task in this corpus to be accepted on a single push. That is the finding
worth carrying: the design was assembled entirely out of rules the earlier
retrospectives had already paid for, and it needed no iteration.

---

## 1. What the task asks

Tap appliances recorded pcapng captures during an intrusion. The agent writes a
self-contained stdlib-only `/app/reassemble.py`, invoked

```
python3 /app/reassemble.py <capture.pcapng> <report.json>
```

which emits one record per TCP conversation: the two endpoints, the instant of the
connection's SYN and of its last packet (whole nanoseconds since the epoch), and the
length and SHA-256 of the reassembled byte stream in each direction.

- **Agent sees:** `instruction.md` plus three sample captures under `/app/samples/`,
  **each with the report the retired analysis box produced for it**.
- **Graded on:** ten held-out captures, none of them shipped. Twelve tests,
  all-or-nothing.
- Comparison is exact equality on every field, with no tolerance anywhere.

---

## 2. The crux, and the invariants that keep it alive

Three mechanisms, each a **real, published, conditional** behaviour of a format or
protocol the instruction *names and does not restate*:

| # | Mechanism | Standard | Natural wrong implementation |
|---|---|---|---|
| 1 | A pcapng packet timestamp counts a unit set **per interface** by `if_tsresol` — one octet, top bit clear → negative power of ten, set → negative power of **two**, absent → 10⁻⁶ | pcapng §4.2 | Hardcode microseconds for the whole file |
| 2 | A frame carrying an IPv4 datagram shorter than the **minimum Ethernet data field** is padded, and the padding is captured; the datagram's own total-length field bounds the payload | IEEE 802.3 | Payload = everything after the TCP header to the end of the frame |
| 3 | TCP sequence numbers are 32 bits and **wrap**; a byte's position is its modular distance from the ISN | RFC 793 §3.3 | `offset = seq - isn - 1` behind an `if offset >= 0` guard |

**Invariants, machine-enforced in `check_shipped_invariants` — the generator refuses
to emit a sample capture that violates one:**

1. no shipped interface carries an `if_tsresol` option at all;
2. no shipped frame carries an octet beyond the datagram it announces — **every host
   in the samples negotiates TCP timestamps**, which keeps even a bare ACK above the
   46-byte minimum, so padding never appears;
3. no shipped conversation runs its sequence numbers within reach of the wrap point.

**The corpus-witness half.** Everything that is *not* a crux is exercised by the
shipped three: both section byte orders, two interfaces in one file, SHB/IDB/EPB
options, interface statistics blocks, VLAN tags, IPv4 options, TCP options,
out-of-order segments, retransmissions, a reset teardown, a direction with no
payload, and ARP/UDP/ICMP/IPv6 traffic to ignore. That is what keeps the task out of
`qc_gate` B5: only the three external rules are unstated.

### Why the timestamp axis is *noticed*, not *recalled*

Straight from `experiment-analysis-frame` §4(b). `if_tsresol` is not a table to look
up — it is a **single octet whose top bit changes the base**. `0x09` means 10⁻⁹ and
`0x89` means 2⁻⁹, and they differ by a factor of ~1,953,125. That is the same shape
as `P2D` vs `PT48H` and cron's first-character `*`: a syntactic property of the input
that an otherwise-correct implementation does not think to check. One pass@5 trial
implemented the selector **backwards** (`<128 → binary`, `>=128 → decimal`), which no
amount of memorised knowledge would have produced — it is a distinction, not a fact.

### Making the pipeline integer-only, deliberately

The first draft reported timestamps as ISO-8601 with nine fractional digits. That was
abandoned before a line of it shipped: epoch seconds with nanosecond precision need
19 significant digits, `datetime` is microsecond-limited, and float64 gives ~16 — so
**any** solver formatting through `datetime` would have lost the bottom three digits
and been failed on a rounding artifact rather than on the crux. That is exactly the
`difficulty_evidence` "threshold / formatting near-miss" BLOCK that cost
`experiment-analysis-frame` a cycle.

Reporting **integer nanoseconds since the epoch** removed the entire class. Every
fixture instant is exact in nanoseconds by construction (the generator asserts
`ts_ns % tick == 0`), including the binary-tick interface — `2⁻⁹ s = 1,953,125 ns`
exactly, because `10⁹ = 2⁹ · 5⁹`. Only `k ≤ 9` is exact in nanoseconds, which is why
`0x89` and not `0xA0`. `lumenp` §6's rule generalises: **ask whether the pipeline can
be made integer-only before reaching for a tolerance.** Here it could, so grading is
exact and no rounding argument is available to anyone.

---

## 3. What was reused, and from where

Nothing in this design was invented at the design stage. Each decision traces to a
prior file:

| Decision | Source | Why |
|---|---|---|
| Deciding rules are **real external conventions the instruction names but does not enumerate** | `lumenp` §3, §10 | Invented rules must be disclosed (else B5) and disclosed rules get implemented — six were solved 2/2 |
| Rules must be **conditional**, firing only in a sub-case no sample shows | `lumenp` §6 | BMP row padding was real, unconditional, and still solved 2/2 |
| Rules must be **noticed**, not memorised | `experiment-analysis-frame` §4(b) | An ISO 4217 exponent table was fetched on demand; a syntactic split was not |
| **Two or more independent** conventions | `experiment-analysis-frame` §4 | Different agents fail on different ones — the difference between 2/5 and 0/5. Here three axes produced three distinct root causes across four failures |
| Cruxes that **compose**, plus fixtures combining them | `lumenp` §4, §9 item 4 | `h09`/`h10` combine all three and were the **only two tests to fail in all four failing trials** |
| Ship a **complete-looking self-check silent on the trap** | `contact-export` §9, `merge-lora` §2 | Sample reports are correct and complete, and inert on all three mechanisms |
| Ship expected answers **only for inputs that are not graded** | `merge-lora` §4.1, `sweep-replay` §5.1 | Removes both the `cp` bypass and the diff-and-self-correct path |
| Enforce stdlib-only with `sys.addaudithook`, **never an AST screen** | `contact-export` §3.2, `audit-build-context` §4.2 | Three consecutive `ava_review` BLOCKs on the screen; the hook passed first time here |
| The hook must raise **`ImportError`** | `audit-build-context` §4.2 | A solver's `try/except ImportError` fallback is correct and must survive |
| Drop privileges for the graded program | `freight` §4 | Everything runs as root otherwise |
| `.dockerignore` up front | `fir` §6.1, `tarballs` §5.3 | Cheap; don't learn it from CI |
| **Omit** the "You have N seconds…" line | five prior tasks | The rubric fails it under `instruction_concision` |
| Every mutation **asserts its pattern still matches** | `experiment-analysis-frame` §7 | Three patterns went silently no-op there |
| Root `README.md` current in the same commit | `readme-rule.md`, `tarballs` §5.4 | Reviewer-facing and goes stale silently |

---

## 4. What actually worked — and the one genuinely new move

**Ground truth is planted, not parsed.** The fixture generator scripts each
conversation onto the wire, so it already holds the exact payload bytes it put in each
direction and the exact instant it stamped on each packet. The expected report is
built from those planted values. **No reference parser sits between the fixtures and
the answer.**

This is stronger than `audit-build-context` §4.1 (ground truth from running the real
tool) and it retires `experiment-analysis-frame` §7's warning that `oracle = 1.000` is
"nearly vacuous when `solution/` is byte-identical to `tests/_reference.py`". Here
there is no `_reference.py` at all: the oracle is an *independent* consumer that has to
parse the bytes back and agree with what was planted. Oracle 1.000 is a real
cross-check, and `tests/` is ~200 lines lighter for it.

The rubric reviewer noticed and credited exactly this — `reviewable`: *"Expected values
derived by the generator, not hardcoded."*

**Carry this forward: when you generate the input, you already know the answer. Do not
compute it a second time.**

### Calibration, before the first push

Five one-rule variants, each clean on all three shipped samples:

| Variant | Shipped | Held-out broken |
|---|---|---|
| Assumes every interface ticks at 10⁻⁶ | clean | 6 — h02, h03, h04, h06, h09, h10 |
| Reads `if_tsresol` but ignores its top bit | clean | 3 — h04, h06, h10 |
| Payload runs to the end of the captured frame | clean | 4 — h05, h06, h09, h10 |
| Sequence offsets by subtraction, no wrap | clean | 4 — h07, h08, h09, h10 |
| ISN off by one | *diverges on shipped* | 10 — all |

The first sweep left the binary-tick variant caught by only **2** fixtures. Per
`lumenp` §7 that reads as a dud-fixture signal, not a subtle mutant; the fix was to put
a `0x89` interface on `h06` as well, which also bought a padding × binary-tick
combination. **Do the sweep before the first push and act on a low catch count.**

The ISN variant is instructive in a different way. It initially broke **nothing**,
because `stream()` assembled with `bytearray` slice assignment, and assigning past the
end of a bytearray silently appends instead of leaving a hole — so a uniformly shifted
set of offsets produced identical bytes. Rewriting `stream()` to size a buffer from the
furthest byte seen and write into it made the variant observable. **A mutant that
breaks nothing is more often a hole in your own assembly than an equivalent mutant.**

---

## 5. Gate-by-gate log

Run `31642881870` on `0f0e5c6` — **every gate passed, first time**:

| Gate | Verdict |
|---|---|
| `changes`, `ratelimit`, `cosine_similarity`, `similarity` | pass — top similarity 0.863 against a 0.9 threshold |
| static (`review` deterministic checks) | pass — all 25, including `.dockerignore` and the Qwen3 ≤1500 count (measured 685) |
| Dynamo eval (rubric) | **PASS — all 31 criteria, zero failures** |
| duplicate check | **UNIQUE** — closest lexical 0.114 (`kv-store-grpc`) |
| `validation` | pass — Docker ✅ Oracle ✅ Nop ✅ |
| `pass2` | **pass — 0/2 solved, 2 valid fails**, `Rerun Recommended: NO` (24m41s) |
| `pass2_suggestion` | **skipping** — no difficulty suggestion needed |
| `deep_review` | pass — no blocking issues |
| `ava_review` | pass — one advisory (§6) |
| `tier1` | pass |
| `qc_eval`, `qc_exec`, `qc_gate` | pass — 38 checks clean, 6 minor advisory, `QC-FIXES-B64:W10=` → zero blocking |
| `trials` (pass@5) | **pass — 1 solved, 4 good valid fails, avg@5 = 0.200** (29m39s) |
| `gate` | pass → `accepted` |

Timings for planning: whole run ≈ **1h27m** wall clock. `pass2` 24m41s, `trials`
29m39s, `qc_eval` 9m10s, `ava_review` 7m8s, `qc_exec` 4m36s.

---

## 6. What the model actually did

**pass@2 — 0/2.** Both agents converged on the same architecture and both wrote
`offset = seq - (isn + 1)` behind an `if offset >= 0` gate. One of them named the risk
in its own step-14 reasoning — *"TCP sequences wrap around 32-bit… We don't handle
wrap-around… not necessary? Could improve if needed. But task likely fine."* — and
deferred it. That is `accrued-interest`'s *"probably isn't being tested"* almost word
for word, in a different category three months later.

**pass@5 — 1/5 solved, 4 valid fails, stratified across all three axes:**

| Root cause | Trials | Detail |
|---|---|---|
| Non-modular sequence arithmetic | 3 | All three independently wrote `offset = seq - isn - 1` with a `>= 0` guard; post-wrap segments silently dropped |
| `if_tsresol` high-bit selector **inverted** | 1 | Coded `<128 → 1 << val` (binary) and `>=128 → 10**val` (decimal) — the opposite of the spec. Timestamps out by up to six orders of magnitude. Compounded with the wrap bug: 8 of 12 tests failed |
| Ethernet padding not excluded | 1 | Read `tcp = pkt[ip_off + ihl:]` instead of bounding by total length. Its own step-5 exploratory script computed `total_ip_len` correctly and never carried it into the final code |

Three findings worth keeping:

1. **The compound fixtures did the deciding work.** `h09` and `h10` were the only two
   tests to fail in **all four** failing trials, each for a different reason. This is
   `lumenp` §4's corollary confirmed in a second, unrelated category: build fixtures
   that combine cruxes, not only isolate them.
2. **The padding failure escalated into an OOM kill.** Including padding meant a SYN-ACK
   landed at the ISN position, so the stream dict held keys at `0xFFFFFFFF` and above and
   the subsequent `bytearray(0x100000005)` (~4.3 GB) was SIGKILLed. It still graded as a
   *good valid fail* — the agent's approach was sound and its own bug killed it. **A
   crash is not automatically an invalid failure**; what matters is whether the
   instruction and inputs made the approach wrong.
3. **The one solved trial cost nothing.** The gate needs ≥1 good valid fail and ≥3
   total; 4 of 5 cleared it comfortably. Three independent axes are why: no single
   mistake explains all four failures.

### The `ava_review` advisory (non-blocking, and correct)

> *"expected reject a capture containing a mid-stream (SYN-absent) TCP flow, which must
> NOT be reported, but the verifier would instead accept on all 10 captures because none
> contain a SYN-absent flow."*

A rule stated in `instruction.md` with **no fixture witnessing its reject side** — the
same `complete_test_coverage` shape as `contact-export` §3.1 and `freight` §3. The fix
was built and validated locally the same day: mid-stream flows added to one shipped
sample (disclosed side) and to `h01`/`h05`/`h10` (graded side), plus a
`reports-syn-absent-flows` variant caught by 3 held-out captures. Oracle re-verified at
1.000, nop 0.000.

**It was deliberately not pushed.** The PR was already `accepted`, and a push re-runs
the whole pipeline, burns a rate-limited pass@2/pass@5, and re-rolls all 31 LLM-graded
criteria plus `deep_review`, `ava_review` and QC — any of which can flip. `merge-lora`
§7 and `experiment-analysis-frame` §8 both say hold it and ship it with the next
blocking fix. It sits on a local `held-improvements` branch so `submission` stays
byte-identical to `origin`; if a human reviewer sends the task back, it ships in that
commit. **Write the fix immediately, push it only when something else forces a push.**

### The QC advisories worth understanding

Three of QC's six minor advisories were the *same* inconclusive probe: rival readings
(keep-first vs keep-last retransmission, unconditional `last_seen`) *"reproduce all
disclosed samples AND pass all held-out graded"* captures. That is not ambiguity — it
is the generator's guarantee that retransmissions carry identical bytes, so the two
readings are provably indistinguishable and neither can be wrong. **A probe that
reports two rival rules agreeing everywhere is reporting that you removed the
ambiguity, not that you have one.** Compare `sweep-replay` §6: read the evidence line,
not the headline.

---

## 7. Bugs I introduced myself

- **Block types read in the wrong byte order.** `read_packets` read every block type
  as little-endian. The SHB's `0x0A0D0D0A` is a byte-order-agnostic palindrome so it
  matched anyway, but in a big-endian section an IDB reads as `0x01000000` and the
  interface table stayed empty — the big-endian sample produced **zero sessions**.
  Caught only because the cross-check compares the oracle against planted truth on
  every capture. Read the type in the section's own order; detect the SHB by its
  literal bytes.
- **`bytearray` slice assignment hides gaps.** Covered in §4 — it silently appends past
  the end, which made a whole class of offset error unobservable.
- **A calibration variant that broke nothing** looked like an equivalent mutant and was
  a hole in the assembly code. Investigate every survivor.
- **An unreachable helper left in the generator.** `Wire.sorted_packets` was written,
  never called, and contained a nonsense `and`-chained sort key. Harmless, but the QC
  reviewer flags unused code; delete it as you go.

---

## 8. Process notes

- **Fork first, then set identity in the repo's local config** at clone time
  (`git config user.name/user.email`) before the first commit. Rewriting later cancels
  whatever run is in flight.
- The upstream repo is **private**. A PR opened from the fork lives on the *upstream*
  repo, not the fork — the fork's Pull requests tab is empty, which reads as "the PR
  didn't get created". Check the signed-in account before debugging anything else.
- `gh repo fork <repo> --clone --remote` fails with a usage dump; `--clone=true` works.
- **Stage explicit paths.** The repo `.gitignore` does not cover `jobs/`; add it. Binary
  fixtures under `environment/data/` need `git add -f` if any ignore pattern touches
  them — verify the staged file count.
- `harbor run -p .` from inside `task/`, not `-p task` from the repo root.
- Probe the audit hook **inside the built image**, both sides, before pushing. Twelve
  spellings blocked here (plain import, `__import__`, `importlib.import_module`,
  `eval`-wrapped, `sys.path` injection, `CDLL`, `getattr`-spelled `CDLL`,
  `cdll.LoadLibrary`, `subprocess`, `getattr`-spelled `os.system`, `os.fork`,
  `socket.connect`) and the `try/except ImportError` fallback still ran. Test an
  **installed** third-party package (`pytest` is in the image), not only an absent one.

---

## 9. Reusable checklist

1. Is every deciding rule **real, external and published**? If the task invented it, it
   must be disclosed, and disclosed rules get implemented.
2. Is each **conditional** — fires only in a sub-case absent from every shipped sample?
3. Is each **noticed rather than recalled** — a syntactic property of the input (a top
   bit, a `P` vs `PT`, a first character `*`), not a table?
4. Are there **three independent** axes? Different agents fail on different ones.
5. Do the axes **compose**, with held-out fixtures combining them? That is where the
   real failures land.
6. Can ground truth be **planted by the generator** instead of parsed back? If so, you
   need no reference module and your oracle becomes a genuine cross-check.
7. Can the pipeline be made **integer-only** so grading is exact? Ask before reaching
   for a tolerance — and check what a tolerance would make uncatchable.
8. Are the sample invariants **machine-enforced in the generator**, so a later edit
   cannot quietly leak the trap?
9. Does a **corpus-witness** pass prove the shipped set exercises every non-crux feature?
10. Mutation sweep **before** the first push: every variant clean on all shipped, caught
    by **≥3** held-out; investigate any survivor and any low catch count.
11. Does every rule the instruction states have a fixture on **both** sides — the accept
    side *and* the reject side?
12. Audit hook probed both ways inside the image; `ImportError`, not a bespoke exception.
13. `.dockerignore` present; no "You have N seconds" line; instruction re-measured after
    the last edit.
14. README current in the same commit; test-name diff clean; no AI attribution.

---

## 10. One-paragraph version for future me

This task was accepted on the first push, with pass@2 0/2 and pass@5 1/5
(avg@5 = 0.200), because every design decision was taken from a previous
retrospective rather than rediscovered. The container is real (pcapng, Ethernet,
IPv4, TCP) and the three deciding rules are real published behaviours the instruction
names and never restates — a per-interface `if_tsresol` whose **top bit** switches the
base between powers of ten and powers of two, the Ethernet minimum-frame padding that
makes the IPv4 total-length field the only honest payload bound, and the 32-bit
sequence space that wraps — each invisible in the three shipped captures because every
sample host negotiates TCP timestamps, no sample interface carries the option, and no
sample connection approaches the wrap point, all three enforced by the generator. The
shipped samples come with correct, complete-looking reports that are silent on all
three, and are not graded. Two decisions did the most work: reporting **integer
nanoseconds** instead of a formatted timestamp, which deleted the entire rounding class
before `deep_review` could call it a threshold artifact; and **planting ground truth in
the generator** rather than parsing it back, which removed the reference module
entirely and turned oracle = 1.000 into a real independent cross-check. Four of five
trials failed across three distinct root causes — three on non-modular sequence
arithmetic, one with the `if_tsresol` high-bit selector implemented backwards, one on
padding bleeding into the payload and OOM-killing itself — and the two capture fixtures
that **combined** all three mechanisms were the only tests to fail in every failing
trial.
