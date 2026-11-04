# ML-052 redesign (R11+) frozen contract

Frozen 3 November 2026 by the coordinator, before the third reserve
(`fresh-v3.json`) is labelled and before any R11 candidate run, as required by
the "ML-052 redesign placement" ledger entry. Changing anything here after the
first R11 run needs a new ledger entry and voids any reserve already authored
under this version.

## 1. Statuses and exactness

- Statuses stay `met`, `missing`, `contradicted`, `uncertain`
  (`backend/training_assessment.STATUSES`). No new status is added.
- A paraphrase the classifier cannot confirm is `uncertain`. It never earns credit.
- `missing` means the requested content is genuinely absent; `uncertain` means
  it is present but cannot be confidently judged.
- A case is exact only when every criterion status equals the gold status.
  "Valid" means every gold status is `met`. False credit means `met` where
  gold is not `met`. These definitions are unchanged from R1–R10.

## 2. Quote contract (experiment layer)

- Each point carries `learnerQuotes`: a list of 0–3 strings. Each is a
  nonempty exact contiguous substring of the learner response, at most 160
  characters, and the quotes do not overlap.
- `met` and `contradicted` need at least one quote; `missing` has none;
  `uncertain` may have 0–3.
- Each quote must be relevant to that point, meaning it states content the
  point's status relies on. Extra quotes must not widen what is credited.
- Quote order follows ascending source position in the learner response. Resolve
  repeated strings by the earliest available nonoverlapping occurrence after the
  preceding quote; reject a list that cannot be bound this way. Do not repeat an
  identical quote string in one point. The total quoted text per point is at most
  480 characters (the existing three-by-160 bound). This span-binding clarification
  is recorded before the first R11 inference and third-reserve labeling.
- The legacy `learnerQuote` field equals the first quote (or `""`), so the
  existing validator, and the frozen baseline, keep working unchanged.
- Delivered means a review that passes this contract plus the existing checks
  in `backend/training_assessment.py`. The baseline keeps its single-quote
  contract, so delivered yield is compared under different contracts and is
  reported that way.
- Production code and the Unity display change only at promotion, after
  semantic acceptance. Native acceptance must then cover multi-quote rendering.

## 3. Label conventions confirmed for fresh-v3

- Gold uses only reports received by the checkpoint cutoff, in the same episode.
- A report's `source` field is part of the eligible evidence. A learner who
  correctly attributes a fact to that source ("stand planning says…") is
  supported for that attribution. Attributing it to the wrong source is an
  unsupported addition (grounding is not `met`).
- The earlier conventions in `TYPED_RELATION_REVIEW.md` still hold:
  - unknown clearance is not a denial;
  - absent readiness is a report-scope unknown, not "not ready";
  - a correct core with an unsupported extra keeps its core statuses, but grounding blocks approval;
  - latest values need not recite superseded ones.

## 4. Unchanged

These are unchanged:
- pinned DeBERTa-v3-large model and revision `b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7`, MPS float16, threshold 0.8, no truncation within the 512-token bound;
- the 55/60/90-second budgets;
- the five fixed gates;
- the frozen small-NLI v2 CPU baseline;
- the 1200-character input limit.
