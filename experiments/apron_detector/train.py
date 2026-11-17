"""SUBSTANTIVE: fit and assess a pretrained detector on grouped Unity captures."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import torch
from PIL import Image
from torchvision.models.detection import (
    SSDLite320_MobileNet_V3_Large_Weights, ssdlite320_mobilenet_v3_large,
)
from torchvision.ops import box_iou
from torchvision.transforms.functional import to_tensor


def captures(root):
    for meta in sorted(root.rglob("*.json")):
        row = json.loads(meta.read_text())
        if "visibleBoxes" not in row or not row.get("trackingAvailable", True):
            continue
        image = meta.with_suffix(".png")
        if not image.is_file():
            raise FileNotFoundError(image)
        box = []
        for b in row["visibleBoxes"]:
            left, bottom = b["xMin"], b["yMin"]
            right, top = left + b["width"], bottom + b["height"]
            box.append([left, row["height"] - top, right, row["height"] - bottom])
        yield image, box


def tensors(rows):
    images, targets = [], []
    for path, boxes in rows:
        with Image.open(path) as encoded:
            images.append(to_tensor(encoded.convert("RGB")))
        targets.append({
            "boxes": torch.tensor(boxes, dtype=torch.float32).reshape(-1, 4),
            # COCO index 8 (truck) is the pretrained starting point for this
            # one-class fuel-transfer truck pilot. All other categories are ignored.
            "labels": torch.full((len(boxes),), 8, dtype=torch.int64),
        })
    return images, targets


def detections(model, rows):
    model.eval()
    scored = []
    with torch.inference_mode():
        for path, boxes in rows:
            images, targets = tensors([(path, boxes)])
            started = time.monotonic()
            pred = model(images)[0]
            elapsed = time.monotonic() - started
            keep = pred["labels"] == 8
            overlaps = box_iou(pred["boxes"][keep], targets[0]["boxes"])
            scored.append((
                str(path), pred["scores"][keep].tolist(), overlaps.tolist(), len(boxes), elapsed,
            ))
    return scored


def measure(rows, threshold):
    tp = fp = fn = 0
    for _, scores, overlaps, count, _ in rows:
        used = set()
        for score, ious in zip(scores, overlaps):
            if score < threshold:
                continue
            match = max((i for i in range(count) if i not in used and ious[i] >= .5),
                        default=None, key=lambda i: ious[i])
            if match is None:
                fp += 1
            else:
                tp += 1
                used.add(match)
        fn += count - len(used)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return dict(tp=tp, fp=fp, fn=fn, precision=precision, recall=recall,
                f1=2 * precision * recall / (precision + recall) if precision + recall else 0.0)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("dataset", type=Path)
    cli.add_argument("output", type=Path)
    cli.add_argument("--epochs", type=int, default=3)
    cli.add_argument("--development", action="store_true", help="Keep the held-out test split unopened")
    args = cli.parse_args()
    train = list(captures(args.dataset / "train"))
    val = list(captures(args.dataset / "validation"))
    test = [] if args.development else list(captures(args.dataset / "test"))
    splits = (train, val) if args.development else (train, val, test)
    if any(len(rows) < 2 or not any(boxes for _, boxes in rows) for rows in splits):
        raise SystemExit("Each split needs at least two captures and one visible labeled truck")
    hashes = {str(path.relative_to(args.dataset)): hashlib.sha256(path.read_bytes()).hexdigest()
              for rows in splits for path, _ in rows}
    if len(set(hashes.values())) != len(hashes):
        # Repeated frames within one split are allowed; identical images across
        # splits would contaminate the evaluation.
        per_split = [{hashes[str(path.relative_to(args.dataset))] for path, _ in rows}
                     for rows in splits]
        if any(left & right for index, left in enumerate(per_split) for right in per_split[index + 1:]):
            raise SystemExit("Identical RGB frame across splits")
    args.output.mkdir(parents=True, exist_ok=False)
    torch.set_num_threads(4)
    torch.manual_seed(17)
    model = ssdlite320_mobilenet_v3_large(weights=SSDLite320_MobileNet_V3_Large_Weights.DEFAULT)
    baseline = detections(model, test)
    model.backbone.requires_grad_(False)
    optimizer = torch.optim.AdamW(model.head.parameters(), lr=2e-4)
    loss_history = []
    for epoch in range(args.epochs):
        model.train()
        model.backbone.eval()
        order = torch.randperm(len(train)).tolist()
        losses = []
        for pos in range(0, len(order) - 1, 2):
            images, targets = tensors([train[i] for i in order[pos:pos + 2]])
            optimizer.zero_grad(set_to_none=True)
            loss = sum(model(images, targets).values())
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
        loss_history.append(sum(losses) / len(losses))
        print(f"epoch {epoch + 1}: loss {loss_history[-1]:.4f}", flush=True)
    choices = (.002, .005, .01, .02, .05, .1, .2, .3, .4, .5, .6, .7, .8)
    validation = detections(model, val)
    threshold = max(choices, key=lambda value: (measure(validation, value)["f1"], value))
    evaluated = detections(model, test)
    torch.save(model.state_dict(), args.output / "weights.pt")
    report = dict(
        scope="development only" if args.development else "grouped synthetic detector pilot",
        pretrained="torchvision SSDLite COCO",
        seed=17, splitCounts=dict(train=len(train), validation=len(val), test=len(test)),
        splitRGBSHA256=hashes, losses=loss_history, threshold=threshold,
        validation=measure(validation, threshold),
    )
    if evaluated:
        report.update(adapted=measure(evaluated, threshold), unchanged=measure(baseline, threshold),
                      meanTestSeconds=sum(row[4] for row in evaluated) / len(evaluated))
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
