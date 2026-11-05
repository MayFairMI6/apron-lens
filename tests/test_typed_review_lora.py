import copy,json
from experiments.typed_review_lora.build_data import cases,FAMILIES
from experiments.typed_review_lora.evaluate import score,summarize
from backend.training_assessment import validate_review


def test_all_authored_targets_structurally_valid():
    for family in FAMILIES:
        for episode in range(4):
            for row in cases(family,episode):validate_review(json.dumps(row['target']),row['payload'])


def test_false_credit_counted_even_under_needs_review():
    row=list(cases('stand_occupancy',0))[3]
    response=copy.deepcopy(row['target']);response['points'][0]['status']='met'
    assert score(json.dumps(response),row)['false_acceptance']==1


def test_refusal_cannot_pass_promotion_gate():
    row=list(cases('stand_occupancy',0))[0]
    records=[{'id':row['id'],'arm':arm,'elapsed':1,'score':score('',row)} for arm in ('base','adapter')]
    assert not summarize(records)['research_gate_passed']
    assert not summarize(records)['base']['supported_accepted']


def test_omission_not_contradiction():
    row=list(cases('service_dependency',0))[2]
    assert [x['status'] for x in row['target']['points']]==['met','missing','met']
    assert row['target']['points'][1]['learnerQuote']==''


def test_cross_clause_contradiction_precedence():
    assert list(cases('stand_occupancy',0))[3]['target']['points'][0]['status']=='contradicted'
    assert list(cases('position_destination',0))[4]['target']['points'][1]['status']=='contradicted'


def test_future_report_citation_rejected():
    row=list(cases('stand_occupancy',0))[0]
    row['payload']['reports'][0]['receiptTime']=101
    assert not score(json.dumps(row['target']),row)['valid']

def test_equal_counts_do_not_hide_new_false_credit():
    row=list(cases('stand_occupancy',0))[3]
    base=copy.deepcopy(row['target']);adapter=copy.deepcopy(row['target'])
    base['points'][0]['status']='met';adapter['points'][1]['status']='met'
    records=[{'id':row['id'],'arm':arm,'elapsed':1,'score':score(json.dumps(response),row)}
             for arm,response in [('base',base),('adapter',adapter)]]
    result=summarize(records)
    assert result['new_false_acceptance_cases']==[row['id']]
    assert not result['research_gate_passed']


import unittest
class TypedReviewLoraTests(unittest.TestCase):
    pass
for name,check in list(globals().items()):
    if name.startswith('test_') and callable(check):
        setattr(TypedReviewLoraTests,name,lambda self,check=check:check())
del name,check
