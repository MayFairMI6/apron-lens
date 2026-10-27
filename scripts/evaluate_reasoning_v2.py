"""Frozen fresh evaluation: no dataset parsing until --run, no retried attempts.

The deterministic answer baseline is scored separately and never supplied to
select_claims. This runner reads gold only for scoring after each model call.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SUITE = ROOT / 'data/reasoning_v2_fresh'
OUT = ROOT / 'outputs/reasoning_v2'
EXPECTED_SUITE_SHA = 'c8e85ec2b1deffe626220c7af526f7f2b9789558a69bc260336531c9c49ca36c'
CONDITIONS = ['legacy_state_text', 'decisions_state_text',
              'decisions_unfiltered_text', 'decisions_state_image']
BASELINE = 'deterministic_baseline'
LEGACY = 'outputs/reasoning_v1/source_snapshot/backend/reasoning.py'
SOURCES = ['backend/evidence.py', 'backend/reasoning.py', 'backend/decisions.py',
           'backend/server.py', 'scripts/evaluate_reasoning_v2.py',
           'scripts/report_reasoning_v2.py', 'requirements-qwen.lock.txt', LEGACY]
CONFIG = dict(questionCount=32, conditions=CONDITIONS, baseline=BASELINE,
              split='heldout_fresh', developmentTrials=5, developmentSmokeQueries=2,
              legacyDecoding=dict(do_sample=False, max_new_tokens=512),
              order='Rotate four model conditions left by question index modulo four',
              retries=0, resume='Only never-started calls; interrupted attempts count as failures',
              expectedSuiteManifestSha256=EXPECTED_SUITE_SHA)
CAVEATS = [
    'Synthetic scenario-family pilot; no domain-expert validation or real-airfield outcome evidence.',
    'Qwen selects literal predicates. Temporal statuses are supplied by a deterministic resolver.',
    'Values, status labels, and citations are projected from selected records by construction.',
    'Unknown flags compose model membership/current decisions; empty evidence needs no model call.',
    'High hybrid accuracy does not prove learned temporal reasoning or benefit over the deterministic baseline.',
    'The image is a non-diagnostic negative control, not evidence of visual reasoning.',
    'The unfiltered condition is an identity-filtering stress diagnostic, not a matched-token causal comparison.',
    'The guard uses the deterministic answer contract; withholding never earns raw accuracy credit.',
    'Five development trials plus two real-Unity M1 development smoke queries; fresh suite unopened until run.',
    'Pairwise receipt comparisons cache repeated numeric pairs, so predicate compute budgets vary by query.',
    'Family-cluster comparisons are descriptive only; correlated questions are not independent samples.',
]


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def bounded_path(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Path escapes declared root')
    return path


def check_suite():
    """Read only manifest metadata; hash data bytes without decoding questions."""
    manifest_path = SUITE / 'manifest.json'
    if digest(manifest_path) != EXPECTED_SUITE_SHA:
        raise RuntimeError('Fresh suite manifest differs from independently recorded hash')
    manifest = json.loads(manifest_path.read_text())
    for name, sha in manifest['files'].items():
        if digest(bounded_path(SUITE, name)) != sha:
            raise RuntimeError('Dataset integrity failure: ' + name)
    if 'queries.json' not in manifest['files']:
        raise RuntimeError('Manifest must cover queries.json')
    return manifest


def source_hashes():
    return {name: digest(ROOT / name) for name in SOURCES}


def freeze():
    # Deliberately no dataset loaders, model imports, or questions/gold parsing.
    check_suite()
    model_path = ROOT / 'models/Qwen2.5-VL-3B-Instruct/download-manifest.json'
    protocol = dict(createdUTC=utc(), config=CONFIG, sources=source_hashes(),
                    modelManifest=json.loads(model_path.read_text()),
                    modelManifestSha256=digest(model_path), caveats=CAVEATS,
                    primary='Raw exact claim/value/status/citation set AND unknown-property set',
                    scoring='All attempted calls included, including malformed/interrupted/error outputs')
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'protocol.json'
    if target.exists() or (OUT / 'source_snapshot').exists():
        raise RuntimeError('Frozen version exists; never overwrite or tune this version')
    for name in SOURCES:
        dst = OUT / 'source_snapshot' / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes((ROOT / name).read_bytes())
    with target.open('x') as stream:
        json.dump(protocol, stream, indent=2)
        stream.write('\n')
    print('FROZEN', digest(target), flush=True)


def verify_protocol():
    protocol_path = OUT / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    if protocol['config'] != CONFIG or protocol['sources'] != source_hashes():
        raise RuntimeError('Frozen source/config changed; do not retry or rescore this version')
    model_path = ROOT / 'models/Qwen2.5-VL-3B-Instruct/download-manifest.json'
    if digest(model_path) != protocol['modelManifestSha256']:
        raise RuntimeError('Model manifest changed after freeze')
    for name, sha in protocol['sources'].items():
        if digest(OUT / 'source_snapshot' / name) != sha:
            raise RuntimeError('Frozen source snapshot changed: ' + name)
    manifest = check_suite()
    return protocol, digest(protocol_path), manifest


def score(raw, context, gold, scenario):
    from backend.reasoning import parse_claims, normalized_claims, validate_answer
    counts = ['claims', 'correct_claims', 'invented_fact_id', 'unavailable_fact_id',
              'wrong_identity', 'wrong_status', 'wrong_value', 'wrong_citation', 'supported_citations']
    metrics = {key: 0 for key in counts}
    metrics.update(json_valid=False, exact=False, unknown_exact=False,
                   gold_claims=len(gold['claims']), has_missing_evidence=bool(gold['unknown_properties']))
    selected = {f['fact_id']: f for f in context['facts']}
    received = {f['fact_id']: f for f in context['receivedFacts']}
    all_ids = {e['id'] + ':' + f['property'] for e in scenario['events'] for f in e['facts']}
    try:
        parsed = parse_claims(raw)
        metrics['json_valid'] = True
        metrics['claims'] = len(parsed['claims'])
        metrics['unknown_exact'] = set(parsed['unknown_properties']) == set(gold['unknown_properties'])
        gold_atoms = set(normalized_claims(gold))
        metrics['exact'] = normalized_claims(parsed) == normalized_claims(gold) and metrics['unknown_exact']
        for claim in parsed['claims']:
            atom = normalized_claims({'claims': [claim]})[0]
            metrics['correct_claims'] += atom in gold_atoms
            fid = claim['fact_id']
            if fid not in all_ids:
                metrics['invented_fact_id'] += 1
                continue
            if fid not in received:
                metrics['unavailable_fact_id'] += 1
                continue
            if fid not in selected:
                metrics['wrong_identity'] += 1
                continue
            fact = selected[fid]
            value_ok = claim['value'] == fact['value']
            citation_ok = claim['evidence_ids'] == [fact['event_id']]
            metrics['wrong_status'] += claim['status'] != fact['status']
            metrics['wrong_value'] += not value_ok
            metrics['wrong_citation'] += not citation_ok
            metrics['supported_citations'] += value_ok and citation_ok
    except (ValueError, TypeError, KeyError):
        pass
    guarded = validate_answer(raw, context)
    metrics['guard_accepted'] = guarded['resultStatus'] == 'generated'
    metrics['guard_accepted_incorrect'] = metrics['guard_accepted'] and not metrics['exact']
    metrics['guard_errors'] = guarded['validationErrors']
    return metrics, guarded


def read_journal(path):
    if not path.exists():
        return []
    # Refuse truncated/corrupt journals instead of silently discarding an attempt.
    return [json.loads(line) for line in path.read_text().splitlines()]


def append(path, row):
    with path.open('a') as stream:
        stream.write(json.dumps(row, allow_nan=False) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def legacy_prompt():
    spec = importlib.util.spec_from_file_location('frozen_v1_reasoning_prompt', ROOT / LEGACY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.prompt_for


def run(resume=False):
    protocol, protocol_sha, manifest = verify_protocol()
    run_path, attempts_path = OUT / 'fresh-runs.jsonl', OUT / 'attempts.jsonl'
    if not resume and (run_path.exists() or attempts_path.exists()):
        raise RuntimeError('Run already started; --resume only runs never-started calls')
    # The first permitted decode of fresh cases happens after verified freeze.
    queries = json.loads((SUITE / 'queries.json').read_text())
    if len(queries) != CONFIG['questionCount'] or len({q['id'] for q in queries}) != len(queries):
        raise RuntimeError('Question count or unique-ID mismatch')
    if any(q['split'] != CONFIG['split'] for q in queries):
        raise RuntimeError('Unexpected split in fresh suite')
    expected_keys = {(q['id'], c) for q in queries for c in CONDITIONS + [BASELINE]}
    previous, attempts = read_journal(run_path), read_journal(attempts_path)
    for records in (previous, attempts):
        keys = [(r['questionId'], r['condition']) for r in records]
        if len(keys) != len(set(keys)) or not set(keys).issubset(expected_keys):
            raise RuntimeError('Duplicate or unexpected journal key')
        if any(r['protocolSha256'] != protocol_sha for r in records):
            raise RuntimeError('Journal/protocol mismatch')
    done = {(r['questionId'], r['condition']) for r in previous}
    started = {(r['questionId'], r['condition']) for r in attempts}
    if not done.issubset(started):
        raise RuntimeError('Result exists without recorded attempt')
    from backend.evidence import build_context, validate_scenario, expected_selection
    from backend.decisions import select_claims
    from backend.server import LocalQwen
    from PIL import Image
    make_legacy_prompt = legacy_prompt()
    pending_model = any((q['id'], c) not in done | started for q in queries for c in CONDITIONS)
    engine = LocalQwen() if pending_model else None  # Startup is outside per-call timing.
    for index, query in enumerate(queries):
        rel = 'scenarios/' + query['scenarioId'] + '.json'
        if rel not in manifest['files'] or query['image'] not in manifest['files']:
            raise RuntimeError('Question references unmanifested input')
        scenario = validate_scenario(json.loads(bounded_path(SUITE, rel).read_text()))
        context = build_context(scenario, query['aircraftId'], query['checkpoint'],
                                query['queryType'], query['properties'])
        offset = index % len(CONDITIONS)
        order = CONDITIONS[offset:] + CONDITIONS[:offset] + [BASELINE]
        for condition in order:
            key = query['id'], condition
            if key in done:
                continue
            interrupted = key in started
            if not interrupted:
                append(attempts_path, dict(questionId=query['id'], condition=condition,
                                           protocolSha256=protocol_sha, startedUTC=utc()))
            raw, prompt, trace, error = '', None, {}, None
            start = time.perf_counter()
            if interrupted:
                error = 'Interrupted attempt: output unavailable; deliberately not retried'
            else:
                try:
                    if condition == BASELINE:
                        raw = json.dumps(expected_selection(context))
                        trace = dict(inputTokens=0, outputTokens=0, forwardPasses=0)
                    else:
                        if condition == 'legacy_state_text':
                            prompt = make_legacy_prompt(context, query['question'], 'state_aware')
                            raw, inputs, outputs = engine.generate(prompt, None)
                            trace = dict(inputTokens=inputs, outputTokens=outputs, forwardPasses=outputs,
                                         forwardPassesNote='Derived from greedy generated-token count, including EOS')
                        else:
                            image = None
                            if condition == 'decisions_state_image':
                                with Image.open(bounded_path(SUITE, query['image'])) as original:
                                    image = original.convert('RGB')
                            raw, trace = select_claims(engine, context, image=image,
                                                      unfiltered=condition == 'decisions_unfiltered_text')
                except Exception as exc:
                    error = f'{type(exc).__name__}: {exc}'
            elapsed = None if interrupted else round(time.perf_counter() - start, 4)
            # Freeze raw output before parsing gold or invoking the separate guard.
            raw_sha = hashlib.sha256(raw.encode()).hexdigest()
            metrics, guarded = score(raw, context, query['gold'], scenario)
            row = dict(questionId=query['id'], scenarioId=query['scenarioId'], family=query['family'],
                       condition=condition, split=query['split'], queryType=query['queryType'],
                       checkpoint=query['checkpoint'], properties=query['properties'],
                       protocolSha256=protocol_sha, model=protocol['modelManifest'],
                       device=engine.device if engine is not None and condition != BASELINE else None,
                       python=platform.python_version(), raw=raw, rawSha256=raw_sha, prompt=prompt,
                       promptSha256=hashlib.sha256(prompt.encode()).hexdigest() if prompt is not None else None,
                       trace=trace, inputTokens=trace.get('inputTokens'), outputTokens=trace.get('outputTokens'),
                       forwardPasses=trace.get('forwardPasses'), seconds=elapsed, error=error,
                       imageSha256=digest(SUITE / query['image']) if condition.endswith('_image') else None,
                       contextSha256=hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest(),
                       gold=query['gold'], metrics=metrics, guarded=guarded, recordedUTC=utc())
            append(run_path, row)
            done.add(key)
            print(f"{query['id']} {condition}: exact={metrics['exact']} accepted={metrics['guard_accepted']} {elapsed}s", flush=True)
    print('COMPLETE', len(done), 'records; model calls', len(queries) * len(CONDITIONS), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--freeze', action='store_true')
    mode.add_argument('--run', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.freeze and args.resume:
        parser.error('--resume applies only to --run')
    freeze() if args.freeze else run(args.resume)
