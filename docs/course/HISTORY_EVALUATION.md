# History-aware scoring and varied report scenarios

The user authorised this separate evaluation to resolve the mismatch between
change questions and the previous current-only scorer. The old result sets,
scorers and prompts remain unchanged. The app default is v5; v6 remains a frozen
candidate. No weight training, graph database, new app exercise or promotion is
part of this task.

Scorer `report-question-scorer-v2` uses question labels fixed before inference:

| Question mode | Required behavior |
|---|---|
| Current | Provide the required current facts; non-current claims do not pass. |
| History | Include the specifically requested past fact with its actual cutoff status. Relevant current context may also be allowed. |
| Change | Include the declared before and after facts, with correct values, sources and superseded/current labels. |

Every case specifies the expected flight, required and allowed fact IDs, receipt
cutoff and requested unknown properties. Allowed scope prevents unrelated old
reports from passing simply because the question mentions history. A claim must
match its receipt-eligible source's exact value and status. Future facts, wrong
flight identity, fabricated citations, wrong statuses, duplicate claims, omitted
required updates and incorrect unknowns fail. A withheld response cannot pass.
The scorer is evaluation-only; its labels and answer key never enter the model
prompt or app validator. Only current and superseded report states are exercised;
scheduled, expired and conflicting states are outside this battery.

Four new authored report worlds provide 24 questions per model version:

- Weather-related route restrictions, delayed reports, an escort update and a later inspection hold.
- Three stand assignments, a delayed reassignment, a specific past-stand question and a correction to another flight.
- Service completion withdrawn, re-completion, explicit readiness confirmation and subsequent withdrawal.
- Repeated off-block estimate revisions, a past estimate and a flight switch followed by another update.

These worlds use new flight IDs, times and report sequences rather than replaying
the old lesson worlds. They are fictional controlled report exercises, not newly
implemented scenes, Heathrow operational procedures or independent real-world
data. Each family has three flights, including distractors. Four six-turn episodes
are run separately for frozen v5 and frozen v6, using the same pinned Qwen3.5-9B
revision/runtime, 768-token output limit and receipt cutoffs. No aircraft selection
or image is supplied. Conversation memory is the existing validated reference
state, not a full chat transcript. Sessions are isolated between families/versions.

Before inference, the runner saves all worlds, questions, labels, source hashes and
original-artifact hashes in a lock file. It refuses overwrites. Conditions run in
fixed order, so latency is descriptive. It does not enforce native deadlines;
responses exceeding 35/40 seconds must be reported separately. Actual stop reasons
remain unavailable from the unchanged adapter. Retain actual raw selections,
expanded/displayed answers, retries, failures and costs. No pass-rate requirement
or production promotion follows from this experiment.

A separate `old-answer-diagnostic.json` re-scores the two previously observed
readiness-change answers under explicit history-aware labels. This is post-hoc
scorer verification, not new inference, a replacement of the original scores,
or permission to revisit v6's failed promotion gate. Both old studies stay intact.

```sh
.venv-candidates/bin/python -m scripts.evaluate_history_questions --output outputs/history-evaluation/run-v1.json
```

Use a new output path for a new run. `--validate-only` checks labels without loading
the model. Stop the local model service to avoid duplicate allocation and restore
it afterward. The independent review checks scorer counterexamples, the frozen
fixture, actual prompts/results and preservation. Completing a measured comparison
does not require either version to win. Four dependent scenario families cannot
establish broad accuracy, safety, learning benefit or a need for weight training.

Observed result: v5 and v6 each passed22/24 (current12/13, history3/3, change7/8).
Both omitted readiness uncertainty in the weather question and both selected a real
stand report for the wrong flight in the stand-history follow-up. Citation failure
in that case means the source belongs to the wrong expected flight, not that a
citation was fabricated. All48 replies passed structural validation, illustrating
why semantic coverage and identity require separate evaluation. No prompt was
changed in response to these results. The two old-answer diagnostic checks pass
without overwriting their original strict scores.
