"""Sealed paired evaluation, after checkpoint selection. No retries or retuning."""
import argparse,contextlib,json,time
from pathlib import Path
from backend.training_assessment import validate_review
from .runtime import load,encode,metadata,rows,sha,source_hashes


def score(raw,row):
    try:result=validate_review(raw,row['payload'])
    except Exception as exc:
        return {'valid':False,'error':str(exc),'false_acceptance':0,'false_acceptance_criteria':[],'negative_criteria':sum(p['status']!='met' for p in row['target']['points']),
                'correct_statuses':0,'criteria':len(row['target']['points']),'supported_case':row['target']['verdict']=='supported','supported_accepted':False,'exact':False}
    pairs=list(zip(result['points'],row['target']['points']))
    return {'valid':True,'false_acceptance_criteria':[g['criterionId'] for p,g in pairs if p['status']=='met' and g['status']!='met'],'false_acceptance':sum(p['status']=='met' and g['status']!='met' for p,g in pairs),
            'negative_criteria':sum(g['status']!='met' for p,g in pairs),'correct_statuses':sum(p['status']==g['status'] for p,g in pairs),
            'criteria':len(pairs),'supported_case':row['target']['verdict']=='supported',
            'supported_accepted':row['target']['verdict']=='supported' and result['verdict']=='supported',
            'exact':all(p['status']==g['status'] for p,g in pairs)}


def summarize(records):
    summary={}
    for arm in ('base','adapter'):
        rr=[r for r in records if r['arm']==arm]
        summary[arm]={k:sum(r['score'][k] for r in rr) for k in ['valid','false_acceptance','negative_criteria','correct_statuses','criteria','supported_case','supported_accepted','exact']}
        summary[arm]['count']=len(rr)
        summary[arm]['mean_latency_seconds']=sum(r['elapsed'] for r in rr)/max(1,len(rr))
    pairs={}
    for r in records:pairs.setdefault(r['id'],{})[r['arm']]=r
    new=[]
    for cid,pair in pairs.items():
        if set(pair)!= {'base','adapter'}:raise ValueError('incomplete paired evaluation')
        if set(pair['adapter']['score']['false_acceptance_criteria'])-set(pair['base']['score']['false_acceptance_criteria']):new.append(cid)
    b,c=summary['base'],summary['adapter']
    summary['new_false_acceptance_cases']=new
    summary['research_gate_passed']=bool(records) and not new and c['false_acceptance']<b['false_acceptance'] and c['supported_accepted']>=b['supported_accepted'] and c['valid']>=b['valid']
    summary['deployment_approved']=False
    return summary


def main():
    import torch
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--data',type=Path,required=True)
    p.add_argument('--training',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();lock=json.loads((a.training/'selection-lock.json').read_text());adapter=a.training/lock['selected']
    if lock['runner_sha256']!=sha(__file__) or lock['data_manifest_sha256']!=sha(a.data/'manifest.json'):raise ValueError('evaluation lock mismatch')
    if lock.get('source_hashes')!=source_hashes():raise ValueError('locked prompt/runtime/source changed')
    for name,digest in lock['files'].items():
        if sha(adapter/name)!=digest:raise ValueError('selected adapter changed')
    a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'pre-evaluation-lock.json').write_text(json.dumps(lock,indent=2))
    model,processor=load(a.model,adapter=adapter);model.eval();records=[]
    (a.out/'runtime.json').write_text(json.dumps(metadata(),indent=2))
    for index,row in enumerate(rows(a.data,'test')):
        # Alternate paired order to reduce systematic warmup/order effects.
        for arm in (('base','adapter') if index%2==0 else ('adapter','base')):
            inputs={k:v.to('cuda') for k,v in encode(processor,row).items()};start=time.monotonic()
            error=None;raw='';out_tokens=0;stop='error'
            try:
                with (model.disable_adapter() if arm=='base' else contextlib.nullcontext()),torch.inference_mode():
                    output=model.generate(**inputs,max_new_tokens=900,do_sample=False,use_cache=True)
                torch.cuda.synchronize();tokens=output[0,inputs['input_ids'].shape[1]:];out_tokens=len(tokens)
                raw=processor.decode(tokens,skip_special_tokens=True)
                eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else eos
                stop='eos' if len(tokens) and int(tokens[-1]) in eos else 'length' if len(tokens)>=900 else 'other'
            except Exception as exc:error=type(exc).__name__+': '+str(exc)
            result={'id':row['id'],'family':row['family'],'kind':row['kind'],'arm':arm,'raw':raw,'error':error,
                    'elapsed':time.monotonic()-start,'input_tokens':inputs['input_ids'].shape[1],'output_tokens':out_tokens,'stop_reason':stop,
                    'score':score(raw,row)}
            records.append(result)
            with (a.out/'records.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
    (a.out/'summary.json').write_text(json.dumps(summarize(records),indent=2))

if __name__=='__main__':main()
