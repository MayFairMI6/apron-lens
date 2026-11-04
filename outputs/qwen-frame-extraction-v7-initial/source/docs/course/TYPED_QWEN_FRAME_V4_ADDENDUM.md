# Qwen v4 untrusted claim interpretation diagnostic

`typed-qwen-claims-extraction-v4` is a new diagnostic module. V3 source and all
earlier results remain preserved. The model receives only learner text in exact
original sentence units, within the unchanged 1,200-character input limit. The
same frozen six controls and their twenty-three interpretation obligations are
assessed before any expansion. Generation remains capped at 1,000 tokens and
55 seconds without retries. No reserve3 material enters this experiment.

The JSON root has exactly `claims` and `unresolved`, both arrays. A claim row has
exactly five columns: `[id, quoteRefs, interpretedClaimText, lifecycle,
correctionTarget]`. An unresolved row is `[quoteRefs, reason]`. The parser rejects
wrong widths, object rows, invalid types, extra root fields, invalid references,
duplicate IDs and invalid correction links. There is no repair or fallback. Claims and unresolved entries are each bounded
to twenty-four rows; multiple independent ambiguity notes may share one sentence.
The ambiguity bound does not depend on the number of transport units.

`quoteRefs` bind exact contiguous ascending original sentence-unit IDs, preserving
the complete original text and offsets. Multiple claims may share a unit. Internal
units are not limited to final review quotation sizes. Coverage requires all
nonpunctuation source units to appear in claims or unresolved. Neither text
coverage nor exact quotations establish semantic faithfulness or completeness.

`interpretedClaimText` is explicitly untrusted model interpretation. It may
paraphrase the learner and therefore is not validated as literal source wording.
The prompt requires preservation of restrictions, temporal operators, attribution,
negation, knowledge uncertainty, causal/implication links, conditional future,
comparisons, corrections and unresolved identities. It forbids filling names or
roles from outside knowledge. Unknown permission is not denied permission, and a
conditional future event is not an occurred event. Interpretation errors remain
possible and must be assessed independently against the actual learner text.

`lifecycle` is exactly `active`, `withdrawn`, `history` or `ambiguous`. It is not
truth, confidence or knowledge state. A correction links a later claim to an
earlier withdrawn claim ID. An entity repair may retain a withdrawn noun fragment
without inventing a complete earlier predicate. The parser validates link
structure; it cannot establish that the learner actually made that correction.

Every parsed result sets `fidelityVerified=False`, `reportCheckAllowed=False` and
`semanticCompletenessVerified=False`, including syntactically valid fabricated
interpretations. The module exposes no report-checking or grading API. Unit tests
inject bad interpretations to demonstrate that syntactic acceptance never grants
fidelity or permission for a report stage. No flag or mocked checker substitutes
for independent semantic assessment. The present experiment does not implement
downstream checking, automatic adoption, production promotion or native integration.

Independent agent assessment is the diagnostic fidelity pass for these controls.
It does not make the parser a semantic verifier or qualify an automatic pipeline.
Raw model output, wire rows, expanded named fields and exact quotation audits are
retained separately so interpretation failures remain visible.
