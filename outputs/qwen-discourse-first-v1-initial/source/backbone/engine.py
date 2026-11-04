"""Frozen vision-language model behind three calls. No prompts, data or task logic.

generate     free text for a prompt and optional image
score_labels log-probabilities of single-token labels (e.g. Yes/No) as the next token
embed        mean-pooled final hidden state, as frozen features for project modules

Since 1.1.0 every engine is created with an explicit runtime (device, dtype,
attention implementation), usually from a named profile, and exposes it as
engine.runtime so results can record it.
"""
import json
from pathlib import Path
from backbone.registry import (check_transformers, expected_manifest, model_dir, model_entry,
                               PRIMARY_MODEL, runtime_profile)
from backbone.runtime import resolve_runtime

VERSION = Path(__file__).with_name('VERSION').read_text().strip()


class VLMEngine:
    def __init__(self, name=PRIMARY_MODEL, *, device, dtype, attn_implementation):
        entry = model_entry(name)
        path = model_dir(name)
        manifest = json.loads((path / 'download-manifest.json').read_text())
        if manifest != expected_manifest(name):
            raise ValueError(f'{path} does not hold the pinned {name} revision')
        import torch
        import transformers
        check_transformers(name, transformers.__version__)
        self.name = name
        self.torch = torch
        self.device, self.dtype, self.attn_implementation = resolve_runtime(torch, device, dtype, attn_implementation)
        if entry['loader'] == 'qwen2_5_vl':
            from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
            self.processor = AutoProcessor.from_pretrained(path, local_files_only=True, use_fast=False)
            self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                path, dtype=self.dtype, attn_implementation=self.attn_implementation, local_files_only=True
            ).to(self.device).eval()
        else:
            from transformers import AutoModelForImageTextToText, AutoProcessor
            self.processor = AutoProcessor.from_pretrained(path, local_files_only=True)
            self.model = AutoModelForImageTextToText.from_pretrained(
                path, dtype=self.dtype, attn_implementation=self.attn_implementation, local_files_only=True
            ).to(self.device).eval()
        # Per-model chat-template switches from the registry, e.g. Qwen3.5's thinking mode (1.2.0).
        self.template_kwargs = dict(entry.get('chat_template_kwargs', {}))
        self.manifest = manifest
        self.runtime = dict(device=device, dtype=dtype, attn_implementation=attn_implementation,
                            torch=torch.__version__, transformers=transformers.__version__, backbone=VERSION)

    def _inputs(self, prompt, image):
        content = ([{'type':'image'}] if image is not None else []) + [{'type':'text','text':prompt}]
        text = self.processor.apply_chat_template([{'role':'user','content':content}], tokenize=False, add_generation_prompt=True,
                                                    **self.template_kwargs)
        inputs = self.processor(text=[text], images=[image] if image is not None else None, return_tensors='pt').to(self.device)
        if 'pixel_values' in inputs: inputs['pixel_values'] = inputs['pixel_values'].to(self.dtype)
        return inputs

    def generate(self, prompt, image, max_new_tokens=512):
        """Greedy decoding only; returns (text, input_tokens, output_tokens)."""
        inputs = self._inputs(prompt, image)
        with self.torch.inference_mode():
            output = self.model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
        if self.device == 'mps':
            self.torch.mps.synchronize()
        count = inputs['input_ids'].shape[1]
        answer = self.processor.batch_decode(output[:, count:], skip_special_tokens=True)[0]
        return answer, int(count), int(output.shape[1] - count)

    def score_labels(self, prompt, image, labels=('A','B')):
        inputs = self._inputs(prompt, image)
        token_ids = {label:self.processor.tokenizer.encode(label,add_special_tokens=False) for label in labels}
        if any(len(ids)!=1 for ids in token_ids.values()):raise ValueError('Decision labels must each be one token')
        with self.torch.inference_mode():
            logits = self.model(**inputs,logits_to_keep=1,use_cache=False).logits[0,-1].float()
            scores = self.torch.log_softmax(logits,dim=-1)
        return {label:float(scores[ids[0]].item()) for label,ids in token_ids.items()},int(inputs['input_ids'].shape[1])

    def embed(self, prompt, image=None):
        """Frozen features only; any trained module that uses them lives in a project, not here."""
        inputs = self._inputs(prompt, image)
        with self.torch.inference_mode():
            hidden = self.model(**inputs, output_hidden_states=True, use_cache=False).hidden_states[-1][0]
        return hidden.float().mean(dim=0).cpu().tolist()


def load_engine(name=PRIMARY_MODEL, *, profile=None, device=None, dtype=None, attn_implementation=None):
    """Load with a named runtime profile, or with all three runtime values given explicitly."""
    explicit = (device, dtype, attn_implementation)
    if profile is not None:
        if any(v is not None for v in explicit):
            raise ValueError('Give a runtime profile or explicit runtime values, not both')
        return VLMEngine(name, **runtime_profile(profile))
    if any(v is None for v in explicit):
        raise ValueError('A runtime profile or device, dtype and attn_implementation are required; '
                         'the backbone does not choose them')
    return VLMEngine(name, device=device, dtype=dtype, attn_implementation=attn_implementation)
