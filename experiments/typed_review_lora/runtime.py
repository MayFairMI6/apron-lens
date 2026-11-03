"""Isolated pinned QLoRA runtime. Never imported by the application."""
import hashlib
import importlib.metadata
import json
import random
from pathlib import Path
from backend.training_assessment import review_prompt

REVISION='c202236235762e1c871ad0ccb60c8ee5ba337b9a'
TARGET=r'model\.language_model\.layers\.\d+\.self_attn\.(q_proj|k_proj|v_proj|o_proj)'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load(model_path, adapter=None, train=False):
    import torch
    from transformers import AutoModelForImageTextToText,AutoProcessor,BitsAndBytesConfig
    from peft import LoraConfig,PeftModel,get_peft_model,prepare_model_for_kbit_training
    path=Path(model_path)
    pin=json.loads((path/'pinned-revision.json').read_text())
    if pin != {'model':'Qwen/Qwen3.5-9B','revision':REVISION}: raise ValueError('wrong pinned model')
    if not torch.cuda.is_available(): raise RuntimeError('This paired experiment requires CUDA; no silent CPU/MPS fallback')
    torch.manual_seed(17);random.seed(17)
    processor=AutoProcessor.from_pretrained(path,local_files_only=True)
    config=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type='nf4',bnb_4bit_use_double_quant=True,bnb_4bit_compute_dtype=torch.float16)
    model=AutoModelForImageTextToText.from_pretrained(path,local_files_only=True,quantization_config=config,
          device_map={'':0},dtype=torch.float16,attn_implementation='eager')
    model.config.use_cache=False
    if train:
        model=prepare_model_for_kbit_training(model,use_gradient_checkpointing=True,
                       gradient_checkpointing_kwargs={'use_reentrant':False})
        model=get_peft_model(model,LoraConfig(r=8,lora_alpha=16,lora_dropout=.05,
                             target_modules=TARGET,task_type='CAUSAL_LM',bias='none'))
        names=[n for n,p in model.named_parameters() if p.requires_grad]
        if not names or any('lora_' not in n or '.language_model.' not in n for n in names):
            raise RuntimeError('unexpected trainable parameters')
    elif adapter:
        model=PeftModel.from_pretrained(model,adapter,is_trainable=False)
    return model,processor

def encode(processor,row,completion=False):
    import torch
    prompt=review_prompt(row['payload'])
    messages=[{'role':'user','content':[{'type':'text','text':prompt}]}]
    prefix=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,enable_thinking=False)
    prefix_ids=processor.tokenizer(prefix,add_special_tokens=False)['input_ids']
    if not completion:return processor(text=[prefix],return_tensors='pt')
    answer=json.dumps(row['target'],ensure_ascii=False,separators=(',',':'))
    # Concatenate at the token boundary to preserve exactly the inference prefix.
    # Qwen's explicit end-of-turn token is the configured eos token, not a guessed string.
    answer_ids=processor.tokenizer(answer,add_special_tokens=False)['input_ids']+[processor.tokenizer.eos_token_id]
    ids=prefix_ids+answer_ids
    if len(ids)>4096:raise ValueError(f"target would be truncated: {row['id']} ({len(ids)})")
    return {'input_ids':torch.tensor([ids]),'attention_mask':torch.ones(1,len(ids),dtype=torch.long),
            'labels':torch.tensor([[-100]*len(prefix_ids)+answer_ids])}

def metadata():
    import torch
    return {'packages':{p:importlib.metadata.version(p) for p in ['torch','transformers','peft','bitsandbytes','accelerate']},
            'gpu':torch.cuda.get_device_name(0),'cuda':torch.version.cuda,'revision':REVISION,
            'quantization':'nf4-double-float16','attention':'eager','seed':17}

def rows(data,split):
    data=Path(data);manifest=json.loads((data/'manifest.json').read_text()); entry=manifest['splits'][split]
    path=data/entry['file']
    if sha(path)!=entry['sha256']:raise ValueError('dataset hash mismatch')
    result=[json.loads(line) for line in path.read_text().splitlines()]
    if len(result)!=entry['count'] or set(x['family'] for x in result)!=set(entry['families']):raise ValueError('split mismatch')
    return result


def source_hashes():
    root=Path(__file__).resolve().parents[2]
    files=list(Path(__file__).parent.glob('*.py'))+[Path(__file__).with_name('protocol.json'),root/'backend/training_assessment.py',root/'modelaccess/contract.py']
    return {str(f.resolve().relative_to(root)):sha(f) for f in sorted(files)}
