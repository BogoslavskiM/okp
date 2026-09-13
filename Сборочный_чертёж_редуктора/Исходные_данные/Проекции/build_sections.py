"""True planar longitudinal sections of the reducer, from supplied BRep solids."""
import sys, json, math, time
from pathlib import Path
from build_projections import *
from conventional_fast import fast
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.BRepPrimAPI import BRepPrimAPI_MakeHalfSpace
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.HLRBRep import HLRBRep_PolyAlgo, HLRBRep_PolyHLRToShape

AXES={
    'II':(5.0,-.05), 'III':(14.225,-9.275),
    'IV':(4.89119,-18.60881), 'V':(-6.667,-11.93568),
    'VI':(-15.33,3.07),
}
# Exact model axes, when available, replace the rounded drawing coordinates.
for label,gid in [('II',36),('III',292),('IV',67),('V',301),('VI',252)]:
    AXES[label]=gear_axis(gid,GEARS[gid][0])
PAIRS={'section_b':('II','III'),'section_c':('IV','V'),'section_d':('VI',)}

def names(i):
    parts=[]
    while i is not None:
        parts.append(NODES[i]['name']);i=NODES[i]['parent']
    return ' '.join(parts).lower()

def poly_project(shape,normal,xdir):
    t=time.time()
    BRepMesh_IncrementalMesh(shape,.003,False,.08,False).Perform()
    a=HLRBRep_PolyAlgo();a.Load(shape)
    a.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0,0,0),gp_Dir(*normal),gp_Dir(*xdir))))
    a.Update();h=HLRBRep_PolyHLRToShape();h.Update(a)
    v={'visible':edges(h.VCompound())+edges(h.OutLineVCompound()),'hidden':[],
       'extra_visible':edges(h.Rg1LineVCompound())}
    print('PROJECTED',round(time.time()-t,2),len(v['visible']),flush=True)
    return v

def run(task):
    pair=PAIRS[task];ca=AXES[pair[0]]
    if len(pair)==2:
        cb=AXES[pair[1]];dx,dz=cb[0]-ca[0],cb[1]-ca[1];length=math.hypot(dx,dz)
        direction=(dx/length,0,dz/length)
    else:direction=(0,0,1)
    normal=(direction[2],0,-direction[0]);point=(ca[0],0,ca[1])
    plane=gp_Pln(gp_Pnt(*point),gp_Dir(*normal))
    face=BRepBuilderAPI_MakeFace(plane,-500,500,-500,500).Face()
    half=BRepPrimAPI_MakeHalfSpace(face,gp_Pnt(*[point[k]-100*normal[k] for k in range(3)])).Solid()
    shapes=[];sections=[];cut_ids=[]
    for i in leaves(ROOTS):
        box=NODES[i]['bbox'];corners=[(x,y,z) for x in [box[0],box[3]] for y in [box[1],box[4]] for z in [box[2],box[5]]]
        distances=[sum((v[k]-point[k])*normal[k] for k in range(3))for v in corners]
        if min(distances)>1e-6:continue
        src=fast(i)
        # Conventional axial engagement: the driving tooth is in front.
        foreground={'section_b':{66:36},'section_c':{304:67},'section_d':{252:301,257:301}}[task]
        if i in foreground:
            driver=foreground[i];ra,rf,y0,y1,mod=GEARS[driver];cx,cz=gear_axis(driver,ra)
            tool=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(cx,y0,cz),gp_Dir(0,1,0)),ra,y1-y0).Shape()
            cut_overlap=BRepAlgoAPI_Cut(src,tool);cut_overlap.Build();src=cut_overlap.Shape()
        intersects=max(distances)>1e-6 and min(distances)<-1e-6
        name=names(i)
        unhatched=any(w in name for w in ['вал-шестерня','вад-шестерня','вал vi','винт','шарик','пружина','штифт','шпонка','гайка','шайба'])
        whole=unhatched and any(w in name for w in ['вал-шестерня','вад-шестерня','вал vi'])
        if intersects:
            cut=BRepAlgoAPI_Common(src,half);cut.Build();shown=cut.Shape()
            if whole:
                # Longitudinal sections show solid shafts uncut.
                shown=src
            cut_ids.append(i)
            if not unhatched:
                hatch_source=src
                if i in GEARS:
                    ra,rf,y0,y1,m=GEARS[i];cx,cz=gear_axis(i,ra)
                    ax=gp_Ax2(gp_Pnt(cx,y0,cz),gp_Dir(0,1,0))
                    annulus=BRepAlgoAPI_Cut(BRepPrimAPI_MakeCylinder(ax,ra+.001,y1-y0).Shape(),
                                          BRepPrimAPI_MakeCylinder(ax,rf,y1-y0).Shape()).Shape()
                    hatch_source=BRepAlgoAPI_Cut(src,annulus).Shape()
                section=BRepAlgoAPI_Section(hatch_source,plane,False);section.Build()
                sections.append({'id':i,'edges':edges(section.Shape(),.003)})
        else:shown=src
        if not shown.IsNull():shapes.append(shown)
    print('CUT DONE',task,len(shapes),len(sections),flush=True)
    value=poly_project(compound(shapes),normal,(0,1,0))
    value['sections']=sections
    value['metadata']={'normal':normal,'xdir':[0,1,0],'plane_point':point,'shaft_pair':pair,
                       'axes':AXES,'cut_ids':cut_ids,'included_root_ids':ROOTS,
                       'mesh_deflection_mm':.003}
    (OUT/f'{task}.json').write_text(json.dumps(value,separators=(',',':')))
    print('SAVED',task,flush=True)

if __name__=='__main__':run(sys.argv[1])
