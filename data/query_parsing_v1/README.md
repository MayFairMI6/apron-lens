# Question → structured query, v1

Typed coordinator questions paired with the structured query that answers them:
`queryType` (latest | current | change) and `properties` (field names from
`backend/evidence.py`). The aircraft is the one selected in the app, so it is
not part of the parse.

- `dev.json` (36): used to develop the model prompt and the keyword baseline.
- `test.json` (36): frozen by hash in `manifest.json` and committed before
  either parser was written; differently worded from dev.

Questions and labels were written by the AI assistant that also wrote the
parsers, without independent human review, and all describe fictional
operations. Treat results as a small development-scale comparison.
