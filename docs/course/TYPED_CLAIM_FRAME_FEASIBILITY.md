# Feasibility of evidence-bearing learner claim frames

A small deterministic mechanism can preserve explicit surface structure for a
bounded subset of answers. The existing evidence does not establish that it can
derive reliable semantic frames across the 78 exposed answers, or that the
pinned classifier can supply unresolved attributes. A source-bound frame is an
auditable representation, not proof that its interpretation is correct. This
note proposes a falsifiable diagnostic; it implements nothing and authorizes no
model call, parser dependency, candidate change, or adoption.

This assessment follows the final 4 November strategy section in
`MILESTONE_LEDGER.md`, the R11v3.2 assessment and exposed second-reserve replay in
`TYPED_REVIEW_FINAL_ACCEPTANCE.md`, its historical R10 and R11 diagnostic notes,
and the cover findings in `TYPED_COVER_DIAGNOSTIC_PLAN.md`. Only public payloads
from the following 78 already exposed records were read: old six at
`outputs/compact-review-development-v2/records.jsonl`, and 24 each in
`development-v1.json`, `fresh-v1.json`, and `fresh-v2.json` under
`experiments/typed_relation_review/`. Prior reserves remain exposed development.
No third-reserve content, candidate implementation, or 3.3 results informed this
note. Gold grading statuses were not read to supply any frames.

## What existing evidence permits

R10's phrase-triggered relation gates missed ordinary paraphrases, fragments,
contractions, and abbreviations. Its sentence-wide modal rules confused a
relative clause about a path an aircraft “would take” with a hedged main
assertion. Its correction list missed an ordinary retraction. Expanding those
lists after each failure is not a uniform discourse mechanism.

R11's meta hypotheses did not establish the needed attributes: current text
could score as historical; correct operational content could score as correction
or unsupported content. Topic-presence probes also failed. Consequently, the
new mechanism must not ask the same classifier whether an aircraft is identified,
a correction occurred, or a claim is ultimately asserted and then treat high
confidence as a scope certificate. Ordinary content comparisons have also falsely
resolved “one of … the other,” credited a withdrawn time, and supplied omitted
safeguarding. Source clock or exact quotation repair alone does not answer these
failures. The cover diagnostic further shows false entailment between broad
readiness unknown and specific clearance unknown in both directions; reciprocal
entailment does not independently validate a frame built from those predictions.

## Concrete bounded algorithm to test

The proposed first experiment is a deterministic **partial recognizer**, using
Python's standard library only. Its grammar and all terminals must be frozen
before testing. A grammar rule may describe a construction across predicates;
it may not match a fixture ID, response string, desired rubric result, or a
case-specific correction phrase added after an error. A finite grammar is still
limited language coverage. Calling its terminal lists grammatical does not make
R10's generalization problem disappear.

1. Preserve the complete original answer and character offsets immutably. Produce
   a token stream with exact spans, including punctuation, contractions, aircraft
   identifiers, times, and stand labels. Expanded contractions are analysis
   alternatives tied to the original token, never substituted learner text.
   Canonical aircraft identifiers may be detected by their identifier syntax;
   actor roles cannot be inferred from identifier order.
2. Run a small chart grammar, retaining **all** parses. Its initial construction
   families are explicit subject–predicate clauses, possessive property/value
   clauses, copular/passive complements, coordination of complete clauses,
   subject-coordinated shared predicates, finite negation, matrix epistemic/modal
   complements, relative clauses, explicit time modifiers, and repair links.
   Predicate and object remain exact surface constituents rather than invented
   canonical propositions. If a construction cannot be parsed without guessing
   its predicate boundary or attachment, mark it unresolved. Punctuation alone
   cannot certify independent assertions.
3. Create candidate frames with exact span references for subject/entity,
   predicate, object/value, negation operator and its argument, modal/epistemic
   operator and its argument, time expression and attachment, and attribution.
   Include entity-candidate sets, competing parses, correction links and frame
   lifecycle (`active`, `withdrawn`, `historical`, or `unresolved`). “Unconfirmed”
   is an epistemic state of its named property, not negation of the event. A
   source nonconfirmation assertion and the learner's inability to decide are
   different operator structures. Keep takeoff clearance, ground release and
   readiness as different surface objects; no similarity score merges them.
4. Link an anaphor only where every retained parse has the same eligible
   antecedent. Record the exact antecedent span and reason. Explicitly different
   actors, ambiguous quantified pairs, or several compatible earlier references
   remain candidate sets. Do not resolve them from the question, reports, rubric,
   source truth, or a preferred NLI score. Unique mention alone is insufficient
   when the grammatical referent could be a stand, update, or service.
5. A correction edge requires a recognized repair construction, an explicit
   replacement constituent, and an unambiguous property/entity binding across
   its two sides. A lexical “correction” occurrence is insufficient. Preserve
   the withdrawn assertion as an audit frame; exclude it only from a later
   current-assertion support obligation. If the recognizer cannot determine
   the repair target, withhold current commitment rather than retain whichever
   value scores best. Historical states stay historical only when the operator
   attachment is uniquely established from learner text.
6. Split conjunctions only with a complete syntactic account of each conjunct,
   including shared subjects and modifier scope. Create a separate support
   obligation for every active factual conjunct and attribution. Preserve
   asserted non-implication relations as relations, rather than turning their
   mentioned objects into factual assertions. Account for every nonpunctuation
   token as an assertion constituent, a scoped operator/link, or explicitly
   unresolved material; an unrecognized tail cannot silently disappear.
7. A frame is structurally usable only when all retained parses agree on the
   relevant entity, relation boundary, polarity, modality, time, and correction
   status. Otherwise retain its alternatives and unresolved reason. Successful
   character-span accounting is a mechanical test, not semantic completeness.
   Grammar abstention is neither evidence of omission nor successful handling.
8. Only after structure is established may the unchanged pinned NLI compare
   ordinary content against a rubric facet or receipt-eligible source. The
   actual premise must remain an exact learner constituent plus, when necessary,
   its exact bound antecedent spans; no generated subject or expected fact is
   inserted. A dependent constituent that cannot stand as exact contextual text
   remains unresolved. Every frame keeps its full original answer as an audited
   control. The primary representation and disagreement rule are fixed globally:
   disagreement with the original-answer control withholds a positive decision;
   it never selects whichever representation earns credit. An agreeing high
   score still cannot repair an unresolved attribute or establish missingness.

This describes the proposed transformations precisely enough to challenge, but
not a finished grammar. In particular, recognizing where an open predicate ends,
handling arbitrary relative clauses, repair discourse, and anaphora are the
unproved work. Before implementation, each proposed grammar production and
terminal inventory must be independently reviewed against the controls below.
The diagnostic must report unsupported constructions explicitly rather than
claiming that these eight steps already solve them.

## Dependency choice and failure boundary

The smallest proposed diagnostic uses no parser package and no new learned
weights. That is a concrete dependency choice: a frozen, bounded chart recognizer
built with the Python standard library. It can test whether a narrow grammatical
subset yields useful structure without introducing another semantic model. It
cannot promise general English coverage, reliable arbitrary predicate boundaries,
or open-ended pronoun and discourse resolution. Filling unsupported patterns by
regular expressions would recreate the failed lexical approach.

If adequate coverage requires general dependency parsing, a concrete alternative
for a separate placement review is spaCy with its English `en_core_web_sm`
pipeline, pinned together with the package version and model artifact hashes.
That pipeline adds learned parser/tagger weights. It is a new dependency/model
choice, not implicitly approved by this note; no package was inspected, installed,
or selected for execution. Dependency arcs could propose subject, coordination,
negation and clause attachments, but do not themselves establish discourse
correction, real-world authority, or all epistemic distinctions. They would need
the same independent frame annotations and failure tests. A parser's predicted
arc is not more authoritative than an unvalidated NLI score. The existing pinned
NLI alone cannot validate this alternative: it has already assigned confidently
wrong entities, correction scope, and unknown-scope relations, and it returns
three pairwise labels rather than independently checked attribute spans.

Abstain on unsupported grammar, incompatible parses, nonunique antecedents,
unbound repair targets, ambiguous temporal attachment, unsplit extra content,
and question-dependent fragments. Also abstain on ordinary-content NLI
conflict/disagreement. Absent a separate validated absence mechanism, no parsed
frame for a rubric facet is not sufficient to declare that facet missing. These
abstentions count against valid-case acceptance; they cannot be hidden by only
reporting precision on the recognized subset.

## Predefined exposed control matrix

The smallest first diagnostic is **24 learner snippets, arranged as 12 fixed
pairs**, using the exposed domain. These are proposed authored development
controls, not an unseen reserve. Freeze their exact text and independently
annotated spans/attributes before building the recognizer. The expected
attributes below are offline test annotations only; neither annotations nor
rubric gold are runtime inputs. The payload question/reports may be retained
for provenance but cannot populate a missing learner entity or relation.

| Pair | A: exact proposed answer | B: exact proposed answer | Predefined structural distinction |
|---|---|---|---|
| 1: explicit roles | TRN102 occupies Stand B. TRN103 waits for Stand B. | TRN103 occupies Stand B. TRN102 waits for Stand B. | Two complete frames with reversed actor bindings; no role by identifier order. |
| 2: unresolved roles | TRN102 and TRN103 are involved: one occupies Stand B and the other waits for it. | TRN102 occupies Stand B and TRN103 waits for it. | A has two actor candidates and no specific assignment; B has explicit bindings. “It” has stand antecedent, not aircraft antecedent. |
| 3: voice | A service vehicle obstructs TRN102's route. | TRN102's route is obstructed by a service vehicle. | Preserve vehicle agent and route owner under active/passive transformation; exact spans differ. |
| 4: negation attachment | Fuel completion does not establish baggage completion. | Fuel is not complete; baggage is complete. | A negates the implication relation and does not assert either service complete. B negates fuel completion and asserts baggage completion. |
| 5: modality attachment | A service vehicle blocks the route TRN102 would take. | A service vehicle might block TRN102's route. | A asserts blockage, with a modal only inside the route's relative clause. B has uncertain blockage. |
| 6: epistemic source | The reports do not confirm takeoff clearance for TRN102. | I cannot tell whether TRN102 has takeoff clearance. | A asserts report-scope nonconfirmation; B expresses learner uncertainty without asserting report contents. Neither denies permission. |
| 7: unknown object | Overall departure readiness remains unconfirmed. | Takeoff clearance remains unconfirmed. | Different explicit objects; no broad-to-specific or specific-to-broad substitution. |
| 8: value correction | TRN102's current off-block estimate is 10:20; correction: it is 10:35. | TRN102's current off-block estimate is 10:35; correction: it is 10:20. | Opposite current values; earlier value retained as withdrawn, with the same explicit repair binding. |
| 9: actor correction | TRN103 — no, sorry, TRN102 — is delayed by late bags. | TRN102 — no, sorry, TRN103 — is delayed by late bags. | Opposite corrected actors; withdrawn actor must not remain a competing current assignment or contaminate following context. |
| 10: historical/current | Safeguarding cancellation was pending; it is now confirmed. | Safeguarding cancellation was confirmed; it is now pending. | Two linked time-scoped frames with opposite current commitment; no admitting the historical state as current. |
| 11: extra obligation | Fuel service for TRN102 is complete, and its baggage loading is complete. | Fuel service for TRN102 is complete, and its baggage loading is complete, and the tower has granted TRN102 takeoff clearance. | B adds a third independent factual obligation with attribution. The familiar first two cannot suppress it. No source-truth claim is annotated here. |
| 12: wording/fragment boundary | Refuelling for TRN102 has finished. | Fuel: complete per ground handling. | A has an explicit aircraft; B has service/value/attribution but no explicit aircraft. Preserve B's absent binding instead of filling it from the expected question. Both should retain their exact predicate/value spans. |

The matrix tests some difficult construction types openly; it does not estimate
unseen generalization. Passing a grammar that simply recognizes these 24 strings
would be meaningless. Freeze production rules first, apply them uniformly, then
also inventory every original answer in the 78 exposed payloads without adding
rules or terminals. Report per-construction unresolved counts and complete-frame
agreement on that inventory, as well as valid coverage when separately evaluated
against existing legitimate review gold. No threshold change, fixture deletion,
phrase addition after failure, or repeated holdout consumption is part of this
experiment. If errors motivate a new grammar, retain the original failed result
and register the revision as exposed development.

## Smallest falsifiable execution proposal

First run only a frame-derivation experiment; **no NLI is necessary**. Independently
annotate the 24 snippets' exact spans and the attributes above. Freeze the grammar,
parser source hash, complete annotations, annotation disagreements and fixture
hashes. Runtime receives only each original answer. Compare produced candidate
frames against annotations field by field, including unsupported/unresolved
outputs, and verify every factual tail is retained. Save full original answers,
all alternative parses, exact frame spans, and transformation reasons. Required
positive outcomes are usable explicit roles, passive roles, main versus relative
modality, both corrections, epistemic-source distinctions, and retained extra
obligations. Required negative outcomes are unresolved actor assignment in pair
2A and no invented aircraft for pair 12B. A reject-all recognizer does not pass.
Any unjustified resolution, dropped conjunct, merged unknown object or reversed
correction invalidates the proposed structural mechanism. An unresolved required
positive shows insufficient coverage; it is not relabeled correct after the run.

If that first stage supports proceeding, a separately approved and frozen
follow-up can use at most **96 ordinary-content pairs**: for each of the 24
snippets, exactly two fixed opposing/content-contrast hypotheses against the
unchanged raw full answer and against its structurally usable exact-span view.
The specific hypotheses, individual expected labels where defensible, and nulls
for ambiguous cases must be independently frozen before calls. Hypotheses must
be ordinary operational content, never “the learner ultimately asserts,” topic
coverage, or correction/history category probes. Unusable views are recorded as
withheld, not rewritten to achieve 96 scores; there is no fallback that turns
raw-answer entailment into resolved scope. Compare both representations rather
than selecting a favorable one. Keep pinned model/revision, actual MPS float16,
threshold 0.8, no question in learner premises, 512-token no-truncation bound,
and existing clock constraints. Record every actual probability and runtime
artifact. This note does not authorize that follow-up or pretend its hypotheses
have already been frozen.

Even successful structure and content diagnostics would establish only exposed
feasibility. A resulting reviewer would still need full exposed/stress results,
independent source/contract review and the unchanged acceptance gates. If a
bounded recognizer cannot derive the required frames with useful coverage,
present that concrete failure and the parser/extraction dependency alternative
for placement review; do not bundle a general parser, Qwen, new weights, or a
new answer format into another source/quotation repair. Keeping the current
reviewer without adoption remains the comparison. No result here closes ML-052.
