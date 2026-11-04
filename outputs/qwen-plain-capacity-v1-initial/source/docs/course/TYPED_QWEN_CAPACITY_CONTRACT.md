# Plain-language learner-interpretation capacity diagnostic

This frozen diagnostic tests the same local model without the structured-output
task. The independent reviewer and milestone ledger approved the bounded capacity
experiment in CURRENT. It is not a new grader, an automatic fidelity checker,
structured-frame qualification or permission to enter report checking. Earlier
results, video and production behavior remain unchanged.

The same six exposed learner answers and all 23 frozen meaning obligations remain
the assessment set. There is no expansion to contrasts or reserve material. The
generic prompt receives exact learner text only. It requests a concise ordinary
prose account of assertions, earlier/corrected readings, restrictions, references,
uncertainty and relationships. It contains no aviation examples, reports,
questions, expected answers, obligation annotations, grading or self-assessment.
Original learner text is untrusted data, never executable instructions.

The model and runtime remain Qwen/Qwen3.5-9B at revision
`c202236235762e1c871ad0ccb60c8ee5ba337b9a`, the existing local artifact and
`apronlens-v2-mps` profile: MPS, float16, eager attention, greedy decoding and
thinking disabled. This experiment does not enable thinking or change the model,
weights, template, decoding profile or shared runtime. The input limit remains
1,200 characters, the output cap 1,000 tokens and the isolated generation deadline
55 seconds. Startup remains separately bounded to 300 seconds. There is one
planned call per answer, no retry, fallback, output repair or concurrent owner.
Observed EOS is still required for completed generation; timeouts and incomplete
outputs remain failures and are preserved.

The API keeps the existing runner function names `prompt_for(learner)` and
`parse_frames(raw, learner)`, but the latter checks only nonempty text transport.
It does not parse frames, enforce prose form, identify atomic claims, validate
quotations or certify semantic meaning. Raw nonempty output in an unintended form
can pass that transport check and still fail the diagnostic. The result explicitly
states `transportValidation='nonempty-text-only'`, `structuredFrame=False`,
`interpretationUntrusted=True`, `fidelityVerified=False`,
`reportCheckAllowed=False` and `semanticCompletenessVerified=False`.

All prompts, raw responses, observed terminal-token metadata, timing, usage,
runtime/source/model hashes and failures are retained without retrospective repair.
Independent assessment reviews all six responses against every existing meaning
obligation, including omissions, invented predicates, reference mistakes, changed
certainty, lost scope and incorrect correction readings. Nonempty transport is
reported separately and never called structured validity or semantic success.

The purpose is to distinguish an interpretation-capacity limitation from a
structured-generation burden under this fixed profile; a result can support or
weaken that hypothesis without proving its cause. Even complete prose fidelity on
these six exposed controls would not satisfy structured acceptance, establish
generalization or qualify an automatic downstream pipeline. Any subsequent route
requires separate placement, source freeze and unchanged full acceptance gates.
