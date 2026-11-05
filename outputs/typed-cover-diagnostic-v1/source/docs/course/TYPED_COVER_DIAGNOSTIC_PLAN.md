# Exposed semantic cover diagnostic, version 1

This is a bounded diagnostic of AirfieldLens rubric semantics, frozen before
inference. It is not grading policy, learner evidence, a source-grounding check,
or an adoption claim. It reads only the exposed `development-v1.json`; synthetic
paired controls use its already exposed question topics. No reserve answers or
other experiment outputs are read. The question is whether a forward entailment
vector plus reverse reconstruction of the exact complete answer can help
separate genuinely absent rubric content from content explicitly addressed but
unresolved.

The canonical fixture, all control strings, expected forward labels, and
comparison interpretations live in `scripts/probe_typed_cover.py`. The builder
is pure. `--freeze` writes the matrix, hashes, and source snapshots without
importing the classifier or accessing its model cache. An exclusive output
directory is mandatory; reusing an existing directory fails.

For every case, forward pairs are **raw full learner answer → individual rubric
facet**, with no question in the learner premise. For every nonempty subset of
its at most three facets, the builder precomputes **facet conjunction → exact
full answer**. Every conjunction uses the same rule: facet sentences in declared
order, separated by newlines. No question, extracted clause, favorable per-case
cover wording, reverse-derived facet, or topic/category hypothesis is added.
The complete answer retains qualifiers, extras, corrections, and entity names.

After scoring, deterministic analysis selects exactly one reverse pair whose
members are **all and only** the facets with forward entailment at probability
at least 0.8. It never selects a smaller cover because that cover scores better.
If no forward facet entails, no reverse pair is selected. If a forward score is
unavailable, cover selection is withheld. All precomputed pair scores, including
unselected reverse scores, remain in the raw record. Unknown scores are never
substituted with neutral labels.

The fixed controls and interpretations are:

- Procedures and safeguarding alone versus the same answer plus explicitly
  unclear TRN101 hold: hold is absent in the first and addressed but unresolved
  in the second. These controls test whether exact-answer reverse entailment
  changes when the unresolved clause remains present.
- Estimate alone versus the same estimate plus explicitly unclear authority
  distinction: authority is absent versus addressed but unresolved. Reverse
  comparison labels remain null; this classifier's treatment of epistemic
  qualifiers is the object of observation.
- A causal change sentence that also explicitly asserts release versus vehicle
  clearance alone: the first includes release by authored logical dependency,
  while vehicle clearance alone does not establish the hold decision. No rule
  demands that the learner repeat the release in a separate sentence.
- A correct estimate plus an unsupported takeoff-clearance extra: reverse keeps
  the extra. Independent clearance does not contradict the statement that an
  estimate itself does not establish clearance. The extra can prevent exact
  cover even with an otherwise clear core, so non-entailment cannot identify
  unclear rubric content by itself. No report-source grounding inference is made.
- Corrections in both directions: the final corrected value is the intended
  assertion. Both earlier value and correction remain in reverse. Any inability
  to reconstruct that history is a diagnostic limitation, not missing content.
- Wrong aircraft identity: TRN103's estimate does not state TRN102's estimate;
  different aircraft can have different estimates without contradiction.
- Broad readiness unknown versus specific takeoff-clearance unknown: neither
  unknown licenses the other. The declared broad-to-specific dependency is
  explicitly absent. An unknown is never a denial.

Unambiguous direct forward-content controls have authored entailment, neutral,
or contradiction expectations. Reverse labels and comparison-label expectations
are null; no accuracy denominator or invented semantic gold is created for them.
Interpretations are frozen in each case before calls. There is no blanket
neutral-to-missing rule. Reverse entailment only says that the selected rubric
cover is compatible with reconstructing this exact answer under this classifier;
it does not prove omission. Reverse non-entailment also has competing causes:
unclear content, unsupported extras, corrections, wrong entities, incomplete
covers, and classifier error. Neither result grants `met`, grounding, or approval.
Every pair and selected observation has role `rubricCoverDiagnostic` and
`learnerEvidence: false`.

The run uses the pinned DeBERTa revision, MPS with no CPU fallback, threshold
0.8, and a 55-second scoring deadline between/after device batches. Tokenization
is checked before scoring, with no truncation and the engine's maximum at most
512 tokens. As in the current pair-engine convention, the process owner must
enforce a hard wall-clock timeout if required. The engine's actual dtype
is recorded verbatim and must equal `torch.float16` before any scoring; a
different dtype causes an explicit recorded failure without conversion. Prior
actual runs of the unchanged engine reported float16. This diagnostic neither
changes global dtype nor casts the model; a missing explicit cast alone does
not establish a dtype mismatch.

The run records source and exposed-fixture SHA-256 hashes, the complete frozen
matrix hash, local model-artifact hashes, actual runtime/device/dtype/version
metadata, token lengths, raw probabilities for every scored pair, scoring clock,
UTC start/end times, total duration, and deterministic observations. Source and
fixture hashes are rechecked at construction and completion. Partial scores and
errors are retained. Model loading is local-only through the pinned engine.

Pure verification: compile the script, invoke `build_cases()` and `build_pairs()`
twice to check determinism, verify the pair limit, assert every reverse hypothesis
matches the untouched answer, check all subset counts, and feed synthetic scores
to confirm exact forward-E selection, empty selection, and incomplete-score
withholding. These tests require no model calls. The parent will run actual MPS
inference only after the current frozen 3.2 evaluations finish, to avoid contention.

Commands from the repository root (choose a new output path for each):

```sh
python3 scripts/probe_typed_cover.py --freeze /tmp/typed-cover-v1-freeze
.venv-candidates/bin/python scripts/probe_typed_cover.py outputs/typed-cover-diagnostic-v1
```
