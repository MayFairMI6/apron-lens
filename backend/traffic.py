"""External, seeded ground-traffic driver for the training app, separate from held-out replays.

The shared taxi circuit is reserved for one moving aircraft at a time. This is
an intentionally conservative exercise model, not operational ATC separation.
"""
import argparse
import json
import math
import random
import secrets
import time
from pathlib import Path
from fastapi import Header, HTTPException
from backend.conversation.server import create_app, local_token, ROOT
from modelaccess.contract import Settings

CATALOG = json.loads((ROOT/'data/training/scenarios.json').read_text())
PROFILES = {p['id']: p for p in CATALOG}
ROLES = {r['id']:r for r in json.loads((ROOT/'data/training/role_profiles.json').read_text())}
DURATION = 3600.0

def make_scenario(seed, exercise=None, role='controller_awareness'):
    track=ROLES[role];exercise=exercise or track['defaultExercise']
    rng = random.Random(seed); profile = PROFILES[exercise]
    data = dict(scenarioId=f'TRAIN-{role.replace("_","-")}-{exercise.replace("_", "-")}-{seed}', duration=DURATION,
                trainingProfile=exercise, trainingRole=role, trainingRoleLabel=track['label'],
                trainingObjective=profile['roleObjectives'][role], assistantQuestionLabels=track['questionLabels'],
                assistantQuestions=profile['roleQuestions'][role], targetWidth=.7, livery='uniform', clockWhileUntracked='runs', aircraft=[], events=[], visualProps=[])
    last = {}; reservations = []
    def report(a, t, prop, value, message, source='exercise-control', lag=None):
        delay = rng.uniform(.5, 5) if lag is None else lag
        if t+delay > DURATION: return
        event_id = f'T{len(data["events"])+1:04d}'; key=(a['id'],prop)
        fact = dict(property=prop,value=value)
        if key in last: fact['supersedes']=[last[key]]
        last[key] = event_id+':'+prop
        data['events'].append(dict(id=event_id,aircraftId=a['id'],flightInstance=a['flightInstance'],source=source,
                                   eventTime=round(t,3),receiptTime=round(t+delay,3),facts=[fact],message=message))
    for i,x in enumerate([-.045,.035,.115]):
        a=dict(id=f'A{i+1}',flightInstance=f'TRN10{i+1}',waypoints=[dict(t=0,x=x,z=.04)])
        data['aircraft'].append(a)
        report(a,0,'stand','ABC'[i],f'{a["id"]} assigned Stand {"ABC"[i]}.','stand-planning',0)
        report(a,1,'movement_condition','hold: '+profile['report'],profile['report'],lag=1)
        report(a,2,'route','training ground circuit; stand '+ 'ABC'[i],
               'Reported route is the fictional training ground circuit from Stand '+ 'ABC'[i]+'. No runway or takeoff clearance is represented.','ground-control',1)
        report(a,3,'movement_status','holding at stand','Aircraft is reported holding at its stand.','ground-control',1)
        if role=='ramp' or exercise=='fuel_delay':
            report(a,4,'fuel_status','in progress','Fuelling is in progress.','ground-handling',1)
        if role=='ramp' or exercise=='late_baggage':
            report(a,5,'baggage_status','in progress','Baggage loading is in progress.','ground-handling',1)
    target=data['aircraft'][1]
    # Exercise injections concern the selected departure A2. Off-screen inbound/runway
    # incidents affect its movement condition; they do not turn a parked aircraft into
    # an airborne incident participant.
    if exercise in ('late_baggage','late_arrival','late_departure'):
        report(target,6,'tobt','10:20 training clock','Initial target off-block estimate is 10:20. This is not takeoff clearance.','operations',1)
        report(target,12,'tobt','10:35 training clock','Target off-block estimate revised to 10:35; the previous estimate is superseded.','operations',rng.uniform(3,9))
    if exercise=='late_baggage':
        report(target,8,'baggage_status','delayed','A late baggage batch is holding loading completion.','ground-handling',rng.uniform(1,7))
    elif exercise=='fuel_delay':
        report(target,8,'fuel_status','interrupted','Fuelling interrupted; no completion confirmation received.','ground-handling',rng.uniform(1,7))
    elif exercise=='conflicting_stand':
        previous=last[(target['id'],'stand')]
        report(target,8,'stand','C','Another source reports Stand C; this conflicts with Stand B.','handling-dispatch',rng.uniform(1,5))
        conflict=data['events'][-1];conflict['facts'][0].pop('supersedes',None)
        report(target,18,'stand','B','Stand planning confirms B and corrects the conflicting C assignment; physical position did not change.','stand-planning',rng.uniform(2,8))
        data['events'][-1]['facts'][0]['supersedes'].append(previous)
    elif exercise=='emergency_landing':
        report(target,18,'movement_condition','hold: inbound touchdown confirmed; restriction remains','Exercise control confirms the off-screen inbound has landed; the departure restriction remains.','exercise-control',rng.uniform(3,9))
    elif exercise=='late_arrival':
        report(target,18,'movement_condition','hold: inbound delay confirmed; stand availability unconfirmed','Inbound delay confirmed; intended stand availability has not been confirmed.','stand-planning',rng.uniform(1,7))
    elif exercise in ('takeoff_accident','landing_accident','rejected_takeoff'):
        report(target,18,'movement_condition','hold: runway restriction confirmed; cause and reopening time unknown','Exercise control confirms the affected runway restriction. Cause and reopening time are not established.','exercise-control',rng.uniform(2,9))
    elif exercise=='surface_conflict':
        report(target,18,'movement_condition','hold: ground route conflict confirmed','Ground control confirms a vehicle conflict on the ground route. A route release has not been received.','ground-control',rng.uniform(1,7))
    ready=rng.uniform(*profile['hold'])
    for a in data['aircraft']:
        if role=='ramp' or exercise=='fuel_delay':report(a,ready-10,'fuel_status','complete','Fuel service completion reported.','ground-handling')
        if role=='ramp' or exercise=='late_baggage':report(a,ready-5,'baggage_status','complete','Baggage loading completion reported.','ground-handling')
        report(a,ready,'movement_condition','released','Exercise controller advances to the apron movement phase and releases the exercise hold. This is not a real runway reopening or takeoff clearance.')
    # Reserve the entire circuit. Random order/timing/speed change between seeds, but
    # no aircraft starts the shared route before the preceding aircraft has parked.
    slot=ready+8; order=[2,0,1]; rng.shuffle(order); cycle=0
    while slot < DURATION-200:
        a=data['aircraft'][order[cycle%3]]; x=a['waypoints'][0]['x']; start=slot+rng.uniform(2,12)
        points=[(x,.04),(x,-.025),(.24,-.025),(.27,-.065),(.24,-.105),(-.22,-.105),(-.25,-.065),(-.22,-.005),(x,-.005),(x,.04)]
        # Round taxi corners with quadratic curves (geometry only; speed is bounded).
        rounded=[points[0],points[1]]
        for i in range(2,len(points)-1):
            before,p,after=points[i-1],points[i],points[i+1]
            def toward(q):
                dx,dz=q[0]-p[0],q[1]-p[1]; length=math.hypot(dx,dz); d=min(.012,length*.25)
                return p[0]+dx*d/length,p[1]+dz*d/length
            entry,leave=toward(before),toward(after)
            rounded.append(entry)
            for j in range(1,7):
                u=j/6;rounded.append(((1-u)**2*entry[0]+2*(1-u)*u*p[0]+u*u*leave[0],(1-u)**2*entry[1]+2*(1-u)*u*p[1]+u*u*leave[1]))
        rounded.append(points[-1]); speed=rng.uniform(.004,.006); t=start; plan=[dict(t=round(start,3),x=x,z=.04)]
        for i,p in enumerate(rounded[1:],1):
            old=rounded[i-1]; segment_speed=.002 if i==1 else speed
            t+=math.dist(old,p)/segment_speed
            plan.append(dict(t=round(t,3),x=round(p[0],7),z=round(p[1],7),reverse=i==1))
            if i==1:
                t+=rng.uniform(3,9);taxi_start=t;plan.append(dict(t=round(t,3),x=p[0],z=p[1]))
        if t>DURATION-5:break
        a['waypoints'].extend(plan)
        if cycle>0:
            report(a,start-7,'movement_condition','hold: awaiting training ground-route availability',
                   'The selected flight is reported holding for training ground-route availability.','ground-control',1)
            report(a,start-2,'movement_condition','released',
                   'The exercise hold is released for the ground circuit. This does not establish takeoff clearance.','exercise-control',1)
        report(a,start,'movement_status','pushback','Ground control reports pushback started.','ground-control')
        report(a,taxi_start,'movement_status','taxiing','Ground control reports taxi movement on the training circuit.','ground-control',8)
        report(a,t,'movement_status','parked','Aircraft returned to its training stand.','ground-control',0)
        reservations.append(dict(aircraftId=a['id'],start=start,end=t,speedMetresPerSecond=speed*1000,taxiStart=taxi_start))
        slot=t+10;cycle+=1
    for a in data['aircraft']:
        final=a['waypoints'][-1];a['waypoints'].append(dict(t=DURATION,x=final['x'],z=final['z']))
    return data,reservations

class TrafficDriver:
    def __init__(self, seed, exercise=None, clock=time.monotonic, role='controller_awareness'):
        self.role=role;self.seed=seed;self.exercise=exercise or ROLES[role]['defaultExercise'];self.clock=clock;self.started=clock()
        self.scenario,self.reservations=make_scenario(seed,self.exercise,role)
    def snapshot(self):
        return dict(serverTime=min(DURATION,self.clock()-self.started),scenario=self.scenario,
                    exerciseTitle=ROLES[self.role]['shortLabel']+' · '+PROFILES[self.exercise]['title'],synthetic=True)

def traffic_app(adapter,settings,driver,audit_path=None):
    scenarios={driver.scenario['scenarioId']:driver.scenario}
    options={} if audit_path is None else {'audit_path':audit_path}
    app=create_app(adapter,settings,scenarios=scenarios,**options)
    @app.get('/traffic')
    def traffic(authorization: str|None=Header(default=None)):
        if not secrets.compare_digest(authorization or '', 'Bearer '+app.state.token):raise HTTPException(401,'Connection token required')
        return driver.snapshot()
    return app

if __name__=='__main__':
    import uvicorn
    from backend.training_adapter import TrainingAdapter
    parser=argparse.ArgumentParser();parser.add_argument('--exercise',choices=PROFILES)
    parser.add_argument('--role',choices=ROLES,default='controller_awareness')
    parser.add_argument('--seed',type=int);parser.add_argument('--port',type=int,default=8767)
    args=parser.parse_args();seed=args.seed if args.seed is not None else secrets.randbelow(2**31)
    driver=TrafficDriver(seed,args.exercise,role=args.role)
    record=ROOT/'work/traffic-runs';record.mkdir(parents=True,exist_ok=True)
    (record/f'{driver.scenario["scenarioId"]}.json').write_text(json.dumps(dict(seed=seed,role=args.role,exercise=driver.exercise,scenario=driver.scenario,reservations=driver.reservations),indent=2))
    adapter=TrainingAdapter('qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=ROOT/'work/training-prompts.jsonl',training_role=args.role)
    settings=Settings(model=adapter.served_model,max_output_tokens=768,image_max_side=672)
    local_token();print(f'Training driver: {args.role} / {driver.exercise}; seed {seed}; port {args.port}',flush=True)
    uvicorn.run(traffic_app(adapter,settings,driver),host='127.0.0.1',port=args.port,access_log=False)
