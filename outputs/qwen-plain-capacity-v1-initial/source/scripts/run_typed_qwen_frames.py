"""Frozen exposed-only extraction diagnostic. No grades or report inputs."""
import argparse
import importlib
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    from experiments.typed_qwen_frames.runtime import FrameAdapter
    from backend.training_worker import IsolatedTrainingAdapter
    from modelaccess.contract import Settings, Request, FinishReason
    from backbone import model_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('fixture', type=Path)
    parser.add_argument('--module', default='experiments.typed_qwen_frames.candidate',
                        choices=['experiments.typed_qwen_frames.candidate',
                                 'experiments.typed_qwen_frames.claims_candidate',
                                 'experiments.typed_qwen_frames.capacity_candidate'])
    args = parser.parse_args()
    candidate = importlib.import_module(args.module)
    VERSION, prompt_for, parse_frames = candidate.VERSION, candidate.prompt_for, candidate.parse_frames
    output_kind = getattr(candidate, 'OUTPUT_KIND', 'structured_interpretation')
    validity_label = 'transportValid' if output_kind == 'plain_language_diagnostic' else 'structurallyValid'
    cases = json.loads(args.fixture.read_text())['cases']
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    sources = (list((ROOT/'experiments/typed_qwen_frames').glob('*.py')) +
               list((ROOT/'backbone').glob('*.py')) + list((ROOT/'modelaccess').glob('*.py')) +
               [ROOT/'backbone/models.json', ROOT/'backbone/VERSION', Path(__file__),
                ROOT/'backend/training_worker.py', ROOT/'backend/training_result.py',
                ROOT/'docs/course/TYPED_QWEN_FRAME_CONTRACT.md'])
    sources += sorted((ROOT/'docs/course').glob('TYPED_QWEN_FRAME_*_ADDENDUM.md'))
    if output_kind == 'plain_language_diagnostic':
        sources.append(ROOT/'docs/course/TYPED_QWEN_CAPACITY_CONTRACT.md')
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    for path in sources:
        target = out/'source'/path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    factory = FrameAdapter
    identity = factory().served_model
    settings = Settings(identity, 1000, image_max_side=672)
    lock = dict(version=VERSION, module=args.module, outputKind=output_kind,
                sourceHashes=hashes, fixtureSHA256=sha(args.fixture),
                fixture=str(args.fixture), model=identity, settings=asdict(settings),
                createdAt=time.time(), runtimeProfile='apronlens-v2-mps',
                generationTimeoutSeconds=55, retries=0,
                stage=('plain-language capacity diagnostic; no structured qualification or grading'
                       if output_kind == 'plain_language_diagnostic'
                       else 'extraction-only; no grading or report evidence'),
                modelArtifactSHA256={p.name: sha(p) for p in sorted(model_dir('qwen3.5-9b').iterdir())
                                    if p.is_file()})
    (out/'lock.json').write_text(json.dumps(lock, indent=2)+'\n')
    owner = IsolatedTrainingAdapter(factory, identity, audit_path=out/'worker.jsonl',
                                    generation_timeout=55, startup_timeout=300)
    rows = []
    try:
        start = time.monotonic()
        startup = owner.warmup(settings)
        (out/'startup.json').write_text(json.dumps(dict(elapsedSeconds=time.monotonic()-start,
                                                       result=startup), default=str, indent=2)+'\n')
        for case in cases:
            # Semantic annotations stay outside the prompt and parser.
            learner = case['learnerResponse']
            prompt = prompt_for(learner)
            begin = time.monotonic()
            result = owner.review(Request('frames-'+str(case['id']), (('user', prompt),), settings))
            parsed = None
            error = None
            try:
                if not result.ok or result.finish_reason != FinishReason.STOP:
                    raise ValueError(result.error or 'incomplete_generation')
                if not result.metadata.get('observedEOS'):
                    raise ValueError('missing_observed_EOS')
                parsed = parse_frames(result.text, learner)
            except (ValueError, TypeError, KeyError) as exc:
                error = type(exc).__name__+': '+str(exc)
            row = dict(id=case['id'], learnerResponse=learner, prompt=prompt,
                       result=asdict(result), parsed=parsed, error=error,
                       elapsedSeconds=time.monotonic()-begin)
            rows.append(row)
            with (out/'records.jsonl').open('a') as stream:
                stream.write(json.dumps(row, default=str)+'\n')
            print(case['id'], validity_label, parsed is not None, error, flush=True)
            # Do not conceal a timeout with a recovered/second attempt.
            if owner.status != 'ready':
                break
    finally:
        owner.close()
        summary = dict(planned=len(cases), completed=len(rows), outputKind=output_kind,
                       semanticAcceptance='not assessed by this runner')
        summary[validity_label] = sum(r['parsed'] is not None for r in rows)
        (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    if any(sha(ROOT/p) != digest for p, digest in hashes.items()) or sha(args.fixture) != lock['fixtureSHA256']:
        raise RuntimeError('Frozen source or fixture changed during run')


if __name__ == '__main__':
    main()
