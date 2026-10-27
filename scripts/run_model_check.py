"""Append-free development check. Never reads the fresh/held-out question sets."""
import argparse
import datetime
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def run(suite, output):
    from backend.server import LocalQwen
    from backend.decisions import select_claims, VERSION
    from backend.evidence import build_context, load_scenario, expected_selection
    from backend.reasoning import normalized_claims, validate_answer
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    target = output / 'results.jsonl'
    if target.exists():
        raise ValueError('Output already exists. Choose a new output directory; no run is overwritten.')
    if suite == 'dev':
        queries = [q for q in json.loads((ROOT / 'data/reasoning_v1/queries.json').read_text()) if q['split'] == 'dev']
    else:
        queries = [dict(id=f'M1-{t}', scenarioId='M1-stand-coordination-01', aircraftId='A2', checkpoint=t, queryType='latest', properties=[]) for t in (13, 14)]
    engine = LocalQwen()
    pinned = json.loads((ROOT / 'config/model-manifest.json').read_text())
    if engine.manifest != pinned:
        raise ValueError('Loaded model does not match the pinned model manifest')
    rows = []
    for q in queries:
        context = build_context(load_scenario(q['scenarioId']), q['aircraftId'], q['checkpoint'], q['queryType'], q['properties'])
        started = time.perf_counter()
        # Gold and deterministic baseline are evaluated only after model inference.
        raw, trace = select_claims(engine, context)
        parsed = json.loads(raw)
        baseline = expected_selection(context)
        gold = q.get('gold', baseline)
        exact = normalized_claims(parsed) == normalized_claims(gold) and set(parsed['unknown_properties']) == set(gold['unknown_properties'])
        baseline_exact = normalized_claims(baseline) == normalized_claims(gold) and set(baseline['unknown_properties']) == set(gold['unknown_properties'])
        guard = validate_answer(raw, context)
        row = dict(id=q['id'], raw=raw, trace=trace, exact=exact, baselineExact=baseline_exact,
                   guardStatus=guard['resultStatus'], seconds=round(time.perf_counter()-started, 4))
        rows.append(row)
        with target.open('a') as stream:
            stream.write(json.dumps(row)+'\n')
        print(q['id'], 'raw exact:', exact, 'baseline:', baseline_exact, 'guard:', guard['resultStatus'], flush=True)
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    sources = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in ('backend/decisions.py','backend/evidence.py','backend/server.py')}
    result = dict(suite=suite, purpose='Development regression; not fresh held-out evidence',
                  recordedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  commit=commit.stdout.strip() if commit.returncode == 0 else None,
                  method=VERSION, model=engine.manifest, device=engine.device, python=platform.python_version(),
                  sources=sources, total=len(rows), rawExact=sum(r['exact'] for r in rows),
                  deterministicExact=sum(r['baselineExact'] for r in rows), guardAccepted=sum(r['guardStatus']=='generated' for r in rows))
    (output / 'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    # Scores are research observations, not a gate encouraging answer-specific tuning.


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=('smoke','dev'), default='smoke')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.suite, args.output)
