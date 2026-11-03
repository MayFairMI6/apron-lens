import math
import unittest
from backend.fleet_scenarios import FLEET_DEMONSTRATIONS, TYPES, DIMENSIONS, PROCEDURE_09R, build_fleet
from backend.runway_scenarios import inside_polygon
from backend.evidence import validate_scenario, received_facts, classify
from backend.training_session import TrainingSession


def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def intersects(a,b,c,d):return cross(a,b,c)*cross(a,b,d)<-1e-16 and cross(c,d,a)*cross(c,d,b)<-1e-16
def edges(poly):return list(zip(poly,poly[1:]+poly[:1]))
def rectangle(a,p,margin=0):
 d=DIMENSIONS[a['aircraftType']];yaw=math.radians(p['heading']);f=(math.sin(yaw),math.cos(yaw));r=(math.cos(yaw),-math.sin(yaw))
 return [(p['x']+(r[0]*x+f[0]*z)/1000,p['z']+(r[1]*x+f[1]*z)/1000) for x,z in [(-d['span']/2-margin,-d['tail']-margin),(d['span']/2+margin,-d['tail']-margin),(d['span']/2+margin,d['nose']+margin),(-d['span']/2-margin,d['nose']+margin)]]
def point_in(p,poly):return inside_polygon(*p,[dict(x=x,z=z) for x,z in poly])
def polygons_overlap(a,b):return any(point_in(p,b) for p in a) or any(point_in(p,a) for p in b) or any(intersects(*x,*y) for x in edges(a) for y in edges(b))
def line_distance(p,a,b):
 dx=b['x']-a['x'];dz=b['z']-a['z'];u=max(0,min(1,((p[0]-a['x'])*dx+(p[1]-a['z'])*dz)/(dx*dx+dz*dz)))
 return math.hypot(p[0]-a['x']-u*dx,p[1]-a['z']-u*dz)

class FleetCases(unittest.TestCase):
 def test_all_profiles_seeded_causal_and_distinct(self):
  outcomes=[]
  for case in FLEET_DEMONSTRATIONS:
   for seed in range(20):
    w,res,probes=build_fleet(seed,case);self.assertEqual((w,res,probes),build_fleet(seed,case));validate_scenario(w)
    self.assertEqual(set(a['aircraftType'] for a in w['aircraft']),set(TYPES));self.assertEqual(len(w['aircraft']),4)
    self.assertEqual(len(w['demoQuestions']),3);self.assertEqual(probes,[])
    for a in w['aircraft']:
     ts=[p['t'] for p in a['waypoints']];self.assertEqual(ts,sorted(set(ts)));self.assertEqual((ts[0],ts[-1]),(0,3600))
    for q in w['demoQuestions']:
     facts=received_facts(w,q['at']);self.assertTrue(facts);self.assertTrue(all(f['receiptTime']<=q['at'] for f in facts))
   outcomes.append(w['aircraft'][0]['phases'][-1]['id'])
  self.assertEqual(outcomes,['outside_area','stopped','stopped','outside_area'])
  names=[tuple(p['id'] for p in build_fleet(17,c)[0]['aircraft'][0]['phases']) for c in FLEET_DEMONSTRATIONS]
  self.assertEqual(len(set(names)),4)

 def test_parked_full_envelopes_fit_mapped_aprons_and_clear_obstacles(self):
  for case in FLEET_DEMONSTRATIONS:
   w,_,_=build_fleet(17,case);features=w['geography']['features'];parked=[]
   obstacles=[[(p['x'],p['z']) for p in f['points']] for f in features if f['kind'] in ('building','jet_bridge') and f.get('closed')]
   for a in w['aircraft'][1:]:
    if not a['parkingApron']:continue
    bound=rectangle(a,a['waypoints'][0],margin=2)
    apron=next(f for f in features if f['id']==a['parkingApron']);poly=[(p['x'],p['z']) for p in apron['points']]
    self.assertTrue(all(point_in(p,poly) for p in bound),(case,a['aircraftType'],'corners'))
    self.assertFalse(any(intersects(*e,*f) for e in edges(bound) for f in edges(poly)),(case,a['aircraftType'],'edge'))
    self.assertFalse(any(polygons_overlap(bound,o) for o in obstacles),(case,a['aircraftType'],'obstacle'))
    self.assertFalse(any(polygons_overlap(bound,b) for b in parked));parked.append(bound)

 def test_ground_wheels_on_runway_and_stop_inside_end(self):
  for case in FLEET_DEMONSTRATIONS:
   for seed in range(20):
    w,_,_=build_fleet(seed,case);runway=next(f for f in w['geography']['features'] if f['id']=='osm-way-2798800');segments=list(zip(runway['points'],runway['points'][1:]))
    for a in w['aircraft']:
     if a['parkingApron']:continue
     d=DIMENSIONS[a['aircraftType']]
     for p in a['waypoints']:
      if p['y']>1e-8:continue
      yaw=math.radians(p['heading']);f=(math.sin(yaw),math.cos(yaw));r=(math.cos(yaw),-math.sin(yaw))
      for x,z in [(-d['track']/2,0),(d['track']/2,0),(0,d['wheelbase'])]:
       wheel=(p['x']+(r[0]*x+f[0]*z)/1000,p['z']+(r[1]*x+f[1]*z)/1000)
       self.assertLess(min(line_distance(wheel,*s) for s in segments),runway['width']/2,(case,a['id'],p['t']))

 def test_active_envelope_clears_buildings_and_parked_aircraft(self):
  for case in FLEET_DEMONSTRATIONS:
   w,_,_=build_fleet(17,case);a=w['aircraft'][0]
   obstacles=[([(p['x'],p['z']) for p in f['points']],f.get('heightMetres',18)) for f in w['geography']['features'] if f['kind'] in ('building','jet_bridge') and f.get('closed')]
   parked=[rectangle(b,b['waypoints'][0],2) for b in w['aircraft'][1:]]
   for p in a['waypoints']:
    if p['y']>.06:continue
    bounds=rectangle(a,p,2)
    self.assertFalse(any(polygons_overlap(bounds,o) for o,h in obstacles if p['y']*1000<h),(case,p['t'],'building'))
    if p['y']<.03:self.assertFalse(any(polygons_overlap(bounds,b) for b in parked),(case,p['t'],'aircraft'))

 def test_kinematics_and_flight_transitions(self):
  for case in FLEET_DEMONSTRATIONS:
   for seed in range(20):
    a=build_fleet(seed,case)[0]['aircraft'][0];points=a['waypoints'];speeds=[]
    for x,y in zip(points,points[1:]):
     dt=y['t']-x['t'];v=1000*math.hypot(y['x']-x['x'],y['z']-x['z'])/dt;speeds.append(v)
     self.assertLessEqual(v,76);self.assertGreaterEqual(y['y'],0);self.assertLess(y['y'],1.3)
     self.assertLessEqual(abs(y['pitch']-x['pitch'])/dt,3.1)
     if dt<=.5:self.assertLessEqual(abs(y['y']-x['y'])*1000/dt,7.1)
    for x,y in zip(speeds,speeds[1:]):self.assertLess(abs(x-y),2.1)
    if case.endswith('go_around'):self.assertGreater(min(p['y'] for p in points),.045)
    if case.endswith('priority_landing'):
     td=next(p['t'] for p in a['phases'] if p['id']=='landing_roll')
     self.assertTrue(all(p['y']>0 for p in points if p['t']<td));self.assertTrue(all(p['y']==0 for p in points if p['t']>=td))

 def test_report_boundaries_preserve_unknowns_and_separate_release(self):
  w,_,_=build_fleet(17,FLEET_DEMONSTRATIONS[0])
  def current(t):return [f['value'] for f in classify(received_facts(w,t),t) if f['status']=='current' and f['property']=='movement_condition']
  self.assertIn('hold: inspection complete; separate departure release awaited',current(100));self.assertEqual(current(101),['exercise departure release received'])
  for case in FLEET_DEMONSTRATIONS[1:]:
   w,_,_=build_fleet(17,case);facts=classify(received_facts(w,3600),3600)
   state=[f['value'] for f in facts if f['status']=='current' and f['aircraftId']=='A1' and f['property']=='movement_condition']
   self.assertTrue(any('unconfirmed' in v for v in state),case)

 def test_acceleration_has_same_available_evidence_and_next_cycles_fleet(self):
  for case in FLEET_DEMONSTRATIONS:
   wall=[0.];normal_wall=[0.]
   fast=TrainingSession(17,case,'demo',clock=lambda:wall[0]);normal=TrainingSession(17,case,'continuous',clock=lambda:normal_wall[0])
   for _ in range(500):
    wall[0]+=1;state=fast.state();normal_wall[0]=state['sourceTime'];plain=normal.state()
    self.assertAlmostEqual(plain['sourceTime'],state['sourceTime'])
    self.assertEqual(received_facts(normal.scenario,plain['sourceTime']),received_facts(fast.scenario,state['sourceTime']))
    self.assertGreaterEqual(state['nextBoundary']+1e-6,state['sourceTime'])
    if state.get('demoCue') and state['demoCue']['status']=='pending':self.assertEqual(state['rate'],1)
    if state['phase']=='debrief':break
   wall[0]=5000;state=fast.state();self.assertEqual(state['phase'],'debrief')
   before=fast.run_id
   result=fast.action(dict(action='next',actionId='fleet-next',runId=state['runId'],revision=state['revision']))
   self.assertNotEqual(before,fast.run_id);self.assertEqual(fast.exercise,FLEET_DEMONSTRATIONS[(FLEET_DEMONSTRATIONS.index(case)+1)%4])
   self.assertEqual(result['sourceTime'],0);self.assertEqual(len(fast.scenario['aircraft']),4)

 def test_bounded_published_09r_reference_and_authored_flare(self):
  from backend.runway_scenarios import project
  tx,tz=project(PROCEDURE_09R['thresholdLongitude'],PROCEDURE_09R['thresholdLatitude'])
  for seed in range(20):
   w,_,_=build_fleet(seed,'fleet_b787_priority_landing');a=w['aircraft'][0]
   td=next(p['t'] for p in a['phases'] if p['id']=='landing_roll')
   threshold=next(p for p in a['waypoints'] if p['t']==td-5)
   self.assertAlmostEqual(threshold['x'],tx);self.assertAlmostEqual(threshold['z'],tz)
   self.assertAlmostEqual(threshold['y']*1000,50*.3048)
   before=next(p for p in a['waypoints'] if p['t']==td-15)
   horizontal=1000*math.hypot(before['x']-tx,before['z']-tz)
   self.assertAlmostEqual((before['y']-threshold['y'])*1000/horizontal,math.tan(math.radians(3)))
   self.assertEqual(threshold['heading'],89.68)
   self.assertIn('not a modelled ILS antenna',w['provenance']['limitations'])
   w,_,_=build_fleet(seed,'fleet_a380_go_around');a=w['aircraft'][0]
   ceiling=(3000-75.3)*.3048
   self.assertAlmostEqual(a['waypoints'][-1]['y']*1000,ceiling)
   self.assertTrue(all(p['y']*1000<=ceiling+1e-8 for p in a['waypoints']))
   self.assertTrue(all(p['heading']==89.68 for p in a['waypoints']))
   outside=next(p['t'] for p in a['phases'] if p['id']=='outside_area')
   self.assertEqual(w['flightShowcases'][0]['end'],outside)
   self.assertIn('as-directed boundary',w['provenance']['limitations'])

 def test_reservations_and_visual_boundaries(self):
  for case in FLEET_DEMONSTRATIONS:
   for seed in range(20):
    w,res,_=build_fleet(seed,case)
    self.assertEqual(res,w['runwayReservations']);self.assertEqual(len(res),1)
    slot=res[0];self.assertEqual(slot['start'],0)
    self.assertEqual(slot['aircraftId'],'A2' if case.endswith('go_around') else 'A1')
    if case.endswith('birds'):
     airborne=next(p['t'] for p in w['aircraft'][0]['phases'] if p['id']=='climb')
     self.assertGreater(slot['end'],airborne)
    else:self.assertEqual(slot['end'],3600)
    for incident in w['incidents']:
     for key in ('start','end'):self.assertIn(incident[key],w['predictionBoundaries'])

 def test_each_cue_is_delivered_and_failure_is_not_replaced(self):
  for case in FLEET_DEMONSTRATIONS:
   wall=[0.];driver=TrainingSession(17,case,'demo',clock=lambda:wall[0]);seen=[]
   for _ in range(1000):
    wall[0]+=1;state=driver.state();cue=state.get('demoCue')
    if cue and cue['status']=='pending' and cue['id'] not in seen:
     seen.append(cue['id']);self.assertEqual(state['rate'],1)
     success=len(seen)!=2
     driver.action(dict(action='demo_answer',actionId='answer-'+cue['id'],runId=state['runId'],revision=state['revision'],cueId=cue['id'],success=success))
     result=driver.state();self.assertEqual(result['demoCue']['status'],'answered' if success else 'failed')
     before=result['sourceTime'];wall[0]+=9
     self.assertAlmostEqual(driver.state()['sourceTime'],before+9)
    if state['phase']=='debrief':break
   self.assertEqual(seen,[q['id'] for q in driver.scenario['demoQuestions']])
   self.assertEqual(driver.state()['phase'],'debrief')

 def test_session_modes_and_legacy_lists(self):
  from backend.runway_scenarios import DEMONSTRATIONS
  self.assertFalse(set(DEMONSTRATIONS)&set(FLEET_DEMONSTRATIONS))
  for case in FLEET_DEMONSTRATIONS:
   with self.assertRaises(ValueError):TrainingSession(17,case,'lesson')
   normal=TrainingSession(17,case,'continuous');fast=TrainingSession(17,case,'demo')
   for driver in (normal,fast):driver.scenario['scenarioId']='comparison'
   self.assertEqual(normal.scenario,fast.scenario)
   self.assertEqual(normal.target,'A1');self.assertEqual(fast.target,'A1')

if __name__=='__main__':unittest.main()
