"""Score question-to-query parsing: the model parser against the keyword baseline.

    python scripts/evaluate_query_parsing.py --split dev --model qwen2.5-vl-3b --output work/parse-dev-3b
    python scripts/evaluate_query_parsing.py --split test --model qwen3-vl-4b --output work/parse-test-4b

The dataset hashes must match data/query_parsing_v1/manifest.json. Gold labels are
read only after both parsers have answered. No run is overwritten.
"""
import argparse
import datetime
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.models import PRIMARY_MODEL, model_names
from backend.query_parser import VERSION, keyword_parse, parse

DATA = ROOT / 'data/query_parsing_v1'


def load(split):
    manifest = json.loads((DATA / 'manifest.json').read_text())
    path = DATA / f'{split}.json'
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['files'][f'{split}.json']:
        raise ValueError(f'{split}.json differs from its frozen hash')
    return json.loads(path.read_text())


def score(rows, key):
    exact = sum(r[key]['queryType'] == r['gold']['queryType'] and r[key]['properties'] == r['gold']['properties'] for r in rows)
    types = sum(r[key]['queryType'] == r['gold']['queryType'] for r in rows)
    props = sum(r[key]['properties'] == r['gold']['properties'] for r in rows)
    return dict(exact=exact, queryType=types, properties=props, total=len(rows))


def run(split, model, output):
    from backend.engine import load_engine
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    target = output / 'results.jsonl'
    if target.exists():
        raise ValueError('Output already exists. Choose a new output directory; no run is overwritten.')
    items = load(split)
    engine = load_engine(model)
    rows = []
    for item in items:
        started = time.perf_counter()
        parsed = parse(engine, item['question'])
        seconds = round(time.perf_counter() - started, 3)
        keyword = keyword_parse(item['question'])
        row = dict(id=item['id'], question=item['question'], seconds=seconds,
                   model={k: parsed[k] for k in ('queryType', 'properties')}, keyword=keyword, trace=parsed['trace'],
                   gold={k: item[k] for k in ('queryType', 'properties')})
        rows.append(row)
        with target.open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        ok = row['model'] == row['gold']
        print(item['id'], 'model', 'ok' if ok else f"{row['model']} != {row['gold']}", flush=True)
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    summary = dict(split=split, method=VERSION, modelName=model, model=engine.manifest, device=engine.device,
                   dtype=str(engine.dtype).removeprefix('torch.'),
                   transformers=importlib.metadata.version('transformers'), python=platform.python_version(),
                   recordedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   commit=commit.stdout.strip() if commit.returncode == 0 else None,
                   sources={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                            for p in ('backend/query_parser.py', 'backend/engine.py', 'data/query_parsing_v1/manifest.json')},
                   modelScore=score(rows, 'model'), keywordScore=score(rows, 'keyword'),
                   medianSeconds=sorted(r['seconds'] for r in rows)[len(rows) // 2])
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: summary[k] for k in ('modelName', 'dtype', 'modelScore', 'keywordScore', 'medianSeconds')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--split', choices=('dev', 'test'), required=True)
    parser.add_argument('--model', choices=model_names(), default=PRIMARY_MODEL)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.split, args.model, args.output)
