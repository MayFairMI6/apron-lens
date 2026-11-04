# Discourse-first learner interpretation diagnostic contract

This source plan was independently reviewed before implementation. The reviewer
cleared the four-column assignment design and unchanged runtime budget; candidate,
test and runtime sources still require frozen readback before inference. It supplements `TYPED_QWEN_FRAME_CONTRACT.md`. Earlier candidates,
two-pass outputs and the plain-language capacity diagnostic remain immutable.
The capacity results motivate a hypothesis that correction identification can be
separated from full source-preserving claim extraction. Correct prose repairs
do not prove structured fidelity, the hypothesis or general model capacity.

## Planned tasks and inputs

Both stages use the same complete original learner utterance, limited to 1,200
characters, in the unchanged exact original sentence units. They receive no
question, reports, rubric, expected answer, semantic reference annotation or
reserve material. Unit boundaries are transport, not discourse boundaries. The
same six exposed initial controls and all 23 final meaning obligations remain.

Stage A maps explicit or genuinely ambiguous repairs only. It does not select all
claims, paraphrase operational facts, resolve the entire answer or certify fidelity.
There is deliberately no all-clause coverage requirement: an answer without a
repair can validly return an empty map. This makes missed repairs and false repair
detections independent semantic audit obligations rather than a unit-coverage
test. A full negative assertion, contrast, unknown knowledge or two different
actors is not automatically a correction.

Stage B receives the complete original learner text and Stage A's map, explicitly
untrusted. It selects and interprets all source-preserving claims, including
unrelated or unsupported-sounding extras and all operator relationships. Its
scope is the complete original answer, never just mapped repair spans. It may
use original context to resolve references, but not outside facts, question
presuppositions or authority supplied by the map. This is not parsing prose,
retrying a failed Stage A, or asking the model to certify its own fidelity.

## Stage A format and exact provenance

The root has exactly `repairs` and `unresolved`, both arrays bounded to 24 rows.
A repair row is exactly:

`[repairId, quoteRefs, oldText, cueText, newText, oldScope]`

IDs are unique string IDs such as `r1`. References are nonempty contiguous
ascending original unit IDs. Each of the three text fields is a nonempty exact
contiguous mention inside the cited range, independently bound to original
start/end offsets with the frozen original-text token-edge rule. Ambiguous
repeated mentions are rejected rather than resolved by a convenient occurrence.
No paraphrase or fabricated predicate is accepted in these text fields. The cue
must be retained as original text, not translated into an invented negation.

`oldScope` is exactly `fragment`, `complete_assertion` or `ambiguous`. It annotates
the claimed scope of the old reading; it is not a factual source field. An
interrupted actor name can be an old fragment without asserting that actor did
or did not perform the eventual predicate. A complete earlier assertion may
instead have been retracted. Scope labels remain untrusted model interpretation.

An unresolved row is `[quoteRefs, reason]`, with a bounded nonempty string reason
and no lifecycle column. It describes an unresolved repair interpretation, not
unknown operational truth. A suspected repair that cannot be exactly selected
remains unresolved instead of invented. Transport validation checks exact text,
references, types, bounds and map identity; it cannot prove repair scope, intended
old/new roles or whether a cue actually retracts a reading. The parser retains
raw wire, exact fields, full original context, offsets and false fidelity flags.
Span overlaps can retain context; they do not certify a repair relation. The
old mention must start no later than the new mention, measured using its exact
bound offset, not a whole-unit reference start. Equal starts and contextual
overlap remain permitted; no cue-specific temporal inference is made by binding.

## Stage B full extraction and map assignments

The Stage B root has exactly `claims`, `unresolved` and `repairAssignments`.
Claims use the existing five-column format:

`[claimId, quoteRefs, interpretedClaimText, lifecycle, correctionTarget]`

Claim IDs are unique strings such as `c1`. All original nonpunctuation units
must occur in claims or unresolved; this is syntactic coverage only. Independent
claims must remain distinct, with restrictions, negation, uncertainty, attribution,
conditional future, temporal and causal/implication arguments intact. Source
wording is preserved with minimal grammar or licensed antecedents, not new facts.
Interpreted text remains untrusted; it is not made faithful by exact references.

Lifecycle remains `active|withdrawn|history|ambiguous`. An actual correction
retains the earlier fragment/assertion as withdrawn and the corrected claim's
target explicitly links that earlier ID. A clear negative assertion is not a
withdrawn fragment. Unknown knowledge is not denial, omission or automatic
ambiguous lifecycle. Stage B can extract any claims supported by original text;
the previous all-clause Stage A ID-preservation rule does not apply here.

For minimal unambiguous traceability, the assignment row has four columns:

`[repairId, oldClaimId, newClaimId, unresolvedReason]`

There is exactly one assignment for every Stage A repair ID, with no invented
map IDs. When the map is usable, both claim IDs are existing final IDs and the
reason is null. The old claim must be withdrawn, the new claim must link to it,
and their exact evidence reference ranges must contain the mapped old/new spans.
The replacement need not remain active: an intermediate corrected reading can
itself be withdrawn in a subsequent correction chain.
This is provenance/link validation, never proof that accepting the map was right.
The original cue and its offsets remain in the map audit.

When the original learner text does not support using the proposed map, both
claim IDs are null and `unresolvedReason` is a nonempty string explaining the
interpretation limitation. The inline reason keeps rejection explicitly attached
to the map ID without an ambiguous reason-string cross-reference. Partial
assignments and silent map deletion are rejected. The independently reviewed four-column assignment keeps this limitation
explicit; it is not an automatic fidelity check. Rejected maps do not disappear from original raw audit.

The ordinary Stage B unresolved format remains `[quoteRefs, reason]`. Stage A's
unresolved notes remain retained separately and unchanged in the final audit;
they are not blindly treated as still-unresolvable after original-text annotation.
Both lists remain visible so any licensed resolution can be assessed independently.
The three Stage B arrays are each bounded to 24. Overflow is a failure, not a
reason to omit a claim, uncertainty note or map assignment.

Stage B need not force a wrong map into its claim interpretation. Nevertheless,
rejecting or correcting that map cannot turn a semantically failed Stage A into
a passing complete diagnostic. Stage A repair false positives, omissions, wrong
scope and wrong old/new/cue bindings are assessed independently. Stage B also
must not invent a repair absent from the original learner text; a missed Stage A
repair cannot be rescued into an end-to-end pass by a later correct interpretation.
All original map evidence remains available alongside final claim evidence.

## Runtime, assessment and limits

The same pinned Qwen/Qwen3.5-9B revision
`c202236235762e1c871ad0ccb60c8ee5ba337b9a` and existing local artifact/profile
remain unchanged: `apronlens-v2-mps`, MPS, float16, eager attention, greedy
decoding and thinking disabled. There is no reasoning-profile ablation, training,
fallback or alternate model in this plan.

Two planned calls share ONE 55-second killable isolated-worker request deadline,
including interstage validation and prompt construction. Stage A has at most 500
output tokens, Stage B at most 500; unused capacity does not transfer. Startup
remains separately bounded to 300 seconds. No concurrent model owner is allowed.
Each stage must terminate with observed EOS. Invalid, missing-EOS or timed-out
Stage A aborts before B; there is no no-op fallback, retry, repaired map or prose
parser. A failed Stage B is not replaced by A or recovered output.

The existing stage-audit requirement remains: append, flush and fsync Stage A raw output,
termination metadata, timing, prompt, usage and parse result before Stage B starts,
so a later timeout cannot erase it. Original input and all source/model/runtime/
fixture hashes are frozen before calls. Both stages' raw responses and failures
are retained without repair or retrospective reinterpretation as successful runs.
Any runtime reuse must be explicit about the new stage-specific root schemas.

The proposed candidate API retains `selection_prompt`, `parse_selection`,
`annotation_prompt` and `parse_annotation` for runtime orchestration. This naming
does not make repair mapping equivalent to prior all-clause selection. The new
candidate remains a separate module, with no edits to historical implementations.

All six attempts remain in the denominator. Independent assessment separately
records Stage A repair detection/scope/omission errors and all 23 final meaning
obligations, plus map acceptance/rejection provenance. Syntactic validity,
correct assignments or a fluent explanation are never semantic success by
themselves. A structurally valid empty map is not evidence that no repair exists.

Parsed results always retain `fidelityVerified=False`, `reportCheckAllowed=False`
and `semanticCompletenessVerified=False`. There is no automatic fidelity gate,
grade, report truth check, production promotion or native integration. Later
checking still requires a separately approved automatic fidelity mechanism and
all unchanged acceptance gates. Sealed reserves and evaluator contrast references
remain unread for authoring this plan. Independent contract review cleared implementation and milestone placement remains
separate; source/test/runtime freezes precede inference.
