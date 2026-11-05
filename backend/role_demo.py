"""Three role views over identical world data, sharing one local model.

Each authenticated /demo/reset starts a fresh conversation namespace at the
same exercise time. This is an instructor recording control, not learner UI.
"""
import asyncio
import copy
import hashlib
import json
import secrets
import threading
import time
from pathlib import Path
from fastapi import Header, HTTPException
from backend.traffic import make_scenario, traffic_app, ROLES, PROFILES, ROOT, DURATION
from backend.training_adapter import TrainingAdapter
from modelaccess.contract import Settings

ROLE_PORTS={'controller_awareness':8770,'pilot_awareness':8771,'ramp':8772}
START_TIME=70.0

def world_hash(scenario):
    return hashlib.sha256(json.dumps({k:scenario[k] for k in ('aircraft','events','duration','visualProps')},sort_keys=True).encode()).hexdigest()

class RoleView:
    def __init__(self,canonical,reservations,role,clock=time.monotonic):
        self.canonical=canonical;self.reservations=reservations;self.role=role;self.clock=clock;self.generation=0
        self.exercise=canonical['trainingProfile'];self.reset()
    def reset(self):
        self.generation+=1;self.started=self.clock();self.scenario=copy.deepcopy(self.canonical)
        track=ROLES[self.role];profile=PROFILES[self.exercise]
        self.scenario.update(scenarioId=f'DEMO-surface-{self.role.replace("_","-")}-{self.generation}',
            trainingRole=self.role,trainingRoleLabel=track['label'],trainingObjective=profile['roleObjectives'][self.role],
            assistantQuestionLabels=track['questionLabels'],assistantQuestions=profile['roleQuestions'][self.role])
    def snapshot(self):
        return dict(serverTime=min(DURATION,START_TIME+self.clock()-self.started),scenario=self.scenario,
                    exerciseTitle=ROLES[self.role]['shortLabel']+' · Surface conflict',synthetic=True)

def demo_app(adapter,settings,driver):
    app=traffic_app(adapter,settings,driver,audit_path=ROOT/'work/three-role-conversations.jsonl')
    @app.post('/demo/reset')
    def reset(authorization: str|None=Header(default=None)):
        if not secrets.compare_digest(authorization or '', 'Bearer '+app.state.token):raise HTTPException(401,'Connection token required')
        driver.reset();app.state.scenarios[driver.scenario['scenarioId']]=driver.scenario
        return {'scenarioId':driver.scenario['scenarioId'],'worldHash':world_hash(driver.scenario),'startTime':START_TIME}
    return app

async def main():
    import uvicorn
    canonical,reservations=make_scenario(1,'surface_conflict',role='ramp')
    audit=ROOT/'work/three-role-prompts.jsonl'
    # Load once; all roles use the exact same weights and serialized inference.
    owner=TrainingAdapter('qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=audit)
    engine=owner.load();lock=threading.Lock()
    class SharedAdapter(TrainingAdapter):
        def _generate(self,request,effective):
            with lock:return super()._generate(request,effective)
    servers=[]
    for role,port in ROLE_PORTS.items():
        adapter=SharedAdapter('qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=audit,
                              training_role=role,engine_factory=lambda *args,**kwargs:engine)
        driver=RoleView(canonical,reservations,role)
        settings=Settings(adapter.served_model,768,image_max_side=672)
        app=demo_app(adapter,settings,driver)
        servers.append(uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,access_log=False)))
    (ROOT/'work/three-role-world.json').write_text(json.dumps(dict(seed=1,worldHash=world_hash(canonical),
        startTime=START_TIME,canonical=canonical,reservations=reservations),indent=2))
    print('THREE_ROLE_DEMO_READY '+world_hash(canonical),flush=True)
    await asyncio.gather(*(s.serve() for s in servers))

if __name__=='__main__':asyncio.run(main())
