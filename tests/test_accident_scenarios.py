import math
import unittest
from backend.lessons import build_lesson, HOUR_EXERCISES
from backend.evidence import received_facts, classify


class AccidentScenarioTests(unittest.TestCase):
    def current(self, world, aid, at):
        return {f['property']:f['value'] for f in classify(received_facts(world,at),at)
                if f['aircraftId']==aid and f['status']=='current'}

    def test_sixty_worlds_incident_order_continuity_and_disabled_aircraft(self):
        for exercise in HOUR_EXERCISES:
            for seed in range(20):
                world,slots,probes=build_lesson(seed,exercise)
                bag,collision,crash=world['incidents'][2:]
                self.assertLess(bag['end'],collision['start'])
                self.assertLess(collision['onset']+90,crash['start'])
                self.assertEqual([p['at'] for p in probes],[60,120,180])
                self.assertTrue(all(a['end']<b['start'] for a,b in zip(slots,slots[1:])))
                self.assertTrue(all(a['end']<b['start'] for a,b in zip(world['runwayReservations'],world['runwayReservations'][1:])))
                for plane,incident in zip(world['aircraft'][1:],(collision,crash)):
                    ws=plane['waypoints']
                    for a,b in zip(ws,ws[1:]):
                        speed=math.sqrt(sum((b.get(k,0)-a.get(k,0))**2 for k in ('x','y','z')))*1000/(b['t']-a['t'])
                        self.assertLess(speed,110)
                    stopped=next(p for p in plane['phases'] if p['id']==('vehicle_collision' if plane['id']=='A2' else 'disabled_runway'))
                    after=[p for p in ws if p['t']>=stopped['t']]
                    self.assertEqual(len({(p['x'],p['z'],p.get('y',0),p['heading']) for p in after}),1)
                    for key in ('start','onset','clearedAt','end'):
                        self.assertIn(incident[key],world['predictionBoundaries'])
                plane=world['aircraft'][2];at=crash['onset']
                self.assertTrue(any(p['t']<at and p.get('y',0)>.4 for p in plane['waypoints']))
                self.assertTrue(all(abs(p['z']+.4)<.0225 and abs(p['x'])<.9
                                    for p in plane['waypoints'] if p['t']>=at))
                self.assertTrue(plane['waypoints'][-1]['gearRetracted'])
                self.assertGreater(plane['waypoints'][-1]['bodySink'],0)

    def test_contact_reports_do_not_precede_impact_or_release_aircraft(self):
        w,_,_=build_lesson(17,'late_arrival');i=w['incidents'][3];at=i['onset']
        self.assertNotIn('contact',self.current(w,'A2',at+1.99).get('movement_condition',''))
        self.assertIn('contact',self.current(w,'A2',at+2)['movement_condition'])
        later=self.current(w,'A2',at+57)
        self.assertIn('inspection and movement release pending',later['movement_condition'])
        self.assertEqual(self.current(w,'A2',3599)['movement_condition'],later['movement_condition'])
        self.assertNotIn('injury_status',later)

    def test_crash_containment_does_not_reopen_runway_or_reveal_future_status(self):
        w,_,_=build_lesson(17,'late_arrival');i=w['incidents'][4];at=i['onset']
        self.assertIn('emergency arrival',self.current(w,'A3',at+1.99)['movement_condition'])
        self.assertIn('crash landing',self.current(w,'A3',at+2)['movement_condition'])
        self.assertNotIn('contained',self.current(w,'A3',at+57.99)['movement_condition'])
        after=self.current(w,'A3',at+62)
        self.assertEqual(after['movement_status'],'disabled on Runway 09')
        self.assertIn('Runway 09 closed: fire contained',after['movement_condition'])
        self.assertEqual(self.current(w,'A3',3599),after)
        self.assertNotIn('cause',after)


if __name__=='__main__':unittest.main()
