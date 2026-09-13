"""Projection-only conventional gear envelopes; source CAD remains unchanged."""
import sys, json, math, time
from pathlib import Path
sys.path.insert(0, '/tmp')
import okp_projection_fine as exact
import okp_projection_detailed as detail
from okp_projection_fine import *
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.gp import gp_Ax2

OUT=Path(__file__).resolve().parent
PHYSICAL=set(json.loads((DATA/'physical_ids.json').read_text()))
EXCLUDED={4,7,8,9,123,126,129,132,406,375,148,151,159,156,164,194,197,378,381,384,409,167,410,182,183,184,187,190,191}
ROOTS=[n['id'] for n in NODES if n['parent']==0 and n['bbox'] and n['id'] not in EXCLUDED]
OPEN_REMOVED={341,93,94,95,138,221,222,344,345,105,108,111,114,117,120,282,285,288,348,351,354,357,360,363,366,369,372,
              387,279,135,247,139,142,145,170,173,176,179,182,183,184,187,190,191}
# Parts wholly screened by the closed casing and cover can be omitted in external views.
CLOSED_EXTERNAL={1,93,94,95,138,221,222,223,341,344,345,105,108,111,114,117,120,282,285,288,348,351,354,357,360,363,366,369,372,
                 387,279,135,247,139,142,145,170,173,176,179}
def under(i,root):
    while i is not None:
        if i==root:return True
        i=NODES[i]['parent']
    return False
def leaves(roots):return [i for i in sorted(PHYSICAL) if any(under(i,r) for r in roots)]

# id: tooth tip radius, root radius, start Y, end Y, module.
# All actual axis coordinates are extracted from matching cylindrical surfaces.
GEARS={36:(3.15,2.475,18.775,21.475,.3),37:(12.075,11.2875,6.025,8.825,.35),
66:(10.5,9.825,18.925,21.325,.3),67:(3.15,2.475,22.325,24.225,.3),
80:(10.65,9.975,14.375,16.775,.3),252:(14.35,13.5625,10,11.6,.35),
257:(14.35,13.5625,11.6,13.2,.35),292:(3.15,2.475,14.225,16.925,.3),
301:(3.675,2.8875,9.825,13.375,.35),304:(10.8,10.125,22.475,24.075,.3),
389:(23,21.875,46,50,.5),392:(23,21.875,42,46,.5)}

def gear_axis(i,r):
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_Cylinder
    from OCP.TopAbs import TopAbs_FACE
    exp=TopExp_Explorer(load(i),TopAbs_FACE)
    while exp.More():
        s=BRepAdaptor_Surface(TopoDS.Face(exp.Current()))
        if s.GetType()==GeomAbs_Cylinder:
            c=s.Cylinder();a=c.Axis()
            if abs(c.Radius()-r)<1e-5 and abs(a.Direction().Y())>.99:
                return (a.Location().X(),a.Location().Z())
        exp.Next()
    raise ValueError(i)

def conventional(i):
    from conventional_fast import fast
    return fast(i)

def manifest():
    ids=leaves(ROOTS);boxes=[NODES[i]['bbox'] for i in ids]
    v={'included_root_ids':ROOTS,'included_physical_ids':ids,'excluded_root_ids':sorted(EXCLUDED),
       'open_view_removed_root_ids':sorted(OPEN_REMOVED),'open_view_included_physical_ids':leaves([r for r in ROOTS if r not in OPEN_REMOVED]),
       'bbox':[min(b[k] for b in boxes) for k in range(3)]+[max(b[k] for b in boxes) for k in range(3,6)],
       'gears':[dict(id=i,center_xz=gear_axis(i,a[0]),tip_radius=a[0],root_radius=a[1],pitch_radius=a[0]-a[4],tooth_y_range=a[2:4],module=a[4]) for i,a in GEARS.items()]}
    (OUT/'Состав_и_геометрия.json').write_text(json.dumps(v,ensure_ascii=False,indent=2))
    return v

def project_poly(shape,normal,xdir):
    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.HLRBRep import HLRBRep_PolyAlgo,HLRBRep_PolyHLRToShape
    t=time.time();print('POLY START',normal,flush=True)
    mesh=BRepMesh_IncrementalMesh(shape,.006,False,.10,False);mesh.Perform()
    algo=HLRBRep_PolyAlgo();algo.Load(shape)
    algo.Projector(HLRAlgo_Projector(gp_Ax2(gp_Pnt(0,0,0),gp_Dir(*normal),gp_Dir(*xdir))));algo.Update()
    hlr=HLRBRep_PolyHLRToShape();hlr.Update(algo)
    value={'visible':edges(hlr.VCompound())+edges(hlr.OutLineVCompound()),'hidden':[],'extra_visible':edges(hlr.Rg1LineVCompound())}
    print('POLY DONE',round(time.time()-t,2),len(value['visible']),len(value['extra_visible']),flush=True)
    return value

def transverse_section():
    from conventional_fast import fast
    plane=gp_Pln(gp_Pnt(0,34.5,0),gp_Dir(0,1,0));clip=clipping_box(1,34.5,False)
    shapes=[];sections=[]
    for i in leaves(ROOTS):
        box=NODES[i]['bbox']
        if box[1]>=34.5:continue
        s=fast(i)
        if box[4]>34.5:
            cut=BRepAlgoAPI_Common(s,clip);cut.Build();shown=cut.Shape()
            section=BRepAlgoAPI_Section(s,plane,False);section.Build()
            sections.append({'id':i,'edges':edges(section.Shape(),.002)})
        else:shown=s
        if not shown.IsNull():shapes.append(shown)
    print('CUT A DONE',len(shapes),len(sections),flush=True)
    value=project_poly(compound(shapes),(0,1,0),(-1,0,0));value['sections']=sections
    value['metadata']={'normal':[0,1,0],'xdir':[-1,0,0],'plane_point':[0,34.5,0],'included_root_ids':ROOTS,'mesh_deflection_mm':.006}
    (OUT/'section_a.json').write_text(json.dumps(value,separators=(',',':')))
    print('SAVED section_a',flush=True)

if __name__=='__main__':
    task=sys.argv[1]
    if task=='section_a':transverse_section();sys.exit(0)
    if task=='manifest':
        print(json.dumps(manifest(),ensure_ascii=False,indent=2));sys.exit(0)
    if task=='prepare':
        for i in GEARS:conventional(i)
        manifest();sys.exit(0)
    from conventional_fast import fast
    roots=[r for r in ROOTS if (r not in OPEN_REMOVED if task=='open' else r in CLOSED_EXTERNAL)]
    ids=leaves(roots);shape=compound([fast(i) for i in ids])
    normal,xdir=((1,0,0),(0,1,0)) if task=='side' else ((0,1,0),(-1,0,0))
    value=project_poly(shape,normal,xdir)
    value['metadata']={'normal':normal,'xdir':xdir,'assembly_root_ids':ROOTS,'included_root_ids':roots,'included_physical_ids':ids,
                       'conventional_gear_envelopes':True,'mesh_deflection_mm':.006,'mesh_angle_rad':.10,
                       'external_omissions':'Internal components wholly occluded by closed casing/cover omitted for calculation' if task!='open' else None}
    (OUT/f'{task}.json').write_text(json.dumps(value,separators=(',',':')))
    print('SAVED',task,len(value['visible']),len(value['extra_visible']),flush=True)
