# Stand B detector revision (v2): pre-registered protocol

Written and committed **before** any v2 frame is rendered or any v2 model is
trained. Changes after that point must be recorded as amendments with a date
and reason; nothing here may change after the held-out split is opened.

## Why a revision

The v1 pilot (`outputs/checkpoint2-run/detector-pilot.json`) found 0 of 6
held-out trucks. Its later development-only fit reached 1 of 6 with 45 false
detections on validation. Both stay on record unchanged. Likely causes: the
tanker is about 60×25 px in a 960×540 frame and SSDLite resizes to 320 px; and
there were only 13 labelled training boxes. The v1 test split has been opened
and is never reused for selection or acceptance.

## Data

- Source: the existing Stand B scene (`stand_clearance`, seed 17), rendered by
  `P01CaptureBatch` in plan mode at 960×540 with synchronized RGB, linear depth
  and an object mask. No scenery, asset or route changes.
- Labels: the tanker's visible mask extent, computed by Unity. They are
  geometric ground truth, not human annotations.
- Plans: `experiments/apron_detector/plan.py`. Development seed `20261117`
  (12 training and 4 validation domains); held-out seed `20261118` (5 domains).
  40 frames per domain. A domain is one tanker colour and size; frames vary
  source time, viewpoint and field of view, including look-away views (about
  15%) and views behind the Stand B bridge cab (about 10% while parked).
- Splits are by domain; no domain appears in two splits. Held-out frames come
  from the same distribution as development frames (same apron, same ranges),
  so held-out results do not measure transfer to another airport or to real
  photographs.

## Held-out access

1. Render the held-out plan into `work/detector-v2/heldout/`.
2. Write `outputs/checkpoint2-run/detector-v2-heldout-manifest.json` with the
   SHA-256 of every held-out file, and commit it **before training starts**.
3. Training and selection code never reads `heldout/`. The evaluation command
   verifies the manifest, runs **once**, for the **one** selected candidate,
   and appends its output to the record whatever the result.

## Candidates (fixed before training)

| ID | Model | Input | Fixed budget |
|---|---|---|---|
| A | torchvision SSDLite320 MobileNetV3, COCO weights (cached) | 320×320 tiles at native resolution, stride 160; detections merged with NMS IoU 0.5 | 12 epochs, AdamW lr 2e-4, head only, batch 8 tiles |
| B | torchvision Faster R-CNN MobileNetV3-Large-FPN, COCO weights (owner-approved download) | full frame, min side 540, max 960 | 8 epochs, AdamW lr 1e-4, default trainable backbone layers, batch 4 |

Both predict COCO class 8 (truck) as the tanker; other classes are ignored.
Seed 17. No other hyperparameter search.

## Scoring

- **Evaluable box:** a ground-truth box with at least 150 visible pixels and
  both sides at least 6 px. Smaller boxes are *ignore* regions: a detection
  overlapping one (IoU ≥ 0.3) counts as neither correct nor false.
- **Match:** detections in descending score order, greedy, IoU ≥ 0.5 with an
  unmatched evaluable box.
- **Reported:** precision, recall and F1 over evaluable boxes; the same over
  all boxes with no ignore rule (comparable with v1); false detections per
  look-away frame; mean inference seconds per frame on this Mac.
- **Threshold:** chosen per candidate on validation only, from
  {0.05, 0.1, …, 0.95}, maximizing F1, ties to the higher threshold.
- **Selection:** the candidate with the higher validation F1; ties go to the
  higher validation precision.

## Qualification gate (for use as camera evidence in the replay)

On the held-out split, at the validation-selected threshold:
**precision ≥ 0.90 and recall ≥ 0.70** on evaluable boxes. A candidate that
fails is recorded as not qualified and is not used as evidence. Its
detections may still be shown in development tools, labelled as unqualified.

## Out of scope here

Real-photo accuracy (a separate check), depth-based features, and the
reports-versus-camera comparison, which has its own frozen evaluation.
