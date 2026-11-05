"""Pinned local pair classification; no aviation rules or generated text.

Actual classifier label identities are verified from its configuration. Inputs
are never truncated; device batch completion and over-budget rejection are audited.
A process owner, rather than this synchronous engine, enforces hard deadlines.
"""
import time
import importlib.metadata

MODEL_ID = 'MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli'
MODEL_REVISION = 'b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7'
LABELS = ('contradiction', 'entailment', 'neutral')

class PairClassifier:
    def __init__(self, model_dir=MODEL_ID, batch_size=8, *, device='cpu'):
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        torch.set_num_threads(min(4, torch.get_num_threads()))
        if device not in ('cpu','mps'):
            raise ValueError('Unsupported classifier device')
        if device=='mps' and not torch.backends.mps.is_available():
            raise RuntimeError('This classifier profile requires Apple MPS; no silent fallback')
        self.device=device
        self.torch = torch
        self.batch_size = batch_size
        self.records = []
        self.planned_pairs = []
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir, revision=MODEL_REVISION,
            local_files_only=True, trust_remote_code=False)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir,
            revision=MODEL_REVISION, local_files_only=True, trust_remote_code=False,
            use_safetensors=True).to(device).eval()
        labels = {str(v).lower(): int(k) for k, v in self.model.config.id2label.items()}
        if set(labels) != set(LABELS):
            raise ValueError('Unverified classifier labels')
        self.order = [labels[x] for x in LABELS]
        self.max_length = min(512, self.model.config.max_position_embeddings,
            self.tokenizer.model_max_length)
        self.runtime = dict(device=device,dtype=str(self.model.dtype),
            torchVersion=torch.__version__,transformersVersion=importlib.metadata.version('transformers'),
            threads=torch.get_num_threads(),batchSize=batch_size,maxInputTokens=self.max_length,
            modelId=MODEL_ID,modelRevision=MODEL_REVISION,labelOrder=LABELS)

    def score(self, pairs, deadline):
        self.planned_pairs = list(pairs)
        rows = []
        for offset in range(0, len(pairs), self.batch_size):
            if time.monotonic() >= deadline:
                raise TimeoutError('Classification deadline between batches')
            batch = pairs[offset:offset+self.batch_size]
            started = time.monotonic()
            encoded = [self.tokenizer(p['premise'], p['hypothesis'], truncation=False) for p in batch]
            lengths = [len(x['input_ids']) for x in encoded]
            if any(n > self.max_length for n in lengths):
                for pair, n in zip(batch, lengths):
                    self.records.append(dict(**pair, modelId=MODEL_ID, modelRevision=MODEL_REVISION,
                        inputTokens=n, truncationRejected=n>self.max_length, probabilities=None,
                        error='input_too_long' if n>self.max_length else 'batch_withheld',
                        elapsedSeconds=time.monotonic()-started))
                raise ValueError('Classification input exceeds token bound; no truncation')
            inputs = self.tokenizer.pad(encoded, padding=True, return_tensors='pt')
            inputs = {k:v.to(self.device) for k,v in inputs.items()}
            with self.torch.inference_mode():
                probabilities = self.torch.softmax(self.model(**inputs).logits[:,self.order], dim=-1).cpu().tolist()
            elapsed = time.monotonic()-started
            for pair, n, prob in zip(batch, lengths, probabilities):
                row = dict(**pair, modelId=MODEL_ID, modelRevision=MODEL_REVISION,
                    labelOrder=LABELS, inputTokens=n, truncationRejected=False,
                    probabilities=prob, error=None, elapsedSeconds=elapsed)
                self.records.append(row)
                rows.append(row)
            if time.monotonic() >= deadline:
                raise TimeoutError('Classification deadline after device batch')
        return rows
