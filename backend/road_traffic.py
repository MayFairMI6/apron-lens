"""Authored ambient vehicles on sourced landside roads; never report evidence.

The external driver's source time is the only motion input. Geometry, turn radii,
speed and vehicle phase are explicit, so a reconnect or time-lapse is repeatable.
"""
import math
import random
from backend.ground_routes import heading, point, distance


def closed_road_path(points, radius=.005):
    vertices = points[:-1] if points[0] == points[-1] else points
    route, turns = [], []
    for i, b in enumerate(vertices):
        a, c = vertices[i-1], vertices[(i+1) % len(vertices)]
        lu, lv = distance(a,b), distance(b,c)
        if min(lu, lv) < 1e-8: raise ValueError('Road route has a duplicate vertex')
        u=((b['x']-a['x'])/lu,(b['z']-a['z'])/lu)
        v=((c['x']-b['x'])/lv,(c['z']-b['z'])/lv)
        angle=math.acos(max(-1,min(1,u[0]*v[0]+u[1]*v[1])))
        if angle < 1e-6:
            route.append(point(b['x'],b['z'],heading(*v))); continue
        if angle > math.pi-.001: raise ValueError('Road route reverses through a corner')
        tangent=min(radius*math.tan(angle/2),lu*.4,lv*.4)
        r=tangent/math.tan(angle/2);sign=1 if u[0]*v[1]-u[1]*v[0]>0 else -1
        entry=(b['x']-u[0]*tangent,b['z']-u[1]*tangent)
        center=(entry[0]-u[1]*r*sign,entry[1]+u[0]*r*sign)
        start=math.atan2(entry[1]-center[1],entry[0]-center[0]);steps=math.ceil(math.degrees(angle)/5)
        first=len(route)
        for j in range(steps+1):
            theta=start+sign*angle*j/steps
            route.append(point(center[0]+r*math.cos(theta),center[1]+r*math.sin(theta),
                               heading(-math.sin(theta)*sign,math.cos(theta)*sign)))
        turns.append(dict(radiusMetres=r*1000,sweepDegrees=math.degrees(angle)*sign,
                          firstPoint=first,lastPoint=len(route)-1))
    route.append(dict(route[0])); total=0
    for i,p in enumerate(route):
        if i: total+=distance(route[i-1],p)*1000
        p['distanceMetres']=total
    return route,turns,total


def build_road_traffic(geo, seed):
    source_routes=geo.get('roadTrafficRoutes',[])
    if not source_routes: return None
    rng=random.Random(seed); routes=[]; vehicles=[]
    for source in source_routes:
        if not source.get('closed') or not source.get('oneway'): raise ValueError('Ambient route must be a closed one-way loop')
        route,turns,length=closed_road_path(source['points'])
        routes.append(dict(id=source['id'],points=route,lengthMetres=length,turns=turns,
                           sourceWayIds=source['sourceWayIds'],speedMetresPerSecond=3,
                           sourceLengthMetres=source['lengthMetres']))
        phase=rng.uniform(0,length)
        for i in range(6):
            vehicles.append(dict(id=f'road-{len(vehicles)+1}',routeId=source['id'],
                offsetMetres=(phase+i*length/6)%length,kind='van' if i==2 else 'car',
                colourIndex=rng.randrange(5)))
    return dict(version=1,routes=routes,vehicles=vehicles,
                provenance='Mapped one-way road loop; authored tangent turns up to 5 m radius, 3 m/s speed, centreline placement and six ambient vehicles. No live traffic or operational evidence.')


def road_pose(traffic, vehicle, source_time):
    route=next(r for r in traffic['routes'] if r['id']==vehicle['routeId'])
    d=(vehicle['offsetMetres']+max(0,source_time)*route['speedMetresPerSecond'])%route['lengthMetres']
    for a,b in zip(route['points'],route['points'][1:]):
        if d<=b['distanceMetres']:
            f=(d-a['distanceMetres'])/(b['distanceMetres']-a['distanceMetres'])
            return dict(x=a['x']+(b['x']-a['x'])*f,z=a['z']+(b['z']-a['z'])*f,
                        heading=(a['heading']+((b['heading']-a['heading']+180)%360-180)*f)%360)
    raise ValueError('Incomplete ambient road route')
