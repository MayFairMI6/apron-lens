"""Independent, report-driven incident demonstrations on a sourced regional map.

These are authored teaching examples informed by investigations, not flight-data
reconstructions. Geometry cannot enter the assistant's report evidence channel.
"""
import copy
import json
import math
import random
from pathlib import Path
from backend.ground_routes import rounded_path, timed_path, add_pavement, heading
from backend.road_traffic import build_road_traffic

DEMONSTRATIONS = ('rejected_takeoff', 'occupied_runway_go_around', 'runway_incursion', 'water_landing', 'fog_visibility')
TITLES = dict(zip(DEMONSTRATIONS, ('A rejected takeoff', 'A go-around with the runway occupied',
                                 'A vehicle entering the runway', 'An emergency water landing',
                                 'Fog and changing restrictions')))
OBJECTIVES = dict(zip(DEMONSTRATIONS, (
    'Separate a reported rejected takeoff, a stopped aircraft and a runway release.',
    'Follow the arrival that goes around and the aircraft still occupying the runway.',
    'Recognise the incursion and cancelled departure; wait for explicit runway status.',
    'Track the reported emergency and location; keep response and survivor status separate.',
    'Distinguish improving visibility, cancelled procedures and the restrictions still reported for your flight.')))
SOURCES = {
    'rejected_takeoff': ['https://assets.publishing.service.gov.uk/media/6221e05fe90e0710be03550f/Various_CAT_03-22.pdf'],
    'occupied_runway_go_around': ['https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/local-community/noise/reports-and-statistics/reports/anatmt/Heathrow_ANATMT_Annual_Report_2024.pdf'],
    'runway_incursion': ['https://assets.publishing.service.gov.uk/media/5f452cc98fa8f51f7993ac9b/Airbus_A300b4-622R_F__D-AEAD_12-19.pdf'],
    'water_landing': ['https://www.ntsb.gov/investigations/Pages/DCA09MA026.aspx'],
    'fog_visibility': [
        'https://www.heathrow.com/content/dam/heathrow/web/common/documents/company/team-heathrow/airside/operational-safety-insttructions/ASWeather_OSI_052_v3-1.pdf',
        'https://nats.aero/blog/2025/10/low-visibility-procedures-what-you-need-to-know/'],
}

def project(longitude, latitude):
    """Fixed, documented local projection in kilometres, east/north positive."""
    return ((longitude+.46)*math.pi/180*6371.0088*math.cos(math.radians(51.47)),
            (latitude-51.47)*math.pi/180*6371.0088)

def geography():
    source = json.loads((Path(__file__).resolve().parents[1]/'data/geography/heathrow-west.json').read_text())
    def points(coords):return [dict(zip(('x','z'),project(*p))) for p in coords]
    features=[]
    for f in source['features']:
        item=dict(id=f['id'],name=f['name'],kind=f['kind'],width=f['widthMetres']/1000,
                  closed=f['closed'],points=points(f['coordinates']))
        for key in ('widthBasis','widthAuthored','heightMetres','heightBasis','deckHeightMetres','deckHeightBasis','bodyHeightMetres','bodyHeightBasis'):
            if key in f:item[key]=f[key]
        if f.get('holes'):item['holes']=[dict(points=points(ring.get('coordinates') if isinstance(ring,dict) else ring)) for ring in f['holes']]
        if f.get('roofCoordinates'):
            item['roofPoints']=points(f['roofCoordinates']);item['roofTriangles']=f['roofTriangles']
        features.append(item)
    sites=[]
    for site in source.get('referenceSites',[]):
        item={k:site[k] for k in ('id','name','renderAs','status','note','statusSource','statusSourceDate') if k in site}
        item['points']=points(site['coordinates'])
        item['holes']=[dict(points=points(ring.get('coordinates') if isinstance(ring,dict) else ring)) for ring in site.get('holes',[])]
        sites.append(item)
    routes=[]
    for route in source.get('roadTrafficRoutes',[]):
        item={k:route[k] for k in ('id','name','closed','oneway','lengthMetres','sourceWayIds','sourceWaySpans','provenance') if k in route}
        item['points']=points(route['coordinates']);routes.append(item)
    return dict(version=source.get('version',1), attribution=source['attribution'], features=features,
                referenceSites=sites,roadTrafficRoutes=routes,
                note='Heathrow region · authored paths · not a navigation chart')

def inside_polygon(x, z, points):
    inside=False
    for a,b in zip(points, points[1:]+points[:1]):
        if (a['z']>z)!=(b['z']>z) and x<(b['x']-a['x'])*(z-a['z'])/(b['z']-a['z'])+a['x']:
            inside=not inside
    return inside

def build_demonstration(seed, exercise):
    if exercise not in DEMONSTRATIONS: raise ValueError('Unknown demonstration')
    rng=random.Random(seed); start=60.+rng.randrange(5)
    geo=geography()
    runway=next(f for f in geo['features'] if f['id']=='osm-way-2798800')
    west,east=sorted((runway['points'][0],runway['points'][-1]),key=lambda p:p['x'])
    length=math.hypot(east['x']-west['x'],east['z']-west['z'])
    ux,uz=(east['x']-west['x'])/length,(east['z']-west['z'])/length
    yaw=heading(ux,uz)
    def along(metres, offset=0):
        return west['x']+ux*metres/1000-uz*offset/1000,west['z']+uz*metres/1000+ux*offset/1000
    def wp(t,x,z,y=0,heading=yaw,pitch=0,**kw):
        return dict(t=round(t,4),x=x,y=y,z=z,heading=heading,pitch=pitch,**kw)
    world=dict(scenarioId=f'DEMO-{exercise}-{seed}',duration=3600,targetWidth=.7,livery='uniform',
        clockWhileUntracked='runs',trainingProfile=exercise,trainingRole='controller_awareness',
        trainingRoleLabel='Controller awareness',trainingObjective=OBJECTIVES[exercise],
        assistantQuestionLabels=['Latest report','What changed?'],
        assistantQuestions=['What is the latest reported movement for this flight?','What changed for this flight?'],
        geography=geo,ambientTraffic=build_road_traffic(geo,seed),aircraft=[],events=[],visualProps=[],groundVehicles=[],incidents=[],
        demoQuestions=[],flightShowcases=[],flightTeachingWindows=[],taxiPaths=[],
        provenance=dict(kind='authored-precedent-informed',sources=SOURCES[exercise],
            limitations='Generic aircraft; authored flight paths, elapsed times and report delays. No recovered flight-data trajectory, operational clearance or performance validation.',
            localEventClaim=False if exercise=='water_landing' else None))
    last={}
    def report(aid,t,prop,value,message,source='exercise-tower',lag=None):
        eid=f'R{len(world["events"])+1:03d}';fact=dict(property=prop,value=value)
        if (aid,prop) in last:fact['supersedes']=[last[aid,prop]]
        last[aid,prop]=eid+':'+prop
        world['events'].append(dict(id=eid,aircraftId=aid,flightInstance='TRN10'+aid[-1],source=source,
            eventTime=float(t),receiptTime=float(t+(rng.uniform(1,3) if lag is None else lag)),facts=[fact],message=message))
    for i in range(3):
        # Keep wire identities stable; nonparticipants have no visible geometry
        # or selection buttons in these cases, rather than parking on unmapped grass.
        x,z=project(-.468+i*.001,51.4705)
        world['aircraft'].append(dict(id=f'A{i+1}',flightInstance=f'TRN10{i+1}',preciseHeading=True,hidden=i>0,
            waypoints=[wp(0,x,z,heading=0)],phases=[]))
    a=world['aircraft'][0]; points=[]
    def phase(t,id,label):a['phases'].append(dict(t=t,id=id,label=label))
    def cue(t,id,question):world['demoQuestions'].append(dict(id=id,at=t,aircraftId='A1',assistantQuestion=question))
    def window(a,b):world['flightTeachingWindows'].append(dict(start=a,end=b))

    if exercise=='rejected_takeoff':
        # 0→50 m/s over 25 seconds; 50→0 over 18 seconds. Authored kinematics,
        # not the reported crew airspeed readings or a certified stopping distance.
        points=[wp(0,*along(80)),wp(start,*along(80))]
        for i in range(1,26):points.append(wp(start+i,*along(80+i*i)))
        for i in range(1,19):points.append(wp(start+25+i,*along(705+50*i-25*i*i/18)))
        phase(0,'lined_up','Lined up on Runway 09R');phase(start,'takeoff_roll','Takeoff roll')
        phase(start+25,'rejected_takeoff','Rejected takeoff · decelerating');phase(start+43,'stopped','Stopped on runway')
        report('A1',0,'route','Runway 09R','TRN101 is lined up on Runway 09R.',lag=0)
        report('A1',start,'movement_status','takeoff roll','TRN101 has begun its takeoff roll.')
        report('A1',start+25,'movement_condition','takeoff rejected: crew reported unreliable airspeed; cause unconfirmed',
               'The crew reports unreliable airspeed and a rejected takeoff. The cause is not yet confirmed.')
        report('A1',start+43,'movement_status','stopped on Runway 09R','TRN101 is stopped on Runway 09R.')
        report('A1',start+44,'movement_condition','hold: runway occupied; assessment pending',
               'Runway 09R remains occupied by TRN101. Aircraft assessment is pending; no runway release has been reported.')
        report('A1',600,'movement_condition','hold: runway occupied; recovery assessment continues',
               'TRN101 remains stopped. A recovery assessment is continuing. The exercise reports do not confirm the fault or a runway release.')
        cue(start+30,'rto-reason','Why did TRN101 reject takeoff?')
        cue(start+52,'rto-stop','What is the latest reported movement for TRN101?')
        cue(610,'rto-release','Is the runway released for TRN101?')
        window(start-3,start+58)
    elif exercise=='occupied_runway_go_around':
        a2=world['aircraft'][1];a2['hidden']=False;a2['waypoints']=[wp(0,*along(2400)),wp(3600,*along(2400))]
        a2['phases']=[dict(t=0,id='runway_occupied',label='Stopped on runway')]
        # Continuous descent then transition into climb; never contacts pavement.
        for t,d,y,pitch in [(0,-7000,.38,-3),(start,-3100,.18,-3),(start+35,-650,.052,-3),
                            (start+39,-370,.05,3),(start+45,50,.075,10),(start+70,1800,.32,10),
                            (start+120,5300,.85,8),(start+160,8100,1.2,0),(3600,8100+(3600-start-160)*70,1.2,0)]:
            points.append(wp(t,*along(d),y=y,pitch=pitch,gearRetracted=t>=start+70))
        phase(0,'approach','Approach to Runway 09R');phase(start+35,'go_around','Go-around');phase(start+45,'climb','Climbing away');phase(start+160,'outside_area','Beyond the exercise area')
        report('A1',0,'route','approach to Runway 09R','TRN101 is approaching Runway 09R.',lag=0)
        report('A2',start+20,'movement_status','stopped on Runway 09R','TRN102 is stopped on Runway 09R.')
        report('A1',start+35,'movement_condition','go-around: Runway 09R occupied by TRN102',
               'The exercise tower reports TRN101 going around because TRN102 has not vacated Runway 09R.')
        report('A1',start+45,'movement_status','climbing away on go-around','TRN101 is climbing away. No landing is reported.')
        report('A1',300,'movement_condition','hold: runway still occupied; another approach unconfirmed',
               'Runway 09R remains occupied. The reports do not confirm another approach or a completed landing for TRN101.')
        cue(start+42,'ga-reason','Why is TRN101 going around?')
        cue(start+60,'ga-movement','What is the latest reported movement for TRN101?')
        cue(310,'ga-next','What is still reported about the runway restriction for TRN101?')
        window(start+25,start+75)
    elif exercise=='runway_incursion':
        points=[wp(0,*along(60)),wp(3600,*along(60))]
        phase(0,'lined_up','Lined up on Runway 09R');phase(start+20,'cancelled_departure','Departure cancelled · holding')
        # The AAIB precedent was cancelled BEFORE the roll, not an RTO/crash.
        # Connector and turn are authored, visibly paved; not the historic track.
        entry=along(1700,100);v0=along(1700,25);v1=along(1700,-4);v2=along(1720,-4);v3=along(1720,100)
        path,turns=rounded_path([entry,v0,v1,v2,v3],radius=.009)
        motion=timed_path(path,start,speed=5)
        world['groundVehicles']=[dict(id='maintenance-vehicle',preciseHeading=True,
            waypoints=[wp(0,**{k:path[0][k] for k in ('x','z','heading')})]+motion+
                      [dict(motion[-1],t=3600)])]
        add_pavement(world,path,turns);world['taxiPaths'][-1]['kind']='service';world['taxiPaths'][-1]['width']=.009
        cleared=motion[-1]['t']
        report('A1',0,'route','Runway 09R','TRN101 is lined up on Runway 09R; the takeoff roll has not started.',lag=0)
        report('A1',start+20,'movement_condition','takeoff cancelled: maintenance vehicle entered Runway 09R',
               'The exercise tower cancels TRN101 takeoff clearance after a maintenance vehicle enters Runway 09R. TRN101 has not started its takeoff roll.')
        report('A1',start+21,'movement_status','holding on Runway 09R; takeoff roll not started',
               'TRN101 remains stationary on the runway. There is no aircraft–vehicle contact.')
        report('A1',cleared+3,'movement_condition','hold: vehicle vacated; runway release unconfirmed',
               'The maintenance vehicle has vacated. TRN101 remains held; no new departure authorisation is reported.')
        cue(start+27,'incursion-hold','Why is TRN101 holding?')
        cue(cleared+10,'incursion-clear','What changed in the restriction for TRN101?')
        cue(310,'incursion-release','Is TRN101 now authorised to depart?')
        window(start-3,cleared+15)
        world['geography']['focusX'],world['geography']['focusZ']=along(1100)
    elif exercise=='fog_visibility':
        # A stationary flight on a mapped T3 apron keeps this a restriction-
        # interpretation task. Weather alone never releases or moves it.
        points=[wp(0,.16,-.19,heading=0),wp(3600,.16,-.19,heading=0)]
        phase(0,'parked','Parked at Terminal 3')
        world['provenance']['limitations']+=' Fog attenuation, event timings and the flight-specific hold are authored. No measured visibility, RVR, operational minima, capacity forecast or current Heathrow procedure compliance is asserted.'
        world['provenance']['localEventClaim']=False
        world['fogApronSourceId']='osm-way-105366849'
        report('A1',0,'route','Terminal 3 apron','TRN101 is parked on the Terminal 3 apron.',lag=0)
        report('A1',0,'movement_status','parked; departure movement not started',
               'TRN101 remains parked. No departure movement has started.',lag=0)
        report('A1',30,'movement_condition','hold: safeguarding requested; confirmation pending; departure held',
               'The exercise tower has requested low-visibility safeguarding. Confirmation is pending. TRN101 is held at its stand.')
        report('A1',300,'movement_condition','hold: low-visibility safeguarding confirmed; departure held',
               'Airside Operations confirms safeguarding in place. TRN101 is held pending a further movement update.',source='exercise-airside-operations')
        report('A1',600,'movement_condition','hold: low-visibility procedures in force; safeguarding remains; departure held',
               'Low-visibility procedures are now in force. Safeguarding remains active and TRN101 is still held.')
        report('A1',2400,'movement_condition','hold: low-visibility procedures cancelled; safeguarding remains; departure held',
               'The exercise tower has cancelled low-visibility procedures, but safeguarding remains in place. TRN101 is still held; this update is not a departure clearance.')
        report('A1',2900,'movement_condition','hold: safeguarding cancellation requested; confirmation pending; departure held',
               'The exercise tower has requested safeguarding cancellation. Confirmation is pending and TRN101 remains held.')
        report('A1',3000,'movement_condition','hold: safeguarding cancelled; departure clearance still unconfirmed',
               'Airside Operations confirms safeguarding cancellation. The reports still do not confirm a departure clearance for TRN101, which remains parked.',source='exercise-airside-operations')
        cue(650,'fog-active','What restrictions are reported for TRN101?')
        cue(2450,'fog-partial-release','What restrictions remain for TRN101 after low-visibility procedures are cancelled?')
        cue(3050,'fog-authority','Does the safeguarding cancellation confirm that TRN101 may depart?')
    else:
        # Geographical example only: south-to-north crossing inside the REAL
        # Wraysbury polygon. No claim of a feasible emergency diversion to it.
        x,z=project(-.526,51.4558)
        points=[wp(0,x,z-4.8,y=.36,heading=0,pitch=-3,gearRetracted=True),
                wp(start,x,z-1.8,y=.14,heading=0,pitch=-3,gearRetracted=True),
                wp(start+30,x,z,y=0,heading=0,pitch=6,bodySink=.003287387,gearRetracted=True)]
        for i in range(1,21):
            points.append(wp(start+30+i,x,z+(50*i-1.25*i*i)/1000,heading=0,
                             pitch=6*(1-i/20),bodySink=.003287387+(.004476700-.003287387)*i/20,gearRetracted=True))
        phase(0,'emergency_descent','Emergency descent');phase(start+30,'water_contact','Water landing');phase(start+50,'afloat','Stopped on water · status unconfirmed')
        world['incidents']=[dict(id='water-contact',kind='water_landing',aircraftId='A1',start=start+30,
                                onset=start+30,end=3600,x=x,y=0,z=z)]
        report('A1',0,'route','Wraysbury Reservoir area','TRN101 is approaching the Wraysbury Reservoir area.',lag=0)
        report('A1',start-5,'movement_condition','emergency: crew reports loss of thrust; cause unconfirmed',
               'The crew reports loss of thrust and an emergency descent. The cause and outcome are unconfirmed.',source='exercise-flight-crew')
        report('A1',start+33,'movement_status','water landing reported at Wraysbury Reservoir',
               'A water landing is reported at Wraysbury Reservoir.',source='exercise-emergency')
        report('A1',start+52,'movement_condition','emergency response requested; evacuation and survivor status unconfirmed',
               'Emergency assistance has been requested. The reports do not confirm evacuation completion, injuries or survivor numbers.',source='exercise-emergency')
        report('A1',600,'movement_condition','emergency response coordinating access; evacuation outcome unconfirmed',
               'The exercise response is coordinating access to the reservoir. No evacuation outcome is confirmed.',source='exercise-emergency')
        cue(start+5,'water-emergency','What emergency is reported for TRN101?')
        cue(start+58,'water-location','Where did TRN101 land according to the reports?')
        cue(610,'water-outcome','What does the latest emergency report confirm for TRN101?')
        window(start+18,start+65)
        world['provenance']['limitations']+=' Hudson Flight 1549 informs the event category only. No Heathrow ditching precedent, local rescue timing, obstacle clearance or reservoir suitability is asserted.'
    a['waypoints']=points
    for aircraft in world['aircraft']:
        if aircraft['waypoints'][-1]['t']<3600:aircraft['waypoints'].append(dict(aircraft['waypoints'][-1],t=3600))
    world['flightShowcases']=[dict(id=exercise,aircraftId='A1',start=0,end=start+160 if exercise=='occupied_runway_go_around' else 3600)]
    if exercise=='occupied_runway_go_around':
        world['flightShowcases']=[dict(id='goaround_overview',aircraftId='A1',start=0,end=start+75),
            dict(id=exercise,aircraftId='A1',start=start+75,end=start+160)]
    if exercise=='water_landing':
        window(0,8)
        world['flightShowcases']=[dict(id='region_intro',aircraftId='A1',start=0,end=8),
            dict(id=exercise,aircraftId='A1',start=8,end=3600)]
    if exercise=='runway_incursion':
        world['flightShowcases']=[dict(id=exercise,aircraftId='A1',start=0,end=start-5),
            dict(id='incursion_vehicle',aircraftId='A1',start=start-5,end=cleared+15),
            dict(id='incursion_after',aircraftId='A1',start=cleared+15,end=3600)]
    world['predictionBoundaries']=sorted({p['t'] for aircraft in world['aircraft']+world['groundVehicles'] for p in aircraft['waypoints']}|
        {p['t'] for aircraft in world['aircraft'] for p in aircraft['phases']})
    world['events'].sort(key=lambda e:(e['receiptTime'],e['id']))
    world['runwayReservations']=[dict(aircraftId='A2' if exercise=='occupied_runway_go_around' else 'A1',
        start=0,end=3600,kind=exercise)] if exercise not in ('water_landing','fog_visibility') else []
    return world,copy.deepcopy(world['runwayReservations']),[]
