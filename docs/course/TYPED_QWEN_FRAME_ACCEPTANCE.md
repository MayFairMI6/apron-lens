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

## Actual prompt-only v2 — concrete claims, unresolved semantic and delivery gaps

The complete [v2 run](../../outputs/qwen-frame-extraction-v2-initial/summary.json)
attempted the same six frozen inputs once. It produced **five observed-EOS
completions, three structurally valid results, two binding failures and one
55-second worker timeout**. The valid results are cases 17, 19 and 20; structural
validity does not establish their semantic completeness. No complete six-case
interpretation pass or downstream grading result is certified. Records SHA-256 is
`1b46f26e444071b2c806cca2d9fd5f17347462f2cfdea8d8c6e4a46216293e2d`.
Every saved source snapshot matches its lock hash; the input fixture matches its
unchanged hash. Independently reconstructing each prompt from the frozen v2
candidate reproduces the recorded prompt exactly. Only fixed instructions and
the original learner units entered these requests.

The frozen candidate is
`33a12ba457b1593f315b2787be616bb9bbfc13578ef7c95093bc2ac2ee3557be`.
Its change from v1 is confined to version and prompt instructions, replacing the
copied placeholder with the unrelated concrete chair example. The parser,
schema, model/profile, fixture and no-retry rule stayed fixed. V2 no longer emits
the invalid placeholder. This is evidence that the prompt change removed that
specific failure, not evidence of general extraction accuracy.

| Exposed case | Actual request seconds | Output tokens | Actual delivery |
|---:|---:|---:|---|
| 12 | 39.668 | 362 | EOS; rejected exact-substring binding of `it` |
| 17 | 53.899 | 491 | EOS; structurally valid |
| 19 | 30.272 | 256 | EOS; structurally valid |
| 20 | 53.078 | 467 | EOS; structurally valid |
| 23 | 41.030 | 368 | EOS; rejected scope outside cited unit |
| 2 | 55.187 | Unknown | Worker timeout; no returned raw answer or verified EOS |

The five completions record terminal/EOS token 248044. Startup/warmup took
14.147 seconds. Cases 17 and 20 consume nearly the entire generation allowance
before any report-checking stage. The last attempt remains a timeout, with
unknown usage and no recovered partial interpretation. These are extraction-stage
measurements; they do not pass the complete request's 55/60/90-second budgets.

The following review covers **all 23 frozen obligations**. “Faithful raw” means
the emitted claim fields preserve that obligation's meaning, even where the
whole output failed parsing. “Partial” identifies retained content with a lost
binding, operator, or incompatible metadata. Neither raw intent nor quoted-unit
coverage repairs an invalid output. The assessment is schema-neutral: equivalent
actor/attribution structure is allowed, and an indefinite asserted claim need
not be marked epistemically ambiguous merely because its named identity is
unknown.

| Case / obligation | Independent raw semantic assessment |
|---|---|
| 12 `entities` | Faithful raw: the two-aircraft set and both identifiers are explicit; no named role is invented. |
| 12 `occupancy` | Faithful generic assertion: `one of them` occupies Stand B. Its named member remains unassigned. `unresolved: []` does not explicitly audit that remaining identity alternative; downstream must retain it. |
| 12 `waiting` | Partial: `the other` preserves the different-actor wording and `it` preserves the pronoun. There is no explicit stand-reference binding or unresolved-reference record. The parser additionally counts letters inside `waiting` as another `it` occurrence, so the actual result is rejected. |
| 17 `withdrawn-value` | Partial: TRN102, the newest target, 10:35 and withdrawn lifecycle are correctly retained. The initially asserted claim is labeled epistemically `uncertain`, conflating withdrawal with its original assertion state. |
| 17 `correction` | Faithful raw: active 10:20 retains the same aircraft/property and links to the withdrawn 10:35 frame. The withdrawn value is not kept active. |
| 17 `estimate` | Faithful raw for the frozen obligation: `A TOBT` estimates off-block timing. The surface `only` is absent from scope, so the complete operator structure is not separately certified. |
| 17 `permission-scope` | Faithful literal non-conferral: the subject remains `A TOBT`, relation `grants`, value `no permission to depart`. No actual authority denial is asserted. Negative metadata must not negate the already negative literal value a second time. |
| 19 `resolved-items` | Faithful raw: the exact fuel/bags/hold sorted phrase is attached as the basis/scope of the readiness claim. No outside prerequisite is added. |
| 19 `readiness` | Faithful raw: positive active readiness for TRN102 is extracted rather than corrected using source truth. |
| 19 `unknown-permission` | Partial: `its takeoff clearance` and `remains unconfirmed` preserve unknown-confirmation wording. The `Only` operator is omitted, the pronoun is not explicitly linked to TRN102, and negative/asserted metadata does not express knowledge-unknown unambiguously. The literal text does **not** warrant calling this a generated denial of clearance. |
| 20 `not-released` | Faithful raw: negative active release claim names TRN101 and retains the exact negated relation. |
| 20 `held` | Partial: held state and `at its stand` are retained, with no invented stand identifier. The actor is null and no reference link or unresolved note connects it to TRN101. |
| 20 `permission` | Partial: negative `gives` / `departure clearance` retains non-conferral content. Both the recipient link to TRN101 and the exact `nothing` quantifier/scope are absent. It must not become an authority's explicit refusal. |
| 20 `lvp` | Faithful raw: `The tower` is the actor of putting low-visibility procedures in force. This actor representation preserves the stated attribution despite the separate attribution field being null. No safeguarding claim is invented. |
| 23 `cancellation` | Partial: Airside Operations, confirmation and cancelled safeguarding survive. Current `now` is omitted; negative polarity on the positive `confirms` relation is underdefined/inconsistent metadata. It cannot safely mean that confirmation was denied. |
| 23 `clearance` | Partial: positive active clearance for TRN101 is present, but its asserted `with that` link to cancellation is omitted. Source truth is not used to remove the learner's clearance assertion. |
| 23 `parked` | Faithful raw for current parked state: TRN101 is explicitly bound to staying parked. The surface `only` qualifier is omitted from scope. |
| 23 `condition` | Faithful raw pending condition: `until a pushback slot opens` qualifies staying parked and does not claim the slot has already opened. Actual parsing correctly rejects it because only `u1` is cited while the final `opens.` lies in `u2`; `u2` is also uncovered. |
| 2 `actor-repair` | No result: the worker timed out before returning an answer. |
| 2 `delay` | No result: the worker timed out before returning an answer. |
| 2 `fuel` | No result: the worker timed out before returning an answer. |
| 2 `baggage-unknown` | No result: the worker timed out before returning an answer. |
| 2 `contrast` | No result: the worker timed out before returning an answer. |

The inventory separates eleven faithful raw obligation meanings, seven partial
meanings and five obligations with no returned result. It is **not** an accuracy
score or eleven accepted obligations: case-level parsing, omitted operators and
unresolved argument/reference structure remain required. In particular, the
generic roles in case 12 are not wrong named assignments, and the negative enum
in case 19 is not evidence that actual clearance was denied. V2's field semantics
did not define the polarity argument precisely enough for that conclusion.

The bounded next experiment is a separately frozen v3 transport/definition
revision, preserving v2 raw failures: compact fixed-column arrays, original
sentence units rather than arbitrary 160-character cuts, exact token-edge mention
binding, and explicit distinctions among literal polarity, knowledge state and
lifecycle. Those changes target demonstrated wire/binding/definition problems.
They cannot by themselves certify coreference, operator completeness, correction
generalization, report support or whole-request delivery. No model call,
candidate edit, raw-output repair or sealed-reserve inspection was made by this
reviewer.

## V3 pre-inference independent source clearance

The candidate, focused tests and versioned addendum hashes independently match:

- Candidate: `7c6d6e48e2fef7a15bb46b8978be28af7ee7d1cfed589648da0f978ac8aded43`.
- Tests: `e7f88640a671b2a2a0863cebcdf7682b8e54e5f8ee1fbb0baff8ee4194d18528`.
- Addendum: `dca63fa22014dd23bbe21d32b7f54c83046094c30d803240980faa457906089d`.

The full source/addendum readback and 28 independently executed offline frame/
runtime controls pass. Claim rows require exactly twelve ordered fields;
unresolved rows require two. There is no object fallback, repair, retry or
reinterpretation of historical outputs. Valid wire rows expand deterministically
to named audit fields while preserving wire/raw data. Original sentence transport
is lossless within the unchanged 1,200-character input cap; its documented boundary
convention is not a linguistic guarantee. Internal units remain separate from the
unchanged eventual three quotations of at most 160 characters each.

Exact mention binding checks original-input Unicode alphanumeric/underscore
edges, retains case/punctuation and rejects genuinely repeated qualifying
occurrences. The rules distinguish literal negation, unknown knowledge and claim
lifecycle; indefinite actors cannot be filled from external evidence. The prompt
still receives only learner units and has no report, question, rubric, grading
or gold fields. No concrete blocker was found for the bounded six-case diagnostic.
This is source/mechanical clearance only; actual v3 semantic outputs, latency and
later unchanged grading gates remain unassessed here.

## Actual compact v3 — faster delivery, interpretation gate still failed

The complete [v3 run](../../outputs/qwen-frame-extraction-v3-initial/summary.json)
attempted all six unchanged controls once: **6/6 observed-EOS completions, 2/6
structurally valid outputs and no timeouts**. Cases 12 and 17 parse; cases 19,
20, 23 and 2 fail. No complete faithful interpretation is independently certified
for any of the six. Saved records SHA-256 is
`2756849f9b7faa689d39c9810ee25cb18b2d6fc1a388600a195951b76e9437c7`.
All frozen source snapshots and the unchanged input fixture match their lock
hashes. Each recorded prompt independently reconstructs exactly from the frozen
v3 candidate and original learner text. No private annotation, report, question
or grading gold entered the model request.

| Exposed case | Actual request seconds | Output tokens | Actual delivery |
|---:|---:|---:|---|
| 12 | 8.513 | 72 | EOS; structurally valid |
| 17 | 16.546 | 147 | EOS; structurally valid |
| 19 | 17.723 | 151 | EOS; nonexact value binding rejected |
| 20 | 17.287 | 155 | EOS; repeated real pronoun binding rejected |
| 23 | 13.156 | 116 | EOS; nonexact relation binding rejected |
| 2 | 14.252 | 125 | EOS; six unresolved rows exceed two-unit bound |

Every completion records actual EOS token 248044; startup/warmup took 13.735
seconds. Delivery is substantially faster than the prior run with 72–155 output
tokens. Because both transport and instructions changed, this observation does
not isolate an array-only causal speed benefit. More importantly, a faster
invalid or incomplete interpretation cannot establish whole-request acceptance.

All 23 obligations were independently inspected in the complete raw outputs:

| Case / obligation | Independent raw semantic assessment |
|---|---|
| 12 `entities` | Omitted from extracted fields: neither named aircraft nor their two-member set is represented. The full transport quote still contains them, which does not establish extracted semantic coverage. |
| 12 `occupancy` | Partial: `one of them` occupies Stand B without a guessed name. The antecedent set and its unresolved alternatives are not represented; `unresolved` is empty. An active asserted generic role is itself legitimate. |
| 12 `waiting` | Partial: different-actor wording `the other` and the pronoun `it` survive, but neither the set binding nor explicit Stand B reference is resolved or audited. Token-edge binding now correctly accepts the single standalone `it`. |
| 17 `withdrawn-value` | Partial: TRN102, 10:35, withdrawn status and originally asserted epistemic state are preserved. The off-block-target property and newest/current scope are missing from extracted fields. |
| 17 `correction` | Partial: active 10:20 has the same actor, but both the target-property scope and required correction link are absent. `correctionTarget: null` does not identify which earlier value was replaced. |
| 17 `estimate` | Faithful raw for the obligation: a TOBT estimates off-block timing. `only` is not retained as an operator. |
| 17 `permission-scope` | Faithful literal non-conferral: the TOBT subject grants no permission to depart. No operational authority denial is invented; literal negative wording must not be negated again. |
| 19 `resolved-items` | Incorrect/incomplete extraction: fuel and bags become invented literal `has` predicates rather than the stated sorted-items basis; `hold sorted` is also not an exact source phrase. The common sorted state and its connection to readiness are lost. |
| 19 `readiness` | Faithful raw core assertion: TRN102 is ready to depart remains positive and active. The extra lowercase value `readiness` is not an exact occurrence of the capitalized source word, so actual parsing rejects the output before later nonexact `has` relations are reached. |
| 19 `unknown-permission` | Partial/withheld: the exact unconfirmed-clearance words appear only in an unresolved note. The clear unknown-confirmation claim, actor reference and `Only` scope are not extracted as claims. This is not an actual clearance denial, but it also does not satisfy the explicit obligation. |
| 20 `not-released` | Faithful raw negative release assertion for TRN101, despite a redundant TRN101 argument value. |
| 20 `held` | Partial: held-at-stand wording is retained, but actor `it` has two qualifying occurrences in the cited sentence. The parser correctly refuses the ambiguous occurrence binding; no explicit TRN101 link is supplied. |
| 20 `permission` | Partial: `nothing` and the literal gives-it-clearance relation preserve non-conferral, but the recipient remains an unresolved pronoun. It must not be converted into an authority's refusal. |
| 20 `lvp` | Faithful raw: tower agency, low-visibility procedures and in-force state are retained without inventing safeguarding. |
| 23 `cancellation` | Partial: confirmation, Airside Operations attribution and cancelled safeguarding are retained. `now` is omitted, and negative polarity still conflicts with positive confirmation under the clarified v3 definition. |
| 23 `clearance` | Partial: positive active departure clearance for TRN101 is retained; the asserted `with that` causal/inferential link is omitted. |
| 23 `parked` | Faithful raw current parked assertion for TRN101, but its relation `is staying parked` is not contiguous in the source, which says `is only staying parked`. The parser correctly rejects the actual result. |
| 23 `condition` | Omitted: no frame or unresolved entry retains the pushback-slot opening or its `until` relationship to staying parked. Referencing the now-whole sentence is not coverage of that meaning. |
| 2 `actor-repair` | Incorrect/withheld: only an ambiguity note is emitted for TRN103 versus TRN102. It does not preserve the explicit withdrawn subject, corrected active actor or repair link. No prior complete predicate should be fabricated. |
| 2 `delay` | Incorrect/withheld: the note treats `held up` as potentially negated by `no` and `sorry`, although those words repair the subject before the predicate. The delay and late-bag cause are not extracted. |
| 2 `fuel` | Omitted: completed refuelling for the corrected actor does not appear in any frame or unresolved note. |
| 2 `baggage-unknown` | Partial/withheld: notes mention negated received information and loading, but do not preserve the definite lack of received loading confirmation or its baggage/actor references. The text is treated as unclear rather than extracted. |
| 2 `contrast` | Omitted: known refuelling completion versus absent loading confirmation is not represented. |

The two parse-valid outputs therefore do not pass the semantic controls. Case 17
improves the withdrawal/epistemic distinction but loses the actual repair link;
case 12 remains a generic two-role statement without its explicit entity set or
audited references. The clear subject correction in case 2 is misread as possible
predicate negation. These failures are separate from mechanically valid JSON,
exact substring matching and observed EOS. No output was repaired or replaced,
and no model call or sealed-reserve read was made by this reviewer.

## Bounded next-representation opinion — proposal, not implementation acceptance

The actual v3 failures justify testing a separately versioned representation with
exact source references plus standalone interpreted-claim text, lifecycle and an
explicit correction link. Twelve exact lexical fields are brittle when the model
tries to express a coherent predicate: it invents surface `has`, removes `only`
inside `is only staying parked`, duplicates arguments and cannot bind a repeated
pronoun without a positional schema. Further example-specific lexical prompt
patches would not resolve the distinction between interpretation and literal
mention binding. A smaller representation is a defensible diagnostic direction,
not evidence that the model's interpretations are correct.

Interpreted text would be explicitly model-authored interpretation, never an
exact quotation or source/report fact. Its exact original witness and full learner
context must remain available. Ambiguous roles must stay ambiguous; a subject
repair fragment must not become a fabricated complete earlier assertion; unknown
confirmation must not become denial; omitted operator arguments and correction
edges still fail the same independent semantic obligations. Every positive
claim, addition, omission, withholding and fidelity-check failure must be saved.

A separate frozen fidelity-check diagnostic may test whether these interpreted
claims preserve the quoted/full learner meaning, using no question, report,
rubric or gold. It cannot certify fidelity by generator self-attestation,
syntactic source coverage, or NLI agreement alone: the earlier exposed controls
already demonstrated incorrect entailments, and an omitted claim cannot be
recovered by checking only the claims the generator chose to emit. Independent
all-obligation review and contrasting exposed controls must precede any grading
integration. The new representation, source plan, checker role and addendum need
a separate freeze/placement decision; no new implementation or promotion is
approved by this opinion. Existing model, no-retry rule and whole-request budgets
remain in force.

## V4 pre-inference independent source clearance

The separately versioned compact-interpretation diagnostic freezes these hashes:

- New `claims_candidate.py`: `943329a6eb343930f34732a89da12a6bd81ab27c98a7be31d10537dc7e6f597f`.
- New structural tests: `04414440c001b208a635786c019b310b2231b25633c605650c81d56f7bb56e5f`.
- V4 addendum: `58d81d8c01c05bf92c7014f071c9ab665677b1922991698dacd36b3f9cada247`.

Independent full-source/addendum readback and 42 offline tests pass (14 new,
24 preserved v3 and four runtime controls). The v3 candidate remains unchanged at
`7c6d6e48e2fef7a15bb46b8978be28af7ee7d1cfed589648da0f978ac8aded43`.
A pre-call coordinator-requested correction permits up to 24 unresolved entries
independently of sentence count, so multiple legitimate ambiguities can share one
sentence; the 25th entry rejects. This does not grant semantic validity to an
ambiguity declaration.

Five-column claim rows preserve exact source references separately from untrusted
interpreted text, lifecycle and earlier-withdrawn correction links. The parser
checks types, bounds, IDs, references, link structure and syntactic unit coverage;
it does not decide whether an interpretation is faithful. Even deliberately
fabricated interpretations receive `fidelityVerified=False`,
`reportCheckAllowed=False` and `semanticCompletenessVerified=False`. No report or
grading API exists in the new module. The runner's explicit module selection is
recorded in the lock; source snapshots must include the preserved sentence-unit
helper dependency and the new addendum. Model/runtime, same six input texts,
23 private obligations, no-retry rule and generation budget remain unchanged.

No concrete blocker was found for that bounded v4 extraction diagnostic. This
clearance does not implement or qualify an automatic fidelity checker. Full raw
semantic assessment remains necessary, including clear assertions that the model
withholds, corrections, unresolved identities and all operator/causal edges.
No model call, candidate edit or sealed-reserve read was made by this reviewer.
