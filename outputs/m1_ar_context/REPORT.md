# Milestone 1 report: AR conversational context

Held-out evaluation of the M1 method on the `m1` set, run once on 1 November 2026
under freeze 1. Scope and plan: `docs/AR_SCOPE.md`. Decisions: ledger D-080 to
D-087. Development history: `docs/REVIEW_DISPOSITIONS.md`.

## Question

Does AR context help a conversational assistant keep a shared referent and its
evidence current across turns? Two AR conditions are tested, each against an
ablation:

- **AR pointing:** the user selects or taps the aircraft in the AR view.
  Ablation: a text-only user who names the aircraft, stand or flight in words.
- **Tracking interruptions:** the app tells the assistant when the board was
  out of the user's view, and the prompt lists what changed in that interval.
  Ablation: the same turns without that information.

## Method and data

- **Method, frozen:** freeze 1, approved by the user
  (`config/conversation-freeze.json`): `conversation-prompt-v6`,
  `referent-rule-v3`, `conversation-validator-v2`, `conversation-scoring-v2`
  and `json-repair-v1`. Every run reports the freeze as approved and matching.
- **Held-out set `m1`:** 17 families, 40 turns, 4 scenarios, no images.
  - Written outside the repository by a separate session that saw neither the
    development families, the prompt nor any result.
  - Its hashes are committed in `config/heldout-m1.json`.
  - Its labels were revised once, before any run, for the precision label
    (checkpoint 1, D-085 and D-086).
  - Contents: `textOnly` on every turn; `lastSeen` on 12 turns in 10 families;
    `citeOnly` on 7 turns.
- **Family types (families/turns):**
  - ar-pointing 3/6, ambiguous-reference 2/6, rotation-correction 2/6,
    tracking-interruption 2/6;
  - missing-evidence 2/4, scene-change 2/4;
  - conflicting-reports 1/2, late-report 1/2, no-change 1/2,
    superseded-report 1/2.
- **Systems:**
  - `qwen3.5-9b` (backbone 1.2.0, thinking off) and `qwen3-vl-4b`, local, on
    `apronlens-v2-mps`;
  - the deterministic baseline (every received fact of the current referent,
    with changes flagged mechanically).
- **Conditions:** full AR, text-only, and no tracking; images off throughout.
- **Scoring:** a turn is correct only if every labelled criterion holds:
  status, referent, required citations, precision (`citeOnly`), change flag
  and unknowns. Intervals are Wilson 95%. Paired differences use a 95%
  bootstrap over families.
- **Records:** per-turn results contain the questions, so they stay with the
  set outside the repository. This report gives counts only.

## Results

| System | Full AR | Text-only | No tracking |
|---|---|---|---|
| `qwen3.5-9b` | **24/40 (60%)**, 45–74% | 19/40 (48%), 33–63% | 25/40 (62%), 47–76% |
| `qwen3-vl-4b` | 16/40 (40%), 26–55% | 10/40 (25%), 14–40% | 16/40 (40%), 26–55% |
| Deterministic baseline | 16/40 (40%), 26–55% | 16/40 (40%), 26–55% | 16/40 (40%), 26–55% |

Paired differences (percentage points, 95% family-bootstrap interval):

| Comparison | 9B | 4B |
|---|---|---|
| Full AR − text-only (AR pointing) | +12 (−5 to +31) | **+15 (+5 to +29)** |
| Full AR − no tracking (tracking) | −2 (−13 to +8) | 0 (0 to 0) |
| Model − baseline, full AR | +20 (0 to +38) | 0 (−15 to +15) |
| Model − baseline, no tracking | **+22 (+5 to +40)** | 0 (−15 to +15) |
| 9B − 4B, full AR | **+20 (+2 to +39)** | |

By family type, full AR vs text-only:

- **AR pointing families:** 9B 5/6 vs 2/6; 4B 4/6 vs 0/6.
- **Rotation corrections:** 9B 2/6 vs 0/6; 4B 2/6 in both.
- **Tracking-interruption families:** 9B 3/6, 4B 1/6, baseline 3/6, in every
  condition.

Selective prediction, full AR. A turn is answered when an answer is accepted,
and abstains otherwise (clarify, unknown or withheld):

| System | Coverage | Accuracy on answered | Abstentions right | Wrong answers shown |
|---|---|---|---|---|
| `qwen3.5-9b` | 25/40 | 18/25 (72%) | 6/15 | 7 |
| `qwen3-vl-4b` | 23/40 | 14/23 (61%) | 2/17 | 9 |
| Baseline | 40/40 | 16/40 (40%) | — | 24 |

Without pointing, the 9B's accuracy on answered turns falls from 72% to 54%,
and its wrong answers shown rise from 7 to 12.

Precision on the 7 `citeOnly` turns: 9B 3/7 with tracking and 2/7 without; 4B
0/7 and 1/7; baseline 0/7.

## Findings

1. **AR pointing helps.** Removing it costs the 4B 15 points (interval +5 to
   +29) and the 9B 12 points (interval −5 to +31, so not conclusive at this
   size). The effect concentrates where the referent can't be named easily:
   the AR-pointing families drop from 5/6 to 2/6 for the 9B and from 4/6 to 0/6
   for the 4B. Without pointing, the 9B also shows more wrong answers, not just
   more clarifications.
2. **Tracking information, as given here, doesn't help.** Listing the changes
   from the look-away interval made no measurable difference for either model
   (9B −2 points, 4B 0). The models seldom limit their answer to what the user
   missed: precision is 3/7 at best. This repeats the development pattern, and
   the precedence rule in the prompt didn't fix it. The finding concerns this
   way of passing tracking context to the model; it doesn't show that the
   context is worthless.
3. **The 9B beats the baseline; the 4B doesn't.** The 9B is 20 points above
   the baseline with full AR (interval 0 to +38) and 22 points above with no
   tracking (+5 to +40). The 4B equals the baseline at 40%.
4. **The models abstain more than they need to.** The 9B abstains on 15 turns
   and only 6 of those abstentions are right; the 4B on 17, with 2 right. Most
   of the rest are withheld replies. The validator is doing its job, but the
   models' replies often fail it.
5. **Development scores were optimistic, as expected.** On development
   families the 9B scored 92% with full AR; on held-out data it scores 60%.

## Limits

- 40 turns in 17 families: intervals are wide, and only the larger effects are
  conclusive. Milestone 3's final set is about five times larger.
- Images were off. The visual side is milestone 2.
- **Latency** wasn't measured cleanly: the 9B and 4B ran at the same time on one
  Mac for most of the run, so their latencies are inflated. Milestone 3
  measures it.
- The held-out author is a Claude session. It's independent of the method's
  development, but it isn't a person.

## Checkpoint 2: what changes for milestone 2

Following `docs/AR_SCOPE.md`, milestone 2 builds on what helped and fixes what
didn't. It never retunes on `m1`.

- **Pointing helps:** M2 extends it to viewpoint-relative references ("the one
  behind A2") from the user's own AR view.
- **Tracking didn't help as model context:** M2 makes the look-away a
  proactive notice from the app. The deterministic list of what changed while
  away is shown to the user directly, and the model only phrases it. That
  stops relying on the model to filter. It is measured on `m2`.
- **Over-abstention and withheld replies:** M2's validator-guided self-repair
  (one retry with the validator's errors) targets them directly.
- **The 4B is no better than the baseline:** M2 and M3 report it as the
  small-model reference, not as a candidate for the deployed assistant.
