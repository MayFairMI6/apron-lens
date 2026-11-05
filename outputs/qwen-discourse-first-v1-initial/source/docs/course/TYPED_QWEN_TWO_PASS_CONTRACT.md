# Two-pass learner interpretation diagnostic: proposed source contract

This is the versioned source contract reviewed for CURRENT milestone placement.
Candidate source, tests and runtime must still be frozen and independently read
before inference; this document does not authorize a call by itself. It supplements the general learner-only
experiment contract in `TYPED_QWEN_FRAME_CONTRACT.md`; all previous candidates,
prompts, raw outputs and evaluations remain immutable. It tests whether separating
selection from discourse annotation changes the observed tradeoff between copied
compound statements and invented paraphrases. That causal explanation is a
hypothesis, not an established result.

Both stages receive only original learner material. Neither receives questions,
reports, rubric, expected answers, reference annotations, previous model results
or reserve material. Stage B also receives the current Stage A proposal explicitly
labelled untrusted. These are two planned tasks, not a retry, output repair,
fallback, fidelity self-check or automatic truth verification.

## Frozen tasks and wire formats

The original input limit remains 1,200 characters. Exact original sentence units
and their offsets are the unchanged v3 transport. Unit boundaries are not semantic
boundaries and all units form one continuous utterance. Internal references remain
separate from the final review's three quotations of at most 160 characters each.

Stage A selects source-preserving atomic clauses and fragments. Its JSON root has
exactly `clauses` and `unresolved`, both arrays. Each clause row is exactly
`[id, quoteRefs, sourceText]`. IDs are unique `c1`, `c2`, etc.; quoteRefs are
nonempty contiguous ascending original unit IDs. `sourceText` is a nonempty exact
contiguous substring within that cited range, with one unambiguous mention under
the v3 original-text token-edge binding rule. It is not free paraphrase. Exact
start/end offsets and the original cited context are retained by the parser.
Repeated actual mentions require sufficient original context to disambiguate;
the parser never chooses a convenient occurrence or repairs a proposed substring.

Stage A can select overlapping contextual source spans when necessary to preserve
operators, shared arguments, conditional/causal edges or a repair fragment. It
must not produce only one copied answer when there are independent assertions.
It need not resolve pronouns, expand ellipsis, decide lifecycle or rewrite clauses
into complete propositions. If a connected meaning cannot be selected atomically
without loss, preserve the necessary connected text and expose the limitation
for review rather than invent a new sentence. A noun repair can be selected as a
fragment without inventing a predicate. Atomicity and faithfulness are independent
assessment obligations, not parser guarantees.

Each Stage A unresolved row is exactly `[quoteRefs, reason]`, where reason is a
bounded nonempty string describing a genuine selection limitation. Pronoun
resolution and lifecycle interpretation are deliberately delegated to Stage B,
not recorded here as selection failures merely because they remain unannotated.
It is not a request to check an operational assertion's truth. Clauses and unresolved
rows are each bounded to 24. Every nonpunctuation unit must be referenced by one
or both lists. This syntactic coverage does not certify coverage of every meaning.
Selecting all units as unresolved may be structurally valid but is not successful
selection.

Stage B receives the complete original learner text/units and the structurally
validated Stage A wire proposal, explicitly untrusted. Its planned task is to
annotate discourse, lifecycle and relationships without changing what the learner
asserted. It outputs the existing five-field claim format under `claims` plus
two-column `unresolved`: `[id, quoteRefs, interpretedClaimText, lifecycle,
correctionTarget]`. Lifecycle remains `active|withdrawn|history|ambiguous`.
Interpreted text remains untrusted; no exact-text binder certifies its meaning.

Stage B must retain every Stage A clause ID exactly once, with no invented IDs,
merging, deletion or replacement-selection pass. Its claim reference range must
contain the corresponding Stage A selected span; it may include additional exact
original antecedent context. This is a mechanical preservation rule for all
proposals, not a claim that the Stage A selection was faithful. If the proposal is
unfaithful, the run remains a diagnostic failure under independent review;
Stage B is not an authorized repair path. It may preserve ambiguity and describe
the limitation without erasing the proposed item. Stage A unresolved rows remain
in the final unresolved list unchanged; Stage B may add bounded uncertainty notes.
Both unresolved lists remain bounded to 24, so no unbounded annotation expansion
is permitted. Overflow is recorded as failure, never silently dropped.

An explicit repair retains the earlier selected fragment/assertion as withdrawn
and links its replacement to that earlier ID. Structural validation requires
an earlier withdrawn target, original source ordering measured using the
retained Stage A selected-span offsets (not whole-unit reference starts), and
retained exact evidence references. Necessary overlapping context may share a
start offset; equal starts do not independently prove a correction relationship. It does not prove that the learner made the repair.
Unknown knowledge is not denied permission or ambiguous lifecycle. Relations,
attribution, restrictions, temporal operators, causal/implication arguments,
conditional futures and unresolved roles must survive annotation. Necessary
antecedents may be resolved only from the original continuous learner utterance;
retaining literal pronouns and their exact context is preferable to invented
named roles. No operational certainty may be supplied from the proposal itself.

## Delivery, runtime and provenance

The same pinned local Qwen/Qwen3.5-9B revision
`c202236235762e1c871ad0ccb60c8ee5ba337b9a`, artifact hashes and
`apronlens-v2-mps` profile remain fixed: MPS, float16, eager attention, greedy
decoding and thinking disabled. There is no training or alternate model.

The proposed experimental adapter performs both planned calls inside ONE isolated
worker request and ONE killable 55-second deadline. Stage A has at most 500 output
tokens and Stage B at most 500, for 1,000 aggregate. Unused Stage A capacity is not
transferred to B. Prompt construction and interstage parsing consume that same
request deadline. Startup remains separately bounded to 300 seconds. No model
owner may run concurrently. Each stage must independently terminate with observed
EOS; token count or short text is not evidence of successful completion.

Stage A failure, missing EOS or malformed/unbound selection aborts before B. A
failed Stage B does not fall back to A, become a single-stage delivered result or
trigger another call. This diagnostic does not yet establish that future report
checking fits the unchanged whole-request budgets.

An append-only stage audit records request/stage identity, frozen source/input
hashes, complete prompt, raw output, actual usage/token termination metadata,
timing, parse result/error and exact quotation/selection audit. The completed
Stage A record must be durably appended before Stage B starts, so it survives a
second-stage timeout. Stage B start/failure and the outer worker timeout are
recorded without substituting later recovered output. Source, prompts, parser,
runtime and fixture hashes are frozen before inference. Raw outputs are never
repaired, retrospectively re-decoded or overwritten.

## Assessment and limits

The same six exposed controls and all 23 frozen interpretation obligations are
retained before expansion. Independent assessment separately examines Stage A
selection, Stage B annotation and final meaning. It records whether each error
originated in selection, annotation or both. Stage B compliance cannot turn an
unfaithful Stage A proposal into an accepted control. Every attempted case,
including aborted and timed-out cases, remains in the denominator and raw audit.

Parsed outputs always retain `fidelityVerified=False`, `reportCheckAllowed=False`
and `semanticCompletenessVerified=False`. Independent agent review is a diagnostic
assessment, not an implemented automatic fidelity gate. No report/grading API or
production adoption follows from a valid parse or self-assessment. A later report
pipeline would require a separately approved automatic fidelity mechanism and
unchanged complete acceptance gates; this contract does not supply one. Sealed
reserve and contrast reference files are not read for authoring this plan.

The independent reviewer cleared the selection-versus-annotation separation and
selected-span correction clock before implementation; the milestone ledger approved
CURRENT placement. Implementation ownership remains separate:
candidate/prompt/validator and tests, experimental runtime/runner with aggregate
deadline/audit, and independent assessment. The initial document was prepared before candidate or runtime implementation;
subsequent source/test freezes remain separately recorded.
