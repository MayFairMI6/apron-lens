## Change

Describe the user-visible behavior or research question.

## Shared backbone

- [ ] This PR does not touch `backbone/`, or:
- [ ] `backbone/VERSION` is bumped and `python -m backbone.check --stamp` re-run
- [ ] The same backbone change is made (or planned) in the compaction repository

## Validation

Record relevant backend, model, Unity or phone checks. Identify model test doubles.

## Research impact

If inference or data changed: name the development cases used, preserve frozen results,
and state whether a new untouched evaluation is needed. Report raw model results
separately from the deterministic baseline and guard coverage.
