"""One fixed bounded run; only train and validation splits are read."""
import argparse,json,random,time
from pathlib import Path
from .runtime import load,encode,metadata,rows,sha,source_hashes

def main():
    import torch
    p=argparse.ArgumentParser();p.add_argument('--model',required=True);p.add_argument('--data',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--approval',type=Path,required=True)
    p.add_argument('--smoke',type=Path,required=True)
    a=p.parse_args(); approval=json.loads(a.approval.read_text())
    protocol=Path(__file__).with_name('protocol.json')
    if approval.get('accepted') is not True or approval.get('data_manifest_sha256')!=sha(a.data/'manifest.json') or approval.get('protocol_sha256')!=sha(protocol):
        raise ValueError('independent pre-training gate missing or stale')
    if approval.get('source_hashes')!=source_hashes():raise ValueError('reviewed executable source changed')
    smoke=json.loads(a.smoke.read_text())
    if smoke.get('full_model_backward_save_reload') is not True or smoke.get('source_hashes')!=source_hashes():raise ValueError('GPU compatibility gate missing or stale')
    a.out.mkdir(parents=True,exist_ok=False)
    train=rows(a.data,'train');val=rows(a.data,'validation')
    model,processor=load(a.model,train=True)
    # Fail all overlength examples before any optimisation. Do not truncate targets.
    batches=[encode(processor,r,True) for r in train]; validation=[encode(processor,r,True) for r in val]
    params=[p for p in model.parameters() if p.requires_grad]
    opt=torch.optim.AdamW(params,lr=1e-4)
    scaler=torch.amp.GradScaler('cuda',init_scale=1.0)
    receipt=metadata()|{'protocol_sha256':sha(protocol),'data_manifest_sha256':sha(a.data/'manifest.json'),
        'trainable_parameters':sum(p.numel() for p in params),'source_hashes':source_hashes(),'validation':[]}
    (a.out/'receipt.json').write_text(json.dumps(receipt,indent=2))
    rng=random.Random(17);order=list(range(len(batches)));rng.shuffle(order);cursor=0;start=time.monotonic()
    for step in range(1,73):
        model.train();opt.zero_grad(set_to_none=True);loss_sum=0
        for _ in range(4):
            if cursor==len(order):rng.shuffle(order);cursor=0
            batch={k:v.to('cuda') for k,v in batches[order[cursor]].items()};cursor+=1
            with torch.autocast('cuda',dtype=torch.float16): loss=model(**batch).loss/4
            if not torch.isfinite(loss):raise RuntimeError('non-finite training loss')
            scaler.scale(loss).backward();loss_sum+=float(loss.detach())
        scaler.unscale_(opt)
        if not all(torch.isfinite(p.grad).all() for p in params if p.grad is not None):raise RuntimeError('non-finite training gradients')
        torch.nn.utils.clip_grad_norm_(params,1.0);scaler.step(opt);scaler.update()
        with (a.out/'steps.jsonl').open('a') as f:f.write(json.dumps({'step':step,'loss':loss_sum,'elapsed':time.monotonic()-start})+'\n')
        if step in (24,48,72):
            model.eval();total=0;tokens=0
            with torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):
                for batch in validation:
                    b={k:v.to('cuda') for k,v in batch.items()};n=int((b['labels']!=-100).sum());loss=float(model(**b).loss)
                    if not torch.isfinite(torch.tensor(loss)):raise RuntimeError('non-finite validation loss')
                    total+=loss*n;tokens+=n
            directory=a.out/f'checkpoint-{step}';model.save_pretrained(directory,safe_serialization=True)
            receipt['validation'].append({'step':step,'completion_token_loss':total/tokens})
            (a.out/'receipt.json').write_text(json.dumps(receipt,indent=2))
    chosen=min(receipt['validation'],key=lambda r:(r['completion_token_loss'],r['step']))
    selected=a.out/f"checkpoint-{chosen['step']}"
    lock={'selected':selected.name,'step':chosen['step'],'selection':'validation completion-token loss only',
          'files':{f.name:sha(f) for f in selected.iterdir() if f.is_file()},'runner_sha256':sha(Path(__file__).with_name('evaluate.py')),
          'protocol_sha256':sha(protocol),'data_manifest_sha256':sha(a.data/'manifest.json'),'source_hashes':source_hashes()}
    (a.out/'selection-lock.json').write_text(json.dumps(lock,indent=2));print(json.dumps(lock),flush=True)

if __name__=='__main__':main()
