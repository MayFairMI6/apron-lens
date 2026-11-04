"""Three forced real-model recovery cycles with resources measured per owner."""
import os,json,sys,time,subprocess,hashlib
from pathlib import Path
from dataclasses import asdict
from functools import partial
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.worker_fault_probe import FaultProbeAdapter
from backend.training_worker import IsolatedTrainingAdapter
from modelaccess.contract import Settings,Request

def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
    (out/'lock.json').write_text(json.dumps({'cycles':['forced-hang','forced-crash','forced-hang'],'sourceSHA256':hashlib.sha256((ROOT/'backend/training_worker.py').read_bytes()).hexdigest(),'testTimeout':.2,'normalTimeout':55},indent=2))
    factory=partial(FaultProbeAdapter,'qwen3.5-9b',profile='apronlens-v2-mps',prompt_audit_path=out/'selector.jsonl')
    a=IsolatedTrainingAdapter(factory,factory().served_model,audit_path=out/'lifecycle.jsonl')
    settings=Settings(a.served_model,16,image_max_side=672)
    def resource():
        return {'parentRSSKiB':int(subprocess.check_output(['ps','-o','rss=','-p',str(os.getpid())],text=True).strip()),'workerRSSKiB':int(subprocess.check_output(['ps','-o','rss=','-p',str(a._process.pid)],text=True).strip())}
    def descendants(pid):
        pairs=[]
        for line in subprocess.check_output(['ps','-axo','pid=,ppid='],text=True).splitlines():
            child,parent=map(int,line.split());pairs.append((child,parent))
        found={pid}
        while True:
            expanded=found|{child for child,parent in pairs if parent in found}
            if expanded==found:return sorted(found-{pid})
            found=expanded
    def alive(pid):
        try:os.kill(pid,0);return True
        except ProcessLookupError:return False
    rows=[]
    try:
        a.warmup(settings);initial=resource()
        for i,fault in enumerate(['forced-hang','forced-crash','forced-hang']):
            old=a._process.pid;old_descendants=descendants(old);start=time.monotonic();a.generation_timeout=.2
            failure=a.review(Request(fault,(('user','fault probe'),),settings));a.generation_timeout=55.
            deadline=time.monotonic()+300
            while a.status in ('starting','recovering') and time.monotonic()<deadline:time.sleep(.2)
            if a.status!='ready':raise RuntimeError('Recovery failed')
            elapsed=time.monotonic()-start
            reply=a.review(Request('success-'+str(i),(('user','Reply with the word ready.'),),settings))
            row=dict(cycle=i,fault=fault,oldPID=old,newPID=a._process.pid,recoverySeconds=elapsed,failure=asdict(failure),actualReply=asdict(reply),resources=resource(),oldDescendantPIDs=old_descendants,oldOwnerStillAlive=alive(old),oldDescendantsStillAlive=[pid for pid in old_descendants if alive(pid)])
            rows.append(row)
            with (out/'records.jsonl').open('a') as f:f.write(json.dumps(row,default=str)+'\n')
            print(i,fault,elapsed,reply.ok,flush=True)
            assert not failure.ok and reply.ok and reply.text.strip() and old!=a._process.pid
            assert not row['oldOwnerStillAlive'] and not row['oldDescendantsStillAlive']
        (out/'summary.json').write_text(json.dumps({'initialResources':initial,'cyclesCompleted':len(rows),'parentRSSDeltaKiB':rows[-1]['resources']['parentRSSKiB']-initial['parentRSSKiB'],'scope':'three forced cycles, not indefinite stability'},indent=2))
    finally:a.close()
if __name__=='__main__':main()
