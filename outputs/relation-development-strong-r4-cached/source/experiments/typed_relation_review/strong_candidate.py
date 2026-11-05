"""Development-only verifier comparison. Same policy, independently pinned model."""
from . import candidate as core
VERSION=core.VERSION+'-anli-large-verifier'
MODEL_ID='MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli'
MODEL_REVISION='b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7'
THRESHOLD=core.THRESHOLD
LABELS=core.LABELS
DEADLINE_SECONDS=core.DEADLINE_SECONDS
evaluate=core.evaluate

class NLIEngine(core.NLIEngine):
    def __init__(self,model_dir=MODEL_ID,batch_size=8):
        import torch
        from transformers import AutoTokenizer,AutoModelForSequenceClassification
        torch.set_num_threads(min(4,torch.get_num_threads()))
        self.torch=torch;self.batch_size=batch_size;self.records=[];self.planned_pairs=[]
        self.tokenizer=AutoTokenizer.from_pretrained(model_dir,revision=MODEL_REVISION,local_files_only=True,trust_remote_code=False)
        model=AutoModelForSequenceClassification.from_pretrained(model_dir,revision=MODEL_REVISION,local_files_only=True,trust_remote_code=False,use_safetensors=True).to('cpu').eval()
        labels={str(v).lower():int(k) for k,v in model.config.id2label.items()}
        if set(labels)!=set(LABELS):raise ValueError('Unverified classifier labels')
        order=[labels[x] for x in LABELS]
        class OrderedModel:
            def __call__(self,**inputs):
                result=model(**inputs);result.logits=result.logits[:,order];return result
        self.model=OrderedModel()
        self.max_length=min(512,model.config.max_position_embeddings,self.tokenizer.model_max_length)
    def score(self,pairs,deadline):
        try:return super().score(pairs,deadline)
        finally:
            for r in self.records:r.update(modelId=MODEL_ID,modelRevision=MODEL_REVISION,labelOrder=LABELS)
