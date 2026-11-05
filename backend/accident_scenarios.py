"""Two fictional, externally timed incident-awareness demonstrations.

Contact geometry and crash attitude are authored illustrations, not dynamics or
evidence. The affected aircraft never resume movement after their incident.
"""
from backend.ground_routes import departure_path, rounded_path, timed_path, add_pavement


def add_accident_scenarios(world, reservations, report):
    start = max(r['end'] for r in reservations) + 35
    plane = world['aircraft'][1]
    old = plane['waypoints'][-1]
    push, taxi, turns = departure_path((old['x'], old['z']),
                                      [(old['x'], -.025), (.22, -.025)])
    plane['waypoints'] += timed_path(push, start, end=start+25)
    plane['waypoints'] += timed_path(taxi, start+25, end=start+56)[1:]
    add_pavement(world, push); add_pavement(world, taxi, turns)
    impact = start+56
    world['incidents'].append(dict(id='aircraft-vehicle-contact', kind='vehicle_collision',
        aircraftId='A2', start=impact-14, onset=impact, clearedAt=impact+50, end=3600,
        x=.221, y=.00015, z=-.0348))
    world['taxiPaths'].append(dict(id='contact-service-lane', kind='service', width=.012,
        points=[dict(x=.221, z=-.082), dict(x=.221, z=-.015)], turns=[]))
    world['flightShowcases'].append(dict(id='vehicle-collision', aircraftId='A2', start=impact-14, end=impact+80))
    world['flightTeachingWindows'].append(dict(start=impact-14, end=impact+80))
    reservations.append(dict(aircraftId='A2', start=start, end=impact+90,
                             kind='vehicle-contact-response'))
    plane.setdefault('phases', []).extend([
        dict(t=start,id='pushback',label='Pushback'),
        dict(t=start+25,id='taxi_out',label='Apron taxi'),
        dict(t=impact,id='vehicle_collision',label='Ground vehicle contact · stopped'),
        dict(t=impact+52,id='collision_recovery',label='Vehicle secured · aircraft held')])
    world['demoQuestions'].extend([
        dict(id='vehicle-contact-hold',at=impact+8,aircraftId='A2',
             assistantQuestion='Why has TRN102 stopped on the apron?'),
        dict(id='vehicle-contact-recovery',at=impact+57,aircraftId='A2',
             assistantQuestion='Can TRN102 move now that the vehicle is secured?')])
    report('A2contactRoute','A2',start-2,'route','apron taxi route outside closed Stand A',
           'TRN102 will taxi along the apron outside closed Stand A.',1,'ground-control')
    report('A2contactTaxi','A2',start+25,'movement_status','taxiing on the apron',
           'TRN102 has begun forward taxi after pushback.',1,'ground-control')
    report('A2contactHold','A2',impact,'movement_condition',
           'hold: aircraft contact with a ground vehicle on the apron',
           'Contact between TRN102 and a service vehicle is reported on the apron taxi route. '
           'The aircraft and vehicle are stopped. The cause, extent of damage and injury status are unconfirmed.',2,'airfield-operations')
    report('A2contactStopped','A2',impact,'movement_status','stopped after ground vehicle contact',
           'TRN102 remains stopped at the contact location. The affected route is isolated.',2,'ground-control')
    report('A2contactRecovery','A2',impact+50,'movement_condition',
           'hold: vehicle secured; aircraft inspection and movement release pending',
           'The response team reports the vehicle secured. TRN102 remains stopped pending aircraft inspection '
           'and a separate movement release; securing the vehicle is not an aircraft release.',2,'airfield-operations')
    report('A3contactRestriction','A3',impact,'movement_condition',
           'hold: local response to aircraft and vehicle contact',
           'TRN103 remains at its stand while the affected apron route is isolated.',2,'ground-control')
    report('A3contactRelease','A3',impact+84,'movement_condition',
           'exercise ground route released outside the isolated contact area',
           'TRN103 may use the separate western taxi route. TRN102 and its contact area remain held.',2,'ground-control')

    # A different aircraft completes an unbroken departure/circuit before the
    # emergency arrival. No teleport from a stand into an approach is required.
    start = impact+110
    plane = world['aircraft'][2]; old = plane['waypoints'][-1]
    push,taxi,turns = departure_path((old['x'],old['z']),
        [(old['x'],-.025),(-.28,-.025),(-.28,-.28),(-.8,-.28),(-.8,-.35)])
    plane['waypoints'] += timed_path(push,start,end=start+30)
    plane['waypoints'] += timed_path(taxi,start+30,end=start+150)[1:]
    lineup,lineup_turns = rounded_path([(-.8,-.35),(-.8,-.4),(-.74,-.4)],radius=.020)
    plane['waypoints'] += timed_path(lineup,start+160,end=start+172)
    add_pavement(world,push);add_pavement(world,taxi,turns);add_pavement(world,lineup,lineup_turns)
    path=[(182,-.64,0,-.4),(192,-.34,0,-.4),(202,.16,0,-.4),
          (208,.58,0,-.4),(214,1.02,.035,-.4),(234,2.4,.25,-.4),(254,4,.5,-.4),
          (300,3,.8,-3),(355,-3,.8,-3),(390,-4,.21,-.4),(410,-2.7,.13,-.4),
          (430,-1.3,.055,-.4),(440,-.7,.010,-.4),(442,-.57,0,-.4),
          (443,-.505,.003,-.4),(445,-.39,0,-.4),(452,-.05,0,-.4),
          (465,.30,0,-.4),(480,.42,0,-.4)]
    for t,x,y,z in path:
        plane['waypoints'].append(dict(t=start+t,x=x,y=y,z=z,heading={300:180,355:270}.get(t,90),
            pitch=7 if 208<=t<=234 else 5 if 390<=t<=443 else -2 if t>=445 else 0,
            roll=-3 if t>=445 else 4 if t==443 else 0,
            bodySink=.0038 if t>=452 else .001 if t>=445 else 0,
            gearRetracted=234<=t<390 or t>=445,reverse=False))
    contact=start+442
    plane['phases']=[dict(t=start+t,id=ident,label=label) for t,ident,label in [
        (0,'pushback','Pushback'),(30,'taxi_out','Taxi to runway'),(150,'hold_short','Holding short'),
        (160,'line_up','Line up'),(172,'takeoff_roll','Takeoff roll'),(208,'rotation','Rotation / liftoff'),
        (214,'climb','Climb'),(254,'circuit','Local training circuit'),
        (410,'emergency_approach','Emergency approach'),(442,'crash_landing','Crash landing · runway closed'),
        (445,'damaged_rollout','Landing gear collapse · decelerating'),
        (480,'disabled_runway','Aircraft disabled on runway'),(502,'response_ongoing','Fire contained · runway closed')]]
    reservations.append(dict(aircraftId='A3',start=start,end=3599,kind='emergency-flight-and-runway-closure'))
    world['runwayReservations'].extend([
        dict(aircraftId='A3',start=start+160,end=start+270,kind='departure'),
        dict(aircraftId='A3',start=start+410,end=3600,kind='emergency-arrival-and-closure')])
    world['incidents'].append(dict(id='runway-crash-landing',kind='crash_landing',aircraftId='A3',
        start=start+410,onset=contact,clearedAt=contact+55,end=3600,x=.42,y=.00015,z=-.4))
    world['flightShowcases'].extend([
        dict(id='second-departure',aircraftId='A3',start=start,end=start+270),
        dict(id='crash-landing',aircraftId='A3',start=start+410,end=contact+100)])
    world['flightTeachingWindows'].append(dict(start=start+410,end=contact+100))
    world['demoQuestions'].extend([
        dict(id='crash-runway-closure',at=contact+10,aircraftId='A3',
             assistantQuestion='Why is Runway 09 closed for TRN103?'),
        dict(id='crash-contained-closure',at=contact+62,aircraftId='A3',
             assistantQuestion='Has the runway reopened after the fire was contained?')])
    report('A3circuitRoute','A3',start-1,'route','western taxi route; local circuit; return to Runway 09',
           'TRN103 uses the separate western route for a local circuit and return. The TRN102 contact area stays isolated.',0,'exercise-operations')
    report('A3departure','A3',start+159,'movement_condition','exercise runway departure authorised',
           'The exercise tower authorises TRN103 to depart Runway 09 for its local circuit.',0,'exercise-tower')
    report('A3emergencyApproach','A3',start+409,'movement_condition','emergency arrival; runway reserved for TRN103',
           'TRN103 reports an emergency return. Runway 09 is reserved for this arrival. The cause and landing outcome are not yet confirmed.',1,'exercise-tower')
    report('A3crashClosure','A3',contact,'movement_condition',
           'Runway 09 closed: crash landing reported; emergency response active',
           'A crash landing involving TRN103 is reported on Runway 09. The runway is closed and the exercise emergency response is active. '
           'The cause, injuries and evacuation status are unconfirmed.',2,'exercise-emergency')
    report('A3gearDamage','A3',contact+6,'movement_status','landing gear collapse reported; damaged rollout',
           'The response report confirms a landing gear collapse during the damaged rollout of TRN103.',2,'exercise-emergency')
    report('A3disabled','A3',contact+38,'movement_status','disabled on Runway 09',
           'TRN103 is stopped and disabled on Runway 09. It has no movement release.',1,'exercise-emergency')
    report('A3fireContained','A3',contact+55,'movement_condition',
           'Runway 09 closed: fire contained; aircraft recovery and inspection pending',
           'The response team reports the post-landing fire contained. Runway 09 remains closed for aircraft recovery '
           'and inspection. No reopening has been reported.',3,'exercise-emergency')
    # Disabled aircraft and the closed runway end the active movement sequence.
    world['accidentSequenceEndsMovement']=True
