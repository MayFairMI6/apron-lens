# Independent typed NLI review

Final decision: **reject both NLI development versions; stop at the revision
cap and leave the unused 24-case pilot untouched.** V2 delivers 5/6 exact reviews
and 2/3 fully correct valid-answer reviews, below the required 6/6 and 3/3.
Production typed feedback remains unchanged. The detailed v1 history and final
v2 audit follow.

The initial discriminative candidate fails its exposed six-case development gate:
**1/6 exact delivered reviews**, despite **6/6 mechanically accepted reviews**.
Do not promote v1 or consume the unused 24-case pilot on this result. Three
fully correct learner answers all receive `needs_review`; there is no demonstrated
valid-answer semantic success among those three. The partial answer correctly
retains its missing hold point. The two unsafe controls receive `needs_review`,
without false credit, but their substantive statuses are not fully correct.

This reviewer inspected source, all six learner answers/reports, every authored
expected status, every emitted point/quotation and **all 58 raw NLI pair-score
rows** in `outputs/typed-nli-development-v1/records.jsonl`. Offline replay using
those saved scores reproduced every review exactly, without loading or calling a
model. All four source hashes in the development lock match current source at
this review. No unused pilot, GPU, new inference, production/UI/media change or
old-result edit was used. Only this review document was created.

## Design and source findings

The direction of inference is explicit and appropriate for the experiment:
learner response → authored criterion proposition for coverage; exact learner
sentence/short complete response → proposition for quotation witnesses; eligible
current report messages → each learner sentence for grounding. The classifier
does not generate answers, IDs, quotations or JSON. Code assembles the existing
contract. That removes a generation dependency, but does not make classifier
judgments accurate or their probabilities calibrated.

All twelve live rubric mappings were independently inspected before development.
The pre-inference refinements removed an unnecessary inbound qualifier from the
waiting proposition, avoided requiring a superseded off-block time in the latest
estimate proposition, and used a fuel/baggage non-inference proposition instead
of requiring an asserted factual denial of baggage completion. These changes
occurred before the frozen initial run, not in response to its outcomes.

| Exercise | Check 1 | Check 2 | Check 3 |
|---|---|---|---|
| surface_conflict | Held flight; service-vehicle obstruction | Ground-hold release; connection to cleared vehicle | Unconfirmed takeoff permission; ground release does not establish it |
| late_arrival | TRN103 waiting for Stand B; TRN102 occupant | Availability unconfirmed; reposition plan insufficient | Confirmed stand availability; related exercise hold release |
| late_baggage | Late baggage delay; fuel complete and separate from baggage completion | Latest 10:35 estimate; estimate does not establish clearance | Overall readiness unconfirmed; no takeoff/every-prerequisite inference |
| fog_restrictions | Active procedures and safeguarding; held flight and no clearance | Cancelled procedures with safeguarding retained; hold/unconfirmed clearance | Confirmed safeguarding cancellation; parked flight/unconfirmed clearance |

The propositions broadly preserve authored criterion meanings. They are authored
hypotheses, not independently verified correct-answer labels. Composite facets
must all entail for `met`; any confident contradiction takes priority; a
confident neutral facet produces `missing`; otherwise the criterion is uncertain.
Several hypotheses remain compounds, and their semantic interpretation remains
the model's responsibility. Full-response inference does not independently prove
that every requested facet was expressed.

Input validation rejects duplicate reports, wrong episode, future receipts and
unavailable authored bundles before tokenization/inference. Grounding context
removes only wholly explicitly superseded messages and withholds partially
superseded messages. It does not splice clauses or invent current report wording.
History-marked learner sentences can include qualified old messages but cannot
receive an all-met grounding result merely through those historical premises.
This conservative lexical history handling is bounded and may withhold harmless
uses of words such as “before.” No general temporal reasoning guarantee follows.

Substantive citations are authored comparison bundles. Grounding citations are
the chosen actual premise's report IDs intersected with the authored grounding
bundle; an empty intersection withholds. Neither eligibility nor the presence of
a reference means the cited report entails the feedback. In particular, an
invented fire is not proven by the unrelated reports attached to its correction.

A confident neutral grounding label maps to the existing `contradicted` contract
bucket to block unsupported approval. Its comment is correctly **“Not established
by the received reports.”** That is an unsupported-claim judgment, not a claim
that an opposite fact has been proven. Conversely, neutral criterion coverage
means missing evidence that the learner expressed the point, not an explicit
wrong assertion. Both interpretations still rely on a fallible classifier.

Quotes use original offsets and are at most 160 characters; no generated or
truncated quote is accepted. A met composite must have witnesses for each facet,
and their complete contiguous span must fit. Lack of an eligible witness or an
overwide span withholds. Grounding scores every complete learner sentence, then
aggregates any unsupported sentence before uncertainty. This preserves separate
extra sentences, but does not deterministically decompose every conjunction or
claim within a sentence. An exact quote can still be irrelevant to its judgment,
as the observed authority failure below demonstrates.

The pinned model/revision, label order, threshold 0.8, CPU/batch configuration and
source snapshots are preserved in the development lock. Model file provenance is
recorded separately in `outputs/typed-nli-pass/model-provenance.json`. The
threshold is expressly uncalibrated. Inputs over 512 tokens are rejected rather
than truncated; observed pair lengths range below that bound, with a maximum
155 tokens. Startup took 2.961 seconds; measured reviews took 0.067–0.209 seconds.
These are six development measurements, not native-flow timing or a controlled
latency comparison. The 55-second deadline is checked between CPU batches and
before returning; a running kernel is not interrupted, so no hard wall-clock
termination guarantee is established.

## Actual six-case findings

| Index | Independent finding |
|---|---|
| 0 | Correct waiting/occupant answer: both criteria met, but grounding falsely marks it unsupported. Report→sentence neutral probability is 0.90688 despite the report establishing the stated waiting/occupancy relation. All three statuses should be met. |
| 1 | Correct baggage/fuel answer: delay met, separation uncertain and grounding contradicted. Fuel-completion facet entailment is only 0.55303; the supported “Fuel is complete, but…” sentence receives report→sentence neutral 0.98222. This is false negative feedback on a valid answer, not genuine learner uncertainty. |
| 2 | Omitted hold answer: procedures met, hold missing, grounding met. Both omitted hold/clearance facets are neutral; no learner words are invented and no implicit hold credit is awarded. This is the sole exact review. |
| 3 | False TRN103 occupancy: occupant and grounding correctly contradicted, but flight uncertain rather than contradicted. The waiting proposition's highest score is neutral 0.71053, below the fixed threshold. Overall `needs_review` is appropriate, but exact status coverage fails. |
| 4 | Correct safeguarding/authority core plus invented fire: confirmation met and fire correctly unsupported (neutral 0.99480). Authority is falsely missing because full-response parked entailment is only 0.00118 and neutral is 0.99628, even though the correct core sentence alone entails parked at 0.99449. The unrelated extra sentence damages correct-core coverage. |
| 5 | Fully correct explicit unknown/parked answer: authority falsely contradicted. Full-response unknown-clearance contradiction is 0.89138; parked contradiction is 0.95367. The chosen authority quote is the unrelated safeguarding-confirmation sentence, scored as contradicting unconfirmed departure clearance at 0.99860. The actual authority sentence entails unknown clearance at 0.99557 and parked at 0.99437. Literal quotation validity conceals a severe relevance error. |

Thus all six reviews pass the output contract, but five have semantic status
errors. All three fully correct answers are delivered erroneous negative
feedback; semantic valid-answer acceptance is 0/3 despite mechanical yield 6/6.
There is no observed false-credit criterion in these six, but that does not rescue
the exact or valid-answer gate. Unsafe-control verdicts alone are insufficient to
call the reviewer correct.

## Decision and remaining action

**V1 rejected.** The unchanged production typed reviewer remains the default.
The experiment permits at most one documented development revision after this
initial result; it does not require spending that revision. Any revision must
preserve these results and freeze its new policy before inference. Do not tune a
threshold alone until these unrelated-context and witness-relevance failures
appear to pass: the scores are confidently wrong, and the diagnosis concerns
semantic input/aggregation as well as uncertainty calibration.

A defensible revision would need a coherent policy for relevant learner spans,
contradictions, cross-sentence identity/negation and all extra assertions. Simply
choosing the highest entailing sentence can ignore an explicit contradiction
elsewhere; treating every sentence as contradictory evidence can reproduce the
irrelevant-witness error above. Similarly, reducing report context can improve
focus but can hide an exception or unsupported additional claim. Those tradeoffs
need an authored, frozen policy and the same six-case gate, not case-specific
answer insertion. If the second allowed version fails, stop before the fresh
pilot. Passing either exposed development version would still require independent
fresh-pilot label validation, frozen paired production comparison and the saved
acceptance gates before promotion.

A proposed final revision was reviewed conceptually after v1: authored neutral
facet-topic relevance can select complete learner sentences; conflicting relevant
statements must block met. Grounding can compare every learner sentence with
short active criterion-report bundles and individual current reports, retaining
the actual chosen premise's citations. This is a legitimate bounded authored
policy, rather than case-ID logic, only if it is frozen across all twelve live
rubrics, uses no expected truth/status in relevance selection, preserves whole
sentences/qualifiers and handles incompatible relevant current reports
conservatively. An individual entailing report cannot silently override a
relevant conflicting current report. Ambiguous pronoun context must remain
uncertain or withheld.

An explicit occupancy counterhypothesis may represent an authored exclusive
relation for the same named flight/resource; waiting for a stand or planned
movement cannot trigger it. Such checks are domain assumptions whose scope must
be reported, not general NLI competence. No v2 implementation or outcome is
accepted by this conceptual recommendation. The single-revision cap and unused
fresh-pilot boundary remain in force.

## Final permitted revision: pre-inference source review

The final v2 source was independently inspected before its six-case run. Candidate
SHA-256 is `676983919306563a2fb06d75d538060c049d57fb75b10c9dbef433f81e95801b`;
propositions SHA-256 is
`3a18d47632a2e29fc48e72b84cf11ff3c5a9720c40e1180f68ead3aa3a5c3b27`.
The same pinned classifier and 0.8 threshold remain. Sixteen offline injected-score
and mock checks passed independently; no model was loaded by those checks.

V2 uses neutral topical sentence selection across all twelve rubrics, preserves
all clauses of selected sentences, and blocks met for conflicting relevant
entailment/contradiction. No-topic coverage means missing; a topically relevant
sentence whose meaning is merely neutral now means uncertain rather than a
confident assertion that the learner omitted it. This policy change is explicit
and must be evaluated against the unchanged expected statuses, not used to relax
the six-case gate.

The separately audited optional entity context adds only a uniquely anchored
learner flight name consistent with source scope. Names normalize to uppercase;
identity-denial, quotation/speaker, correction and competing-identity safeguards
conservatively disable context. The visible quote remains the original sentence,
not the context-bearing NLI premise. This is a bounded lexical coreference rule,
not a general attribution guarantee. Baggage-delay wording no longer requires
“loading,” while preserving the late-baggage cause and flight identity.

Every learner sentence remains mandatory for grounding. Active bundles, combined
relevant reports and individual reports are considered, with a relevant combined
contradiction veto and pre-inference current typed-fact conflict withholding.
All-met grounding citations union the actual support-premise source IDs for every
sentence, instead of representing only the first sentence. Failure/uncertainty
cites the selected comparison context. The authored occupancy counter is restricted
to the same explicit flight/resource and excludes planned/future/waiting forms.

No concrete source blocker remained for the single permitted v2 development run.
This clearance is permission to test the isolated experiment, not semantic
acceptance, promotion, or a claim that lexical relevance and NLI check every
possible assertion. The final six outcomes still determine whether the unused
pilot boundary can be reconsidered.


## Final v2 outcome: rejected, revision cap exhausted

The final six-case run at `outputs/typed-nli-development-v2/` completed with all
six reviews mechanically accepted and **5/6 exact**. This reviewer independently
read every raw probability row (**44 pairs**), every learner response and report,
and all six assembled reviews. Saved-score offline replay reproduced all six
reviews exactly, with no model loading or calls. All source hashes in the v2 lock
match reviewed source. Quotes remain exact contiguous original substrings within
160 characters, and references remain eligible comparison context.

| Index | Final independent finding |
|---|---|
| 0 | Correct waiting/occupant answer now receives all met and `supported`. The short L010 grounding premise entails the complete sentence at 0.97375, and is the actual cited support source. |
| 1 | Correct baggage/fuel answer still fails: delay met, separation uncertain, grounding uncertain, overall `partly_supported`. The unrelated baggage-delay sentence is scored as contradicting the fuel/baggage non-inference facet at 0.99275, while the actual fuel sentence entails it at 0.99567. The conservative conflict rule correctly blocks cherry-picked credit, but the underlying relevance/classifier combination has manufactured that conflict. The identity-context fuel-completion facet itself now entails at 0.94645. Grounding against L011/L014 has no confident entailment for the complete fuel/non-inference sentence (combined scores contradiction 0.39991, entailment 0.06859, neutral 0.53150); L014 alone is neutral 0.99904. The learner's accurate meaning has not become unclear merely because the classifier fails. |
| 2 | Procedures met, omitted hold missing, grounding met and `partly_supported`, matching gold. No implicit hold/permission credit. |
| 3 | All three points contradicted and `needs_review`, matching gold. The explicit same-flight/resource occupancy counter entails at 0.99554; this authored exclusive-relation policy supplies the flight contradiction rather than an improved waiting-proposition contradiction score. Grounding also independently contradicts at 0.99759 for the combined relevant reports. |
| 4 | Both correct core criteria met, extra engine-fire sentence unsupported, overall `needs_review`, matching gold. The core is preserved separately; fire is quoted exactly. R008 is the actual comparison premise. Its contradiction probability 0.95804 is still only fallible classifier evidence; the conservative comment says “Not established,” rather than claiming a proven opposite fact. |
| 5 | Correct explicit unknown/parked answer now receives all met and `supported`. Authority quotes the relevant second learner sentence. Both sentence grounding premises use R008; the all-met citation union consequently remains R008. |

There are no observed false-credit criteria among these six. Two of the three
fully correct answers now receive exact positive feedback, while the correct
baggage/fuel answer remains negatively qualified. Therefore **6/6 delivery is not
6/6 semantic success**, and **2/3 valid-answer success fails the predeclared gate**.
All three non-fully-correct controls receive the expected statuses; those controls
do not compensate for the remaining valid-answer failure.

V2 maximum pair length is 83 tokens, below the 512-token rejection limit. Startup
is recorded at 2.556 seconds; individual reviews at 0.029–0.141 seconds. No case
was withheld, retried, truncated or over deadline in this run. These remain
CPU-only exposed-development measurements with no native execution or general
latency guarantee. The observed exact improvement from 1/6 to 5/6 is development
iteration on the same known cases, not an independent accuracy improvement claim.

The initial version and one permitted revision are now exhausted. **Stop; no
further proposition, relevance, aggregation, model, threshold or prompt revision
under this experiment, and no fresh-pilot consumption or production promotion.**
Retain both source freezes, all 102 total pair rows across versions, failed
judgments and exact outcomes. Mechanical citation/quote repair is useful isolated
engineering evidence but is not a deployable semantic reviewer.

This independent review made no new model/GPU calls, did not read the unused
24-case pilot, and changed only this document during the final audit. Broader
suite, preservation, ledger and publication checks belong to the coordinator's
separate receipts; no video, UI, scene or production change is claimed here.
