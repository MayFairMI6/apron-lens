# ApronLens: shared context across AR conversations

This document records the earlier research proposal and candidate experiments.
Current delivery status is in `docs/course/CHECKPOINT1_CURRENT.md`; completed M1
results are in `outputs/m1_ar_context/REPORT.md`; the active research milestones
are in `docs/AR_SCOPE.md`. Hosted-model candidates and pricing below are historical
planning notes, not current availability or newly verified recommendations.

## Research question and application

**How should an AR assistant maintain and revise shared context when user
corrections and external event updates arrive between conversational turns?**

ApronLens investigates this question through a smartphone AR environment with
moving aircraft, flight rotations and changing surface-movement reports.
Aviation supplies the application context; the research focus is the assistant's
handling of spatial references, conversational corrections and time-valid evidence.

The current application stakeholders are controller and pilot trainees practising
situational awareness. Controllers follow aircraft identity, movement reports,
restrictions and handovers; pilots review the selected flight’s reported route,
restrictions and changes. The shared research question remains how the assistant
revises spatial and temporal context as evidence arrives. Training and debrief
are now the primary application direction. Turnaround and ground-handling trainees
remain a third audience with a service-coordination emphasis, using the same
scenario and evidence engine. The current scene supplies surface
movements and report-led runway events, not operational clearance issuance,
separation assurance, cockpit procedures or flight dynamics. Professional training
usefulness requires stakeholder validation. Earlier turnaround-focused evidence
is preserved and is not relabelled as controller or pilot validation.

The retained turnaround track has an earlier mobile-coordination workflow precedent: Honeywell's
[GoDirect Ground Handling brochure](https://aerospace.honeywell.com/content/dam/aerobt/en/documents/learn/services/maintenance-and-service-plans/brochures/C61-1519-000-001-GoDirect-bro.pdf),
[INFORM GS TeamWork](https://www.inform-software.com/en/lp/gs-teamwork), and
[SITA Mission Control](https://www.sita.aero/mission-control/) describe mobile
coordination. These vendor sources motivate a plausible device/workflow fit;
they do not establish the effectiveness of ApronLens or the value of AR.

The current environment is an original printed fictional airfield board. It
provides repeatable object motion and timestamped reports. Real-airfield
localization, operational A-CDM feeds and professional deployment are outside
the demonstrated capabilities. A-CDM-inspired estimates such as TOBT remain
estimates rather than movement clearance. Accident or collision reduction
requires separate evidence and is not an outcome established by this project.

## Implemented foundation and proposed capabilities

| Component | Current evidence | Proposed extension |
|---|---|---|
| Spatial interface | Android Unity/Vuforia app; scripted aircraft; explicit selection; phone-layout simulation | Natural-language references linked to the current AR view and explicit pointing/selection |
| Event context | Receipt-time filtering, event/validity times, supersession, conflicts and flight identity | Reconcile arriving reports with previously discussed claims |
| Model reasoning | Local Qwen predicate selection with source/value projection and a guard | Follow-up dialogue, clarification and revision of shared references |
| Memory | Received reports and replay checkpoints | Versioned user intent, corrections and shared context across turns; later across resumed sessions |
| Evaluation | Frozen synthetic structured-query comparisons and app checks | Dialogue-family tests, visually necessary tasks and an interface pilot |
| Hosted models | No hosted provider connected | Provider adapters and controlled model/effort/cache comparisons |

The released app has no conversational input or shared-dialogue memory. Its
current query types are latest report, current facts and change history. The
[implementation record](IMPLEMENTATION.md) and [connection guide](QWEN_CONNECTION.md)
describe what is available today. Proposed capabilities below are research plans,
not results from the current APK.

## Literature and the proposed distinction

[Seeing Eye to Eye / Eye2Eye](https://doi.org/10.1145/3772318.3791059)
(CHI 2026; [author preprint](https://arxiv.org/abs/2603.12701)) combines shared
attention, revisable memory and feedback for human–AI collaboration through a
first-person perspective. It motivates maintaining and correcting common ground.
ApronLens would study the narrower problem of reconciling conversational
corrections with independently arriving, source-backed event updates. The phone
prototype can use explicit selection/pointing; eye tracking is not implemented.

[Pro²Assist](https://doi.org/10.1145/3832022) (IMWUT 2026;
[publication record](https://research.cuhk.edu.hk/en/publications/prosup2supassist-continuous-step-aware-proactive-assistance-with-/))
tracks procedural context and provides assistance as tasks evolve. It motivates
a later study of when to notify users that new evidence invalidates an earlier
answer. Timing would be evaluated after context reconciliation works reliably.

[ALCE](https://aclanthology.org/2023.emnlp-main.398/) motivates evaluating citation
support and coverage, while [FActScore](https://aclanthology.org/2023.emnlp-main.741/)
motivates examining factual support at the atomic-claim level. The current typed
claim checks are inspired by that distinction; they are not reproductions of
those benchmarks or general natural-language entailment verification.

These papers establish relevant approaches, not novelty for the proposed method.
A fuller comparison of conversational AR, temporal memory and source reconciliation
is required before claiming an original contribution. A generic chatbot added to
an AR screen would not establish the research value of the proposed context model.

## Example interaction and context rules

1. The user selects an aircraft and asks, “Why is this one waiting?”
2. The user clarifies, “I mean its next rotation.” The assistant updates the
   intended flight instance and retains the correction in its dialogue state.
3. A delayed report arrives. The assistant checks when the event occurred,
   when it became known, its validity and whether it replaces an earlier report.
4. The user asks, “Does that change what you said?” The assistant revises or
   maintains its answer and identifies the relevant source and time boundary.

A proposed context record separates:

- **User intent:** the intended aircraft/rotation, question, selected object and
  corrections, each associated with its turn and scope.
- **External evidence:** immutable source records with aircraft and flight IDs,
  event time, receipt time, validity and supersession links.
- **Assistant interpretation:** a revisable reference and answer linked to the
  user turns, external evidence and checkpoint that supported it.

A user correction changes intended reference; it does not establish that a service
is complete or overwrite an external report. New reports can invalidate a prior
interpretation without erasing its provenance. A change of flight, replay time
or tracking state must trigger revalidation of the context it affects.

The aircraft entity and flight instance remain distinct: the same physical
object can appear in different rotations. Ambiguous references require a concise
clarification or explicit selection. The interface should show current focus,
what changed and source access, with details available on demand rather than
covering the spatial view with conversation text.

## Primary experimental design

Compare the same scenario/dialogue families using:

1. **Stateless assistant:** current legitimate scene context and latest user turn.
2. **Conversation-history assistant:** eligible prior turns and reports, with a
   documented context limit and no explicit shared-context update model.
3. **Explicit context-management assistant:** versioned reference/intent state,
   scoped user corrections and temporal evidence retrieval.
4. **Structured interface baseline:** explicit aircraft/rotation selection and
   deterministic report lookup, with its coverage and interaction effort recorded.

Use the same fixed model, output contract and available observations for the
initial model comparisons. Match retrieval/input budgets where feasible, report
actual budgets for every condition, and avoid giving a method answer-bearing
reference IDs unavailable to its comparators. An oracle-reference condition is a
separately labeled diagnostic for reference resolution versus answer generation.

Initial scenario families should combine ambiguous object references, corrected
rotations, delayed reports, cancelled plans, conflicting reports, missing evidence,
tracking loss and scene changes between turns. Include cases where the proper
response is a clarification or unknown, and cases where new evidence does not
change the answer. Keep every turn, paraphrase and visual variant of one family
in the same data split.

The first comparison concerns context across turns within a session. A separate
longitudinal study would link rotations or resume sessions after interruptions,
testing which references and evidence should persist and which must expire.
This is distinct from measuring a trainee's learning or retention over weeks.

## Data, visual grounding and leakage controls

The existing structured-query suites remain preserved historical evidence. The
32 previously fresh questions have been observed; they cannot serve as an
untouched test set for the new dialogue method.

The proposed dialogue collection needs new families, independently authored
reference/answer labels, explicit update timelines and domain review where
aviation interpretation matters. Each example should record the AR observation,
selection/pointing cue, user turn, eligible reports, intended referent, expected
context revision, source support and permissible abstention. Set collection size
and test allocation after a development pilot, before opening the new test set.

Use scripted Unity scenes for controlled timing and geometry. For a visually
necessary subset, remove answer-bearing object/pose IDs from model inputs and
retain them only for scoring. Compare with and without images using the same
remaining inputs. Explicit hit-testing or structured geometry may already solve
some references; retain those as conventional baselines. A schematic that cannot
change the answer is a negative control, not a visual-reasoning benchmark.

Freeze the data, prompts, retrieval/state-update rules, model configuration and
scoring before the new evaluation. Preserve failures, incomplete responses and
interruptions. Log receipt-time eligibility and prevent later turns/reports from
leaking into earlier checkpoints. Test generalization across new update patterns
and layouts rather than relying only on parameter changes to one script.

## Measures and interpretation

Primary measures are correct reference/rotation resolution, retention of valid
user corrections, stale-context errors and task-answer correctness. Also record
unsupported memory updates, source support, clarification behavior, appropriate
unknowns and whether the correct answer revision occurs after an external update.
Score raw model answers, context-state updates, guard withholding and deterministic
baseline performance separately. A rejected answer is not a correct raw answer.

Report results by independent scenario family as well as by turn. Questions
within a family are correlated; use family-level uncertainty estimates only with
an adequate number of families. Record latency, tokens and failures alongside
quality rather than excluding unsuccessful runs from performance summaries.

A counterbalanced interface pilot should compare conversational AR with a 2D
structured view using equivalent tasks and evidence. Assess task success, time,
correction recovery, clarification burden and workload. General-participant
results support interaction feasibility; industry effectiveness needs relevant
stakeholders and appropriate tasks. AR's benefit and a model's benefit over the
structured interface are empirical questions.

## Model and API comparisons

Hosted API adapters are proposed; the implementation currently runs local Qwen.
The following are candidates for evaluation, not a ranking demonstrated on
ApronLens. Provider documentation was checked on 28 October 2026; confirm account
access, current model IDs and configuration support when implementing an adapter.

| Candidate | Proposed role | Documentation |
|---|---|---|
| Local Qwen2.5-VL-3B | Reproducible local baseline; retain the current structured selector | [Pinned model](config/model-manifest.json) |
| OpenAI Responses / GPT-6 Astra | Selective high-capability reference and difficult conversational/visual turns | [Model](https://developers.openai.com/api/docs/models/gpt-6-astra) |
| Lower-cost OpenAI model | Candidate for routine turns after quality/latency measurement | [Model catalog](https://developers.openai.com/api/docs/models) |
| Claude Sonnet 5.5 | Cross-provider text/image dialogue comparison | [Models](https://platform.claude.com/docs/en/models/overview) |
| DeepSeek Flash | Additional text/image comparison and cost measurement | [Vision](https://api-docs.deepseek.com/guides/vision/), [pricing](https://api-docs.deepseek.com/quick_start/pricing/) |
| Gemini | Optional comparison when actual video/timestamp understanding is necessary | [Video understanding](https://ai.google.dev/gemini-api/docs/video-understanding) |

Astra's listed standard text rates are $10 per million uncached input tokens
and $50 per million output tokens. An illustrative 2,000-input/500-billed-output
turn costs $0.045 before caching or other charges; 1,000 such turns cost $45.
This is arithmetic for the stated usage, not a measured app bill. Use selective
reference runs and an explicitly agreed budget rather than assuming Astra is
appropriate for every interactive turn. Higher effort, longer histories and
additional image/tool usage require metered end-to-end cost measurement.

Run the initial memory comparison with one fixed model. Only then compare fixed
low/high inference budgets with adaptive model or effort selection. Treat provider
switching and within-model effort changes as different interventions. Keep the
application's semantic context and evidence ledger outside provider-specific
conversation state; record how each adapter reconstructs equivalent inputs.

Do not assume effort changes always destroy cached context. OpenAI documents
append-only configuration updates that preserve earlier prefixes on supported
models; Claude documents model-dependent cache-preserving per-message effort
updates alongside invalidation from request-level changes. Use the documented
path for each model and record the exact configuration. Compaction, changes to
prompt prefixes, model choice and cache thresholds need separate controls.
Sources: [OpenAI caching](https://developers.openai.com/api/docs/guides/prompt-caching)
and [Claude caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching).

Measure cached reads/writes, total billed tokens, reasoning usage where exposed,
first-response and completion latency, compaction/reconstruction overhead and
quality before and after a correction. Report actual local compute for Qwen and
verified provider billing for hosted models. Raw reasoning traces and controls
are not interchangeable across providers. Keep the output/evidence contract
consistent and record unsupported features rather than silently treating them
as equivalent. API credentials belong on the backend and in dedicated evaluation
secrets, never in the APK or repository. No paid API calls have been made for
this scope update.

## Later proactive assistance

Once context reconciliation has been evaluated, study whether a concise notice
is useful when a newly received report changes an earlier answer. Compare
user-triggered review, a simple event-rule notice and a learned timing policy.
Measure useful notices, unnecessary interruptions, missed update opportunities
and recovery time. The proposed notice concerns explanation/evidence changes;
it does not issue real-airfield movement instructions.

## Preserved results and current limits

The first synthetic suite has 36 questions across eight development and four
author-known held-out families. Its [frozen report](outputs/reasoning_v1/REPORT.md)
preserves the original conditions and development history.

The later [paired evaluation](outputs/reasoning_v2/REPORT.md) has 32 questions in
eight separately authored families. The original prompt scored 9/32, the revised
Qwen hybrid 31/32 and the separate deterministic baseline 32/32. The revised
pipeline scored 12/12 missing-evidence cases and 8/8 change histories; its extra
unrelated-property claim was withheld. Two missing-evidence successes used
empty-context logic without inference. The image negative control scored 10/32.

These are structured-query results with deterministic temporal labels and
provenance projection. They do not demonstrate conversational memory, learned
state inference, visual reasoning, or superiority to the baseline. The legacy
latest-event wording differs from the corrected policy for a tied receipt time.
See the [audit notes](outputs/reasoning_v2/audit-notes.json). Separate-agent data
authorship is not external expert validation, and family-level sample size is
small. Source snapshots, raw responses and dataset hashes remain preserved.

The current implementation includes Android packaging and simulated S24 layout
checks; physical phone validation remains pending. Broader claims require new
evidence for dialogue, visual grounding, interaction utility and stakeholder fit.
The project's contribution should be stated through its implemented mechanisms
and measured comparisons, with proposed features labeled as plans.
