"""Replace only tooth rim faces, keeping all inner faces and openings."""
from build_projections import *
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane
from OCP.TopAbs import TopAbs_FACE, TopAbs_VERTEX, TopAbs_WIRE, TopAbs_SHELL
from OCP.BRep import BRep_Tool
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeEdge,BRepBuilderAPI_MakeWire,BRepBuilderAPI_MakeFace,BRepBuilderAPI_Sewing,BRepBuilderAPI_MakeSolid
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.ShapeFix import ShapeFix_Shape
from OCP.gp import gp_Circ,gp_Pln

def points(shape):
    exp=TopExp_Explorer(shape,TopAbs_VERTEX);out=[]
    while exp.More():
        p=BRep_Tool.Pnt_s(TopoDS.Vertex(exp.Current()));out.append(p);exp.Next()
    return out

def fast(i):
    cache=OUT/'Условная_геометрия_fast';cache.mkdir(exist_ok=True);path=cache/f'{i}.brep'
    if path.exists():
        s=TopoDS_Shape();BRepTools.Read_s(s,str(path),BRep_Builder());return s
    if i not in GEARS:return load(i)
    ra,rf,y0,y1,m=GEARS[i];cx,cz=gear_axis(i,ra);src=load(i)
    faces=[];exp=TopExp_Explorer(src,TopAbs_FACE);caps=0;removed=0
    while exp.More():
        face=TopoDS.Face(exp.Current());exp.Next();p=points(face)
        r=[math.hypot(q.X()-cx,q.Z()-cz) for q in p];ys=[q.Y() for q in p]
        if not r:faces.append(face);continue
        surf=BRepAdaptor_Surface(face)
        if surf.GetType()==GeomAbs_Plane and abs(surf.Plane().Axis().Direction().Y())>.999:
            yc=surf.Plane().Location().Y()
            if min(abs(yc-y0),abs(yc-y1))<1e-5 and max(r)>ra-.01:
                outer=BRepTools.OuterWire_s(face)
                circ=gp_Circ(gp_Ax2(gp_Pnt(cx,yc,cz),gp_Dir(0,1,0)),ra)
                wire=BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(circ).Edge()).Wire()
                builder=BRepBuilderAPI_MakeFace(surf.Plane(),wire,True)
                wx=TopExp_Explorer(face,TopAbs_WIRE)
                while wx.More():
                    w=TopoDS.Wire(wx.Current())
                    if not w.IsSame(outer):builder.Add(w)
                    wx.Next()
                replacement=builder.Face();replacement.Orientation(face.Orientation())
                faces.append(replacement);caps+=1;continue
        if min(r)>=rf-.0001 and min(ys)>=y0-.0001 and max(ys)<=y1+.0001:
            removed+=1;continue
        faces.append(face)
    cylinder=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(cx,y0,cz),gp_Dir(0,1,0)),ra,y1-y0).Shape()
    exp=TopExp_Explorer(cylinder,TopAbs_FACE)
    while exp.More():
        face=TopoDS.Face(exp.Current());exp.Next()
        if BRepAdaptor_Surface(face).GetType()==GeomAbs_Cylinder:faces.append(face)
    sew=BRepBuilderAPI_Sewing(1e-5)
    for f in faces:sew.Add(f)
    sew.Perform();shape=sew.SewedShape()
    exp=TopExp_Explorer(shape,TopAbs_SHELL);shells=[]
    while exp.More():shells.append(TopoDS.Shell(exp.Current()));exp.Next()
    if len(shells)==1:shape=BRepBuilderAPI_MakeSolid(shells[0]).Solid()
    fixer=ShapeFix_Shape(shape);fixer.Perform();shape=fixer.Shape()
    valid=BRepCheck_Analyzer(shape).IsValid()
    print('FAST',i,'caps',caps,'removed',removed,'faces',len(faces),'shells',len(shells),'free',sew.NbFreeEdges(),'valid',valid,flush=True)
    if caps!=2 or sew.NbFreeEdges()!=0 or not valid:raise ValueError(f'Invalid conventional geometry {i}')
    BRepTools.Write_s(shape,str(path));return shape

if __name__=='__main__':
    for i in GEARS:fast(i)
