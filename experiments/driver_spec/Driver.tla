---- MODULE Driver ----
EXTENDS Naturals, FiniteSets, TLC
CONSTANTS Flights, Resources, Reports, Horizon, Checkpoint, ReviewFlight, NoOwner
VARIABLES now, phase, currentReview, reportIds, occupied, reservations, closedAt

vars == <<now, phase, currentReview, reportIds, occupied, reservations, closedAt>>
At(t) == {r.id : r \in {item \in Reports : item.receipt <= t}}
ReleaseAvailable(resource, flight) ==
    \E r \in Reports:
        /\ r.id \in reportIds
        /\ r.kind = "release"
        /\ r.resource = resource
        /\ r.flight = flight
        /\ IF closedAt[resource] = NoOwner THEN TRUE ELSE r.event >= closedAt[resource]
        /\ \neg (\E other \in Reports:
            /\ other.id \in reportIds
            /\ other.resource = resource
            /\ other.event > r.event
            /\ other.kind = "restriction")

Init ==
    /\ now = 0
    /\ phase = "practice"
    /\ currentReview = NoOwner
    /\ reportIds = At(0)
    /\ occupied = [r \in Resources |-> NoOwner]
    /\ reservations = [r \in Resources |-> NoOwner]
    /\ closedAt = [r \in Resources |-> NoOwner]

Tick ==
    /\ phase = "practice"
    /\ now < Horizon
    /\ now' = now + 1
    /\ reportIds' = At(now')
    /\ phase' = IF now' = Checkpoint THEN "checkpoint"
                 ELSE IF now' = Horizon THEN "debrief" ELSE phase
    /\ UNCHANGED <<currentReview, occupied, reservations, closedAt>>

RequestReview ==
    /\ phase = "checkpoint"
    /\ phase' = "reviewing"
    /\ currentReview' = ReviewFlight
    /\ UNCHANGED <<now, reportIds, occupied, reservations, closedAt>>

ResolveReview(success) ==
    /\ phase = "reviewing"
    /\ phase' = IF success THEN "feedback" ELSE "checkpoint"
    /\ currentReview' = NoOwner
    /\ UNCHANGED <<now, reportIds, occupied, reservations, closedAt>>

Continue ==
    /\ phase = "feedback"
    /\ phase' = "practice"
    /\ UNCHANGED <<now, currentReview, reportIds, occupied, reservations, closedAt>>

Reserve(resource, flight) ==
    /\ phase = "practice"
    /\ closedAt[resource] = NoOwner
    /\ reservations[resource] = NoOwner
    /\ occupied[resource] = NoOwner
    /\ ReleaseAvailable(resource, flight)
    /\ reservations' = [reservations EXCEPT ![resource] = flight]
    /\ UNCHANGED <<now, phase, currentReview, reportIds, occupied, closedAt>>

Enter(resource, flight) ==
    /\ phase = "practice"
    /\ closedAt[resource] = NoOwner
    /\ occupied[resource] = NoOwner
    /\ reservations[resource] = flight
    /\ ReleaseAvailable(resource, flight)
    /\ occupied' = [occupied EXCEPT ![resource] = flight]
    /\ UNCHANGED <<now, phase, currentReview, reportIds, reservations, closedAt>>

Vacate(resource, flight) ==
    /\ phase = "practice"
    /\ occupied[resource] = flight
    /\ occupied' = [occupied EXCEPT ![resource] = NoOwner]
    /\ reservations' = [reservations EXCEPT ![resource] = NoOwner]
    /\ UNCHANGED <<now, phase, currentReview, reportIds, closedAt>>

Incident(resource) ==
    /\ phase = "practice"
    /\ closedAt[resource] = NoOwner
    /\ closedAt' = [closedAt EXCEPT ![resource] = now]
    /\ reservations' = [reservations EXCEPT ![resource] = occupied[resource]]
    /\ UNCHANGED <<now, phase, currentReview, reportIds, occupied>>

Reopen(resource) ==
    /\ phase = "practice"
    /\ closedAt[resource] # NoOwner
    /\ occupied[resource] = NoOwner
    /\ \E f \in Flights: ReleaseAvailable(resource, f)
    /\ closedAt' = [closedAt EXCEPT ![resource] = NoOwner]
    /\ UNCHANGED <<now, phase, currentReview, reportIds, occupied, reservations>>

Next ==
    \/ Tick
    \/ RequestReview
    \/ ResolveReview(TRUE)
    \/ ResolveReview(FALSE)
    \/ Continue
    \/ \E resource \in Resources, flight \in Flights:
        Reserve(resource, flight) \/ Enter(resource, flight) \/ Vacate(resource, flight)
    \/ \E resource \in Resources: Incident(resource) \/ Reopen(resource)

Spec == Init /\ [][Next]_vars
Consistent ==
    /\ now \in 0..Horizon
    /\ reportIds = At(now)
    /\ \A resource \in Resources:
        occupied[resource] = NoOwner \/ occupied[resource] = reservations[resource]
    /\ ((phase = "reviewing") <=> (currentReview = ReviewFlight))
====
