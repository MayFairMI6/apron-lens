# Stronger-model research for typed-answer interpretation

Research only, checked 4 November 2026. The user selected stronger-model evaluation
and then deferred implementation and inference. No hosted model was called, no
credentials were requested, and the app, video and existing results remain unchanged.

The final user decision assigns this work to Checkpoint 2 (B06 / ML-053),
prioritizes free downloadable local models, and closes the current planning
discussion. Implementation, downloads and inference await that milestone.

The first proposed comparison is quantized Qwen3.5-27B against the frozen local
Qwen3.5-9B baseline. gpt-oss-20B is the independent-family alternative; Qwen3.5-35B-A3B
is a latency/capacity alternative if the dense 27B configuration is unsuitable.
These are candidates, not measured improvements. The inspected Mac has an M5 Pro
and 48 GB unified memory. Ollama lists quantized packages that make the Qwen
candidates plausible to investigate, but package size is not total runtime memory
or proof of meeting the response deadline.

Ollama is a model-serving/runtime option, not a model. The existing implementation
uses Transformers/PyTorch MPS float16. A new local configuration must freeze the
weight revision/package digest, quantization, prompt template, runtime and context
limit; changing these together is a configuration comparison, not a pure model-size
ablation. The model remains Mac-hosted for the phone app. Ollama and Apple-oriented
alternatives can be assessed during implementation without changing the baseline.
Sources: [Qwen 27B](https://huggingface.co/Qwen/Qwen3.5-27B),
[Qwen 35B-A3B](https://huggingface.co/Qwen/Qwen3.5-35B-A3B),
[Ollama Qwen packages](https://ollama.com/library/qwen3.5),
[gpt-oss-20B package](https://ollama.com/library/gpt-oss:20b).

The hosted candidates below are retained as background research and a contingent
fallback. They are not the selected primary execution plan or spending approval.

| Candidate | Proposed use | Standard USD per million input/output tokens |
|---|---|---:|
| Claude Sonnet 5.5 | First practical candidate | $2 / $10 |
| GPT-6.1 Sol | Alternative balanced candidate if OpenAI access is preferred | $2 / $10 |
| GPT-6 Astra | Higher-capability reference on the identical complete test set | $10 / $50 |
| Claude Opus 5.5 | Same-provider escalation alternative | $4 / $20 |

Anthropic describes Sonnet as fast and Opus as moderate-latency; these categories
are not measured AirfieldLens response times. Opus thinking is always on. OpenAI
documents medium effort for Sol and Astra, and describes Astra as its most capable
model. Matching effort labels does not match computation across providers. Current
prices and access must be rechecked before execution.

Sources: [Sonnet](https://platform.claude.com/docs/en/models/sonnet-5-5/overview),
[Opus](https://platform.claude.com/docs/en/models/opus-5-5/overview),
[Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol),
[Astra](https://developers.openai.com/api/docs/models/gpt-6-astra).

The local comparison delivered six valid Qwen interpretations with reasoning off;
four preserved the required meanings. It still added confirmation to an assertion
and failed a corrected aircraft reference. Reasoning on timed out on its first
assessment, leaving five unattempted. These observations motivate a stronger-model
comparison but do not establish global incapacity. See the preserved
[run report](../../outputs/qwen-reasoning-ablation-v2/RESULTS.md).

The research question is whether a hosted model preserves corrections, pronouns,
uncertainty, attribution and temporal meaning within the application's response
budget. Better JSON formatting alone cannot answer it. Claude and Gemini document
schema-constrained outputs, while OpenAI also supports structured outputs. This
can prevent some structural errors, but an incorrect actor or invented confirmation
can still fit a valid schema. Treat constrained decoding as a separate experimental
factor rather than silently adding it during a model comparison.
Sources: [Claude structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs),
[Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output).
Gemini was considered, but the inspected repository already has OpenAI and Anthropic
adapters; prioritizing them avoids adding another provider for the first comparison.

When work resumes, freeze one provider/model/effort configuration and the exact v6
learner-only prompt/parser used in the latest comparison. Test all six exposed
controls with the same 23 independent meaning obligations, a 1,000-token generated
budget and 55-second deadline. Provider reasoning tokens count toward the output
budget where applicable; failure to finish is a recorded failure. Preserve raw
available responses, requested and returned model identity, settings, actual usage,
provider stop reason, elapsed time and exceptions. Disable retries and fallbacks.
If the provider rejects the configuration, record incompatibility rather than
silently substituting a supported setting. API inference is a model-plus-runtime
comparison; it does not isolate model weights. Do not claim greedy or deterministic
sampling for providers that do not expose those controls.

If all six pass, evaluate the already frozen twelve contrasts before broader
qualification. Reference annotations, reports and expected answers remain outside
the extraction prompt. An independent reviewer should apply the unchanged meaning
rubric; the candidate must not certify its own answers. A second candidate, if
needed, receives the complete same set rather than only the first model's failures.
No held-out set is reused for tuning; the sealed reserve remains untouched and
ineligible under its original contract. Existing full development, fresh-evaluation,
report-grounding and native end-to-end gates remain necessary before deployment.

The primary local pilot has **$0 provider-token fees** on existing hardware.
It still consumes electricity, memory, storage and time. Budget for unsuccessful
requests explicitly: assume a 20% failed-attempt rate for planning only, not as an
observed prediction. Eighteen primary cases divided by 0.8 gives 22.5 attempts;
round conservatively to 24 main slots, including six failure/development allowance
slots. Add three preflight and six repeat-validation slots: **33 slots per new
configuration**, or 66 if two candidates are evaluated. Use only eligible cases
and stop at failed gates; an allowance does not require consuming all slots.

At the existing 55-second assessment deadline, 33 slots represent up to 30.25
minutes of capped request time per configuration; two configurations represent
60.5 minutes. This excludes downloads, startup, cold compilation, independent
review and whole-suite/native verification, so it is not a wall-clock completion
promise. Six unsuccessful slots alone reserve 5.5 minutes per configuration.
Measure actual energy/runtime rather than inventing an electricity price.

If a hosted comparison is later selected, retain a separate conditional budget.
At 2,000 input/1,000 output tokens per slot, Sonnet's $0.014 and Astra's $0.070 give
$2.772 for 33 slots each; a 25% contingency adds $0.693, for **$3.465, rounded to
$3.50**, with a proposed **$5 ceiling**. This is a pilot allowance, not the cost of
all Checkpoint 2 work or authorization to spend. Recheck prices and actual prompt
counts before execution. Unknown billed timeout usage reserves the full assumed
cap until reconciled. Reasoning counts toward provider output usage where applicable.

For either route, failed, malformed, refused, incomplete and timed-out attempts
remain in the records. There are no automatic retries; any later development or
validation attempt has a separately registered purpose and configuration. Repeats
never erase failure denominators, become independent samples, or authorize tuning
on held-out data. Broader qualification and native testing require a subsequent
budget based on measured pilot costs. Weight training is not needed for this first
comparison.

The repository's hosted adapters mark capabilities unverified and do not currently
enable schema-constrained output. Their transport, timeout and returned-model
checks need a bounded preflight before actual evaluation. No OpenAI or Anthropic
API key was present in the inspected shell environment, and their SDKs were absent
from the candidate environment; that does not establish account-wide availability.
Access setup and all execution are deferred at the user's request.
