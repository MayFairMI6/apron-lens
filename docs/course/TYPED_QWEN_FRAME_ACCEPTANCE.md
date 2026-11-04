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

## Actual v4 interpretation — semantic progress, structure and fidelity still fail

The [complete v4 run](../../outputs/qwen-frame-extraction-v4-initial/summary.json)
attempted all six unchanged controls once: **6/6 observed-EOS completions, 5/6
structurally valid outputs and no timeouts**. Saved records SHA-256 is
`3f11b92d79be6cd615991ee515958051b838a7a75dadeb8a6764d694548f3726`.
Independent checks confirm every snapshot hash, unchanged fixture hash and exact
prompt reconstruction. Source, question, report and private evaluator facts did
not enter these learner-only prompts. The result is not an accepted structured
interpretation pipeline: even faithful compound text can violate atomic/lifecycle
requirements, while syntactically valid text can introduce unsupported meanings.

| Exposed case | Actual request seconds | Output tokens | Actual delivery |
|---:|---:|---:|---|
| 12 | 6.101 | 52 | EOS; structurally valid |
| 17 | 9.527 | 82 | EOS; structurally valid |
| 19 | 8.239 | 70 | EOS; structurally valid |
| 20 | 7.776 | 64 | EOS; structurally valid |
| 23 | 7.151 | 58 | EOS; structurally valid |
| 2 | 15.696 | 142 | EOS; malformed unresolved rows rejected |

All six record terminal/EOS token 248044. Startup/warmup took 12.225 seconds.
These extraction-stage measurements do not pass a future combined report-checking
or native request budget. No automatic fidelity checker was implemented; parsed
interpretations remain untrusted with report checking prohibited.

The reviewer inspected every raw output against all 23 unchanged obligations:

| Case / obligation | Independent raw semantic assessment |
|---|---|
| 12 `entities` | Faithful raw: both aircraft identifiers and the two-aircraft set are retained. |
| 12 `occupancy` | Faithful generic role: one unnamed member occupies Stand B; no named assignment is invented. The whole interpretation remains compound and its unresolved identity is not separately audited. |
| 12 `waiting` | Faithful raw role contrast: the other member waits for the same stand in the complete sentence context. Keeping `it` in a coherent full interpretation is not itself a wrong reference. Explicit unresolved auditing remains absent. |
| 17 `withdrawn-value` | Partial structured result: the paraphrase says the learner corrects 10:35, so the withdrawal meaning survives in text. It is embedded in an active compound claim rather than a separate withdrawn value. |
| 17 `correction` | Partial: replacement 10:20 and the same current target are explicit in text, but there is no earlier withdrawn frame or correction link. Null `correctionTarget` fails the required lifecycle representation. |
| 17 `estimate` | Faithful raw: only-estimate wording and off-block timing survive, merged with the independent non-conferral proposition. |
| 17 `permission-scope` | Faithful raw: a TOBT grants no permission to depart. No actual denial is added, but independent claim boundaries are not preserved. |
| 19 `resolved-items` | Faithful raw: all three sorted items are retained as the learner's stated readiness basis. Here `because` expresses the basis already given by `with ... all sorted`; it is not the unsupported causal invention found in case 20. |
| 19 `readiness` | Faithful raw: the positive readiness assertion and TRN102 remain intact. |
| 19 `unknown-permission` | Faithful raw: only takeoff clearance for TRN102 remains unconfirmed; the actor, unknown state and exclusivity are retained without a denial. |
| 20 `not-released` | Partial/distorted: unreleased TRN101 is retained, but the interpretation adds an explicit `because` cause unsupported by the original juxtaposition/explanation structure. |
| 20 `held` | Incorrect weakening: `remains at its stand` replaces `is still held at its stand`, losing the held/restricted state. Being at a stand is not equivalent to being held there. |
| 20 `permission` | Incorrect strengthening: `lacks departure clearance` replaces the narrower `nothing gives it departure clearance`. Non-conferral by the stated situation does not establish actual absence of permission. |
| 20 `lvp` | Faithful raw: the tower activated low-visibility procedures. No safeguarding state is invented. |
| 23 `cancellation` | Faithful raw: the verbatim compound retains Airside Operations attribution, current `now`, confirmation and cancellation. |
| 23 `clearance` | Faithful raw: positive clearance for TRN101 and the learner's asserted `with that` link remain intact. |
| 23 `parked` | Faithful raw: current parked state and `only` qualifier remain. |
| 23 `condition` | Faithful raw: the `until` condition and pending slot-opening event survive without being asserted as already completed. All four meanings occur in one compound claim, rather than the required separate claims with preserved links. |
| 2 `actor-repair` | Incorrect: the interpretation invents an active negative claim that TRN103 is not held up. The original repairs a subject fragment before its predicate; it does not assert that negative proposition. No withdrawn fragment or repair link is emitted. |
| 2 `delay` | Partial: TRN102's late-bag delay is retained, but merged with the invented TRN103 denial rather than represented as the corrected actor's committed assertion. |
| 2 `fuel` | Partial: completed refuelling remains in text, but its corrected aircraft reference is not made explicit in the standalone interpretation. |
| 2 `baggage-unknown` | Partial: lack of received loading confirmation survives and is not converted into actual noncompletion. Its corrected actor/baggage references remain implicit across claim context. |
| 2 `contrast` | Faithful raw contrast: completed refuelling versus absent received baggage-loading confirmation survives in the second compound interpretation. The actual result remains rejected because unresolved entries contain many token columns instead of `[quoteRefs, reason]`. |

Faithful text and valid structure must be assessed separately. Case 23 preserves
all four original obligation meanings; calling it semantically omitted because
it is a copied compound would be inaccurate. Conversely, its one-row structure
does not demonstrate atomic extraction. Case 12 preserves legitimate ambiguity
without assigning names. Cases 20 and 2 demonstrate real added or changed meanings
despite exact source references. Case 17 describes its correction in prose but
still cannot supply the required lifecycle/link structure to a downstream stage.
These observations do not certify complete structured interpretation or permit
report checking.

## Contrast references and bounded prompt-only v5 proposal

Before any contrast inference, this reviewer independently inspected all twelve
texts and 23 obligations in `TYPED_QWEN_CONTRAST_REFERENCES_V1.json`, SHA-256
`2a29304d224ff074d4a2e16812bcdef3c914af4666a3ed1114a4d7ea715baa70`.
The separate inputs-only fixture, SHA-256
`40af8e16dcd443a98451c81abf9fdcddb7390e9545e58136998d74614e1c3d2e`,
contains identical learner strings and IDs. Every learner hash and exact evidence
substring independently validates. References and counterfactual misreadings are
evaluator-only and must remain outside prompts and parsing/inference inputs.

The six pairs appropriately contrast subject repair with negative ellipsis,
unidentified with explicitly named roles, unknown with refused permission,
expected with completed vacancy, unknown service completion with unknown overall
readiness, and conditional with completed attributed events. No substantive
annotation blocker was found. In contrast 02a, the assigned occupant/waiter roles
must not be strengthened into an external capacity rule or an assertion that an
aircraft can never occupy the stand. These are exposed diagnostic controls, not
an independent reserve, population benchmark or satisfaction of initial qualification.

A controlled prompt-only v5 using a concrete nonaviation multi-claim example is
a defensible bounded next experiment. It should demonstrate an earlier withdrawn
actor fragment and explicit replacement link, split independent conjuncts while
preserving operator arguments, retain knowledge-unknown and conditional future,
and avoid introducing a causal `because` absent from learner meaning. The five-field
parser, original inputs/private obligations, model/runtime, budget and no-retry
rule remain frozen. The idea that the single-sentence example caused merging is
a hypothesis, not an established causal result. A richer example can also create
new copying or scope losses, which the same complete raw audit must detect.

This opinion does not approve semantic acceptance, raw-text-only grading, altered
reference labels or an automatic fidelity checker. The actual new source/prompt
must be frozen and independently read before calls; initial qualification remains
unmet. This reviewer made no model call, edited no candidate, repaired no output
and read no sealed reserve.

## V5 pre-inference independent prompt-only clearance

Frozen candidate SHA-256 is
`401c92326a9cb6784e9abc1575da1586ae1b43b842e99c5c6d5b843284c4c260`.
Independent AST comparison with the actual preserved v4 source confirms that only
`VERSION` and `INSTRUCTIONS` changed. The five-field parser, constants, sentence
transport dependency, untrusted/fidelity/report-permission behavior and runtime
remain unchanged. All 42 offline structural/runtime controls independently pass.

The new unrelated examples demonstrate a withdrawn subject fragment and linked
replacement, a separate conditional claim, active unknown-confirmation knowledge,
a numeric correction with explicit lifecycle/link, and a correctly shaped unresolved
reason. They provide no aviation facts or expected control answers. Instructions
require independent conjuncts to be split while retaining asserted relationships,
and prohibit inventing causation, authority, resolved roles or completed future
events. These requirements remain model behavior to test, not parser guarantees.
No concrete blocker was found for a single no-retry run of the unchanged six
initial inputs. Initial qualification and the contrast run remain pending; no
semantic acceptance, automatic checker or report-stage permission is granted.
The independent reviewer made no model call, candidate edit or sealed-reserve read.

## Actual v5 — correction structure improves; interpretation still not qualified

The [complete v5 run](../../outputs/qwen-frame-extraction-v5-initial/summary.json)
attempted all six unchanged controls once: **6/6 observed-EOS completions, 5/6
structurally valid outputs and no timeouts**. Records SHA-256 is
`122439054a3532ff6492b37af3a95d69934b14f601fcedc74ca667ecd5a25482`.
Independent checks match every saved source snapshot, the unchanged input-only
fixture and each prompt reconstructed from the frozen v5 source. Source reports,
questions, grading labels and private semantic annotations remain absent from
runtime inputs. No output was repaired or retried.

| Exposed case | Actual request seconds | Output tokens | Actual delivery |
|---:|---:|---:|---|
| 12 | 9.664 | 80 | EOS; structurally valid |
| 17 | 12.767 | 106 | EOS; structurally valid |
| 19 | 10.538 | 86 | EOS; structurally valid |
| 20 | 11.370 | 94 | EOS; structurally valid |
| 23 | 10.683 | 87 | EOS; structurally valid |
| 2 | 21.741 | 186 | EOS; three-column unresolved rows rejected |

All six record observed EOS token 248044; startup/warmup took 10.711 seconds.
These are extraction-stage measurements. The automatic fidelity checker,
downstream report stage and combined/native runtime gates remain unimplemented
or unqualified; their budgets cannot be inferred from these times.

The independent assessment covers all 23 unchanged obligations:

| Case / obligation | Independent raw semantic assessment |
|---|---|
| 12 `entities` | Faithful raw: both named aircraft and the two-aircraft set are retained in their own row. |
| 12 `occupancy` | Faithful generic occupant assertion without guessed identity. The explicit unresolved-list audit requested by the prompt is still absent; the interpretation itself does not assign a named role. |
| 12 `waiting` | Faithful raw: the other aircraft waits for Stand B. Its different-actor relation and resource reference are retained without naming which aircraft. |
| 17 `withdrawn-value` | Faithful raw and lifecycle: TRN102's newest target at 10:35 is explicitly withdrawn rather than active or epistemically uncertain. |
| 17 `correction` | Faithful raw and link: active 10:20 links to the earlier withdrawn target. `The target` resolves through that explicit earlier frame, which retains aircraft/property/current scope. Repeating every noun in the replacement row is not independently required. |
| 17 `estimate` | Faithful raw: only-estimate wording and off-block timing are retained in a separate claim. |
| 17 `permission-scope` | Faithful raw: a TOBT's non-conferral is separate and does not deny actual authority permission. |
| 19 `resolved-items` | Partial with added meaning: sorted fuel, bags and hold remain the readiness basis, but the interpretation strengthens the learner assertion into `Readiness is confirmed`. No confirming source or received confirmation was stated. |
| 19 `readiness` | Faithful positive readiness is retained in a separate row. The additional confirmation assertion elsewhere remains an invented strengthening, so the whole interpretation still fails fidelity. |
| 19 `unknown-permission` | Partial: clearance for TRN102 is correctly unconfirmed rather than denied, but `Only` and its remaining-unknown scope are dropped. |
| 20 `not-released` | Faithful raw: TRN101 has not been released, without the prior invented `because`. |
| 20 `held` | Faithful raw in connected context: `It is still held at its stand` retains restriction rather than mere location; `It` resolves to the preceding TRN101 frame. |
| 20 `permission` | Faithful raw in connected context: `Nothing gives it departure clearance` retains non-conferral and recipient reference without claiming actual refusal or absence of all possible permission. |
| 20 `lvp` | Faithful raw: tower attribution and active low-visibility procedures are retained. No safeguarding claim is added. |
| 23 `cancellation` | Faithful raw: current cancellation confirmation and Airside Operations attribution survive. |
| 23 `clearance` | Faithful raw: TRN101's asserted positive clearance explicitly retains its claimed cancellation basis. |
| 23 `parked` | Faithful raw: TRN101 is only staying parked, without weakening or converting clearance to unknown. |
| 23 `condition` | Faithful raw: the pending pushback-slot opening remains the `until` condition of the parked state, not an occurred event. Keeping this dependent condition with its argument preserves meaning. |
| 2 `actor-repair` | Incorrect: an active negative proposition about TRN103 is invented; the withdrawn actor fragment and replacement link are absent. The unresolved note calls the interpretation a negation/affirmation pair and seeks outside operational verification, although the task is to interpret the learner's repair, not verify report truth. |
| 2 `delay` | Faithful raw positive late-bag delay for TRN102 is present, but does not cancel the independently invented TRN103 denial. |
| 2 `fuel` | Faithful raw in connected context: refuelling completion follows the corrected TRN102 assertion and its exact learner witness. An independent repeated aircraft name is not required in every row. The separate invented TRN103 denial still fails the whole result. |
| 2 `baggage-unknown` | Faithful raw in connected context: received information does not confirm loading of the previously mentioned bags, rather than asserting actual noncompletion. Preceding TRN102/bag context can supply the reference; the malformed uncertainty notes remain a separate failure. |
| 2 `contrast` | Faithful raw difference between adjacent known-fuel and unknown-loading propositions in connected context. Repeating the literal word `but` is not required when that relationship survives. The entire result is structurally rejected for three-column unresolved entries. |

V5 provides actual improvement over v4 on numeric correction structure, held
state, non-conferral and the cancellation/clearance/slot explanation. It still
does not qualify the initial diagnostic: case 19 adds confirmation and loses
exclusive scope; case 2 invents a negative assertion and fails its structural
contract. Faithful ambiguity, source quotations, parsed rows and EOS remain
separate from semantic acceptance. Existing fidelity/report/completeness flags
stay false; no report checking or promotion follows.

Qualification uses the frozen schema-neutral obligations, not newly imposed
serialization preferences. Case 12's explicit two-name set plus one/other roles
and shared Stand B can preserve faithful ambiguity even with an empty unresolved
list. That empty list is an instruction/audit omission, not a new independent
semantic failure or a demand to resolve names the learner leaves unspecified.
Similarly, connected claim context and the exact learner witness may resolve
case 2's pronouns; every row need not repeat a stronger actor identifier than the
original statement. The invented active denial, missing withdrawal/link and
malformed unresolved rows remain decisive failures without those extra demands.

## Bounded v6 prompt-only recommendation

A further controlled prompt-only diagnostic is supported by these specific
failures. Its unrelated examples should contrast an interrupted noun corrected
**before its predicate**, including `no, sorry`, with a complete explicit negative
proposition. The former retains a withdrawn noun fragment and links the corrected
actor's active assertion; it must not invent a denied earlier predicate. The latter
retains the actual negation and must not be erased as a repair. Neither the mere
word `no` nor a blanket repair phrase rule is a semantic classifier.

Instructions should distinguish a learner's assertion from independently confirmed
knowledge, preserve `Only` with its actual argument/scope, and require unresolved
entries to have exactly two columns `[quoteRefs, reason]`, without lifecycle.
Unknown operational truth does not by itself make the meaning of a clear learner
statement unresolved; the interpreter must not seek outside verification. The
five-field parser, constants, same initial inputs/private obligations, model,
runtime, no-retry policy and status/acceptance gates remain unchanged. A frozen
source readback is required before any actual call.

This is a bounded experiment recommendation, not evidence that another example
will solve the repair failure, permission for raw-text grading, or a change to
semantic labels. Newly authored countercontrols, if separately authorized, need
independent references frozen before calls and must stay outside prompt examples;
they do not replace the still-failing original case. No additional contrast or
sealed-reserve input was read in this review. The reviewer made no model call,
candidate edit or raw-output repair.

## V6 pre-inference independent prompt-only clearance

Frozen candidate SHA-256 is
`da73694d3c3caeeb08fc43039f64f7edfcd93dfdee32a5e7ad355ea90153b0b1`.
Independent AST comparison against the preserved actual v5 source confirms that
only `VERSION` and `INSTRUCTIONS` changed. All 42 offline frame/runtime controls
independently pass. The parser, five-column claim schema, exact references,
untrusted/fidelity/report flags, limits, runtime, inputs and acceptance gates are
unchanged.

The paired unrelated examples distinguish an interrupted `no, sorry` subject
repair from a complete negative proposition, retaining the withdrawn fragment and
replacement link only for the former. They retain conditional and unknown states,
numeric correction links and properly shaped unresolved reasons. Instructions
explicitly distinguish assertion from confirmation, preserve `Only` scope, and
separate interpretive ambiguity from operational truth verification. The model
still receives no report, question, rubric, source judgment or evaluator annotation.

No concrete blocker was found for the unchanged six-case no-retry diagnostic.
Faithful ambiguity remains schema-neutral under the clarification above; the new
request for both text and unresolved auditing does not retroactively strengthen
the original semantic obligations. Actual output fidelity remains unassessed,
initial qualification is unmet, and neither a report stage nor automatic fidelity
checker is approved. No model call, candidate edit or reserve read was performed.

## Actual v6 — all structures valid, two semantic mechanisms still fail

The [complete v6 run](../../outputs/qwen-frame-extraction-v6-initial/summary.json)
records **6/6 observed-EOS completions and 6/6 structurally valid outputs**, with
no timeout or retry. Records SHA-256 is
`9ac0be6aff36d3123473de8a2fc8242e886e59ffea855f0dda21d2e254ab80c4`.
Independent source-snapshot, fixture-hash and exact-prompt reconstruction checks
pass. All six record terminal/EOS token 248044. Startup/warmup took 15.379 seconds;
requests took 11.137–15.536 seconds and 80–126 output tokens. These remain
extraction-stage measurements, not complete pipeline budget acceptance.

All 23 unchanged obligations were reviewed; grouping below preserves their IDs:

| Case | All frozen obligations and independent assessment |
|---:|---|
| 12 | `entities`, `occupancy`, `waiting`: faithful in connected text. The two named aircraft retain unspecified, different occupant/waiter roles and the same Stand B reference. Empty unresolved auditing does not become a new semantic gate or justify inventing named roles. |
| 17 | `withdrawn-value`, `correction`, `estimate`, `permission-scope`: faithful. Withdrawn 10:35 is explicitly linked to active 10:20 for the same newest target; separate estimate and non-conferral claims remain. |
| 19 | `resolved-items`: the sorted-items basis survives, but the extra `Readiness is confirmed` again strengthens assertion into confirmation without stated confirming evidence. `readiness`: the learner's positive TRN102 readiness assertion survives separately. `unknown-permission`: now faithful, including `Only` and unknown rather than denied clearance. The extra confirmation still fails the whole interpretation. |
| 20 | `not-released`, `held`, `permission`, `lvp`: faithful in connected context, retaining held restriction, non-conferral and tower attribution without invented causality or safeguarding. |
| 23 | `cancellation`, `clearance`, `parked`, `condition`: faithful, retaining current confirmation attribution, the learner's cancellation/clearance link, `only`, and the pending slot-opening condition. |
| 2 | `actor-repair`: improved but incomplete; the subject fragment is now withdrawn, yet the corrected TRN102 row has null `correctionTarget`. `delay`: faithful positive late-bag delay with no invented TRN103 denial. `fuel`: positive completion wording survives, but an unresolved note falsely says `Its` has no identifiable referent, ignoring preceding corrected TRN102 context. `baggage-unknown`: faithful lack of received loading confirmation in connected bag/actor context. `contrast`: known refuelling versus unknown loading remains clear across adjacent propositions; a repeated literal `but` is not required. |

The initial semantic diagnostic remains unqualified despite perfect structural
delivery. In particular, case 2's wrong unresolved declaration is not a demand
to repeat names in every claim: it is a false statement about reference ambiguity
in the whole learner utterance. Missing correction links and invented confirmation
remain independent, directly visible failures. No parsed-result fidelity or
report-permission flag is changed.

A bounded prompt-only v7 is supported: demonstrate plain assertion versus an
explicitly attributed confirmation without upgrading either; treat all learner
units as one utterance for genuine antecedents; cite adjacent context when a
resolved interpretation relies on a preceding unit; and require the corrected
active assertion to link its earlier withdrawn fragment. This must not become
a rule that resolves genuinely unspecified roles, invents confirmation authority
or seeks outside operational truth. The parser/runtime, original semantic labels,
same initial controls, no-retry rule and acceptance gates stay unchanged. The
new source needs a separate freeze/readback before calls; another prompt example
is an experiment, not a demonstrated general solution. No additional contrast,
sealed-reserve read, model call, candidate edit or raw repair was performed here.

## V7 pre-inference review and resolved reference-example finding

The first unrun v7 prompt used `They stayed nearby` and declared Leo its unique
human antecedent. Independent review and the coordinator both flagged that
singular/plural ambiguity; withdrawing a subject fragment does not logically erase
the person from discourse. Before any call, the author replaced it with `The person
who moved the chair stayed nearby`, explicitly linking the reference to the
corrected mover's prior predicate rather than nearest-name or deleted-person logic.

The corrected frozen candidate is
`ae4f042b03af15fd0bc534a23be5fa265e6d9bc4444f29e31cfb211b5d53cf61`.
Independent readback, AST comparison against actual frozen v6 and all 42 offline
controls pass. Only version/instructions changed. The prompt also contrasts plain
assertion with explicit confirmation and requires cross-unit antecedent references
and correction links without resolving genuine alternatives. No concrete blocker
remains for the unchanged six-case diagnostic. This clearance grants no semantic
acceptance, automatic fidelity certification or report permission. The reviewer
made no model call, candidate edit, new contrast inspection or reserve read.

## Actual v7 — prior semantic blockers persist

The [complete v7 run](../../outputs/qwen-frame-extraction-v7-initial/summary.json)
records **6/6 observed-EOS completions, 5/6 structurally valid results, no timeout**.
Records SHA-256 is
`8718257fbc18813eee5db1846336e69a071620687568c8fd6a9732dddd363e81`.
All snapshot/fixture hashes and reconstructed prompts independently match. Startup
took 9.804 seconds; requests took 10.874–15.780 seconds with 80–128 output tokens.
All six record EOS token 248044. No input/prompt truncation or external evaluator
content explains the failures. These measurements remain extraction-stage only.

| Case | Complete 23-obligation assessment, with v6 deltas |
|---:|---|
| 12 | `entities`, `occupancy`, `waiting`: unchanged faithful ambiguity in connected text; no named role invented. Missing unresolved-list auditing is not a new semantic-label failure. |
| 17 | `withdrawn-value`, `correction`, `estimate`, `permission-scope`: faithful. Replacement now repeats the full target/aircraft description and still explicitly links the withdrawn value. |
| 19 | `resolved-items`: sorted basis remains but invented `Readiness is confirmed` persists. `readiness`: positive readiness itself remains faithful. `unknown-permission`: faithful, including `Only`. The extra confirmation fails fidelity. |
| 20 | `not-released`, `held`, `permission`, `lvp`: unchanged faithful meanings and connected references, with no invented cause or actual permission denial. |
| 23 | `cancellation`, `clearance`, `parked`, `condition`: unchanged faithful attribution/current state, asserted causal link, `only` and pending `until` condition. |
| 2 | `actor-repair`: withdrawn noun fragment survives but corrected assertion still has null repair link. `delay`: faithful TRN102 delay, with no active TRN103 denial. `fuel`: completion text survives but an unresolved note again falsely disregards its corrected-actor antecedent. `baggage-unknown`, `contrast`: faithful in connected context. The unresolved row adds a lifecycle third column and is correctly rejected. |

Initial qualification remains failed. The new wording did not remove invented
confirmation or fix repair-link/context handling, and unresolved syntax regressed.
The false note that `Its` is not explicitly identified is not legitimate ambiguity
merely because its antecedent lies in an earlier unit.

A bounded v8 prompt-only wording-preservation mode is a defensible general next
diagnostic: prefer original clauses/fragments with minimal editing, rather than
summarizing them into new predicates or certainty. Retain operator arguments,
attribution, linked causes/conditions, withdrawal/replacement links and licensed
continuous-utterance references. Shorter prioritized instructions may help but
remain an empirical hypothesis. Do not add a case-specific banned phrase, enforce
the earlier brittle exact-slot schema, or repair the raw output afterward.
Copied words alone cannot certify selection, scope, coverage or lifecycle; the
same 23 obligations, parser/runtime, inputs, no-retry rule and gates remain in
force. Frozen-source review and complete actual outputs are still required. No
model call, candidate edit, raw repair, additional contrast or reserve read occurred.

## V8 pre-inference source clearance

Frozen candidate `095faa86619d7bd3047880b9db35acfdad0c1fafce0f9068dc2ea3fb90416267`
matches independent readback. AST comparison against actual frozen v7 confirms
only version/instructions changed; all 42 offline controls independently pass.
The shorter prioritized prompt requests minimally edited learner clauses, retains
operator/relationship scope, permits context-supported pronouns, mandates repair
links and preserves strict unresolved syntax. It does not grant fidelity from
copying or unit coverage. No concrete blocker was found for the unchanged six-case
no-retry run. Semantic gates, parser/runtime and untrusted/report flags remain
unchanged. No model call, candidate edit or additional contrast/reserve read occurred.

## Actual v8 — wording fidelity improves, structure trades off

The [complete v8 run](../../outputs/qwen-frame-extraction-v8-initial/summary.json)
records **6/6 observed-EOS completions and 6/6 structurally valid outputs**, without
timeout or retry. Records SHA-256 is
`fc96fccf65afc2ef62c0def6dd7ae4d9584699c05d48e34da5242b24ab7c1f17`.
Snapshot/fixture hashes and exact prompt reconstruction independently match.
Startup took 9.764 seconds; requests took 6.586–12.080 seconds and 54–105 tokens.
All six record EOS token 248044; these are extraction-stage measurements only.

| Case | All 23 frozen semantic obligations and structure assessment |
|---:|---|
| 12 | `entities`, `occupancy`, `waiting`: faithful ambiguity and resource/different-role meaning survive in a copied whole sentence. The independent-claim output requirement remains unmet; preserved text is not atomic extraction. |
| 17 | `withdrawn-value`, `correction`, `estimate`, `permission-scope`: faithful, with withdrawn value, explicit linked replacement and separate estimate/non-conferral claims. Context supplies the literal replacement pronoun. |
| 19 | `resolved-items`, `readiness`, `unknown-permission`: faithful original stated basis/readiness and `Only` unknown-clearance meaning; the invented confirmation is gone. No named actor must be repeated beyond what connected context resolves. |
| 20 | `not-released`, `held`, `permission`, `lvp`: faithful meanings, including non-conferral rather than denial. Unreleased/held/non-conferral remain a copied compound rather than separate independent claims. |
| 23 | `cancellation`: faithful current attributed confirmation. `clearance`: the positive assertion survives but its `with that` basis/link is dropped. `parked`, `condition`: faithful connected parked/only/pending-until meaning. |
| 2 | `actor-repair`: the original literal repair survives, but the whole correction is marked active without a withdrawn fragment or replacement link. `delay`, `fuel`, `baggage-unknown`, `contrast`: faithful in connected original wording. Copied correction and service sentences do not establish their required semantic decomposition. |

Initial qualification still fails. V8 fixes the invented confirmation but does not
solve the correction metadata and atomicity requirements, and introduces a lost
cancellation/clearance relationship. This pattern across exposed prompt revisions
supports a task-burden hypothesis: preserving all wording and constructing the
needed discourse structure compete in the current single generation. It does not
prove that the pinned model is incapable of either task or of generalization.

The next defensible bounded route is a separately versioned, predeclared
decomposition diagnostic rather than another accumulating warning prompt. One
planned interpretation pass would select source-preserving atomic clauses and
repair fragments; a second planned pass would receive the original full learner
utterance plus that **untrusted** selection to annotate discourse/lifecycle/links.
Each stage's exact task, outputs and failure handling must be frozen in advance.
The second annotator is not a fidelity certificate, retry or opportunity to hide
and replace a failed first stage. Preserve both raw outputs and count first-stage
omissions/compounds and second-stage additions/link errors separately against all
23 unchanged obligations. Do not add reports, questions, rubric or private labels.

Such a route requires its own source plan/addendum and placement approval before
implementation. Both planned passes must share the unchanged whole-request budget;
55 seconds cannot become 55 per pass. No parsing repair, automatic adoption or
self-verified fidelity is allowed. Independent semantic assessment and later
contrasting controls remain required before grading integration. No new architecture
is accepted by this recommendation. The reviewer made no model call, candidate
edit, raw repair, new contrast inspection or sealed-reserve read.

## Two-pass pre-implementation plan review

The reviewer read `TYPED_QWEN_TWO_PASS_CONTRACT.md` end-to-end. Fixed Stage A
clause IDs retained exactly once in B deliberately prevent silent repair of
selection omissions/compounds. That is a defensible diagnostic tradeoff, provided
selection and annotation errors remain separate and both stages face the unchanged
23 obligations. Exact spans and retained IDs do not establish semantic fidelity.
One aggregate 55-second deadline, fixed 500+500 output caps, observed EOS for each,
durable A evidence before B, and abort/no-fallback behavior match the agreed scope.

Two narrow clarifications were sent before implementation: correction ordering
must consult retained selected-span offsets, not just sentence-reference starts
when both claims share a unit; and A unresolved notes must concern genuine
selection limitations rather than pronoun/lifecycle work deliberately delegated
to B. Original A notes/raw output remain preserved, never silently removed to
claim improvement. No architectural blocker was found; these meanings should be
explicit in the frozen plan/source. No code, inference, new contrast or reserve
material was created/read by the reviewer.

## Two-pass v1 frozen-source clearance

Independent full readback matches candidate `2766a80b1ef39016615893480152962a239767beba165082d8469601dfdcd667`,
runtime `55edf6d1894a107c0b147633cd68e0303bf93a68b5a43049aef3425ac38fd8a6`,
runner `3b8765c591043515f3b45b958338921c59092c2bca3eca25a73351e285715863`,
and contract `f36e439c928616e6cc2bf5eeb0ce14f9b1d07948cf5afdb9da719e936e1ccd56`.
Runtime-test SHA-256 is
`0ffeed54867418dd66e605dbcefd6c09e126cd85e5ca4ad083874176a36db24a`.
All 67 focused offline controls independently pass in 0.586 seconds.

Both pre-code clarifications are implemented: correction ordering uses selected
span offsets, and A uncertainty is limited to selection work. B retains every
selection ID exactly once, contains its original span and preserves unresolved
rows with multiplicity. Wrong meanings may still parse but always remain untrusted
with all fidelity/report/completeness flags false.

The runtime runs both planned calls inside one owner review request, under the
outer 55-second killable deadline, with fixed 500+500 caps and per-stage observed
EOS/usage checks. Raw A output is flushed and fsynced before parsing or B; invalid
A aborts B, and invalid B never falls back to A. Warmup directly generates its
readiness probe rather than recursively running the two-pass pipeline. A real
isolated-process timeout test with fake inference verifies that completed A raw
evidence survives termination during B. These are mechanical/runtime controls,
not model-quality or actual pipeline-latency evidence.

The coordinator reported an earlier test-harness mistake: its fake lacked a
`load` override, causing actual weights to load before the ten-second test startup
failed. The fake now explicitly returns from `load` without weights; the corrected
67-test run passes, and the coordinator reports no remaining model owner. That
attempt was not the six-case diagnostic and supplies no semantic evidence. This
reviewer's test invocation used the corrected fake and made no model call.

No concrete source blocker was found for the unchanged initial six-case diagnostic.
All raw selections, annotations, aborted attempts and 23 stage-specific semantic
obligations still require independent review. No report checker, semantic
acceptance or reserve eligibility follows. The reviewer edited no candidate and
read no additional contrast/reserve material.

## Actual two-pass v1 — stage-specific failures, no accepted combined result

The [complete run](../../outputs/qwen-two-pass-v1-initial/summary.json) attempted
all six inputs: **A selection valid 5/6; B annotation valid 0/5 attempted; combined
valid 0/6**. Case 19's malformed A aborts B as designed. Every one of the eleven
actual calls records observed EOS; no timeout or retry occurred. Startup took
8.441 seconds; aggregate case requests took 13.949–25.985 seconds. These are
failed-interpretation diagnostic measurements, not pipeline acceptance.

Records SHA-256 is `1a97883b9175d60d04066926c42db44211e0854445765e130f60865442a84c68`;
durable stage-audit SHA-256 is
`34ec437550d4d7121c0fef643ad4ba61c6d89ad53bd36dc96a41a0b4160046f3`.
Independent checks match all frozen source/fixture hashes, every audit lock hash
and both prompts reconstructed from the frozen source and actual A proposal.
Original learner-only inputs match the frozen six. A raw/validation events precede
B starts; all raw failures remain saved. No report, gold or reference annotation
entered either task.

| Case | All 23 obligations, by selection and annotation stage |
|---:|---|
| 12 | `entities`, `occupancy`, `waiting`: A selects three faithful clauses, preserving genuine unnamed-role ambiguity and shared resource context. B raw meanings remain faithful, but numeric IDs and duplicated `claims` root keys invalidate the entire annotation. |
| 17 | `withdrawn-value`, `correction`: A selects both original value/correction spans. B leaves the earlier value active and adds reciprocal/forward links rather than a valid withdrawal/replacement structure. `estimate`, `permission-scope`: A retains both meanings in one compound, failing independent-claim selection; B leaves that compound. Numeric IDs and extra root `notes` also invalidate B. |
| 19 | `resolved-items`, `readiness`, `unknown-permission`: raw A strings retain the source meanings, including `Only`, without inventing confirmation, but malformed row/bracket structure makes A unusable. Overlapping full statements also do not demonstrate atomic selection. B is correctly not called; all three obligations have no annotation result. |
| 20 | `not-released`, `held`, `permission`, `lvp`: A correctly selects separate faithful clauses. B merges the first three and reduces four selection IDs to two numeric IDs; duplicate root keys additionally invalidate it. Original meanings remain visible in raw text but stable-ID/atomic annotation fails. |
| 23 | `cancellation`, `parked`, `condition`: A/raw B preserve the original meanings. `clearance`: positive clearance survives but A omits its `with that` relationship; B also omits it. Numeric IDs and duplicate root keys invalidate B. |
| 2 | `actor-repair`: A copies the whole correction instead of separate fragment/replacement items, so fixed-ID B cannot supply the required two lifecycle-linked items. `delay`, `fuel`, `baggage-unknown`, `contrast`: original meaning survives in compound selections/raw B, but independent selection and discourse structure remain unmet. B adds numeric IDs, string `none` and extra `notes`; no valid annotation is delivered. |

Stage A demonstrates some benefit on cases 12 and 20, but its repair/compound and
edge-selection failures remain. B has a distinct systematic wire-format problem:
all five attempted outputs use numeric IDs, three duplicate `claims` keys, two add
`notes`, and the subject-repair output uses string `none`. Those failures are not
evidence that the selected meanings are correct, but also do not by themselves
establish architectural impossibility. The correction and merged-ID mistakes are
additional semantic/structural failures beyond JSON spelling.

One controlled prompt-only v2 is defensible: provide a complete unrelated matched
source/A-selection/B-annotation example showing exact string IDs, null, one root,
all IDs exactly once, a selected repair fragment with linked replacement, and
separate conjuncts retaining their asserted relationship. Stage B currently lacks
a concrete valid wire example. This experiment must keep code/parser/runtime,
500+500 caps, aggregate deadline, original six/23 obligations and all failure
denominators fixed. Do not repair historical JSON, let B reselect, or claim success
from valid formatting alone. A errors remain independently failed even if B
format improves; complete next outputs must guide any later change rather than a
prewritten prompt chain. No model call, candidate edit, new contrast inspection,
raw repair or sealed-reserve read was performed by the reviewer.

## Two-pass v2 pre-inference prompt clearance

Candidate `05aff80bcaa6e3c2448adaa9fb30d644d176d8a29fe590ec268c4b843e9e977f`
matches independent readback. AST comparison with actual frozen two-pass v1
confirms only version and the two prompts changed. All 67 offline controls pass;
the concrete unrelated matched example independently passes both strict parsers
while fidelity remains false. It demonstrates exact string IDs, null, one root,
preserved IDs, withdrawn fragment/link and retained conjunct relationship. No
aviation answer facts enter the examples. No concrete blocker was found for the
unchanged six-case no-retry diagnostic; code/runtime, budgets, semantic gates and
failure denominators remain fixed. Formatting improvements cannot erase A's
selection failures or certify B's meaning. No model call, candidate edit, raw
repair, additional contrast or reserve read was performed by the reviewer.
