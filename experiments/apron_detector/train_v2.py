"""SUBSTANTIVE: Stand B detector revision v2 (see PROTOCOL.md in this folder).

Three subcommands, run in this order:

    # 1. Fit both candidates on development data; select on validation only.
    python -m experiments.apron_detector.train_v2 fit work/detector-v2/development work/detector-v2/fit
    # 2. Freeze the held-out split (hashes every file; commit the manifest before step 3).
    python -m experiments.apron_detector.train_v2 manifest work/detector-v2/heldout outputs/checkpoint2-run/detector-v2-heldout-manifest.json
    # 3. One held-out run of the selected candidate. Refuses to run twice.
    python -m experiments.apron_detector.train_v2 evaluate work/detector-v2/fit work/detector-v2/heldout \
        outputs/checkpoint2-run/detector-v2-heldout-manifest.json outputs/checkpoint2-run/detector-v2-heldout.json

`fit` never reads a held-out folder. The v1 pilot script (train.py) is unchanged.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import time

os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
import torch  # noqa: E402
from PIL import Image  # noqa: E402
from torchvision.ops import batched_nms, box_iou  # noqa: E402
from torchvision.transforms.functional import to_tensor  # noqa: E402

TRUCK = 8  # COCO "truck"; the tanker is mapped to it, other classes ignored
MIN_PIXELS, MIN_SIDE = 150, 6
THRESHOLDS = [round(0.05 * i, 2) for i in range(1, 20)]
TILE, STRIDE_X, TILE_Y = 320, 160, (0, 110, 220)
BUDGET = {'A': dict(epochs=12, lr=2e-4, batch=8), 'B': dict(epochs=8, lr=1e-4, batch=4),
          'C': dict(epochs=10, lr=1e-4, batch=4)}  # C: PROTOCOL.md amendment 1


# ---------- data ----------------------------------------------------------------
def frames(folder):
    """(image path, evaluable boxes, ignore boxes, metadata); boxes top-left origin x0,y0,x1,y1."""
    rows = []
    for meta_path in sorted(Path(folder).glob('*.json')):
        meta = json.loads(meta_path.read_text())
        if 'visibleBoxes' not in meta:
            continue
        image = meta_path.with_suffix('.png')
        if not image.is_file():
            raise FileNotFoundError(image)
        good, ignore = [], []
        for b in meta['visibleBoxes']:
            box = [b['xMin'], meta['height'] - (b['yMin'] + b['height']), b['xMin'] + b['width'], meta['height'] - b['yMin']]
            (good if b['visiblePixels'] >= MIN_PIXELS and min(b['width'], b['height']) >= MIN_SIDE else ignore).append(box)
        rows.append((image, good, ignore, meta))
    if not rows:
        raise SystemExit(f'No frames in {folder}')
    return rows


def load(path):
    with Image.open(path) as encoded:
        return to_tensor(encoded.convert('RGB'))


def target(boxes):
    return {'boxes': torch.tensor(boxes, dtype=torch.float32).reshape(-1, 4),
            'labels': torch.full((len(boxes),), TRUCK, dtype=torch.int64)}


# ---------- candidates ----------------------------------------------------------
def build(candidate):
    from torchvision.models import detection as d
    if candidate == 'A':
        return d.ssdlite320_mobilenet_v3_large(weights=d.SSDLite320_MobileNet_V3_Large_Weights.DEFAULT)
    size = dict(min_size=810, max_size=1440) if candidate == 'C' else dict(min_size=540, max_size=960)
    return d.fasterrcnn_mobilenet_v3_large_fpn(weights=d.FasterRCNN_MobileNet_V3_Large_FPN_Weights.COCO_V1, **size)


def tiles(width, height):
    xs = list(range(0, max(1, width - TILE) + 1, STRIDE_X))
    if xs[-1] != width - TILE:
        xs.append(width - TILE)
    return [(x, y) for y in TILE_Y if y + TILE <= height for x in xs]


def crop_sample(image, boxes, rng):
    """Candidate A training crop: half the time it contains a whole evaluable box."""
    _, height, width = image.shape
    if boxes and rng.random() < .5:
        x0, y0, x1, y1 = rng.choice(boxes)
        left = rng.randint(max(0, int(x1) - TILE), min(width - TILE, int(x0)))
        top = rng.randint(max(0, int(y1) - TILE), min(height - TILE, int(y0)))
    else:
        left, top = rng.randint(0, width - TILE), rng.randint(0, height - TILE)
    kept = []
    for x0, y0, x1, y1 in boxes:
        cx0, cy0, cx1, cy1 = max(x0, left), max(y0, top), min(x1, left + TILE), min(y1, top + TILE)
        if cx1 > cx0 and cy1 > cy0 and (cx1 - cx0) * (cy1 - cy0) >= .6 * (x1 - x0) * (y1 - y0):
            kept.append([cx0 - left, cy0 - top, cx1 - left, cy1 - top])
    return image[:, top:top + TILE, left:left + TILE], kept


def predict(candidate, model, image, device):
    """Truck detections for one full frame: (boxes N×4, scores N), on CPU."""
    model.eval()
    with torch.inference_mode():
        if candidate in ('B', 'C'):
            out = model([image.to(device)])[0]
            keep = out['labels'] == TRUCK
            return out['boxes'][keep].cpu(), out['scores'][keep].cpu()
        _, height, width = image.shape
        boxes, scores = [], []
        positions = tiles(width, height)
        outputs = model([image[:, y:y + TILE, x:x + TILE].to(device) for x, y in positions])
        for (x, y), out in zip(positions, outputs):
            keep = out['labels'] == TRUCK
            boxes.append(out['boxes'][keep].cpu() + torch.tensor([x, y, x, y], dtype=torch.float32))
            scores.append(out['scores'][keep].cpu())
        boxes, scores = torch.cat(boxes), torch.cat(scores)
        if len(scores):
            keep = batched_nms(boxes, scores, torch.zeros_like(scores, dtype=torch.int64), .5)
            boxes, scores = boxes[keep], scores[keep]
        return boxes, scores


def fit_candidate(candidate, train, device, seed=17):
    torch.manual_seed(seed)
    rng = random.Random(seed)
    model = build(candidate).to(device)
    if candidate == 'A':
        model.backbone.requires_grad_(False)
        params = model.head.parameters()
    else:
        params = [p for p in model.parameters() if p.requires_grad]
    budget = BUDGET[candidate]
    optimizer = torch.optim.AdamW(params, lr=budget['lr'])
    history = []
    for epoch in range(budget['epochs']):
        model.train()
        if candidate == 'A':
            model.backbone.eval()
        order = list(range(len(train)))
        rng.shuffle(order)
        losses = []
        for start in range(0, len(order), budget['batch']):
            images, targets = [], []
            for index in order[start:start + budget['batch']]:
                image = load(train[index][0])
                boxes = train[index][1]
                if candidate == 'A':
                    image, boxes = crop_sample(image, boxes, rng)
                images.append(image.to(device))
                targets.append({k: v.to(device) for k, v in target(boxes).items()})
            optimizer.zero_grad(set_to_none=True)
            loss = sum(model(images, targets).values())
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu()))
        history.append(sum(losses) / len(losses))
        print(f'{candidate} epoch {epoch + 1}/{budget["epochs"]}: loss {history[-1]:.4f}', flush=True)
    return model, history


# ---------- scoring --------------------------------------------------------------
def score_frame(boxes, scores, good, ignore, threshold, use_ignore=True):
    keep = scores >= threshold
    boxes, scores = boxes[keep], scores[keep]
    order = torch.argsort(scores, descending=True)
    truth = torch.tensor(good if use_ignore else good + ignore, dtype=torch.float32).reshape(-1, 4)
    skip = torch.tensor(ignore, dtype=torch.float32).reshape(-1, 4) if use_ignore else torch.zeros(0, 4)
    used, tp, fp = set(), 0, 0
    for i in order.tolist():
        box = boxes[i:i + 1]
        ious = box_iou(box, truth)[0] if len(truth) else torch.zeros(0)
        best = max((j for j in range(len(truth)) if j not in used and ious[j] >= .5), key=lambda j: float(ious[j]), default=None)
        if best is not None:
            used.add(best)
            tp += 1
        elif len(skip) and float(box_iou(box, skip).max()) >= .3:
            continue
        else:
            fp += 1
    return tp, fp, len(truth) - len(used)


def summarize(results, threshold):
    out = {}
    for name, use_ignore in (('evaluable', True), ('allBoxes', False)):
        tp = fp = fn = 0
        for boxes, scores, good, ignore, _, _ in results:
            a, b, c = score_frame(boxes, scores, good, ignore, threshold, use_ignore)
            tp, fp, fn = tp + a, fp + b, fn + c
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        out[name] = dict(tp=tp, fp=fp, fn=fn, precision=round(precision, 4), recall=round(recall, 4), f1=round(f1, 4))
    away = [r for r in results if r[4].startswith('away')]
    out['falseDetectionsPerLookAwayFrame'] = round(
        sum(int((r[1] >= threshold).sum()) for r in away) / len(away), 4) if away else None
    out['lookAwayFrames'] = len(away)
    out['meanSecondsPerFrame'] = round(sum(r[5] for r in results) / len(results), 4)
    return out


def evidence(results, rows, threshold):
    """Amendment 1 evidence gate. Ground truth (boxes, route) is used here for scoring only."""
    from backend.camera_evidence import load_capture, locate, on_stand_b
    from experiments.apron_detector.plan import route, tanker_at
    points = route()
    tp = fp = fn = 0
    errors, agree = [], 0
    for (boxes, scores, good, ignore, _, _), (image, _, _, meta) in zip(results, rows):
        if not good and ignore:
            continue  # only ignore-size boxes: left out of presence scoring
        truth = bool(good)
        keep = scores >= threshold
        said = bool(keep.any())
        tp, fp, fn = tp + (said and truth), fp + (said and not truth), fn + (truth and not said)
        if said and truth:
            top = boxes[keep][torch.argmax(scores[keep])].tolist()
            _, depth = load_capture(str(image)[:-4])
            point = locate(meta, depth, top)
            tx, tz = tanker_at(points, meta['sourceTime'])
            errors.append(float('inf') if point is None else ((point[0] - tx) ** 2 + (point[2] - tz) ** 2) ** .5)
            truth_on = 12 <= tx <= 58 and 7 <= tz <= 57
            agree += point is not None and on_stand_b(point) == truth_on
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    within = sum(e <= 8 for e in errors) / len(errors) if errors else 0.0
    stand = agree / len(errors) if errors else 0.0
    ordered = sorted(errors)
    return dict(presence=dict(tp=tp, fp=fp, fn=fn, precision=round(precision, 4), recall=round(recall, 4)),
                location=dict(frames=len(errors), within8m=round(within, 4), standBAgreement=round(stand, 4),
                              medianErrorMetres=round(ordered[len(ordered) // 2], 2) if ordered else None,
                              maxErrorMetres=round(ordered[-1], 2) if ordered else None),
                passed=precision >= .95 and recall >= .80 and within >= .90 and stand >= .95)


def run(candidate, model, rows, device):
    results = []
    for image_path, good, ignore, meta in rows:
        image = load(image_path)
        started = time.monotonic()
        boxes, scores = predict(candidate, model, image, device)
        if device.type == 'mps':
            torch.mps.synchronize()
        results.append((boxes, scores, good, ignore, meta.get('pose', ''), time.monotonic() - started))
    return results


def device_for(candidate):
    return torch.device('mps' if torch.backends.mps.is_available() else 'cpu')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------- commands -------------------------------------------------------------
def fit(args):
    root = Path(args.development)
    if 'heldout' in str(root.resolve()).lower():
        raise SystemExit('fit must not read held-out data')
    train, validation = frames(root / 'train'), frames(root / 'validation')
    args.output.mkdir(parents=True, exist_ok=False)
    report = dict(protocol='experiments/apron_detector/PROTOCOL.md', version='stand-b-detector-v2', seed=17,
                  counts=dict(train=len(train), validation=len(validation),
                              trainEvaluableBoxes=sum(len(r[1]) for r in train),
                              validationEvaluableBoxes=sum(len(r[1]) for r in validation)),
                  torch=torch.__version__, candidates={})
    for candidate in args.candidates:
        device = device_for(candidate)
        started = time.monotonic()
        model, history = fit_candidate(candidate, train, device)
        fit_seconds = time.monotonic() - started
        results = run(candidate, model, validation, device)
        grid = {t: summarize(results, t)['evaluable'] for t in THRESHOLDS}
        threshold = max(THRESHOLDS, key=lambda t: (grid[t]['f1'], t))
        torch.save(model.state_dict(), args.output / f'candidate-{candidate}.pt')
        report['candidates'][candidate] = dict(device=device.type, budget=BUDGET[candidate], losses=history,
                                               validationEvidence=evidence(results, validation, threshold),
                                               fitSeconds=round(fit_seconds, 1), threshold=threshold,
                                               validation=summarize(results, threshold),
                                               validationGrid={str(t): grid[t] for t in THRESHOLDS},
                                               weightsSha256=sha(args.output / f'candidate-{candidate}.pt'))
        print(candidate, 'threshold', threshold, report['candidates'][candidate]['validation']['evaluable'], flush=True)
    for spec in args.carry:
        # Reuse an already fitted candidate unchanged: same weights, same recorded validation results.
        name, folder = spec.split('=', 1)
        earlier = json.loads((Path(folder) / 'fit-report.json').read_text())['candidates'][name]
        source = Path(folder) / f'candidate-{name}.pt'
        if sha(source) != earlier['weightsSha256']:
            raise SystemExit(f'Carried weights for {name} changed')
        (args.output / f'candidate-{name}.pt').write_bytes(source.read_bytes())
        device = device_for(name)
        model = build(name)
        model.load_state_dict(torch.load(source, map_location='cpu'))
        model.to(device)
        results = run(name, model, validation, device)
        if summarize(results, earlier['threshold'])['evaluable'] != earlier['validation']['evaluable']:
            raise SystemExit(f'Carried candidate {name} does not reproduce its validation result')
        report['candidates'][name] = dict(earlier, carriedFrom=folder,
                                          validationEvidence=evidence(results, validation, earlier['threshold']))
        print(name, 'carried; validation reproduced', flush=True)
    scored = report['candidates']
    report['selected'] = max(scored, key=lambda c: (scored[c]['validation']['evaluable']['f1'],
                                                   scored[c]['validation']['evaluable']['precision']))
    (args.output / 'fit-report.json').write_text(json.dumps(report, indent=1) + '\n')
    print('selected', report['selected'])


def manifest(args):
    root = Path(args.heldout)
    files = sorted(p for p in root.rglob('*') if p.is_file())
    if not files:
        raise SystemExit('No held-out files')
    body = dict(version='stand-b-detector-v2', split='heldout', frozenUtc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                files={str(p.relative_to(root)): sha(p) for p in files},
                frames=len(list(root.rglob('*.json'))) - (1 if (root / 'capture-summary.json').exists() else 0))
    with args.output.open('x') as stream:
        json.dump(body, stream, indent=1)
    print('frozen', len(files), 'files ->', args.output)


def evaluate(args):
    if args.output.exists():
        raise SystemExit('The held-out evaluation has already been run; it is not repeated.')
    frozen = json.loads(Path(args.manifest).read_text())['files']
    root = Path(args.heldout)
    present = {str(p.relative_to(root)): sha(p) for p in root.rglob('*') if p.is_file()}
    if present != frozen:
        raise SystemExit('Held-out files do not match the frozen manifest')
    fit_report = json.loads((Path(args.fit) / 'fit-report.json').read_text())
    candidate = fit_report['selected']
    chosen = fit_report['candidates'][candidate]
    weights = Path(args.fit) / f'candidate-{candidate}.pt'
    if sha(weights) != chosen['weightsSha256']:
        raise SystemExit('Selected weights changed after fitting')
    # Write the claim first, so a crash cannot be quietly retried.
    args.output.write_text(json.dumps(dict(status='started', candidate=candidate), indent=1) + '\n')
    device = device_for(candidate)
    model = build(candidate)
    model.load_state_dict(torch.load(weights, map_location='cpu'))
    model.to(device)
    rows = frames(root / 'heldout')
    results = run(candidate, model, rows, device)
    summary = summarize(results, chosen['threshold'])
    gate = summary['evaluable']['precision'] >= .90 and summary['evaluable']['recall'] >= .70
    record = dict(status='complete', protocol='experiments/apron_detector/PROTOCOL.md', candidate=candidate,
                  threshold=chosen['threshold'], frames=len(rows), evaluableBoxes=sum(len(r[1]) for r in rows),
                  heldout=summary, qualificationGate=dict(precisionAtLeast=.90, recallAtLeast=.70, passed=gate),
                  manifestSha256=sha(args.manifest), weightsSha256=chosen['weightsSha256'])
    if args.evidence_gate:
        record['boxGate'] = record.pop('qualificationGate')
        record['evidenceGate'] = evidence(results, rows, chosen['threshold'])
        record['qualifiedAsCameraEvidence'] = record['evidenceGate']['passed']
        record['amendment'] = 'PROTOCOL.md amendment 1'
    args.output.write_text(json.dumps(record, indent=1) + '\n')
    print(json.dumps(record['heldout']['evaluable']), 'box gate passed' if gate else 'box gate FAILED')
    if args.evidence_gate:
        print(json.dumps(record['evidenceGate']))


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = cli.add_subparsers(dest='command', required=True)
    f = sub.add_parser('fit')
    f.add_argument('development', type=Path)
    f.add_argument('output', type=Path)
    f.add_argument('--candidates', nargs='*', default=['A', 'B'], choices=['A', 'B', 'C'])
    f.add_argument('--carry', nargs='*', default=[], help='NAME=FIT_FOLDER: reuse a fitted candidate unchanged')
    m = sub.add_parser('manifest')
    m.add_argument('heldout', type=Path)
    m.add_argument('output', type=Path)
    e = sub.add_parser('evaluate')
    e.add_argument('fit', type=Path)
    e.add_argument('heldout', type=Path)
    e.add_argument('manifest', type=Path)
    e.add_argument('output', type=Path)
    e.add_argument('--evidence-gate', action='store_true', help='Amendment 1: also score the evidence gate')
    args = cli.parse_args()
    dict(fit=fit, manifest=manifest, evaluate=evaluate)[args.command](args)


if __name__ == '__main__':
    main()
