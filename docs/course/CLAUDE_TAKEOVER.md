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

The reserved file `experiments/typed_relation_review/fresh-v1.json` is now exposed. It must not be reused as a fresh held-out test after tuning. Frozen candidate SHA256: `74f3445cfb89d85548074e250774e2726549040a3126b4036a77462236d83adc`. The CPU baseline comparison for this reserve has NOT run. (Superseded 3 November 2026: the baseline arm has now run; see Progress log below.) Candidate failures include paraphrase/coverage failures, a long valid quote-span rejection and uncertain clearance grounding. Consult raw records and independent review before changing code.

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

## Progress log

**3 November 2026 — first reserve baseline arm complete (Claude takeover).** The frozen small-NLI v2 CPU baseline (`discriminative-nli-review-v2`, `cross-encoder/nli-deberta-v3-small` rev `fa2804872c3b4bd748f38c0185cc85775361e735`, threshold 0.8) ran on `fresh-v1` into `outputs/relation-reserved-baseline-v2/`: 7/24 exact, 1/12 valid exact, 24/24 delivered, zero false credit (commit `617f092`; command and hashes in ML-052). Paired with R8 (11/24, 3/12, 23/24, 0 false credit): cases 10, 11, 17 are exact in baseline but not R8, R8 delivered yield is below baseline, and R8 is below 10/12 valid exact, so R8 fails those gates. Independent audit of the baseline arm is in progress. The CPU baseline is a rejected experimental reviewer, not production; no superiority claim. `fresh-v1` is now exposed development evidence only.

### Active ownership (3 November 2026)

| Role | Owner | Files / resources |
|---|---|---|
| Coordinator | Claude, main session | Integration; commits/pushes to `codex/checkpoint1-controller-training` |
| Implementation agent | Claude subagent | `experiments/typed_relation_review/{candidate,propositions,strong_candidate,mps_candidate}.py`, `tests/test_typed_relation_review.py`, implementation section of `docs/course/TYPED_RELATION_REVIEW.md`; the ONLY GPU/MPS model owner; new `outputs/relation-*-mps-r9+` directories |
| Independent semantic reviewer | Claude subagent | `docs/course/TYPED_REVIEW_FINAL_ACCEPTANCE.md` and the new `experiments/typed_relation_review/fresh-v2.json`; no model calls |
| Native verification agent | Claude subagent | `docs/course/TYPED_NATIVE_ACCEPTANCE_PLAN.md`; preparation only, no model owners |
| Documentation agent | Claude subagent | This file and `MILESTONE_LEDGER.md` |

**Next concrete action:** implementation agent develops R9+ on exposed data (6 regressions, 24 development cases, exposed `fresh-v1`) without GPU contention; the independent reviewer authors `fresh-v2.json`, withheld from implementation, for the next uncached reserve run. All gates are unchanged.

**3 November 2026 — R9/R10 and second reserve.** Pushed commits `621a753`, `5420cdb`, `aa98646`, `89a660d`, `28f9777`, `8c450e4`, `e47dfbb`, `16dbaf7`. New reserve `fresh-v2.json` (SHA256 `cdb4e59bd3fb3f6b75c5f4f4c423296f4ac274d8a8a27e000814ea371cb35d8f`, 24 cases, independently authored; second label check 24/24, non-blind). R9 was reviewed as NOT qualified (confirm-then-retract false-credit path). R10 (`candidate.py` SHA256 `47da262a...e87556d9961e7a5de4a5286b5`; 6/6, 24/24, 24/24 exposed, 0 false credit; 487 unit tests) was qualified and run once, uncached, paired with the baseline on `fresh-v2`: R10 3/24 exact, 0/12 valid exact, 21/24 delivered, false credit 12 and 17; baseline 4/24, 1/12, 22/24, false credit 9, 12, 17. Newly failing vs baseline: 8, 10, 19. R10 fails all five gates (outputs `outputs/relation-reserve2-mps-r10/`, `outputs/relation-reserve2-baseline-v2/`). Independent audit (`16dbaf7`) confirms rejection; about 13 of 21 failures are structural, and the reviewer judges the current lexical-list plus sentence-NLI architecture unlikely to reach 10/12 on an unseen reserve. `fresh-v2` is exposed; a future acceptance claim needs a third independently validated reserve. ML-052 UNFINISHED; no production promotion or native acceptance; native plan (`0858bc9`) exists, nothing executed. Full detail and the four architecture options are in ML-052.

### Active ownership (updated 3 November 2026)

| Role | Owner | Status |
|---|---|---|
| Coordinator | Claude, main session | Integration; commits/pushes to `codex/checkpoint1-controller-training` |
| Implementation agent | Claude subagent | Idle; implementation paused pending architecture decision. No process running; GPU idle |
| Independent semantic reviewer | Claude subagent | Idle |
| Native verification agent | Claude subagent | Idle; plan only, nothing executed |
| Documentation agent | Claude subagent | `CLAUDE_TAKEOVER.md` and `MILESTONE_LEDGER.md` |

**Next concrete action:** user architecture decision (continue current design; redesign within scope; generative claim extraction verified by NLI; or defer/reject production adoption), then a milestone-ledger placement review before any new revision consumes a third reserve.
