# Matched Qwen reasoning-toggle ablation: source plan

This source plan was independently reviewed before implementation. The reviewer
cleared the pinned marker IDs/template behavior, matched budgets and suffix-only
protocol; runtime/source readback is still required before inference. The milestone ledger and independent reviewer approved a bounded
matched ablation in CURRENT. It is a diagnostic, not structured qualification,
an automatic fidelity checker, production promotion or evidence of general model
incapacity. All earlier prompts, candidates, outputs and videos remain preserved.

## Frozen control and paired design

The control is the exact original single-pass v6 source at
`outputs/qwen-frame-extraction-v6-initial/source/experiments/typed_qwen_frames/claims_candidate.py`,
SHA-256 `da73694d3c3caeeb08fc43039f64f7edfcd93dfdee32a5e7ad355ea90153b0b1`.
After this plan is reviewed, the coordinator will copy those exact bytes into
`experiments/typed_qwen_frames/claims_v6_control.py`. No prompt, constant, schema,
parser or version string is edited in that copy. Existing frozen dependencies
are snapshotted and hashed as well. The public one-pass API remains `prompt_for`
and `parse_frames`; final text uses that original v6 parser unchanged.

The same six original learner inputs and all 23 independently authored meaning
obligations remain fixed. Both arms are freshly run; old v6 responses are not the
OFF arm. OFF runs first, then ON, with sequential isolated owners and no concurrent
model process. Failed or incomplete cases stay in the planned paired denominator;
neither arm is selected per case. No reserve or evaluator contrast reference enters
the prompt, runtime or authoring. The model receives only original learner text
and its frozen v6 transport/prompt, never questions, reports, gold or obligations.

The sole intentional treatment difference is the effective chat-template argument
`enable_thinking=False` versus `enable_thinking=True`. Prompt strings, decoding
parameters, weights, dtype, device, attention backend, input limit, output cap,
generation deadline and parser remain identical. The resulting template input
tokens necessarily differ; both token sequences and template hashes are retained.
The arm cannot silently introduce a stronger model, new instructions, constrained
decoder, different sampling or output cleanup.

The model remains Qwen/Qwen3.5-9B revision
`c202236235762e1c871ad0ccb60c8ee5ba337b9a`, with the same local artifact and base
`apronlens-v2-mps` profile: MPS, float16, eager attention and greedy decoding.
ON is an explicit experimental per-request template override. It does not mutate
the shared registry, base profile, production adapter or default thinking setting.
Actual effective generation and template arguments are saved for each request.

## Budget and observed completion

Each arm makes one planned generation call per learner answer, with at most 1,000
ALL generated tokens and one killable 55-second deadline. Reasoning, protocol
markers, final answer and observed EOS all consume this same token cap; reasoning
is not free or assigned an extra deadline. The two-stage 500/500 allocation is
irrelevant to this single-pass ablation. The learner limit remains 1,200 characters.

Both owners receive the same neutral warmup request and a 128-token warmup cap,
within the unchanged 300-second startup limit. Warmup remains separately labelled
startup evidence, not an assessment response. Each arm's effective thinking setting
also applies to its warmup. Failure to finish warmup does not authorize a fallback,
longer cap, unreported recovery or another model. It is retained as a feasibility
failure, and the affected assessment cases are not silently counted as attempted.

Observed terminal EOS is required. Output length or short text does not establish
completion. There are no retries, alternate profiles, output repair, recovered
replacement responses or automatic fallback between arms. A timeout, length stop,
missing EOS, invalid thought protocol, empty final suffix or invalid v6 JSON is a
recorded failure. A plausible substring inside malformed output is not delivered.

## Exact token protocol

The existing local tokenizer artifacts identify `<think>` as token ID `248068`
and `</think>` as `248069`. These IDs and tokenizer/config hashes must be verified
again by runtime freeze. The current OFF template includes an already closed empty
thought prefix in its input; the ON template ends with an open thought prefix.
Input-prefix markers are not generated tokens and are not counted as such.

Only generated token IDs determine the boundary. No JSON searching, code-fence
stripping, textual marker matching, regex answer recovery or alternate parser is
permitted. The generated sequence must end in an actual effective EOS token, with
no earlier EOS inside that sequence. Effective EOS IDs and the observed terminal
token are saved, rather than inferred from decoded strings.

OFF requires zero generated opening or closing thought-marker IDs. Its final
candidate is the complete generated token sequence before the terminal EOS.

ON requires no generated opening thought marker and exactly one generated closing
thought marker. Generated tokens before that close are reasoning; the final
candidate is exactly the token suffix after that close and before terminal EOS.
There is no requirement that reasoning be nonempty, but final decoded text must
be nonempty. Missing close, multiple closes, any generated opening marker, an
empty final suffix or missing EOS is a failure, not an invitation to find JSON.

The final suffix is decoded without discarding other special tokens and passed
directly to the unchanged v6 parser. Removal of the validated protocol delimiter
and terminal EOS is the declared transport operation, not semantic output repair.
The complete original generated IDs and full decoded text remain preserved even
when the suffix fails JSON parsing. Reasoning text is model output, not learner
evidence, source facts, verified meaning or a fidelity certificate.

Usage records distinguish generated reasoning and final token counts without
underreporting protocol costs. ON's reasoning count includes its closing marker;
its final count includes terminal EOS. OFF has zero generated reasoning tokens
and counts all generated tokens, including EOS, as final. These counts sum to the
actual generated length. Reasoning/final decoded text may separately exclude the
marker/EOS for display, but token accounting never drops them. Incomplete sequences
retain actual observed counts and a failure status without an invented final answer.

## Provenance and interpretation

Before inference, freeze candidate, original v6 dependency, token protocol helper,
runtime, runner, tokenizer/template, model artifacts, fixture and this contract.
For every arm/case retain input/prompt identity, effective kwargs, exact templated
input IDs and hash, full generated token IDs, full decoded output, extracted suffix
or extraction error, thought-close position, EOS metadata, usage, timing and final
parse result. Partial audit is retained on length failure and timeout whenever
observed; a kill before output availability must state that limitation, never
fabricate missing tokens. No failed output is overwritten by a later response.

Independent assessment reviews all six pairs against the same 23 obligations and
separately reports delivery/protocol errors, semantic omissions, invented certainty,
reference mistakes, correction/link errors and changed operators. Generated thought
is not used to excuse a wrong final answer or alter the reference meanings.
Structurally valid v6 output always remains unverified and unavailable for report
checking. No extracted frame obtains credit merely because a thought explains it.

This comparison tests a reasoning-toggle hypothesis under this exact budget and
profile. Any differences remain six exposed control observations, not population
accuracy, proof of causal architecture failure or whole-task acceptance. ON may
consume capacity and timeout; OFF may still interpret incorrectly. Neither result
changes gold, four review statuses, quotation requirements, full qualification,
fresh eligibility, native gates or publication requirements. Any later automatic
fidelity/report pipeline still needs separate approval and empirical acceptance.

The pure helper `reasoning_protocol.split_generated` implements only the declared
token transport. It validates nonnegative integer token IDs (not booleans), an
explicit nonempty effective EOS collection, a boolean arm and a positive token cap
no greater than 1,000. It returns final token IDs without EOS plus counts including
close/EOS as defined above, or raises `ProtocolError(ValueError)`. It neither decodes
text nor searches for JSON. Its acceptance is not fidelity or a final parse. The
caller retains all raw tokens and errors, checks decoded nonempty text and applies
the unchanged v6 parser. Experimental runtime/runner source and integration tests
still require independent frozen readback before calls.
