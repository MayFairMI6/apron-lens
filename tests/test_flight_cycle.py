import unittest
from backend.lessons import build_lesson, HOUR_EXERCISES
from backend.evidence import received_facts, classify
from backend.training_session import TrainingSession

class FlightCycleTests(unittest.TestCase):
    def test_sixty_circuits_depart_and_land_continuously_after_scored_lesson(self):
        for exercise in HOUR_EXERCISES:
            for seed in range(20):
                world,reservations,probes=build_lesson(seed,exercise)
                plane=world['aircraft'][0];phases={p['id']:p['t'] for p in plane['phases'] if p['id'] not in ('pushback','taxi_in','parked')}
                by_time={p['t']:p for p in plane['waypoints']}
                self.assertEqual([p['at'] for p in probes],[60,120,180])
                self.assertGreater(phases['takeoff_roll'],210)
                self.assertEqual(by_time[phases['rotation']].get('y',0),0)
                self.assertGreater(by_time[phases['climb']]['y'],0)
                self.assertGreater(by_time[phases['approach']]['y'],by_time[phases['flare']]['y'])
                self.assertEqual(by_time[phases['landing_roll']]['y'],0)
                self.assertTrue(by_time[phases['circuit']]['gearRetracted'])
                self.assertFalse(by_time[phases['flare']]['gearRetracted'])
                self.assertGreater(by_time[phases['flare']]['pitch'],0)
                self.assertGreater(by_time[phases['rotation']]['pitch'],0)
                slots=world['runwayReservations'];self.assertLess(slots[0]['end'],slots[1]['start'])
                self.assertTrue(all(a['end']<b['start'] for a,b in zip(reservations,reservations[1:])))
                circuit=next(r for r in reservations if r.get('kind')=='local-flight-circuit')
                self.assertEqual((by_time[round(circuit['end'],3)]['x'],by_time[round(circuit['end'],3)]['z']),(-.045,.04))
                for a,b in zip(plane['waypoints'],plane['waypoints'][1:]):
                    distance=sum((b.get(k,0)-a.get(k,0))**2 for k in ('x','y','z'))**.5*1000
                    self.assertLessEqual(distance/(b['t']-a['t']),110,'No teleport or implausible jump between adjacent positions')

    def test_airborne_reports_do_not_leak_into_earlier_checkpoints(self):
        world,_,_=build_lesson(17,'late_arrival')
        for cutoff in (60,120,180,210):
            self.assertFalse(any(f['source']=='exercise-tower' for f in received_facts(world,cutoff)))
        phase=next(p for p in world['aircraft'][0]['phases'] if p['id']=='climb')
        at=received_facts(world,phase['t'])
        self.assertFalse(any(f['value']=='climb' for f in at))
        later=classify(received_facts(world,phase['t']+.5),phase['t']+.5)
        self.assertTrue(any(f['value']=='climb' and f['status']=='current' for f in later))

    def test_flight_teaching_windows_are_normal_speed_and_expose_focus(self):
        now=[0.];s=TrainingSession(17,'late_arrival','demo',clock=lambda:now[0])
        for window in s.scenario['flightTeachingWindows']:
            s.source_time=window['start'];s.last_wall=now[0];s.demo_index=3;s.cue=None;s.read_until=0
            state=s.state();self.assertEqual(state['rate'],1)
            expected={'baggage-incident':'A2','vehicle-collision':'A2','crash-landing':'A3'}
            self.assertEqual(state['spotlightAircraft'],expected.get(state['spotlightId'],'A1'))
            self.assertLessEqual(state['nextBoundary'],window['end'])
        s.source_time=3500;s.last_wall=now[0]
        self.assertEqual(s.state()['spotlightAircraft'],'')

if __name__=='__main__':unittest.main()
