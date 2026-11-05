"""Illustrative local circuit after the scored apron lesson; no flight dynamics claim.

Positions use the existing kilometres-to-Unity-metres scale. A single aircraft
departs and returns, continuously; the runway and ground circuit are reserved.
Movement geometry remains rendering input. Only received reports reach answers.
"""
from backend.ground_routes import departure_path, rounded_path, timed_path, add_pavement
from backend.baggage_incident import add_baggage_incident

def add_flight_cycle(world, reservations, report):
    start=max(300.,max((r['end'] for r in reservations),default=0)+30)
    aircraft=world['aircraft'][0]
    push,taxi,turns=departure_path((-.045,.04),[(-.045,-.025),(-.28,-.025),(-.28,-.28),(-.8,-.28),(-.8,-.35)])
    departure=timed_path(push,start,end=start+34,reverse=True)+timed_path(taxi,start+34,end=start+145)[1:]
    lineup,lineup_turns=rounded_path([(-.8,-.35),(-.8,-.4),(-.74,-.4)],radius=.020)
    departure+=timed_path(lineup,start+185,end=start+197)
    aircraft['waypoints'].extend(departure)
    add_pavement(world,push);add_pavement(world,taxi,turns);add_pavement(world,lineup,lineup_turns)
    # Offset seconds, x/y/z in board units, gear retracted, reverse movement.
    path=[
        (175,-.74,0,-.4,False,False),(185,-.64,0,-.4,False,False),
        (195,-.34,0,-.4,False,False),(205,.16,0,-.4,False,False),
        (211,.58,0,-.4,False,False),(217,1.02,.035,-.4,False,False),
        (235,2.4,.25,-.4,True,False),(255,4,.5,-.4,True,False),
        (325,4,1,-3,True,False),(425,-4,1,-3,True,False),
        (505,-4,.21,-.4,True,False),(525,-3,.16,-.4,False,False),
        (545,-1.6,.08,-.4,False,False),(557,-.8,.015,-.4,False,False),
        (560,-.6,0,-.4,False,False),(563,-.42,0,-.4,False,False),(570,0,0,-.4,False,False),
        (580,.35,0,-.4,False,False),
    ]
    # Attitude differs from travel direction: flare is nose-up while descending.
    pitch={205:0,211:7,217:8,235:8,255:6,505:3,525:3,545:3,557:6,560:6,563:0}
    headings={325:180,425:270}
    aircraft['waypoints'].extend(dict(t=round(start+t+32,3),x=x,y=y,z=z,pitch=pitch.get(t,0),heading=headings.get(t,90),
        gearRetracted=gear,reverse=reverse) for t,x,y,z,gear,reverse in path)
    inbound,in_turns=rounded_path([(.35,-.4),(.5,-.4),(.5,-.34),(.5,-.10),(-.045,-.10),(-.045,.04)])
    arriving=timed_path(inbound,start+612,end=start+787);aircraft['waypoints'].extend(arriving[1:]);add_pavement(world,inbound,in_turns)
    exit_at=arriving[in_turns[0]['firstPoint']]['t']-start
    clear_at=next(p['t']-start for p in arriving if p['z']>=-.340001)
    stages=[(0,'pushback','Pushback'),(34,'taxi_out','Taxi to runway'),
        (145,'hold_short','Holding short'),(185,'line_up','Line up'),
        (207,'takeoff_roll','Takeoff roll'),(243,'rotation','Rotation / liftoff'),
        (249,'climb','Climb'),(287,'circuit','Local training circuit'),
        (537,'approach','Final approach'),(589,'flare','Flare'),
        (592,'landing_roll','Touchdown / rollout'),(exit_at,'runway_exit','Runway exit'),
        (clear_at,'taxi_in','Taxi to stand'),(787,'parked','Parked at Stand A')]
    aircraft['phases']=[dict(t=round(start+t,3),id=phase,label=label) for t,phase,label in stages]
    reservations.append(dict(aircraftId='A1',start=start,end=start+787,taxiStart=start+34,
                             speedMetresPerSecond=0,kind='local-flight-circuit'))
    world['runway']=dict(id='09/27',x=0,z=-.4,length=1.8,width=.045)
    world['runwayReservations']=[dict(aircraftId='A1',start=start+185,end=start+267,kind='departure'),
                                dict(aircraftId='A1',start=start+557,end=start+clear_at,kind='arrival')]
    world['flightShowcases']=[dict(id='departure',aircraftId='A1',start=start,end=start+287),
                             dict(id='arrival',aircraftId='A1',start=start+537,end=start+787)]
    world['flightTeachingWindows']=[dict(start=start+207,end=start+267),
                                   dict(start=start+557,end=start+clear_at)]
    report('A1circuitRoute','A1',start-1,'route','Stand A to Runway 09; local circuit; return to Stand A',
           'TRN101 will fly a local training circuit and return to Stand A.',0,'exercise-operations')
    world['incidents']=[dict(id='wildlife-runway',kind='wildlife',aircraftId='A1',
        start=start+143,end=start+173,x=-.775,y=.001,z=-.4)]
    world['flightTeachingWindows'].insert(0,dict(start=start+140,end=start+197))
    world['flightShowcases'].insert(0,dict(id='wildlife-detail',aircraftId='A1',start=start+140,end=start+178))
    world['demoQuestions']=[dict(id='wildlife-hold',at=start+151,aircraftId='A1',
        assistantQuestion='Why is TRN101 holding short of the runway?')]
    report('A1wildlifeHold','A1',start+145,'movement_condition','hold: birds reported on Runway 09; inspection pending',
        'TRN101 is held short of Runway 09. Airfield Operations reports a small flock on the western runway entry, crossing the centreline; species unconfirmed. No strike has been reported.',1,'airfield-operations')
    report('A1wildlifeInspect','A1',start+178,'movement_condition','hold: runway inspection complete; awaiting exercise controller release',
        'Airfield Operations reports the birds dispersed and the runway inspection complete. TRN101 remains held pending the exercise controller release.',2,'airfield-operations')
    report('A1circuitRelease' ,'A1',start+184,'movement_condition','exercise runway departure authorised',
           'The exercise controller authorises TRN101 to depart Runway 09 for the local circuit.',0,'exercise-tower')
    report('A1circuitArrival','A1',start+536,'movement_condition','exercise runway arrival authorised',
           'The exercise controller authorises the returning TRN101 arrival on Runway 09.',0,'exercise-tower')
    report('A1circuitComplete','A1',start+787,'movement_condition','circuit complete; no active runway authorisation',
           'TRN101 is back at Stand A. Its runway movement authorisation has ended.',1,'exercise-tower')
    for t,phase,label in stages:
        report('A1phase'+phase,'A1',start+t,'movement_status',label.lower(),
               'TRN101: '+label+'.',.5,'exercise-tower' if 165<=t<598 else 'ground-control')
    fire=start+822
    world['incidents'].append(dict(id='stand-engine-fire',kind='engine_fire',aircraftId='A1',
        start=fire,end=fire+65,x=-.051,y=.004,z=.041))
    world['flightShowcases'].append(dict(id='stand-incident',aircraftId='A1',start=fire-5,end=fire+95))
    world['flightTeachingWindows'].append(dict(start=fire-5,end=fire+95))
    world['demoQuestions'].append(dict(id='engine-fire-hold',at=fire+9,aircraftId='A1',
        assistantQuestion='Why is TRN101 held at Stand A?'))
    aircraft['phases'] += [dict(t=fire,id='engine_fire',label='Engine fire at Stand A'),
                           dict(t=fire+68,id='stand_closed',label='Stand A closed · inspection pending')]
    reservations.append(dict(aircraftId='A1',start=start+788,end=fire+110,kind='incident-response'))
    report('A1fireHold','A1',fire,'movement_condition','hold: engine fire reported at Stand A',
        'An engine fire is reported on TRN101 at Stand A. The aircraft is stopped, the stand is closed and the exercise emergency response is active. Cause unconfirmed.',2,'exercise-emergency')
    report('A1fireStatus','A1',fire,'movement_status','stopped at Stand A',
        'TRN101 remains stationary at Stand A during the emergency response.',2,'exercise-emergency')
    report('A1fireContained','A1',fire+65,'movement_condition','hold: fire contained; Stand A closed pending inspection',
        'The exercise response team reports the fire contained. Stand A stays closed pending inspection; TRN101 has no movement release.',3,'exercise-emergency')
    for aid in ('A2','A3'):
        report(aid+'emergencyHold',aid,fire,'movement_condition','hold: emergency response at Stand A',
            'Apron movement is held during the exercise emergency response at Stand A.',2,'ground-control')
        report(aid+'emergencyRelease',aid,fire+105,'movement_condition','exercise ground hold released; keep clear of closed Stand A',
            'Apron movement may resume outside closed Stand A. TRN101 remains held.',2,'ground-control')
    add_baggage_incident(world,reservations,report,fire+125)
    return start+787
