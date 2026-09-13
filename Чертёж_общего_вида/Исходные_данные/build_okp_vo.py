from pathlib import Path
import json,fitz,sys,math
sys.path.insert(0,str(Path(__file__).parent))
from okp_pdf_helpers import Sheet,MM
DATA=Path(__file__).parent/'Проекции';OUT=Path(__file__).resolve().parent.parent;OUT.mkdir(exist_ok=True)
doc=fitz.open();s=Sheet(doc);maps={};boxes={}
layout=[
 ('gearbox',65,55,2.5,(0,1,0),(-1,0,0),'А–А (2,5:1)'),
 ('long',345,55,2.5,(1,0,0),(0,1,0),'Б–Б (2,5:1)'),
 ('clutch',560,60,4,(1,0,0),(0,1,0),'В–В (4:1)'),
 ('support',755,60,4,(1,0,0),(0,1,0),'Е–Е (4:1)'),
 ('lvk10',565,220,4,(0,-1,0),(1,0,0),'Поз. 33 (4:1)'),
 ('lvk11',710,220,2.5,(0,1,0),(-1,0,0),'Поз. 48 (2,5:1)'),
 ('side',75,420,1,(1,0,0),(0,1,0),''),
 ('front',325,420,1,(0,1,0),(-1,0,0),'А (1:1)')]
for name,x,y,scale,n,xd,title in layout:
 p=DATA/(name+'_clean.json')
 if '--preview' in sys.argv and not p.exists():p=DATA/(name+'.json')
 assert p.exists(),p
 d=json.loads(p.read_text());m,b=s.view(d,x,y,scale,n,xd,d.get('sections'));maps[name]=m;boxes[name]=b
 if title:s.text((b[0]+b[2])/2,24 if name=='long' else y-17,title,7,align='center')
 print(name,b,flush=True)
# Axes of shafts / rack, projected from model coordinates.
def axis(name,a,b):s.line(maps[name](a),maps[name](b),.18,'[18 4 2 4] 0')
for x,z in [(5,15),(5,-.05),(14.23,-9.28),(4.89,-18.61),(-6.667,-11.936),(-15.33,3.07)]:
 axis('gearbox',(x-3,34,z),(x+3,34,z));axis('gearbox',(x,34,z-3),(x,34,z+3))
axis('long',(-15.33,-2,3.07),(-15.33,67,3.07))
axis('clutch',(-6.667,-1,-11.936),(-6.667,42,-11.936))
for name,r in [('lvk10',15.6),('lvk11',25)]:
 axis(name,(-15.33-r,0,3.07),(-15.33+r,0,3.07));axis(name,(-15.33,0,3.07-r),(-15.33,0,3.07+r))
axis('support',(17,49.5,-42),(17,49.5,-10));axis('support',(17,39,-21.93),(17,61,-21.93))
axis('side',(5,-65,15),(5,45,15));axis('side',(-15.33,-2,3.07),(-15.33,69,3.07))
axis('front',(-80,49.5,-21.93),(56,49.5,-21.93));axis('front',(-15.33,40,-43),(-15.33,40,44))
# Positions: unchanged numbering from the user's existing ТСЧ.docx.
def pos(view,q,shelf,num,left=False):s.leader(maps[view](q),shelf,num,left)
for q,sh,num in [((-38,20,10),(42,94),40),((5,6,15),(115,37),52),((10,10,8),(45,145),29),((5,25,-.05),(43,174),23),((19,23,-8),(43,205),30),((14.23,29,-9.28),(46,232),24),((4.89,31,-18.61),(109,301),25),((9,13,-25),(157,315),31),((-10,24,-20),(218,307),32),((-6.667,32,-11.936),(278,221),26),((-24,14,7),(283,135),33)]:pos('gearbox',q,sh,num)
for q,sh,num in [((-15.33,25,3.07),(522,133),22),((-15.33,39,36),(508,43),46),((-15.33,41,7),(527,170),45),((-15.33,48,-30),(510,264),47)]:pos('long',q,sh,num)
pos('clutch',(-6.667,11,-11.936),(557,163),26)
pos('clutch',(-6.667,23.5,-2),(573,43),32)
pos('clutch',(-6.667,37.3,-14.6),(724,166),11,True)
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
def cut_vertical(view,q1,q2,label,direction=1):
 a=maps[view](q1);b=maps[view](q2)
 for pt,sign in [(a,-1),(b,1)]:
  inner=(pt[0],pt[1]+sign*8);s.line(pt,inner,.8)
  tail=(pt[0]-direction*12,pt[1]+sign*3);tip=(pt[0],pt[1]+sign*3)
  s.line(tail,tip,.35);s.arrow(tip,tail,3)
  s.text(tail[0]-direction*2,tail[1]-3,label,5,align='center')
cut_vertical('side',(0,34.5,47),(0,34.5,-49),'А',-1)
cut_vertical('front',(-15.33,0,48),(-15.33,0,-49),'Б',1)
cut_vertical('gearbox',(-6.667,0,-.5),(-6.667,0,-24),'В',1)
cut_vertical('front',(17.17,0,-8),(17.17,0,-40),'Е',1)
# Viewing direction A for the overall front view.
tip=maps['side']((0,71,-4));tail=(tip[0]+16,tip[1]);s.line(tail,tip,.35);s.arrow(tip,tail,3);s.text(tail[0],tail[1]-4,'А',5)
# Dimensions supported by the supplied model / assembly drawing.
m=maps['front'];a=m((179.07,0,-38.63));b=m((-77.03,0,-21.93));s.dimh(a[0],b[0],570,a[1],b[1],'256,1*')
m=maps['side'];a=m((0,-61,15));b=m((0,66.5815286,-21.93));s.dimh(a[0],b[0],555,a[1],b[1],'127,6*')
a=m((0,0,-41));b=m((0,40,-41));s.dimh(a[0],b[0],539,a[1],b[1],'40*')
m=maps['long'];a=m((-15.33,0,39));b=m((-15.33,40,39));s.dimh(a[0],b[0],40,a[1],b[1],'40*')
# Rack / bushing fit, copied from the supplied assembly drawing.
a=maps['support']((17,46,-21.93));s.poly([a,(745,180),(809,180)],.18);s.arrow(a,(745,180),2.5);s.text(775,178,'⌀7H7/h6',3.5,align='center')
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
doc.set_metadata({'title':'Следящий привод. Чертеж общего вида','author':'','subject':'По STEP-модели пользователя; позиции по ТСЧ.docx','keywords':'РЛ5.41.00.00.00 ВО, А1'})
file=OUT/('Промежуточный.pdf' if '--preview' in sys.argv else 'Чертёж_общего_вида_А1.pdf');doc.save(file,garbage=4,deflate=True)
s.p.get_pixmap(matrix=fitz.Matrix(.95,.95),alpha=False).save(str(OUT/'Предпросмотр.png'))
(OUT/'Чертёж_общего_вида_А1.svg').write_text(s.p.get_svg_image(text_as_path=True))
print('SAVED',file,flush=True)
