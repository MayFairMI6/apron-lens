"""Small CUDA/quantization backward check before loading 9B weights."""
import argparse,json,tempfile,math
from pathlib import Path
import torch
import bitsandbytes as bnb
import peft
from .runtime import metadata,load,encode,rows,source_hashes

def main():
    if not torch.cuda.is_available():raise RuntimeError('CUDA unavailable')
    linear=bnb.nn.Linear4bit(64,64,compute_dtype=torch.float16,quant_type='nf4',compress_statistics=True).cuda()
    linear.requires_grad_(False)
    x=torch.randn(2,64,device='cuda',dtype=torch.float16,requires_grad=True)
    y=linear(x);y.float().square().mean().backward()
    if x.grad is None or not torch.isfinite(x.grad).all():raise RuntimeError('4-bit backward failed')
    receipt=metadata()|{'quantized_backward':True,'source_hashes':source_hashes()}
    p=argparse.ArgumentParser();p.add_argument('--model');p.add_argument('--data');p.add_argument('--out',type=Path);a=p.parse_args()
    if a.model:
        if not a.data or not a.out:raise ValueError('full model smoke requires data and output')
        model,processor=load(a.model,train=True)
        row=rows(a.data,'train')[0];batch={k:v.cuda() for k,v in encode(processor,row,True).items()}
        params=[p for p in model.parameters() if p.requires_grad]
        opt=torch.optim.AdamW(params,lr=1e-4);model.train()
        scaler=torch.amp.GradScaler('cuda',init_scale=1.0)
        with torch.autocast('cuda',dtype=torch.float16):loss=model(**batch).loss
        if not torch.isfinite(loss):raise RuntimeError('non-finite full model loss')
        scaler.scale(loss).backward();scaler.unscale_(opt)
        gradients=[p.grad for p in params if p.grad is not None]
        if not gradients or not all(torch.isfinite(g).all() for g in gradients) or not any(g.abs().sum()>0 for g in gradients):raise RuntimeError('invalid adapter gradients')
        before_params=[p.detach().clone() for p in params]
        scaler.step(opt);scaler.update()
        if not any(not torch.equal(old,p.detach()) for old,p in zip(before_params,params)):raise RuntimeError('optimizer did not update adapter')
        del before_params
        opt.zero_grad(set_to_none=True);model.eval()
        with torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):before=float(model(**batch).loss)
        with tempfile.TemporaryDirectory(dir=a.out.parent) as tmp:
            model.save_pretrained(tmp,safe_serialization=True)
            # Reload into a second named adapter on the same frozen base, without a second 9B allocation.
            model.load_adapter(tmp,adapter_name='reload_check',is_trainable=False);model.set_adapter('reload_check');model.eval()
            with torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):after=float(model(**batch).loss)
        if not math.isfinite(before) or not math.isfinite(after) or abs(before-after)>1e-4:raise RuntimeError('adapter save/reload changed loss')
        receipt.update(full_model_backward_save_reload=True,initial_loss=float(loss),saved_loss=before,reloaded_loss=after)
        a.out.write_text(json.dumps(receipt,indent=2))
    print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
