# Research plan: time-valid visual reasoning for AR airfield coordination

Status: proposed protocol. Local model installation and a synthetic-image
inference check have passed on Apple MPS. The first Unity replay implementation
compiles and passes deterministic checks. Android and physical tracking
validation are recorded separately in MILESTONE_1.md. Synthetic evaluation results are linked below; no training-effectiveness
findings or operational reliability claims are established. This plan extends the existing proposal's event-history
evaluation; it preserves the smartphone AR, moving-aircraft, and A-CDM scope.

## Motivation and distinctive question

The intended airfield stakeholder is a turnaround coordinator or ramp supervisor
reviewing the situation at an aircraft stand. Stand assignments, readiness
estimates, and movement plans change; a late report, superseded estimate, or
report for another rotation can change an otherwise plausible answer. The
proposed task is identifying the relevant aircraft/stand, reconstructing what
was known at a checkpoint, and inspecting the sources behind a changed plan.
Training and debrief are secondary applications of the same replay capability.

Handheld coordination has an industry precedent: Honeywell's GoDirect Ground
Handling brochure describes a mobile app for turnaround coordinators with
timestamped services; INFORM GS TeamWork provides mobile task coordination for
ground-handling frontline managers; SITA Mission Control supports ramp, gate,
cockpit, and operations collaboration on phones and other devices. These vendor
sources establish product/workflow precedent, not effectiveness of this AR app:

- https://aerospace.honeywell.com/content/dam/aerobt/en/documents/learn/services/maintenance-and-service-plans/brochures/C61-1519-000-001-GoDirect-bro.pdf
- https://www.inform-software.com/en/lp/gs-teamwork
- https://www.sita.aero/mission-control/

The proposed AR addition is spatially associated, source-aware explanation of
changing coordination information. Its benefit over an ordinary screen remains
a testable question. The prototype uses an original printed fictional stand
diagram as a reproducible surrogate; it has no real-airfield localization,
surveillance feed, aircraft identification, or movement authority. Field use
would require approved equipment/procedures, authoritative data integration,
identity/alignment validation, and appropriate stationary-use conditions. Those
are deployment requirements, not capabilities demonstrated by milestone one.

Research question: Does retrieval that respects information availability,
validity, source, and flight identity improve a vision-language model's answers
about a changing simulated airport scene compared with recent history or
retrieval without those constraints?

The separate video-reasoning study, as recalled from saved personal context,
focuses on learned visual-evidence retention and reasoning-rollout allocation
under compute limits, anchored by AVIS. The AR project's independent focus is
the validity of persistent event context and its use in interactive explanations.
This distinction is a research design choice, not a claim of literature novelty.
A focused related-work review is required before asserting a new method.

## Current integration versus research scope

The implemented pipeline now uses typed atomic claims, exact source/value/status
validation, receipt-time filtering, validity intervals, explicit supersession,
conflict handling, and aircraft/flight/rotation identity. Qwen selects claims;
deterministic templates render only validated selections. Raw model selections
and guard actions are evaluated separately. This is a constrained evidence
interface, not a general verifier for free-form generated explanations.

A reproducible synthetic pilot now covers 12 scenario families and 36 questions,
with 8 development and 4 author-known held-out composition families. Its protocol,
raw results, deterministic baseline, and limitations are in
`outputs/reasoning_v1/REPORT.md`. This pilot is separate from the larger course
collection planned below; do not describe the planned 144 events/96 questions
as completed. The fixture images are non-diagnostic controls, not a visual test.
The same developer authored data and labels; independent review is outstanding.

A subsequent frozen evaluation uses 32 fresh questions in eight new composition
families authored by a separate agent. The original prompt scored 9/32; the
revised predicate-selection method scored 31/32; the deterministic baseline
scored 32/32. Missing-evidence cases were 12/12 and change histories 8/8 for the
new method. One unrelated-property selection was retained as an error and
withheld. See `outputs/reasoning_v2/REPORT.md` and its raw records. This is a
hybrid structured-query result: deterministic temporal labels and provenance
projection reduce the learned task; it does not establish a need for Qwen over
the baseline. The schematic-image condition scored 10/32 and establishes no
visual reasoning benefit. A genuinely visual task is required next.

Multi-frame motion reasoning, visually necessary questions, learned retrieval,
linked rotations over days, and professional UI evaluation are not yet complete.
The deterministic baseline is essential: if it solves the supported query types,
we must not claim Qwen adds value merely because the interface uses it.

## Planned full research implementation

- Unity supplies object identity, geometry, occupancy intervals, and replay time.
- Append-only events record episode, flight instance, aircraft, property/value,
  event time, receipt time, source role, validity interval, and supersession.
- At checkpoint t, evidence availability requires receipt_time <= t. Applicability,
  validity, identity, and explicit supersession determine which values are
  current. Earlier values remain accessible as labeled historical evidence.
- Distinguish reports, confirmed scenario states, estimates, and future plans.
  An estimate or A-CDM target time does not authorize movement.
- Qwen receives selected images, computed facts, and eligible records and returns
  an answer, supporting IDs, and an explicit insufficient-evidence outcome when
  needed. Deterministic checks verify IDs, eligible timestamps, and numeric
  claims. A manually audited subset assesses whether cited evidence actually
  supports the explanation; citation existence alone is insufficient.
- Geometry and collision-proxy calculations remain deterministic. The model
  explains those calculations and identifies relevant evidence.

## Data stages and leakage controls

The course dataset remains planned: 12 cases, 144 event records, 60 visual
checkpoints, and 96 questions. Eight complete cases support development and
four are held out. Preserve all related frames, paraphrases, and timing variants
of a scenario family in one partition. Author and independently review answer
labels before evaluation. This small split supports feasibility, with limited
generalization evidence.

Cover stand reassignment, late arrival of a report, superseded readiness
estimates, missing evidence, irrelevant intervening updates, movement timing,
and wrong-flight/rotation identity. Include answerable and insufficient-evidence
questions. Freeze test scenarios, labels, model revision, prompts, and retrieval
settings before the final run. Never tune on held-out answers.

For a research extension, add independently authored scenario families and
linked rotations across simulated days. Set the expanded sample and test plan
after examining development-pilot variability and authoring effort, then freeze
them before the research evaluation. Measure generalization to unseen layouts
and update patterns. More parameter variations of one script do not establish
independent scenario diversity. Longitudinal event memory and longitudinal
trainee learning are separate questions.

## Controlled comparisons

Use the same model revision, questions, visual checkpoints, calculated geometry,
decoding settings, and output schema. Compare:

0. A deterministic event-state engine with authored answer templates for the
   question types it supports. Report its coverage as well as accuracy; this
   tests whether the generative model adds value beyond conventional software.
1. Current scene/facts, without earlier history.
2. Current scene/facts plus a fixed recent-event window.
3. Current scene/facts plus full eligible history, within a documented limit.
4. Current scene/facts plus relevance-based retrieval without explicit temporal
   and identity validation.
5. Current scene/facts plus relevance retrieval with availability, validity,
   supersession, source, and flight-identity checks.

For condition 4, access only the locally stored episode records that have
arrived by the live/replay clock; stale and wrong-rotation retrieval are the
intended tests. Future-information exposure is assessed separately through
explicit as-of checkpoint tests, rather than deliberately giving a baseline
the answer from future observations.

Compare conditions 4 and 5 under matched retrieval token limits. Record actual
input/output tokens, latency, and evidence counts for every condition. Full
history is a separate evidence-budget baseline, not an equal-cost comparison.
An oracle-evidence condition can diagnose retrieval versus answer-generation
failures. A with-images/without-images ablation tests the contribution of visual
input. Motion questions must include changes requiring ordered checkpoints;
single-image position descriptions alone do not test temporal perception.

Some geometry-derived questions can already be solved from structured facts.
Treat that as an explicit structured-data baseline. For dedicated visual tests,
withhold answer-bearing pose/geometry fields from model inputs and retain them
only as scoring ground truth. Document that separate input condition. If images
provide no measurable benefit in the combined condition, report that result
rather than describing the pipeline as demonstrated visual reasoning.

## Measures and interpretation

Primary outcomes: structured answer correctness and temporally invalid answer
rate on prespecified time/identity-sensitive questions. Invalid answers assert
unavailable future information as known, superseded information as current, or
facts from another flight instance as applicable. Report each error type and
its denominator. Also report evidence support, appropriate insufficient-evidence
responses, latency, tokens, and failures.

Compare answers on the same held-out questions. Questions within one scenario
are correlated: report results by scenario and condition, and use scenario-level
resampling for uncertainty when there are enough independent cases. Four test
cases yield imprecise estimates and do not support broad superiority claims.
Log failed runs as failures rather than silently excluding them.

Evaluate interface effects separately with a counterbalanced AR-versus-2D
pilot using identical scenarios, facts, and feedback. Peer usability observations
support interface feasibility; professional competence, retention over weeks,
and accident reduction require appropriate participants and separate studies.

## Milestones and evidence for a portfolio

1. AR scene, scripted motion, clock, and reproducible event capture. Verify local
   Qwen inference with a synthetic image; keep this smoke test separate from
   scenario evaluation.
2. As-of replay, versioned event memory, deterministic geometry checks, and a
   development-only end-to-end reasoning example with checked evidence IDs.
3. Frozen held-out evaluation, ablations, error analysis, and a reproducible
   report. Follow with the bounded interface pilot if feasible.

Keep package/model revisions, scenario provenance and splits, prompts, raw
responses, scoring rules, and logs. Share original assets and scenarios only
with appropriate licenses. Retain the upstream Qwen Research License; do not
redistribute weights as ordinary project source.

A later CV entry should name the implemented system and the measured result,
including its simulated setting and comparison. Until those exist, describe it
as an in-progress AR prototype and evaluation plan. Publication potential and
professional safety value remain questions to investigate.
