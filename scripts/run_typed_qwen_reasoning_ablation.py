"""Fresh matched OFF/ON controls; only the experimental thinking flag differs."""
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
CONTROL_SHA = 'da73694d3c3caeeb08fc43039f64f7edfcd93dfdee32a5e7ad355ea90153b0b1'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    from experiments.typed_qwen_frames.reasoning_runtime import ReasoningFrameAdapter, EXPERIMENT_VERSION
    from experiments.typed_qwen_frames import claims_v6_control as candidate
    from backend.training_worker import IsolatedTrainingAdapter
    from modelaccess.contract import Settings, Request, FinishReason
    from backbone import model_dir
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('fixture', type=Path)
    args = parser.parse_args()
    if sha(Path(candidate.__file__)) != CONTROL_SHA:
        raise RuntimeError('Immutable v6 control has changed')
    cases = json.loads(args.fixture.read_text())['cases']
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    sources = (list((ROOT/'experiments/typed_qwen_frames').glob('*.py')) +
               list((ROOT/'backbone').glob('*.py')) + list((ROOT/'modelaccess').glob('*.py')) +
               [ROOT/'backbone/models.json', ROOT/'backbone/VERSION', Path(__file__),
                ROOT/'backend/training_worker.py', ROOT/'backend/training_result.py',
                ROOT/'docs/course/TYPED_QWEN_FRAME_CONTRACT.md',
                ROOT/'docs/course/TYPED_QWEN_REASONING_ABLATION_CONTRACT.md'])
    sources += sorted((ROOT/'docs/course').glob('TYPED_QWEN_FRAME_*_ADDENDUM.md'))
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in sources}
    for path in sources:
        target = out/'source'/path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    identity = ReasoningFrameAdapter(thinking=False, audit_path=out/'unused.jsonl').served_model
    settings = Settings(identity, 1000, image_max_side=672)
    lock = dict(version=EXPERIMENT_VERSION, candidateVersion=candidate.VERSION,
                candidateSHA256=CONTROL_SHA, sourceHashes=hashes,
                fixtureSHA256=sha(args.fixture), fixture=str(args.fixture),
                model=identity, settings=asdict(settings), createdAt=time.time(),
                baseRuntimeProfile='apronlens-v2-mps', armOrder=['off', 'on'],
                soleArmFactor='enable_thinking', generationTimeoutSeconds=55,
                allGeneratedTokensCap=1000, warmupGeneratedTokensCap=1000,
                startupTimeoutSeconds=300, retries=0,
                eosPolicy='base generation EOS union verified chat-end token 248046',
                modelArtifactSHA256={p.name: sha(p) for p in sorted(model_dir('qwen3.5-9b').iterdir())
                                    if p.is_file()})
    (out/'lock.json').write_text(json.dumps(lock, indent=2)+'\n')
    summaries = []
    for thinking in (False, True):
        arm_name = 'on' if thinking else 'off'
        arm = out/arm_name
        arm.mkdir()
        context = dict(pairLockSHA256=sha(out/'lock.json'), arm=arm_name,
                       candidateSHA256=CONTROL_SHA, fixtureSHA256=lock['fixtureSHA256'])
        factory = partial(ReasoningFrameAdapter, thinking=thinking,
                          audit_path=str(arm/'generation.jsonl'), audit_context=context)
        owner = IsolatedTrainingAdapter(factory, identity, audit_path=arm/'worker.jsonl',
                                        generation_timeout=55, startup_timeout=300)
        rows, startup_error = [], None
        try:
            started = time.monotonic()
            try:
                startup = owner.warmup(settings)
                startup_record = dict(elapsedSeconds=time.monotonic()-started, result=startup, error=None)
            except Exception as exc:
                startup_error = type(exc).__name__ + ': ' + str(exc)
                startup_record = dict(elapsedSeconds=time.monotonic()-started, result=None, error=startup_error)
            (arm/'startup.json').write_text(json.dumps(startup_record, default=str, indent=2)+'\n')
            if startup_error is None:
                for case in cases:
                    learner = case['learnerResponse']
                    prompt = candidate.prompt_for(learner)
                    started = time.monotonic()
                    result = owner.review(Request(arm_name+'-'+str(case['id']), (('user', prompt),), settings))
                    parsed, error = None, None
                    try:
                        if not result.ok or result.finish_reason != FinishReason.STOP or not result.metadata.get('observedEOS'):
                            raise ValueError(result.error or 'incomplete_generation')
                        parsed = candidate.parse_frames(result.text, learner)
                    except (ValueError, TypeError, KeyError) as exc:
                        error = type(exc).__name__+': '+str(exc)
                    row = dict(id=case['id'], learnerResponse=learner, prompt=prompt,
                        promptSHA256=hashlib.sha256(prompt.encode()).hexdigest(),
                        result=asdict(result), parsed=parsed, error=error,
                        elapsedSeconds=time.monotonic()-started)
                    rows.append(row)
                    with (arm/'records.jsonl').open('a') as stream:
                        stream.write(json.dumps(row, default=str)+'\n')
                    print(arm_name, case['id'], 'structurally_valid', parsed is not None, error, flush=True)
                    if owner.status != 'ready':
                        break
        finally:
            owner.close()  # No next arm until this owner and recovery are stopped.
            summary = dict(arm=arm_name, thinkingEnabled=thinking, planned=len(cases),
                attempted=len(rows), startupError=startup_error,
                structurallyValid=sum(r['parsed'] is not None for r in rows),
                semanticAcceptance='not assessed; all final meanings require independent review')
            (arm/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
            summaries.append(summary)
        if any(sha(ROOT/p) != digest for p, digest in hashes.items()) or sha(args.fixture) != lock['fixtureSHA256']:
            raise RuntimeError('Frozen source or fixture changed during arm')
    (out/'summary.json').write_text(json.dumps(dict(arms=summaries, plannedTotal=2*len(cases),
        semanticAcceptance='not assessed; paired exposed diagnostic only'), indent=2)+'\n')


if __name__ == '__main__':
    main()
