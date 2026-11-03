# AirfieldLens execution queue

The owner has adopted the correctness work discussed after the formal-methods
brainstorm. This queue records execution order, dependencies and completion gates;
adding a task does not mean it has been implemented or verified. The decision
record is [the milestone ledger](MILESTONE_LEDGER.md). Work remains confined to
AirfieldLens, with the existing free-assets constraint and local model.

The current F03/T01 typed-lesson acceptance comes first. The newly adopted M1 work
documents and checks those existing contracts; it does not require replacing the
current model-review architecture before the demonstration can be accepted.
The original M2 visual-evidence study, Q01 weather queues, turnaround task and
assigned scenario variations remain in scope. The original M3 integrated
evaluation and controlled size/demand comparison remain in scope. Frozen M1
research, historical recordings and held-out records remain unchanged.

## Execution order

| Order | Unit | Milestone and status | Deliverable | Exit gate |
|---|---|---|---|---|
| 1 | F03/T01 — typed lessons | M1; bounded qualitative prototype verified | Exact v2 restored after the second bounded revision failed review. One full typed fog run plus targeted original-lesson native checks; failures retained. | Preserve failed requests; verify learner interpretation, report eligibility, typing, feedback, retry, stale responses, orientations and debrief. Existing MCQ or positioned API checks do not substitute for native typed-flow acceptance. |
| 2 | C01 — correctness contracts and acceptance record | M1; complete within stated limits | A concise contract mapping each implemented safeguard to code, checks, failures and limits. Source hashes, independent checks, semantic failures and native evidence are consolidated. | Each claimed property has supporting evidence or an explicit unresolved gap. Distinguish structural validation, semantic development checks and native execution. No mathematical-proof or validated-grading claim. |
| 3 | M1 publication and submission preparation | M1; outstanding work | Publish the accepted typed increment with matching demo/script/handoff; finish the separate submission requirements. | Preserve Person 1 audio and historical footage. Complete Person 2 contribution, final one-page reflection review and resolution of the smartphone-evidence requirement. These are distinct from feature acceptance. |
| 4a | C02 — structured claim and evidence checker | M2; queued | A bounded typed-claim vocabulary, eligible-evidence rules, deterministic checker and source/rule trace. The existing model interprets learner wording and proposes claims. Integrate with report/camera evidence and the already-planned validation study. | Demonstrate supported, contradicted, unknown and conflicting cases; check subject/time/provenance and correction handling; measure semantic extraction errors separately. Preserve the original visual-evidence experiment. |
| 4b | C03 — bounded scenario-state specification | M2; queued alongside Q01 design | A small TLA+ specification of report availability, lesson/review transitions and runway/stand reservations, with explicit abstraction and fault/incident transitions. | Define normal/accelerated correspondence at matched source times, specified action schedules and seeds; document safety and progress assumptions. Review representative traces against the implementation. This is a specification deliverable, not a completed proof. |
| 5 | C04 — model checking and comparative evaluation | M3; queued after C02/C03 stabilise | Check the bounded driver/evidence-state model with TLC; record counterexamples and implementation-trace correspondence. Compare direct model review, the existing structural/citation validator and the structured checker on a separately frozen evaluation set. | Publish checked configurations, assumptions, specification/tool versions, outcomes and limitations. Report unsupported feedback, valid answers rejected, uncertainty/coverage and latency; preserve failures whether or not the checker improves results. |

C02 and C03 are supporting parts of the existing M2 work, not separate training
courses. Their design should share the evidence identities and time semantics.
Choose one bounded formal verification target for C04: the driver/evidence-state
model. A separate Dafny implementation-proof project and automatic question
generation are deferred outside this adopted queue. No new renderer, foundation
model, backbone rewrite or video-memory work is required by C01–C04.

## Data, model and training requirements

| Work | Data or inputs needed | Model use | Training needed for this work |
|---|---|---|---|
| C01 | Existing scenario reports, tests, actual-model development logs and native acceptance evidence. | Reuse the existing Qwen3.5-9B service for the already-authorised typed-response checks. | None. |
| C02 | A curated development set and separate frozen evaluation cases containing scenario/run identity, report source/availability times, checkpoint cutoffs, learner responses, expected atomic claims, evidence references and uncertainty labels. | Keep the existing preselected Qwen3.5-9B configuration fixed while developing the language-to-claims interface. The deterministic checker itself is ordinary code. | No LLM fine-tuning or learned checker is required. |
| C03 | Explicit states, transition rules, event traces, reservation constraints and declared incident/fault transitions from the scenario driver. | No language model is required to execute the specification. | None. |
| C04 | Bounded state configurations for model checking; independently frozen evaluation cases and recorded implementation traces for empirical comparisons. | Run the fixed model in the comparative language tasks. TLC's term “model” refers to a system specification, not an ML model. | None for formal verification or the proposed comparison. |

No new external dataset is a prerequisite for this correctness increment. The
authored scenarios and reports supply a starting point, but a defensible evaluation
still needs curated cases and independently checked labels. The existing 18 typed
v2 cases are development material only; they must not later be relabelled as an
unseen test set or used as evidence of general assessment accuracy.

Before generating paraphrases or variants, allocate scenario/template/episode
families to development and evaluation groups, keeping related derivatives
together. Record the split manifest, protocol and hashes. Cover valid paraphrases,
negation, omitted requested information, swapped aircraft, waiting-for versus
occupying, unsupported extra clauses, stale/future/cross-run reports, explicit
unknowns, corrections and conflicting evidence. Independently check reference
claims and citations; model-generated labels are not accepted as ground truth
without review. Any synthetic learner responses must be identified as synthetic.
They do not establish learning benefit or representative student performance.

The checker receives only information available to the learner at the cutoff.
Hidden scene state and reference answers are for annotation/scoring and must not
leak into inference. Camera observations remain distinguishable from reported
facts and can be wrong even when their provenance and time are valid. Source time,
availability time and explicit supersession must remain distinct; late receipt
alone does not make an old report the latest operational state.

The original M2 visual-evidence study has separate data and training requirements:
labelled Unity renders, a real-photo check and the planned detector training.
Those commitments are not removed by saying that C01–C04 require no model
training. The existing image/no-image and viewpoint research remains a distinct
evaluation, with perception errors separated from language interpretation and
rule checking. No new paid API or model purchase is introduced by this queue.

## Correctness boundaries and records

C01 should cover receipt-time eligibility, correct run and aircraft identity,
fixed checkpoint cutoffs, duplicate action handling, stale-result rejection,
failure/retry and absence of scripted success after a model failure. Evidence
must distinguish what a test establishes from what remains untested. The intended
artifacts are `docs/CORRECTNESS_CONTRACT.md` and
`outputs/checkpoint1/correctness-acceptance.json`; they now contain the bounded completion evidence and explicit limitations.

C02 may establish that a formal claim follows from specified facts and rules.
That does not establish that the model extracted the learner's intended claim
correctly or that an observation/report is physically true. In particular,
unconfirmed departure authority is not proof that clearance was denied, and an
omitted answer component cannot receive credit merely because the report supplies
it. Separate claim support from coverage of the learner's full response so that
unparsed or unsupported clauses cannot silently disappear from assessment.

C03/C04 should specify the bounded number of entities, report versions and pending
actions, the treatment of time, and any fairness or termination assumptions.
Designed incidents may violate normal-operation constraints; their declared fault
transitions and subsequent closures/reports must be checked explicitly. A normal
collision-avoidance invariant cannot simultaneously forbid the intended incident
exercise. Trace comparison must identify the abstraction that maps actual runs to
formal states. Successful checking of a finite model is not proof of every
implementation execution, continuous flight physics or professional competence.

At completion, each unit needs identifiable source/configuration versions,
reproducible commands, outcomes, retained failures and an independent review.
Keep formal-property results, semantic answer evaluation and native usability
evidence separate. Do not change held-out protocols after observing their results;
do not reuse frozen M1 results as acceptance for new methods. Update this queue
and the ledger from evidence before describing a task as delivered.
