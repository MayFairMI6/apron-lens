"""Contract tests with injected NLI probabilities; no model loads or GPU calls."""
import copy
import time
import unittest
from backend.training_assessment import RUBRICS,TYPED_QUESTIONS
from experiments.typed_relation_review.candidate import (
    THRESHOLD, NLIEngine, confident_label,evaluate,grounding_context,learner_sentences,service_relation,learner_clauses,relation_present,relation_units,explicit_identity_mismatch,comparison_context,source_text,canonical_source,unreported_readiness,unsupported_readiness_assertion,hold_reference_binding,explicit_unrepresented_takeoff_scope,unsupported_takeoff_assertion)
from experiments.typed_relation_review.propositions import PROPOSITIONS,RELEVANCE


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
        self.assertIn('Non-current historical source',historical['premise'])
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
        with self.assertRaisesRegex(ValueError,'conflicting current'):self.run_review(p)

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
        from experiments.typed_relation_review.candidate import _counter_eligible
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


def service_payload(sentence):
    return dict(episodeId='SERVICE-TEST',checkpointId='check-1',aircraftId='A2',cutoff=30,
        learnerResponse='A late baggage batch is delaying TRN102. '+sentence,
        question=TYPED_QUESTIONS['late_baggage'][0],
        reports=[dict(id='B',episodeId='SERVICE-TEST',aircraftId='A2',flightInstance='TRN102',
                      eventTime=10,receiptTime=12,message='A late baggage batch delays TRN102 loading.',
                      facts=[dict(property='baggage_status',value='delayed')]),
                 dict(id='F',episodeId='SERVICE-TEST',aircraftId='A2',flightInstance='TRN102',
                      eventTime=20,receiptTime=22,message='Fuel service for TRN102 is complete.',
                      facts=[dict(property='fuel_status',value='complete')])],
        criteria=[dict(id='delay',expected='Baggage delay.',evidenceIds=['B']),
                  dict(id='separation',expected='Separate fuel completion and unresolved baggage.',evidenceIds=['B','F']),
                  dict(id='grounding',expected='All factual clauses supported.',evidenceIds=['B','F'])])


class ServiceRelationTests(unittest.TestCase):
    def analyze(self,sentence,mutate=None):
        p=service_payload(sentence)
        if mutate:mutate(p)
        current,_=grounding_context(p)
        span=learner_sentences(p['learnerResponse'])[1]
        return service_relation(span,p,current),p

    def test_grammar_generalizes_aliases_connectors_without_rewriting(self):
        for text in [
            'Fuel is complete, but that does not mean baggage loading is complete.',
            'Fuel service has finished; this cannot establish that bags are complete.',
            'Fuel service is finished, but that finished service does not establish completed baggage loading.',
            'Fuel service is completed and fuel completion does not prove baggage is finished.',
            'Fuel for TRN102 is done, yet it doesn’t guarantee loading is done.',
            'Fuel is complete; baggage is outstanding.',
            'Fuel service is complete, but baggage loading remains delayed.',
        ]:
            with self.subTest(text=text):
                audit,p=self.analyze(text)
                self.assertTrue(audit['applied'],audit)
                self.assertEqual(set(audit['evidenceIds']),{'F','B'})
                self.assertEqual(audit['firstProperty'],'fuel_status')
                self.assertEqual(audit['secondProperty'],'baggage_status')
                for span in audit['spans']:
                    self.assertEqual(p['learnerResponse'][span['start']:span['end']],span['text'])

    def test_negative_polarity_wrong_relation_and_extra_clauses_not_hidden(self):
        for text in [
            'Fuel is not complete, but that does not mean baggage is complete.',
            'Fuel was complete, but baggage is delayed.',
            'Fuel is complete, but that does not mean baggage is complete?',
            'Fuel had been complete, but baggage is delayed.',
            'Fuel is complete, so that means baggage is complete.',
            'Fuel is complete, but that does not mean baggage is incomplete.',
            'Fuel is complete, but that does not mean baggage is complete and TRN102 is cleared for takeoff.',
            'Fuel is complete, but that does not mean baggage is complete; an engine exploded.',
            'Fuel is complete, but that does not mean fuel service is complete.',
            'Fuel for TRN101 is complete, but that does not mean baggage for TRN102 is complete.',
            'Baggage is complete, but that does not mean fuel is complete.',
        ]:
            with self.subTest(text=text):self.assertFalse(self.analyze(text)[0]['applied'])

    def test_independent_reported_unresolved_second_service_is_required(self):
        sentence='Fuel is complete, but that does not mean baggage is complete.'
        for mutate in [lambda p:p['reports'][0]['facts'][0].update(value='complete'),
                       lambda p:p['reports'][1]['facts'][0].update(value='in progress'),
                       lambda p:p['reports'][0].update(aircraftId='OTHER'),
                       lambda p:p['reports'][0].update(flightInstance='TRN101'),
                       lambda p:p.update(learnerResponse=p['learnerResponse'].replace('TRN102','TRN101'))]:
            with self.subTest(mutate=mutate):self.assertFalse(self.analyze(sentence,mutate)[0]['applied'])
        # A specific pending assertion cannot be substituted for reported delay.
        self.assertFalse(self.analyze('Fuel is complete, but baggage remains pending.')[0]['applied'])
        for prefix in ['I am not discussing TRN102.', 'This is not TRN102.', 'Someone said TRN102.', 'TRN102.']:
            audit,_=self.analyze(sentence,lambda p:p.update(learnerResponse=prefix+' '+sentence))
            self.assertFalse(audit['applied'])

    def test_rule_cannot_silently_drop_following_clearance_claim(self):
        p=service_payload('Fuel is complete, but that does not mean baggage is complete. TRN102 is cleared for takeoff.')
        scorer=FakeScorer(lambda x:'neutral' if x['kind']=='grounding' and 'takeoff' in x['hypothesis'] else 'entailment')
        result=evaluate(p,scorer,time.monotonic()+10)
        self.assertEqual(result['points'][-1]['status'],'contradicted')
        self.assertIn('takeoff',result['points'][-1]['learnerQuote'])

    def test_relation_topic_requires_both_services_and_keeps_raw_nli(self):
        p=service_payload('Fuel is complete, but that does not mean baggage loading is complete.')
        scorer=FakeScorer(lambda x:'neutral' if x['kind']=='grounding' and 'does not mean' in x['hypothesis']
                          else 'contradiction' if x.get('semanticRuleSupport') else 'entailment')
        result=evaluate(p,scorer,time.monotonic()+10)
        self.assertEqual(result['verdict'],'supported')
        self.assertFalse(any(x['kind']=='criterion' and x.get('criterionId')=='separation' and x['facet']==2
                             and x['premise'].startswith('A late baggage batch') for x in scorer.pairs))
        self.assertTrue(any(x.get('semanticRuleSupport') for x in scorer.pairs))
        self.assertEqual(sum(x['applied'] for x in scorer.semantic_rule_audit),1)
        self.assertEqual(set(result['points'][-1]['evidenceIds']),{'F','B'})



class RelationCoverageTests(unittest.TestCase):
    def span(self,text):return dict(start=0,end=len(text),text=text)

    def test_omitted_relation_is_not_inferred_from_topic_mention(self):
        for text,mode in [('TRN103 is waiting for Stand B.','occupancy'),
                          ('The most recent target off-block estimate is 10:35.','estimate_authority'),
                          ('The obstructing vehicle is clear.','hold_change_link'),
                          ('Releasing a ground hold differs from takeoff permission.','permission_status'),
                          ('Its completed fuel proves baggage loading is complete.','baggage_delay')]:
            with self.subTest(text=text):self.assertFalse(relation_present(text,mode))
        self.assertTrue(relation_present('TRN102 is delayed by a late baggage batch.','baggage_delay'))
        self.assertTrue(relation_present('Departure clearance remains unconfirmed.','permission_status'))

    def test_exact_clauses_preserve_core_and_grounding_extra(self):
        text='B is confirmed available for TRN103 and the exercise hold is released, so TRN103 has takeoff clearance.'
        span=self.span(text);clauses=learner_clauses(span)
        self.assertGreater(len(clauses),1)
        self.assertTrue(all(text[c['start']:c['end']]==c['text'] for c in clauses))
        availability=relation_units(span,'availability_status')
        release=relation_units(span,'stand_hold_link')
        self.assertTrue(availability);self.assertTrue(release)
        self.assertTrue(all('takeoff' not in c['text'] for c in availability+release))
        p=payload(text);scorer=FakeScorer()
        # The outer grounding interface still receives the complete original,
        # including the unsafe extra that minimal criterion windows exclude.
        evaluate(p,scorer,time.monotonic()+10)
        self.assertTrue(any(x['kind']=='grounding' and x['hypothesis']==text for x in scorer.pairs))

    def test_outer_negation_and_conditional_are_not_affirmative_fragments(self):
        for text in ['It is not true that fuel is complete and baggage is complete.',
                     'If TRN103 is held and baggage is delayed, then something changes.',
                     'TRN103 might be held because a service vehicle blocks its route.']:
            clauses=learner_clauses(self.span(text))
            self.assertEqual(len(clauses),1)
            self.assertEqual(clauses[0]['text'],text)
            self.assertFalse(explicit_identity_mismatch(clauses[0],'TRN102 is held.','movement_status'))

    def test_unambiguous_causal_subject_mismatch_and_other_flight_extra(self):
        text='TRN103 is held because a service vehicle blocks its route.'
        unit=relation_units(self.span(text),'vehicle_obstruction')[0]
        self.assertTrue(explicit_identity_mismatch(unit,"A service vehicle obstructs TRN102's ground route.",'vehicle_obstruction'))
        from backend.training_assessment import TYPED_QUESTIONS
        p=payload('TRN102 is held because a service vehicle blocks its route. TRN101 is also held.')
        p['question']=TYPED_QUESTIONS['surface_conflict'][0]
        p['criteria']=[dict(id='flight',expected='held',evidenceIds=['R008']),dict(id='reason',expected='obstruction',evidenceIds=['R008']),p['criteria'][-1]]
        scorer=FakeScorer();review=evaluate(p,scorer,time.monotonic()+10)
        self.assertEqual(review['points'][0]['status'],'met')
        self.assertEqual(review['points'][1]['status'],'met')
        self.assertFalse(any(x['kind']=='criterion' and x['criterionId']=='flight' and 'TRN101 is also' in x['premise'] for x in scorer.pairs))
        self.assertTrue(any(x['kind']=='grounding' and 'TRN101 is also' in x['hypothesis'] for x in scorer.pairs))


class TypedSourceAndContextTests(unittest.TestCase):
    def test_validity_expiry_and_supersession_use_existing_classifier(self):
        p=payload();p['reports'][1]['facts'][0]['validFrom']=40
        current,old=grounding_context(p)
        self.assertEqual([r['id'] for r in current],['R007'])
        self.assertEqual(old[0]['_typedFacts'][0]['status'],'scheduled')
        p=payload();p['reports'][1]['facts'][0]['validUntil']=23
        current,old=grounding_context(p)
        self.assertEqual(current,[])
        statuses={f['fact_id']:f['status'] for r in old for f in r['_typedFacts']}
        self.assertEqual(statuses,{'R007:safeguarding':'superseded','R008:safeguarding':'expired'})
        p=payload();p['reports'][1]['facts'][0]['validUntil']=19
        with self.assertRaisesRegex(ValueError,'validity'):grounding_context(p)

    def test_source_serialization_preserves_identity_value_ids_and_time(self):
        p=service_payload('Fuel is complete, but baggage remains delayed.')
        current,_=grounding_context(p)
        text=source_text(current[0])
        for value in ['B:baggage_status','TRN102','A2','current','"delayed"','10','12']:
            self.assertIn(value,text)
        p['reports'][1]['facts'][0]['supersedes']=['B:baggage_status']
        with self.assertRaisesRegex(ValueError,'supersession'):grounding_context(p)

    def test_resource_alias_requires_current_typed_provenance_and_keeps_quote(self):
        p=service_payload('Fuel is complete, but baggage remains delayed.')
        p['reports'].append(dict(id='S',episodeId='SERVICE-TEST',aircraftId='A2',flightInstance='TRN102',
            eventTime=5,receiptTime=7,message='TRN102 is assigned Stand B.',facts=[dict(property='stand',value='B')]))
        current,_=grounding_context(p)
        text='TRN103 is waiting for B;'
        unit=dict(start=0,end=len(text),text=text)
        premise,_,_,aliases,_=comparison_context(unit,text,p,current)
        self.assertIn('waiting for Stand B',premise)
        self.assertEqual(unit['text'],text)
        self.assertEqual(aliases[0]['sourceFactIds'],['S:stand'])
        p['reports'].append(dict(id='SA',episodeId='SERVICE-TEST',aircraftId='A1',flightInstance='TRN101',eventTime=5,receiptTime=7,message='Stand A assigned.',facts=[dict(property='stand',value='A')]))
        article='A service vehicle is blocking its route.'
        self.assertEqual(comparison_context(dict(start=0,end=len(article),text=article),article,p,grounding_context(p)[0])[3],[])
        none=copy.deepcopy(p);none['reports']=[r for r in none['reports'] if r['id'] not in ('S','SA')]
        self.assertEqual(comparison_context(unit,text,none,grounding_context(none)[0])[3],[])

    def test_exact_antecedents_restore_clause_without_assertion_invention(self):
        text='TRN102 is held because a service vehicle obstructs its route.'
        p=service_payload('Fuel is complete, but baggage remains delayed.')
        unit=relation_units(dict(start=0,end=len(text),text=text),'vehicle_obstruction')[0]
        premise,_,_,_,antecedents=comparison_context(unit,text,p,grounding_context(p)[0])
        self.assertEqual(antecedents,[text])
        self.assertIn(text,premise)
        self.assertTrue(relation_present('An estimate does not give departure clearance.','estimate_authority'))
        self.assertTrue(relation_present('The reposition plan proves Stand B is free.','availability_status'))
        self.assertFalse(relation_present('Low-visibility procedures were cancelled.','safeguarding_status'))
        self.assertTrue(relation_present('Safeguarding continues.','safeguarding_status'))
        text='Stand B is available for TRN103 and TRN102 ground hold is released.'
        unit=relation_units(dict(start=0,end=len(text),text=text),'stand_hold_link')[0]
        self.assertTrue(explicit_identity_mismatch(unit,"Stand B is available for TRN103, and TRN103's ground hold is released.",'stand_hold_link'))

    def test_canonical_source_uses_only_current_exact_source_condition(self):
        fact=dict(status='current',property='movement_condition',flightInstance='TRN103',aircraftId='A3',
                  value='hold: Stand B occupied by TRN102',fact_id='C:movement_condition',eventTime=20,receiptTime=23)
        result=canonical_source(fact)
        self.assertIn('TRN103 is waiting for Stand B',result['propositions'][0])
        self.assertEqual(result['sourceFactId'],'C:movement_condition')
        for change in [dict(status='superseded'),dict(value='plan: Stand B occupied by TRN102'),
                       dict(flightInstance=None),dict(value='hold: Stand B occupied by TRN102; cleared for takeoff')]:
            self.assertIsNone(canonical_source(dict(fact,**change)))


class ReadinessAndRawSourceTests(unittest.TestCase):
    def test_invalid_time_is_rejected_before_any_inference_including_empty_reports(self):
        for value in [float('nan'),float('inf'),-1,True,'25',None]:
            p=payload();p['cutoff']=value;scorer=FakeScorer()
            with self.assertRaises(ValueError):evaluate(p,scorer,time.monotonic()+10)
            self.assertEqual(scorer.calls,0)
        for field in ['eventTime','receiptTime']:
            for value in [float('nan'),float('inf'),-1,True,'10',None]:
                p=payload();p['reports'][0]['facts']=[];p['reports'][0][field]=value;scorer=FakeScorer()
                with self.assertRaises(ValueError):evaluate(p,scorer,time.monotonic()+10)
                self.assertEqual(scorer.calls,0)

    def test_raw_support_survives_unhelpful_normalization_and_raw_veto_stays(self):
        p=payload();scorer=FakeScorer(lambda x:'neutral' if x['kind']=='grounding' and x['sourceVariant']=='normalized' else 'entailment')
        self.assertEqual(evaluate(p,scorer,time.monotonic()+10)['points'][-1]['status'],'met')
        for pair in scorer.pairs:
            if pair['kind']=='grounding' and pair['sourceVariant']=='raw':
                self.assertNotIn('Evidence policy',pair['premise'])
                self.assertEqual(pair['sourceFactIds'],[])
        scorer=FakeScorer(lambda x:'contradiction' if x['kind']=='grounding' and x['sourceVariant']=='raw' else 'entailment')
        self.assertEqual(evaluate(p,scorer,time.monotonic()+10)['points'][-1]['status'],'uncertain')

    def test_absence_is_source_only_unconfirmed_and_any_known_state_disables(self):
        p=service_payload('Fuel is complete, but baggage remains delayed.')
        current,_=grounding_context(p);absence=unreported_readiness(current,'A2')
        self.assertIn('not confirmed',absence['proposition'])
        self.assertNotIn('not ready',absence['proposition'])
        for value in ['ready','not ready','unconfirmed']:
            q=copy.deepcopy(p);q['reports'][0]['facts'].append(dict(property='overall_readiness',value=value))
            self.assertIsNone(unreported_readiness(grounding_context(q)[0],'A2'))
        q=copy.deepcopy(p);q['reports'][0]['message']='TRN102 is not ready for departure.'
        self.assertIsNone(unreported_readiness(grounding_context(q)[0],'A2'))

    def test_positive_readiness_cannot_get_grounding_credit_from_model(self):
        text='TRN102 is now ready for departure: fuel and baggage are complete and its ground hold means every departure prerequisite is satisfied.'
        p=service_payload(text);p['learnerResponse']=text
        scorer=FakeScorer();review=evaluate(p,scorer,time.monotonic()+10)
        self.assertEqual(review['points'][-1]['status'],'contradicted')
        self.assertEqual(review['points'][-1]['learnerQuote'],'TRN102 is now ready for departure')
        self.assertTrue(any(x['rule']=='unsupported-positive-readiness-v1' for x in scorer.semantic_rule_audit))
        # Independent clauses and the full original are all saved; no extra
        # assertion disappears because a structural rule already found a flaw.
        self.assertTrue(any(x['kind']=='grounding' and x['groundingCoverage']=='full_sentence' for x in scorer.pairs))
        self.assertTrue(any(x['kind']=='grounding' and x['groundingCoverage']=='independent_clause' for x in scorer.pairs))

    def test_readiness_rule_respects_negation_questions_and_attribution(self):
        p=service_payload('Fuel is complete, but baggage remains delayed.')
        absence=unreported_readiness(grounding_context(p)[0],'A2')
        for text in ['TRN102 is now ready for departure?',
                     'If TRN102 is now ready for departure, it could move.',
                     'It is not true that TRN102 is now ready for departure.',
                     'Someone said "TRN102 is now ready for departure".',
                     'TRN102 fuel completion does not mean every departure prerequisite is satisfied.',
                     'TRN102 is not ready for departure.',
                     'I do not believe TRN102 is ready for departure.',
                     'It is false that TRN102 is ready for departure.',
                     'TRN102 is ready for departure if baggage is complete.',
                     'TRN102 is ready for departure unless the report is wrong.',
                     'There is no evidence that TRN102 is ready for departure.',
                     'I suspect TRN102 is ready for departure.',
                     'All departure prerequisites are satisfied for TRN102 provided the vehicle clears.',
                     'It is not the case that every departure prerequisite is satisfied for TRN102.',
                     'TRN102 does not have all departure prerequisites satisfied.',
                     'TRN102 has fuel complete, but not every departure prerequisite is satisfied.']:
            self.assertIsNone(unsupported_readiness_assertion(dict(start=0,end=len(text),text=text),absence),text)


class FullStatementAndHoldBindingTests(unittest.TestCase):
    def test_true_atoms_do_not_erase_unsupported_causal_relation(self):
        text='Safeguarding cancellation is confirmed. TRN101 remains parked and clearance is unconfirmed. TRN101 is at Stand A, so TRN102 is held.'
        p=payload(text)
        scorer=FakeScorer(lambda x:'contradiction' if x['kind']=='grounding' and x['groundingCoverage']=='full_sentence' and 'so TRN102' in x['hypothesis'] else 'entailment')
        review=evaluate(p,scorer,time.monotonic()+10)
        self.assertEqual(review['points'][-1]['status'],'contradicted')
        self.assertIn('so TRN102',review['points'][-1]['learnerQuote'])
        self.assertTrue(all(x['contributesToDecision'] for x in scorer.pairs if x['kind']=='grounding'))
        scorer=FakeScorer(lambda x:'uncertain' if x['kind']=='grounding' and x['groundingCoverage']=='full_sentence' and 'so TRN102' in x['hypothesis'] else 'entailment')
        self.assertEqual(evaluate(p,scorer,time.monotonic()+10)['points'][-1]['status'],'uncertain')

    def test_wrong_flight_original_context_cannot_be_dropped(self):
        p=payload('TRN103 is held because a vehicle blocks its route.')
        scorer=FakeScorer(lambda x:'contradiction' if x['kind']=='grounding' and x['groundingCoverage']=='full_sentence' else 'entailment')
        self.assertEqual(evaluate(p,scorer,time.monotonic()+10)['points'][-1]['status'],'contradicted')

    def test_any_untyped_target_report_or_ready_language_blocks_absence(self):
        p=service_payload('Fuel is complete, but baggage remains delayed.')
        for message,facts in [('TRN102 is ready to depart.',[]),
                              ('TRN102 is holding.',[]),
                              ('TRN102 is ready to depart.',[dict(property='movement_status',value='parked')]),
                              ('TRN102 is not ready.',[dict(property='movement_status',value='parked')])]:
            q=copy.deepcopy(p);q['reports'].append(dict(id='X',episodeId=q['episodeId'],aircraftId='A2',flightInstance='TRN102',
                eventTime=24,receiptTime=25,message=message,facts=facts))
            self.assertIsNone(unreported_readiness(grounding_context(q)[0],'A2'))

    def binding_payload(self):
        p=payload('Stand B is confirmed available for TRN103 and the exercise hold is released, so TRN103 has takeoff clearance.')
        p.update(aircraftId='A3',question=TYPED_QUESTIONS['late_arrival'][2],reports=[dict(id='H',episodeId=p['episodeId'],
            aircraftId='A3',flightInstance='TRN103',eventTime=10,receiptTime=12,message='Stand B is available for TRN103; its ground hold is released.',
            facts=[dict(property='movement_condition',value='Stand B available; exercise ground hold released')])])
        return p

    def test_unqualified_hold_binding_is_entity_only_with_source_identity(self):
        p=self.binding_payload();current,_=grounding_context(p)
        units=relation_units(learner_sentences(p['learnerResponse'])[0],'stand_hold_link')
        premise,entity,_,_,_=comparison_context(units[0],p['learnerResponse'],p,current,['H'])
        binding=entity['holdReferenceBinding']
        self.assertEqual(binding['flightInstance'],'TRN103')
        self.assertEqual(binding['sourceReportIds'],['H'])
        self.assertEqual(p['learnerResponse'][binding['start']:binding['end']],binding['exactReference'])
        self.assertEqual(premise,units[0]['text'].replace('the exercise hold',"TRN103's ground hold"))
        self.assertNotIn('No operational state',premise)
        self.assertEqual(binding['normalizedReference'],"TRN103's ground hold")
        self.assertEqual(binding['holdKindAlias']['sourceFactIds'],['H:movement_condition'])
        self.assertEqual(units[0]['text'],p['learnerResponse'][units[0]['start']:units[0]['end']])


    def test_hold_binding_refuses_competitors_conditionals_and_quotations(self):
        p=self.binding_payload();current,_=grounding_context(p)
        for text in ['Stand B is available for TRN103 and the other hold is released.',
                     'Stand B is available for TRN103 and another aircraft has the exercise hold.',
                     'Stand B is available for TRN103 and TRN102 has the exercise hold.',
                     'If Stand B is available for TRN103, the exercise hold is released.',
                     'Someone says "Stand B is available for TRN103 and the exercise hold is released".',
                     'The exercise hold is released.']:
            unit=dict(start=0,end=len(text),text=text)
            self.assertIsNone(hold_reference_binding(unit,p,current,['H']),text)
        other=copy.deepcopy(current[0]);other.update(id='OTHER',flightInstance='TRN102',aircraftId='A2')
        self.assertIsNone(hold_reference_binding(learner_sentences(p['learnerResponse'])[0],p,current+[other],['H','OTHER']))


class ExplicitTakeoffScopeTests(unittest.TestCase):
    def scoped_payload(self):
        p=service_payload('Fuel is complete, but baggage remains delayed.')
        p['reports'].append(dict(id='ROUTE',episodeId=p['episodeId'],aircraftId='A2',flightInstance='TRN102',
            eventTime=2,receiptTime=3,message='The reported route is within the apron. No runway or takeoff clearance is represented.',
            facts=[dict(property='route',value='apron ground circuit')]))
        return p

    def test_real_explicit_source_scope_supports_only_unsupported_assertion(self):
        p=self.scoped_payload();scope=explicit_unrepresented_takeoff_scope(grounding_context(p)[0],'A2')
        self.assertEqual(scope['evidenceIds'],['ROUTE'])
        self.assertIn('not an actual denial',scope['scope'])
        for text in ['TRN102 has takeoff clearance because its hold is released.',
                     'TRN102 is cleared for takeoff.',
                     'TRN102 has received clearance to take off.']:
            span=dict(start=0,end=len(text),text=text)
            rule=unsupported_takeoff_assertion(span,scope)
            self.assertTrue(rule['applied'],text)
            self.assertEqual(text[rule['offendingSpan']['start']:rule['offendingSpan']['end']],rule['offendingSpan']['text'])
            self.assertEqual(rule['sourcePreconditions']['sourceStatements'][0]['sourceFactIds'],['ROUTE:route'])

    def test_other_permission_report_disables_closed_scope_regardless_identity(self):
        for text in ['TRN102 has takeoff clearance.', 'TRN102 has been denied takeoff clearance.',
                     'Departure clearance for TRN102 is unconfirmed.',
                     'TRN103 has takeoff clearance.',
                     'The ground release is not takeoff permission.']:
            p=self.scoped_payload();p['reports'].append(dict(id='AUTH',episodeId=p['episodeId'],aircraftId='A2',flightInstance='TRN102',
                eventTime=24,receiptTime=25,message=text,facts=[]))
            self.assertIsNone(explicit_unrepresented_takeoff_scope(grounding_context(p)[0],'A2'),text)
        p=self.scoped_payload();p['reports'][-1]['message']='No departure movement has started.'
        self.assertIsNone(explicit_unrepresented_takeoff_scope(grounding_context(p)[0],'A2'))
        p=self.scoped_payload();p['reports'][-1]['flightInstance']=None
        self.assertIsNone(explicit_unrepresented_takeoff_scope(grounding_context(p)[0],'A2'))

    def test_positive_scope_rule_refuses_questions_embeddings_negations_and_other_flight(self):
        p=self.scoped_payload();scope=explicit_unrepresented_takeoff_scope(grounding_context(p)[0],'A2')
        for text in ['TRN102 has takeoff clearance?',
                     'I do not believe TRN102 has takeoff clearance.',
                     'It is false that TRN102 has takeoff clearance.',
                     'TRN102 has takeoff clearance if its hold is released.',
                     'If the hold is released, TRN102 has takeoff clearance.',
                     'Someone said "TRN102 has takeoff clearance".',
                     'TRN102 does not have takeoff clearance.',
                     'TRN102 takeoff clearance is unconfirmed.',
                     'TRN103 has takeoff clearance.',
                     'TRN102 has departure clearance.',
                     'The cancelled restriction gives TRN102 takeoff clearance.']:
            self.assertIsNone(unsupported_takeoff_assertion(dict(start=0,end=len(text),text=text),scope),text)

    def test_scope_rule_is_local_not_global_nli_conflict_override(self):
        p=self.scoped_payload()
        p['learnerResponse']='TRN102 has takeoff clearance because a ground hold is released.'
        # Use the live source-conflict question; actual model scores are injected
        # as favorable here to prove that the explicit source precondition is
        # independently checked instead of propagating another NLI label.
        p['question']=TYPED_QUESTIONS['surface_conflict'][2]
        p['criteria']=[dict(id='unknown',expected='authority unknown',evidenceIds=['ROUTE']),
                       dict(id='scope',expected='release differs',evidenceIds=['ROUTE']),
                       dict(id='grounding',expected='all claims supported',evidenceIds=['B','F','ROUTE'])]
        scorer=FakeScorer();review=evaluate(p,scorer,time.monotonic()+10)
        self.assertEqual(review['points'][-1]['status'],'contradicted')
        self.assertEqual(review['points'][-1]['learnerQuote'],'TRN102 has takeoff clearance')
        self.assertTrue(any(r['rule']=='unsupported-positive-takeoff-scope-v1' for r in scorer.semantic_rule_audit))


class HoldKindAndQualifiedPermissionTests(unittest.TestCase):
    def test_hold_kind_needs_explicit_current_same_actor_condition(self):
        maker=FullStatementAndHoldBindingTests();p=maker.binding_payload()
        unit=relation_units(learner_sentences(p['learnerResponse'])[0],'stand_hold_link')[0]
        p['reports'][0]['facts'][0]['value']='exercise hold released'
        current,_=grounding_context(p)
        premise,entity,_,_,_=comparison_context(unit,p['learnerResponse'],p,current,['H'])
        self.assertNotIn('holdKindAlias',entity['holdReferenceBinding'])
        self.assertIn("TRN103's exercise hold",premise)
        p['reports'][0]['facts'][0]['value']='ground hold request pending'
        current,_=grounding_context(p)
        premise,entity,_,_,_=comparison_context(unit,p['learnerResponse'],p,current,['H'])
        # Only the kind is resolved: pending is not injected, and the learner's
        # asserted release remains available for factual grounding to reject.
        self.assertIn("TRN103's ground hold is released",premise)
        self.assertNotIn('pending',premise)
        alias=entity['holdReferenceBinding']['holdKindAlias']
        self.assertEqual(alias['exactSourceValues'],['ground hold request pending'])
        self.assertIn('no released',alias['scope'])
        unknown=copy.deepcopy(current[0]);unknown['id']='UNKNOWN';unknown['flightInstance']=None
        self.assertIsNone(hold_reference_binding(unit,p,current+[unknown],['H','UNKNOWN']))

    def test_qualified_or_cancelled_clearance_is_not_clipped_to_positive_grant(self):
        p=ExplicitTakeoffScopeTests().scoped_payload();scope=explicit_unrepresented_takeoff_scope(grounding_context(p)[0],'A2')
        for suffix in ['pending','requested','unconfirmed','cancelled','canceled','withdrawn','revoked','expired','awaiting confirmation']:
            text='TRN102 has takeoff clearance '+suffix+'.'
            self.assertIsNone(unsupported_takeoff_assertion(dict(start=0,end=len(text),text=text),scope),text)

    def test_allow_permit_approve_and_any_untyped_target_report_disable_scope(self):
        for text in ['TRN102 is allowed to depart.', 'TRN102 is permitted to depart.',
                     'Departure for TRN102 is approved.', 'TRN102 is holding.']:
            p=ExplicitTakeoffScopeTests().scoped_payload()
            p['reports'].append(dict(id='X',episodeId=p['episodeId'],aircraftId='A2',flightInstance='TRN102',
                eventTime=24,receiptTime=25,message=text,facts=[]))
            self.assertIsNone(explicit_unrepresented_takeoff_scope(grounding_context(p)[0],'A2'),text)
            if 'holding' not in text:
                # Vocabulary protection also applies to typed messages; an
                # actor-state fact must not hide untyped permission language.
                p['reports'][-1]['facts']=[dict(property='movement_status',value='parked')]
                self.assertIsNone(explicit_unrepresented_takeoff_scope(grounding_context(p)[0],'A2'),text)


class WaitingAndExplicitOccupancyTests(unittest.TestCase):
    def arrival_payload(self,text):
        p=payload(text)
        p['question']=TYPED_QUESTIONS['late_arrival'][0]
        p['criteria']=[dict(id='flight',expected='waiting flight',evidenceIds=['R008']),
                       dict(id='occupant',expected='occupying aircraft',evidenceIds=['R008']),p['criteria'][-1]]
        return p

    def test_relative_occupancy_is_not_erased_by_waiting_for(self):
        text='The inbound TRN103 is waiting for Stand B, which is occupied by TRN102.'
        self.assertTrue(relation_present(text,'occupancy'))
        self.assertTrue(relation_units(dict(start=0,end=len(text),text=text),'occupancy'))
        scorer=FakeScorer();review=evaluate(self.arrival_payload(text),scorer,time.monotonic()+10)
        self.assertEqual(review['points'][1]['status'],'met')
        self.assertTrue(any(p['kind']=='criterion' and p['criterionId']=='occupant' for p in scorer.pairs))
        self.assertEqual(review['points'][1]['learnerQuote'],text)

    def test_waiting_alone_still_omits_occupant_and_wrong_occupant_is_judged(self):
        text='TRN103 is waiting for Stand B.'
        self.assertFalse(relation_present(text,'occupancy'))
        scorer=FakeScorer();review=evaluate(self.arrival_payload(text),scorer,time.monotonic()+10)
        self.assertEqual(review['points'][1]['status'],'missing')
        self.assertFalse(any(p['kind']=='criterion' and p['criterionId']=='occupant' for p in scorer.pairs))
        text='TRN103 is waiting for Stand B, which is occupied by TRN101.'
        self.assertTrue(relation_present(text,'occupancy'))
        scorer=FakeScorer(lambda p:'contradiction' if p.get('criterionId')=='occupant' else 'entailment')
        review=evaluate(self.arrival_payload(text),scorer,time.monotonic()+10)
        self.assertEqual(review['points'][1]['status'],'contradicted')
        self.assertEqual(review['points'][1]['learnerQuote'],text)

if __name__=='__main__':unittest.main()
