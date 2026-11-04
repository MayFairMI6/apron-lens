# Classifier-based typed feedback experiment

This is a new, isolated approach following the rejected generative reviewers.
The user authorized it while preserving earlier results and the final video.
Production feedback remains unchanged until all adoption gates pass.

A fixed natural-language-inference classifier compares pairs of statements.
Learner text is the premise for required-point coverage. Received report text is
the premise for checking learner assertions. The classifier outputs scores for
contradiction, entailment and neutral; it does not generate JSON, quotations,
citations or successful learner answers. Code assembles qualitative feedback,
exact learner spans and eligible authored comparison-report references. Model
scores remain fallible and are not a formal proof or professional assessment.

Use `cross-encoder/nli-deberta-v3-small`, revision
`fa2804872c3b4bd748f38c0185cc85775361e735`, Apache-2.0, on CPU with safetensors.
The publisher specifies label order contradiction, entailment, neutral and
training on SNLI/MultiNLI. Those general-domain results do not establish aviation
or learner-assessment accuracy. Source:
https://huggingface.co/cross-encoder/nli-deberta-v3-small

Freeze model, thresholds, propositions, sentence segmentation, temporal filtering,
quote selection and runner before each development version. Reject oversized
inputs rather than silently truncate. Reject invalid run/cutoff/source scopes
before inference. Preserve literal negation and uncertainty. A neutral substantive
criterion indicates missing evidence of coverage; it is not a contradiction.
For grounding only, confidently unsupported content blocks approval under the
existing contract, with feedback saying it is not established rather than false.

Run the same six exposed development failures/controls, keeping labels unchanged.
Require six exact delivered reviews, all three valid answers accepted, and no
false credit. Permit an initial version plus one documented development revision.
If both fail, stop and preserve the diagnosis without deploying. No fresh pilot
may be consumed to tune the candidate. If development passes, independently
validate the unused 24-case draft before running a frozen paired comparison with
production; keep its original file unchanged and retain any labelled derivative.
The existing no-new-false-credit, valid-answer-yield, deadline and native-flow
acceptance gates remain required. ML-051 records the independent plan review.

No model weights are trained. No assistant, UI, scene, media or frozen research
result is changed by running this experiment. A new classifier dependency is
experimental until promotion, and no native execution or device suitability is
claimed from CPU development tests alone.

## Final allowed revision: sentence-local NLI v2

V1 is retained at outputs/typed-nli-development-v1 with its source snapshots and
all six outputs. It failed at 1/6 exact and 0/3 valid exact. V2 is the one allowed
development revision; no further source tuning follows its fixed six-case run.

The fixed 0.8 threshold and pinned model are unchanged. Neutral topical patterns
are authored for every facet of all twelve questions, with no case IDs or gold
labels. Exact full learner sentences matching a topic are tested independently.
No topical coverage means missing; topical coverage with neutral NLI means
uncertain, because a paraphrase can fail entailment. Conflicting relevant
entailment/contradiction means uncertain and blocks met. Other relevant explicit
contradictions retain contradiction priority. Sentences and negation are not
rewritten, and same-sentence extra clauses remain in every relevant pair.

An optional entity-context field names only a unique explicitly stated learner
flight consistent with the criterion source scope, with an operational subject
anchor. It adds no operational fact or status. Competing identities, correction,
identity denial, quotation and speaker attribution disable it; operational
negation itself does not. Names normalize to uppercase. Context-bearing NLI
premises are identified separately from exact learner sentences in the audit;
quotations remain exact original text, never the context prefix.

A bounded authored exclusive-relation hypothesis tests present occupancy of the
same flight and stand when evaluating waiting-for that stand. The premise must
explicitly name that flight and resource and mention occupancy/present position;
planned, future or waiting statements cannot activate it. Entailed occupancy
contradicts waiting-for; simultaneous entailment of both relations is uncertain.
This is a domain rule, not a saved-case label override. Other relation ambiguity
remains NLI uncertainty.

Grounding evaluates every full learner sentence against the active authored
criterion-bundle union, combined topically relevant same-flight current reports,
and individual relevant reports. Only actually entailed premises supply positive
support. A contradictory combined relevant premise blocks favorable individual
support; incompatible current typed facts also withhold before inference.
Wholly superseded messages are removed, partial supersession still withholds,
and qualified historical evidence still forces conservative uncertainty.
Grounding neutral means not established, not that the statement is factually
false. When every sentence is met, citations union the sources actually used to
support every sentence; otherwise they identify the selected offending or
uncertain comparison premise. Authored criterion bundles remain comparison
context rather than proof of a semantic judgment.

Before v2 inference, rubric-faithful hypotheses remove loading-specific wording
from the baggage-delay proposition: the requested point is the delay cause.
Neutral relevance remains a bounded lexical mechanism, not complete semantic
coverage. NLI itself may ignore clauses, mishandle negation or produce false
entailment; injected-probability tests verify policy, not model reliability.
V2 must still pass every existing development and subsequent independent gate.
