"""Vector A1 assembly drawing of РЛ5.41.01.00.00, from saved model projections."""
from pathlib import Path
import sys, json, math, fitz
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT=HERE.parent
SOURCE=ROOT/'Чертёж_общего_вида/Исходные_данные/Редакция_2'
sys.path.insert(0,str(SOURCE))
from okp_pdf_helpers import Sheet,MM,F
DATA=HERE/'Проекции'
CODE='РЛ5.41.01.00.00 СБ'
spec=json.loads((HERE/'Состав_и_позиции_по_структурной_схеме.json').read_text())
geom=json.loads((DATA/'Состав_и_геометрия.json').read_text())
gears={g['id']:g for g in geom['gears']}
doc=fitz.open();s=Sheet(doc);maps={};boxes={};datasets={}

layout=[('open',65,52,2.5,'А–А (2,5:1)'),('front',354,52,2.5,''),
        ('side',657,52,2.5,''),('section_b',74,314,2.5,'Б–Б (2,5:1)'),
        ('section_c',344,314,2.5,'В–В (2,5:1)'),('section_d',614,314,2.5,'Г–Г (2,5:1)')]
for name,x,y,scale,title in layout:
    filename='section_a' if name=='open' else name
    d=json.loads((DATA/(filename+'.json')).read_text());datasets[name]=d
    meta=d['metadata'];m,b=s.view(d,x,y,scale,meta['normal'],meta['xdir'],d.get('sections'))
    maps[name]=m;boxes[name]=b
    if title:s.text((b[0]+b[2])/2,20 if name=='open' else y-14,title,7,align='center')
    print(name,[round(v,2)for v in b],flush=True)

def axis(view,a,b):s.line(maps[view](a),maps[view](b),.18,'[18 4 2 4] 0')
AXES=datasets['section_b']['metadata']['axes']
for view in ['open','front']:
    for x,z in AXES.values():
        axis(view,(x-3,0,z),(x+3,0,z));axis(view,(x,0,z-3),(x,0,z+3))
for name in ['section_b','section_c','section_d']:
    for label in datasets[name]['metadata']['shaft_pair']:
        x,z=AXES[label];axis(name,(x,-3,z),(x,68,z))
for label in ['VI']:
    x,z=AXES[label];axis('side',(x,-3,z),(x,68,z))
axis('front',(-52,49.5,-21.93),(27,49.5,-21.93))

# Conventional pitch/initial curves at the model's unshifted nominal centres.
for view,ids in [('front',[389])]:
    for gid in ids:
        g=gears[gid];x,z=g['center_xz'];c=maps[view]((x,0,z))
        s.p.draw_circle(fitz.Point(c[0]*MM,c[1]*MM),g['pitch_radius']*2.5*MM,
                        width=.18*MM,dashes='[18 4 2 4] 0',color=(0,0,0))
pitch=json.loads((DATA/'section_a_pitch.json').read_text())
for path in pitch['visible']:
    s.poly([maps['open']((-q[0],0,q[1]))for q in path],.18,'[18 4 2 4] 0')

# Root and initial generators in axial cuts; only shafts actually on the plane.
for name in ['section_b','section_c','section_d']:
    meta=datasets[name]['metadata'];n=meta['normal'];p=meta['plane_point'];yd=( -n[2],0,n[0])
    for gid,g in gears.items():
        x,z=g['center_xz'];distance=(x-p[0])*n[0]+(z-p[2])*n[2]
        if abs(distance)>.01:continue
        for radius,width,dash in [(g['root_radius'],.5,None),(g['pitch_radius'],.18,'[10 2 1 2] 0')]:
            for sign in [-1,1]:
                qs=[(x+sign*radius*yd[0],y,z+sign*radius*yd[2])for y in g['tooth_y_range']]
                s.line(maps[name](qs[0]),maps[name](qs[1]),width,dash)

def leader(view,world,shelf,position,left=False):
    s.leader(maps[view](world),shelf,position,left)

# Components visible with the end cover removed.
for world,shelf,pos in [
    ((34,34.5,17.5),(39,81),43),((5,7,9),(36,121),34),
    ((14.225,20,-3),(36,158),35),((4.891,15,-25),(61,286),36),
    ((-25,13.2,12.5),(250,35),54),
    ((-16,12,12),(226,25),57),((-9.16,14,12.77),(284,59),28),
    ((20,30,-9.275),(41,210),62),((22.23,38,-9.28),(43,244),7),
    ((-6.667,29,-11.936),(282,243),27),
]:leader('open',world,shelf,pos)

# Outer assembly, reference positions match the current structural scheme.
for world,shelf,pos in [
    ((20,40,20),(329,74),49),((-15.33,61,3.07),(560,106),9),
    ((-20,48,13),(566,60),59),((-30.33,48,3.07),(568,142),29),
    ((-27,50,-11),(568,184),52),((17,55,-24),(331,267),53),
    ((-12,43,-32),(477,286),60),((10.67,43,-26.03),(341,289),6),
    ((34.64,41,20),(328,44),8),
]:leader('front',world,shelf,pos)

# Anchors lie in the actual section plane, on the named shaft's radius.
def radial(view,shaft,y,r):
    n=datasets[view]['metadata']['normal'];cx,cz=AXES[shaft]
    return (cx-r*n[2],y,cz+r*n[0])
for view,shaft,y,r,shelf,pos in [
    ('section_b','II',26,0,(50,420),24),
    ('section_b','III',32,0,(252,366),25),
    ('section_b','III',31.7,3.2,(252,390),30),
    ('section_b','III',36.2,1.7,(252,414),38),
    ('section_b','III',24.3,0,(252,440),20),
    ('section_b','II',3.5,2.8,(46,457),13),
    ('section_b','II',41,4,(251,471),45),
    ('section_b','II',40.25,6.5,(251,499),39),
    ('section_c','IV',20,0,(316,448),26),
    ('section_c','V',22,4.5,(508,340),31),
    ('section_c','V',25.3,5.5,(508,363),50),
    ('section_c','V',27.5,5.5,(508,386),56),
    ('section_c','V',30.5,5.5,(508,409),58),
    ('section_c','V',34.5,6,(508,432),33),
    ('section_c','V',41,3.5,(508,467),47),
    ('section_c','IV',41,3.5,(508,494),46),
    ('section_d','VI',27,0,(589,400),23),
    ('section_d','VI',3.75,4.5,(587,370),14),
    ('section_d','VI',36.5,5.8,(797,365),15),
    ('section_d','VI',34.5,5.5,(797,391),11),
    ('section_d','VI',41,7,(797,417),48),
    ('section_d','VI',40.25,7.5,(797,443),42),
    ('section_d','VI',52,4.7,(797,469),18),
    ('section_d','VI',44,17,(797,495),55),
    ('section_d','VI',15.7,0,(588,437),22),
    ('section_d','VI',9.5,7,(588,345),51),
]:leader(view,radial(view,shaft,y,r),shelf,pos)

# Longitudinal cutting planes are indicated on the end view.
for name,label,extension in [('section_b','Б',17),('section_c','В',20),('section_d','Г',25)]:
    meta=datasets[name]['metadata'];pair=meta['shaft_pair'];n=meta['normal']
    if len(pair)==2:
        a,b=[AXES[k]for k in pair];v=(b[0]-a[0],b[1]-a[1]);length=math.hypot(*v);v=(v[0]/length,v[1]/length)
        av=a[0]*v[0]+a[1]*v[1]
        radius=58 if name=='section_c' else 50
        disc=math.sqrt(av*av+radius**2-a[0]**2-a[1]**2)
        endpoints=[(a[0]+t*v[0],0,a[1]+t*v[1])for t in [-av-disc,-av+disc]]
    else:
        a=AXES[pair[0]];v=(0,1);endpoints=[(a[0],0,-50),(a[0],0,50)]
    for k,q in enumerate(endpoints):
        pt=maps['open'](q);sign=-1 if k==0 else 1
        other=maps['open']((q[0]+sign*3*v[0],0,q[2]+sign*3*v[1]))
        s.line(pt,other,.8)
        tip=maps['open']((q[0]+sign*v[0],0,q[2]+sign*v[1]))
        tail=maps['open']((q[0]+sign*v[0]+5*n[0],0,q[2]+sign*v[1]+5*n[2]))
        s.line(tail,tip,.3);s.arrow(tip,tail,3)
        s.text(tail[0],tail[1]-3,label,5,align='center')

# Actual transverse plane, retaining the half toward the motor interface.
for z,sign in [(46,1),(-46,-1)]:
    pt=maps['side']((0,34.5,z));outer=maps['side']((0,34.5,z+sign*3));s.line(pt,outer,.8)
    tip=maps['side']((0,34.5,z+sign));tail=(tip[0]+12,tip[1])
    s.line(tail,tip,.3);s.arrow(tip,tail,3);s.text(tail[0],tail[1]-3,'А',5,align='center')
axis('side',(-15.33,42,25.567337),(-15.33,50,25.567337))

# Dimensions: model geometry checked independently against calculation/source drawing.
m=maps['side'];a=m((0,0,43.27));b=m((0,40,43.27));s.dimh(a[0],b[0],36,a[1],b[1],'40*')
a=m((0,0,-43.27));b=m((0,64.5,3.07));s.dimh(a[0],b[0],286,a[1],b[1],'64,5*')
m=maps['front'];a=m((-48.33,0,-43.27));b=m((40.58971,0,-43.27));s.dimh(a[0],b[0],277,a[1],b[1],'88,9*')
c=m((0,0,0));s.p.draw_circle(fitz.Point(c[0]*MM,c[1]*MM),43*2.5*MM,width=.18*MM,dashes='[18 4 2 4] 0',color=(0,0,0))
for world,shelf,text in [((21.5,0,37.23909),(369,31),'⌀4; 3 отв.'),((-30.4056,0,30.4056),(546,31),'⌀86*')]:
    pt=m(world);s.poly([pt,shelf,(shelf[0]+26,shelf[1])],.18);s.arrow(pt,shelf,2.5);s.text(shelf[0]+2,shelf[1]-2,text,3.5)
for name,value in [('section_b','13,05 ±0,009'),('section_c','13,35 ±0,009'),('section_d','17,325 ±0,009')]:
    meta=datasets[name]['metadata'];pair=meta['shaft_pair']
    if len(pair)!=2:continue
    pts=[maps[name]((AXES[k][0],0,AXES[k][1]))for k in pair];pts.sort(key=lambda p:p[1])
    x=boxes[name][0]-14;s.dimv(pts[0][1],pts[1][1],x,pts[0][0],pts[1][0],value)
for view,world,shelf,text in [('open',(5,0,23.5),(72,33),'⌀17H8'),
                              ('side',(23.67,49.5,-18.43266),(595,254),'⌀7H7')]:
    pt=maps[view](world);s.poly([pt,shelf,(shelf[0]+25,shelf[1])],.18);s.arrow(pt,shelf,2.5)
    s.text(shelf[0]+2,shelf[1]-2,text,3.5)
m=maps['front'];a=m((-48.33,0,43.27018));b=m((-48.33,0,-43.27018))
s.dimv(a[1],b[1],637,a[0],b[0],'86,5*')

# Existing requirements only: no inferred bearing fits or clutch setting.
for i,line in enumerate(['1. * Размеры для справок.',
                         '2. Точность зубчатых передач: степень 6, вид сопряжения H.',
                         '3. Погрешность редуктора на выходном валу — не более 30′.',
                         '4. Межосевое расстояние валов поз. 25 и 26 — 13,2 ±0,009 мм.',
                         '5. Межосевое расстояние валов поз. 27 и 23 — 17,325 ±0,009 мм.']):
    s.text(30,553+i*8,line,3.5)

# Preserve the main inscription appearance of the existing project.
s.rect(20,5,816,584,.6)
stamp=fitz.open(SOURCE/'Основная_надпись_по_образцу.pdf');p=stamp[0]
fontpath=SOURCE/'GOST_из_габаритного.ttf';font=fitz.Font(fontfile=str(fontpath));p.insert_font(fontname='ReducerStamp',fontfile=str(fontpath))
def clear_mm(x0,y0,x1,y1):
    p.add_redact_annot(fitz.Rect(x0*MM,y0*MM,x1*MM,y1*MM),fill=(1,1,1))
    p.apply_redactions(images=0,graphics=0)
def stamptext(cx,y,text,size):
    p.insert_font(fontname='ReducerStamp',fontfile=str(fontpath))
    pt=fitz.Point(cx*MM-font.text_length(text,fontsize=size)/2,y*MM)
    p.insert_text(pt,text,fontname='ReducerStamp',fontsize=size,morph=(pt,fitz.Matrix(1,0,.364,1,0,0)))
clear_mm(65.3,.3,184.7,14.6);stamptext(124.5,11.2,CODE,29.16547)
clear_mm(65.3,15.3,134.7,39.7);stamptext(100,24.8,'Редуктор',20.73208);stamptext(100,34.8,'Сборочный чертеж',20.73208)
clear_mm(150.3,20.3,166.7,34.7)
clear_mm(167.3,20.3,184.7,34.7);stamptext(176,29,'2,5:1',18)
target=fitz.Rect(651*MM,534*MM,836*MM,589*MM);s.p.show_pdf_page(target,stamp,0)
from restore_frame import restore_stamp_frame
restore_stamp_frame(s.p)
s.rect(20,5,70,14,.35);s.text(87,9,CODE,3.5,rotate=180)
s.text(833,592,'Формат А1',2.5,align='right')
doc.set_metadata({'title':'Редуктор. Сборочный чертеж','subject':CODE,'author':'','keywords':'А1, STEP, сборочный чертеж редуктора'})
pdf=OUT/'Редуктор_сборочный_чертёж_А1.pdf';doc.save(pdf,garbage=4,deflate=True)
s.p.get_pixmap(matrix=fitz.Matrix(.8,.8)).save(OUT/'Предпросмотр.png')
(OUT/'Редуктор_сборочный_чертёж_А1.svg').write_text(s.p.get_svg_image(text_as_path=True))
(HERE/'Компоновка.json').write_text(json.dumps(boxes,ensure_ascii=False,indent=2))
print('SAVED',pdf)
