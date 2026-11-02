import json
import unittest
from backend.traffic import make_scenario
from backend.training_adapter import selector_context,expand_selection
from backend.conversation.turns import build_prompt
from backend.conversation.validate import validate_proposal

class TrainingSelectorTests(unittest.TestCase):
    def setUp(self):
        self.data,_=make_scenario(7,'late_baggage',role='ramp')
        prompt=build_prompt(self.data,25,('A2','TRN102'),None,[],{},'Is it ready to depart?')
        self.prompt,self.candidates=selector_context(prompt)
        self.flight=next(c for c in self.candidates if c['aircraftId']=='A2')
    def proposal(self,ids,unknowns=[]):
        return json.loads(expand_selection(json.dumps(dict(aircraftId='A2',flightInstance='TRN102',fact_ids=ids,unknowns=unknowns)),self.candidates))
    def test_reference_expansion_passes_unchanged_validation(self):
        fid=next(f['fact_id'] for f in self.flight['facts'] if f['property']=='tobt' and f['status']=='current')
        self.assertTrue(validate_proposal(self.proposal([fid],['overall_readiness']),self.data,25)['accepted'])
    def test_invented_evidence_is_not_repaired_into_a_valid_answer(self):
        r=validate_proposal(self.proposal(['invented:stand']),self.data,25)
        self.assertFalse(r['accepted']);self.assertIn('claim_outside_eligible_evidence',r['errors'])
    def test_known_property_cannot_be_presented_as_unknown(self):
        r=validate_proposal(self.proposal([],['stand']),self.data,25)
        self.assertFalse(r['accepted']);self.assertIn('unknown_contradicts_current_fact',r['errors'])

    def test_stand_answer_uses_only_reports_received_at_cutoff(self):
        from backend.lessons import build_lesson
        data,_,_=build_lesson(17,'late_arrival')
        release=next(e for e in data['events'] if e['aircraftId']=='A3'
                     and e['facts'][0]['value']=='Stand B available; exercise ground hold released')
        for cutoff in (120,release['receiptTime']-.001,release['receiptTime']):
            base=build_prompt(data,cutoff,('A3','TRN103'),None,[],{},'Is the stand available?')
            _,candidates=selector_context(base)
            facts=candidates[0]['facts']
            current=next(f for f in facts if f['property']=='movement_condition' and f['status']=='current')
            if cutoff<release['receiptTime']:
                self.assertIn('occupied',current['value'])
                self.assertNotIn(release['id'],{f['event_id'] for f in facts})
            else:self.assertEqual(current['event_id'],release['id'])
            selection=dict(aircraftId='A3',flightInstance='TRN103',fact_ids=[current['fact_id']],unknowns=[])
            proposal=json.loads(expand_selection(json.dumps(selection),candidates))
            self.assertTrue(validate_proposal(proposal,data,cutoff)['accepted'])
            # Reproduce the original model error: never silently remove it.
            selection['unknowns']=['movement_condition']
            proposal=json.loads(expand_selection(json.dumps(selection),candidates))
            self.assertEqual(proposal['unknowns'],['movement_condition'])
            self.assertIn('unknown_contradicts_current_fact',validate_proposal(proposal,data,cutoff)['errors'])

    def test_genuinely_missing_service_remains_unknown(self):
        from backend.lessons import build_lesson
        data,_,_=build_lesson(17,'late_arrival')
        base=build_prompt(data,120,('A3','TRN103'),None,[],{},'Is fuel service complete?')
        _,candidates=selector_context(base)
        selection=dict(aircraftId='A3',flightInstance='TRN103',fact_ids=[],unknowns=['fuel_status'])
        proposal=json.loads(expand_selection(json.dumps(selection),candidates))
        result=validate_proposal(proposal,data,120)
        self.assertTrue(result['accepted']);self.assertEqual(result['display']['unknowns'],['fuel_status'])
    def test_duplicate_references_remain_rejected(self):
        fid=self.flight['facts'][0]['fact_id']
        self.assertFalse(validate_proposal(self.proposal([fid,fid]),self.data,25)['accepted'])
    def test_role_context_is_explicit_and_frozen_evidence_stays_the_same(self):
        base=build_prompt(self.data,25,('A2','TRN102'),None,[],{},'What restriction is reported?')
        controller,c1=selector_context(base,'controller_awareness')
        pilot,c2=selector_context(base,'pilot_awareness')
        self.assertIn('Controller awareness',controller)
        self.assertIn('Pilot awareness',pilot)
        self.assertEqual(c1,c2)
        self.assertNotEqual(controller,pilot)

    def test_one_json_fence_changes_format_only(self):
        fid=self.flight['facts'][0]['fact_id']
        raw=json.dumps(dict(aircraftId='A2',flightInstance='TRN102',fact_ids=[fid],unknowns=['stand']))
        plain=expand_selection(raw,self.candidates)
        for language in ('json',''):
            self.assertEqual(expand_selection('```'+language+'\n'+raw+'\n```',self.candidates),plain)
        self.assertFalse(validate_proposal(json.loads(plain),self.data,25)['accepted'])

    def test_fences_do_not_accept_prose_extra_documents_or_invalid_json(self):
        raw=json.dumps(dict(aircraftId='A2',flightInstance='TRN102',fact_ids=[],unknowns=[]))
        for value in ('Answer: '+raw,'```json\n'+raw+'\n``` extra','```json\n'+raw+raw+'\n```','```json\n{bad}\n```'):
            with self.assertRaises(ValueError):expand_selection(value,self.candidates)

    def test_incomplete_json_is_not_fabricated(self):
        with self.assertRaises(ValueError):expand_selection('{"aircraftId":',self.candidates)

if __name__=='__main__':unittest.main()
