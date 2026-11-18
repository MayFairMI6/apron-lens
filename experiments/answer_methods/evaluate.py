"""Score five ways of answering a question: direct inference, model-written Python run in a
sandbox (PAL-style), and model choice, model-written query or keywords turned into a query
that code answers.

    python -m experiments.answer_methods.evaluate --dataset apron --split dev --model qwen2.5-vl-3b \\
        --device cpu --dtype float16 --attn eager --output work/answer-methods/p1

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

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from backbone import PRIMARY_MODEL, load_engine, model_names
from backend.evidence import build_context, expected_selection
from experiments.answer_methods.direct import answer_directly
from experiments.answer_methods.pal import answer_with_program
from experiments.answer_methods.parser import VERSION, keyword_parse, parse, parse_generated
from experiments.answer_methods.scenarios import TOWER_ID, load as load_scenario

DATASETS = {'apron': HERE / 'data/apron', 'tower': HERE / 'data/tower'}
# Scenario, aircraft and replay time each dataset's questions are asked about. Both aircraft's
# reports are in the scenario, so direct inference must also pick the right flight.
REPLAY = {'apron': ('M1-stand-coordination-01', 'A2', 20.0), 'tower': (TOWER_ID, 'A1', 50.0)}


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


METHODS = ('choice', 'generated', 'direct', 'pal')


def score(rows, key):
    rows = [r for r in rows if key in r['queries']]
    answered = [r for r in rows if r['queries'][key] is not None]
    exact = sum(r['queries'][key] == r['gold'] for r in answered)
    types = sum(r['queries'][key]['queryType'] == r['gold']['queryType'] for r in answered)
    props = sum(r['queries'][key]['properties'] == r['gold']['properties'] for r in answered)
    return dict(exact=exact, queryType=types, properties=props, invalid=len(rows) - len(answered), total=len(rows))


def answer_score(rows, key):
    rows = [r for r in rows if key in r['answers']]
    return dict(exact=sum(r['answers'][key] == r['answers']['gold'] for r in rows),
                invalid=sum(r['answers'][key] is None for r in rows), total=len(rows))


def timed(fn, *args):
    started = time.perf_counter()
    result = fn(*args)
    return result, round(time.perf_counter() - started, 3)


def run(dataset, split, model, output, runtime, methods=METHODS, resume=False):
    """runtime: dict(device=..., dtype=..., attn_implementation=...), recorded with the results."""
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    target = output / 'results.jsonl'
    if target.exists() and not resume:
        raise ValueError('Output already exists. Choose a new output directory, or --resume an interrupted run.')
    # --resume keeps every recorded answer and asks only the questions not yet answered.
    rows = [json.loads(line) for line in target.read_text().splitlines()] if target.exists() else []
    done = {r['id'] for r in rows}
    items = load(dataset, split)
    scenario_id, aircraft, checkpoint = REPLAY[dataset]
    data = load_scenario(scenario_id)
    engine = load_engine(model, **runtime)
    for item in items:
        if item['id'] in done:
            continue
        question = item['question']
        row = dict(id=item['id'], question=question, queries={}, answers={}, errors={}, raw={}, seconds={})
        if 'choice' in methods:
            parsed, row['seconds']['choice'] = timed(parse, engine, question, dataset)
            row['queries']['choice'] = {k: parsed[k] for k in ('queryType', 'properties')}
            row['trace'] = parsed['trace']
        if 'generated' in methods:
            generated, row['seconds']['generated'] = timed(parse_generated, engine, question, dataset)
            row['queries']['generated'] = generated['query']
            row['errors']['generated'], row['raw']['generated'] = generated['error'], generated['raw']
        keyword = keyword_parse(question, dataset)
        row['queries']['keyword'] = {k: keyword[k] for k in ('queryType', 'properties')}
        for name, query in row['queries'].items():
            row['answers'][name] = answer_for(data, aircraft, checkpoint, query)
        for name, fn in (('direct', answer_directly), ('pal', answer_with_program)):
            if name in methods:
                result, row['seconds'][name] = timed(fn, engine, data, aircraft, checkpoint, question)
                row['answers'][name] = result['answer']
                row['errors'][name], row['raw'][name] = result['error'], result['raw']
        # Gold is read only after every method has answered.
        row['gold'] = {k: item[k] for k in ('queryType', 'properties')}
        row['answers']['gold'] = answer_for(data, aircraft, checkpoint, row['gold'])
        rows.append(row)
        with target.open('a') as stream:
            stream.write(json.dumps(row) + '\n')
        print(item['id'], ' '.join(f"{k}:{'ok' if v == row['answers']['gold'] else (row['errors'].get(k) or 'miss')}"
                                    for k, v in row['answers'].items() if k != 'gold'), flush=True)
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True)
    run_methods = [m for m in METHODS if m in methods] + ['keyword']
    summary = dict(dataset=dataset, split=split, replay=dict(scenario=scenario_id, aircraft=aircraft, checkpoint=checkpoint),
                   methods=run_methods, parserVersion=VERSION, modelName=model, model=engine.manifest, device=engine.device,
                   runtime=runtime,
                   transformers=package_version('transformers'), python=platform.python_version(),
                   recordedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   commit=commit.stdout.strip() if commit.returncode == 0 else None,
                   sources={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                            for p in ('experiments/answer_methods/parser.py', 'experiments/answer_methods/direct.py',
                                      'experiments/answer_methods/pal.py', 'experiments/answer_methods/scenarios.py',
                                      'backbone/engine.py', f'{DATASETS[dataset].relative_to(ROOT)}/manifest.json')},
                   queryScore={m: score(rows, m) for m in run_methods if m in ('choice', 'generated', 'keyword')},
                   answerScore={m: answer_score(rows, m) for m in run_methods},
                   medianSeconds={m: sorted(r['seconds'][m] for r in rows)[len(rows) // 2] for m in run_methods if m != 'keyword'})
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: summary[k] for k in ('dataset', 'split', 'modelName', 'runtime', 'queryScore', 'answerScore', 'medianSeconds')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dataset', choices=tuple(DATASETS), default='apron')
    parser.add_argument('--split', choices=('dev', 'test'), required=True)
    parser.add_argument('--model', choices=model_names(), default=PRIMARY_MODEL)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--methods', default=','.join(METHODS), help='comma-separated subset of ' + ','.join(METHODS))
    parser.add_argument('--resume', action='store_true', help='continue an interrupted run in the same output directory')
    parser.add_argument('--device', choices=('cpu', 'mps', 'cuda'), required=True)
    parser.add_argument('--dtype', choices=('float16', 'bfloat16', 'float32'), required=True)
    parser.add_argument('--attn', choices=('eager', 'sdpa'), required=True)
    args = parser.parse_args()
    methods = tuple(args.methods.split(','))
    if not set(methods) <= set(METHODS):
        parser.error('unknown method')
    run(args.dataset, args.split, args.model, args.output,
        dict(device=args.device, dtype=args.dtype, attn_implementation=args.attn), methods, args.resume)
