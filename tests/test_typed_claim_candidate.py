import json,unittest,copy
from experiments.typed_claim_review.candidate import units_for,expand_review
from backend.training_session import TrainingSession

class CandidateContract(unittest.TestCase):
    def payload(self):
        s=TrainingSession(17,'fog_restrictions',clock=lambda:0.)
        s.phase='checkpoint';s.active_probe=0;s.source_time=60;s.revision=2
        c,_=s.prepare_response(dict(actionId='test',runId=s.run_id,revision=2,checkpointId='check-1',responseText='Procedures are active. TRN101 is held.'))
        return json.loads(c.payload_json)
    def result(self,p):
        return dict(units=[dict(id=u['id'],status='supported',evidenceIds=['R005'],comment='Matches report.') for u in units_for(p['learnerResponse'])],criteria=[dict(id=c['id'],status='met',unitIds=['U1'],evidenceIds=[c['evidenceIds'][-1]],comment='Matches report.') for c in p['criteria'][:-1]])
    def test_exact_text_partition_without_lost_nonspace_characters(self):
        for text in ['A is held; B is waiting, but C is clear.','Long '+('word '*100),'All done and TRN101 is cleared for departure.']:
            units=units_for(text)
            self.assertEqual(''.join(''.join(u['text'].split()) for u in units),''.join(text.split()))
            for u in units:self.assertEqual(u['text'],text[u['start']:u['end']]);self.assertLessEqual(len(u['text']),160)
    def test_unsupported_unit_overrides_other_met_criteria(self):
        p=self.payload();r=self.result(p);r['units'][-1]['status']='unsupported'
        out=expand_review(json.dumps(r),p)
        self.assertEqual(out['verdict'],'needs_review')
        self.assertEqual(out['points'][-1]['learnerQuote'],'TRN101 is held.')
    def test_omitted_unit_bad_citation_or_invented_reference_rejected(self):
        p=self.payload();base=self.result(p)
        for mutate in [lambda x:x['units'].pop(),lambda x:x['criteria'][0].update(unitIds=['invented']),lambda x:x['units'][0].update(evidenceIds=['future'])]:
            r=copy.deepcopy(base);mutate(r)
            with self.assertRaises(ValueError):expand_review(json.dumps(r),p)
    def test_met_credit_cannot_reference_unsupported_unit(self):
        p=self.payload();r=self.result(p);r['units'][0]['status']='unsupported'
        with self.assertRaisesRegex(ValueError,'credit conflicts'):expand_review(json.dumps(r),p)

    def test_missing_and_uncertain_cannot_become_supported(self):
        p=self.payload();r=self.result(p);r['criteria'][0].update(status='missing',unitIds=[]);r['units'][0]['status']='uncertain';r['criteria'][1]['unitIds']=['U2']
        out=expand_review(json.dumps(r),p)
        self.assertEqual(out['verdict'],'partly_supported');self.assertEqual(out['points'][0]['learnerQuote'],'')

if __name__=='__main__':unittest.main()
