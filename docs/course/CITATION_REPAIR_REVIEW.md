# Compact typed-review citation contract review

Current position: the v2 candidate repairs the two concrete v1 boundary defects
below. The v2 addendum is authoritative for the current source; retain the v1
findings and test outcome as development history. Neither version has semantic
acceptance from these offline checks.

Independent text/source review, 3 November 2026. Scope: isolated
`experiments/typed_review_repair/candidate.py`, production
`backend/training_assessment.py`, the older unit candidate, saved
`outputs/remaining-fixes-review.md`, and Unity text construction. No model calls,
GPU work, held-out labels, image interpretation, production edit, video edit or
layout change. Reviewed candidate SHA-256:
`56e4e20144e876de77d4c23dbfe78d1b48b50223e50365bf6924ff58e33facb2`.
Synthetic contract tests use parcel statements invented for this
review. This is a contract review, not semantic acceptance or milestone approval.

The candidate removes model-written report IDs and quotations. Its attached
criterion report bundles are authored comparison references; they do not prove
that a model judgment follows from those reports. In particular, no report proves
an invented engine fire merely because it is attached to a grounding correction.
The correction means the assertion is absent from, or incompatible with, the
available reports. The distinction must remain explicit in presentation and
research claims. Literal learner text establishes what was written, not whether
a criterion was met.

## V1 findings and minimal remedies

1. **Prompt context is not receipt bounded at this boundary.** `prompt_for`
   serializes every supplied report, stripping episode/time metadata.
   `expand_review` checks attachment eligibility later. A future or other-episode
   report outside the attached authored bundle can therefore influence a model
   decision without causing rejection. The current session normally supplies
   cutoff-bounded reports, so this is a demonstrated boundary weakness with
   synthetic input, not evidence of leakage in an actual saved run. Filter reports
   by episode and receipt cutoff before constructing either prompt, or reject
   contaminated payloads before a model call. Check that report IDs are unique;
   ID-only set membership cannot disambiguate duplicate records. Reject missing,
   empty, future or cross-episode authored reference bundles before inference.

2. **Multiple learner references are silently reduced to the first unit in the
   accepted result.** `refs` can contain U1 and U2, but `learnerQuote` contains
   only U1. A composite met judgment can consequently display a quote that omits
   its second supporting part. The older candidate had the same behavior.
   Preserve all referenced unit IDs and offsets in an audit sidecar, together
   with every unit support check. If their complete contiguous span is at most
   160 characters, the legacy quote field may use that literal span. If it is
   longer, retain separately bounded literal snippets in the audit; identify the
   displayed legacy quote as an excerpt. Never concatenate noncontiguous snippets
   into a string represented as a verbatim contiguous quotation, truncate away a
   negation, or imply one displayed excerpt supports every part of a criterion.
   Adding fields directly to the production result requires an explicit contract
   version because the current validator requires exact keys.

3. **Mechanical checks cannot establish criterion coverage or entailment.**
   Any existing unit can currently be assigned to any met criterion, including
   one that does not express it; any model-written reason can survive within the
   length bound. The model can also label every unit supported despite an extra
   invented claim. The current prompt correctly prohibits omission-based credit,
   but this is an instruction, not a deterministic guarantee. Keep a semantic
   acceptance gate that checks actual learner coverage, criterion scope and all
   extra claims. Do not call the quote/ID repair a semantic remedy.

4. **Do not restore a blanket “met cannot cite unsupported unit” rule.** A broad
   unit can contain both the correct criterion and an unrelated unsupported
   addition. Crediting the correct part while marking grounding contradicted is
   appropriate. Conversely, blindly crediting a supported clause cannot excuse
   an incompatible answer to the criterion itself. Unit-level status alone cannot
   resolve this; neutral claim spans or independent semantic review are needed.
   The grounding aggregate must examine every unit and every clause, choose
   contradicted if any assertion is unsupported, and retain all offending spans
   in its audit even if the legacy display shows only one example.

## Honest presentation without a layout change

Text inspection found the typed feedback renders `Reports: <IDs>` per point in
`TrainingView.cs`'s `FeedbackText`, then the full available reports. Its `Sources`
button belongs to the ordinary assistant panel; it is not the typed point label.
Do not describe the typed point display as already saying “Sources.” No image
inspection or visual/layout acceptance is claimed.

A safe wording-only presentation is “Comparison reports: <IDs>” with an
explanation such as “Compare your answer with these reports. References do not
verify the feedback.” Keep “Your words” only for an exact contiguous excerpt;
“Your words (excerpt)” is accurate when not all selected learner units appear.
An unsupported-grounding comment should say “This claim is not established by the
available reports,” or identify an actual contradiction. It should not call the
attached bundle proof of the unsupported assertion. Full authored bundles are
acceptable as comparison sets, with no precision, relevance-per-ID or entailment
claim. The current generic “Compare each point with its reference reports” helps,
but does not make every attached report relevant to every asserted claim.

All learner text is already shown as “Your answer”; preserving that and retaining
all unit checks in the audit avoids losing unrelated unsupported additions. One
example quote is insufficient evidence that every extra claim was checked.
These are recommendations only; this reviewer changed no UI text or layout.

## Bounded two-stage coverage recommendation

A report-free first stage is a reasonable experimental safeguard against answer
leakage into learner coverage. Give it the learner response, stable literal units,
and the question's requested topics. Do not give it reports or an authored
“expected” criterion that already states the answer. Ask only which exact spans
address each requested topic, whether a requested part is absent, and neutral
claims expressed with subject, negation, tense, attribution and uncertainty
preserved. Do not ask this stage to assign factual support or infer missing
answers. The topic mapping itself must be authored without answer-bearing hints.

The second stage receives eligible reports, authored criterion meanings, the full
learner response and the frozen coverage output. It judges factual compatibility
and every assertion, including all additions outside requested topics. It cannot
upgrade a clearly absent first-stage topic to met. An ambiguous or failed coverage
stage should withhold or mark uncertain rather than force a missing/credit answer.
Audit both raw stages and the mapping, including every selected span. A neutral
coverage output remains fallible, so its schema and exact spans are mechanical
checks; completeness and relevance still require empirical semantic review.

This is an integration recommendation for an isolated development candidate. It
does not establish that two stages improve accuracy, justify production promotion,
or authorize using fresh evaluation results as iterative prompt-development data.

## Preserved v1 offline verification

`python3 -m unittest discover -s tests -p test_compact_review_contract.py -v`
ran 11 synthetic tests: 9 passed and 2 explicitly expected failures documented
above. Passing checks cover literal/160-character unit extraction, unavailable
reference rejection at expansion, complete unit checks, unknown unit rejection,
missing-point empty quotations and a correct core plus unrelated unsupported extra
remaining `needs_review`. Expected failures expose prompt contamination and lost
multi-unit mapping. They are unresolved defects, not repaired or passing behavior.
The test suite makes no claim that the model detects unsupported claims; its
support judgments are deliberately supplied synthetic inputs. The initial attempt
with `python` could not run because that executable is unavailable; `python3`
completed the bounded run. No existing results were changed.


## V2 independent contract addendum

Root implemented `blind-coverage-review-v2`; this reviewer changed only this
review and its owned test file, plus the explicitly requested preserved copy of
the v1 tests at `outputs/compact-review-development-v1/contract-tests-v1.py`.
The original v1 outcome remains 9 passing checks and 2 expected failures.

Reviewed v2 candidate SHA-256:
`111d63ef1ffa01cf0531138ce2b730595311472ea1f82e9150e093aadbec7230`.
Reviewed neutral coverage module SHA-256:
`afba85d86d8962e0b39f0a4329727df9a3ee13445cc50a3a18e412e28cc20f08`.

The current bounded command is unchanged:
`python3 -m unittest discover -s tests -p test_compact_review_contract.py -v`.
It completed **18 tests, all passing**, with no expected failures. Synthetic
criteria use explicitly mocked neutral facets; a separate check covers the
criterion/topic mapping for all twelve live questions without inspecting labels.
The first adaptation run had one fixture error: its synthetic coverage falsely
assigned a delivery-time facet to a dragon claim. Correcting that fixture to put
both correct core facts in U1, and both coverage facets on U1, made the intended
unrelated-extra test valid. This was not a candidate fix or semantic observation.

Verified v2 guards:

- Future and other-episode reports are rejected before either prompt; duplicate
  report IDs and missing or empty authored bundles are rejected before stage one.
- Every unit needs an ordered known support check. Missing or unknown checks,
  unknown learner references, and malformed/reordered/duplicate coverage fail.
- Multi-unit quotations use the exact contiguous minimum-to-maximum span,
  including original punctuation and whitespace, with no new UI schema fields.
  Spans over 160 characters are withheld, rather than silently reducing to U1.
- Any required facet with empty blind coverage blocks met. An explicit wrong
  answer can still be contradicted when another requested facet is absent.
- A correct core can remain met while an unrelated unsupported extra makes
  grounding contradicted and the overall verdict `needs_review`.

Stage-one prompt data contains only topics, units and learner response. Report
messages and authored expected-answer sentinels are absent. Text inspection of
all twelve topic definitions found neutral descriptions of the requested subject,
relationship or certainty, with no supplied aircraft identity, time, actual
procedure status or correct factual answer. The stage-one instruction about not
inferring aircraft/permission from procedures explains a coverage rule, not a
world fact. Stage two receives reports and expected meanings after coverage is
parsed. The met guard requires each required facet's selected units to appear in
that criterion's references.

These guards address the demonstrated v1 mechanical weaknesses. They do not
prove that stage one selected relevant spans or recognized omissions, that stage
two judged all claims correctly, or that attached bundles entail a judgment.
Overwide quotes now deliberately reduce delivered yield; record these withheld
results explicitly in development evidence. Keep both raw stages and every unit
check in the runner audit. The wording-only presentation recommendations and
semantic acceptance requirements above remain applicable. No model calls,
held-out-label inspection, production/UI changes or promotion decision were made
by this reviewer.
