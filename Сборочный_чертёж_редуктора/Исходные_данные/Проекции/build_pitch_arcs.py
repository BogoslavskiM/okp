"""Native visibility of initial circles against the real A–A retained half."""
import json,math,time
from pathlib import Path
from build_projections import *
from conventional_fast import fast
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCP.gp import gp_Lin

def retained_shape():
    clip=clipping_box(1,34.5,False);shapes=[]
    for i in leaves(ROOTS):
        box=NODES[i]['bbox']
        if box[1]>=34.5:continue
        s=fast(i)
        if box[4]>34.5:
            cut=BRepAlgoAPI_Common(s,clip);cut.Build();s=cut.Shape()
        if not s.IsNull():shapes.append(s)
    return compound(shapes)

def run():
    start=time.time();scene=retained_shape()
    ray=IntCurvesFace_ShapeIntersector();ray.Load(scene,1e-7)
    output={'visible':[],'hidden':[],'gears':[],
            'metadata':{'normal':[0,1,0],'xdir':[-1,0,0],
                        'coordinates':'Projection coordinates [-world_X, world_Z, 0], in mm',
                        'section_plane_y_mm':34.5,'circle_offset_from_front_face_mm':.005,
                        'sample_angle_deg':1,'boundary_refinement_deg':.001,
                        'occlusion':'IntCurvesFace_ShapeIntersector against the conventional solids retained at Y<=34.5'}}
    for gid in [37,66,80,304,252]:
        ra,rf,y0,y1,m=GEARS[gid];cx,cz=gear_axis(gid,ra);radius=ra-m
        # Z10 is one split wheel. Its front half is node257, sharing the same initial circle.
        yfront=13.2 if gid==252 else y1
        yray=yfront+.005;cache={};tests=0
        def point(angle):
            a=math.radians(angle);return cx+radius*math.cos(a),cz+radius*math.sin(a)
        def visible(angle):
            nonlocal tests
            key=round(angle%360,8)
            if key in cache:return cache[key]
            x,z=point(key)
            ray.PerformNearest(gp_Lin(gp_Pnt(x,yray,z),gp_Dir(0,1,0)),1e-6,34.5-yray+1e-6)
            if not ray.IsDone():raise RuntimeError(f'Visibility failed: gear {gid}, angle {angle}')
            val=ray.NbPnt()==0;cache[key]=val;tests+=1;return val
        def boundary(a,b,state):
            # Locate the first transition in this one-degree interval.
            while b-a>.001:
                c=(a+b)/2
                if visible(c)==state:a=c
                else:b=c
            return (a+b)/2
        states=[visible(a) for a in range(360)]
        intervals=[]
        for a in range(360):
            b=a+1;va=states[a];vb=states[b%360]
            if va!=vb:
                c=boundary(a,b,va)
                intervals.append((float(a),c) if va else (c,float(b)))
            else:
                # Midpoint check catches narrow visible or masked segments.
                vm=visible(a+.5)
                if vm==va:
                    if va:intervals.append((float(a),float(b)))
                else:
                    c1=boundary(a,a+.5,va);c2=boundary(a+.5,b,vm)
                    if vm:intervals.append((c1,c2))
                    else:intervals.extend([(float(a),c1),(c2,float(b))])
        joined=[]
        for a,b in intervals:
            if b-a<1e-7:continue
            if joined and abs(joined[-1][1]-a)<1e-7:joined[-1]=(joined[-1][0],b)
            else:joined.append((a,b))
        if len(joined)>1 and joined[0][0]==0 and joined[-1][1]==360:
            joined=[(joined[-1][0],joined[0][1]+360)]+joined[1:-1]
        paths=[]
        for a,b in joined:
            count=max(1,math.ceil(b-a));angles=[a+(b-a)*k/count for k in range(count+1)]
            paths.append([[-point(t)[0],point(t)[1],0] for t in angles])
        output['visible'].extend(paths)
        output['gears'].append({'id':gid,'center_xz':[cx,cz],'radius':radius,
                                'front_face_y_mm':yfront,'visible_intervals_deg':joined,
                                'visible_fraction':sum(b-a for a,b in joined)/360,
                                'visibility_tests':tests,'paths':paths})
        print('GEAR',gid,'visible',round(output['gears'][-1]['visible_fraction'],4),'arcs',len(paths),'rays',tests,flush=True)
    (OUT/'section_a_pitch.json').write_text(json.dumps(output,separators=(',',':')))
    print('SAVED',round(time.time()-start,2),'seconds',flush=True)

if __name__=='__main__':run()
