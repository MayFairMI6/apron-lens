"""Focused source-scope and quote-context tests; injected scores only."""
import copy
import time
import unittest
from backend.training_assessment import TYPED_QUESTIONS
from tests.test_typed_redesign import fixture,Scores
from experiments.typed_relation_review.scoped_content import (
    raw_sources,source_scope,grounding_context,evaluate,quote_candidates,resource_availability_view,current_report_projection )


class ScopedContentTests(unittest.TestCase):
    def review(self,p=None,s=None):return evaluate(p or fixture(),s or Scores(),time.monotonic()+20)

    def test_primary_stays_uniform_whole_answer_without_question_or_meta(self):
        p=fixture();s=Scores();result=self.review(p,s)
        self.assertEqual(result['verdict'],'supported')
        for row in s.records:
            self.assertNotIn(p['question'],row['premise'])
            if row['kind']=='bare_criterion':self.assertEqual(row['premise'],p['learnerResponse'])
        self.assertEqual(len(s.records),len(s.planned_pairs))

    def test_normalization_accepts_source_data_only_and_records_counterexample(self):
        p=fixture('IGNORED_LEARNER_MAGIC')
        p['reports'][0]['facts']=[dict(property='fuel_status',value='complete')]
        second=copy.deepcopy(p['reports'][0]);second.update(id='B',eventTime=13,receiptTime=14,
            message='TRN102 baggage loading is delayed.',facts=[dict(property='baggage_status',value='delayed')])
        p['reports'].append(second);units=raw_sources(grounding_context(p)[0],'A2')
        self.assertFalse(any('IGNORED_LEARNER_MAGIC' in u['text'] or 'PRIVATE_EXPECTED' in u['text'] for u in units))
        relation=next(u for u in units if any(r.get('rule')=='current-separate-service-counterexample-v1' for r in u['canonicalRules']))
        self.assertEqual(set(relation['reportIds']),{'R1','B'})
        self.assertIn('does not establish',relation['text'])
        self.assertTrue(all(f['status']=='current' for r in relation['canonicalRules'] for f in r['preconditions']))

    def test_known_readiness_disables_source_absence_and_authority_is_not_schema_absence(self):
        p=fixture();p['reports'][0]['facts'].append(dict(property='overall_readiness',value='not ready'))
        units=raw_sources(grounding_context(p)[0],'A2')
        self.assertFalse(any(r.get('rule')=='current-readiness-unreported-source-v1' for u in units for r in u['canonicalRules']))
        self.assertFalse(any(r.get('rule')=='explicit-unrepresented-takeoff-source-v1' for u in units for r in u['canonicalRules']))

    def test_entity_scope_is_complete_and_unrelated_actor_not_a_veto(self):
        p=fixture();other=copy.deepcopy(p['reports'][0]);other.update(id='OTHER',aircraftId='A1',flightInstance='TRN101',
            message='TRN101 is at Stand A.',facts=[dict(property='stand',value='A')])
        p['reports'].append(other)
        s=Scores(lambda row:'contradiction' if row['kind'] in ('bare_grounding','bare_grounding_quote') and 'OTHER' in row['reportIds'] else None)
        result=self.review(p,s)
        self.assertEqual(result['points'][-1]['status'],'met')
        ground=[r for r in s.records if r['kind']=='bare_grounding']
        self.assertTrue(all('OTHER' not in r['reportIds'] for r in ground))
        self.assertTrue(all('OTHER' in r['sourceScope']['allCurrentReportIds'] for r in ground))
        self.assertTrue(all(r['sourceScope']['complete'] and 'movement_condition' in r['sourceScope']['propertyScope'] for r in ground))

    def test_wrong_actor_resource_links_and_unbound_extra_are_never_dropped(self):
        p=fixture();p['reports'][0].update(aircraftId='A3',flightInstance='TRN103',message='TRN103 is held for Stand B.',
            facts=[dict(property='movement_condition',value='hold: Stand B occupied by TRN102')])
        other=copy.deepcopy(p['reports'][0]);other.update(id='OCC',aircraftId='A2',flightInstance='TRN102',
            message='TRN102 occupies Stand B.',facts=[dict(property='stand',value='B')])
        p['reports'].append(other);units=raw_sources(grounding_context(p)[0],'A3')
        selected,scope=source_scope(units,'TRN103 is already occupying Stand B instead of TRN102.')
        self.assertEqual(set(scope['includedReportIds']),{'R1','OCC'})
        self.assertEqual(set(scope['actorIds']),{'TRN102','TRN103'})
        self.assertIn('B',scope['resourceIds'])
        selected,scope=source_scope(units,'An engine caught fire.')
        self.assertEqual(scope['entityScope'],'global_unbound')
        self.assertEqual(set(scope['includedReportIds']),{'R1','OCC'})

    def test_neutral_does_not_become_missing_or_unsupported(self):
        s=Scores(lambda row:'neutral' if row['kind'] in ('bare_criterion','bare_grounding') else None)
        result=self.review(s=s)
        self.assertTrue(all(p['status']=='uncertain' for p in result['points']))

    def test_quote_windows_keep_full_negation_qualifiers(self):
        text='It is not true that '+('fuel completion and baggage loading '*6)+'establish permission to depart.'
        bundles=quote_candidates(text)
        self.assertTrue(bundles)
        self.assertTrue(all(b['text']==text for b in bundles))
        for bundle in bundles:
            self.assertTrue(bundle['quoteSpans'][0]['text'].startswith('It is not true'))
            self.assertLessEqual(len(bundle['quoteSpans']),3)
            self.assertTrue(all(len(s['text'])<=160 and text[s['start']:s['end']]==s['text'] for s in bundle['quoteSpans']))

    def test_quote_ranking_preserves_antecedent_and_explicit_scope_together(self):
        first='Fuel and baggage completion and release of TRN102 ground hold leave overall readiness unconfirmed.'
        second='Those reports do not grant takeoff clearance or confirm every departure prerequisite.'
        p=fixture(first+' '+second);p['question']=TYPED_QUESTIONS['late_baggage'][2]
        p['criteria']=[dict(id='unknown',expected='readiness',evidenceIds=['R1']),
            dict(id='scope',expected='authority distinctions',evidenceIds=['R1']),p['criteria'][-1]]
        class ContextScores(Scores):
            def score(self,pairs,deadline):
                rows=super().score(pairs,deadline)
                for row in rows:
                    if row['kind']=='bare_quote_witness':
                        if first in row['premise'] and second in row['premise']:row['probabilities']=[.005,.99,.005]
                        elif row['premise'].startswith('Those reports'):row['probabilities']=[.01,.01,.98]
                return rows
        result=self.review(p,ContextScores());quotes=result['points'][1]['learnerQuotes']
        self.assertIn(first,' '.join(quotes));self.assertIn(second,' '.join(quotes))
        self.assertLessEqual(len(quotes),3)



class ProofEdgesAndQuoteContextTests(unittest.TestCase):
    def authority_fixture(self):
        p=fixture('TRN103 is held because a service vehicle blocks its route.')
        p['reports'].append(dict(id='R2',episodeId=p['episodeId'],aircraftId='A3',flightInstance='TRN103',
            eventTime=2,receiptTime=3,source='ground-control',message='TRN103 is holding.',
            facts=[dict(property='movement_status',value='holding at stand')]))
        p['reports'].append(dict(id='ROUTE',episodeId=p['episodeId'],aircraftId='A2',flightInstance='TRN102',
            eventTime=1,receiptTime=2,source='ground-control',
            message='The reported route is within the apron. No runway or takeoff clearance is represented.',
            facts=[dict(property='route',value='apron ground circuit')]))
        p['criteria'][-1]['evidenceIds']=['R1','R2','ROUTE']
        return p

    def test_authority_search_proof_ids_are_not_semantic_retrieval_edges(self):
        p=self.authority_fixture();units=raw_sources(grounding_context(p)[0],'A2')
        authority=next(u for u in units if any(r.get('rule')=='explicit-unrepresented-takeoff-source-v1' for r in u['canonicalRules']))
        self.assertIn('R2',authority['proofDependencies'])
        self.assertEqual(authority['reportIds'],['ROUTE'])
        self.assertEqual(authority['semanticReportIds'],[])
        selected,scope=source_scope(units,p['learnerResponse'])
        self.assertEqual(scope['actorIds'],['TRN103'])
        self.assertEqual(scope['semanticRawReportIds'],['R2'])
        self.assertFalse(any('service vehicle' in u['text'] for u in selected))
        target,scope=source_scope(units,'TRN102 is held.')
        self.assertIn('R2',scope['proofDependencyReportIds'])
        self.assertNotIn('R2',scope['semanticRawReportIds'])
        self.assertNotIn('TRN103',scope['actorIds'])

    def test_wrong_actor_source_cannot_supply_the_missing_obstruction(self):
        p=self.authority_fixture()
        def scores(row):
            if row['kind'] in ('bare_grounding','bare_grounding_quote'):
                return 'entailment' if 'service vehicle' in row['premise'] else 'contradiction'
        s=Scores(scores);result=evaluate(p,s,time.monotonic()+20)
        self.assertEqual(result['points'][-1]['status'],'contradicted')
        self.assertTrue(all('R1' not in r['reportIds'] for r in s.records if r['kind']=='bare_grounding'))
        self.assertTrue(all('R2' in r['sourceScope']['includedReportIds'] for r in s.records if r['kind']=='bare_grounding'))

    def test_independent_sentences_cannot_create_a_confidence_context_or_parked_tail(self):
        first='The cancellation of safeguarding has been confirmed.'
        second='I do not know that TRN101 has departure clearance because no such confirmation was received; it remains parked.'
        text=first+' '+second;bundles=quote_candidates(text)
        self.assertEqual([b['text'] for b in bundles],[first,second])
        self.assertTrue(all(len(b['quoteSpans'])==1 for b in bundles))
        self.assertFalse(any(q['text']=='parked.' for b in bundles for q in b['quoteSpans']))
        self.assertTrue(all(not b['antecedentSentences'] for b in bundles))

    def test_closed_class_context_is_exact_antecedent_not_independent_support(self):
        first='Fuel service and baggage loading have separately reported statuses.'
        second='Those reports do not establish departure permission.'
        bundles=quote_candidates(first+' '+second)
        contextual=next(b for b in bundles if b['targetSentence']['text']==second)
        self.assertEqual([s['text'] for s in contextual['antecedentSentences']],[first])
        self.assertEqual([s['role'] for s in contextual['quoteSpans']],['necessary_antecedent','target'])
        self.assertEqual(contextual['text'],first+' '+second)
        # Expletive denial is a complete sentence, not an anaphoric invitation
        # to attach an independently discussed earlier status.
        denial='It is not true that fuel completion establishes permission.'
        self.assertTrue(all(not b['antecedentSentences'] for b in quote_candidates(first+' '+denial)))


class ImplicitContextAndResourceClockTests(unittest.TestCase):
    def resource_reports(self):
        old=dict(id='MOVE',episodeId='CLOCK',aircraftId='A2',flightInstance='OP201',source='stand-planning',
            eventTime=10,receiptTime=12,message='OP201 will reposition from K7 to M2. Stand K7 is not yet confirmed available.',
            facts=[dict(property='movement_condition',value='reposition to Stand M2')])
        new=dict(id='AVAILABLE',episodeId='CLOCK',aircraftId='A3',flightInstance='OP202',source='stand-planning',
            eventTime=30,receiptTime=35,message='Stand K7 is confirmed available for OP202. Its exercise ground hold is released.',
            facts=[dict(property='movement_condition',value='Stand K7 available; exercise ground hold released')])
        return [old,new]

    def test_unique_learner_actor_binds_implicit_argument_but_never_multiple_actors(self):
        first='A late baggage batch is delaying TRN102.'
        target='Fuel is complete, but that does not establish completed baggage loading.'
        contextual=next(b for b in quote_candidates(first+' '+target) if b['targetSentence']['text']==target)
        self.assertEqual(contextual['contextKind'],'implicit_actor_argument')
        self.assertEqual([s['text'] for s in contextual['antecedentSentences']],[first])
        self.assertEqual(contextual['text'],first+' '+target)
        ambiguous='TRN102 and TRN103 are waiting.'
        for second in [target,'Its fuel service is complete.']:
            candidate=next(b for b in quote_candidates(ambiguous+' '+second) if b['targetSentence']['text']==second)
            self.assertEqual(candidate['antecedentSentences'],[])
        independent='TRN103 fuel service is complete.'
        candidate=next(b for b in quote_candidates(first+' '+independent) if b['targetSentence']['text']==independent)
        self.assertEqual(candidate['antecedentSentences'],[])

    def test_resource_clock_crosses_actor_boundary_and_retains_original_plan(self):
        reports=self.resource_reports();original=copy.deepcopy(reports)
        p=fixture();p.update(episodeId='CLOCK',cutoff=40,reports=reports)
        current,_=grounding_context(p)
        units=raw_sources(current,'A3',reports,40)
        old=next(u for u in units if u['reportIds']==['MOVE'] and u['sourceFacts'])
        self.assertIn('OP201 will reposition from K7 to M2.',old['text'])
        self.assertIn("movement_condition='reposition to Stand M2'",old['text'])
        self.assertNotIn('not yet confirmed available',old['text'])
        projection=next(r for r in old['canonicalRules'] if r.get('rule')=='actor-message-resource-clock-projection-v1')
        stale=next(r for r in projection['resourceAssertions'] if r['origin']=='message')
        self.assertEqual(stale['value'],'unconfirmed')
        self.assertEqual(stale['resourceStatus'],'historical_resource')
        self.assertEqual(stale['exactSpan']['text'],'Stand K7 is not yet confirmed available.')
        self.assertFalse(projection['messageParts'][1]['inCurrentInput'])
        self.assertEqual(reports,original)

    def test_receipt_eligibility_and_operative_event_clock_not_last_arrival(self):
        reports=self.resource_reports()
        before=resource_availability_view(reports,34)
        self.assertTrue(all(r['reportId']=='MOVE' for r in before))
        self.assertEqual(next(r for r in before if r['origin']=='message')['resourceStatus'],'current_resource')
        delayed=dict(id='DELAYED',episodeId='CLOCK',aircraftId='A4',flightInstance='OP203',source='stand-planning',
            eventTime=20,receiptTime=39,message='Stand K7 is not yet confirmed available.',
            facts=[dict(property='movement_status',value='holding')])
        view=resource_availability_view(reports+[delayed],40)
        self.assertTrue(all(r['resourceStatus']=='historical_resource' for r in view if r['reportId']=='DELAYED'))
        self.assertTrue(all(r['value']=='confirmed_available' for r in view if r['resourceStatus']=='current_resource'))
        # Assignment does not manufacture a new availability update.
        assignment=copy.deepcopy(delayed);assignment.update(id='ASSIGNED',eventTime=38,receiptTime=39,
            message='OP203 is assigned Stand K7.',facts=[dict(property='stand',value='K7')])
        self.assertFalse(any(r['reportId']=='ASSIGNED' for r in resource_availability_view(reports+[assignment],40)))

    def test_same_time_conflict_and_unseparable_mixed_clause_cannot_certify(self):
        reports=self.resource_reports();conflict=copy.deepcopy(reports[0]);conflict.update(id='CONFLICT',eventTime=30,receiptTime=36)
        view=resource_availability_view(reports+[conflict],40)
        self.assertTrue(any(r['resourceStatus']=='ambiguous_resource' for r in view))
        p=fixture();p.update(episodeId='CLOCK',cutoff=40,reports=reports+[conflict])
        current,_=grounding_context(p);units=raw_sources(current,'A3',p['reports'],40)
        self.assertFalse(source_scope(units,'Stand K7 is available.')[1]['complete'])
        reports=self.resource_reports();reports[0]['message']='Stand K7 is not yet confirmed available and OP201 will reposition.'
        p.update(reports=reports);current,_=grounding_context(p)
        unit=next(u for u in raw_sources(current,'A2',reports,40) if u['reportIds']==['MOVE'] and u['sourceFacts'])
        self.assertIn(reports[0]['message'],unit['text'])
        self.assertIn('reposition to Stand M2',unit['text'])
        self.assertFalse(unit['complete'])

    def test_unrecognized_factual_unavailability_is_not_relabelled_unconfirmed(self):
        reports=self.resource_reports();reports[1]['message']='Stand K7 is unavailable.'
        reports[1]['facts'][0]['value']='hold at stand'
        view=resource_availability_view(reports,40)
        latest=[r for r in view if r['reportId']=='AVAILABLE']
        self.assertTrue(all(r['value'] is None and r['resourceStatus']=='ambiguous_resource' for r in latest))
        self.assertFalse(any(r['value']=='unconfirmed' and r['resourceStatus']=='current_resource' for r in view))

    def test_resource_validity_does_not_apply_future_state_or_revive_expired_prior(self):
        reports=self.resource_reports();reports[1]['facts'][0]['validFrom']=50
        view=resource_availability_view(reports,40)
        self.assertTrue(all(r['resourceStatus']=='scheduled' for r in view if r['reportId']=='AVAILABLE'))
        self.assertTrue(all(r['value']=='unconfirmed' for r in view if r['resourceStatus']=='current_resource'))
        reports=self.resource_reports();reports[1]['facts'][0]['validUntil']=38
        view=resource_availability_view(reports,40)
        self.assertTrue(all(r['resourceStatus']=='expired_resource' for r in view if r['reportId']=='AVAILABLE'))
        self.assertFalse(any(r['resourceStatus']=='current_resource' for r in view))
        self.assertTrue(all(r['resourceStatus']=='historical_resource' for r in view if r['reportId']=='MOVE'))

    def test_actor_supersession_does_not_retract_independent_resource_confirmation(self):
        reports=self.resource_reports();later=copy.deepcopy(reports[1]);later.update(id='ACTOR-UPDATE',eventTime=36,receiptTime=37,
            message='OP202 remains parked.',facts=[dict(property='movement_condition',value='parked',supersedes=['AVAILABLE:movement_condition'])])
        p=fixture();p.update(episodeId='CLOCK',cutoff=40,reports=reports+[later])
        current,historical=grounding_context(p)
        self.assertNotIn('AVAILABLE',{r['id'] for r in current})
        units=raw_sources(current,'A3',p['reports'],40)
        resource=next(u for u in units if u['reportIds']==['AVAILABLE'])
        self.assertIn('Stand K7 is confirmed available for OP202.',resource['text'])
        self.assertNotIn('ground hold is released',resource['text'])
        self.assertEqual(resource['properties'],['stand.availability_confirmation'])


class IndependentResourceAmbiguityGuardTests(unittest.TestCase):
    def test_resource_ambiguity_survives_both_actor_field_supersessions(self):
        reports=[]
        for actor,aircraft,state in [('TRN102','A2','Stand B is confirmed available.'),('TRN103','A3','Stand B is not yet confirmed available.')]:
            old=dict(id=actor+'OLD',episodeId='e',aircraftId=aircraft,flightInstance=actor,source='stand-planning',eventTime=10,receiptTime=11,
                message=state,facts=[dict(property='movement_condition',value=state)])
            new=dict(id=actor+'NEW',episodeId='e',aircraftId=aircraft,flightInstance=actor,source='ground-control',eventTime=20,receiptTime=21,
                message=actor+' remains held.',facts=[dict(property='movement_condition',value='hold: further update pending',supersedes=[old['id']+':movement_condition'])])
            reports.extend([old,new])
        p=fixture();p.update(episodeId='e',cutoff=30,reports=reports)
        current,_=grounding_context(p);units=raw_sources(current,'A2',reports,30)
        marker=next(u for u in units if not u['complete'])
        self.assertEqual(marker['actorIds'],[])
        self.assertEqual(set(marker['proofDependencies']),{'TRN102OLD','TRN103OLD'})
        self.assertNotIn('further update pending',marker['text'])
        scoped,scope=source_scope(units,'Stand B is confirmed available.')
        self.assertFalse(scope['complete'])
        self.assertTrue(any(u is marker for u in scoped))
        self.assertFalse(source_scope(units,'An engine caught fire.')[1]['resourceClockComplete'])


if __name__=='__main__':unittest.main()
