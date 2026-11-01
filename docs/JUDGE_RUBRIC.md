# LLM judge rubric (`judge-rubric-v1`)

Written on 1 November 2026, before any judged output was produced or read. Once
a judge run has used it, it changes only under a new version number, and
earlier judge results keep the version they used.

## Role

The judge is a secondary metric. Correctness (referent, required citations,
status, changes) stays with the deterministic scores
(`backend/conversation/scoring.py`); the judge never overrides them. It rates
what the labels can't: how useful and clear an answer is to a stand
coordinator.

## What the judge sees

For each turn, in random order across systems and conditions, with no system,
model or condition name:

- the user's question and the replay time;
- the conversation so far in that family: each earlier turn's question, replay
  time and displayed answer, as the same system gave them. On a follow-up
  ("has anything changed since you answered?"), this is how the judge knows
  the previous answer and its cutoff, and so which facts arrived since then and
  whether "no change" is right;
- the facts received for the referent flight by that time, with their status,
  event and receipt times, and, for a follow-up, the facts that are new or
  changed since the previous answer (the same `changed_facts` set the
  validator checks);
- when the user was away, the time interval(s);
- the answer as the app displays it: the checked claims, the unknowns and the
  status, plus the model's interpretation text, which is shown to the user as
  unverified.

Withheld turns aren't judged: the app shows no model answer for them, and the
deterministic scores already count them.

## Dimensions

Each dimension scores 1–4 or N/A, with a one-sentence reason.

1. **Usefulness:** does the answer give the coordinator what the question asks
   for, with the most important fact first?
   - 4 = direct and complete;
   - 3 = complete but buried or padded;
   - 2 = partial;
   - 1 = doesn't answer the question.
2. **Clarity:** is it short, unambiguous, and clear about status (superseded,
   conflicting, scheduled, expired)?
   - 4 = immediately clear;
   - 3 = clear with effort;
   - 2 = confusing in places;
   - 1 = misleading.
3. **Clarifying question** (only when the status is clarify, otherwise N/A):
   does it name the candidate aircraft or flights and ask one question that
   resolves the ambiguity?
   - 4 = names the candidates and asks one decisive question;
   - 3 = decisive but vague about the candidates;
   - 2 = asks, but the reply wouldn't resolve it;
   - 1 = no usable question.
4. **Change explanation** (only when something changed since the previous
   answer, or while the user was away; otherwise N/A): does it say what
   changed and when, and separate what the user missed from what they watched?
   - 4 = all of that;
   - 3 = says what changed, but not when or which;
   - 2 = mentions a change vaguely;
   - 1 = misses or misstates it.
5. **Faithful interpretation:** does the unverified interpretation text stay
   within the listed facts?
   - 4 = nothing beyond the facts;
   - 3 = harmless inference, clearly marked as such;
   - 2 = an unsupported claim;
   - 1 = contradicts a fact.

Milestone 2 adds a sixth dimension for proactive change notices (timely, short,
not alarming) in `judge-rubric-v2`, written before that milestone's judge runs.

## Judge and calibration

- **The judge** comes from a model family other than every system it judges.
  That excludes Qwen and Gemma; it also excludes Claude, because a Claude
  session wrote the held-out sets. A hosted model needs the user's approval and
  a cost estimate (`--estimate-only`) before any call.
- **Settings:** greedy decoding or the provider's lowest temperature; the
  rubric text above is sent verbatim; the output is JSON, with one score and
  one reason per dimension.
- **Calibration:** the user rates a stratified sample of about 30 judged
  answers with this rubric, without seeing the judge's scores. Agreement is
  reported per dimension as quadratic-weighted Cohen's kappa. A dimension's
  judge scores are reported as results only when kappa is at least 0.6; below
  that, they're reported as not reliable.
- **Reporting:** the mean score per system and condition, with a family-level
  bootstrap interval, next to the deterministic scores and never merged into
  them.
