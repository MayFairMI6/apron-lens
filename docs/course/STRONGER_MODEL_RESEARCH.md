# Stronger-model research for typed-answer interpretation

Research only, checked 4 November 2026. The user selected stronger-model evaluation
and then deferred implementation and inference. No hosted model was called, no
credentials were requested, and the app, video and existing results remain unchanged.

The recommended first candidate is Claude Sonnet 5.5 at medium effort. GPT-6 Astra
at medium effort is the proposed higher-cost reference if the first candidate fails.
This recommendation balances a short, text-only interpretation task, documented
model capabilities and existing provider adapters. It is a test order, not evidence
that either model fixes AirfieldLens's errors.

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

A hypothetical 2,000-input/1,000-output-token request costs $0.014 on Sonnet or Sol,
$0.028 on Opus, and $0.070 on Astra at these standard rates. Eighteen such requests
would cost $0.252, $0.504 and $1.26 respectively. These are arithmetic examples,
not measured usage or a spend authorization; actual prompt lengths, reasoning,
provider overhead, taxes and timeouts can change charges. A future $5 hard cap
would be a reasonable small pilot proposal once real inputs are counted. This
stage needs inference access, not weight training.

The repository's hosted adapters mark capabilities unverified and do not currently
enable schema-constrained output. Their transport, timeout and returned-model
checks need a bounded preflight before actual evaluation. No OpenAI or Anthropic
API key was present in the inspected shell environment, and their SDKs were absent
from the candidate environment; that does not establish account-wide availability.
Access setup and all execution are deferred at the user's request.
