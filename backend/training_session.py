"""Authoritative lesson clock and assessment state; independent of Unity frames."""
import copy
import hashlib
import json
from pathlib import Path
import secrets
import threading
import time

from backend.lessons import EXERCISES, HOUR_EXERCISES, TITLES, OBJECTIVES, build_lesson
from backend.fog_lesson import FOG_LESSON
from backend.runway_scenarios import DEMONSTRATIONS, TITLES as DEMO_TITLES, OBJECTIVES as DEMO_OBJECTIVES, build_demonstration
from backend.fleet_scenarios import FLEET_DEMONSTRATIONS, TITLES as FLEET_TITLES, OBJECTIVES as FLEET_OBJECTIVES, build_fleet
from backend.training_environment import attach_environment, ENVIRONMENTS
from evidencekit import SourceRecord, check_references
from backend.training_assessment import MAX_RESPONSE_CHARS, ReviewContext, rubric_for, typed_question_for

class ActionConflict(ValueError): pass
class ReviewBusy(ActionConflict): pass

class TrainingSession:
    def __init__(self, seed, exercise='surface_conflict', mode='lesson', clock=time.monotonic, audit_path=None, environment=None, assessment_mode='typed'):
        if mode not in ('lesson','continuous','demo'): raise ValueError('Unknown training mode')
        if exercise not in EXERCISES+DEMONSTRATIONS+FLEET_DEMONSTRATIONS: raise ValueError('Unknown exercise')
        if mode=='lesson' and exercise in DEMONSTRATIONS+FLEET_DEMONSTRATIONS: raise ValueError('This case is a demonstration, not a practice lesson; use --mode demo or continuous')
        if exercise==FOG_LESSON:
            if mode!='lesson':raise ValueError('fog_restrictions is a 210-second lesson with typed practice feedback; use --mode lesson, or fog_visibility for the separate one-hour demonstration')
            if environment not in (None,'fog'):raise ValueError('The fog practice lesson requires its fog timeline; omit --environment or use fog')
        if environment is None:environment='clear'
        if environment not in ENVIRONMENTS: raise ValueError('Unknown environment')
        if exercise=='fog_visibility' and environment not in ('clear','fog'):
            raise ValueError('The fog demonstration requires its fog timeline')
        if assessment_mode not in ('typed','choice'):raise ValueError('Unknown assessment mode')
        self.assessment_mode=assessment_mode
        self.environment=environment
        self.seed=seed;self.exercise=exercise;self.mode=mode;self.clock=clock
        self.audit_path=Path(audit_path) if audit_path else None
        self.lock=threading.RLock();self.transitions={};self._reset()

    def _reset(self):
        self.run_id=secrets.token_hex(10);self.revision=0;self.source_time=0.;self.last_wall=self.clock()
        self.started_wall=self.last_wall;self.phase='briefing' if self.mode=='lesson' else 'practice'
        builder=build_fleet if self.exercise in FLEET_DEMONSTRATIONS else build_demonstration if self.exercise in DEMONSTRATIONS else build_lesson
        self.scenario,self.reservations,self.probes=builder(self.seed,self.exercise)
        self.title={**TITLES,**DEMO_TITLES,**FLEET_TITLES}[self.exercise]
        self.objective={**OBJECTIVES,**DEMO_OBJECTIVES,**FLEET_OBJECTIVES}[self.exercise]
        self.target='A1' if self.exercise in DEMONSTRATIONS+FLEET_DEMONSTRATIONS or self.exercise==FOG_LESSON else 'A3' if self.exercise=='late_arrival' else 'A2'
        effective_environment='fog' if self.exercise in ('fog_visibility',FOG_LESSON) else self.environment
        # The short scored lesson already owns a validated 210-second fog curve.
        # Applying the hour-long visual profile would extend it past its clock.
        if self.exercise!=FOG_LESSON:attach_environment(self.scenario,effective_environment)
        self.demo_probes=sorted(self.probes+self.scenario.get('demoQuestions',[]),key=lambda p:p['at'])
        self.scenario['scenarioId']='LESSON-'+self.run_id
        self.records=[SourceRecord(self.scenario['scenarioId'],e['id'],e['eventTime'],e['receiptTime'],'report')
                      for e in self.scenario['events']]
        self.world_boundaries=sorted({e['receiptTime'] for e in self.scenario['events']} |
            set(self.scenario.get('predictionBoundaries',[p['t'] for a in self.scenario['aircraft']+self.scenario.get('groundVehicles',[]) for p in a['waypoints']])))
        for probe in self.probes:
            check_references(probe['evidenceIds'],self.records,self.scenario['scenarioId'],probe['at'])
        self.answers=[];self.actions={};self.active_probe=0;self.demo_index=0;self.cue=None
        self.review_requests={};self.review_status='idle';self.review_error='';self.response_text='';self.review_action=None
        self.assistant_pending={};self.read_until=0.;self.last_rate=None
        self._log('start',seed=self.seed,exercise=self.exercise,mode=self.mode,environment=effective_environment,assessmentMode=self.assessment_mode,
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
            self.cue=dict(id=p['id'],aircraftId=p.get('aircraftId',self.target),question=p['assistantQuestion'],cutoff=p['at'],status='pending',deadline=wall+40)
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
        if answer.get('kind')=='typed':return copy.deepcopy(answer['feedback'])
        p=next(p for p in self.probes if p['id']==answer['checkpointId'])
        reports={e['id']:e for e in self.scenario['events']}
        later=[e for e in self.scenario['events'] if p['at']<e['receiptTime']<=self.source_time
               and e['aircraftId']==p.get('aircraftId',self.target)][:3]
        return dict(checkpointId=p['id'],question=p['question'],chosen=p['choices'][answer['choice']],
            correctAnswer=p['choices'][p['correct']],correct=answer['correct'],explanation=p['explanation'],
            cutoff=p['at'],reports=[reports[i] for i in p['evidenceIds']],laterReports=later)

    def state(self):
        with self.lock:
            self.advance()
            result=dict(runId=self.run_id,revision=self.revision,mode=self.mode,phase=self.phase,
                title=self.title,objective=self.objective,exercise=self.exercise,
                sourceTime=self.source_time,rate=self._rate(self.clock()),nextBoundary=self._boundary(),
                checkpointNumber=min(self.active_probe+1,len(self.probes)),checkpointCount=len(self.probes),
                answered=len(self.answers),
                assessmentMode=self.assessment_mode,reviewStatus=self.review_status,reviewError=self.review_error,responseText=self.response_text,
                targetAircraft=self.target,
                checkpoint=None,feedback=None,reviews=[],demoCue=None,
                perspectives=[dict(role='Controller',text='Follow identity, restrictions and received updates. An occupied stand stays a reported hold until the availability update; birds leaving view do not establish a runway release.'),
                    dict(role='Pilot',text='Review the reported route and restrictions. A time estimate is not a clearance. Report wildlife location and activity; keep a sighting separate from a suspected or confirmed strike.'),
                    dict(role='Turnaround',text='Report service status and revised estimates separately from readiness. After the fire is contained, the stand remains closed until an explicit update. These are fictional exercises informed by Heathrow guidance.')])
            if self.assessment_mode=='choice':result['score']=sum(a.get('correct',False) for a in self.answers)
            if self.phase=='checkpoint':
                p=self.probes[self.active_probe]
                fields=('id','at','question','choices') if self.assessment_mode=='choice' else ('id','at','question')
                result['checkpoint']={k:p[k] for k in fields}
                if self.assessment_mode=='typed':result['checkpoint']['question']=typed_question_for(self.exercise,p)
            if self.phase=='feedback':result['feedback']=self._feedback(self.answers[-1])
            if self.phase=='debrief':result['reviews']=[self._feedback(a) for a in self.answers]
            if self.exercise in DEMONSTRATIONS+FLEET_DEMONSTRATIONS or self.exercise==FOG_LESSON:
                result['perspectives']=[
                    dict(role='Controller',text=self.objective),
                    dict(role='Pilot',text='Review the latest report for your flight and identify what still needs confirmation.'),
                    dict(role='Turnaround',text='Include active restrictions and outstanding confirmations in the handover.'),
                    dict(role='Scenario basis',text=self.scenario['provenance']['limitations'])]
            if self.cue:result['demoCue']={k:v for k,v in self.cue.items() if k!='deadline'}
            focus=next((f for f in self.scenario.get('flightShowcases',[]) if f['start']<=self.source_time<f['end']),None)
            result['spotlightId']=focus['id'] if focus and self.mode=='demo' else ''
            result['spotlightAircraft']=focus['aircraftId'] if focus and self.mode=='demo' else ''
            focused=next((a for a in self.scenario['aircraft'] if focus and a['id']==focus['aircraftId']),self.scenario['aircraft'][0])
            stages=focused.get('phases',[])
            current=[p for p in stages if p['t']<=self.source_time]
            result['flightPhase']=current[-1]['id'] if current else ''
            return result

    def snapshot(self):
        with self.lock:
            state=self.state()
            return dict(serverTime=state['sourceTime'],scenario=self.scenario,synthetic=True,exerciseTitle=self.title,
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
            if action_id in self.review_requests:raise ActionConflict('Action ID already used by a typed response')
            if action_id in self.actions:
                old,result=self.actions[action_id]
                if old!=fingerprint:raise ActionConflict('Action ID reused with different data')
                return copy.deepcopy(result)
            if body.get('revision')!=self.revision:raise ActionConflict('Exercise phase changed')
            action=body.get('action')
            if action=='ready' and self.phase=='briefing':self._phase('practice')
            elif action=='answer' and self.phase=='checkpoint':
                if self.review_status=='pending':raise ActionConflict('A typed response is being reviewed')
                if any(a.get('kind')=='typed' for a in self.answers):raise ActionConflict('This attempt uses typed responses')
                if self.assessment_mode!='choice':raise ActionConflict('This attempt requires a typed response')
                choice=body.get('choice');p=self.probes[self.active_probe]
                if type(choice)!=int or not 0<=choice<4 or body.get('checkpointId')!=p['id']:raise ValueError('Invalid checkpoint answer')
                row=dict(checkpointId=p['id'],choice=choice,correct=choice==p['correct'],cutoff=p['at'])
                self.answers.append(row);self._log('answer',**row);self._phase('feedback')
            elif action=='continue' and self.phase=='feedback':
                self.active_probe+=1;self.review_status='idle';self.review_error='';self.response_text='';self.review_action=None;self._phase('practice')
            elif action=='demo_answer' and self.mode=='demo' and self.cue and body.get('cueId')==self.cue['id']:
                if self.cue['status']=='pending':
                    self.cue['status']='answered' if body.get('success') is True else 'failed'
                    self.read_until=max(self.read_until,self.clock()+10)
                    self._log('assistant_cue_end',cueId=self.cue['id'],success=body.get('success') is True)
            elif action in ('retry','next') and self.phase=='debrief':
                if action=='next':
                    sequence=FLEET_DEMONSTRATIONS if self.exercise in FLEET_DEMONSTRATIONS else DEMONSTRATIONS if self.exercise in DEMONSTRATIONS else (
                        EXERCISES if self.mode=='lesson' else HOUR_EXERCISES)
                    self.exercise=sequence[(sequence.index(self.exercise)+1)%len(sequence)]
                self._reset()
                result=self.state();self.transitions[transition]=(fingerprint,copy.deepcopy(result))
                return result
            else:raise ActionConflict('Action is not available in this phase')
            result=self.state();self.actions[action_id]=(fingerprint,copy.deepcopy(result));return result

    def prepare_response(self, body, model_available=True):
        """Freeze private review input; duplicates never schedule another model call."""
        with self.lock:
            self.advance()
            keys={'actionId','runId','revision','checkpointId','responseText'}
            if not isinstance(body,dict) or set(body)!=keys:raise ValueError('Invalid response fields')
            action_id=body['actionId'];text=body['responseText']
            if not isinstance(action_id,str) or not 1<=len(action_id)<=80:raise ValueError('Action ID required')
            if type(body['revision'])!=int:raise ValueError('Invalid response revision')
            if not isinstance(text,str) or not text.strip() or len(text)>MAX_RESPONSE_CHARS:
                raise ValueError('Enter a response between 1 and 1200 characters')
            if body['runId']!=self.run_id:raise ActionConflict('This attempt has ended')
            fingerprint=hashlib.sha256(json.dumps(body,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            old=self.review_requests.get(action_id)
            if old:
                if old['fingerprint']!=fingerprint:raise ActionConflict('Action ID reused with different data')
                return None,copy.deepcopy(old['result']) if old.get('result') else self.state()
            if action_id in self.actions:raise ActionConflict('Action ID already used by another action')
            if self.mode!='lesson' or self.phase!='checkpoint' or body['revision']!=self.revision:
                raise ActionConflict('Exercise phase changed')
            probe=self.probes[self.active_probe]
            if body['checkpointId']!=probe['id']:raise ActionConflict('Checkpoint changed')
            if self.review_status=='pending':raise ActionConflict('A response is already being reviewed')
            if self.assessment_mode!='typed':raise ActionConflict('This attempt uses the legacy choice checks')
            if not model_available:raise ReviewBusy('The model is still finishing another request; retry shortly')
            reports=[dict(copy.deepcopy(e),episodeId=self.scenario['scenarioId']) for e in self.scenario['events'] if e['receiptTime']<=probe['at']]
            criteria=rubric_for(self.exercise,probe,reports)
            for criterion in criteria:check_references(criterion['evidenceIds'],self.records,self.scenario['scenarioId'],probe['at'])
            payload=dict(episodeId=self.scenario['scenarioId'],checkpointId=probe['id'],cutoff=probe['at'],
                aircraftId=probe.get('aircraftId',self.target),question=typed_question_for(self.exercise,probe),learnerResponse=text,
                reports=reports,criteria=criteria)
            self.response_text=text;self.review_status='pending';self.review_error='';self.review_action=action_id;self.revision+=1
            context=ReviewContext(self.run_id,self.revision,probe['id'],action_id,fingerprint,json.dumps(payload,sort_keys=True,ensure_ascii=False))
            self.review_requests[action_id]=dict(fingerprint=fingerprint,context=context,result=None)
            self._log('typed_response_start',actionId=action_id,checkpointId=probe['id'],cutoff=probe['at'],responseText=text,fingerprint=fingerprint)
            return context,self.state()

    def finish_response(self, context, review=None, error=None):
        """Apply only the still-active immutable review; a late result is discarded."""
        with self.lock:
            self.advance()
            current=(context.run_id==self.run_id and context.revision==self.revision and
                self.phase=='checkpoint' and self.review_status=='pending' and self.review_action==context.action_id and
                self.probes[self.active_probe]['id']==context.checkpoint_id)
            if not current:
                self._log('typed_response_discarded',responseRunId=context.run_id,actionId=context.action_id,reason=error or 'stale completion')
                return False
            record=self.review_requests.get(context.action_id)
            if not record or record['fingerprint']!=context.fingerprint or record['context']!=context:return False
            payload=json.loads(context.payload_json)
            if error or review is None:
                self.review_status='failed';self.review_error=error or 'Review unavailable. Your response is saved; please retry.';self.revision+=1
                self._log('typed_response_failed',actionId=context.action_id,checkpointId=context.checkpoint_id,error=self.review_error)
            else:
                from backend.training_assessment import validate_review
                # The session boundary also validates references/context; callers
                # cannot inject a review for another run or a future source.
                review=validate_review(json.dumps(review),payload)
                ids={i for point in review['points'] for i in point['evidenceIds']}
                feedback=dict(kind='typed',checkpointId=context.checkpoint_id,question=payload['question'],chosen=payload['learnerResponse'],
                    cutoff=payload['cutoff'],reports=[r for r in payload['reports'] if r['id'] in ids],
                    verdict=review['verdict'],explanation=review['explanation'],points=review['points'])
                self.answers.append(dict(kind='typed',checkpointId=context.checkpoint_id,cutoff=payload['cutoff'],feedback=feedback))
                self.review_status='idle';self.review_error='';self._phase('feedback')
                self._log('typed_response_accepted',actionId=context.action_id,checkpointId=context.checkpoint_id,verdict=review['verdict'],points=review['points'])
            record['result']=copy.deepcopy(self.state())
            return True

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
