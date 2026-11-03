"""Post-run completeness and descriptive audit; never changes frozen scores or labels."""
import argparse,json,math
from collections import Counter
from pathlib import Path
from experiments.typed_review_lora.evaluate import score


def audit(data,records):
    expected={r['id']:r for r in data}
    if not expected or len(expected)!=len(data):raise ValueError('empty or duplicate source cases')
    seen=Counter((r['id'],r['arm']) for r in records)
    required={(cid,arm) for cid in expected for arm in ('base','adapter')}
    if set(seen)!=required or any(n!=1 for n in seen.values()):raise ValueError('Evaluation is incomplete, duplicated, or contains unexpected records')
    result={}
    for arm in ('base','adapter'):
        rr=[r for r in records if r['arm']==arm]
        confusion=Counter();by_family={};by_kind={}
        for r in rr:
            row=expected[r['id']]
            if r['family']!=row['family'] or r['kind']!=row['kind']:raise ValueError('record identity differs from source')
            if not math.isfinite(r['elapsed']) or r['elapsed']<0:raise ValueError('invalid latency')
            s=r['score']
            if s!=score(r['raw'],row):raise ValueError('stored score does not replay')
            if s['valid']:
                points=json.loads(r['raw'])['points']
                for pred,gold in zip(points,row['target']['points']):confusion[gold['status']+' -> '+pred['status']]+=1
            else:
                for gold in row['target']['points']:confusion[gold['status']+' -> rejected']+=1
            for group,key in ((by_family,row['family']),(by_kind,row['kind'])):
                bucket=group.setdefault(key,dict(count=0,valid=0,exact=0,false_acceptance=0,supported_accepted=0,supported_case=0))
                bucket['count']+=1
                for k in ('valid','exact','false_acceptance','supported_accepted','supported_case'):bucket[k]+=s[k]
        lat=sorted(r['elapsed'] for r in rr)
        result[arm]={'count':len(rr),'confusion':dict(confusion),'by_family':by_family,'by_kind':by_kind,
                     'median_latency':(lat[(len(lat)-1)//2]+lat[len(lat)//2])/2,'p95_latency':lat[math.ceil(.95*len(lat))-1],
                     'input_tokens':sum(r['input_tokens'] for r in rr),'output_tokens':sum(r['output_tokens'] for r in rr),
                     'stop_reasons':dict(Counter(r['stop_reason'] for r in rr)),'errors':dict(Counter(r['error'] for r in rr if r['error']))}
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--records',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise ValueError('refusing to overwrite an audit')
    read=lambda p:[json.loads(s) for s in p.read_text().splitlines()]
    a.out.write_text(json.dumps(audit(read(a.data),read(a.records)),indent=2)+'\n')
