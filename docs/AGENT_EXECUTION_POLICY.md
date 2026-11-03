# Agent model and reasoning policy

The user requested proportionate effort on 3 November 2026. Do not give every
agent the coordinator's model or reasoning setting by inheritance.

| Work | Default | Escalation |
|---|---|---|
| Milestone placement, acceptance bookkeeping, source/hash checks | Sol, medium | High only for a specific unresolved evidence conflict |
| Strategic compaction and handoffs | Sol, medium | High only when priorities or evidence cannot be reconciled |
| Routine implementation, tests and document updates | Sol, medium | High for a demonstrated difficult defect |
| Scenery reference gathering and ordinary placement checks | Sol, medium | High for complex geometry or inconsistent reference evidence |
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
