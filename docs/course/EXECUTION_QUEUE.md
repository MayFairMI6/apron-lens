# AirfieldLens execution queue

The owner has adopted the correctness work discussed after the formal-methods
brainstorm. This queue records execution order, dependencies and completion gates;
adding a task does not mean it has been implemented or verified. The decision
record is [the milestone ledger](MILESTONE_LEDGER.md). Work remains confined to
AirfieldLens, with the existing free-assets constraint and local model.

For Checkpoint 2, the primary product is a **surface incident replay tool for
tower controllers and supervisors**. Its purpose is to reconstruct what was
visible, reported, and unresolved at a selected point in a recorded or synthetic
scenario. The A380 runway-occupied go-around is the lead case. The replay uses
a single controller workspace for controllers and supervisors. Pilot and
Stand/Turnaround roles do not appear as modes in this workspace. Keep the existing
typed lessons available for course acceptance and regression checks. Their
recordings, frozen evaluations, and assessment contracts remain in the project.

## Why this replay: an occupied runway is an existing airfield safety problem

A runway that is still occupied when another aircraft is about to use it is a
long-standing surface safety risk. The protection is a timely go-around or a
cancelled clearance, and both depend on who knew what, and when. The two lead
cases are informed by documented situations at Heathrow. They do not
reconstruct them:

- **Delayed runway vacation leading to a go-around.** Heathrow's 2024 annual
  operational report discusses delayed vacation as a go-around context
  ([ANATMT Annual Report 2024, section 3.5](https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/local-community/noise/reports-and-statistics/reports/anatmt/Heathrow_ANATMT_Annual_Report_2024.pdf)).
  The A380 case shows this: TRN102 has not vacated Runway 09R and TRN101 goes around.
- **Runway incursion.** On 26 February 2019 a disorientated maintenance-vehicle
  driver entered a Heathrow runway and a takeoff clearance was cancelled before
  the roll began ([AAIB: D-AEAD](https://www.gov.uk/aaib-reports/aaib-investigation-to-airbus-a300b4-622r-f-d-aead)).
  The existing maintenance-vehicle case stays in the inventory for this reason.

After such an event, a controller or supervisor reviewing it faces three
practical difficulties, and each replay feature answers one of them:

| Difficulty in a review | What the replay does |
|---|---|
| Hindsight: later reports colour the reading of earlier moments. | One source cutoff. Reports received later are hidden until their receipt time, in the list and in the assistant's context. |
| When something happened is confused with when it became known. | Every report shows its event time and its receipt time separately, with its source. |
| Unresolved items are lost at handover (here, whether another approach is confirmed). | A short handoff note tied to the run and cutoff, and an assistant that reports what is still unconfirmed and does not fill the gap. |

This follows the situation-awareness view that an operator needs an accurate,
current picture of a changing situation (Endsley 1995, cited in
[related work](../RELATED_WORK_DRAFT.md)). The replay is a review and training
aid over synthetic scenarios. It makes no claim to reduce incursions or
go-arounds, and it has no operational authority.

## Controller replay implementation

1. **Lead with the A380 go-around.** Open the existing four-aircraft replay with
   the A380 and the aircraft occupying Runway 09R identified. Provide a source-time
   scrubber, play/pause and event jumps for the runway-occupancy report, go-around,
   climb-away, and later report that another approach remains unconfirmed. A
   controller can tap either aircraft or select it from the timeline, inspect
   the source for a claim, and record a short handoff summary of unresolved
   items. Reuse the existing aircraft assets, authored motion, report history,
   and timeline clock. Verify each event jump against the original source
   cutoffs and show the two aircraft separately during the review.
2. **Use one evidence cutoff across the replay.** Give playback an independent
   read-only review session over immutable scenario data. Reuse source snapshots
   and evidence rules from the driver. Keep seeks separate from the live lesson
   clock. Pass the run ID, selected
   aircraft and flight identity, and source cutoff through the existing
   driver/evidence paths. On a seek or selection change, refresh the scene,
   report list, and assistant context together. Discard stale responses for the
   previous view. On a backward seek, remove later-turn memory from the
   assistant's context. Preserve event time and receipt time separately and show
   camera observations, airborne observations, and airport reports with their
   own source and age. The assistant summarizes eligible evidence and reports
   uncertainty. Controller notes are annotations and the replay is read-only
   with respect to airport clearances, routing, reservations, and traffic.
3. **Retain the 787-8 Bluebird handoff.** Compare the pinned synthetic
   two-contact trace with the existing 787 priority-landing replay at matched
   cutoffs. Preserve TRN101 identity, the second track, the authored
   30-second handoff gap, and the subsequent hydraulic concern, landing,
   inspection, and unconfirmed runway release. The offline comparison is
   recorded. The first live answer at the handoff failed the output schema.
   Keep that failure as a development control and finish positive and negative
   handoff checks in the Simulator and the model before acceptance.
   [Trace and offline results](../../outputs/bluebird-handoff/README.md)
4. **Use Stand B for the AR evidence comparison.** Reuse the approved occupied
   and cleared Stand B design, existing apron and fleet assets, and the source
   clock. The moving fuel-transfer vehicle, explicit tracking loss, look-away
   and return, and physical occlusion supply distinct conditions. Verify
   synchronized RGB and simulated metric depth, the visible footprint at 92
   and 95 seconds, the release received at 150 seconds, and TRN103 movement
   starting at 158 seconds. Keep the 60-, 120-, and 180-second typed check
   sequence, withheld/retry path, and debrief available through the course flow.
5. **Review and acceptance on the iPhone Pro Simulator.** Show an image preview
   of the A380 timeline and source inspection before implementing the new
   controller screens and obtain approval. Keep the aircraft and runway
   visible behind concise controls. Test portrait and landscape, forward and
   backward seeks, aircraft switching, stale replies, late and corrected
   reports, and handoff gaps. Verify the A380, 787, and Stand B journeys, then
   cover the other assigned cases. Present the A380 first in the narrated
   demonstration, followed by the 787 handoff. Keep Stand B in the engineering
   and detector evidence. Deliver the
   Simulator build, the narrated demonstration with each contribution named,
   and the one-page achievement reflection in Downloads. Link the exact build source and verified evidence from GitHub.

**Status at 17 November 2026 (evidence in ledger ML-054 to ML-056).** The
replay service and the controller screens are built. The A380 and 787 handoff
journeys ran in the iPhone 18 Pro Simulator in both orientations with real
model answers; ML-055 and ML-056 list each check and what is still open. Camera
observations are stored and cut off with the view but do not reach the
assistant's prompt. Stand B has not been run through the replay. To regenerate
or add a scenario, see the [driver guide](../SCENARIO_DRIVER_GUIDE.md).

Treat this sequence as the new Checkpoint 2 presentation order. The units below
retain the earlier engineering, scenario, and research dependencies. The
integrated Checkpoint 3 evaluation and controlled size/demand comparison remain
assigned, alongside integrated client replay and runner parity, the device and
connection checks, operating-day and solar-cycle work, and the reproducible
final report.

## Engineering and research dependencies

| Order | Unit | Milestone and status | Deliverable | Exit gate |
|---|---|---|---|---|
| 1 | F03/T01 — typed lessons | M1; bounded qualitative prototype verified | Exact v2 restored after the second bounded revision failed review. One full typed fog run plus targeted original-lesson native checks; failures retained. | Preserve failed requests; verify learner interpretation, report eligibility, typing, feedback, retry, stale responses, orientations and debrief. Existing MCQ or positioned API checks do not substitute for native typed-flow acceptance. |
| 2 | C01 — correctness contracts and acceptance record | M1; complete within stated limits | A concise contract mapping each implemented safeguard to code, checks, failures and limits. Source hashes, independent checks, semantic failures and native evidence are consolidated. | Each claimed property has supporting evidence or an explicit unresolved gap. Distinguish structural validation, semantic development checks and native execution. No mathematical-proof or validated-grading claim. |
| 3 | M1 publication and submission preparation | M1; outstanding work | Publish the accepted typed increment with matching demo/script/handoff; finish the separate submission requirements. | Preserve Person 1 audio and historical footage. Complete Person 2 contribution, final one-page reflection review and resolution of the smartphone-evidence requirement. These are distinct from feature acceptance. |
| 4a | C02 — structured claim and evidence checker | M2; queued | A bounded typed-claim vocabulary, eligible-evidence rules, deterministic checker and source/rule trace. The existing model interprets learner wording and proposes claims. Integrate with report/camera evidence and the already-planned validation study. | Demonstrate supported, contradicted, unknown and conflicting cases; check subject/time/provenance and correction handling; measure semantic extraction errors separately. Preserve the original visual-evidence experiment. |
| 4b | C03 — bounded scenario-state specification | M2; queued alongside Q01 design | A small TLA+ specification of report availability, lesson/review transitions and runway/stand reservations, with explicit abstraction and fault/incident transitions. | Define normal/accelerated correspondence at matched source times, specified action schedules and seeds; document safety and progress assumptions. Review representative traces against the implementation. This is a specification deliverable, not a completed proof. |
| 4c | Bluebird inbound handoff for the 787-8 | M2; offline replay checked | A pinned Bluebird synthetic two-aircraft trace followed by the authored 787-8 priority-landing replay, compared at matched cutoffs with the authored replay alone. | Retain the trace and comparison results. Check identity, cutoff eligibility, the handoff gap, and unchanged airport evidence. Verify phone presentation and assistant behavior separately before claiming either. |
| 5 | C04 — model checking and comparative evaluation | M3; queued after C02/C03 stabilise | Check the bounded driver/evidence-state model with TLC; record counterexamples and implementation-trace correspondence. Compare direct model review, the existing structural/citation validator and the structured checker on a separately frozen evaluation set. | Publish checked configurations, assumptions, specification/tool versions, outcomes and limitations. Report unsupported feedback, valid answers rejected, uncertainty/coverage and latency; preserve failures whether or not the checker improves results. |

C02 and C03 are supporting parts of the existing M2 work, not separate training
courses. Their design should share the evidence identities and time semantics.
The four existing AMV Lab fleet models and Unity landing gear remain in use.
Their cases are the A380-800 runway-occupied go-around, 787-8 hydraulic concern
and priority landing, A320-200 Sharklet bird hold, dispersal, inspection and
release, and 737-800 rejected takeoff after a reported airspeed concern. Keep
the A320 wildlife return and E01 737 single-engine return with landing,
inspection, and separately reported recovery status. Keep the existing
aircraft–vehicle contact, stand engine fire, damaging landing, maintenance
vehicle runway incursion, water landing, and fog cases. The
[scenario register](TRAINING_SCENARIO_REGISTER.md) remains the full inventory.
Checkpoint 2 retains P01/P07 and fuel interruption, P03/P06/P09 and Q01, and P05
plus the protected-boundary, callsign/readback, conflicting-stand, and
disabled-aircraft recovery variants. Checkpoint 3 retains P02 pushback and
wingtip conflict, P08 water-incident handover, and the two-engine and structural
damage cases. Use the [fleet asset record](../FLEET_DEMONSTRATION.md) for reuse
and attribution.

Checkpoint 2 retains the Google MediaPipe exercise and detector fine-tuning on
Unity captures, the independently labeled real apron photo check for both the
detector and vision-language model, and the
Gemini structured-output exercise. Keep reports alone, reports with RGB
detections, and reports with RGB detections and simulated depth at matched
cutoffs. Compare current frames with deterministic tracked history within the
visual arms. Keep the per-aircraft last-seen state, source-backed change
notices after a look-away, and viewpoint-relative references. Compare one
bounded validator-guided repair with zero retries. Preserve the exposed
detector pilot and evaluate a revised
candidate on a fresh test split. Track precision, recall, identity changes,
uncertainty, unsupported authority claims, and latency. Use the same
independently frozen conditions for the incident replay questions. Retain the
original image/no-image and viewpoint comparisons, deterministic primary
scoring, calibrated blind secondary review, and a reproducible report of
failures, coverage, and latency.

B06 retains the local quantized Qwen3.5-27B versus frozen Qwen3.5-9B comparison,
its original promotion gates, and the prior LoRA and deterministic baselines.
The 27B candidate produced six structurally valid outputs and preserved
meaning in four controls. The six-control semantic gate therefore failed.
Preserve those results and keep the twelve contrasts sealed until an eligible
candidate passes the controls. The [B06 protocol](STRONGER_MODEL_RESEARCH.md)
defines the remaining gates.
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


## Adopted current-checkpoint addition: B01 / #70

The user approved a bounded AI-assistant comparison on 3 November 2026. Execute
18 authored questions across three scenarios in lexical-retrieval-plus-selector,
selector-without-history and selector-with-history configurations. Preserve all
real responses, failures and costs; publish the protocol and descriptive results.
This is not learner grading or a new held-out benchmark. No training data, model
training or graph database is required for this bounded comparison. See
[protocol](ASSISTANT_COMPARISON.md) and [task #70](https://github.com/MayFairMI6/apron-lens/issues/70).
Approved videos and the app remain unchanged. The completed run has 54 real responses: lexical/history18/18, selector without
history14/18, selector with history17/18. Independent review records acceptance
in the milestone ledger. #30/#31/#32 remain separate submission gates.
