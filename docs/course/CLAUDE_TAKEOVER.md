# AirfieldLens shared takeover and resume record

## Shared working location

Use the SAME existing checkout for Claude and Codex:
`/Users/mayfairmi6/Documents/Codex/2026-10-12/the-final-project-is-to-create`.
Do not move the project into the currently selected Smarter Skies workspace or create an untracked parallel copy. Save code, tests, new immutable results and documentation here so either agent can resume. Use `docs/course/CLAUDE_TAKEOVER.md` as the common handoff entry point and append dated progress below; record who owns active edits to avoid simultaneous writers. Never save secrets, credentials, downloaded model weights or private audio in tracked files.

Repository: https://github.com/MayFairMI6/apron-lens
Branch: `codex/checkpoint1-controller-training`; PR #22 is the publication destination, not a claim of merge into main. Base before this handoff: `9ef14e718b057b128e52812857755b62be9741df`.

## Read in order

1. [Milestone ledger](MILESTONE_LEDGER.md), especially ML-052.
2. [Independent acceptance review](TYPED_REVIEW_FINAL_ACCEPTANCE.md).
3. [Implementation and experiment report](TYPED_RELATION_REVIEW.md).
4. [Agent policy](../AGENT_EXECUTION_POLICY.md).
5. Current git status/diff and only the relevant code/tests.

## Verified current position — 3 November 2026

ML-052 is UNFINISHED. Latest R8 fixes pass all six old regressions and all 24 exposed development questions, with independent review. The actual uncached reserved test FAILED: 11/24 exact, 3/12 valid answers exact, 23/24 delivered, zero false-credit criteria. Evidence is in `outputs/relation-regression-mps-r8/`, `outputs/relation-development-mps-r8/`, and `outputs/relation-reserved-mps-r8/`. Preserve every prior run.

The reserved file `experiments/typed_relation_review/fresh-v1.json` is now exposed. It must not be reused as a fresh held-out test after tuning. Frozen candidate SHA256: `74f3445cfb89d85548074e250774e2726549040a3126b4036a77462236d83adc`. The CPU baseline comparison for this reserve has NOT run. Candidate failures include paraphrase/coverage failures, a long valid quote-span rejection and uncertain clearance grounding. Consult raw records and independent review before changing code.

New production scaffolding exists in `backend/typed_review_service.py`, `backend/typed_classifier_adapter.py`, `modelaccess/nli.py`, and backend admission/worker changes. Main still uses the old reviewer. `backend/typed_review_policy.py` does not yet exist: the inactive adapter deliberately requires explicit policy promotion. Do not activate this rejected candidate.

The strong candidate uses pinned DeBERTa-v3-large revision `b3546ea6b0346eb6f8d5d68b13c7dc6d0376b3d7`, MPS, threshold 0.8 and 55-second policy deadline. Run locks preserve actual hashes/settings. CPU baseline is a rejected experimental small NLI model, not deployed production; model/runtime differ, so no policy-only superiority claim.

## Next work and fixed acceptance

First finish the frozen reserve baseline comparison and independent failure analysis without tuning during evaluation. Then develop fixes using exposed cases, preserve failures, and independently author a NEW reserve. All six old regressions and 24 development questions must pass; the fresh reserve requires at least 10/12 valid answers exact, zero false-credit criteria, no newly failing baseline case, and delivery/valid acceptance at least baseline. Do not weaken these gates.

Only after semantic acceptance: promote equivalent policy into backend, activate the isolated service, verify actual owner startup/warmup, shared GPU admission, stale/duplicate requests, timeout recovery and retries. Test actual native iOS typed input, displayed feedback and expandable sources. Backend-only tests do not establish native acceptance. Then complete full tests, research integrity, backbone boundary, independent ledger review, GitHub publication/CI and factual write-up status updates. Do not claim physical-phone or TestFlight validation.

Run evaluations from the shared checkout with `.venv-candidates/bin/python scripts/run_relation_review.py OUTPUT FIXTURE --module MODULE`. Use a new OUTPUT every time. Candidate module: `experiments.typed_relation_review.mps_candidate`; frozen baseline: `experiments.typed_nli_review.candidate`. Do not run GPU model owners concurrently. Check current processes first; stale process IDs in chat are not reliable.

## Subagent division and return handoff

Coordinator: continue until all acceptance gates pass or a genuine external blocker requires user action. Use bounded subagents with separate files: (1) implementation/runtime, (2) independent semantic acceptance, (3) native end-to-end verification, (4) factual ledger/publication documentation. Sonnet is suitable for routine work; use Opus for difficult independent semantic review if available. Follow available repository visual-review requirements and accurately identify actual reviewers. Reviewers must not silently change gold labels or implementation to improve results.

After every meaningful step, save progress IN THIS SAME FOLDER: append decisions and evidence to the milestone ledger; append acceptance findings to the acceptance report; keep this handoff current. Record changed files, exact commands and output paths, versions/hashes, observed pass/fail counts, publication commit/PR, active ownership/processes if any, and the next concrete action. Commit/push verified relevant artifacts to the existing branch, preserving history. This lets Codex jump back in later without reading the entire conversation. Do not save the only progress record in Claude's private memory or another checkout.

## Preserve video, old results and user writing

The final narrated video is unchanged: `/Users/mayfairmi6/Downloads/AirfieldLens-Checkpoint-1-Presentation.mp4`, 486.4 seconds, SHA256 `5d7a20600a32c9211ef16ab9fcb5dd891366b4badb4c7f0888af728f62af3af1`. Preservation manifest: `work/relation-preexisting-evidence.json` (local).

Claude may refine prose separately; implementation handoff updates to live write-ups should be factual status only and preserve all user Coordination/Meetings text and newer edits. Reflection: https://docs.google.com/document/d/1snPF1vh7iPIfRgaiQk2L0TAGWjCK6T1_6i8NQCRjahI/edit . Script: https://docs.google.com/document/d/10VUWMZId-5iPD4astkIK-sS09xTaTNF-CLYNVZVvR7E/edit . Do not edit video or spoken script. Older PDFs are not automatically current.

## Publication checks for this handoff

Pending final local checks and push at initial creation; coordinator will append actual outcomes before delivery. No acceptance or deployment claim is implied by publishing this development snapshot.

Local handoff checks: 473 unit tests passed in43.933seconds; research integrity passed with160 frozen records; backbone boundary passed; diff whitespace check passed. All411 prior tracked output hashes and final Downloads video hash verified unchanged. These checks do not override failed semantic acceptance.
