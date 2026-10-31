"""Local Qwen service. No cloud calls; synthetic scene images are not persisted."""
import argparse
import asyncio
import json
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool
from backend.reasoning import ROOT, MODEL_PATH, context_for, decode_image, validate_answer
from backend.decisions import select_claims, VERSION as DECISION_VERSION

TOKEN_PATH = ROOT / 'work/qwen-server-token.txt'
AUDIT_PATH = ROOT / 'work/qwen-requests.jsonl'


def local_token():
    TOKEN_PATH.parent.mkdir(exist_ok=True)
    if not TOKEN_PATH.exists():
        TOKEN_PATH.write_text(secrets.token_urlsafe(32))
        TOKEN_PATH.chmod(0o600)
    return TOKEN_PATH.read_text().strip()


class ReasonRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    requestId: str = Field(min_length=1, max_length=80)
    scenarioId: str = Field(min_length=1, max_length=80)
    aircraftId: str = Field(min_length=1, max_length=20)
    checkpoint: float = Field(ge=0, le=3600)
    queryType: str = Field(default='latest', pattern='^(latest|current|change)$')
    properties: list[str] = Field(default_factory=list, max_length=10)
    imageBase64: str = Field(min_length=1, max_length=2_800_000)
    question: str = Field(default='What does the latest received report say for this aircraft, when did it happen and arrive, and what remains unconfirmed?', min_length=1, max_length=400)


class LocalQwen:
    def __init__(self):
        import torch
        from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
        self.torch = torch
        self.device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        self.dtype = torch.float16 if self.device == 'mps' else torch.float32
        self.processor = AutoProcessor.from_pretrained(MODEL_PATH, local_files_only=True, use_fast=False)
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            MODEL_PATH, dtype=self.dtype, attn_implementation='eager', local_files_only=True
        ).to(self.device).eval()
        self.manifest = json.loads((MODEL_PATH / 'download-manifest.json').read_text())

    def generate(self, prompt, image):
        content = ([{'type':'image'}] if image is not None else []) + [{'type':'text','text':prompt}]
        messages = [{'role':'user','content':content}]
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.processor(text=[text], images=[image] if image is not None else None, return_tensors='pt').to(self.device)
        if 'pixel_values' in inputs: inputs['pixel_values'] = inputs['pixel_values'].to(self.dtype)
        with self.torch.inference_mode():
            output = self.model.generate(**inputs, max_new_tokens=512, do_sample=False)
        if self.device == 'mps':
            self.torch.mps.synchronize()
        count = inputs['input_ids'].shape[1]
        answer = self.processor.batch_decode(output[:, count:], skip_special_tokens=True)[0]
        return answer, int(count), int(output.shape[1] - count)

    def score_labels(self, prompt, image, labels=('A','B')):
        content=([{'type':'image'}] if image is not None else [])+[{'type':'text','text':prompt}]
        text=self.processor.apply_chat_template([{'role':'user','content':content}],tokenize=False,add_generation_prompt=True)
        inputs=self.processor(text=[text],images=[image] if image is not None else None,return_tensors='pt').to(self.device)
        if 'pixel_values' in inputs:inputs['pixel_values']=inputs['pixel_values'].to(self.dtype)
        token_ids={label:self.processor.tokenizer.encode(label,add_special_tokens=False) for label in labels}
        if any(len(ids)!=1 for ids in token_ids.values()):raise ValueError('Decision labels must each be one token')
        with self.torch.inference_mode():
            logits=self.model(**inputs,logits_to_keep=1,use_cache=False).logits[0,-1].float()
            scores=self.torch.log_softmax(logits,dim=-1)
        return {label:float(scores[ids[0]].item()) for label,ids in token_ids.items()},int(inputs['input_ids'].shape[1])


def create_app(engine=None, token=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.engine = engine or await run_in_threadpool(LocalQwen)
        app.state.token = token or local_token()
        app.state.busy = asyncio.Lock()
        yield
    app = FastAPI(title='Airfield replay reasoning', lifespan=lifespan)

    def authenticate(authorization):
        if not secrets.compare_digest(authorization or '', 'Bearer ' + app.state.token):
            raise HTTPException(401, 'Connection token required')

    @app.middleware('http')
    async def bound_body(request, call_next):
        # Enforce a real body bound including requests without Content-Length.
        if request.method == 'POST':
            from starlette.responses import JSONResponse
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 3_000_000:
                    return JSONResponse({'detail': 'Request too large'}, status_code=413)
            request._body = bytes(body)
        return await call_next(request)

    @app.get('/health')
    def health(authorization: Annotated[str | None, Header()] = None):
        authenticate(authorization)
        return {'status': 'ready', 'model': app.state.engine.manifest['model_id'],
                'revision': app.state.engine.manifest['revision'], 'device': app.state.engine.device}

    @app.post('/reason')
    async def reason(body: ReasonRequest, authorization: Annotated[str | None, Header()] = None):
        authenticate(authorization)
        try:
            context = context_for(body.scenarioId, body.aircraftId, body.checkpoint, body.queryType, body.properties)
            image, image_hash = decode_image(body.imageBase64)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        if app.state.busy.locked():
            raise HTTPException(429, 'Model is answering another request; retry shortly')
        async with app.state.busy:
            start = time.perf_counter()
            try:
                # Typed report queries have no visual answer-bearing evidence.
                # Images remain auditable context, never a substitute for reports.
                raw, trace = await run_in_threadpool(select_claims, app.state.engine, context)
                inputs, outputs = trace['inputTokens'], trace['outputTokens']
            except Exception as exc:
                raise HTTPException(503, 'Local model generation failed; inspect server log') from exc
            result = validate_answer(raw, context)
            result.update(requestId=body.requestId, scenarioId=body.scenarioId, aircraftId=body.aircraftId,
                          flightInstance=context['flightInstance'], checkpoint=body.checkpoint,
                          model=app.state.engine.manifest['model_id'], revision=app.state.engine.manifest['revision'],
                          elapsedSeconds=round(time.perf_counter() - start, 2), inputTokens=inputs, outputTokens=outputs,
                          decisionVersion=DECISION_VERSION, forwardPasses=trace['forwardPasses'],
                          imageUsedForInference=False, modelRole=trace['provenance'],
                          eligibleEvidenceIds=[e['id'] for e in context['evidence']])
            # No image bytes, authentication secrets, or raw camera frames in the audit.
            audit = dict(result, imageSha256=image_hash, question=body.question, rawModelOutput=raw,
                         decisionTrace=trace, promptVersion=DECISION_VERSION,
                         evidence=context['evidence'], recordedAt=time.time())
            AUDIT_PATH.parent.mkdir(exist_ok=True)
            with AUDIT_PATH.open('a') as stream:
                stream.write(json.dumps(audit) + '\n')
            return result
    return app


if __name__ == '__main__':
    import uvicorn
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    local_token()
    print('Local token stored in work/qwen-server-token.txt; model is loading.', flush=True)
    uvicorn.run(create_app(), host=args.host, port=args.port, access_log=False)
