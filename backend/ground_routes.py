"""One geometric source for ground trajectories, pavement and heading.

Coordinates are in the scenario's kilometre-scaled units. Corners are tangent
circular arcs sampled at at most five degrees, with their exact radius and sweep
retained for verification. Pavement is a ribbon around these same points.
"""
import math

def heading(dx,dz):return math.degrees(math.atan2(dx,dz))%360
def distance(a,b):return math.hypot(b['x']-a['x'],b['z']-a['z'])
def point(x,z,yaw):return dict(x=round(x,8),z=round(z,8),heading=round(yaw%360,6),hasHeading=True)

def rounded_path(vertices,radius=.025):
    result=[];turns=[]
    def append(p):
        if not result or distance(result[-1],p)>1e-9:result.append(p)
        else:result[-1]=p
    ax,az=vertices[0];bx,bz=vertices[1]
    append(point(ax,az,heading(bx-ax,bz-az)))
    for i in range(1,len(vertices)-1):
        a,b,c=vertices[i-1:i+2]
        u=(b[0]-a[0],b[1]-a[1]);v=(c[0]-b[0],c[1]-b[1])
        lu,lv=math.hypot(*u),math.hypot(*v)
        if min(lu,lv)<1e-9:continue
        u=(u[0]/lu,u[1]/lu);v=(v[0]/lv,v[1]/lv)
        angle=math.acos(max(-1,min(1,u[0]*v[0]+u[1]*v[1])))
        if angle<1e-6:append(point(*b,heading(*v)));continue
        if angle>math.pi-1e-6:raise ValueError('Ground route cannot reverse through a zero-radius corner')
        tangent=min(radius*math.tan(angle/2),lu*.4,lv*.4)
        r=tangent/math.tan(angle/2);sign=1 if u[0]*v[1]-u[1]*v[0]>0 else -1
        entry=(b[0]-u[0]*tangent,b[1]-u[1]*tangent)
        center=(entry[0]-u[1]*r*sign,entry[1]+u[0]*r*sign)
        start=math.atan2(entry[1]-center[1],entry[0]-center[0]);steps=math.ceil(math.degrees(angle)/5)
        first=len(result)
        for j in range(steps+1):
            theta=start+sign*angle*j/steps
            append(point(center[0]+r*math.cos(theta),center[1]+r*math.sin(theta),
                         heading(-math.sin(theta)*sign,math.cos(theta)*sign)))
        turns.append(dict(centerX=center[0],centerZ=center[1],radiusMetres=r*1000,
                          sweepDegrees=math.degrees(angle)*sign,firstPoint=first,lastPoint=len(result)-1))
    a,b=vertices[-2:];append(point(*b,heading(b[0]-a[0],b[1]-a[1])))
    return result,turns

def departure_path(origin,vertices,radius=.020):
    """Push straight back, then taxi forward through a tangent quarter-circle."""
    x,z=origin;taxi_z=vertices[0][1];next_x=vertices[1][0]
    side=1 if next_x>x else -1
    r=min(radius,abs(next_x-x)*.4);stop=(x,taxi_z-r)
    push=[point(x,z,0),point(*stop,0)] # nose stays toward the stand during reverse
    center=(x+side*r,stop[1]);arc=[]
    for i in range(19):
        theta=(math.pi-math.pi/2*i/18) if side>0 else math.pi/2*i/18
        sign=-1 if side>0 else 1
        arc.append(point(center[0]+r*math.cos(theta),center[1]+r*math.sin(theta),
                         heading(-math.sin(theta)*sign,math.cos(theta)*sign)))
    rest,turns=rounded_path([(arc[-1]['x'],arc[-1]['z']),*vertices[1:]],radius)
    taxi=arc+rest[1:]
    turn=dict(centerX=center[0],centerZ=center[1],radiusMetres=r*1000,
              sweepDegrees=-side*90,firstPoint=0,lastPoint=18)
    for t in turns:t['firstPoint']+=18;t['lastPoint']+=18
    return push,taxi,[turn,*turns]

def timed_path(points,start,speed=None,end=None,reverse=False):
    lengths=[distance(a,b)*1000 for a,b in zip(points,points[1:])]
    total=sum(lengths)
    if total<=0 or (speed is None and (end is None or end<=start)):raise ValueError('Ground path needs distance and positive duration')
    speed=speed or total/(end-start);t=start
    result=[dict(t=round(t,3),y=0,reverse=reverse,**points[0])]
    for p,length in zip(points[1:],lengths):
        t+=length/speed;result.append(dict(t=round(t,3),y=0,reverse=reverse,**p))
    return result

def add_pavement(world,points,turns=()):
    geometry=[dict(x=p['x'],z=p['z']) for p in points]
    paths=world.setdefault('taxiPaths',[])
    if not any(p['points']==geometry for p in paths):
        paths.append(dict(id='taxi-'+str(len(paths)+1),width=.023,points=geometry,turns=list(turns)))
