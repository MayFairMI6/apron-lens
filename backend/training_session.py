"""Authoritative lesson clock and assessment state; independent of Unity frames."""
import copy
import hashlib
import json
from pathlib import Path
import secrets
import threading
import time

from backend.lessons import EXERCISES, TITLES, OBJECTIVES, build_lesson
from evidencekit import SourceRecord, check_references

class ActionConflict(ValueError): pass

class TrainingSession:
    def __init__(self, seed, exercise='surface_conflict', mode='lesson', clock=time.monotonic, audit_path=None):
        if mode not in ('lesson','continuous','demo'): raise ValueError('Unknown training mode')
        self.seed=seed;self.exercise=exercise;self.mode=mode;self.clock=clock
        self.audit_path=Path(audit_path) if audit_path else None
        self.lock=threading.RLock();self.transitions={};self._reset()

    def _reset(self):
        self.run_id=secrets.token_hex(10);self.revision=0;self.source_time=0.;self.last_wall=self.clock()
        self.started_wall=self.last_wall;self.phase='briefing' if self.mode=='lesson' else 'practice'
        self.scenario,self.reservations,self.probes=build_lesson(self.seed,self.exercise)
        self.demo_probes=sorted(self.probes+self.scenario.get('demoQuestions',[]),key=lambda p:p['at'])
        self.scenario['scenarioId']='LESSON-'+self.run_id
        self.records=[SourceRecord(self.scenario['scenarioId'],e['id'],e['eventTime'],e['receiptTime'],'report')
                      for e in self.scenario['events']]
        self.world_boundaries=sorted({e['receiptTime'] for e in self.scenario['events']} |
            set(self.scenario.get('predictionBoundaries',[p['t'] for a in self.scenario['aircraft']+self.scenario.get('groundVehicles',[]) for p in a['waypoints']])))
        for probe in self.probes:
            check_references(probe['evidenceIds'],self.records,self.scenario['scenarioId'],probe['at'])
        self.answers=[];self.actions={};self.active_probe=0;self.demo_index=0;self.cue=None
        self.assistant_pending={};self.read_until=0.;self.last_rate=None
        self._log('start',seed=self.seed,exercise=self.exercise,mode=self.mode,
                  worldHash=hashlib.sha256(json.dumps({k:v for k,v in self.scenario.items() if k!='scenarioId'},sort_keys=True).encode()).hexdigest())

    def _log(self, event, **values):
        if self.audit_path:
            self.audit_path.parent.mkdir(parents=True,exist_ok=True)
            with self.audit_path.open('a') as f:
                f.write(json.dumps(dict(recordVersion=1,event=event,runId=self.run_id,sourceTime=self.source_time,
                    wallElapsed=self.clock()-self.started_wall,revision=self.revision,**values))+'\n')

    def _phase(self, phase):
        self.phase=phase;self.revision+=1;self._log('phase',phase=phase)

    def _rate(self, wall):
        if self.phase!='practice': return 0.
        if self.mode!='demo': return 1.
        if self.assistant_pending or wall<self.read_until or (self.cue and self.cue['status']=='pending'):return 1.
        teaching=any(p['at']-10<=self.source_time<p['at']+20 for p in self.demo_probes)
        flight=any(w['start']<=self.source_time<w['end'] for w in self.scenario.get('flightTeachingWindows',[]))
        return 1. if teaching or flight else 30.

    def _boundary(self):
        if self.phase!='practice':return self.source_time
        end=210. if self.mode=='lesson' else 3600.
        points=[end]
        # Rendering prediction cannot cross a report arrival or motion change
        # until the server has published that part of the timeline.
        points += [t for t in self.world_boundaries if self.source_time+1e-8<t<=end]
        if self.mode=='lesson' and self.active_probe<len(self.probes):points.append(self.probes[self.active_probe]['at'])
        if self.mode=='demo':
            points += [p['at']+d for p in self.demo_probes for d in (-10,20) if p['at']+d>self.source_time+1e-8]
            points += [w[k] for w in self.scenario.get('flightTeachingWindows',[]) for k in ('start','end') if w[k]>self.source_time+1e-8]
            if self.demo_index<len(self.demo_probes):points.append(self.demo_probes[self.demo_index]['at'])
        return min(t for t in points if t>=self.source_time-1e-8)

    def _arrive(self, wall):
        if self.mode=='lesson' and self.active_probe<len(self.probes) and self.source_time>=self.probes[self.active_probe]['at']-1e-7:
            self.source_time=self.probes[self.active_probe]['at'];self._phase('checkpoint')
        elif self.mode=='demo' and self.demo_index<len(self.demo_probes) and self.source_time>=self.demo_probes[self.demo_index]['at']-1e-7:
            p=self.demo_probes[self.demo_index];self.demo_index+=1
            self.cue=dict(id=p['id'],aircraftId=p.get('aircraftId','A3' if self.exercise=='late_arrival' else 'A2'),question=p['assistantQuestion'],cutoff=p['at'],status='pending',deadline=wall+40)
            self._log('assistant_cue',cueId=p['id'],question=p['assistantQuestion'])
        if self.source_time>=(210 if self.mode=='lesson' else 3600)-1e-7:
            self._phase('debrief')

    def advance(self):
        with self.lock:
            now=self.clock();wall=self.last_wall
            if now<wall:raise ValueError('Monotonic clock moved backward')
            while wall<now-1e-9:
                # Expirations are wall-time events. Integrate across them rather
                # than applying the current speed to the entire polling gap.
                for rid,deadline in list(self.assistant_pending.items()):
                    if wall>=deadline:
                        del self.assistant_pending[rid];self.read_until=max(self.read_until,wall+10)
                if self.cue and self.cue['status']=='pending' and wall>=self.cue['deadline']:
                    self.cue['status']='timeout';self.read_until=max(self.read_until,wall+10)
                    self._log('assistant_cue_timeout',cueId=self.cue['id'])
                rate=self._rate(wall)
                if rate!=self.last_rate:self.last_rate=rate;self._log('rate',rate=rate)
                if not rate:wall=now;break
                boundary=self._boundary()
                if boundary<=self.source_time+1e-8:
                    self._arrive(wall);continue
                until=min(now,wall+(boundary-self.source_time)/rate)
                expirations=list(self.assistant_pending.values())+[self.read_until]
                if self.cue and self.cue['status']=='pending':expirations.append(self.cue['deadline'])
                until=min([until]+[t for t in expirations if t>wall+1e-9])
                self.source_time=min(boundary,self.source_time+(until-wall)*rate);wall=until
                if self.source_time>=boundary-1e-7:
                    self.source_time=boundary;self._arrive(wall)
            self.last_wall=now
            return self.source_time

    def _feedback(self, answer):
        p=next(p for p in self.probes if p['id']==answer['checkpointId'])
        reports={e['id']:e for e in self.scenario['events']}
        later=[e for e in self.scenario['events'] if p['at']<e['receiptTime']<=self.source_time
               and e['aircraftId']==('A3' if self.exercise=='late_arrival' else 'A2')][:3]
        return dict(checkpointId=p['id'],question=p['question'],chosen=p['choices'][answer['choice']],
            correctAnswer=p['choices'][p['correct']],correct=answer['correct'],explanation=p['explanation'],
            cutoff=p['at'],reports=[reports[i] for i in p['evidenceIds']],laterReports=later)

    def state(self):
        with self.lock:
            self.advance()
            result=dict(runId=self.run_id,revision=self.revision,mode=self.mode,phase=self.phase,
                title=TITLES[self.exercise],objective=OBJECTIVES[self.exercise],exercise=self.exercise,
                sourceTime=self.source_time,rate=self._rate(self.clock()),nextBoundary=self._boundary(),
                checkpointNumber=min(self.active_probe+1,3),checkpointCount=3,
                score=sum(a['correct'] for a in self.answers),answered=len(self.answers),
                targetAircraft='A3' if self.exercise=='late_arrival' else 'A2',
                checkpoint=None,feedback=None,reviews=[],demoCue=None,
                perspectives=[dict(role='Controller',text='Follow identity, restrictions and received updates. An occupied stand stays a reported hold until the availability update; birds leaving view do not establish a runway release.'),
                    dict(role='Pilot',text='Review the reported route and restrictions. A time estimate is not a clearance. Report wildlife location and activity; keep a sighting separate from a suspected or confirmed strike.'),
                    dict(role='Turnaround',text='Report service status and revised estimates separately from readiness. After the fire is contained, the stand remains closed until an explicit update. These are fictional exercises informed by Heathrow guidance.')])
            if self.phase=='checkpoint':
                p=self.probes[self.active_probe]
                result['checkpoint']={k:p[k] for k in ('id','at','question','choices')}
            if self.phase=='feedback':result['feedback']=self._feedback(self.answers[-1])
            if self.phase=='debrief':result['reviews']=[self._feedback(a) for a in self.answers]
            if self.cue:result['demoCue']={k:v for k,v in self.cue.items() if k!='deadline'}
            focus=next((f for f in self.scenario.get('flightShowcases',[]) if f['start']<=self.source_time<f['end']),None)
            result['spotlightId']=focus['id'] if focus and self.mode=='demo' else ''
            result['spotlightAircraft']=focus['aircraftId'] if focus and self.mode=='demo' else ''
            stages=self.scenario['aircraft'][0].get('phases',[])
            current=[p for p in stages if p['t']<=self.source_time]
            result['flightPhase']=current[-1]['id'] if current else ''
            return result

    def snapshot(self):
        with self.lock:
            state=self.state()
            return dict(serverTime=state['sourceTime'],scenario=self.scenario,synthetic=True,exerciseTitle=TITLES[self.exercise],
                clock=dict(runId=self.run_id,revision=self.revision,rate=state['rate'],state=self.phase,nextBoundary=state['nextBoundary']),training=state,
                sourceRecords=[r.wire() for r in self.records if r.available_time<=state['sourceTime']])

    def action(self, body):
        with self.lock:
            self.advance()
            action_id=body.get('actionId')
            if not isinstance(action_id,str) or not 1<=len(action_id)<=80:raise ValueError('Action ID required')
            fingerprint=json.dumps(body,sort_keys=True)
            transition=(body.get('runId'),action_id)
            if transition in self.transitions:
                old,result=self.transitions[transition]
                if old!=fingerprint:raise ActionConflict('Action ID reused with different data')
                return copy.deepcopy(result)
            if body.get('runId')!=self.run_id:raise ActionConflict('This attempt has ended')
            if action_id in self.actions:
                old,result=self.actions[action_id]
                if old!=fingerprint:raise ActionConflict('Action ID reused with different data')
                return copy.deepcopy(result)
            if body.get('revision')!=self.revision:raise ActionConflict('Exercise phase changed')
            action=body.get('action')
            if action=='ready' and self.phase=='briefing':self._phase('practice')
            elif action=='answer' and self.phase=='checkpoint':
                choice=body.get('choice');p=self.probes[self.active_probe]
                if type(choice)!=int or not 0<=choice<4 or body.get('checkpointId')!=p['id']:raise ValueError('Invalid checkpoint answer')
                row=dict(checkpointId=p['id'],choice=choice,correct=choice==p['correct'],cutoff=p['at'])
                self.answers.append(row);self._log('answer',**row);self._phase('feedback')
            elif action=='continue' and self.phase=='feedback':
                self.active_probe+=1;self._phase('practice')
            elif action=='demo_answer' and self.mode=='demo' and self.cue and body.get('cueId')==self.cue['id']:
                if self.cue['status']=='pending':
                    self.cue['status']='answered' if body.get('success') is True else 'failed'
                    self.read_until=max(self.read_until,self.clock()+10)
                    self._log('assistant_cue_end',cueId=self.cue['id'],success=body.get('success') is True)
            elif action in ('retry','next') and self.phase=='debrief':
                if action=='next':self.exercise=EXERCISES[(EXERCISES.index(self.exercise)+1)%len(EXERCISES)]
                self._reset()
                result=self.state();self.transitions[transition]=(fingerprint,copy.deepcopy(result))
                return result
            else:raise ActionConflict('Action is not available in this phase')
            result=self.state();self.actions[action_id]=(fingerprint,copy.deepcopy(result));return result

    def begin_question(self, body):
        with self.lock:
            self.advance()
            if body.get('scenarioId')!=self.scenario['scenarioId'] or self.phase not in ('practice','debrief'):
                raise ActionConflict('Questions are unavailable at this checkpoint')
            cutoff=body.get('checkpoint')
            if isinstance(cutoff,bool) or not isinstance(cutoff,(float,int)) or not 0<=cutoff<=self.source_time+0.05:
                raise ValueError('Question cutoff is ahead of the external clock')
            rid=body.get('requestId','')
            self.assistant_pending[rid]=self.clock()+40
            self._log('question_start',requestId=rid,cutoff=cutoff)
            return self.run_id,self.revision

    def end_question(self, body, context, success):
        with self.lock:
            self.advance()
            if context[0]!=self.run_id:return False
            self.assistant_pending.pop(body.get('requestId',''),None)
            if self.mode=='demo':self.read_until=max(self.read_until,self.clock()+10)
            self._log('question_end',requestId=body.get('requestId'),cutoff=body.get('checkpoint'),success=success)
            return context==(self.run_id,self.revision)
