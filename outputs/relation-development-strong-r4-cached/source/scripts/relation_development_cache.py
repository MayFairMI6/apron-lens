"""Development-only reuse of exact previously measured NLI pairs.

Never use this for acceptance, new-question evaluation, or latency claims.
Only probabilities are reused; current source/rule/criterion metadata is rebuilt.
"""
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path

ALLOWED_FIXTURES = {
 'e6ee0e234919c56276e199419f35627aedd6528702f3003c386d57b25654f397',
 'b385079d10a6b8ea4bcf1d20e417c3b915184ef87e8ce263a268323ef7d00195',
}

class DevelopmentCache:
    def __init__(self, engine, module, paths, fixture_sha):
        if fixture_sha not in ALLOWED_FIXTURES:
            raise ValueError('Cache prohibited outside exact exposed development fixtures')
        self.base=engine;self.module=module;self.records=[];self.planned_pairs=[]
        self.cache={};self.conflicts=set();self.hashes={};self.hits=0;self.misses=0
        self.runtime={x:importlib.metadata.version(x) for x in ('torch','transformers','tokenizers')}
        snapshot=Path.home()/'.cache/huggingface/hub'/('models--'+module.MODEL_ID.replace('/','--'))/'snapshots'/module.MODEL_REVISION
        artifacts={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(snapshot.iterdir()) if p.is_file() and p.name!='README.md'}
        if not {'model.safetensors','tokenizer.json','config.json'}<=set(artifacts):
            raise ValueError('Incomplete pinned classifier provenance')
        self.manifest=dict(kind='development-only exact historical measurement reuse',
            model=module.MODEL_ID,revision=module.MODEL_REVISION,labelOrder=module.LABELS,
            runtime=self.runtime,artifactSHA256=artifacts,device='cpu',maxLength=engine.max_length,
            inferencePrecision='from_pretrained default, pinned config dtype; same CPU engine as frozen runs',
            batchSize=engine.batch_size,files=[],duplicateMaxDelta=0.,conflictingPairs=0,
            provenance='Pinned local HF revision and unchanged installed runtime in this development pass; historical startup records verify torch. Acceptance always uncached.')
        # Earliest lexicographic source wins, independently of score/label.
        for path in sorted(map(Path,paths)):
            lock=json.loads((path.parent/'lock.json').read_text())
            startup=json.loads((path.parent/'startup.json').read_text())
            if lock.get('fixtureSHA256') not in ALLOWED_FIXTURES:
                raise ValueError('Cache source is not exposed development')
            if (lock['model']!=module.MODEL_ID or lock['revision']!=module.MODEL_REVISION
                or startup['torch']!=self.runtime['torch'] or startup['device']!='cpu'):
                raise ValueError('Incompatible development cache provenance')
            data=path.read_bytes();sha=hashlib.sha256(data).hexdigest()
            self.hashes[str(path)]=sha
            for name in ('lock.json','startup.json'):
                p=path.parent/name
                self.hashes[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
            self.manifest['files'].append(dict(path=str(path),sha256=sha,startup=startup))
            for line_no,line in enumerate(data.splitlines()):
                case=json.loads(line)
                if case.get('error'):continue
                for pair_no,row in enumerate(case['pairs']):
                    if row.get('scoreReuse') is not None:continue
                    p=row.get('probabilities')
                    if (row.get('error') or row.get('truncationRejected') or not isinstance(p,list)
                        or len(p)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) or not 0<=x<=1 for x in p)
                        or abs(sum(p)-1)>.001):continue
                    if row.get('modelId')!=module.MODEL_ID or row.get('modelRevision')!=module.MODEL_REVISION:
                        raise ValueError('Cache row model mismatch')
                    if tuple(row.get('labelOrder',()))!=module.LABELS:raise ValueError('Cache label order unknown')
                    key=(row['premise'],row['hypothesis'])
                    provenance=dict(file=str(path),sha256=sha,row=line_no,pair=pair_no)
                    if key in self.cache:
                        old=self.cache[key][0]
                        delta=max(abs(a-b) for a,b in zip(old,p))
                        self.manifest['duplicateMaxDelta']=max(self.manifest['duplicateMaxDelta'],delta)
                        label=lambda v: max(range(3),key=lambda i:v[i]) if max(v)>=module.THRESHOLD else -1
                        if label(old)!=label(p):self.conflicts.add(key)
                    else:self.cache[key]=(p,provenance)
        self.manifest['conflictingPairs']=len(self.conflicts)
        self.manifest['provenanceFileSHA256']=dict(self.hashes)

    def __getattr__(self,name):return getattr(self.base,name)

    def score(self,pairs,deadline):
        self.planned_pairs=list(pairs)
        result=[None]*len(pairs);uncached=[];indices=[]
        for i,pair in enumerate(pairs):
            n=len(self.base.tokenizer(pair['premise'],pair['hypothesis'],truncation=False)['input_ids'])
            if n>self.base.max_length:raise ValueError('Development cache input exceeds unchanged token bound')
            key=(pair['premise'],pair['hypothesis'])
            if key in self.cache and key not in self.conflicts:
                probabilities,provenance=self.cache[key]
                result[i]=dict(**pair,modelId=self.module.MODEL_ID,modelRevision=self.module.MODEL_REVISION,
                    labelOrder=self.module.LABELS,inputTokens=n,probabilities=probabilities,
                    truncationRejected=False,error=None,elapsedSeconds=None,scoreReuse=provenance)
                self.hits+=1
            else:uncached.append(pair);indices.append(i);self.misses+=1
        self.base.records=[]
        try:
            fresh=self.base.score(uncached,deadline) if uncached else []
        except Exception:
            self.records=[r for r in result if r is not None]+self.base.records
            raise
        for i,row in zip(indices,fresh):result[i]=dict(row,scoreReuse=None)
        if any(r is None for r in result):raise ValueError('Cache pair coverage')
        self.records=list(result)
        return result

    def verify(self):
        if any(hashlib.sha256(Path(p).read_bytes()).hexdigest()!=sha for p,sha in self.hashes.items()):
            raise ValueError('Development cache changed during run')
        return dict(hits=self.hits,actualPairs=self.misses,latencyMeaning='mixed reuse/inference; not acceptance timing')
