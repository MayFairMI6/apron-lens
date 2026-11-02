import math
import unittest
from backend.lessons import build_lesson, EXERCISES
from backend.ground_routes import rounded_path, departure_path
from backend.training_session import TrainingSession
from backend.evidence import received_facts, classify

def delta(a,b):return (a-b+180)%360-180

def segment_distance(x,z,a,b):
    dx,dz=b['x']-a['x'],b['z']-a['z'];n=dx*dx+dz*dz
    f=max(0,min(1,((x-a['x'])*dx+(z-a['z'])*dz)/n)) if n else 0
    return math.hypot(x-a['x']-f*dx,z-a['z']-f*dz)

class GroundIncidentTests(unittest.TestCase):
    def test_exact_quarter_turn_radius_tangent_heading_and_five_degree_steps(self):
        for vertices in [[(0,0),(.1,0),(.1,.1)],[(0,0),(.1,0),(.1,-.1)]]:
            path,turns=rounded_path(vertices,radius=.02);turn=turns[0]
            self.assertAlmostEqual(abs(turn['sweepDegrees']),90)
            self.assertAlmostEqual(turn['radiusMetres'],20)
            arc=path[turn['firstPoint']:turn['lastPoint']+1]
            for p in arc:self.assertAlmostEqual(math.hypot(p['x']-turn['centerX'],p['z']-turn['centerZ']),.02,places=7)
            for a,b in zip(arc,arc[1:]):
                self.assertLessEqual(abs(delta(a['heading'],b['heading'])),5.0001)
                chord=math.degrees(math.atan2(b['x']-a['x'],b['z']-a['z']))
                mean=a['heading']+delta(b['heading'],a['heading'])/2
                self.assertAlmostEqual(delta(chord,mean),0,places=3)

    def test_reverse_pushback_keeps_nose_then_enters_forward_tangent_turn(self):
        for side in (-1,1):
            push,taxi,turns=departure_path((0,.04),[(0,-.025),(side*.2,-.025),(side*.2,-.1)])
            self.assertTrue(all(p['heading']==0 for p in push))
            self.assertAlmostEqual(taxi[0]['heading'],0)
            self.assertEqual((push[-1]['x'],push[-1]['z']),(taxi[0]['x'],taxi[0]['z']))
            self.assertAlmostEqual(taxi[18]['heading'],90 if side>0 else 270)

    def test_all_sixty_worlds_ground_movements_have_pavement_and_monotone_times(self):
        for exercise in EXERCISES:
            for seed in range(20):
                world,_,_=build_lesson(seed,exercise)
                segments=[(a,b,p['width']/2) for p in world['taxiPaths'] for a,b in zip(p['points'],p['points'][1:])]
                for aircraft in world['aircraft']:
                    self.assertTrue(aircraft['preciseHeading'])
                    for a,b in zip(aircraft['waypoints'],aircraft['waypoints'][1:]):
                        self.assertGreater(b['t'],a['t'])
                        if a.get('y',0)>0 or b.get('y',0)>0:continue
                        if a['x']==b['x'] and a['z']==b['z']:continue
                        for fraction in (0,.5,1):
                            x=a['x']+(b['x']-a['x'])*fraction;z=a['z']+(b['z']-a['z'])*fraction
                            runway=abs(x)<=.9 and abs(z+.4)<=.0225
                            paved=runway or any(segment_distance(x,z,u,v)<=width+1e-7 for u,v,width in segments)
                            self.assertTrue(paved,(exercise,seed,aircraft['id'],a['t'],x,z))

    def test_wildlife_hold_inspection_release_precede_runway_entry(self):
        world,_,_=build_lesson(17,'late_arrival');plane=world['aircraft'][0]
        wildlife=world['incidents'][0];entry=world['runwayReservations'][0]['start']
        events=world['events'];hold=next(e for e in events if 'birds reported' in e['facts'][0]['value'])
        inspect=next(e for e in events if 'inspection complete;' in e['facts'][0]['value'])
        release=next(e for e in events if e['facts'][0]['value']=='exercise runway departure authorised')
        self.assertLess(wildlife['end'],inspect['receiptTime']);self.assertLess(inspect['receiptTime'],release['receiptTime']);self.assertLess(release['receiptTime'],entry)
        at_hold=[p for p in plane['waypoints'] if hold['eventTime']<=p['t']<=entry]
        self.assertEqual(len({(p['x'],p['z']) for p in at_hold}),1)
        before=classify(received_facts(world,release['receiptTime']-.01),release['receiptTime']-.01)
        self.assertTrue(any('awaiting exercise controller' in f['value'] and f['status']=='current' for f in before))
        self.assertFalse(any(f['value']=='exercise runway departure authorised' for f in before))

    def test_fire_holds_aircraft_until_end_and_other_traffic_until_reported_release(self):
        world,slots,_=build_lesson(17,'late_arrival');fire=world['incidents'][1]
        a=world['aircraft'][0]
        after=[p for p in a['waypoints'] if p['t']>=fire['start']]
        self.assertTrue(all((p['x'],p['z'],p.get('y',0))==(-.045,.04,0) for p in after))
        for slot in slots:
            if slot['start']>fire['start']:self.assertGreater(slot['start'],fire['start']+107)
        facts=classify(received_facts(world,fire['end']+3),fire['end']+3)
        self.assertTrue(any('Stand A closed pending inspection' in f['value'] and f['status']=='current' for f in facts))
        self.assertFalse(any('engine fire' in f['value'] for f in received_facts(world,fire['start']+1.99)))

    def test_semantic_prediction_boundaries_allow_dense_arc_samples_but_not_new_reports(self):
        now=[0.];s=TrainingSession(17,'late_arrival','continuous',clock=lambda:now[0])
        arc=next(p for p in s.scenario['taxiPaths'] if p['turns'])['turns'][0]
        dense=[p['t'] for p in s.scenario['aircraft'][1]['waypoints']]
        interpolation=next(t for t in dense if t>70 and t not in s.world_boundaries)
        now[0]=interpolation-.01;state=s.state()
        self.assertGreater(state['nextBoundary'],interpolation)
        next_report=min(e['receiptTime'] for e in s.scenario['events'] if e['receiptTime']>state['sourceTime'])
        self.assertLessEqual(state['nextBoundary'],next_report)

    def test_extra_demo_questions_target_correct_flight_without_changing_scored_questions(self):
        s=TrainingSession(17,'late_arrival','demo',clock=lambda:0)
        self.assertEqual(len(s.probes),3);self.assertEqual(len(s.demo_probes),11)
        for i,p in enumerate(s.demo_probes[3:],3):
            s.demo_index=i;s.source_time=p['at'];s._arrive(0)
            self.assertEqual(s.cue['aircraftId'],'A1' if i<5 else 'A2' if i<9 else 'A3');self.assertEqual(s.cue['status'],'pending')
            self.assertLess(p['at'],s.scenario['duration'])

    def test_dropped_load_is_after_lessons_and_reserves_aircraft_until_cart_clears(self):
        for exercise in EXERCISES:
            for seed in range(20):
                world,slots,probes=build_lesson(seed,exercise)
                incident=next(i for i in world['incidents'] if i['kind']=='baggage_spill')
                self.assertGreater(incident['start'],210)
                self.assertEqual([p['at'] for p in probes],[60,120,180])
                self.assertTrue(incident['start']<incident['onset']<incident['clearedAt']<incident['end'])
                for boundary in ('start','onset','clearedAt','end'):
                    self.assertIn(incident[boundary],world['predictionBoundaries'])
                plane=world['aircraft'][1]
                before=[p for p in plane['waypoints'] if p['t']<=incident['start']][-1]
                after=[p for p in plane['waypoints'] if p['t']>=incident['end']][0]
                self.assertEqual((before['x'],before['z']),(after['x'],after['z']))
                self.assertGreater(after['t'],incident['end'])
                self.assertAlmostEqual(incident['x'],before['x']+.018)
                self.assertAlmostEqual(incident['z'],before['z']-.018)
                self.assertFalse(any(s['start']<incident['end'] and s['end']>incident['start']
                    and s.get('kind')!='dropped-load-response' for s in slots))

    def test_collecting_bags_does_not_release_hold_or_leak_future_reports(self):
        world,_,_=build_lesson(17,'late_arrival')
        spill=next(i for i in world['incidents'] if i['kind']=='baggage_spill');start=spill['start']
        def current(at):
            return {f['property']:f['value'] for f in classify(received_facts(world,at),at)
                    if f['aircraftId']=='A2' and f['status']=='current'}
        self.assertNotIn('spilled',str(current(spill['onset']+.9)))
        self.assertIn('Stand C',current(start+14)['movement_condition'])
        self.assertEqual(current(start+14)['baggage_status'],'paused: bags spilled from cart')
        self.assertEqual(current(start+47)['movement_condition'],'hold: bags collected; inspection and movement release pending')
        self.assertEqual(current(start+62)['baggage_status'],'complete')
        phases=world['aircraft'][1]['phases']
        self.assertEqual([p for p in phases if p['t']<=start+62][-1]['label'],'Area inspected · movement held')
        self.assertIn('release pending',current(start+71.99)['movement_condition'])
        self.assertTrue(current(start+72)['movement_condition'].startswith('exercise ground hold released'))
        self.assertNotIn('overall_readiness',current(start+72))

if __name__=='__main__':unittest.main()
