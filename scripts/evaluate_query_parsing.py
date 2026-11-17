"""Score four ways of answering a question: direct inference, and model choice, model-written
query or keywords turned into a query that code answers.

    python scripts/evaluate_query_parsing.py --dataset apron --split dev --model qwen2.5-vl-3b --output work/p1
    python scripts/evaluate_query_parsing.py --dataset tower --split test --model qwen3-vl-4b --output work/p2

Each question is answered at one fixed replay moment per dataset (REPLAY). The gold
answer is what the rules return for the labelled query; every method is scored on
its parsed query (where it has one) and on the final answer. The dataset hashes must
match its manifest.json. Gold labels are read only after every method has answered.
No run is overwritten.
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
from backend.direct_answer import answer_directly
from backend.evidence import build_context, expected_selection, load_scenario
from backend.query_parser import VERSION, keyword_parse, parse, parse_generated

DATASETS = {'apron': ROOT / 'data/query_parsing_v1', 'tower': ROOT / 'data/query_parsing_tower_v1'}
# Scenario, aircraft and replay time each dataset's questions are asked about. Both aircraft's
# reports are in the scenario, so direct inference must also pick the right flight.
REPLAY = {'apron': ('M1-stand-coordination-01', 'A2', 20.0), 'tower': ('T1-tower-clearances-01', 'A1', 50.0)}


def answer_for(data, aircraft, checkpoint, query):
    """What the rules return for a query: the fact ids and unknown properties."""
    if query is None:
        return None
    try:
        selected = expected_selection(build_context(data, aircraft, checkpoint, query['queryType'], query['properties']))
    except ValueError:
        return None
    return dict(fact_ids=sorted(c['fact_id'] for c in selected['claims']), unknown=sorted(selected['unknown_properties']))


def package_version(name):
    """Installed version, or None where the package is absent (e.g. CI with a test double)."""
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def load(dataset, split):
    data = DATASETS[dataset]
    manifest = json.loads((data / 'manifest.json').read_text())
    path = data / f'{split}.json'
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['files'][f'{split}.json']:
        raise ValueError(f'{split}.json differs from its frozen hash')
    return json.loads(path.read_text())


def score(rows, key):
    answered = [r for r in rows if r[key] is not None]
    exact = sum(r[key]['queryType'] == r['gold']['queryType'] and r[key]['properties'] == r['gold']['properties'] for r in answered)
    types = sum(r[key]['queryType'] == r['gold']['queryType'] for r in answered)
    props = sum(r[key]['properties'] == r['gold']['properties'] for r in answered)
    return dict(exact=exact, queryType=types, properties=props, invalid=len(rows) - len(answered), total=len(rows))


def answer_score(rows, key):
    return dict(exact=sum(r['answers'][key] == r['answers']['gold'] for r in rows),
                invalid=sum(r['answers'][key] is None for r in rows), total=len(rows))


def run(dataset, split, model, output):
    from backend.engine import load_engine
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    target = output / 'results.jsonl'
    if target.exists():
        raise ValueError('Output already exists. Choose a new output directory; no run is overwritten.')
    items = load(dataset, split)
    scenario_id, aircraft, checkpoint = REPLAY[dataset]
    data = load_scenario(scenario_id)
    engine = load_engine(model)
    rows = []
    for item in items:
        started = time.perf_counter()
        parsed = parse(engine, item['question'], dataset)
        seconds = round(time.perf_counter() - started, 3)
        started = time.perf_counter()
        generated = parse_generated(engine, item['question'], dataset)
        generated_seconds = round(time.perf_counter() - started, 3)
        keyword = keyword_parse(item['question'], dataset)
        started = time.perf_counter()
        direct = answer_directly(engine, data, aircraft, checkpoint, item['question'])
        direct_seconds = round(time.perf_counter() - started, 3)
        queries = dict(choice={k: parsed[k] for k in ('queryType', 'properties')}, generated=generated['query'],
                       keyword={k: keyword[k] for k in ('queryType', 'properties')})
        answers = {name: answer_for(data, aircraft, checkpoint, q) for name, q in queries.items()}
        answers['direct'] = direct['answer']
        row = dict(id=item['id'], question=item['question'], seconds=seconds, generatedSeconds=generated_seconds,
                   directSeconds=direct_seconds, directRaw=direct['raw'], directError=direct['error'],
                   model={k: parsed[k] for k in ('queryType', 'properties')}, trace=parsed['trace'],
                   generated=generated['query'], generatedRaw=generated['raw'], generatedError=generated['error'],
                   keyword={k: keyword[k] for k in ('queryType', 'properties')},
                   gold={k: item[k] for k in ('queryType', 'properties')})
        answers['gold'] = answer_for(data, aircraft, checkpoint, row['gold'])
        row['answers'] = answers
        rows.append(row)
        with target.open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        print(item['id'], 'choice', 'ok' if row['model'] == row['gold'] else 'miss',
              'generated', 'ok' if row['generated'] == row['gold'] else (generated['error'] or 'miss'),
              'direct', 'ok' if answers['direct'] == answers['gold'] else (direct['error'] or 'miss'), flush=True)
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    summary = dict(dataset=dataset, split=split, replay=dict(scenario=scenario_id, aircraft=aircraft, checkpoint=checkpoint),
                   method=VERSION, modelName=model, model=engine.manifest, device=engine.device,
                   dtype=str(engine.dtype).removeprefix('torch.'),
                   transformers=package_version('transformers'), python=platform.python_version(),
                   recordedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   commit=commit.stdout.strip() if commit.returncode == 0 else None,
                   sources={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                            for p in ('backend/query_parser.py', 'backend/direct_answer.py', 'backend/engine.py',
                                      f'{DATASETS[dataset].relative_to(ROOT)}/manifest.json')},
                   modelScore=score(rows, 'model'), generatedScore=score(rows, 'generated'), keywordScore=score(rows, 'keyword'),
                   answerScore={k: answer_score(rows, k) for k in ('direct', 'choice', 'generated', 'keyword')},
                   medianSeconds=sorted(r['seconds'] for r in rows)[len(rows) // 2],
                   medianGeneratedSeconds=sorted(r['generatedSeconds'] for r in rows)[len(rows) // 2],
                   medianDirectSeconds=sorted(r['directSeconds'] for r in rows)[len(rows) // 2])
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: summary[k] for k in ('dataset', 'split', 'modelName', 'dtype', 'modelScore', 'generatedScore', 'keywordScore', 'answerScore',
                                         'medianSeconds', 'medianGeneratedSeconds', 'medianDirectSeconds')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dataset', choices=tuple(DATASETS), default='apron')
    parser.add_argument('--split', choices=('dev', 'test'), required=True)
    parser.add_argument('--model', choices=model_names(), default=PRIMARY_MODEL)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.dataset, args.split, args.model, args.output)
