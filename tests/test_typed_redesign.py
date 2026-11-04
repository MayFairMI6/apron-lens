"""R11 contract and architecture checks; injected scores, never model inference."""
import copy
import math
import time
import unittest
from backend.training_assessment import TYPED_QUESTIONS
from experiments.typed_relation_review.redesign import (
    evaluate,validate_redesign_review,choose_quotes,bounded_spans,Plan,source_pairs,
    source_units,grounding_context,question_answer,label,THRESHOLD)


def fixture(answer='TRN102 is held because a service vehicle obstructs its route.'):
    return dict(episodeId='R11-TEST',checkpointId='check-1',aircraftId='A2',cutoff=30,
        question=TYPED_QUESTIONS['surface_conflict'][0],learnerResponse=answer,
        reports=[dict(id='R1',episodeId='R11-TEST',aircraftId='A2',flightInstance='TRN102',
            eventTime=10,receiptTime=12,source='ground-control',
            message='TRN102 is held because a service vehicle obstructs its ground route.',
            facts=[dict(property='movement_condition',value='hold: vehicle obstructing ground route')])],
        criteria=[dict(id='flight',expected='PRIVATE_EXPECTED_IDENTIFICATION',evidenceIds=['R1']),
                  dict(id='reason',expected='PRIVATE_EXPECTED_REASON',evidenceIds=['R1']),
                  dict(id='grounding',expected='All claims supported.',evidenceIds=['R1'])])


class Scores:
    def __init__(self,choose=None):
        self.choose=choose;self.records=[];self.planned_pairs=[];self.calls=0;self.max_length=512
    def score(self,pairs,deadline):
        self.calls+=1;self.planned_pairs=list(pairs)
        default={'correction_scope':'neutral','criterion_omission':'contradiction',
            'grounding_temporal_scope':'neutral','grounding_unsupported_probe':'contradiction',
            'grounding_scoped_conflict_probe':'contradiction','grounding_nonfactual':'contradiction'}
        vectors={'entailment':[.03,.94,.03],'contradiction':[.94,.03,.03],
                 'neutral':[.03,.03,.94],'uncertain':[.2,.6,.2]}
        result=[]
        for p in pairs:
            value=self.choose(p) if self.choose else None
            value=value or default.get(p['kind'],'entailment')
            row=dict(p,probabilities=vectors[value],error=None,truncationRejected=False)
            result.append(row);self.records.append(row)
        return result


class QuarterCharacterTokenizer:
    def __call__(self,a,b,truncation=False):
        assert truncation is False
        return {'input_ids':list(range(math.ceil((len(a)+len(b))/4)+3))}


class RedesignTests(unittest.TestCase):
    def review(self,p=None,scorer=None):
        return evaluate(p or fixture(),scorer or Scores(),time.monotonic()+30)

    def test_whole_answer_and_question_are_separate_from_expected_and_sources(self):
        p=fixture();scorer=Scores();result=self.review(p,scorer)
        self.assertEqual(result['verdict'],'supported')
        primary=[r for r in scorer.records if r['kind'].startswith('criterion_')]
        self.assertTrue(primary)
        for row in primary:
            self.assertIn(p['learnerResponse'],row['premise'])
            self.assertIn(p['question'],row['premise'])
            self.assertNotIn('PRIVATE_EXPECTED',row['premise'])
            self.assertNotIn('ground-control',row['premise'])
        for point in result['points']:
            self.assertEqual(point['learnerQuote'],point['learnerQuotes'][0])
        self.assertEqual(len(scorer.planned_pairs),len(scorer.records))

    def test_question_presupposition_cannot_earn_omitted_identification(self):
        p=fixture('A service vehicle is obstructing the ground route.')
        def choose(row):
            if row.get('criterionId')=='flight' and row['kind']=='criterion_coverage':return 'neutral'
            if row.get('criterionId')=='flight' and row['kind']=='criterion_omission':return 'entailment'
        # Even a spurious whole-answer entailment cannot supply learner coverage.
        result=self.review(p,Scores(choose))
        self.assertEqual(result['points'][0]['status'],'missing')
        self.assertEqual(result['points'][0]['learnerQuotes'],[])

    def test_present_but_unconfirmed_paraphrase_is_uncertain_not_missing_or_met(self):
        scorer=Scores(lambda r:'neutral' if r['kind']=='criterion_meaning' else None)
        result=self.review(fixture('The situation I described still applies.'),scorer)
        self.assertTrue(all(p['status']=='uncertain' for p in result['points'][:-1]))

    def test_correction_final_scope_vetoes_earlier_snippet_entailment(self):
        def choose(row):
            if row['kind']=='correction_scope':return 'entailment'
            if row['kind']=='criterion_final':return 'neutral'
        scorer=Scores(choose)
        result=self.review(fixture('TRN102 is held. I correct that: I mean TRN103.'),scorer)
        self.assertTrue(all(p['status']=='uncertain' for p in result['points'][:-1]))
        self.assertFalse(any(r['kind']=='quotation_witness' for r in scorer.records))

    def test_neutral_grounding_is_neither_automatic_contradiction_nor_credit(self):
        scorer=Scores(lambda row:'neutral' if row['kind']=='grounding_support' else None)
        self.assertEqual(self.review(scorer=scorer)['points'][-1]['status'],'uncertain')
        def invented(row):
            if row['kind']=='grounding_support':return 'neutral'
            if row['kind']=='grounding_unsupported_probe':return 'entailment'
        scorer=Scores(invented)
        self.assertEqual(self.review(fixture('An engine has exploded.'),scorer)['points'][-1]['status'],'contradicted')

    def test_nonfactual_fragment_is_checked_with_question_and_not_forced_false(self):
        def choose(row):
            if row['kind']=='grounding_support':return 'neutral'
            if row['kind']=='grounding_factuality':return 'contradiction'
            if row['kind']=='grounding_nonfactual':return 'entailment'
        scorer=Scores(choose)
        self.assertEqual(self.review(fixture('Takeoff clearance.'),scorer)['points'][-1]['status'],'met')
        self.assertTrue(all('Question' in r['premise'] for r in scorer.records if r['kind']=='grounding_support'))

    def test_history_is_not_available_to_current_claim_without_semantic_history(self):
        p=fixture();p['reports'][0]['facts'][0].update(supersedes=['OLD:movement_condition'])
        old=copy.deepcopy(p['reports'][0]);old.update(id='OLD',eventTime=1,receiptTime=2,
            message='TRN102 was held by a baggage delay.',facts=[dict(property='movement_condition',value='hold: baggage delayed')])
        p['reports'].append(old)
        scorer=Scores();self.review(p,scorer)
        self.assertFalse(any('OLD' in r.get('reportIds',[]) for r in scorer.records if r['kind']=='grounding_support'))
        scorer=Scores(lambda r:'entailment' if r['kind']=='grounding_temporal_scope' else None)
        self.review(p,scorer)
        self.assertTrue(any('OLD' in r.get('reportIds',[]) for r in scorer.records if r['kind']=='grounding_support'))
        self.assertTrue(any('non-current' in r['premise'] for r in scorer.records if r['kind']=='grounding_support'))

    def test_source_attribution_is_explicit_eligible_evidence(self):
        p=fixture('Ground control reports that TRN102 is held by a vehicle.')
        scorer=Scores();self.review(p,scorer)
        self.assertTrue(all('ground-control' in r['premise'] for r in scorer.records if r['kind']=='grounding_support'))
        self.assertTrue(all(r['reportIds']==['R1'] for r in scorer.records if r['kind']=='grounding_support'))

    def test_unrelated_or_historical_chunk_contradiction_is_not_scoped_conflict(self):
        scorer=Scores(lambda r:'contradiction' if r['kind']=='grounding_support' else None)
        self.assertEqual(self.review(scorer=scorer)['points'][-1]['status'],'uncertain')
        def conflict(row):
            if row['kind']=='grounding_support':return 'contradiction'
            if row['kind']=='grounding_scoped_conflict_probe':return 'entailment'
        self.assertEqual(self.review(scorer=Scores(conflict))['points'][-1]['status'],'contradicted')

    def test_lossless_source_chunks_repeat_provenance_and_cannot_prove_support(self):
        p=fixture();p['reports'][0]['message']='Reported state: '+('not confirmed; ' * 120)
        scorer=Scores();scorer.tokenizer=QuarterCharacterTokenizer();scorer.max_length=128
        plan=Plan(scorer,time.monotonic()+20)
        current,history=grounding_context(p)
        units=source_units(p,current,history)
        indices=source_pairs(plan,'test_source_pack',p['question'],units,'TRN102 is held.')
        rows=[plan.pairs[i] for i in indices]
        self.assertGreater(len(rows),1)
        self.assertTrue(all(r['inputTokensPlanned']<=128 for r in rows))
        chunks=[c for row in rows for c in row['sourceChunks'] if c['sourceRecord']['text']==units[0]['text']]
        self.assertEqual(''.join(c['sourceChunk']['text'] for c in chunks),units[0]['text'])
        self.assertTrue(all('flight TRN102' in c['repeatedProvenance'] for c in chunks))
        self.assertTrue(all(not r['sourceCoverageComplete'] for r in rows if any(c['partialRecord'] for c in r['sourceChunks'])))

    def test_multi_quote_cover_has_each_facet_exact_and_nonoverlapping(self):
        text='First supported part. '+('padding '*30)+'Second supported part.'
        a=dict(start=0,end=21,text=text[:21]);start=text.index('Second');b=dict(start=start,end=len(text),text=text[start:])
        quotes=choose_quotes(text,[[a],[b]])
        self.assertEqual(quotes,[a['text'],b['text']])
        self.assertTrue(all(len(q)<=160 for q in quotes))
        with self.assertRaises(ValueError):choose_quotes(text,[[]])

    def test_contract_rejects_duplicate_overlap_order_and_legacy_mismatch(self):
        p=fixture();result=self.review(p)
        for quotes in [[result['points'][0]['learnerQuote']]*2,['absent'],['x'*161]]:
            bad=copy.deepcopy(result);bad['points'][0]['learnerQuotes']=quotes
            bad['points'][0]['learnerQuote']=quotes[0]
            with self.assertRaises(ValueError):validate_redesign_review(bad,p)
        bad=copy.deepcopy(result);bad['points'][0]['learnerQuote']='TRN102'
        with self.assertRaises(ValueError):validate_redesign_review(bad,p)

    def test_invalid_source_and_deadline_fail_before_scoring(self):
        for mutate in [lambda p:p.update(cutoff=float('nan')),lambda p:p['reports'][0].update(receiptTime=31),
                       lambda p:p['reports'][0].update(episodeId='OTHER')]:
            p=fixture();mutate(p);scorer=Scores()
            with self.assertRaises(ValueError):self.review(p,scorer)
            self.assertEqual(scorer.calls,0)
        with self.assertRaises(TimeoutError):evaluate(fixture(),Scores(),time.monotonic()-1)
        self.assertEqual(THRESHOLD,.8)

    def test_stage_failure_preserves_full_planned_audit(self):
        class Failed(Scores):
            def score(self,pairs,deadline):
                if self.calls:raise RuntimeError('second stage failed')
                return super().score(pairs,deadline)
        scorer=Failed()
        with self.assertRaises(RuntimeError):self.review(scorer=scorer)
        self.assertGreater(len(scorer.planned_pairs),len(scorer.records))


if __name__=='__main__':unittest.main()
