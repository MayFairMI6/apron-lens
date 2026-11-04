# Independent typed relation review and evaluation separation

The new relation experiment is separate from the preserved rejected NLI runs.
The user's latest instruction authorizes continued development toward an end-to-end
acceptance gate. Earlier experiment caps and earlier suggestions to run new
answers despite a failed development gate do not govern this new workflow.
Production typed feedback, prior results and the finished video remain preserved.

Two independently authored suites are ready before new candidate inference:

| Suite | File | Composition | Access and use |
|---|---|---|---|
| Exposed development | `experiments/typed_relation_review/development-v1.json` | 24 answers: one valid and one invalid/partial contrast at each of all 12 real lesson checkpoints | Coordinator/implementer may inspect and develop against it; freeze each candidate version and preserve each run |
| Reserved independent evaluation | `experiments/typed_relation_review/fresh-v1.json` | 24 distinct new answers: 12 valid and 12 invalid/partial; includes 4 valid and 4 invalid/partial fuel/baggage cases and all 12 checkpoints | Keep hidden from implementation until the six exposed cases and varied development pass; no tuning against reserved outcomes |

Development suite SHA-256:
`e6ee0e234919c56276e199419f35627aedd6528702f3003c386d57b25654f397`.
Reserved suite final SHA-256:
`3052119fa3905e862c8ca30c53e99bc6be15684322fe637847dd58c8ec3eeb6b`.

The reserved answers and gold did not change after their initial authoring. Only
planning metadata was updated before calls to reflect the latest user instruction
to reserve the suite until development passes. Earlier pre-update hashes are not
the final file identity. The initial metadata did not authorize the coordinator
to read reserved content; the final policy above is authoritative.

Both files contain top-level `metadata` and `cases`. Each case has a model input
`payload`, fixed per-criterion `expected` statuses and a `why` explanation, plus
evaluation metadata. Only `payload` may enter the candidate. Category, tags,
expected statuses, reasons, indices and metadata must never enter model input or
be consulted by semantic selection. Top-level checkpoint/exercise bookkeeping
also remains outside model input; the payload retains its actual exercise
question and checkpoint identity as normal context.

Payloads were built with `TrainingSession.prepare_response`, seed 17, at each
actual lesson checkpoint. All received reports, authored criteria, question and
receipt cutoff are retained. Random session episode identifiers were consistently
normalized in payload/report context for the saved fixtures only. The initial
system Python lacked FastAPI; the project environment successfully built the
payloads. No model or GPU call was performed. No old unused typed pilot or LoRA
held-out labels were opened or copied.

The development gold was independently checked against the actual reports and
rubrics before candidate calls. It includes valid paraphrases and invalid or
partial contrasts involving wrong aircraft, unsupported permission, superseded
values, plan-versus-completion, negation reversal and omitted points. Missing
requested content is missing; a correct core with an unrelated unsupported extra
retains its correct core statuses while grounding blocks approval. Correct latest
values do not require reciting superseded values. Correct explicit unknowns are
valid; unknown clearance is not an asserted denial. No case demands a denial of
every possible unasked extra claim. Reserved cases add short/long wording,
corrections, non-implication paraphrases and conjunctions without exposing their
answers here. Both suites have a 12/12 valid-versus-invalid/partial split, and no
answer text is identical across the two suites. Reserved maximum response length
is 258 characters, within the existing 1200-character input limit; long answers
are deliberately not removed merely to fit the legacy display quotation field.

## Initial implementation-plan review

The visible new candidate uses a bounded typed service relation rather than an
exact-answer whitelist. It parses a complete original sentence expressing a
completed first service and either denied implication to a second service or an
explicit second unresolved state. Current typed source facts must establish the
same targeted flight and distinct service states; wrong/competing flight identity
and positive implication do not obtain rule support. Exact full-sentence parsing
must consume every token, so adding an unsupported extra clause cannot retain
rule approval. Rule-derived support, source IDs and literal spans must be audited
separately from the unchanged NLI probability rows.

This is a legitimate isolated development plan if its scope is disclosed and
semantic assumptions are tested. Grounding sources remain comparison references,
not proof that every classifier or rule judgment is correct. The neutral
fuel-and-baggage relevance conjunction avoids treating an unrelated baggage-only
sentence as contradictory evidence about a cross-service non-implication.
Fallback NLI remains fallible, and using typed-state rules for recognized grammar
does not establish general language understanding. Every sentence and every
unsupported addition must still be checked; the rule must not bypass conflicts
elsewhere in the learner response.

One concrete pre-freeze concern was sent to the implementer: the initial completion
grammar allowed past-only “was complete.” A past assertion alone must not trigger
rule credit for the requested current service state. Restrict rule approval to
present/current or present-perfect completed-state forms, or withhold past-only
syntax while leaving ordinary semantic fallback intact. No implementation edit
was made by this reviewer. The final pre-call source removed that past-only form; source clearance follows. Actual inference results remain pending.

## Acceptance and preservation

Keep the old six exposed cases as regressions and the new varied suite as
explicitly exposed development. Continue authorized development on those data,
freezing sources/configuration before each run and preserving every result. Do
not inspect the reserved 24 answers to decide how to implement the candidate.
The reserved file can be opened only once the stated development gates pass;
then freeze candidate/runtime/baseline and evaluate both arms without further
tuning against reserved failures.

The current acceptance requirements include valid-answer success at least 10/12,
no newly failing baseline case, no false credit, relevant exact quotations,
eligible comparison references, bounded response/deadline behavior and successful
native end-to-end flow. Report exact per-criterion correctness, accepted yield,
valid-answer correctness, false credit and withholding separately. A mechanical
contract pass or a correct overall unsafe verdict cannot substitute for correct
semantic feedback on the requested points. The independent milestone reviewer
and coordinator retain responsibility for the final adoption/placement decision.
No implementation success, native run, promotion, or defect closure is claimed
by authoring these suites.


## Initial source clearance

The initial relation candidate was reviewed before its new inference run.
Candidate SHA-256:
`4b0f5ef0f41bb55d9198c526c54a00e4491db3dcd7199c75c607e23f39b03ef8`.
Propositions SHA-256:
`8181d79c85600acf31a902e652db12bae3e744760fca39b46d3bed4b184cde8e`.
The bounded grammar now accepts current/present-perfect completion rather than
past-only “was complete,” supports ordinary adnominal completion wording and
referential service wording without matching an exact saved answer, and retains
complete-sentence consumption. The source records rule-derived support in its
semantic audit, while preserving all raw NLI pair scores.

This reviewer independently ran 21 offline mock/injected-score tests; all passed,
including the previous sixteen policy checks. The case runner passes only
`payload` to evaluation, freezes source/case hashes before inference, and records
`semanticRuleAudit`, planned pairs, raw scores and final results. This verifies
logging/policy mechanics, not model accuracy. The original report snapshots and
receipt cutoffs for every case in both suites were independently reconstructed
from `TrainingSession` and matched. No concrete blocker remained for the isolated
initial experiment. No production/adoption or native-flow acceptance is implied.

## Continued development: consolidated design guidance

The latest user instruction keeps this workflow active toward end-to-end gates;
failed development attempts are preserved evidence, not a reason to request
another approval. The old NLI experiment remains rejected and intact. The
reserved file is still unchanged and unavailable to implementation work.

The exposed six-case service check reached 6/6, but varied development exposed
broader shortcomings: initial relation policy 10/24 exact; a separately pinned
larger verifier with the same policy 12/24 exact and 7/12 valid exact, with no
observed false-credit criterion. The latter records are at
`outputs/relation-development-strong-r1/`. This reviewer read the development
failures and their criterion pair scores for design diagnosis. This is not yet a
complete final acceptance audit of that model arm.

The evidence favors relation-specific coverage and whole-answer conflict checks,
rather than more permissive thresholds or a bigger classifier alone. An occupant
facet needs an occupancy relation, not any mention of a stand. A delay facet
needs a delay/cause relation, not every baggage assertion. Estimate/permission
scope needs the relation between them, rather than a time value alone. A genuinely
absent requested relation is missing; a present but unclear relation is uncertain.
An explicit wrong flight on the same relation can contradict the requested
answer only when attribution is unambiguous. Correct requested claims must retain
their own spans when an unrelated added claim is unsupported; that extra claim
still blocks grounding approval. Clause splitting must preserve subject,
negation, modality, attribution and the complete original sentence for audit and
all-claim review, rather than discard inconvenient text.

Report-scope invariants are acceptable only within an explicit contract. Absence
of a current target-flight `overall_readiness` fact establishes lack of reported
readiness, never a factual “not ready” state. Takeoff clearance has no dedicated
property in the current typed schema, so simply testing for an absent clearance
field would always return unknown. Any clearance-scope rule instead needs an
explicit authored no-clearance/unconfirmed report boundary and must withhold if
eligible report text presents a positive-authority conflict or ambiguity. Code
may verify a learner's explicitly expressed nonconfirmation or non-implication;
it must not insert an omitted answer or convert a factual denial into uncertainty.

Hypotheses may remove non-required contextual qualifiers such as “exercise” when
the requested meaning is already the named aircraft's ground-hold release, but
must retain every substantive requested facet. All policy changes remain exposed
development changes, frozen before their run. Reserved inputs/gold and their hash
must remain unchanged through those iterations. No adoption recommendation is
made by these design observations.

## Read-only production integration guidance

An optional `typed_review_service` argument to `training_app` can preserve its
existing default reviewer and ordinary Qwen path while a graduated policy is
introduced. Do not import `experiments` from production. After acceptance, rubric
semantics and relation/grounding policy belong in the backend; generic pinned NLI
loading and pair scoring belong in a separate `modelaccess` classifier component.
The classifier should expose explicit pair-scoring capability, model/revision,
label mapping, finite probabilities and token-bound errors, without generation
settings or an implied language-model completion.

Use a minimal typed request/outcome interface: request ID, immutable context
fingerprint/payload and deadline; outcome state `completed`, `failed` or
`timed_out`, exact request/context identity, pinned model/policy identity, validated
review and pair/rule audit. Classifier completion must not be represented as
`FinishReason.STOP`, EOS generation, output-token usage or a fabricated generated
response. Keep classification pair/input-token counts separate from text-generation
usage. Errors must remain explicit, with no automatic fall back to a different
model or the old reviewer.

The existing killable owner provides useful lifetime/deadline behavior, but
`IsolatedTrainingAdapter._call` currently hardcodes `checked_training_result`,
`finish_reason` and generative request settings. Passing a classifier outcome
through it unchanged is incorrect. A small operation-specific validation/failure
hook or a shared generic owner can reuse the proven process/transport lifecycle,
while leaving the ordinary default checks intact. A separate typed-review owner
must stop before replacement, load and warm once, respect its complete-call
budget and close on service exit. Keep the shared app inference lock initially;
separate engines do not by themselves justify unmeasured concurrent inference.
Both readiness states must be truthful, with the optional path's failure isolated
rather than advertised as a ready classifier.

End-to-end checks should follow the actual submit/review/display path: a correct
new answer, an omitted point, a correct core plus unsupported same-sentence extra,
wrong-flight attribution, and explicit unknown permission. Verify unchanged UI
schema, literal bounded quote, relevant comparison source display, user response
preservation and exactly one state application. Exercise timeout/hang/crash and
recovery in the separate owner, retaining the busy lock until the old call is
stopped; verify next-request recovery, retry idempotence, stale revision/late
result rejection, request/context mismatch and shutdown of both owners. Inspect
real native feedback and verify ordinary assistant behavior remains intact.
Mock policy checks and a ready log do not substitute for that native observation.
No integration code was changed by this review.

The r2 relation source was independently read and its 25 offline checks passed
before its next development run. Candidate hash
`174c07bdd809ea2c7b0b2d03a5b2bf509350ffde04c17e9006c3d6420e411b94` and
propositions hash
`881bc2c87b74b099361043c5f316376a631d4d22deb5e4f5a128bbaafc174527`
match the coordinator's freeze. Outer negation, conditions and modals now preserve
whole scope and prevent deterministic identity/counter inference; independently
stated other-flight facts do not automatically contradict a correctly stated
target answer. Exact clause spans and minimum contiguous relation windows are
still fallible lexical extraction. Full original sentences remain grounding
inputs, and no semantic guarantee follows from the source/test clearance.

## Inactive service scaffold review

The coordinator added an optional separate classifier service without enabling it
in `main` or importing experimental policy into production. This reviewer read
`modelaccess/nli.py`, `backend/typed_review_service.py`, the two operation-specific
worker validation hooks and optional application lifecycle/routing changes.
Ordinary generation retains its default result checks. Classification outcomes
have their own completion state and omit EOS, generation finish reasons and
output-token usage. Successful outcomes bind request/context, model revision and
policy version and pass the existing review contract; malformed metadata and
failed outcomes containing reviews are rejected.

Initial review found a startup cleanup gap, incomplete outcome metadata checks
and missing typed-owner readiness admission. The coordinator repaired them.
This reviewer independently ran the updated five service/HTTP tests: all passed,
including a real fake-worker timeout/replacement/explicit retry, malformed
identity/revision/policy/audit/timing outcomes, classification audit, separate HTTP
routing, recovering status, 429 without response-state mutation, cached duplicate
without another inference and close-on-exit. An additional mock startup fault
probe verified typed cleanup still runs when ordinary cleanup throws.

No new concrete blocker remains in the inactive scaffold. Input episode/cutoff,
duplicate report and authored-bundle preflight must still execute in the final
backend policy before classifier calls; the experimental candidate currently
provides it. A production activation still requires semantic gates, graduated
backend policy, preserved model provenance and native end-to-end review. The
coordinator reports a real generic-classifier pair smoke, but this reviewer did
not rerun it. No classifier, GPU or other model was called during this review;
no source file was edited by the reviewer.

## Development-only exact-pair reuse review

Exact historical score reuse is cleared for the two hash-allowlisted exposed
fixtures only. It is not permitted for reserved evaluation, final acceptance or
performance claims. The reviewer confirmed and reported an initial missing source
fixture guard: an unknown source fixture could be indexed despite an allowed
target. The coordinator fixed that guard before use. Both target and source
fixture hashes are now checked; recursively reused rows are skipped so cached
provenance identifies an actual original measurement.

The wrapper reuses probabilities only, rebuilds current pair/source/rule metadata,
checks current tokenizer bounds, rejects invalid probabilities and verifies model,
revision, label order and recorded CPU/torch compatibility. It logs current
artifact/runtime provenance, historical file/row/pair references, hit/miss counts,
duplicate maximum difference and threshold/label conflicts. Conflicting duplicates
force fresh development inference. Records, locks and startup files are all
hashed before use and rechecked after the run. Historical torch is recorded;
continuity of other historical runtime components remains an explicitly stated
development-pass assumption, not a retroactive runtime certificate.

Three independent mock tests passed, including reserved target/source rejection,
current-metadata preservation, immutable provenance, token bounds and conflict
recomputation. Reviewed cache hash is
`70a2fcf4681c5d1183c7d4675924514db8aa949a4675b246897ed1d8de302020`;
runner hash is
`7fd7e6537da23feaf37e5bc419fcc5bff530200b6f3fe62fba4d756eb7d7e05f`.
No model was called by this review. Cached development timing is mixed retrieval
and inference; cache hits are neither new classifier calls nor fresh empirical
acceptance evidence. Reserved and final acceptance must remain fully uncached.

## R9 implementation after the failed first reserve — 3 November 2026

Implementer record (Claude implementation/runtime agent). The first reserve
`fresh-v1.json` is exposed and was used here as development/regression data;
its results below are development fit, not independent acceptance. The new
held-out reserve was not opened. No gold label, threshold, model, runner,
quotation limit or source check changed.

Frozen candidate: `typed-service-relation-review-v9` (MPS module version
`typed-service-relation-review-v9-anli-large-mps`), `candidate.py` SHA-256
`547a0f5f7d79093154002497be50ab957925e721c2e1ca04dffa52f6b4811ded`.
`propositions.py`, `mps_candidate.py`, `strong_candidate.py`, the runner,
`backend/training_assessment.py` and `modelaccess/nli.py` are unchanged from R8.

General mechanisms changed (no answer whitelist, no gold or metadata input):

- **Relation coverage paraphrases.** Neutral epistemic and contrastive wording
  ("tell", "evidence", "show", "neither", "not a … clearance", "only an
  estimate") now licenses a comparison; baggage delay also covers "holding up"
  and "late bags"; readiness status covers "confirm/establish". Coverage only
  admits a pair; the classifier still decides direction.
- **Anaphora.** A sentence-initial anaphor ("It", "That", "Even together, those
  updates") keeps its exact earlier learner sentence(s) as premise context, and
  an exact two-sentence window is added as a literal unit when it expresses the
  relation. Flight identity can come from an antecedent only when it names one
  flight and has no quotation or identity switch. Within a sentence, an
  anaphoric clause is grounded together with its preceding clause.
- **Corrections.** "Correction"/"actually" are identity-ambiguous only when the
  learner names more than one flight.
- **Same-flight relevance.** A report message without a flight name still
  belongs to its typed flight; another flight's identical scope wording is no
  longer same-flight evidence.
- **Demonstrative back-references.** "from that cancellation" does not create a
  new safeguarding-status unit.
- **Antecedent-resolved grounding.** For an anaphoric sentence, the exact window
  from its antecedent is compared as support-only evidence. It cannot veto, and
  cannot turn neutral checks into a contradiction.
- **Clause-level takeoff scope rule (v2).** With the existing explicit source
  scope ("No runway or takeoff clearance is represented") for the target flight,
  an affirmative clause granting runway/takeoff permission to that flight is
  contradicted, quoting the exact claim. Negation, negative quantifiers, modals,
  conditions, attribution, qualifiers, plans and other flights are refused.
  "Departure clearance" alone stays outside this rule and remains NLI-judged.
- **Per-facet quotation witnesses.** When one span covering every facet witness
  exceeds the unchanged 160-character field, the display quote covers as many
  facet witnesses as fit; every facet witness is kept in the semantic audit.

Uncached gate runs (MPS float16, threshold 0.8, no fallback):

| Suite | Output | Exact | Valid exact | Delivered | False credit |
|---|---|---:|---:|---:|---:|
| Old regressions | `outputs/relation-regression-mps-r9/` | 6/6 | 3/3 | 6/6 | 0 |
| Development | `outputs/relation-development-mps-r9/` | 24/24 | 12/12 | 24/24 | 0 |
| Exposed first reserve | `outputs/relation-firstreserve-mps-r9/` | 24/24 | 12/12 | 24/24 | 0 |

All 13 first-reserve cases that failed in R8 (0, 1, 2, 3, 6, 9, 10, 11, 12, 16,
17, 18, 22) are now exact, including baseline-exact cases 10, 11 and 17. No
case in any suite that was exact in R8 changed. Every planned pair has a finite
row; maximum input is 479 tokens. Direct startup was 2.83–2.88 seconds; direct
review measurements were 0.134–4.329 seconds. These are not native-owner
latency results. Flipping every row with top probability 0.75–0.85 across the
threshold changes only development case 8 (plan, 0.831), an identical R8 row.

Development exploration used a scratch exact-pair replay of earlier MPS rows
plus new MPS scoring, outside the repository; it is not evidence. The uncached
runs above are the record. A handful of invented invalid variants (wrong
flight, wrong estimate, positive implication) produced no false credit in that
scratch check; this is informal and not a test set.

Limits: fitting the exposed first reserve does not show generalization. The
lexical anaphora, coverage and permission grammars remain fallible. Acceptance
still requires the independent held-out reserve under the unchanged gates and
the separate baseline comparison, then runtime/native review.
