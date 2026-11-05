# Fresh-v2 second independent label check

Reviewer: second label validator (Claude Opus 5.5 subagent). It is separate from
the fresh-v2 author/first validator and from the implementation agent.
Date: 3 November 2026. No model, GPU or backend call was made. No fixture,
implementation or other existing file was edited. No implementation source or
R9 output was opened.

This file deliberately contains **no answer text, no gold statuses and no
per-case category**. Cases are referenced only by index and by criterion IDs,
which already appear in every payload. It is safe to share with the
implementation agent. It does not release the reserve.

## Fixture identity

`experiments/typed_relation_review/fresh-v2.json`. The working-tree SHA-256 and
the commit `621a753` SHA-256 both equal
`cdb4e59bd3fb3f6b75c5f4f4c423296f4ac274d8a8a27e000814ea371cb35d8f`.

## Method

1. **Structural checks (scripted, read-only).**
   - Every payload has exactly the eight model-input keys.
   - No payload contains `category`, `tags`, `why`, `index` or category strings.
     Criterion `expected` fields hold rubric text only, as in the prior suites.
   - Every report is from the payload's episode and has `receiptTime <= cutoff`.
   - Every criterion's evidence IDs are present in that payload's reports.
   - Gold keys match the payload criterion order, and every gold value is in the
     status vocabulary.
   - The payload checkpoint matches the case's bookkeeping checkpoint.
2. **Bundle cross-check.** At each exercise/checkpoint, the report bundle (after
   episode-ID normalization), criteria, question and cutoff equal those in
   `development-v1.json` and `fresh-v1.json`. Those suites' bundles were
   independently reconstructed from `TrainingSession` in an earlier review. I
   did not rebuild payloads by running backend code myself.
3. **Semantic label check.** For each case, I read the question, rubric text,
   every report received by the cutoff and the learner answer. I then judged each
   criterion status and grounding against the documented conventions:
   - `TYPED_RELATION_REVIEW.md`, including these rules:
     - Missing requested content is missing.
     - A present but unclear relation is uncertain.
     - A correct core plus an unsupported extra keeps its core statuses, while
       grounding blocks approval.
     - Latest values need not recite superseded values.
     - Unknown clearance is not a denial.
     - Readiness absence is report-scope uncertainty.
     - Explicit wrong-flight attribution contradicts.
   - `TYPED_REVIEW_FINAL_ACCEPTANCE.md`.
   - How the 48 gold labels in `development-v1.json` and `fresh-v1.json` apply
     these conventions, such as half-supplied conjunctive criteria, stale values,
     unsupported non-clearance extras and wrong-flight relations.
4. **Composition check** against the declared counts.

**Limitation (disclosed).** This check was **not blind**. The fixture stores
gold next to each payload, and I saw it while reading cases. My agreement is
therefore a review of the gold against the evidence, not a separately produced
label set compared afterwards. A blind relabel would be stronger evidence. Both
validators also share the same documented conventions. Where a convention
itself is debatable, this check cannot detect the problem.

## Composition

The counts match the declaration:
- 24 cases: 12 valid, 9 invalid, 2 partial and 1 deliberately ambiguous with
  uncertain gold.
- All 4 exercises and all 12 checkpoints are used.
- There are 8 late-baggage checkpoint-1 fuel/baggage cases: 4 valid and 4
  invalid/partial.
- Response lengths are 47–523 characters, within the 1200-character limit.

## Per-case verdicts

"Agree" means every listed criterion's gold status agrees with my reading of the
received reports and rubric. "Note" marks a case where I seriously considered an
alternative status and found the gold supported by a documented convention or a
prior-suite precedent. Notes do not record disagreement.

| Case | Exercise / checkpoint | Criteria checked | Verdict | Note |
|---:|---|---|---|---|
| 0 | late_baggage / 1 | delay, separation, grounding | agree | |
| 1 | late_baggage / 1 | delay, separation, grounding | agree | Every context clause checked against reports received by the cutoff |
| 2 | late_baggage / 1 | delay, separation, grounding | agree | alternative considered for a criterion; resolved by convention or precedent |
| 3 | late_baggage / 1 | delay, separation, grounding | agree | |
| 4 | late_baggage / 1 | delay, separation, grounding | agree | |
| 5 | late_baggage / 1 | delay, separation, grounding | agree | |
| 6 | late_baggage / 1 | delay, separation, grounding | agree | |
| 7 | late_baggage / 1 | delay, separation, grounding | agree | |
| 8 | surface_conflict / 1 | flight, reason, grounding | agree | |
| 9 | surface_conflict / 1 | flight, reason, grounding | agree | |
| 10 | surface_conflict / 2 | release, change, grounding | agree | alternative considered for a criterion; resolved by convention or precedent |
| 11 | surface_conflict / 3 | unknown, scope, grounding | agree | |
| 12 | late_arrival / 1 | flight, occupant, grounding | agree | alternative considered for a criterion; resolved by convention or precedent |
| 13 | late_arrival / 2 | availability, plan, grounding | agree | |
| 14 | late_arrival / 2 | availability, plan, grounding | agree | |
| 15 | late_arrival / 3 | availability, release, grounding | agree | alternative considered for a criterion; resolved by convention or precedent |
| 16 | late_baggage / 2 | estimate, scope, grounding | agree | |
| 17 | late_baggage / 2 | estimate, scope, grounding | agree | |
| 18 | late_baggage / 3 | unknown, scope, grounding | agree | Every context clause checked against reports received by the cutoff |
| 19 | late_baggage / 3 | unknown, scope, grounding | agree | alternative considered for a criterion; resolved by convention or precedent |
| 20 | fog_restrictions / 1 | procedures, hold, grounding | agree | alternative considered for a criterion; resolved by convention or precedent |
| 21 | fog_restrictions / 2 | partial_cancellation, hold, grounding | agree | |
| 22 | fog_restrictions / 3 | confirmation, authority, grounding | agree | |
| 23 | fog_restrictions / 3 | confirmation, authority, grounding | agree | |

## Result

- **Agree: 24 / 24 cases (72 / 72 criterion statuses).**
- **Disagree: 0.**
- **Ambiguous (needing adjudication): 0.**
- Notes on cases 2, 10, 12, 15, 19 and 20 record alternatives I considered and
  rejected. They are not open disputes. The notes deliberately do not name the
  criterion or the direction, so they cannot reveal labels.
- **Payload hygiene:** No gold or metadata appears in model input. Only reports
  from the same episode and received by the cutoff are present. Bundles match
  the previously reconstructed checkpoints.

This check strengthens the fresh-v2 validation that was previously disclosed as
single-reviewer. It is not blind, so it does not fully replace a blind
independent relabel. It does not evaluate any candidate and makes no claim about
ML-052 completion. The reserve stays sealed from implementation under the access
rule in `TYPED_REVIEW_FINAL_ACCEPTANCE.md`.
