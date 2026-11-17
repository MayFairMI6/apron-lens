# C03 source-clock model

The driver abstraction uses one-second source ticks, a bounded scenario with
finite aircraft, resources and reports, and one representative frozen
checkpoint. Report event and receipt times are separate. Reports with later
event times can restrict an earlier release once the newer report is available.
The resource maps represent runway and stand ownership, with at most one flight
per resource. A fault closes the resource, and reopening requires vacancy and a
received release under the report rule.

A normal replay and accelerated replay map to the same source ticks. At each
accepted checkpoint compare the run/flight identifiers, set of eligible report
IDs, review phase and reservations at the same source time. The P01 trace
supplies reference boundaries at 60, 92, 95, 120, 150, 158 and 180 seconds.
A typed review freezes the clock, a failed review returns to its checkpoint, and
continuing from feedback resumes ticks. Bluebird observations remain outside
the airport report set.

This draft leaves scheduling nondeterministic. Progress assumes continued ticks
outside a checkpoint, eventual learner continuation, model response or failure,
and eligible recovery reports. None is guaranteed by the safety model.
Continuous motion, image perception, flight dynamics, and model semantics are
outside this abstraction. TLC model checking and mapping to the complete queue
trace are separate acceptance work.
