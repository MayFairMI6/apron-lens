# Matched local Qwen reasoning experiment

The candidate did not pass the initial six-case acceptance gate. The source was
frozen at `f12c541`; the exact prompt/parser was the unchanged single-pass v6
control. Both arms used Qwen3.5-9B revision
`c202236235762e1c871ad0ccb60c8ee5ba337b9a`, MPS float16 eager inference,
greedy decoding, and the same source-only learner inputs. The only arm difference
was the thinking template flag. Both received the same explicit chat-end EOS
policy, startup allowance and 1,000-token/55-second learner-request limits.

| Outcome | Reasoning off | Reasoning on |
|---|---:|---:|
| Planned questions | 6 | 6 |
| Attempted questions | 6 | 1 |
| Complete, structurally valid interpretations | 6 | 0 |
| Independently faithful complete interpretations | 4 | 0 available to assess |
| Unattempted after worker failure | 0 | 5 |

Off-mode response times were 9.620–14.498 seconds. The readiness answer added
confirmation absent from the learner's words. The corrected-aircraft answer
failed to link the replacement and incorrectly declared the following pronoun
unresolved. The other four initial cases preserved their required meanings.
These are exposed development controls, not held-out accuracy estimates.

On-mode startup completed, using 153 generated tokens including its reasoning
and message boundary. Its first learner request timed out at 55.095 seconds.
The worker was stopped before a generation result was available, so there are
no generated token IDs or final answer available; actual usage is unknown.
The remaining five questions were not attempted. Recovery was started and
cancelled when the runner closed the owner; no question was retried. This is a
practical delivery failure under this configuration, not evidence that its
unobserved interpretation was semantically wrong.

The version 1 transport/startup failures remain unchanged in the sibling
`qwen-reasoning-ablation-v1` directory. Version 2 stops generation at the verified
chat-end token rather than stripping it from a returned answer. Actual inputs,
token IDs and hashes, settings, raw available outputs, worker events, source
snapshots and run log are retained here. The independent all-23-obligation audit
is in `docs/course/TYPED_QWEN_FRAME_ACCEPTANCE.md`.

The implementation passed 644 local tests and the backbone boundary check;
GitHub Checks passed for source `f12c541`. Engineering checks do not override the
failed meaning/delivery gate. Neither arm is approved for report checking,
credit assignment or deployment. The twelve contrasts, full development
qualification and subsequent fresh/native acceptance remain unrun for this
candidate. Existing production behavior, historical results and video remain
unchanged.
