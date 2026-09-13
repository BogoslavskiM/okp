from pathlib import Path
import json,fitz,sys,math
sys.path.insert(0,str(Path(__file__).parent))
from okp_pdf_helpers import Sheet,MM
DATA=Path(__file__).parent/'Проекции';OUT=Path(__file__).resolve().parents[2];OUT.mkdir(exist_ok=True)
doc=fitz.open();s=Sheet(doc);maps={};boxes={};screen_paths={}
layout=[
 ('gearbox',65,55,2.5,(0,1,0),(-1,0,0),'А–А (2,5:1)'),
 ('long',345,55,2.5,(1,0,0),(0,1,0),'Б–Б (2,5:1)'),
 ('clutch',560,60,4,(1,0,0),(0,1,0),'В–В (4:1)'),
 ('support',755,60,4,(1,0,0),(0,1,0),'Е–Е (4:1)'),
 ('lvk10',565,220,4,(0,-1,0),(1,0,0),'Поз. 33 (4:1)'),
 ('lvk11',710,220,2.5,(0,1,0),(-1,0,0),'Поз. 48 (2,5:1)'),
 ('microswitch2',405,270,4,(1,0,0),(0,1,0),'Д–Д (4:1)'),
 ('side',75,420,1,(1,0,0),(0,1,0),''),
 ('front',325,420,1,(0,1,0),(-1,0,0),'Г (1:1)')]
for name,x,y,scale,n,xd,title in layout:
 revised={'long':'long_revised_clean.json'}
 p=DATA/revised.get(name,name+'_clean.json')
 if '--preview' in sys.argv and not p.exists():p=DATA/(name+'.json')
 assert p.exists(),p
 d=json.loads(p.read_text())
 if name=='long':
  # Item 140 (rack guide) contains one coplanar STEP seam shared by two
  # adjacent pieces of the same cut material.  It is useful as a visible
  # geometric edge, but it must not participate in the even/odd hatch fill:
  # doing so creates an odd intersection and leaves the upper flange blank.
  for sect in d.get('sections',[]):
   if sect.get('id')==140:
    sect['edges']=[e for e in sect['edges'] if not (
     len(e)==2
     and all(abs(q[2]+27.93266288594)<1e-3 for q in e)
     and abs(min(q[1] for q in e)-40.0)<1e-3
     and abs(max(q[1] for q in e)-43.0)<1e-3
    )]
 if name=='front':
  # The STEP rack has sub-millimetre edge offsets (0.100 and 0.146 mm)
  # between adjoining faces along its lower generatrix.  At 1:1 these do not
  # describe a readable feature and make one nominally straight outline look
  # broken.  Use the exact lower datum from the rack bounding geometry
  # (top -18.4326628857 minus the nominal 7 mm height), while retaining the
  # real visibility gaps where the two supports cover the rack.
  rack_lower=-25.4326628857024
  for path_index in (1615,1616,1682):
   for point in d['visible'][path_index]:point[1]=rack_lower
  d['visible'][1681]=[]  # obsolete 0.1-mm vertical transition
  d['visible'][1680][-1][1]=rack_lower
 m,b=s.view(d,x,y,scale,n,xd,d.get('sections'));maps[name]=m;boxes[name]=b
 pts=[q for path in d['visible'] for q in path]
 xmin=min(q[0] for q in pts);ymax=max(q[1] for q in pts)
 screen_paths[name]=[
  [(x+(q[0]-xmin)*scale,y+(ymax-q[1])*scale) for q in path]
  for path in d['visible']
 ]
 if title:s.text((b[0]+b[2])/2,24 if name=='long' else y-17,title,7,align='center')
 print(name,b,flush=True)
# The lower keyway flank in the detailed STEP contains several coincident
# tangent/chamfer strokes that look like escaped thread lines at 4:1.  Clear
# only that lower fragment and retain one continuous conventional contour.
vv_x1,vv_x2=591.3,605.5
vv_root_y=111.135
vv_axis_y=maps['clutch']((-6.667,0,-11.9365530061521))[1]
vv_tip_y=2*vv_axis_y-88.558
s.p.draw_rect(fitz.Rect((vv_x1-.55)*MM,(vv_root_y-.55)*MM,
                       (vv_x2+.55)*MM,(vv_tip_y+.55)*MM),
              color=None,fill=(1,1,1))
s.line((vv_x1,vv_root_y),(vv_x1,vv_tip_y),.5)
s.line((vv_x1,vv_tip_y),(vv_x2,vv_tip_y),.5)
s.line((vv_x2,vv_tip_y),(vv_x2,vv_root_y),.5)

# Suppress the paired chamfer/tangent strokes at the root of the same wheel.
# At the sheet scale they read as an escaped thread.  Retain one conventional
# root contour above and below the shaft, continuous with the tooth envelope.
vv_root_x0=572.0
for y in (95.135,111.135):
 s.p.draw_rect(fitz.Rect((vv_root_x0-.2)*MM,(y-.85)*MM,
                        (vv_x1+.25)*MM,(y+.35)*MM),
               color=None,fill=(1,1,1))
 s.line((vv_root_x0,y),(vv_x1,y),.5)
s.line((vv_x1,95.135),(vv_x1,88.558),.5)

# In B-B a longitudinal plane meets each external retaining ring twice.  The
# STEP model already contains the correct d1=8.5 groove in shaft VI.  Mask the
# coincident hub seam, close each cut contour and hatch it separately so every
# upper/lower pair reads as one ring in its groove.
for axial0,axial1 in ((34.0,35.0),(45.5,46.5)):
 for z0,z1 in ((-2.8826629859,-1.1826629859),
               (7.3173372141,9.0173372141)):
  a=maps['long']((-15.33,axial0,z1))
  b=maps['long']((-15.33,axial1,z0))
  x0,x1=sorted((a[0],b[0]));y0,y1=sorted((a[1],b[1]))
  s.p.draw_rect(fitz.Rect(x0*MM,y0*MM,x1*MM,y1*MM),
                color=(0,0,0),fill=(1,1,1),width=.5*MM)
  s.line((x0+.18,y1-.18),(x1-.18,y0+.18),.15)

# The B-B plane meets the wire of the two clutch springs obliquely.  Their
# exact STEP silhouettes become a dense spiral when projected end-on.  GOST
# 2.401 permits only the cut traces of the coils to be retained; with the
# 0.8-mm wire shown at 2.5:1 gives 2-mm sections.  Use one clean circular
# section with a single hatch stroke at each actual intersection; the full
# end-on helix is deliberately not repeated.  Their centres come from the
# STEP intersection loops at x=-15.33.
for wy,wz in ((45.61475506,13.18365594),
              (44.18385727,-9.96429940),
              (46.90119367,-7.92592501)):
 p=maps['long']((-15.33,wy,wz))
 s.p.draw_circle(fitz.Point(p[0]*MM,p[1]*MM),1.0*MM,
                 color=(0,0,0),fill=(1,1,1),width=.35*MM)
 s.line((p[0]-.65,p[1]+.65),(p[0]+.65,p[1]-.65),.18)

# Redraw the adjacent M2 screw conventionally so its complete head and its
# threaded shank remain legible without the exact spring helix crossing them.
# The source STEP geometry is untouched.
screw_cy=maps['long']((-15.33,42,-6.4326629851))[1]
screw_shoulder=maps['long']((-15.33,42,-6.4326629851))[0]
screw_head_tip=maps['long']((-15.33,43.387,-6.4326629851))[0]
screw_tip=maps['long']((-15.33,37,-6.4326629851))[0]
screw_head_r=1.9*2.5;screw_shank_r=1.0*2.5
head_arc=[]
for i in range(13):
 angle=-math.pi/2+i*math.pi/12
 head_arc.append((screw_shoulder+(screw_head_tip-screw_shoulder)*math.cos(angle),
                  screw_cy+screw_head_r*math.sin(angle)))
screw_outline=head_arc+[
 (screw_shoulder,screw_cy+screw_shank_r),
 (screw_tip+.55,screw_cy+screw_shank_r),
 (screw_tip,screw_cy+screw_shank_r-.55),
 (screw_tip,screw_cy-screw_shank_r+.55),
 (screw_tip+.55,screw_cy-screw_shank_r),
 (screw_shoulder,screw_cy-screw_shank_r),
]
s.poly(screw_outline,.5,fill=(1,1,1),close=True)
screw_root_r=.78*2.5
for sign in (-1,1):
 s.line((screw_tip+.55,screw_cy+sign*screw_root_r),
        (screw_shoulder-.8,screw_cy+sign*screw_root_r),.18)
 s.line((screw_shoulder,screw_cy+sign*screw_shank_r),
        (screw_shoulder-.8,screw_cy+sign*screw_root_r),.18)

# The manufacturer STEP contains a diamond surface texture inside the
# purchased microswitch.  It is not useful in the general-view section and
# reads as crossed section hatching.  Keep the case boundary and suppress only
# that internal texture.
s.p.draw_rect(fitz.Rect(431.05*MM,308.15*MM,449.65*MM,324.45*MM),
              color=None,fill=(1,1,1))

# Conventional assembled external M8 thread on shaft VI.  The STEP represents
# only smooth cylinders and the nut bore, so its raw overlap produced broken
# steps.  Clear just the engagement band and redraw the shaft thread, which has
# priority over the internal thread of the nut in an assembled section.
thread_center=maps['long']((-15.33,60,3.06733721406))[1]
thread_major=4.0*2.5
thread_root=3.323418*2.5
thread_x0=maps['long']((-15.33,57.5,3.06733721406))[0]
thread_chamfer=maps['long']((-15.33,64.0,3.06733721406))[0]
thread_x1=maps['long']((-15.33,64.5,3.06733721406))[0]
s.p.draw_rect(fitz.Rect((thread_x0-.2)*MM,(thread_center-thread_major-.25)*MM,
                       (thread_x1+.2)*MM,(thread_center+thread_major+.25)*MM),
              color=None,fill=(1,1,1))
for sign in (-1,1):
 major_y=thread_center+sign*thread_major
 root_y=thread_center+sign*thread_root
 end_y=thread_center+sign*(3.5*2.5)
 shoulder_y=thread_center+sign*(4.5*2.5)
 s.line((thread_x0,shoulder_y),(thread_x0,major_y),.5)
 s.line((thread_x0,major_y),(thread_chamfer,major_y),.5)
 s.line((thread_chamfer,major_y),(thread_x1,end_y),.5)
 s.line((thread_x0+.75,root_y),(thread_chamfer,root_y),.25)
 s.line((thread_x0,major_y),(thread_x0+.75,root_y),.25)
s.line((thread_x1,thread_center-3.5*2.5),
       (thread_x1,thread_center+3.5*2.5),.5)

# On the side view the exact teeth of the split cylindrical wheel collapse
# into a solid black band.  GOST 2.402 shows a cylindrical gear in this
# projection by the addendum-surface envelope; the individual teeth are not
# drawn.  Keep the joint between the two wheel halves and the two pitch-
# surface generatrices.  Use model coordinates so the overlay follows the
# actual 8 mm face width and da=46 / d=45 geometry.
gear_side_left = maps['side']((0,42,3.06733721406))[0]
gear_side_joint = maps['side']((0,46,3.06733721406))[0]
gear_side_right = maps['side']((0,50,3.06733721406))[0]
gear_side_top = maps['side']((0,46,3.06733721406+23))[1]
gear_side_bottom = maps['side']((0,46,3.06733721406-23))[1]
pitch_top = maps['side']((0,46,3.06733721406+22.5))[1]
pitch_bottom = maps['side']((0,46,3.06733721406-22.5))[1]
s.p.draw_rect(
 fitz.Rect((gear_side_left-.65)*MM,(gear_side_top-.65)*MM,
           (gear_side_right+.65)*MM,(gear_side_bottom+.65)*MM),
 color=None,fill=(1,1,1))
s.p.draw_rect(
 fitz.Rect(gear_side_left*MM,gear_side_top*MM,
           gear_side_right*MM,gear_side_bottom*MM),
 color=(0,0,0),width=.5*MM)
s.line((gear_side_joint,gear_side_top),
       (gear_side_joint,gear_side_bottom),.5)
for y in (pitch_top,pitch_bottom):
 s.line((gear_side_left-1.5,y),(gear_side_right+1.5,y),
        .18,'[18 4 2 4] 0')

# Axes of shafts / rack, projected from model coordinates.  All axes have one
# weight and dash pattern.  Gear axes extend 3 mm beyond their tooth tips,
# rather than looking like small crosshairs at the centres.
def axis(name,a,b):s.line(maps[name](a),maps[name](b),.25,'[18 4 2 4] 0')
gear_axes=[
 (5,15,6.15),             # Z1
 (5,-.05,15.075),         # Z2
 (14.225,-9.275,13.5),    # Z4
 (4.89119,-18.60881,13.65), # Z6
 (-6.667,-11.93568,13.8), # Z8
 (-15.33,3.07,17.35),     # Z10
]
for x,z,r in gear_axes:
 axis('gearbox',(x-r,34,z),(x+r,34,z));axis('gearbox',(x,34,z-r),(x,34,z+r))
axis('long',(-15.33,-2,3.07),(-15.33,67,3.07))
axis('clutch',(-6.667,-1,-11.936),(-6.667,42,-11.936))
for name,r in [('lvk10',15.6),('lvk11',25)]:
 axis(name,(-15.33-r,0,3.07),(-15.33+r,0,3.07));axis(name,(-15.33,0,3.07-r),(-15.33,0,3.07+r))
axis('support',(17,49.5,-42),(17,49.5,-10));axis('support',(17,39,-21.93),(17,61,-21.93))
# Axes of the two M1.6 fasteners in the second microswitch section.
for z in (-35.632663,-42.132663):
 axis('microswitch2',(131.419995,48,z),(131.419995,61,z))
axis('side',(5,-65,15),(5,45,15));axis('side',(-15.33,-2,3.07),(-15.33,69,3.07))
axis('front',(-80,49.5,-21.93),(56,49.5,-21.93))
# Output shaft VI is seen end-on in view Г.  Its centre coincides with the
# Z11 wheel centre.  Draw the two perpendicular centre lines through the
# exact centre and extend them 3 mm beyond the 23-mm tooth-tip radius.  The
# previous vertical line ran almost from Б to Б and looked like a cutting
# plane rather than a centre line.
shaft_vi_x=-15.33
shaft_vi_z=3.06733711406
shaft_vi_axis_r=26
axis('front',(shaft_vi_x,40,shaft_vi_z-shaft_vi_axis_r),
             (shaft_vi_x,40,shaft_vi_z+shaft_vi_axis_r))
axis('front',(shaft_vi_x-shaft_vi_axis_r,40,shaft_vi_z),
             (shaft_vi_x+shaft_vi_axis_r,40,shaft_vi_z))
# Positions: unchanged numbering from the user's existing ТСЧ.docx.
def pos(view,q,shelf,num,left=None):s.leader(maps[view](q),shelf,num,left)
for q,sh,num in [((37.4,34.5,10),(42,94),40),((5,6,15),(115,37),52),((10,10,8),(45,145),29),((5,25,-.05),(43,174),23),((8,21.325,-8),(43,205),30),((14.23,29,-9.28),(46,232),24),((4.89,31,-18.61),(109,301),25),((9,13,-25),(157,315),31),((-10,24,-20),(218,307),32),((-6.667,32,-11.936),(278,221),26),((-24,14,7),(283,135),33)]:pos('gearbox',q,sh,num)
for q,sh,num in [((-15.33,64.5,5.0),(518,128),22),((-15.33,39,35),(508,43),46),((-15.33,38,9),(425,112),45),((-15.33,48,-30),(510,264),47)]:pos('long',q,sh,num)
pos('clutch',(-6.667,11,-11.936),(557,163),26)
pos('clutch',(-6.667,23.5,-2),(573,43),32)
pos('clutch',(-6.667,37.3,-14.6),(724,166),11,False)
pos('support',(17,55,-21.93),(813,161),51,True)
pos('front',(30,55,-37),(421,541),10)
pos('front',(90,40,-35.5),(363,556),41)
pos('front',(53,63,-20),(373,442),34)
pos('front',(-62,50,-21),(581,462),49)
pos('front',(-30,48,-29),(545,531),47)
pos('front',(-41.3,51,-16),(583,483),51)
pos('front',(-28,58,10),(548,397),48)
pos('side',(5,-45,15),(70,466),21,True)
pos('side',(0,20,-34),(135,525),40)
pos('side',(0,39,25),(203,409),46)
# Cutting plane traces: view arrows point toward the retained half.
def cut_vertical(view,q1,q2,label,direction=1,label_shifts=((0,0),(0,0))):
 a=maps[view](q1);b=maps[view](q2)
 for mark_index,(pt,sign) in enumerate(((a,-1),(b,1))):
  inner=(pt[0],pt[1]+sign*8);s.line(pt,inner,.8)
  # The arrow tip terminates exactly on the thick end stroke of the cutting
  # plane.  Moving it even 1 mm beyond the stroke makes the arrow visibly
  # protrude past the cutting-plane mark at the plotted scale.
  tail=(pt[0]-direction*12,pt[1]+sign*3);tip=(pt[0],pt[1]+sign*3)
  s.line(tail,tip,.35);s.arrow(tip,tail,3)
  dx,dy=label_shifts[mark_index]
  s.text(tail[0]-direction*2+dx,tail[1]-3+dy,label,5,align='center')
cut_vertical('side',(0,34.5,47),(0,34.5,-49),'А',-1)
cut_vertical('front',(-15.33,0,48),(-15.33,0,-49),'Б',1)
# The V-V cutting-plane marks belong to the same x-plane at any z.  Place the
# two short end marks in free space above and below the mechanism so neither
# the letters nor the arrows cover gear teeth and the clutch springs.
cut_vertical('gearbox',(-6.667,0,45),(-6.667,0,-45),'В',1)
# On view Г the upper Д label otherwise falls on the vertical outline of the
# left-hand stop assembly.  Move only the letter along its arrow into the
# adjacent free field; the cutting plane, end stroke and arrow stay fixed.
cut_vertical('front',(131.419995,0,-29),(131.419995,0,-48),'Д',1,
             ((6,0),(0,0)))
# Put the lower E–E end mark below the complete view.  Keeping its x coordinate
# preserves the exact cutting-plane position through the support; only the
# free end of the conventional trace moves away from the microswitch.
cut_vertical('front',(17.17,0,-8),(17.17,0,-58),'Е',1)
# Viewing direction Г for the overall front view.
tip=maps['side']((0,71,-4));tail=(tip[0]+16,tip[1]);s.line(tail,tip,.35);s.arrow(tip,tail,3);s.text(tail[0],tail[1]-4,'Г',5)
# Dimensions supported by the supplied model / assembly drawing.  Find the
# actual visible contour at every extension-line abscissa so no extension line
# begins in mid-air or inside the object.
def contour_y_at(view,x,toward):
 ys=[]
 for path in screen_paths[view]:
  for (x1,y1),(x2,y2) in zip(path,path[1:]):
   if abs(x2-x1)<1e-7:
    if abs(x-x1)<.03:ys.extend((y1,y2))
   elif min(x1,x2)-1e-7<=x<=max(x1,x2)+1e-7:
    t=(x-x1)/(x2-x1);ys.append(y1+t*(y2-y1))
 if not ys:raise ValueError(f'No contour at {view} x={x}')
 return max(ys) if toward=='below' else min(ys)

m=maps['front'];a=m((179.069994845567,0,0));b=m((-77.03377833972041,0,0))
s.dimh(a[0],b[0],570,contour_y_at('front',a[0],'below'),contour_y_at('front',b[0],'below'),'256,1*')
m=maps['side'];a=m((0,-61,0));b=m((0,66.5815286,0))
s.dimh(a[0],b[0],555,contour_y_at('side',a[0],'below'),contour_y_at('side',b[0],'below'),'127,6*')
a=m((0,0,0));b=m((0,40,0))
s.dimh(a[0],b[0],539,contour_y_at('side',a[0],'below'),contour_y_at('side',b[0],'below'),'40*')
m=maps['long'];a=m((-15.33,0,0));b=m((-15.33,40,0))
s.dimh(a[0],b[0],40,contour_y_at('long',a[0],'above'),contour_y_at('long',b[0],'above'),'40*')
# Rack / bushing fit.  A fit is attached to the cylindrical diameter with a
# proper two-ended diameter dimension through the circle; it is not a
# one-ended item leader.
c=maps['support']((17,49.5,-21.93));radius=3.5*4
angle=math.radians(-35);u=(math.cos(angle),math.sin(angle))
p1=(c[0]-u[0]*radius,c[1]-u[1]*radius)
p2=(c[0]+u[0]*radius,c[1]+u[1]*radius)
elbow=(744,180);end=(809,180)
s.poly([p2,p1,elbow,end],.18)
s.arrow(p1,c,2.5);s.arrow(p2,c,2.5)
s.text((elbow[0]+end[0])/2,178,'⌀7H7/h6',3.5,align='center')
# The wheel is intentionally omitted from B–B by the teacher's review note.
s.text((boxes['long'][0]+boxes['long'][2])/2,32,
       'Зубчатое колесо поз. 32 не показано',3.5,align='center')
# Reference pitch circle and motor/gear housing mounting circle.
c=maps['gearbox']((0,0,0));r=43*2.5;s.p.draw_circle(fitz.Point(c[0]*MM,c[1]*MM),r*MM,width=.18*MM,dashes='[18 4 2 4] 0',color=(0,0,0))
a=(c[0]-r/math.sqrt(2),c[1]-r/math.sqrt(2));s.poly([a,(74,40),(98,40)],.18);s.arrow(a,(74,40),2.5);s.text(85,38,'⌀86*',3.5,align='center')
# General-view notes and specified characteristics; do not assert unverified clutch settings.
x=624;y=397
s.text(x,y,'Технические требования',5);y+=10
for line in ['1. * Размеры для справок.','2. Номера позиций — по существующей таблице','   составных частей (ТСЧ).','3. Посадка рейки в опорах скольжения ⌀7H7/h6.','4. Муфта на разрезе В–В и колеса поз. 33 и 48', '   изображены отдельно.']:
 s.text(x,y,line,3.5);y+=6.5
y+=8;s.text(x,y,'Техническая характеристика',5);y+=10
for line in ['Усилие на выходном звене — 8 Н.','Скорость выходного звена — 0,03 м/с.','Перемещаемая масса — 1 кг.','Ход выходного звена — 60 мм.','Напряжение питания двигателя — 27 В.']:
 s.text(x,y,line,3.5);y+=6.5
s.frame(1,1)
# Copy the existing project's title-block style without altering the other views.
stamp=fitz.open(Path(__file__).parent/'Основная_надпись_по_образцу.pdf')
box=fitz.Rect((841-190)*MM,(594-60)*MM,(841-5)*MM,(594-5)*MM)
s.p.draw_rect(box,color=None,fill=(1,1,1))
s.p.show_pdf_page(box,stamp,0)

doc.set_metadata({'title':'Следящий привод. Чертеж общего вида','author':'','subject':'По STEP-модели пользователя; позиции по ТСЧ.docx','keywords':'РЛ5.41.00.00.00 ВО, А1'})
preview='--preview' in sys.argv
file=OUT/('Промежуточный.pdf' if preview else 'Чертёж_общего_вида_А1_полный_аудит.pdf');doc.save(file,garbage=4,deflate=True)
preview_stem='промежуточный' if preview else 'полный_аудит'
s.p.get_pixmap(matrix=fitz.Matrix(.95,.95),alpha=False).save(str(OUT/f'Предпросмотр_{preview_stem}.png'))
(OUT/f'Чертёж_общего_вида_А1_{preview_stem}.svg').write_text(s.p.get_svg_image(text_as_path=True))
print('SAVED',file,flush=True)
