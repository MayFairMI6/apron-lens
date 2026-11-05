"""Record one complete guided run from an already running local exercise service.

Start backend.training --mode demo first and install/configure the iOS preview.
An active demo is recorded from its current position; a completed one is retried.
This tool never starts or answers scored learner checkpoints.
"""
import argparse
import json
from pathlib import Path
import signal
import subprocess
import time
import urllib.request
import uuid

ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--device',required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--port',type=int,default=8767);p.add_argument('--timeout',type=float,default=600)
    args=p.parse_args()
    token=(ROOT/'work/qwen-server-token.txt').read_text().strip()
    def request(path,body=None):
        data=None if body is None else json.dumps(body).encode()
        r=urllib.request.Request(f'http://127.0.0.1:{args.port}'+path,data=data,
            headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
        return json.load(urllib.request.urlopen(r,timeout=8))
    state=request('/training')
    if state['mode']!='demo':raise SystemExit('The service must use --mode demo; a learner lesson is never changed.')
    if args.output.exists():raise SystemExit('Refusing to overwrite a recording')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    observations=[];started=time.monotonic();completed=False
    with args.output.with_suffix('.capture.log').open('w') as log:
        proc=subprocess.Popen(['xcrun','simctl','io',args.device,'recordVideo','--codec=h264',str(args.output)],stdout=log,stderr=log)
        try:
            # Let simctl attach to the display before resetting the source clock.
            time.sleep(.5)
            if state['phase']=='debrief':
                state=request('/training/action',dict(action='retry',actionId=uuid.uuid4().hex,
                    runId=state['runId'],revision=state['revision']))
            run_id=state['runId']
            while time.monotonic()-started<args.timeout:
                state=request('/training')
                if state['runId']!=run_id:raise RuntimeError('The attempt changed during recording')
                observations.append(dict(wallElapsed=round(time.monotonic()-started,3),
                    **{k:state.get(k) for k in ('runId','sourceTime','rate','phase','demoCue','spotlightId','spotlightAircraft','flightPhase')}))
                if state['phase']=='debrief':completed=True;time.sleep(3);break
                if proc.poll() is not None:raise RuntimeError('Screen recording exited early')
                time.sleep(1)
        finally:
            if proc.poll() is None:proc.send_signal(signal.SIGINT)
            proc.wait(timeout=30)
            args.output.with_suffix('.run.json').write_text(json.dumps(dict(completed=completed,
                exercise=state['exercise'],observations=observations),indent=2)+'\n')
    if not completed:raise SystemExit('The recording stopped before the full hour completed')
    print(f'Recorded the full guided hour: {args.output}')

if __name__=='__main__':main()
