import hashlib
from pathlib import Path
import unittest
from backend.training_adapter_v6 import selector_context as revised, TRAINING_PROMPT_VERSION
from backend.training_adapter_v5 import selector_context as previous
from backend.conversation.turns import build_prompt
from backend.conversation.context import snapshot
from scripts.evaluate_prompt_revision import fresh_suite, make_world, validate_keys

class PromptRevisionTests(unittest.TestCase):
    def test_unpromoted_default_remains_v5(self):
        from backend.training_adapter import TRAINING_PROMPT_VERSION as default_version
        self.assertEqual(default_version,'training-evidence-selector-v5')

    def test_v5_file_is_exact_published_adapter(self):
        self.assertEqual(hashlib.sha256(Path('backend/training_adapter_v5.py').read_bytes()).hexdigest(),
                         '061d724ee2bac06a6545b6376f5cdebfffed3bcd9393b6e307abff4dd29d7695')
    def test_only_instructions_change_not_evidence(self):
        w=make_world('late_baggage',29)
        base=build_prompt(w,159,None,None,[],{},'Does the release establish overall readiness?')
        a,ca=previous(base);b,cb=revised(base)
        self.assertEqual(ca,cb)
        self.assertEqual(a.split('Assigned training role: ',1)[1],b.split('Assigned training role: ',1)[1])
        self.assertNotEqual(a,b)
        self.assertEqual(TRAINING_PROMPT_VERSION,'training-evidence-selector-v6')
    def test_fresh_keys_and_positive_negative_receipt_cutoffs(self):
        validate_keys(fresh_suite(),29)
        self.assertEqual(sum(map(len,fresh_suite().values())),24)
        w=make_world('explicit_readiness',29)
        def readiness(t):
            return [f['value'] for f in snapshot(w,'A2','TRN102',t)['facts'] if f['property']=='overall_readiness' and f['status']=='current']
        self.assertEqual(readiness(199.999),[])
        self.assertEqual(readiness(200),['ready'])
        self.assertEqual(readiness(219.999),['ready'])
        self.assertEqual(readiness(220),['not ready: additional inspection required'])
    def test_original_lessons_do_not_receive_eval_reports(self):
        w=make_world('late_baggage',29)
        self.assertFalse(any(e['id'].startswith('EVAL_') for e in w['events']))

class RevisionReportingTests(unittest.TestCase):
    def test_paired_gate_does_not_hide_a_regression(self):
        from scripts.report_prompt_revision import report_data
        rows=[]
        def row(phase,version,exercise,i,passed):
            return dict(phase=phase,version=version,exercise=exercise,turn=i,
                result=dict(requestId=f'{phase}-{version}-{exercise}-{i}',latencySeconds=1,rawJsonValid=True,rawModelOutput='{}'),
                score=dict(passed=passed,accepted=True,identityCorrect=True,complete=passed,unknownsCorrect=True,staleClaims=False,emptyAnswer=False))
        for i in range(18):rows.append(row('observed_regression','v6','regression',i,True))
        for v in ('v5','v6'):
            for e in fresh_suite():
                for i in range(6):rows.append(row('fresh',v,e,i,not(v=='v5' and e=='surface_conflict' and i==2)))
        data=report_data(dict(records=rows,adopt=True),[])
        self.assertTrue(data['adoptionGate'])
        self.assertEqual(data['improved'],[('surface_conflict',2)])
        next(r for r in rows if r['phase']=='fresh' and r['version']=='v6' and r['exercise']=='late_arrival' and r['turn']==0)['score']['passed']=False
        data=report_data(dict(records=rows,adopt=False),[])
        self.assertFalse(data['adoptionGate'])
        self.assertEqual(data['regressed'],[('late_arrival',0)])
