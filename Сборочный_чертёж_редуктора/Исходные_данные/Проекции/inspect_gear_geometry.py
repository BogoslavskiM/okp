import sys, collections
sys.path.insert(0, '/tmp')
from okp_projection_fine import *
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane
from OCP.TopAbs import TopAbs_FACE

for i in [36,37,66,67,80,252,257,292,301,304,389,392]:
    shape=load(i);exp=TopExp_Explorer(shape,TopAbs_FACE);c=collections.defaultdict(list)
    while exp.More():
        face=TopoDS.Face(exp.Current());s=BRepAdaptor_Surface(face)
        if s.GetType()==GeomAbs_Cylinder:
            v=s.Cylinder();a=v.Axis();p=a.Location();d=a.Direction()
            if abs(d.Y())>.99:
                box=Bnd_Box();BRepBndLib.Add_s(face,box)
                c[(round(v.Radius(),5),round(p.X(),5),round(p.Z(),5))].append(tuple(round(q,5) for q in [box.CornerMin().Y(),box.CornerMax().Y()]))
        exp.Next()
    print(i,NODES[i]['name'])
    for k,vs in sorted(c.items(),reverse=True):print(' ',k,sorted(set(vs)))
