# Learner-only Qwen frame interpretation: independent acceptance record

The user has approved testing the existing local Qwen model for structured
interpretation within ML-052. This experiment extracts what the learner says;
it does not grade the answer, decide report support or supply omitted content.
Production, original results and the final video remain unchanged. The separately
versioned architecture addendum, model/revision, prompt/schema, ownership and
whole-request budget must be frozen before calls. The original R11 contract is
not retroactively rewritten. The old sealed fresh-v3 remains unread and is
ineligible for this route; its replacement requires the ledger's separate
eligibility/placement decision.

## Initial independent controls frozen before inference

[TYPED_QWEN_INITIAL_CONTROLS.json](TYPED_QWEN_INITIAL_CONTROLS.json) contains six
original exposed learner texts and 23 schema-neutral semantic obligations with
exact source spans. Its SHA-256 is
`57d70f9022b9498c8ff6d4f0953b464793a397b10c19c2661459d66d9e2ddfd0`.
Source fixture is the already exposed `fresh-v2.json`, SHA-256
`cdb4e59bd3fb3f6b75c5f4f4c423296f4ac274d8a8a27e000814ea371cb35d8f`.
Each control retains its original index and learner-text hash. Neither source
reports/questions nor grading labels were copied into its runtime input.

For the coordinator's runner, the separate
[TYPED_QWEN_INITIAL_INPUTS_V1.json](TYPED_QWEN_INITIAL_INPUTS_V1.json) contains only
`cases[{id,learnerResponse}]` plus bookkeeping metadata. Its SHA-256 is
`0a57f37b255371bc6bab0fa7584fea545e73d4de7a3a5d232223d3ab9cad7df4`.
The private annotation file above remains unchanged. Both versions have identical
six learner texts; all 23 annotated exact-span bindings were independently
checked against those originals. Only the runtime case's learner-response string
may enter the prompt/parser; even its ID and metadata are bookkeeping.

| Exposed index | Required interpretation | Main prohibited completion or loss |
|---:|---|---|
| 12 | Two aircraft have different occupancy/waiting roles, but which actor has which role is unresolved; “it” refers to the stand. | Assigning specific roles by name order. |
| 17 | Current 10:35 is explicitly withdrawn and replaced by 10:20; the generic estimate/permission distinction remains. | Retaining the withdrawn value or turning estimate non-conferral into actual permission denial. |
| 19 | Preserve both the learner's affirmative readiness claim and unconfirmed takeoff clearance, plus the stated service/hold basis. | Correcting readiness to unknown from outside evidence or inventing a prerequisite list. |
| 20 | Preserve unreleased/held state, absence of clearance conferral and tower attribution for active low-visibility procedures. | Inventing safeguarding, a stand identifier or denied permission. |
| 23 | Preserve confirmed cancellation, claimed positive clearance and its asserted link, parked state, and the pending slot-opening condition. | Dropping the clearance/slot explanation or treating a slot opening as already occurred. |
| 2 | A valid subject repair withdraws TRN103 before the predicate and binds delay/completed refuelling to TRN102; loading remains without received confirmation. | Retaining competing active actors, inventing a prior complete TRN103 assertion, or converting nonconfirmation into actual baggage noncompletion. |

The set intentionally includes five difficult prior failures and one contrasted
valid actor correction. It is an exposed feasibility diagnostic, not a balanced
accuracy sample, independent reserve or acceptance comparison. The semantic
obligations were annotated independently of candidate implementation. They do
not impose one serialization or a fixed number of claim objects where equivalent
structure preserves the same meaning.

Only `case.input.learnerResponse` may reach the interpretation stage. Fixture
references, obligation annotations, forbidden inferences, report facts, rubric
expectations and grading gold remain evaluator-only. The same frozen extraction
prompt and model configuration must apply to every case. No favorable
representation or retry may be selected after reading its annotations.

## Separation of checks

Mechanical checks establish schema validity, exact occurrence/offset binding,
reference integrity, quotation limits and syntactic transport coverage. A complete
list of input-unit references does not prove that every semantic claim survived.
Transport chunks of 160 characters are not independent assertions. Repeated text
needs an unambiguous occurrence binding. A semantic field may refer to an exact
earlier learner span when that reference is faithfully resolved; neither questions
nor source facts can provide its missing actor or property.

Independent semantic review scores each obligation as faithful, unresolved,
incorrect or omitted, and separately records invented active claims. Faithful
ambiguity is required where the learner leaves roles unresolved. Withholding an
explicit positive interpretation or declaring every field unresolved does not
pass the diagnostic. Corrections need the active/withdrawn binding and exact
repair link; polarity, epistemic, temporal and attribution operators need their
argument scope, not merely the presence of a word such as “not.” Claims that a
later report checker would reject must still be extracted faithfully as the
learner's assertions.

Later report checking is a separate stage and separate measurement. A faithful
extraction followed by incorrect evidence support still fails the existing
review gate. Literal quotes, eligible source IDs, NLI agreement or generated
self-attestation cannot certify interpretation correctness. Preserve every raw
generation, parse failure, withheld result and retry. The existing 55/60/90-second
budgets cover the complete request, including all stages and ownership/load work;
stage-specific budgets cannot multiply that allowance.

## Current decision

The six references and private annotations are frozen for the first diagnostic.
No Qwen output, extraction accuracy, successful report check, runtime acceptance,
reserve eligibility or promotion is certified here. The independent reviewer
made no model call, edited no candidate and read no sealed reserve. Actual source,
prompt/schema and configuration review plus the complete raw outputs remain the
next evidence, followed by the full exposed/stress and unchanged downstream gates.
