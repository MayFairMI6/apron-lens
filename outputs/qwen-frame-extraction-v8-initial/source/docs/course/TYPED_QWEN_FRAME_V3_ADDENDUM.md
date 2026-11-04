# Qwen claim-frame v3 transport and field definitions

This versioned addendum accompanies `typed-qwen-frames-extraction-v3`. The
general extraction-only phase in `TYPED_QWEN_FRAME_CONTRACT.md` remains in force.
The preserved v1 and v2 results are not repaired or reinterpreted as v3 results.
This is a diagnostic of learner interpretation, without report evidence, grading,
promotion or a claim of semantic completeness.

The model receives learner text only, represented as exact original sentence
spans with IDs, start/end offsets and all original whitespace. Sentence boundaries
use terminal `.`, `!` or `?` followed by whitespace or end of input; this is a
transport convention, not a linguistic segmentation guarantee. The whole input
limit remains 1,200 characters. A sentence is no longer cut at 160 characters.
Internal extraction references are separate from the eventual review's maximum
three exact quotations of at most 160 characters each. No truncation occurs.

The JSON root has exactly `claims` and `unresolved`, both arrays. Every claim is
an array of exactly twelve columns in this order:

| Position | Field | Meaning |
| --- | --- | --- |
| 1 | id | Unique claim ID such as `c1` |
| 2 | quoteRefs | Nonempty, contiguous, ascending exact source-unit IDs |
| 3 | actor | Exact actor wording or null |
| 4 | relation | Exact predicate/relation wording or null |
| 5 | value | Exact argument/value wording or null |
| 6 | polarity | `positive`, `negative` or `unknown` |
| 7 | epistemic | `asserted`, `uncertain`, `attributed`, `hypothetical`, `question`, `unknown` or `ambiguous` |
| 8 | time | Exact temporal wording or null |
| 9 | attribution | Exact speaker/source wording or null |
| 10 | scope | Exact operator and its argument, or null |
| 11 | status | `active`, `withdrawn`, `historical` or `ambiguous` |
| 12 | correctionTarget | Earlier withdrawn claim ID or null |

Each unresolved row is exactly `[quoteRefs, reason]`. Object rows, wrong widths,
extra columns and invalid types are rejected; there is no object fallback or raw
output repair. The parser deterministically expands valid wire rows into named
fields, retaining the original wire structure and exact source-bound audit spans.
The runtime separately preserves raw output. Compact arrays reduce repeated-key
generation; the output cap remains 1,000 tokens and generation budget 55 seconds.

All six textual fields bind to exact original substrings within the cited unit
range. For a field beginning or ending with a Unicode alphanumeric character or
underscore, the corresponding original-text edge must not be embedded within
another alphanumeric/underscore token. Thus standalone `it` does not match letters
inside `waiting`. Edge checks inspect the complete original input, not an
artificial quotation boundary. Two actual qualifying occurrences remain ambiguous
and reject binding. Matching remains case sensitive and overlap aware; punctuation
and times are preserved exactly. This is mention binding, not coreference proof.

Polarity annotates the literal relation/value; downstream code must never apply a
second logical negation to an already negated phrase. `has not been released` with
negative polarity still means not released. Positive confirmation of a cancellation
is not negative confirmation. Epistemic state records explicit knowledge or modality,
not model confidence, report truth or claim lifecycle. Unconfirmed permission is
unknown knowledge, not denied permission. Attribution remains separately expressible
when knowledge is unknown. A withdrawn claim may have been originally asserted and
must not become epistemically uncertain merely because it was corrected.

An indefinite actor may participate in an active asserted existential claim. Its
unknown named identity must not be filled from questions, reports, rubric or gold.
Unresolved entity alternatives remain explicit in unresolved text. Entity repairs
may be fragments with a null predicate rather than fabricated earlier assertions.

Referencing all nonpunctuation source units establishes syntactic coverage only.
Multiple atomic claims may share a unit. Coverage does not establish that every
conjunct, causal edge, operator, correction or alternative was interpreted correctly.
Those remain obligations for independent assessment of the frozen diagnostic cases.
