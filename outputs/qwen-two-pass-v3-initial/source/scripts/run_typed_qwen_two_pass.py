"""Frozen, learner-only two-task diagnostic; one owner deadline, no grades."""
import argparse
from dataclasses import asdict
from functools import partial
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
    from experiments.typed_qwen_frames.two_pass_runtime import TwoPassFrameAdapter
    from experiments.typed_qwen_frames.two_pass_candidate import VERSION
    from backend.training_worker import IsolatedTrainingAdapter
    from modelaccess.contract import Settings, Request, FinishReason
    from backbone import model_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('fixture', type=Path)
    args = parser.parse_args()
    cases = json.loads(args.fixture.read_text())['cases']
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    sources = (list((ROOT/'experiments/typed_qwen_frames').glob('*.py')) +
               list((ROOT/'backbone').glob('*.py')) + list((ROOT/'modelaccess').glob('*.py')) +
               [ROOT/'backbone/models.json', ROOT/'backbone/VERSION', Path(__file__),
                ROOT/'backend/training_worker.py', ROOT/'backend/training_result.py',
                ROOT/'docs/course/TYPED_QWEN_FRAME_CONTRACT.md',
                ROOT/'docs/course/TYPED_QWEN_TWO_PASS_CONTRACT.md'])
    sources += sorted((ROOT/'docs/course').glob('TYPED_QWEN_FRAME_*_ADDENDUM.md'))
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    for path in sources:
        target = out/'source'/path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    identity = TwoPassFrameAdapter(audit_path=out/'stages.jsonl').served_model
    settings = Settings(identity, 1000, image_max_side=672)
    lock = dict(version=VERSION, sourceHashes=hashes, fixtureSHA256=sha(args.fixture),
                fixture=str(args.fixture), model=identity, settings=asdict(settings),
                createdAt=time.time(), runtimeProfile='apronlens-v2-mps',
                aggregateGenerationTimeoutSeconds=55, stageOutputCaps=[500, 500],
                retries=0, stage='two planned learner interpretation tasks; no grading',
                modelArtifactSHA256={p.name: sha(p) for p in sorted(model_dir('qwen3.5-9b').iterdir())
                                    if p.is_file()})
    (out/'lock.json').write_text(json.dumps(lock, indent=2)+'\n')
    factory = partial(TwoPassFrameAdapter, audit_path=str(out/'stages.jsonl'),
                      audit_context=dict(lockSHA256=sha(out/'lock.json'), version=VERSION,
                                         fixtureSHA256=lock['fixtureSHA256'], sourceHashes=hashes))
    owner = IsolatedTrainingAdapter(factory, identity, audit_path=out/'worker.jsonl',
                                    generation_timeout=55, startup_timeout=300)
    rows = []
    try:
        begin = time.monotonic()
        startup = owner.warmup(settings)
        (out/'startup.json').write_text(json.dumps(dict(elapsedSeconds=time.monotonic()-begin,
                                                       result=startup), default=str, indent=2)+'\n')
        for case in cases:
            learner = case['learnerResponse']
            begin = time.monotonic()
            result = owner.review(Request('two-pass-'+str(case['id']), (('user', learner),), settings))
            valid = (result.ok and result.finish_reason == FinishReason.STOP and
                     result.metadata.get('observedEOS') and result.metadata.get('parsed') is not None)
            row = dict(id=case['id'], learnerResponse=learner, result=asdict(result),
                       structurallyValid=bool(valid), elapsedSeconds=time.monotonic()-begin)
            rows.append(row)
            with (out/'records.jsonl').open('a') as stream:
                stream.write(json.dumps(row, default=str)+'\n')
            print(case['id'], 'structurally_valid', bool(valid), result.error, flush=True)
            if owner.status != 'ready':
                break  # No recovery replay or second attempt.
    finally:
        owner.close()
        (out/'summary.json').write_text(json.dumps(dict(planned=len(cases), completed=len(rows),
            structurallyValid=sum(r['structurallyValid'] for r in rows),
            semanticAcceptance='not assessed by this runner; both stages require independent review'), indent=2)+'\n')
    if any(sha(ROOT/p) != digest for p, digest in hashes.items()) or sha(args.fixture) != lock['fixtureSHA256']:
        raise RuntimeError('Frozen source or fixture changed during run')


if __name__ == '__main__':
    main()
