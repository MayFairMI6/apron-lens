"""PROCEDURAL: genuine frozen-9B answers on 787 handoff DEVELOPMENT cases.

Runs through the controller replay session, so each question uses the replay's
cutoff, selected aircraft and masked memory. These cases are development
material written after the first handoff answer failed `unknowns_schema`; they
are not a held-out set. Every attempt, including failures, is written out.
"""
import argparse
import json
import time
from pathlib import Path

from backend.bluebird_inbound import BLUEBIRD_787
from backend.evidence import FIELDS
from backend.replay_session import ReplayConflict, ReplaySession
from backend.training_adapter import COMPLETENESS_POLICY_VERSION, TRAINING_PROMPT_VERSION, TrainingAdapter
from modelaccess.contract import Settings

# cite: fact IDs the answer must cite. forbid: ID prefixes it must not cite.
# unknown: True when the answer must name at least one unreported property.
CASES = (
    dict(id='gap-latest-and-release', cutoff=75, aircraft='A1', note='the cue that first failed',
         question='What is the latest inbound observation for TRN101, and has an airport landing release been received?',
         cite=['BB-AIR0-10:trajectory_checkpoint'], forbid=['F', 'BB-AIR1'], unknown=True),
    dict(id='gap-negative-authorisation', cutoff=75, aircraft='A1',
         question='Has the airport authorised TRN101 to land?', cite=[], forbid=['F', 'BB-AIR1'], unknown=True),
    dict(id='sector-mid-latest', cutoff=30, aircraft='A1',
         question='What is the latest inbound observation for TRN101?',
         cite=['BB-AIR0-5:trajectory_checkpoint'], forbid=['F', 'BB-AIR1'], unknown=False),
    dict(id='second-contact-identity', cutoff=75, aircraft='A5',
         question='What is the latest observation for this contact?',
         cite=['BB-AIR1-10:trajectory_checkpoint'], forbid=['F', 'BB-AIR0'], unknown=False),
    dict(id='after-handoff-first-airport-report', cutoff=100, aircraft='A1',
         question='What has the airport reported for TRN101?',
         cite=['F001:movement_condition'], forbid=['F002', 'F003', 'BB-AIR1'], unknown=False),
    dict(id='priority-authorised', cutoff=160, aircraft='A1',
         question='Has priority landing been authorised for TRN101?',
         cite=['F002:movement_condition'], forbid=['F003', 'BB-AIR1'], unknown=False),
    dict(id='release-unconfirmed', marker='R-F006', aircraft='A1',
         question='Is recovery complete and the runway released for TRN101?',
         cite=['F006:movement_condition'], forbid=['BB-AIR1'], unknown=False),
    dict(id='backward-seek-into-gap', cutoff=75, aircraft='A1', note='asked after the later cutoffs above',
         question='What is the latest inbound observation for TRN101, and has an airport landing release been received?',
         cite=['BB-AIR0-10:trajectory_checkpoint'], forbid=['F', 'BB-AIR1'], unknown=True),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--candidate', action='store_true', help='use the v9 unknown-names prompt candidate')
    args = parser.parse_args()
    prompts = args.output.with_suffix('.prompts.jsonl')
    adapter_class = TrainingAdapter
    if args.candidate:
        from experiments.unknown_names.candidate import UnknownNamesCandidate as adapter_class
    adapter = adapter_class('qwen3.5-9b', profile='apronlens-v2-mps', prompt_audit_path=prompts)
    started = time.time()
    adapter.load()
    settings = Settings(adapter.served_model, 768, image_max_side=672)
    replay = ReplaySession(args.seed, BLUEBIRD_787)
    count = 0
    with args.output.open('x') as stream:
        stream.write(json.dumps(dict(record='run', exercise=BLUEBIRD_787, seed=args.seed, model=adapter.served_model,
                                     promptVersion=adapter.prompt_version, completenessPolicy=COMPLETENESS_POLICY_VERSION,
                                     scenarioHash=replay.scenario_hash, runId=replay.run_id, split='development',
                                     loadSeconds=round(time.time() - started, 1))) + '\n')
        for case in CASES:
            def act(**body):
                nonlocal count
                count += 1
                return replay.action(dict(actionId=f'a{count}', runId=replay.run_id,
                                          viewRevision=replay.view_revision, **body))
            if 'marker' in case:
                view = act(action='jump', markerId=case['marker'])
            else:
                view = act(action='seek', cutoff=case['cutoff'])
            view = act(action='select', aircraftId=case['aircraft'])
            before = len(prompts.read_text().splitlines()) if prompts.exists() else 0
            clock = time.time()
            error = result = None
            try:
                result = replay.ask(dict(requestId='q-' + case['id'], runId=replay.run_id,
                                         viewRevision=view['viewRevision'], question=case['question']), adapter, settings)
            except (ReplayConflict, ValueError, RuntimeError, KeyError) as exc:
                error = f'{type(exc).__name__}: {exc}'
            attempts = [json.loads(line) for line in prompts.read_text().splitlines()[before:]] if prompts.exists() else []
            selections = []
            for a in attempts:
                try:
                    selections.append(json.loads(a['rawSelectorOutput']))
                except (TypeError, ValueError):
                    selections.append(None)
            final = selections[-1] if selections and isinstance(selections[-1], dict) else {}
            ids, unknowns = final.get('fact_ids', []), final.get('unknowns', [])
            accepted = bool(result and result.get('accepted'))
            checks = dict(
                accepted=accepted,
                citesRequired=all(i in ids for i in case['cite']),
                citesNothingForbidden=not any(i.startswith(p) for i in ids for p in case['forbid']),
                unknownsInVocabulary=all(u in FIELDS for u in unknowns),
                unknownAsExpected=bool(unknowns) == case['unknown'],
                rightFlight=final.get('aircraftId') == case['aircraft'])
            row = dict(record='case', id=case['id'], note=case.get('note', ''), cutoff=view['cutoff'],
                       aircraftId=case['aircraft'], question=case['question'], expected=dict(
                           cite=case['cite'], forbidPrefixes=case['forbid'], unknownExpected=case['unknown']),
                       checks=checks, passed=all(checks.values()), error=error,
                       errors=None if result is None else result.get('errors'),
                       answer=None if result is None else result.get('display', {}).get('answer'),
                       attempts=[dict(attempt=a['attempt'], rawSelectorOutput=a['rawSelectorOutput'],
                                      completenessError=a['completenessError'], usage=a['usage']) for a in attempts],
                       latencySeconds=round(time.time() - clock, 2),
                       memoryTurnsVisibleAfter=len(replay.memory_turns))
            stream.write(json.dumps(row) + '\n')
            stream.flush()
            print(case['id'], 'PASS' if row['passed'] else 'FAIL', checks, row['errors'], flush=True)
        replay.verify_unchanged()
        stream.write(json.dumps(dict(record='end', scenarioUnchanged=True, notes=len(replay.notes))) + '\n')


if __name__ == '__main__':
    main()
