import json
from scripts.evaluate_training_assistant import suite, score, validate_cases, lexical_prompt
from backend.lessons import build_lesson
from backend.conversation.context import snapshot
from backend.conversation.turns import build_prompt


def fixture():
    world,_,_=build_lesson(17,'late_arrival')
    case=suite()['late_arrival'][2]
    fact=next(f for f in snapshot(world,'A3','TRN103',case['cutoff'])['facts'] if f['property']=='movement_condition' and f['status']=='current')
    p=dict(referent=dict(aircraftId='A3',flightInstance='TRN103'),claims=[dict(fact_id=fact['fact_id'],value=fact['value'],status='current',evidence_ids=[fact['event_id']])],unknowns=[])
    return world,case,p


def evaluate(world,case,p,accepted=True):
    return score(dict(accepted=accepted,rawModelOutput=json.dumps(p)),world,case)


def test_authored_keys_and_receipt_boundaries():
    validate_cases()
    assert sum(map(len,suite().values()))==18


def test_supported_complete_answer_passes():
    w,c,p=fixture();assert evaluate(w,c,p)['passed']


def test_supported_but_irrelevant_is_incomplete():
    w,c,p=fixture();p['claims']=[]
    assert not evaluate(w,c,p)['passed']
    assert evaluate(w,c,p)['emptyAnswer']


def test_wrong_identity_rejected_by_score():
    w,c,p=fixture();p['referent']['flightInstance']='TRN102'
    assert not evaluate(w,c,p)['passed']


def test_bad_citation_and_hallucinated_value_fail():
    w,c,p=fixture();p['claims'][0]['evidence_ids']=['nonexistent']
    assert not evaluate(w,c,p)['passed']
    w,c,p=fixture();p['claims'][0]['value']='takeoff cleared'
    assert not evaluate(w,c,p)['passed']


def test_future_release_fails_before_receipt():
    w,c,p=fixture()
    fact=next(f for f in snapshot(w,'A3','TRN103',134)['facts'] if f['property']=='movement_condition' and f['status']=='current')
    p['claims']=[dict(fact_id=fact['fact_id'],value=fact['value'],status='current',evidence_ids=[fact['event_id']])]
    assert not evaluate(w,c,p)['passed']


def test_failure_not_hidden_and_false_unknown_fails():
    w,c,p=fixture();assert not evaluate(w,c,p,False)['passed']
    p['unknowns']=['movement_condition'];assert not evaluate(w,c,p)['passed']


def test_baseline_never_adds_future_evidence_and_is_bounded():
    w,c,_=fixture();prompt=build_prompt(w,c['cutoff'],None,None,[],{},c['question'])
    filtered=lexical_prompt(prompt)
    candidates,_=json.JSONDecoder().raw_decode(filtered.split('Candidate flights and received facts: ',1)[1])
    facts=[f for candidate in candidates for f in candidate['facts']]
    assert len(facts)<=6
    assert all(f['receiptTime']<=c['cutoff'] for f in facts)
    assert lexical_prompt(prompt)==filtered


# Register the bounded scorer checks with the repository unittest runner.
import unittest
class TrainingComparisonTests(unittest.TestCase):
    pass
for name, check in list(globals().items()):
    if name.startswith("test_") and callable(check):
        setattr(TrainingComparisonTests, name, lambda self, check=check: check())
del name, check

class ComparisonReportingTests(unittest.TestCase):
    def test_retries_cost_and_failed_response_remain_in_summary(self):
        from scripts.report_training_comparison import summarize
        w,c,p=fixture()
        r=dict(requestId='r1',latencySeconds=41,accepted=False,rawModelOutput=json.dumps(p))
        run=dict(records=[dict(condition='selector_history',result=r,score=score(r,w,c))])
        attempts=[dict(requestId='r1',usage=dict(input_tokens=100,output_tokens=20)),
                  dict(requestId='r1',usage=dict(input_tokens=None,output_tokens=None))]
        s=summarize(run,attempts)['selector_history']
        self.assertEqual(s['completeSupported'],0)
        self.assertEqual(s['retriedTurns'],1)
        self.assertEqual(s['calls'],2)
        self.assertEqual(s['over35Seconds'],1)
        self.assertEqual(s['over40Seconds'],1)
        self.assertFalse(s['usageComplete'])
        self.assertIsNone(s['inputTokens'])
        self.assertEqual(s['knownInputTokens'],100)
