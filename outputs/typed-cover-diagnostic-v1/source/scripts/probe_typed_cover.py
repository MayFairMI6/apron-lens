"""EXPOSED-only rubric cover diagnostic; pure --freeze never loads a model.

Reverse pairs contain rubric propositions, NOT learner evidence. Nothing here
assigns grading statuses, credit, grounding, or an adoption recommendation.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import itertools
import json
from pathlib import Path
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'typed-cover-diagnostic-v1'
THRESHOLD = .8
DEADLINE_SECONDS = 55.
MODEL_ID = 'MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli'
MODEL_REVISION = 'b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7'
LABELS = ('contradiction', 'entailment', 'neutral')
FIXTURE = ROOT / 'experiments/typed_relation_review/development-v1.json'
SOURCES = ('scripts/probe_typed_cover.py', 'docs/course/TYPED_COVER_DIAGNOSTIC_PLAN.md',
           'backend/training_assessment.py', 'experiments/typed_relation_review/propositions.py',
           'docs/course/TYPED_REVIEW_R11_CONTRACT.md', 'modelaccess/nli.py',
           'scripts/probe_redesign_semantics.py')
DEPENDENCIES = [
    dict(id='cause-implies-release', antecedent='cause', consequent='release',
         scope='surface-causal only', meaning='The authored causal change facet explicitly asserts ground-hold release. No requirement to repeat release separately; no synthetic learner evidence is created.'),
    dict(id='broad-unknown-not-specific', antecedent='broad-readiness-unknown', consequent=None,
         scope='unknown-specific controls only', meaning='Unconfirmed overall readiness does not entail the specific takeoff-clearance unknown. The converse is not asserted either; no unknown is a denial.')]


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def build_cases():
    dev = json.loads(FIXTURE.read_text())['cases']
    if len(dev) != 24:
        raise ValueError('unexpected exposed development fixture')
    fog = [('lvp', 'Low-visibility procedures are active.'),
           ('safeguarding', 'Safeguarding is active.'), ('hold', 'TRN101 remains held.')]
    estimate = [('estimate', 'The latest target off-block estimate for TRN102 is 10:35.'),
                ('authority', 'The target off-block estimate does not establish departure clearance.')]
    causal = [('release', "TRN102's ground hold has been released."),
              ('cause', "TRN102's ground hold was released because the obstructing vehicle is now clear.")]
    unknown = [('broad-readiness-unknown', 'Overall departure readiness remains unconfirmed.'),
               ('specific-clearance-unknown', 'Takeoff clearance remains unconfirmed.')]
    cases = []
    def add(cid, group, answer, facets, expected, fixture_index, interpretation):
        cases.append(dict(id=cid, comparisonGroup=group, answer=answer,
            facets=[dict(id=k, text=v, expectedForwardLabel=e) for (k,v),e in zip(facets,expected)],
            exposedFixtureIndex=fixture_index, fixtureQuestion=dev[fixture_index]['payload']['question'],
            sourceKind='authored exposed diagnostic control',
            expectedComparisonInterpretation=interpretation, expectedComparisonLabel=None))
    add('procedures-only', 'hold-omission', 'Low-visibility procedures are active. Safeguarding is active.', fog,
        ['entailment','entailment','neutral'],18,
        'Hold content is genuinely absent by construction. If the selected reverse cover entails the exact answer, that is a cover-compatible omission control only.')
    add('unclear-hold', 'hold-omission', 'Low-visibility procedures are active. Safeguarding is active. I cannot tell whether TRN101 is held.', fog,
        ['entailment','entailment','neutral'],18,
        'Hold is addressed but unresolved. The uncertainty clause must survive in the reverse hypothesis; a neutral reverse label alone cannot identify which facet was addressed.')
    add('estimate-only', 'authority-omission', estimate[0][1],estimate,
        ['entailment','neutral'],15,
        'The estimate is stated; authority distinction is absent by construction. Reverse cover may explain the whole answer without supplying that distinction.')
    add('unclear-authority', 'authority-omission', estimate[0][1]+' I cannot tell whether that estimate establishes departure clearance.',estimate,
        ['entailment','neutral'],15,
        'The authority relation is explicitly unresolved. Reverse must preserve this qualifier; separation from omission is exploratory, with no fabricated expected comparison label.')
    add('causal-release', 'causal-dependency', causal[1][1],causal,
        ['entailment','entailment'],2,
        'The cause facet already asserts release. The only selected cover is the conjunction of all forward-entailed facets, even if redundant.')
    add('vehicle-only', 'causal-dependency', 'The obstructing vehicle is now clear.',causal,
        ['neutral','neutral'],3,
        'Vehicle clearance alone does not assert hold release or its causal link. Empty forward-E selection has no reverse query or omission verdict.')
    add('unsupported-extra', 'extra-retention', estimate[0][1]+' TRN102 has takeoff clearance.',estimate,
        ['entailment','neutral'],15,
        'The full extra claim stays in the reverse hypothesis. Non-entailment can reflect an unsupported extra rather than unclear rubric content; this does not test source grounding.')
    add('correct-to-current', 'correction', 'The latest target off-block estimate for TRN102 is 10:20; correction: it is 10:35.',estimate,
        ['entailment','neutral'],14,
        'Correction resolves to 10:35; reverse retains both values and the correction. Expected reverse comparison is null because recovery of correction history is not guaranteed.')
    add('correct-to-prior', 'correction', 'The latest target off-block estimate for TRN102 is 10:35; correction: it is 10:20.',estimate,
        ['contradiction','neutral'],14,
        'Correction resolves to 10:20. No reverse cover is selected if there are no forward entailments; no favorable historical clause is extracted.')
    add('wrong-entity', 'entity', 'The latest target off-block estimate for TRN103 is 10:35.',estimate,
        ['neutral','neutral'],15,
        'TRN103 is not TRN102. The answer gives no value for TRN102; different entities do not imply contradictory estimates. Reverse never repairs the entity.')
    add('broad-unknown', 'unknown-specificity', unknown[0][1],unknown,
        ['entailment','neutral'],16,
        'Broad readiness unknown cannot supply a specific clearance unknown. No implication edge is added for the unconfirmed specific permission.')
    add('specific-unknown', 'unknown-specificity', unknown[1][1],unknown,
        ['neutral','entailment'],16,
        'Specific clearance unknown alone is not an assertion about overall readiness; no reverse-derived credit or blanket neutral-to-missing rule.')
    return cases


def build_pairs(cases=None):
    cases = build_cases() if cases is None else cases
    pairs = []
    for case in cases:
        if not 1 <= len(case['facets']) <= 3:
            raise ValueError('cover exceeds three facets')
        def add(direction, premise, hypothesis, members, expected):
            pairs.append(dict(index=len(pairs), caseId=case['id'], direction=direction,
                premise=premise, hypothesis=hypothesis, memberFacetIds=members,
                role='rubricCoverDiagnostic', learnerEvidence=False,
                expectedLabel=expected))
        for facet in case['facets']:
            add('forward',case['answer'],facet['text'],[facet['id']],facet['expectedForwardLabel'])
        for size in range(1,len(case['facets'])+1):
            for subset in itertools.combinations(case['facets'],size):
                # Same fixed conjunction rule for every case; never strip text
                # from the exact full-answer reverse hypothesis.
                add('reverse','\n'.join(f['text'] for f in subset),case['answer'],
                    [f['id'] for f in subset], None)
    if len(pairs)>120:
        raise ValueError('pair budget exceeded')
    return pairs


def label(row):
    probabilities = row.get('probabilities') if row else None
    if not probabilities or row.get('error'):
        return 'unavailable'
    i=max(range(3),key=lambda j:probabilities[j])
    return LABELS[i] if probabilities[i]>=THRESHOLD else 'uncertain'


def analyze(cases,pairs,records):
    observed={r['index']:r for r in records}
    results=[]
    for case in cases:
        forward=[p for p in pairs if p['caseId']==case['id'] and p['direction']=='forward']
        labels={p['memberFacetIds'][0]:label(observed.get(p['index'])) for p in forward}
        complete=all(v!='unavailable' for v in labels.values())
        selected=[f['id'] for f in case['facets'] if labels[f['id']]=='entailment']
        reverse=next((p for p in pairs if p['caseId']==case['id'] and p['direction']=='reverse' and p['memberFacetIds']==selected),None) if complete and selected else None
        reverse_label=label(observed.get(reverse['index'])) if reverse else 'not_selected'
        results.append(dict(caseId=case['id'],comparisonGroup=case['comparisonGroup'],
            forwardLabels=labels,forwardComplete=complete,selectedFacetIds=selected if complete else None,
            selectedReverseIndex=reverse['index'] if reverse else None,selectedReverseLabel=reverse_label,
            observation=('Incomplete forward scoring: no selected cover.' if not complete else
                'No forward entailment: no reverse cover selected.' if not selected else
                'Cover-compatible exact full answer; does not prove omission or grant credit.' if reverse_label=='entailment' else
                'Selected cover does not confidently entail the whole answer; unclear content, extras, corrections, entities and model error remain competing explanations.'),
            expectedComparisonInterpretation=case['expectedComparisonInterpretation'],
            expectedComparisonLabel=None,role='rubricCoverDiagnostic',learnerEvidence=False))
    return dict(cases=results,comparisons=[dict(group=g,caseIds=[r['caseId'] for r in results if r['comparisonGroup']==g],
        expectedComparisonLabel=None,interpretation='Compare selected reverse labels jointly with full forward vectors; exploratory, no accuracy or grading-policy claim.') for g in sorted({r['comparisonGroup'] for r in results})])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--freeze',action='store_true',help='write pure frozen plan and sources only; no model access')
    args=parser.parse_args()
    out=args.output
    out.mkdir(parents=True,exist_ok=False)
    hashes={p:digest(ROOT/p) for p in SOURCES}
    fixture_hash=digest(FIXTURE)
    cases=build_cases();pairs=build_pairs(cases)
    matrix=dict(version=VERSION,cases=cases,pairs=pairs,dependencies=DEPENDENCIES)
    serialized=json.dumps(matrix,ensure_ascii=False,indent=2)+'\n'
    lock=dict(version=VERSION,createdAtUTC=utc(),createdAtUnix=time.time(),sourceHashes=hashes,
        fixtureHashes={str(FIXTURE.relative_to(ROOT)):fixture_hash},matrixSHA256=hashlib.sha256(serialized.encode()).hexdigest(),
        modelId=MODEL_ID,modelRevision=MODEL_REVISION,device='mps',threshold=THRESHOLD,
        deadlineSeconds=DEADLINE_SECONDS,pairCount=len(pairs),caseCount=len(cases),
        role='rubricCoverDiagnostic',learnerEvidence=False,
        scoringRule='Canonical argmax >= .8, otherwise uncertain; unavailable scores are not neutral. Reverse expected labels and ambiguous comparison labels are null.',
        dtypePolicy='Use pinned PairClassifier implementation; require actual runtime torch.float16 before scoring; no dtype mutation or conversion.',
        scope='EXPOSED only; no reserve, credit, grounding, adoption or grading-policy claims.')
    for p in SOURCES+(str(FIXTURE.relative_to(ROOT)),):
        dest=out/'source'/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/p,dest)
    (out/'lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    (out/'matrix.json').write_text(serialized)
    def verify():
        if any(digest(ROOT/p)!=h for p,h in hashes.items()) or digest(FIXTURE)!=fixture_hash:
            raise RuntimeError('source or exposed fixture changed')
    verify()
    if args.freeze:
        print(json.dumps(lock),flush=True)
        return
    sys.path.insert(0,str(ROOT))
    from modelaccess.nli import PairClassifier
    snapshot=Path.home()/'.cache/huggingface/hub'/('models--'+MODEL_ID.replace('/','--'))/'snapshots'/MODEL_REVISION
    artifacts={p.name:digest(p) for p in sorted(snapshot.iterdir()) if p.is_file() and p.name!='README.md'}
    (out/'model-artifacts.json').write_text(json.dumps(artifacts,indent=2)+'\n')
    started=time.monotonic();engine=None;error=None;start_utc=utc()
    try:
        engine=PairClassifier(device='mps')
        (out/'startup.json').write_text(json.dumps(dict(runtime=engine.runtime,elapsedSeconds=time.monotonic()-started,atUTC=utc()),indent=2)+'\n')
        if engine.runtime.get('dtype') != 'torch.float16':
            raise RuntimeError('Pinned MPS profile requires torch.float16; actual dtype: '+str(engine.runtime.get('dtype'))+'; no conversion or scoring performed')
        lengths=[len(engine.tokenizer(p['premise'],p['hypothesis'],truncation=False)['input_ids']) for p in pairs]
        (out/'token-preflight.json').write_text(json.dumps(dict(lengths=lengths,maxTokens=max(lengths),limit=engine.max_length),indent=2)+'\n')
        if any(n>engine.max_length for n in lengths):
            raise ValueError('token bound exceeded: scoring withheld, no truncation')
        score_start=time.monotonic()
        (out/'score-clock.json').write_text(json.dumps(dict(startUTC=utc(),startMonotonic=score_start,deadlineMonotonic=score_start+DEADLINE_SECONDS),indent=2)+'\n')
        engine.score(pairs,score_start+DEADLINE_SECONDS)
    except Exception as exc:
        error=type(exc).__name__+': '+str(exc)
    finally:
        records=[] if engine is None else engine.records
        (out/'raw-scores.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
        observations=analyze(cases,pairs,records)
        summary=dict(planned=len(pairs),scored=len(records),error=error,startUTC=start_utc,endUTC=utc(),elapsedSeconds=time.monotonic()-started,**observations)
        (out/'observations.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps(dict(planned=len(pairs),scored=len(records),error=error,elapsedSeconds=summary['elapsedSeconds'])),flush=True)
    verify()
    if error:
        raise RuntimeError(error)


if __name__=='__main__':
    main()
