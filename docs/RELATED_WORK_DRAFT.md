# Related work (draft for review)

Status: draft written 31 October 2026 and extended on 1 November for the AR
scope (`docs/AR_SCOPE.md`): AR assistants, multi-turn and agentic language
models, and AR and AI in airport operations [17–22]. For the author to review
and rewrite.
Every reference below was checked against its publisher record (Crossref, or
arXiv and the EUROCONTROL publication page). The summaries describe each
work's general aim and how ApronLens relates to it. Before quoting a specific
result from any of these papers, check it against the paper itself. These
works establish the approaches ApronLens builds on; they do not establish its
novelty, and a fuller search is still needed before claiming a contribution.

## Grounding and collaborative reference

Conversation partners build common ground and agree on what a phrase refers
to through repair and acceptance [1, 2]. ApronLens takes the same view of a
correction such as "I mean its next rotation". It is an update to the shared
referent, kept in session memory, and it never changes a reported fact.
ApronLens adds a constraint the classic accounts don't face: the referent's
evidence keeps changing between turns.

## Situated and multimodal reference

Referring-expression datasets tie language to regions of an image [3]. Visual
dialog extends this to multi-turn questions about one image [4], and SIMMC 2.0
to task-oriented conversations in rendered, immersive scenes with ambiguous
object references [5]. ApronLens's visual families sit closest to SIMMC 2.0.
The differences are that the scene changes over time, that reports with their
own receipt times compete with what is visible, and that an observation never
overrides a report.

## Dialogue state

Task-oriented dialogue work such as MultiWOZ [6] tracks a belief state across
turns. ApronLens keeps a deliberately narrow state: user intents from the
selection or a validated correction, and assistant turns tied to the receipt
cutoff they were produced under. Its validator checks every displayed claim
against that cutoff.

## Answers that depend on time and conflicting evidence

SituatedQA shows that the right answer can depend on when and where a
question is asked [7]. Work on knowledge conflicts studies models that prefer
their own knowledge over the evidence they're given [8]. ApronLens's late,
conflicting and missing-evidence families test the same pressures: an answer
must follow the reports received by the cutoff, show conflicts rather than
pick a side, and say "unknown" rather than guess. The development runs found a
related failure: a model reporting a visual state that matched a report
instead of the image.

## Long context and memory

Models use information in long contexts unevenly [9], and some systems manage
context explicitly in tiers [10]. ApronLens gives the model a small, scoped
context instead of a growing transcript: the candidate flights' received
facts, the visible memory, and the changes since the previous answer, computed
by the same function the validator uses.

## Attribution and factual precision

ALCE evaluates whether generated text is supported by its citations [11], and
FActScore scores factual precision at the level of atomic claims [12].
ApronLens's typed claims, checked one by one against receipt-eligible reports
and shown through fixed templates, follow this claim-level view. They are not
a reproduction of either benchmark.

## Shared perspective and proactive assistance

Eye2Eye studies cognitive alignment between a person and an AI through a
shared first-person perspective, with revisable memory and feedback [13].
ApronLens studies the narrower problem of reconciling conversational
corrections with independently arriving, source-backed reports on a phone. It
uses a tap on the aircraft in the AR view rather than gaze. Pro²Assist provides step-aware
proactive assistance from egocentric perception during procedural tasks [14].
It motivates ApronLens's later, separate study of when to tell a user that new
evidence has changed an earlier answer.

## AR assistants and deictic reference

GazePointAR resolves pronouns in spoken questions to a wearable AR assistant
("what's over there?") from eye gaze, pointing and conversation history [17].
It is the closest AR work to ApronLens's pointing condition. ApronLens differs
in three ways: the referent has to persist and be corrected across turns while
the scene and its reports change; the AR pointing condition is compared with a
text-only user on the same intents; and the user's view can be interrupted
(tracking loss) while reports keep arriving, so the assistant must say what
changed while the user was not looking.

## Multi-turn and agentic language models

Language models degrade sharply when a task unfolds over several turns
instead of one: they commit to early assumptions and then answer too soon
[18]. τ-bench evaluates agents that talk with a simulated user and act through
tools under domain rules, and reports low consistency across repeated trials
[19]. Both are text-only, and the facts the agent relies on don't change during
the conversation. ApronLens studies a multi-turn assistant whose evidence does
change between turns, with corrections, late reports and interrupted views,
and it checks every displayed claim against received evidence instead of
trusting the model.

## AR and AI in airport operations

AR has been designed for air cargo handling at terminal warehouses, with
operator guidance through AR glasses [20]. Computer vision monitors aircraft
turnarounds from apron cameras, detecting service activities such as fuelling
and baggage handling [21]. Language models have been benchmarked on aviation
operational knowledge, including ground operations [22]. None of these
combines a conversational assistant, an AR view of the stand and changing,
time-stamped reports. In ApronLens, turnaround-monitoring outputs would be one
more source of reports for the assistant to reconcile, not a replacement for
it. AR head-up displays have also been studied for tower controllers in SESAR
projects; those reports still need checking before they are cited.

## Situation awareness and airport coordination

Situation awareness theory frames the operator's need for an accurate,
current picture of a dynamic system [15]. Airport Collaborative
Decision-Making (A-CDM) defines the shared milestones and estimates, such as
the target off-block time, that ApronLens's fictional reports imitate [16].
ApronLens claims no operational use. Its reports are synthetic, and the
estimates are treated as estimates.

## Gap to state carefully

I didn't find work on conversational AR assistance for turnaround or stand
coordination that combines spatial reference, corrections and time-stamped,
source-backed reports. More specifically, AR assistants resolve a pointing or
gaze reference at one moment [17], and multi-turn agent studies keep the facts
fixed during a conversation [18, 19]. I found no work measuring how an AR
assistant keeps a shared referent and its evidence current across turns while
reports arrive and the user's view is interrupted, which is what ApronLens's AR
conditions test. That reflects a limited search, not proof of absence; a
systematic search should come before stating it as a gap.

## References

1. H. H. Clark and D. Wilkes-Gibbs. Referring as a collaborative process. *Cognition*, 1986. https://doi.org/10.1016/0010-0277(86)90010-7
2. H. H. Clark and S. E. Brennan. Grounding in communication. In *Perspectives on Socially Shared Cognition*, APA, 1991. https://doi.org/10.1037/10096-006
3. L. Yu, P. Poirson, S. Yang, A. C. Berg and T. L. Berg. Modeling context in referring expressions. *ECCV*, LNCS, 2016. https://doi.org/10.1007/978-3-319-46475-6_5
4. A. Das, S. Kottur, K. Gupta, A. Singh et al. Visual Dialog. *CVPR*, 2017. https://doi.org/10.1109/cvpr.2017.121
5. S. Kottur, S. Moon, A. Geramifard and B. Damavandi. SIMMC 2.0: A task-oriented dialog dataset for immersive multimodal conversations. *EMNLP*, 2021. https://doi.org/10.18653/v1/2021.emnlp-main.401
6. P. Budzianowski, T.-H. Wen, B.-H. Tseng, I. Casanueva et al. MultiWOZ: A large-scale multi-domain Wizard-of-Oz dataset for task-oriented dialogue modelling. *EMNLP*, 2018. https://doi.org/10.18653/v1/d18-1547
7. M. J. Q. Zhang and E. Choi. SituatedQA: Incorporating extra-linguistic contexts into QA. *EMNLP*, 2021. https://doi.org/10.18653/v1/2021.emnlp-main.586
8. S. Longpre, K. Perisetla, A. Chen, N. Ramesh et al. Entity-based knowledge conflicts in question answering. *EMNLP*, 2021. https://doi.org/10.18653/v1/2021.emnlp-main.565
9. N. F. Liu, K. Lin, J. Hewitt, A. Paranjape et al. Lost in the middle: How language models use long contexts. *TACL*, 2024. https://doi.org/10.1162/tacl_a_00638
10. C. Packer, S. Wooders, K. Lin, V. Fang, S. G. Patil, I. Stoica and J. E. Gonzalez. MemGPT: Towards LLMs as operating systems. arXiv:2310.08560, 2023. https://arxiv.org/abs/2310.08560
11. T. Gao, H. Yen, J. Yu and D. Chen. Enabling large language models to generate text with citations. *EMNLP*, 2023. https://doi.org/10.18653/v1/2023.emnlp-main.398
12. S. Min, K. Krishna, X. Lyu, M. Lewis et al. FActScore: Fine-grained atomic evaluation of factual precision in long form text generation. *EMNLP*, 2023. https://doi.org/10.18653/v1/2023.emnlp-main.741
13. Teng, Chen, Cai, Lu et al. Seeing Eye to Eye: Enabling cognitive alignment through shared first-person perspective in human–AI collaboration. *CHI*, 2026. https://doi.org/10.1145/3772318.3791059
14. Xu, Yang, Jiang, Liu et al. Pro²Assist: Continuous step-aware proactive assistance with multi-modal egocentric perception for long-horizon procedural tasks. *Proc. ACM IMWUT*, 2026. https://doi.org/10.1145/3832022
15. M. R. Endsley. Toward a theory of situation awareness in dynamic systems. *Human Factors*, 1995. https://doi.org/10.1518/001872095779049543
16. EUROCONTROL. Airport Collaborative Decision-Making (A-CDM) Implementation Manual, version 5.0, March 2017. https://www.eurocontrol.int/publication/airport-collaborative-decision-making-cdm-implementation-manual

First names for [13] and [14] were abbreviated in the publisher record, so
complete them from the papers before submission.
17. J. Lee, J. Wang, E. Brown, L. Chu, S. S. Rodriguez and J. E. Froehlich. GazePointAR: A context-aware multimodal voice assistant for pronoun disambiguation in wearable augmented reality. *CHI*, 2024, article 408. arXiv:2404.08213. https://arxiv.org/abs/2404.08213
18. P. Laban, H. Hayashi, Y. Zhou and J. Neville. LLMs get lost in multi-turn conversation. arXiv:2505.06120, 2025. https://arxiv.org/abs/2505.06120
19. S. Yao, N. Shinn, P. Razavi and K. Narasimhan. τ-bench: A benchmark for tool-agent-user interaction in real-world domains. arXiv:2406.12045, 2024. https://arxiv.org/abs/2406.12045
20. A. A. Tubis, A. Jodejko-Pietruczuk and T. Nowakowski. Use of augmented reality as a tool to support cargo handling operations at the CARGO air terminal. *Sensors*, 2024. https://doi.org/10.3390/s24041099
21. N. Suvittawat and D. W. Soh. Computer vision-based airport turnaround monitoring using YOLOv11, multi-object tracking, and motion-based passenger and baggage activity detection. *Sensors*, 2026. https://doi.org/10.3390/s26134231
22. A. Brooker and T. Hughes. Pre-Flight: A benchmark for evaluating large language models on aviation operational knowledge. arXiv:2607.01829, 2026 (preprint). https://arxiv.org/abs/2607.01829
