"""Contract tests with injected NLI probabilities; no model loads or GPU calls."""
import copy
import time
import unittest
from backend.training_assessment import RUBRICS,TYPED_QUESTIONS
from experiments.typed_nli_review.candidate import (
    THRESHOLD, NLIEngine, confident_label,evaluate,grounding_context,learner_sentences)
from experiments.typed_nli_review.propositions import PROPOSITIONS,RELEVANCE


class FakeScorer:
    def __init__(self, choose=None):
        self.choose=choose or (lambda p:'entailment');self.calls=0;self.pairs=[]
    def score(self,pairs,deadline):
        self.calls+=1;self.pairs=pairs
        values={'entailment':[.05,.9,.05],'contradiction':[.9,.05,.05],
                'neutral':[.05,.05,.9],'uncertain':[.2,.6,.2]}
        return [dict(probabilities=values[self.choose(p)],error=None,truncationRejected=False) for p in pairs]


def payload(text='Safeguarding cancellation is confirmed. TRN101 remains parked and its departure clearance is unconfirmed.'):
    reports=[dict(id='R007',episodeId='NLI-TEST',receiptTime=10,eventTime=9,
                  message='Safeguarding cancellation has been requested.',facts=[dict(property='safeguarding',value='pending')]),
             dict(id='R008',episodeId='NLI-TEST',receiptTime=20,eventTime=19,
                  message='Safeguarding cancellation is confirmed. TRN101 remains parked; departure clearance is unconfirmed.',
                  facts=[dict(property='safeguarding',value='cancelled',supersedes=['R007:safeguarding'])])]
    return dict(episodeId='NLI-TEST',checkpointId='check-3',cutoff=25,learnerResponse=text,
        question=TYPED_QUESTIONS['fog_restrictions'][2],reports=reports,
        criteria=[dict(id='confirmation',expected='Safeguarding cancellation is confirmed.',evidenceIds=['R007','R008']),
                  dict(id='authority',expected='Parked and unconfirmed departure clearance.',evidenceIds=['R008']),
                  dict(id='grounding',expected='All actual claims supported.',evidenceIds=['R007','R008'])])


class TypedNLIReviewTests(unittest.TestCase):
    def run_review(self,p,scorer=None):
        return evaluate(p,scorer or FakeScorer(),time.monotonic()+10)

    def test_all_twelve_have_separate_authored_propositions(self):
        self.assertEqual(set(PROPOSITIONS),set(RUBRICS))
        for exercise,rows in RUBRICS.items():
            self.assertEqual(len(PROPOSITIONS[exercise]),3)
            for i,criteria in enumerate(rows):
                self.assertEqual(list(PROPOSITIONS[exercise][i]),[c[0] for c in criteria])
                self.assertEqual(list(RELEVANCE[exercise][i]),[c[0] for c in criteria])
                self.assertTrue(all(len(RELEVANCE[exercise][i][c])==len(PROPOSITIONS[exercise][i][c]) for c in PROPOSITIONS[exercise][i]))
                self.assertTrue(all(isinstance(h,str) and h for hs in PROPOSITIONS[exercise][i].values() for h in hs))

    def test_source_validation_precedes_inference(self):
        for mutate in [lambda p:p['reports'][0].update(receiptTime=30),
                       lambda p:p['reports'][0].update(episodeId='OTHER'),
                       lambda p:p['criteria'][0].update(evidenceIds=['MISSING']),
                       lambda p:p['reports'].append(copy.deepcopy(p['reports'][0]))]:
            p=payload();mutate(p);scorer=FakeScorer()
            with self.assertRaises(ValueError):self.run_review(p,scorer)
            self.assertEqual(scorer.calls,0)

    def test_current_grounding_excludes_only_fully_superseded_message(self):
        p=payload();current,old=grounding_context(p)
        self.assertEqual([r['id'] for r in current],['R008'])
        self.assertEqual([r['id'] for r in old],['R007'])
        scorer=FakeScorer();review=self.run_review(p,scorer)
        grounding=[x for x in scorer.pairs if x['kind']=='grounding']
        self.assertTrue(all('requested' not in x['premise'] for x in grounding))
        self.assertTrue(all(x['reportIds']==['R008'] for x in grounding))
        self.assertEqual(review['verdict'],'supported')
        self.assertEqual(review['points'][0]['evidenceIds'],['R007','R008'])
        self.assertEqual(review['points'][-1]['evidenceIds'],['R008'])

    def test_partial_supersession_withholds_before_model(self):
        p=payload();p['reports'][0]['facts'].append(dict(property='stand',value='A'))
        scorer=FakeScorer()
        with self.assertRaisesRegex(ValueError,'partially superseded'):self.run_review(p,scorer)
        self.assertEqual(scorer.calls,0)

    def test_historical_grounding_is_qualified_and_conservative(self):
        p=payload('Earlier, safeguarding cancellation was requested. TRN101 remains parked with clearance unconfirmed.')
        scorer=FakeScorer();review=self.run_review(p,scorer)
        historical=next(x for x in scorer.pairs if x['kind']=='grounding' and x['conservativeHistoricalUncertainty'])
        self.assertIn('Earlier superseded report',historical['premise'])
        self.assertEqual(review['points'][-1]['status'],'uncertain')

    def test_missing_facet_and_explicit_contradiction_remain_distinct(self):
        scorer=FakeScorer(lambda p:'neutral' if p['kind']=='criterion' and p['criterionId']=='authority' and p['facet']==1 else 'entailment')
        review=self.run_review(payload(),scorer)
        self.assertEqual(review['points'][1]['status'],'uncertain')
        self.assertEqual(review['points'][1]['learnerQuote'],'')
        scorer=FakeScorer(lambda p:'contradiction' if p.get('criterionId')=='authority' and p.get('facet')==1 else 'neutral' if p.get('criterionId')=='authority' else 'entailment')
        self.assertEqual(self.run_review(payload(),scorer)['points'][1]['status'],'contradicted')

    def test_unsupported_extra_cannot_hide_behind_correct_core(self):
        p=payload('Cancellation is confirmed; TRN101 is parked with clearance unconfirmed. An engine exploded.')
        scorer=FakeScorer(lambda pair:'neutral' if pair['kind']=='grounding' and 'exploded' in pair['hypothesis'] else 'entailment')
        review=self.run_review(p,scorer)
        self.assertEqual(review['points'][0]['status'],'met')
        self.assertEqual(review['points'][-1]['status'],'contradicted')
        self.assertEqual(review['points'][-1]['learnerQuote'],'An engine exploded.')
        self.assertEqual(review['points'][-1]['comment'],'Not established by the received reports.')

    def test_quotes_need_nli_witness_and_are_exact_original_substrings(self):
        p=payload();review=self.run_review(p)
        for point in review['points']:
            self.assertIn(point['learnerQuote'],p['learnerResponse'])
            self.assertLessEqual(len(point['learnerQuote']),160)
        scorer=FakeScorer(lambda pair:'neutral' if pair['kind']=='criterion' else 'entailment')
        self.assertTrue(all(p['status']=='uncertain' for p in self.run_review(p,scorer)['points'][:-1]))
        p=payload('Safeguarding cancellation is confirmed and '+('the reported status remains unchanged '*7)+'with TRN101 parked and clearance unconfirmed.')
        with self.assertRaisesRegex(ValueError,'quotation witness'):self.run_review(p)

    def test_threshold_gray_and_probability_and_deadline_errors(self):
        self.assertEqual(THRESHOLD,.8)
        self.assertEqual(confident_label(dict(probabilities=[.1,.79,.11])),'uncertain')
        self.assertEqual(confident_label(dict(probabilities=[.1,.8,.1])),'entailment')
        with self.assertRaises(ValueError):confident_label(dict(probabilities=[.5,.5,.5]))
        with self.assertRaises(ValueError):confident_label(dict(probabilities=None,error='input_too_long',truncationRejected=True))
        with self.assertRaises(TimeoutError):evaluate(payload(),FakeScorer(),time.monotonic()-1)
        self.assertEqual(self.run_review(payload(),FakeScorer(lambda p:'uncertain'))['points'][0]['status'],'uncertain')

    def test_irrelevant_sentences_cannot_contradict_other_topics(self):
        scorer=FakeScorer(lambda p:'contradiction' if p['kind']=='criterion' and p['criterionId']=='authority' and 'Safeguarding' in p['premise'] else 'entailment')
        review=self.run_review(payload(),scorer)
        self.assertEqual(review['points'][1]['status'],'met')
        self.assertFalse(any(p['kind']=='criterion' and p['criterionId']=='authority' and p['premise'].startswith('Safeguarding') for p in scorer.pairs))
        omitted=self.run_review(payload('Safeguarding cancellation is confirmed.'))
        self.assertEqual(omitted['points'][1]['status'],'missing')

    def test_relevant_conflict_blocks_credit_without_favorable_override(self):
        p=payload('Safeguarding cancellation is confirmed. Safeguarding cancellation is not confirmed. TRN101 remains parked with departure clearance unconfirmed.')
        scorer=FakeScorer(lambda p:'contradiction' if p['kind']=='criterion' and p['criterionId']=='confirmation' and 'not confirmed' in p['premise'] else 'entailment')
        self.assertEqual(self.run_review(p,scorer)['points'][0]['status'],'uncertain')
        p=payload();p['reports'].append(dict(id='R009',episodeId='NLI-TEST',receiptTime=21,eventTime=20,
            message='TRN101 is parked.',facts=[dict(property='position',value='parked')]))
        p['criteria'][-1]['evidenceIds'].append('R009')
        scorer=FakeScorer(lambda x:'contradiction' if x['kind']=='grounding' and len(x['reportIds'])>1 else 'entailment')
        self.assertEqual(self.run_review(p,scorer)['points'][-1]['status'],'uncertain')
        p['reports'].append(dict(id='R010',episodeId='NLI-TEST',receiptTime=22,eventTime=21,
            message='TRN101 is moving.',facts=[dict(property='position',value='moving')]))
        with self.assertRaisesRegex(ValueError,'incompatible current'):self.run_review(p)

    def test_same_sentence_extra_is_not_discarded(self):
        p=payload('Safeguarding cancellation is confirmed and an engine exploded. TRN101 remains parked with clearance unconfirmed.')
        scorer=FakeScorer(lambda x:'neutral' if x['kind']=='grounding' and 'exploded' in x['hypothesis'] else 'entailment')
        review=self.run_review(p,scorer)
        self.assertEqual(review['points'][-1]['status'],'contradicted')
        self.assertIn('and an engine exploded',review['points'][-1]['learnerQuote'])
        self.assertTrue(any(x['kind']=='criterion' and 'engine exploded' in x['premise'] for x in scorer.pairs))

    def test_entity_context_is_identity_only_and_ambiguity_not_resolved(self):
        p=payload('TRN101 remains parked. Its departure clearance is unconfirmed. Safeguarding cancellation is confirmed.')
        scorer=FakeScorer();self.run_review(p,scorer)
        contextual=[x for x in scorer.pairs if x.get('entityContext')]
        self.assertTrue(contextual)
        self.assertTrue(all(x['entityContext']['learnerExplicitFlight']=='TRN101' for x in contextual))
        self.assertTrue(all(x['exactLearnerSentence'] in p['learnerResponse'] for x in contextual))
        p=payload('TRN101 and TRN102 remain parked. Its departure clearance is unconfirmed. Safeguarding cancellation is confirmed.')
        self.assertEqual(self.run_review(p)['points'][1]['status'],'uncertain')
        for text in ['I am not discussing TRN101. Its departure clearance is unconfirmed. Safeguarding cancellation is confirmed.', 'According to a speaker, TRN101 is parked. Its departure clearance is unconfirmed. Safeguarding cancellation is confirmed.']:
            scorer=FakeScorer();self.run_review(payload(text),scorer)
            self.assertFalse(any(x.get('entityContext') for x in scorer.pairs))
        scorer=FakeScorer();self.run_review(payload('trn101 does not have confirmed departure clearance. It remains parked. Safeguarding cancellation is confirmed.'),scorer)
        self.assertTrue(any(x.get('entityContext') for x in scorer.pairs))

    def test_exclusive_occupancy_counter_requires_same_present_relation(self):
        import json
        from experiments.typed_nli_review.candidate import _counter_eligible
        counter=dict(flight='TRN103',stand='B',hypothesis='TRN103 is occupying Stand B.')
        self.assertTrue(_counter_eligible('TRN103 is already occupying Stand B instead of TRN102.',counter))
        for sentence in ['TRN102 occupies Stand B.','TRN103 occupies Stand C.',
                         'TRN103 will occupy Stand B.','TRN103 is waiting for Stand B.']:
            self.assertFalse(_counter_eligible(sentence,counter))
        p=payload('TRN103 is already occupying Stand B instead of TRN102.')
        p['question']=TYPED_QUESTIONS['late_arrival'][0]
        p['criteria']=[dict(id='flight',expected='waiting',evidenceIds=['R008']),dict(id='occupant',expected='occupant',evidenceIds=['R008']),p['criteria'][-1]]
        scorer=FakeScorer(lambda x:'entailment' if x['kind']=='exclusive_counter' else 'neutral' if x.get('criterionId')=='flight' else 'contradiction')
        review=self.run_review(p,scorer)
        self.assertEqual(review['points'][0]['status'],'contradicted')

    def test_no_truncation_is_audited_without_running_model(self):
        engine=NLIEngine.__new__(NLIEngine)
        engine.batch_size=8;engine.max_length=5;engine.records=[]
        engine.tokenizer=lambda a,b,truncation: {'input_ids':list(range(6))}
        with self.assertRaisesRegex(ValueError,'no truncation'):
            engine.score([dict(kind='grounding',premise='reports',hypothesis='claim')],time.monotonic()+10)
        self.assertEqual(engine.records[0]['inputTokens'],6)
        self.assertTrue(engine.records[0]['truncationRejected'])
        self.assertIsNone(engine.records[0]['probabilities'])
        self.assertEqual(len(engine.planned_pairs),1)

    def test_sentence_spans_preserve_semicolon_and_negation(self):
        text='  It is not cleared; it remains parked. Another claim!'
        spans=learner_sentences(text)
        self.assertEqual([s['text'] for s in spans],['It is not cleared; it remains parked.','Another claim!'])
        self.assertTrue(all(text[s['start']:s['end']]==s['text'] for s in spans))


if __name__=='__main__':unittest.main()
