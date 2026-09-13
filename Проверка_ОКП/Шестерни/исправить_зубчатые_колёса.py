"""Локальная замена векторных зубьев условным изображением. Исходники не изменяются."""
import fitz,json,pathlib,re,math
ROOT=pathlib.Path('/Users/makar/VSC/okp');OUT=ROOT/'Исправленные_PDF';AUDIT=ROOT/'Проверка_ОКП/Шестерни'
num=r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?'
pat=re.compile(rf'({num})\s+({num})\s+m\s+({num})\s+({num})\s+l\s+([sS])\b')
original=fitz.open(next(OUT.glob('*ГГ*pdf')))
ap=[];pts=[];start=None
for i,line_text in enumerate(original.xref_stream(5).decode('latin1').splitlines()):
 tokens=line_text.split(); op=tokens[-1] if tokens else ''
 if op in ['m','l']:
  if start is None:start=i
  pts.append([float(v)*.24 for v in tokens[:2]])
 if op in ['S','s','b','B','f','f*','B*','b*','n']:
  if pts:ap.append(dict(start=start,end=i,pts=pts))
  pts=[];start=None
original.close()
key=lambda pts:tuple(round(c,2) for p in pts for c in p)
sidekeys={key(a['pts'])for a in ap if 2039<=a['start']<=2731 or 2813<=a['start']<=3433 or 471<=a['start']<=542 or 1052<=a['start']<=1132}

def line(p,a,b,width=1.68,dashes=None):p.draw_line(a,b,color=(0,0,0),width=width,dashes=dashes,overlay=True)
def side(p):
 # Видимые границы двух половин венца; нижняя часть закрыта кронштейном.
 for x,yend in [(438.48,913.92),(449.76,922.08),(461.28,888.0)]:line(p,(x,811.44),(x,yend))
 line(p,(438.48,811.44),(461.28,811.44))
 line(p,(437,812.86),(463,812.86),.48,'[9 2 1 2] 0')

def front(p,center,r,scale,rack_intervals,tip_y):
 p.draw_circle(center,r,color=(0,0,0),width=1.68)
 pitch=45/2*72/25.4*scale
 p.draw_circle(center,pitch,color=(0,0,0),width=.48,dashes='[12 2 1 2] 0')
 for x0,x1 in rack_intervals:
  line(p,(x0,tip_y),(x1,tip_y))
  line(p,(x0,center[1]+pitch),(x1,center[1]+pitch),.48,'[12 2 1 2] 0')

def save(d,src,name):
 dst=OUT/name;d.save(dst,garbage=3,deflate=True)
 old=fitz.open(src);new=fitz.open(dst)
 assert old[0].rect==new[0].rect
 assert old[0].get_text()==new[0].get_text(), 'Изменился текст'
 assert [f[1:] for f in old[0].get_fonts()]==[f[1:] for f in new[0].get_fonts()], 'Изменились шрифты'
 new[0].get_pixmap(matrix=fitz.Matrix(1,1)).save(AUDIT/(dst.stem+'.png'))
 print(dst)
 return new

src=next(OUT.glob('*ГГ*pdf'));d=fitz.open(src);s=d.xref_stream(5).decode('latin1').splitlines();count=0
for a in ap:
 if any(lo<=a['start']<=hi for lo,hi in [(471,542),(1052,1132),(8301,11804),(17585,17611),(2039,2731),(2813,3433),(16472,16843),(16847,16849),(16892,16894)]):s[a['end']]='n';count+=1
d.update_stream(5,'\n'.join(s).encode('latin1'));side(d[0]);front(d[0],(702.37136,309.83325),65.20264,1,[(651.36,755.28),(795.84,820.56)],371.04)
new=save(d,src,'Сборочный_чертёж_шестерни_по_ГОСТ.pdf')
new[0].get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(622,237,843,394)).save(AUDIT/'Сборочный_колесо.png')
new[0].get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(423,802,510,970)).save(AUDIT/'Сборочный_вид_сбоку.png');print('Assembly paths',count)

src=OUT/'Габаритный_чертёж_исправленный.pdf';d=fitz.open(src);s=d.xref_stream(23).decode('latin1');count=0
# Сохранённые позиции относятся к исходному потоку PDF, до замены.
def sub(m):
 global count
 pts=[[float(m[i])*.24,float(m[i+1])*.24]for i in [1,3]]
 remove=(85472<=m.start()<116262 or 191200<=m.start()<191432 or 179874<=m.start()<183097 or key(pts)in sidekeys)
 # Вертикальные торцы зубчатого участка рейки.
 if all(abs(x-1133.28)<.02 or abs(x-1471.68)<.02 for x,y in pts) and min(y for x,y in pts)>422 and max(y for x,y in pts)<431:remove=True
 if remove:count+=1;return m[0][:-1]+'n'
 return m[0]
d.update_stream(23,pat.sub(sub,s).encode('latin1'));side(d[0]);front(d[0],(1235.26491,300.93201),130.39,2,[(1133.28,1342.08),(1422.48,1471.68)],423.60)
new=save(d,src,'Габаритный_чертёж_шестерни_по_ГОСТ.pdf')
new[0].get_pixmap(matrix=fitz.Matrix(2,2),clip=fitz.Rect(1095,161,1490,455)).save(AUDIT/'Габаритный_колесо.png');print('Gabarit paths',count)
