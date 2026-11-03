"""Independent four-type incident illustrations; authored kinematics, not flight physics."""
import copy
import math
import random
from backend.runway_scenarios import geography, project

FLEET_DEMONSTRATIONS=('fleet_a320_birds','fleet_b737_rejected_takeoff','fleet_b787_priority_landing','fleet_a380_go_around')
TITLES=dict(zip(FLEET_DEMONSTRATIONS,('Birds before departure','A rejected takeoff','A priority landing','A runway-occupied go-around')))
OBJECTIVES=dict(zip(FLEET_DEMONSTRATIONS,(
    'Separate dispersal, inspection and the later departure release.',
    'Distinguish the reported airspeed concern, stopped aircraft and unconfirmed runway release.',
    'Follow a reported concern through landing, inspection and recovery without inventing a diagnosis.',
    'Identify runway occupancy, the go-around and the next approach that remains unconfirmed.')))
TYPES=('a320_200','b737_800','b787_8','a380_800')
# Dimensions and gear stations from manufacturer airport-planning drawings; not performance data.
DIMENSIONS={
 'a320_200':dict(length=37.57,span=35.80,nose=17.71,tail=19.86,wheelbase=12.64,track=7.59),
 'b737_800':dict(length=39.47,span=35.79,nose=19.69,tail=19.78,wheelbase=15.60,track=5.72),
 'b787_8':dict(length=56.72,span=60.12,nose=28.19,tail=28.53,wheelbase=22.78,track=9.80),
 'a380_800':dict(length=72.73,span=79.75,nose=36.85,tail=35.88,wheelbase=31.88,track=14.34),
}
# Factual reference values transcribed from NATS AIRAC 29 October 2026,
# EGLL AD 2.12/13 and AD 2 EGLL 8-4 (chart change 7/26, aeronautical info 20 Apr 2026).
# The chart's RDH is not a main-wheel height. This display applies it to the
# visual trajectory reference point; it does not model receiver/antenna geometry.
PROCEDURE_09R=dict(thresholdLatitude=51+27/60+53.25/3600,
 thresholdLongitude=-(28/60+56.33/3600),trueBearing=89.68,
 thresholdElevationFeet=75.3,glideDegrees=3.,referenceDatumHeightFeet=50.,
 missedApproachAltitudeFeet=3000.,airac='2026-10-29',chart='AD 2 EGLL 8-4',
 source='https://www.aurora.nats.co.uk/htmlAIP/Publications/2026-10-29-AIRAC/graphics/505230.pdf',
 aerodromeSource='https://www.aurora.nats.co.uk/htmlAIP/Publications/2026-10-29-AIRAC/html/eAIP/EG-AD-2.EGLL-en-GB.html#EGLL-AD-2.12')
PARKING=[('osm-way-105366846',-.4,.13),('osm-way-105452950',-.47,-.9),('osm-way-105452950',.03,-.85)]

def build_fleet(seed,exercise):
    if exercise not in FLEET_DEMONSTRATIONS:raise ValueError('Unknown fleet demonstration')
    rng=random.Random(seed);jitter=rng.randrange(5);geo=geography()
    threshold_x,threshold_z=project(PROCEDURE_09R['thresholdLongitude'],PROCEDURE_09R['thresholdLatitude'])
    west=dict(x=threshold_x,z=threshold_z)
    yaw=PROCEDURE_09R['trueBearing'];ux=math.sin(math.radians(yaw));uz=math.cos(math.radians(yaw))
    def wp(t,d,y=0,pitch=0,gear=False):
        return dict(t=round(t,4),x=west['x']+ux*d/1000,z=west['z']+uz*d/1000,y=y/1000,heading=yaw,pitch=pitch,roll=0,gearRetracted=gear)
    active=TYPES[FLEET_DEMONSTRATIONS.index(exercise)]
    ordered=[active]+[t for t in TYPES if t!=active]
    world=dict(scenarioId=f'FLEET-{exercise}-{seed}',duration=3600,targetWidth=.7,livery='indexed',clockWhileUntracked='runs',
        trainingProfile=exercise,trainingRole='controller_awareness',trainingRoleLabel='Airfield operations',trainingObjective=OBJECTIVES[exercise],
        assistantQuestionLabels=['Latest report','What changed?'],assistantQuestions=['What is the latest reported movement for this flight?','What changed for this flight?'],
        geography=geo,aircraft=[],events=[],visualProps=[],groundVehicles=[],incidents=[],demoQuestions=[],flightShowcases=[],flightTeachingWindows=[],taxiPaths=[],
        provenance=dict(kind='authored-type-specific-illustration',sources=['https://mediaassets.airbus.com/pm_38_916_916266-iujedqawwy.pdf?fileName=aca32001-jul-2026-2.pdf','https://www.boeing.com/content/dam/boeing/v2/airports/acaps/737NG_REV_C.pdf','https://www.boeing.com/content/dam/boeing/v2/airports/acaps/787_ACAP_Rev_Q.pdf','https://www.aircraft.airbus.com/sites/g/files/jlcbta126/files/2025-12/AC_A380_20251201.pdf'],limitations='Type dimensions are referenced; flight speeds, timing, incidents and paths are authored training illustrations. No aircraft-system simulation, certified performance, recovered flight trajectory or type-specific defect probability is claimed.'))
    world['provenance']['procedureReference']=copy.deepcopy(PROCEDURE_09R)
    world['provenance']['limitations'] += ' Final-approach slope, threshold reference and initial straight-ahead missed-approach altitude use published factual values. The chart reference datum is approximated at the visual trajectory root, not a modelled ILS antenna. Speeds, flare, climb transition and incident timing remain authored. No SID, radio-failure turn or routing beyond the as-directed boundary is reproduced.'
    for i,kind in enumerate(ordered):
        if i:
            apron,x,z=PARKING[i-1];points=[dict(t=t,x=x,z=z,y=0,heading=0,pitch=0,roll=0,gearRetracted=False) for t in (0,3600)]
        else:apron=None;points=[]
        world['aircraft'].append(dict(id=f'A{i+1}',flightInstance=f'TRN10{i+1}',aircraftType=kind,surfaceHeightMetres=.2 if i==0 else .05,preciseHeading=True,hidden=False,
            waypoints=points,phases=[] if i==0 else [dict(t=0,id='parked',label='Parked')],parkingApron=apron))
    last={}
    def report(t,prop,value,message,aid='A1',lag=1):
        fact=dict(property=prop,value=value);key=(aid,prop);eid=f'F{len(world["events"])+1:03d}'
        if key in last:fact['supersedes']=[last[key]]
        last[key]=eid+':'+prop
        world['events'].append(dict(id=eid,aircraftId=aid,flightInstance='TRN10'+aid[1:],source='exercise-operations',eventTime=float(t),receiptTime=float(t+lag),facts=[fact],message=message))
    a=world['aircraft'][0]
    def phase(t,key,label):a['phases'].append(dict(t=t,id=key,label=label))
    def cue(t,key,q):world['demoQuestions'].append(dict(id=key,at=t,aircraftId='A1',assistantQuestion=q))
    def sample(end,fn):return [fn(i*.5) for i in range(int(end*2)+1)]
    if exercise=='fleet_a320_birds':
        depart=110+jitter;rotate=depart+36;liftoff=depart+40
        def motion(t):
            if t<=depart:return wp(t,80)
            if t<=liftoff:
                u=t-depart;return wp(t,80+.9*u*u,pitch=8*max(0,(u-36)/4))
            u=t-liftoff;rise=3*u*u/6 if u<6 else 6*(u-3)
            return wp(t,1520+72*u,y=1200*math.tanh(rise/1200),pitch=3+5/math.cosh(min(rise/1200,20))**2,gear=u>=10)
        points=sample(liftoff+100,motion);points.append(motion(3600))
        phase(0,'departure_hold','Departure held');phase(depart,'takeoff_roll','Takeoff roll');phase(rotate,'rotation','Rotation');phase(liftoff,'climb','Climbing');phase(liftoff+100,'outside_area','Beyond exercise area')
        report(0,'movement_condition','hold: birds reported near departure path','TRN101 is held for birds reported near the departure path. No strike is reported.',lag=0)
        report(60,'movement_condition','hold: birds dispersed; inspection pending','Birds have dispersed. TRN101 remains held pending inspection.')
        report(85,'movement_condition','hold: inspection complete; separate departure release awaited','Inspection is complete. Departure release for TRN101 is still awaited.')
        report(100,'movement_condition','exercise departure release received','The exercise controller releases TRN101 for departure.')
        report(depart,'movement_status','takeoff roll','TRN101 has begun its takeoff roll.')
        report(liftoff,'movement_status','airborne and climbing','TRN101 is airborne and climbing. No strike or damage is reported.')
        cue(45,'bird-hold','Why is TRN101 held?');cue(90,'inspection','Does inspection completion release TRN101?');cue(liftoff+12,'departure','What is the latest reported movement for TRN101?')
        bird=wp(0,350)
        world['incidents']=[dict(id='fleet-birds',kind='wildlife',aircraftId='A1',start=0,end=60,x=bird['x'],y=.001,z=bird['z'])]
        world['flightTeachingWindows']=[dict(start=30,end=65),dict(start=depart-3,end=liftoff+20)]
        end_res=liftoff+15
    elif exercise=='fleet_b737_rejected_takeoff':
        depart=60+jitter;reject=depart+35;stop=reject+22
        def motion(t):
            if t<=depart:return wp(t,80)
            if t<=reject:
                u=t-depart;return wp(t,80+65*u*u/70)
            u=min(t-reject,22);return wp(t,1217.5+65*u-65*u*u/44)
        points=sample(stop,motion);points.append(motion(3600))
        phase(0,'lined_up','Lined up');phase(depart,'takeoff_roll','Takeoff roll');phase(reject,'rejected_takeoff','Rejected takeoff');phase(stop,'stopped','Stopped on runway')
        report(0,'route','Runway 09R','TRN101 is lined up on Runway 09R.',lag=0)
        report(depart,'movement_status','takeoff roll','TRN101 has begun its takeoff roll.')
        report(reject,'movement_condition','takeoff rejected: unreliable airspeed reported; cause unconfirmed','The crew reports unreliable airspeed and rejects takeoff; the cause remains unconfirmed.')
        report(stop,'movement_status','stopped on Runway 09R','TRN101 has stopped on Runway 09R.')
        report(stop+2,'movement_condition','hold: runway occupied; aircraft assessment pending','TRN101 remains on the runway pending assessment. No runway release is reported.')
        report(300,'movement_condition','hold: assessment continues; recovery and release unconfirmed','Assessment continues; recovery completion and runway release remain unconfirmed.')
        cue(reject+5,'rejection','Why did TRN101 reject takeoff?');cue(stop+8,'stopped','What is the latest reported movement for TRN101?');cue(310,'release','Is the runway released for TRN101?')
        world['flightTeachingWindows']=[dict(start=depart-3,end=stop+15)];end_res=3600
    elif exercise=='fleet_b787_priority_landing':
        touchdown=180+jitter;stop=touchdown+48;v=72.;flare=5.;slope=math.tan(math.radians(PROCEDURE_09R['glideDegrees']))
        rdh=PROCEDURE_09R['referenceDatumHeightFeet']*.3048;touchdown_distance=v*flare
        def motion(t):
            if t<touchdown:
                remaining=touchdown-t;d=touchdown_distance-v*remaining
                if remaining>=flare:y=rdh-d*slope;pitch=3
                else:
                    # Authored Hermite flare: continuous height/descent at the
                    # threshold, zero vertical speed at touchdown.
                    q=1-remaining/flare
                    y=rdh*(2*q**3-3*q*q+1)-v*slope*flare*(q**3-2*q*q+q);pitch=3+3*q
                return wp(t,d,y=y,pitch=pitch)
            u=min(t-touchdown,48);return wp(t,touchdown_distance+v*u-v*u*u/96,pitch=6*max(0,1-u/8))
        points=sample(stop,motion);points.append(motion(3600))
        phase(0,'approach','Priority approach');phase(touchdown-5,'flare','Flare');phase(touchdown,'landing_roll','Touchdown and rollout');phase(stop,'stopped','Stopped for inspection')
        report(0,'movement_condition','priority arrival: crew reported hydraulic concern; diagnosis unconfirmed','TRN101 reports a hydraulic concern and requests priority landing. The diagnosis and affected system are unconfirmed.',lag=0)
        report(50,'movement_condition','exercise priority landing authorised; hydraulic concern reported','The exercise controller authorises priority landing for TRN101; the reported hydraulic concern remains under assessment.')
        report(touchdown,'movement_status','landed; rolling out on Runway 09R','TRN101 has landed and is rolling out on Runway 09R.')
        report(stop,'movement_status','stopped on Runway 09R','TRN101 is stopped on the runway for inspection.')
        report(stop+2,'movement_condition','hold: inspection pending; runway occupied','Inspection is pending and the runway remains occupied by TRN101.')
        report(stop+70,'movement_condition','hold: inspection underway; recovery requested; runway release unconfirmed','Inspection is underway and recovery assistance has been requested. No completed recovery or runway release is reported.')
        cue(70,'priority','Why is TRN101 receiving priority?');cue(stop+10,'arrival-stop','What is the latest reported movement for TRN101?');cue(stop+80,'recovery','Is recovery complete and the runway released for TRN101?')
        world['flightTeachingWindows']=[dict(start=touchdown-15,end=stop+12)];end_res=3600
    else:
        transition=100+jitter;v=75.;minimum=55.;rate=4.;climb=7.;blend=8.
        ceiling=(PROCEDURE_09R['missedApproachAltitudeFeet']-PROCEDURE_09R['thresholdElevationFeet'])*.3048
        blend_height=minimum-rate*blend+(climb+rate)*blend/2
        level_start=blend+(ceiling-blend_height-100)/climb;level_duration=200/climb
        route_end=transition+level_start+level_duration
        def motion(t):
            u=t-transition;d=-650+v*u
            if u<0:y=minimum-rate*u;pitch=3
            elif u<blend:
                y=minimum-rate*u+(climb+rate)*u*u/(2*blend);pitch=3+7*u/blend
            elif u<level_start:y=blend_height+climb*(u-blend);pitch=10
            else:
                q=min(1.,(u-level_start)/level_duration)
                y=ceiling-100+climb*level_duration*(q-q*q/2);pitch=10-7*q
            # Chart-derived showcase ends at 'as directed'; later off-scene
            # straight motion is only continuity geometry, not a published route.
            return wp(t,d,y=y,pitch=pitch,gear=u>=20)
        points=sample(math.ceil(route_end*2)/2,motion);points.append(motion(3600))
        b=world['aircraft'][1];b['aircraftType']='b737_800'
        # Reorder parked types so each of the four families occurs exactly once.
        world['aircraft'][2]['aircraftType']='a320_200';world['aircraft'][3]['aircraftType']='b787_8'
        b['waypoints']=[wp(t,2400) for t in (0,3600)];b['surfaceHeightMetres']=.2;b['parkingApron']=None;b['phases']=[dict(t=0,id='runway_occupied',label='Stopped on runway')]
        phase(0,'approach','Approach');phase(transition,'go_around','Go-around');phase(transition+blend,'climb','Climbing away');phase(route_end,'outside_area','Beyond exercise area')
        report(0,'route','approach to Runway 09R','TRN101 is approaching Runway 09R.',lag=0)
        report(transition-20,'movement_status','stopped on Runway 09R','TRN102 remains stopped on Runway 09R.',aid='A2')
        report(transition,'movement_condition','go-around: Runway 09R occupied by TRN102','TRN101 goes around because TRN102 has not vacated Runway 09R.')
        report(transition+blend,'movement_status','climbing away after go-around','TRN101 is climbing away; no landing has occurred.')
        report(300,'movement_condition','runway still occupied; another approach unconfirmed','Runway 09R remains occupied. Another approach or landing for TRN101 is not confirmed.')
        cue(transition+4,'go-around','Why is TRN101 going around?');cue(transition+65,'climb','What is the latest reported movement for TRN101?');cue(310,'next','Is another approach confirmed for TRN101?')
        world['flightTeachingWindows']=[dict(start=transition-10,end=transition+35)];end_res=3600
    a['waypoints']=points
    world['runwayReservations']=[dict(aircraftId='A2' if exercise==FLEET_DEMONSTRATIONS[3] else 'A1',start=0,end=end_res,kind=exercise)]
    outside=next((p['t'] for p in a['phases'] if p['id']=='outside_area'),3600)
    world['flightShowcases']=[dict(id=exercise,aircraftId='A1',start=0,end=outside)]
    if exercise==FLEET_DEMONSTRATIONS[0]:
        world['flightShowcases']=[dict(id='wildlife-detail',aircraftId='A1',start=0,end=65),dict(id=exercise,aircraftId='A1',start=65,end=outside)]
    # Dense motion samples are interpolation geometry, not prediction barriers.
    world['predictionBoundaries']=sorted({p['t'] for plane in world['aircraft'] for p in plane['phases']}|{0.,3600.}|{incident[key] for incident in world['incidents'] for key in ('start','end')})
    world['events'].sort(key=lambda e:(e['receiptTime'],e['id']))
    return world,copy.deepcopy(world['runwayReservations']),[]
