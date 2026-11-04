# AirfieldLens shared takeover and resume record

**Current owner: Codex; Claude is paused after exhausting usage.** R11 redesign remains approved in CURRENT under `TYPED_REVIEW_R11_CONTRACT.md`. Latest frozen R11v3.2 completed all 78 exposed cases: 38 exact, 22/39 valid exact, 74 delivered, six false-credit criteria. The separate 16-case stress diagnostic has eight exact and one false-credit criterion. This version is unqualified. The v3.3 source-ambiguity guard is implemented; its proposed learner-context heuristic was rejected before inference and removed. Core ambiguity, correction and conjunction failures remain unresolved. The user approved testing the existing local Qwen model for structured interpretation on 4 November. A separate learner-only extraction experiment is now running under TYPED_QWEN_FRAME_CONTRACT.md; no production adoption is authorized by this experiment. The old third reserve remains sealed and is ineligible for the changed Qwen architecture under its original contract; no replacement is authorized automatically. No production adoption or native acceptance is claimed. Read the latest progress entries; historical tables below are retained.

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

## Historical takeover position — 3 November 2026 (superseded by progress log)

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


**3 November 2026 — Codex resumes approved redesign.** User confirms Claude is paused because usage is exhausted. Codex owns coordination again at base7cd7671; R11 contract and CURRENT milestone placement adopted unchanged. Implementation works in new redesign modules, preserving R10. Root owns model runs; third reserve remains withheld from implementation. First reconcile whether Claude saved a third-reserve draft, then independently complete authoring/blind labeling before freezing. No production adoption, native acceptance or new model result claimed. Shared local folder remains canonical.


**Codex redesign preparation checkpoint (3 November 2026).** Third reserve independently authored, blind-labeled and adjudicated;71/72criterion agreement before one adjudication,24cases12valid/12nonvalid. Final hash94f637d91845f1413a5d003faa400c2f8ab6b724f4a757b4693eaa893b2e472c; root/implementer have not read it. Frozen contract clarified ordered nonoverlapping quotes before inference. Commits031573c and a61d5aa published; openly tunable16case stress set committedaf208e8. Paired comparison validates actual review contracts and all5gates, with7independently passing tests. Prototype redesign.py/redesign_mps_candidate.py is local/unfrozen; no model result yet. Independent reviewer raised historical-source/partial-source-chunk concerns; implementation addresses these before first exposed diagnostic. Old native build found in prior chat work directory; plan corrected without claiming current source equivalence. Root alone owns MPS evaluation.


**R11v1 actual exposed diagnostics (3 November 2026).** Frozen structural prototype `deb6190a419288cc39700d1b7bd93e81078750d636d78a912352d8bc2bda5c77` ran uncached on old6 and DEV24. Old6:1/6exact,1/3valid,6delivered,0falsecredit; DEV24:5/24exact,5/12valid,24delivered,falsecreditcase9availability andcase23grounding. Outputs `outputs/redesign-regression-mps-r11v1/` and `outputs/redesign-development-mps-r11v1/`;198+775 actualpairs, maximum511/512tokens, maximum5.910/8.488seconds respectively. All input/output records preserved. The architecture contract passes offline but semantic control probes incorrectly infer corrections/history/coverage and can override direct operational entailment. Candidate REJECTED/unqualified; no production/native step or third-reserve use. Next bounded task is an exposed probe-format diagnostic before another candidate revision; pinnedmodel/threshold/gates remain unchanged.


**R11v2 uniform content-only actual result (3 November 2026).** Old6=2/6exact,2/3valid,6delivered,0falsecredit; DEV24=9/24exact,6/12valid,24delivered,0falsecredit. Source/rawoutputs in `outputs/content-only-regression-mps-r11v2/` and `outputs/content-only-development-mps-r11v2/`. Independently reviewed core statuses correct5/6old and18/24DEV; nineDEVfailures are grounding-only. R11v2 is unqualified. Independent reviewer supports a bounded source-only normalization/scope and quote-witness repair within the approved design, not a claim of eventual acceptance or necessity of Qwen. Omission, anaphora, unsupported-extra and historical/correction limitations remain. Root full515tests pass41.831seconds; this is code verification, not semantic acceptance. Next implementation is a new scoped_content module preserving v1/v2; no reserve3 consumption or production/native activity.


**4 November 2026 — scoped-source diagnostic and narrow defect repair.** R11v3 old6=2/6exact,1/3valid,6delivered,0falsecredit; DEV24=8/24exact,5/12valid,24delivered,onefalsecredit(case1grounding). Evidence `outputs/scoped-content-regression-mps-r11v3/` and `outputs/scoped-content-development-mps-r11v3/`. Independent review found source-search proof dependencies incorrectly reused as semantic retrieval links, expanding scoped text to unrelated actors; metadata/provenance eligibility did not prevent wrong-flight entailment. Confidence-ranked quotes also produced an irrelevant parked-tail quote for a cancellation criterion. Eight focused offline tests passed but these actual semantic findings reject v3. Narrow3.1 fixes separate audit dependencies from source retrieval and preserve original-sentence/antecedent quote boundaries; no new grading rule, acceptance relaxation, reserve3 usage or production/native step. Root waits explicit3.1sourcefreeze before actual tests; alloldoutputs/video preserved.


**4 November 2026 — R11v3.1 actual result and next bounded repair.** Old6=3/6exact,2/3valid,5delivered; DEV24=13/24exact,8/12valid,22delivered; bothzero falsecredit. Sourceproof retrieval leak repaired; oldconfirmation quote no longer includes unrelated parked fragment; DEV16scope quote retains neededcontext. Remainingvaliddelivery failures old1/DEV4/DEV12 need earlier explicit learneraircraft context despite later sentence not beginning with a pronoun. DEV10 mixes an older cross-aircraft StandB availability assertion with later confirmation because whole-message currentness was incorrectly inferred from peractor/property factcurrentness. Next3.2 addresses those2bounded issues with explicitsource/quoteaudit, preservingactor-specificolderfacts and originalreports. No newstatus/model/gates, noreserve use, noacceptedproduction/nativeclaim. Rawruns at `outputs/scoped-content-regression-mps-r11v3-1/` and `outputs/scoped-content-development-mps-r11v3-1/`.


**4 November 2026 — R11v3.2 complete exposed diagnostic, not accepted.**

outputs/scoped-content-regression-mps-r11v3-2: 3/6 exact; 2/3 valid exact; 6 delivered; 0 false-credit criteria.

outputs/scoped-content-development-mps-r11v3-2: 14/24 exact; 9/12 valid exact; 24 delivered; 0 false-credit criteria.

outputs/scoped-content-exposed-reserve1-mps-r11v3-2: 12/24 exact; 6/12 valid exact; 23 delivered; 0 false-credit criteria.

outputs/scoped-content-exposed-reserve2-mps-r11v3-2: 9/24 exact; 5/12 valid exact; 21 delivered; 6 false-credit criteria.

outputs/scoped-content-stress-mps-r11v3-2: 8/16 exact; 8/12 valid exact; 16 delivered; 1 false-credit criteria.

The same frozen source was evaluated uncached on all 78 exposed cases and the separately authored 16-case development stress set. The first 30 cases no longer have delivery failures, but broader corrections, unspecified aircraft assignments, authority distinctions and unsupported claims expose false credit. The candidate remains unqualified; fresh-v3 remains withheld and production/native promotion has not occurred. Independent review also found that resource ambiguity could disappear from the completeness guard after unrelated actor-field supersession. The next bounded v3.3 repairs that guard and uses exact learner antecedent context for source retrieval without changing the original claim. Neither repair is presumed to solve the remaining semantic failures. The separately frozen 70-pair cover diagnostic completed; it is exploratory evidence, not adopted grading policy. All previous results and the video remain unchanged.


**4 November 2026 — R11v3.3 ambiguity guard verified, semantic qualification still open.** The A-only implementation (`8efa29b36be79c7edbc1aaebddf82c4864f6529e04aea259355712a62d649b66`) preserves conflicting stand-availability evidence independently of actor-field supersession. Independent review reproduces the original defect and confirms both resource-specific and global completeness are now withheld. Twenty focused tests and the full 535-test suite pass (42.720 seconds). An uncached old-six replay at `outputs/scoped-content-regression-mps-r11v3-3/` has the same model inputs and assessment statuses as v3.2: 3/6 exact, 2/3 valid exact, 6 delivered, zero false-credit criteria. This verifies a bounded mechanical repair, not semantic acceptance. The proposed schema-word learner-context retrieval was rejected before inference and removed after counterexamples assigned another aircraft's or a vehicle's fuel to the preceding aircraft. No blacklist patch was retained. The broader v3.2 failures remain applicable; the third reserve and production/native promotion remain gated. A concrete question about testing the existing local Qwen model for structured interpretation is pending user choice; no model/architecture switch has occurred. Original results and video remain unchanged.


**4 November 2026 — user-approved Qwen extraction experiment, initial run failed.** The user explicitly approved testing the existing local Qwen model. The separate learner-only extraction contract and source were frozen at `195e7a0`. Six difficult exposed inputs and independent semantic annotations were frozen separately; only input text entered inference. `outputs/qwen-frame-extraction-v1-initial/` contains all six outputs, model artifacts/runtime metadata, prompts, observed EOS, immutable source snapshots and failures. All six finished with observed EOS in 25.26–38.73 seconds, but none passed structural validation: the model copied the literal schema placeholder into its relation fields. No extraction, grading or report-support acceptance is claimed. A controlled prompt-only v2 revision replaces the placeholder example with a concrete unrelated-domain demonstration, keeping parser/schema/model/runtime/inputs unchanged. The original third reserve remains sealed and ineligible for this changed architecture; no replacement or production promotion has occurred.


**4 November 2026 — controlled Qwen prompt v2 completed, not qualified.** The unchanged six learner-only inputs were run with a concrete nonaviation extraction example replacing the copied placeholder. Three outputs passed structural validation, two failed exact binding/reference checks, and the last request timed out at the existing 55-second owner deadline. All six attempted cases remain in `outputs/qwen-frame-extraction-v2-initial/`, with raw outputs, source snapshots and actual runtime outcomes. Case12's standalone `it` was incorrectly treated as ambiguous because the binder also matched letters inside `waiting`; case23's exact scope phrase crossed an artificial 160-character transport cut without the required second unit reference. These are separately documented mechanisms, not retroactive acceptance. A v3 representation proposal uses strict fixed-column arrays to reduce generation cost, full-sentence internal units within the unchanged 1200-character input bound, and versioned token-edge exact matching. Semantic review and explicit polarity/epistemic/lifecycle definitions remain required. No full grading/report-check pipeline, reserve evaluation or production adoption has occurred.


**4 November 2026 — Qwen compact v3 completed, interpretation gate remains failed.** Source/representation frozen at `55c9095`; full local suite passed 563 tests in 42.870 seconds. All six v3 requests completed with observed EOS in 8.513–17.723 seconds, with two structurally valid outputs and zero timeouts. `outputs/qwen-frame-extraction-v3-initial/` preserves all raw results and source/runtime hashes. Compact output reduced generation time but did not establish faithful interpretation: correction/property links and qualifiers were omitted, exact lexical slots contained paraphrases, repeated pronouns caused binding failures, and the valid subject-repair control was withheld. Independent full semantic assessment remains in TYPED_QWEN_FRAME_ACCEPTANCE.md. The next representation proposal separates exact source quotations from explicitly untrusted, standalone model-interpreted claims; it requires independent placement and a new frozen addendum, not a relaxed semantic gate. No grading or report-check stage is implemented, no reserve was opened, and the app/video remain unchanged.


**4 November 2026 — Qwen interpreted-claim v4 completed, still experimental.** The separately approved five-field representation ran all six inputs with observed EOS in approximately 6.1–15.7 seconds; five outputs passed structural validation. `outputs/qwen-frame-extraction-v4-initial/` retains the complete frozen run. Some compound interpretations preserve the source meanings, but required atomic structure/correction links are incomplete, case20 invents causality and weakens hold/permission distinctions, and case2 adds an unwarranted denial from a subject correction before failing the unresolved-row schema. No faithful complete structured-interpretation acceptance is claimed. A controlled prompt-only v5 will use unrelated multi-claim/correction examples with the same parser, runtime, input texts and semantic obligations. Twelve independently authored contrast controls are frozen and independently reviewed but remain unrun until initial qualification. Interpretation text remains untrusted; report checking, scoring, native promotion and new-reserve evaluation are not implemented or authorized by a parser pass.


**4 November 2026 — Qwen prompt v5 completed.** All six requests reached observed EOS; five parsed. Results and source snapshots are preserved in `outputs/qwen-frame-extraction-v5-initial/`. Initial readback shows explicit withdrawn/replacement time links, separated held/permission claims and retained cancellation/slot relationships, but readiness is strengthened to confirmation with an exclusivity qualifier omitted, and the subject-repair answer still invents an active denial and malformed unresolved rows. Independent complete assessment is required; initial qualification remains unmet. The twelve frozen contrasting development answers remain unrun. No report-checking/grading stage, native promotion, reserve evaluation or video modification has occurred.
