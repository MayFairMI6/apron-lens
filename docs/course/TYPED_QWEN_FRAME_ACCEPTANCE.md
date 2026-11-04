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

## Pre-inference source and contract review

The coordinator's architecture contract SHA-256 is
`4c74df765df201c2d92b339f5c2ad3f7398957023edca72434d6061b78d21e9c`.
It pins existing local `Qwen/Qwen3.5-9B` revision
`c202236235762e1c871ad0ccb60c8ee5ba337b9a` and the MPS float16 greedy profile,
thinking disabled, 1,000 output tokens and no retry/fallback. Its first phase
explicitly separates learner interpretation from later report checking and
whole-request/runtime acceptance. This reviewer read the source and contract,
not an actual loaded model.

Candidate SHA-256 is
`efc694253e6bdc64b26a6d3583778de4bb5307b1f7d2d9b52dd74bc2d55632ba`.
The prompt contains only fixed extraction instructions and mechanically derived
exact learner units. The schema has no grading criterion, review status, report
or support fields. It retains atomic claim fields, exact actor/relation/value/
time/attribution/operator bindings, lifecycle, correction links and unresolved
text. A subject-repair fragment may have no predicate, avoiding a fabricated prior
complete assertion. Claimed ambiguity and unit coverage remain semantic audit
obligations; the parser cannot certify them.

Two concrete pre-call mechanical findings were reported and resolved before
inference: the initial 5,120-character parser cap conflicted with the unchanged
1,200-character contract, and nonoverlapping substring search missed overlapping
repeated occurrences. The revised cap rejects 1,201 and accepts 1,200 characters;
overlap-aware binding rejects “ana” in “banana” as ambiguous. All 17 structural
tests independently pass.

The experimental runtime uses the existing isolated owner and records actual
terminal-token/EOS metadata. This reviewer independently ran four mocked
termination tests: short non-EOS output is unverified, capacity without EOS is a
length failure, actual EOS at capacity is verified completion, and empty output
is unverified. All pass. They establish bookkeeping behavior, not actual startup,
device ownership, latency or generated interpretation quality.

The inputs-only fixture is preferred to the private annotation fixture. The runner
must select each top-level `learnerResponse` string and keep IDs/metadata outside
the prompt; its final source/settings hashes belong in the actual run lock.
No further blocker was found for this bounded first extraction diagnostic.
Every raw generation and structural/semantic failure still requires independent
review against the frozen 23 obligations before any expansion or downstream
grading claim. No model call, candidate edit or sealed-reserve inspection was
performed by this reviewer.

## Initial actual v1 extraction — failed, with raw semantic intent reviewed

The complete [initial run](../../outputs/qwen-frame-extraction-v1-initial/summary.json)
attempted all six frozen inputs once: **6/6 observed-EOS completions, 0/6
structurally valid extractions and 0/6 complete faithful interpretations**.
No result was repaired or replaced. Saved record SHA-256 is
`8462bf5e353900c059bcb6831d5239c1b1d72db42813cf4369bc8395330eb111`.
Source snapshot hashes and the input-only fixture match the run lock. Independent
prompt inspection confirms that only frozen instructions and exact learner units
entered each request; private annotations, reports, questions and grading gold
were absent.

Actual runtime identity is the pinned Qwen revision and MPS float16/eager profile.
Every completion records EOS token 248044, no provider error, no timeout and no
length termination. Output sizes are 236–369 tokens. Isolated startup/warmup took
26.400 seconds; generation requests took 25.258–38.734 seconds. This demonstrates
the recorded extraction-stage execution, not a faithful-extraction latency or
the future combined interpretation/report-checking request budget.

All 15 generated claims copy the literal schema example placeholder
`"relation": "exact learner substring"`, which never occurs in the answers.
The strict parser correctly rejects that unbound field in every output. Actor
and value fields are uniformly null. Cases 17 and 23 additionally leave a second
transport unit uncovered; those losses are visible in the raw references even
though the parser stops at the earlier invalid relation. The experiment did not
silently substitute learner text for the placeholder or repair coverage.

The independent reviewer still inspected every raw generation against all 23
frozen semantic obligations. The following categories describe raw intent only;
**none is a usable accepted extraction**. “Partial” means that a scope string or
lifecycle/link preserves some relevant information while required bindings or
scope remain missing. It is not faithful-obligation credit.

| Exposed case | Partial raw indications | Unsafe/incorrect raw indications | Omitted semantic obligations |
|---:|---|---|---|
| 12 | None | None recoverable beyond the invalid templates | `entities`, `occupancy`, `waiting`: no aircraft set, role alternatives, stand binding or different-actor constraint is represented. |
| 17 | `withdrawn-value`, `correction`: one withdrawn and one active claim are linked. Neither actual time value nor aircraft/property is bound. | None separately recoverable | `estimate`, `permission-scope`: the entire second unit is unreferenced. |
| 19 | `resolved-items`, `readiness`, `unknown-permission`: exact scope strings retain the sorted-items basis, affirmative readiness wording and unconfirmed-clearance wording. | Unknown clearance is labeled negative/asserted without a bound relation/value, so its polarity argument is not established. | None wholly absent, but all three obligations remain incomplete. |
| 20 | `not-released`, `permission`, `lvp`: exact scope fragments retain these phrases. | No fully bound operational interpretation is available. | `held`: the independent held-at-stand meaning is not extracted; citing its transport unit does not recover it. |
| 23 | None | Three empty active template claims cannot establish what was asserted. | `cancellation`, `clearance`, `parked`, `condition`; the final “opens.” unit is also unreferenced. |
| 2 | `baggage-unknown`: its exact nonconfirmation phrase appears in scope, without resolved entity or epistemic argument. | `actor-repair`, `delay`: the “no, sorry” repair cue is attached to a negative active frame rather than a withdrawn subject/replacement link. | `fuel`, `contrast`: completed refuelling and its contrast are not extracted. |

The obligation inventory therefore has nine partial raw indications, two unsafe
repair/delay indications and twelve omitted obligations; all 23 remain unusable
under the actual v1 result. The extra caution on case 19's epistemic wording does
not create another counted obligation. No schema-valid or semantically complete
success can be claimed from this inventory.

The recurring literal placeholder is direct evidence of example copying in this
prompt, not a parser defect or evidence that structured interpretation generally
cannot work. The coordinator authorizes a separately frozen **prompt-only v2**
using a concrete nonaviation example instead of the placeholder. Keep the parser,
schema, model/runtime, controls, private annotations and no-retry rule unchanged;
retain v1 as a failed attempt. No grader/report stage, new reserve, promotion or
acceptance claim follows. This reviewer made no model call, edited no candidate
and read no sealed reserve.
