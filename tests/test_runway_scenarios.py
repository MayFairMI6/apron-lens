import json
import math
import unittest
from pathlib import Path
from backend.runway_scenarios import DEMONSTRATIONS,build_demonstration,inside_polygon,project,geography
from backend.evidence import validate_scenario,received_facts
from backend.training_session import TrainingSession,ActionConflict

class RunwayCases(unittest.TestCase):
    def test_eighty_seeded_worlds_are_reproducible_and_causal(self):
        for case in DEMONSTRATIONS:
            for seed in range(20):
                w,_,checks=build_demonstration(seed,case)
                self.assertEqual((w,_,checks),build_demonstration(seed,case));validate_scenario(w)
                self.assertEqual(checks,[]);self.assertEqual(len(w['demoQuestions']),3)
                self.assertEqual([a['id'] for a in w['aircraft']],['A1','A2','A3'])
                for a in w['aircraft']+w['groundVehicles']:
                    times=[p['t'] for p in a['waypoints']]
                    self.assertEqual(times,sorted(set(times)));self.assertEqual(times[0],0);self.assertEqual(times[-1],3600)
                for cue in w['demoQuestions']:
                    self.assertTrue(any(e['aircraftId']=='A1' and e['receiptTime']<=cue['at'] for e in w['events']))
                self.assertEqual(w['provenance']['kind'],'authored-precedent-informed')

    def test_rejection_decelerates_and_stops_within_actual_runway(self):
        for seed in range(20):
            w,_,_=build_demonstration(seed,'rejected_takeoff');a=w['aircraft'][0]
            start=next(p['t'] for p in a['phases'] if p['id']=='rejected_takeoff')
            p=[p for p in a['waypoints'] if start<=p['t']<3600]
            speeds=[math.hypot(b['x']-a['x'],b['z']-a['z'])*1000/(b['t']-a['t']) for a,b in zip(p,p[1:])]
            self.assertTrue(all(a>b for a,b in zip(speeds,speeds[1:])))
            self.assertTrue(all(p['y']==0 for p in a['waypoints']))
            runway=next(f for f in w['geography']['features'] if f['id']=='osm-way-2798800')
            lo,hi=sorted([runway['points'][0]['x'],runway['points'][-1]['x']])
            self.assertTrue(all(lo<p['x']<hi for p in a['waypoints']))
            self.assertEqual(a['waypoints'][-1]['x'],a['waypoints'][-2]['x'])
            self.assertEqual(w['incidents'],[])

    def test_go_around_never_lands_and_other_aircraft_remains_on_runway(self):
        w,_,_=build_demonstration(17,'occupied_runway_go_around');a,b=w['aircraft'][:2]
        self.assertTrue(all(p['y']>0 for p in a['waypoints']))
        self.assertGreater(a['waypoints'][-1]['y'],a['waypoints'][2]['y'])
        self.assertGreater(a['waypoints'][-1]['x']-a['waypoints'][-2]['x'],100)
        self.assertLess(w['flightShowcases'][0]['end'],300)
        self.assertEqual(b['waypoints'][0]['x'],b['waypoints'][-1]['x'])
        self.assertTrue(any('occupied by TRN102' in e['message'] or 'TRN102 has not vacated' in e['message'] for e in w['events']))

    def test_incursion_cancels_before_roll_and_uses_smooth_vehicle_turn(self):
        w,_,_=build_demonstration(17,'runway_incursion');a=w['aircraft'][0]
        self.assertEqual((a['waypoints'][0]['x'],a['waypoints'][0]['z']), (a['waypoints'][-1]['x'],a['waypoints'][-1]['z']))
        turns=w['taxiPaths'][0]['turns'];self.assertTrue(turns)
        self.assertTrue(all(t['radiusMetres']>0 and abs(t['sweepDegrees'])<=90.01 for t in turns))
        self.assertFalse(any(i['kind'] in ('vehicle_collision','engine_fire') for i in w['incidents']))
        self.assertTrue(any('not started' in e['message'] for e in w['events']))

    def test_water_ground_path_and_wings_stay_inside_real_shoreline(self):
        for seed in range(20):
            w,_,_=build_demonstration(seed,'water_landing');a=w['aircraft'][0]
            poly=next(f['points'] for f in w['geography']['features'] if f['kind']=='water')
            for p in a['waypoints']:
                if p['y']==0:
                    for dx,dz in [(0,0),(-.025,-.025),(.025,.025),(-.025,.025),(.025,-.025)]:
                        self.assertTrue(inside_polygon(p['x']+dx,p['z']+dz,poly))
            self.assertFalse(w['provenance']['localEventClaim'])
            self.assertFalse(any(i['kind']=='engine_fire' for i in w['incidents']))
            self.assertTrue(all(p.get('gearRetracted') for p in a['waypoints']))

    def test_map_provenance_projection_and_real_separation(self):
        g=geography();self.assertIn('OpenStreetMap',g['attribution'])
        self.assertEqual(project(-.46,51.47),(0.,0.))
        self.assertGreater(project(-.45,51.47)[0],0);self.assertGreater(project(-.46,51.48)[1],0)
        water=next(f for f in g['features'] if f['kind']=='water')
        runway=next(f for f in g['features'] if f['id']=='osm-way-2798800')
        self.assertLess(max(p['x'] for p in water['points']),min(p['x'] for p in runway['points']))
        self.assertLess(min(p['z'] for p in water['points']),min(p['z'] for p in runway['points']))
        source=json.loads((Path(__file__).resolve().parents[1]/'data/geography/heathrow-west.json').read_text())
        self.assertTrue(all(('osmTimestamp' in f and 'osmVersion' in f) or
                            (f.get('sourceType')=='FlightGear BTG' and f.get('sourceSha256') and f.get('license'))
                            for f in source['features']))

    def test_terminal_three_roof_preserves_courtyard(self):
        f=next(f for f in geography()['features'] if f['id']=='osm-relation-18911624')
        def signed_area(p):return sum(a['x']*b['z']-b['x']*a['z'] for a,b in zip(p,p[1:]+p[:1]))/2
        expected=abs(signed_area(f['points']))-sum(abs(signed_area(h['points'])) for h in f['holes'])
        triangles=f['roofTriangles'];points=f['roofPoints'];total=0
        for i in range(0,len(triangles),3):
            tri=[points[j] for j in triangles[i:i+3]];area=signed_area(tri)
            self.assertGreater(area,0);total+=area
            centre={axis:sum(p[axis] for p in tri)/3 for axis in ('x','z')}
            self.assertTrue(inside_polygon(centre['x'],centre['z'],f['points']))
            self.assertFalse(any(inside_polygon(centre['x'],centre['z'],h['points']) for h in f['holes']))
        self.assertAlmostEqual(total,expected,places=10)

    def test_only_incident_participants_are_visible(self):
        for case in DEMONSTRATIONS:
            w,_,_=build_demonstration(17,case)
            expected=['A1','A2'] if case=='occupied_runway_go_around' else ['A1']
            self.assertEqual([a['id'] for a in w['aircraft'] if not a.get('hidden')],expected)

    def test_no_new_scored_lessons_and_new_runs_reject_stale_actions(self):
        for case in DEMONSTRATIONS:
            with self.assertRaises(ValueError):TrainingSession(17,case,'lesson')
            now=[0];s=TrainingSession(17,case,'demo',clock=lambda:now[0]);state=s.state()
            self.assertEqual(state['checkpointCount'],0);self.assertEqual(state['targetAircraft'],'A1')
            old=s.run_id;now[0]=10000;self.assertEqual(s.state()['phase'],'debrief')
            s.action(dict(runId=old,revision=s.revision,actionId='next',action='next'))
            self.assertNotEqual(old,s.run_id)
            with self.assertRaises(ActionConflict):s.action(dict(runId=old,revision=s.revision,actionId='stale',action='retry'))

    def test_acceleration_does_not_create_extra_evidence(self):
        for case in DEMONSTRATIONS:
            a=TrainingSession(17,case,'continuous',clock=lambda:0)
            b=TrainingSession(17,case,'demo',clock=lambda:0)
            for cutoff in [0,60,90,120,300,610,3600]:
                self.assertEqual(received_facts(a.scenario,cutoff),received_facts(b.scenario,cutoff))
            self.assertTrue(all(r['kind']=='report' for r in b.snapshot()['sourceRecords']))

if __name__=='__main__':unittest.main()
