# Remaining-fixes independent review

Reviewed 3 November 2026. This bounded review read saved outputs and source; it
made no model calls, inspected no new images and changed no production reviewer.

The unit-support-review-v2 development gate fails. Do not promote this candidate
or consume the fresh paired evaluation set. Its six records contain two exact
accepted reviews, one accepted semantic false credit and three withheld reviews.
This is exposed development evidence, not a paired comparison or benchmark.

The current candidate SHA-256 matches the development lock:
`6f4c039703c13725205fd79ae12cc8971457a3b1bf0fc6afc7c04a02a39eac1c`.
The reviewer read every learner response, actual output, expected status and
relevant report in `typed-claim-development-v2/records.jsonl` and `lock.json`.

| Record index | Independent finding |
|---|---|
| 0, valid waiting/occupant response | Correctly distinguishes TRN103 waiting for Stand B from TRN102 occupying it. Both substantive criteria and grounding are met, with L010 support and literal learner quotations. Accepted exact match. |
| 1, valid baggage/fuel response | Correctly credits baggage delay and the separation of completed fuel from outstanding baggage. L011/L014 support the statements. Accepted exact match. The displayed separation quote covers only the first of its two referenced units; the raw mapping retains both. |
| 2, omitted fog hold answer | Real accepted semantic failure. The learner only states that safeguarding and low-visibility procedures are active. The model nevertheless marks the hold criterion met, explaining that the learner "implies hold status by omitting release". Omission does not state hold/no clearance. Gold hold=missing and verdict=partly_supported are justified; the candidate instead displays all-met/supported. Exact unit text and eligible R005 do not establish learner coverage. |
| 3, false stand occupancy | The raw output correctly identifies the TRN103/TRN102 occupancy contradiction, but returns a list rather than the required units/criteria object. The strict schema rejects it. Honest withheld review, not a successfully delivered correction. |
| 4, correct core plus invented engine fire | The raw output identifies the engine-fire unit as unsupported and correctly credits the cancellation/authority core. It gives that unsupported unit no evidence IDs, contrary to the current all-rows evidence contract; the whole review is withheld. Do not count this as accepted grounding success or as displayed false credit. This is a coverage/contract failure despite promising raw detection. |
| 5, valid explicit unknown | Correct substantive raw statuses, but the authority criterion cites R002 in addition to its permitted R008. R002 is received evidence globally, yet outside this criterion's allowed set. The validator correctly rejects it. The raw comment also says "no clearance" where R008 establishes unconfirmed clearance; the saved learner wording and criterion status preserve uncertainty, but that comment is not a basis for claiming flawless interpretation. Valid answer withheld. |

Thus accepted review yield is 3/6 and exact delivered status match is 2/6. There
is one accepted false-credit criterion (record 2). Three fully correct responses
are present (0, 1, 5), of which two receive accepted reviews. The partial answer
is falsely fully credited. The unsafe examples are withheld rather than given
false credit, but the existing development stopping rule still fails. No new
baseline comparison was run, so no relative false-credit improvement is claimed.
The original v1 JSON-fence failures and their raw outputs must remain preserved.
Production typed-practice-review-v2 remains the default; #60/#61 remain open.

## Worker lifecycle review

The final source adds an independent POSIX Python interpreter, fresh IPC per
owner, deadlines around the complete startup and request exchange, and capped
transport cleanup. The PYTHONPATH handoff now includes the parent's import
search paths, allowing discover-imported fake factories to be unpickled. Source
review found no new concrete ownership/readiness blocker in that final change.
The final suite log `/tmp/airfield-fixes-tests-final.log` records 357 tests passed
in 50.742 seconds. This reviewer read that result rather than rerunning the suite.

Previously reviewed `repeated-worker-recovery-v1` receipts establish three forced
real-runtime recovery cycles, successful actual ready responses, stop-before-start
ownership and absence of the recorded old owner/descendant PIDs after recovery.
Those receipts pin the worker source before the final PYTHONPATH handoff; the
new import-path change has suite coverage, not another exact-final-source real
model run. Preserve that source distinction. The measured recovery times were
19.73, 23.89 and 21.11 seconds. The crash cycle records exit code 7 even though
the shortened probe deadline reported TimeoutError to its caller.

The intended normal generation/cleanup budget is 55 + 2 + 2 + 0.25 seconds, below
the 60-second server wait with an overhead caveat. This is not a universal hard
wall-clock guarantee. Child resource-tracker cleanup warnings remain in stderr;
parent RSS is nonmonotonic and shared device allocation was not measured. Accept
bounded lifecycle behavior without asserting indefinite cleanup or closure of
every #62 latency/device-failure limitation.

Scenery interpretation belongs to the Astra review and was not repeated here.
No visual issue closure, video change, semantic candidate adoption, new scope or
milestone completion is implied by this note.
