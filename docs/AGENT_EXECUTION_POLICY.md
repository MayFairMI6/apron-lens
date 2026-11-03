# Agent model and reasoning policy

The user requested proportionate effort on 3 November 2026. Do not give every
agent the coordinator's model or reasoning setting by inheritance.

| Work | Default | Escalation |
|---|---|---|
| Milestone placement, acceptance bookkeeping, source/hash checks | Sol, medium | High only for a specific unresolved evidence conflict |
| Strategic compaction and handoffs | Sol, medium | High only when priorities or evidence cannot be reconciled |
| Routine implementation, tests and document updates | Sol, medium | High for a demonstrated difficult defect |
| Text-only reference gathering and nonvisual code checks | Sol, medium | High for a concrete difficult defect |
| Image, screenshot, rendered scenery, UI layout or spatial visual reasoning | Astra, low for straightforward checks; medium for involved reasoning | Higher only for a concrete unresolved visual problem |
| Visual evidence handoff during strategic compaction | Astra, low or medium according to complexity | Preserve images and uncertainty; do not substitute unverified prose |
| Training/runtime debugging | Sol, medium initially | Sol high or Astra high for a difficult numerical/architectural failure |
| Final scientific/semantic result review | Sol, high for the bounded review | Astra high if the interpretation remains materially disputed |

No role defaults to extra-high effort. A larger context or expensive model is not
itself evidence of a better decision. Keep independent reviews and empirical tests;
reducing agent effort does not relax acceptance criteria.

For this tool surface, the Sol runtime identifier is `gpt-6.1-sol`; choose
`reasoning_effort="medium"` for routine roles and `fork_turns="none"` when overriding
the model. Supply a compact task brief, exact source paths, scope and acceptance
gates. Use `gpt-6-astra` only when its deeper review is justified by the actual task.
These are runtime tool identifiers, not a claim about public API model names.

An existing agent cannot be relabelled as having a different model. Finish or
interrupt its active task at a safe boundary, then create a replacement with the
explicit settings and durable handoff. Do not start idle agents just to change their
settings. Avoid duplicate reviewers or simultaneous edits to an owned file.

The coordinator should record any escalation and its concrete reason. Restore the
routine default for subsequent work rather than carrying the escalation forward.

## Visual work and compaction

The user assigns all work requiring visual reasoning to Astra. Use runtime
`gpt-6-astra` with `reasoning_effort="low"` (the requested light setting) for simple
visual checks, or `medium` for multiple views, geometry, UI relationships or
ambiguous evidence. Pure textual bookkeeping or code changes that do not require
image interpretation may remain on Sol; the visual interpretation/review belongs
to Astra. Image/video generation tools retain their own tool-specific model setup.

Strategic compaction is normally a text handoff. When the active task relies on
visual evidence, the custodian obtains a bounded Astra visual review and preserves:

- Exact local artifact paths and, where useful, hashes or frame/time identifiers.
- What the images actually establish, distinct from inferred or unverified claims.
- Unresolved defects with the relevant view, region and reproduction conditions.
- The smallest useful image set and the exact visual resume step.

Do not re-open every historical screenshot or launch a visual agent for text-only
work. Do not claim the platform's automatic context compaction includes images or
that a text summary preserves all visual detail. A future visual task must inspect
the referenced images when needed. This is a project handoff workflow, not an
override of platform context management.
