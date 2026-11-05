# R11 redesign stress v1: exposed development fixture

This is openly tunable development material. It is not held out, reserve material, a semantic acceptance set, or evidence of generalisation. The coordinator and implementer may inspect every case and tune against it. No model calls were made during authoring.

The fixture contains 16 cases: 12 fully valid cases (all expected statuses `met`) and four invalid or partial contrasts. The 12 valid cases cover all twelve exposed lesson checkpoints. Learner responses range up to 595 characters, within the frozen 1,200-character input limit. Two deliberately longer answers repeat and qualify the relevant distinction across several sentences, testing whether a complete supported answer survives clause-level review.

Payload provenance

Every payload is copied from the exposed `development-v1.json` case named by `sourceCaseIndex`; only `learnerResponse` changes. Reports, receipt cutoffs, episode IDs, questions, aircraft IDs, criteria and evidence eligibility remain identical. The source fixture SHA-256 is `e6ee0e234919c56276e199419f35627aedd6528702f3003c386d57b25654f397`. The exposed `fresh-v1.json` and `fresh-v2.json` were read for public conventions, but no payload is drawn from them. The frozen R11 contract and `backend/training_assessment.py` supplied status and grounding conventions. No fresh-v3 file, candidate implementation, raw model output or acceptance report was accessed.

The author assigned expected statuses from the received reports and criterion meanings, without running a classifier or using candidate predictions. These are agent-authored development expectations, not an independent evaluation reserve. Feed only each case’s `payload` to a model; all other fields are runner labels or provenance.

Case rationale

| Index | Checkpoint | Stress | Expected statuses in criterion order | Rationale |
| --- | --- | --- | --- | --- |
| 0 | surface_conflict/check-1 | paraphrase | met, met, met | Names the held flight and reported route obstruction without adding a cause or permission. |
| 1 | surface_conflict/check-2 | self_correction, history_then_update | met, met, met | The opening reading is explicitly withdrawn. The final assertion links the released hold to the cleared vehicle. |
| 2 | surface_conflict/check-3 | grounded_uncertainty, paraphrase | met, met, met | Unknown permission is expressed as a report-scope unknown, rather than an asserted denial. |
| 3 | late_arrival/check-1 | source_attribution, resource_awaited | met, met, met | Correct attribution follows the source field. Awaiting B denotes the resource sought, not current occupancy. |
| 4 | late_arrival/check-2 | long_answer, grounded_uncertainty | met, met, met | Every clause restates the distinction between an intended reposition and an absent availability confirmation; no new event is asserted. |
| 5 | late_arrival/check-3 | source_attribution, paraphrase | met, met, met | Both stand availability and the linked ground-hold release are stated; the source attribution is supported. |
| 6 | late_baggage/check-1 | paraphrase, separate_services | met, met, met | Baggage delay and completed fuel are correctly separated without asserting overall readiness. |
| 7 | late_baggage/check-2 | history_then_update, latest_value | met, met, met | The superseded and latest estimates have unambiguous temporal roles; authority remains unconfirmed. |
| 8 | late_baggage/check-3 | long_answer, grounded_uncertainty | met, met, met | Report-scope uncertainty is explicit. Denial and failed readiness are disclaimed rather than asserted. |
| 9 | fog_restrictions/check-1 | paraphrase, grounded_uncertainty | met, met, met | Both restrictions and the retained hold are included, without converting absent clearance into denial. |
| 10 | fog_restrictions/check-2 | paraphrase, partial_cancellation | met, met, met | Cancellation is restricted to procedures; safeguarding and flight restrictions remain. |
| 11 | fog_restrictions/check-3 | self_correction, source_attribution, history_then_update | met, met, met | The pending state is identified as earlier and superseded. Confirmation source, parked state and unknown authority are correct. |
| 12 | late_baggage/check-2 | omission | met, missing, met | States the latest estimate but omits whether that estimate establishes clearance or readiness. Grounding judges only claims made. |
| 13 | late_arrival/check-1 | wrong_actor | met, contradicted, contradicted | The waiting flight and resource are correct, but the occupant is explicitly changed from reported TRN102 to TRN101. |
| 14 | late_baggage/check-2 | wrong_latest_value | contradicted, met, contradicted | The stale value is explicitly called latest. The separate estimate-versus-authority distinction remains correct. |
| 15 | late_arrival/check-3 | wrong_source_attribution | met, met, contradicted | Core availability and release are correct, but ground handling is substituted for the actual stand-planning source. |

Label boundaries and limitations

Explicit self-corrections are read as corrections: an earlier reading that is clearly withdrawn is not a continuing contradictory assertion. Statements that the reports leave clearance or readiness unknown are supported uncertainty and therefore earn `met`; they do not mean the learner answer is uninterpretable (`uncertain`). No case intentionally requires the `uncertain` gold status.

Case 12 omits the authority/readiness distinction while naming the current estimate. Its `scope=missing` follows the exposed development convention (development case 15); calling a value an estimate alone does not answer that criterion’s authority question. Grounding remains `met` because it judges assertions actually made, not omitted caveats.

In case 13, the waiting flight is correct but the occupant is explicitly the wrong aircraft. In case 14, the stale estimate is explicitly asserted as latest; the estimate-versus-authority distinction is separately correct. In case 15, the availability and linked release stay correct, while the unsupported source attribution makes grounding `contradicted`, following the frozen R11 source-field convention. These deliberate separations should be preserved rather than collapsing all criteria to a common status.

The fixture tests paraphrase, correction, grounded uncertainty, omission, wrong actor, wrong latest value, longer answers and source attribution. It is small, constructed from exposed contexts and freely tunable; results cannot support held-out or acceptance claims.

Validation performed

A local structural check confirmed 16 sequential unique indices, 12 all-met cases, 4 invalid/partial cases, valid status names, criterion-order matching, the input character bound and exact payload identity with source cases except for learner response. Existing fixtures were not changed. No inference, acceptance run or full application test was performed for this fixture-only addition.
