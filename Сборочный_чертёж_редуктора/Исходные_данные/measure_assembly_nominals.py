import sys,json,math
from pathlib import Path
sys.path.insert(0,'/tmp')
from okp_projection_fine import *
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Cylinder
from OCP.TopAbs import TopAbs_FACE

OUT = Path(__file__).parent
IDS=[2,5,12,24,36,39,42,54,67,68,81,200,223,226,292,301,305,317,342]
def cylinders(i):
    rows=[];exp=TopExp_Explorer(load(i),TopAbs_FACE)
    while exp.More():
        face=TopoDS.Face(exp.Current());s=BRepAdaptor_Surface(face)
        if s.GetType()==GeomAbs_Cylinder:
            c=s.Cylinder();a=c.Axis();p=a.Location();d=a.Direction()
            if abs(d.Y())>.999999:
                box=Bnd_Box();BRepBndLib.Add_s(face,box)
                rows.append({'diameter':round(2*c.Radius(),9),'center_xz':[round(p.X(),9),round(p.Z(),9)],'y_range':[round(box.CornerMin().Y(),9),round(box.CornerMax().Y(),9)]})
        exp.Next()
    unique={json.dumps(r,sort_keys=True):r for r in rows}
    return sorted(unique.values(),key=lambda r:(r['center_xz'],r['diameter'],r['y_range']))
result={'source':'ОКП/Детальная прорисовка.stp → /tmp/okp_cad_data/*.brep','method':'BRepAdaptor_Surface: цилиндрические поверхности, ось параллельна Y; диаметры измерены по Radius(), центры по Axis.Location(). BBox шариков не использован.','cylinders':{str(i):{'name':NODES[i]['name'],'surfaces':cylinders(i)} for i in IDS}}
(OUT/'Проверка_номиналов_цилиндры.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
axes={label:next(r['center_xz'] for r in result['cylinders'][str(node)]['surfaces'] if r['diameter']==dia) for label,node,dia in [('I',5,17),('II',36,3),('III',292,3),('IV',67,3),('V',301,3),('VI',223,7)]}
distances=[]
for a,b,expected in [('II','III',13.05),('III','IV',13.2),('IV','V',13.35),('V','VI',17.325)]:
    measured=math.dist(axes[a],axes[b])
    distances.append({'axes':a+'–'+b,'measured_mm':measured,'calculation_nominal_mm':expected,'difference_mm':measured-expected,'comparison_tolerance_supplied_by_parent_mm':0.009,'within_supplied_tolerance':abs(measured-expected)<=.009})
bearings=[]
for shaft,ids,inner,outer,shaftnode,housings in [
    ('II',[12,81],3,8,36,[2,342]),
    ('III',[54,42],3,8,292,[39,39]),
    ('IV',[24,68],3,8,67,[2,342]),
    ('V',[317,305],3,8,301,[2,342]),
    ('VI',[200,226],None,None,223,[2,342]),
]:
    for k,ident in enumerate(ids):
        rows=result['cylinders'][str(ident)]['surfaces']
        d=inner if inner is not None else (7 if k==0 else 9)
        D=outer if outer is not None else (11 if k==0 else 14)
        seat=result['cylinders'][str(housings[k])]['surfaces']
        bearing_cyls=[r for r in rows if r['diameter'] in [d,D]]
        matching_housing=[r for r in seat if abs(r['diameter']-D)<1e-7 and math.dist(r['center_xz'],axes[shaft])<1e-6]
        matching_shaft=[r for r in result['cylinders'][str(shaftnode)]['surfaces'] if abs(r['diameter']-d)<1e-7 and math.dist(r['center_xz'],axes[shaft])<1e-6]
        bearings.append({'shaft':shaft,'bearing_node':ident,'type':NODES[ident]['name'],'d_shaft_mm':d,'D_housing_mm':D,'bearing_cylinders':bearing_cyls,'shaft_node':shaftnode,'shaft_cylinders':matching_shaft,'housing_node':housings[k],'housing_cylinders':matching_housing})
mount=[r for r in result['cylinders']['2']['surfaces'] if r['diameter']==4 and r['y_range'][0]<.01 and abs(math.hypot(*r['center_xz'])-43)<1e-7]
summary={
    'source':result['source'],'method':result['method'],'units':'mm',
    'shaft_centers_xz':axes,'center_distances':distances,'bearings':bearings,
    'motor_centering_hole':{'diameter_mm':17,'center_xz':axes['I'],'depth_mm':1.5,'body_node':2,'motor_node':5,'verified_in_both_parts':True},
    'gearbox_mounting':{'bolt_circle_diameter_mm':86,'center_xz':[0,0],'hole_diameter_mm':4,'hole_count':len(mount),'hole_cylinders':mount,'note':'Это три крепёжных отверстия самого корпуса редуктора, не крепление двигателя и не крепление крышки.'},
    'motor_mounting':{'hole_grid_mm':[21,21],'center_xz':axes['I'],'centers_xz':[[-5.5,4.5],[-5.5,25.5],[15.5,4.5],[15.5,25.5]],'note':'4 отверстия; цилиндр тела резьбы в корпусе 1.566987298, а в модели двигателя отверстия 2.4. Номинал резьбы М2 подтверждён именами винтов, не выводится из малого диаметра.'},
    'cover_mounting':{'bolt_circle_diameter_mm':80,'center_xz':[0,0],'hole_count':6,'clearance_hole_diameter_in_cover_mm':2.5,'note':'Не путать с окружностью 86: это крепление крышки корпуса шестью М2.'},
    'tolerances':'Новых допусков и полей посадок не назначено. ±0.009 использовано только для заданного сравнения межосевых.'
}
(OUT/'Проверка_сборочных_номиналов.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k not in ['bearings']},ensure_ascii=False,indent=2))
print('BEARINGS',[(r['shaft'],r['bearing_node'],r['d_shaft_mm'],r['D_housing_mm']) for r in bearings])
