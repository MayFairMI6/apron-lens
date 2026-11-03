# Report-grounded assistant comparison

This bounded Checkpoint 1 development study tests the current training assistant,
separately from the frozen earlier research evaluation. It measures answer quality,
not learner competence, learning gains or operational ATC safety. The user adopted
this addition on 3 November 2026. The learner interface and approved videos are unchanged.

The question is: **Does the current structured-evidence assistant, with its existing
conversation memory, answer connected airport-report questions more completely and
correctly than a simple retrieval baseline and the same assistant without history?**

Three authored conversations use the vehicle obstruction, occupied arrival stand
and baggage-delay lessons. Each contains six turns: an explicit flight reference,
follow-ups, report-arrival boundaries, an unsupported-readiness question and an
explicit change of aircraft. Seed 17 fixes the scenario. These 18 items are development
probes, not independent held-out samples. Turns within a conversation are dependent.

| Condition | Evidence selection | Conversation state |
|---|---|---|
| Lexical retrieval | Top six facts ranked by TF-IDF token overlap; receipt time and ID break ties | Existing validated intent/reference memory |
| Selector without history | Existing full candidate-fact context | Fresh session each turn |
| Selector with history | Existing full candidate-fact context | Normal live training session |

All arms use Qwen3.5-9B, the same pinned revision and MPS runtime, a 768-token
output cap, text-only input, the same questions and report receipt cutoffs. The lexical
baseline starts from the same eligible pool but sends a subset to the same selector;
its purpose is to isolate this simple retrieval restriction, not reproduce a published
RAG implementation. It may omit evidence that the full-context arms receive. Its missing-
property catalogue is derived from its retrieved subset; the normal full-world validator
can reject false unknowns. This is a documented baseline limitation, not an advantage
that should be attributed solely to graph reasoning. Query tokens and the current
referent are used for retrieval; no answer key is used.

The current app stores validated referents/intents and previous-answer metadata,
not an unrestricted verbatim conversation. The no-history comparison removes that
existing state. It is not a test of long-context dialogue memory or raw assistant-text
replay. No aircraft is selected in these probes, so pronoun resolution must use the
conversation. The native app's persistent selection often supplies an additional cue.

A complete supported answer must be accepted by the existing validator, identify the
expected flight, contain every required current fact, cite the matching source IDs,
and preserve exactly the requested unknown properties. Supported but irrelevant answers,
empty answers, false uncertainty, non-current claims and withheld answers do not pass. The strict non-current-claim rule also
rejects correctly labelled historical facts when these current-status questions do not
request them; that is over-inclusion, not automatically a temporal hallucination.
The runner retains raw expanded proposals, displayed answers, prompts, errors, latency,
usage and the selector's per-attempt audit. The scored factual text is expanded from
selected report IDs; this evaluates report selection and answer coverage rather than
unconstrained prose generation or stylistic naturalness. Citation validity is reported
as not applicable for answers without claims. We do not treat valid format as correctness.

The local model adapter currently infers stop versus length from token count; actual
engine stop reasons are unavailable. This limitation is recorded in the run, not
presented as a verified inference-completion signal. Runs proceed in fixed condition
order, so latency is descriptive and may reflect warm-up/order effects. There is one
scenario seed, no statistical significance claim, and no professional expert validation.

Run with the local model service stopped to avoid loading two copies:

```sh
.venv-candidates/bin/python -m scripts.evaluate_training_assistant --output outputs/assistant-comparison/run-v1.json
```

Use a new output path for every run; the runner refuses overwrites. Validate the authored
cutoff keys without loading weights using `--validate-only`. The scoring expectations
are embedded in `suite()` and never sent in model requests. The implementation and
suite are fixed before the live run; any future revisions need a new version and results.
Historical fixtures, models and result files are unchanged.

A graph database is not needed for these three lessons: the existing facts already carry
flight identity, property, source, receipt time and supersession. If later questions need
multi-aircraft/service dependencies beyond this store, compare graph retrieval against a
strong structured query baseline using the same evidence. Graph links must carry provenance
and temporal validity; a graph must not invent a causal explanation or clearance.

Related work informs the comparison rather than supplying directly comparable scores:
[Li et al., airport RAG, NAACL 2025](https://arxiv.org/abs/2505.13006) compares traditional,
SQL and graph retrieval; [Ghazanfari et al., 2026 preprint](https://arxiv.org/abs/2608.19299)
examines stateful ATC dialogue and accumulating errors;
[Chang et al., 2026 preprint](https://arxiv.org/abs/2605.11769) motivates separating
consequential identity and movement-constraint errors from aggregate language metrics.
Our assistant answers reports in training scenarios; these references do not establish
that it is state of the art or appropriate for operational control.

The runner calls the training handler offline and does not enforce the native client
35-second or driver 40-second timeout. Report responses exceeding those thresholds
separately; an offline answer is not evidence it would have reached the phone in time.
The result prompt is the pre-selector base prompt and its rawModelOutput is the
expanded proposal. The `.prompts.jsonl` sidecar contains actual selector prompts and
raw selections, including each retry. Source hashes in `source-manifest.json` identify
the new runner even when its recorded base commit predates this addition.

The task-success score does not penalize every supported but irrelevant extra fact
when required facts and unknowns are present. It therefore does not measure complete
relevance, prose quality or clarity. Review representative outputs separately and
keep this limitation distinct from source support.

A clarification may be appropriate for a configuration deprived of conversation
history but still fail the full conversation task. The raw scorer field `emptyAnswer`
means no claims or unknown properties; it includes valid clarifications and must not
be read as the previously fixed empty-known-flight defect. The summary separates
clarifications. Support and citation scores are relative to the expected flight;
a wrong-flight answer can be internally sourced yet fail both. Representative review
distinguishes that identity error from invented facts or fabricated citations.

Results: lexical retrieval with history **18/18**, full selector without history
**14/18**, full selector with history **17/18**. All 54 responses were real single-
attempt model calls. This bounded result supports a role for reference memory but
does not demonstrate a benefit from the full evidence pool over simple retrieval.
The current assistant omitted an explicit overall-readiness unknown in one answer;
its cited hold-release fact was supported. The no-history arm had one wrong-flight
answer, two clarifications and one withheld malformed selection. These are distinct
failure types. No prompts or keys were tuned after seeing them.

See [complete results](../../outputs/assistant-comparison/RESULTS.md) and the
[semantic limitation record](https://github.com/MayFairMI6/apron-lens/issues/60#issuecomment-6605604155).
The runner and reporting commands are separate:

```sh
.venv-candidates/bin/python -m scripts.report_training_comparison outputs/assistant-comparison/run-v1.json
```
