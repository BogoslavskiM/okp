import fitz,math,json
from pathlib import Path
MM=72/25.4
FONT=str(Path(__file__).parent/'GOST_Type_A.ttf')
F=fitz.Font(fontfile=FONT)
class Sheet:
    def __init__(self,doc,w=841,h=594):
        self.w=w;self.h=h;self.p=doc.new_page(width=w*MM,height=h*MM)
        self.p.insert_font(fontname='GOST',fontfile=FONT)
    def line(self,a,b,width=.25,dash=None):
        self.p.draw_line(fitz.Point(a[0]*MM,a[1]*MM),fitz.Point(b[0]*MM,b[1]*MM),width=width*MM,dashes=dash,color=(0,0,0))
    def poly(self,pts,width=.35,dash=None,fill=None,close=False):
        if len(pts)<2:return
        sh=self.p.new_shape();sh.draw_polyline([fitz.Point(x*MM,y*MM) for x,y in pts]);sh.finish(width=width*MM,dashes=dash,color=(0,0,0),fill=fill,closePath=close);sh.commit()
    def rect(self,x,y,w,h,width=.5):
        self.p.draw_rect(fitz.Rect(x*MM,y*MM,(x+w)*MM,(y+h)*MM),width=width*MM,color=(0,0,0))
    def text(self,x,y,text,h=3.5,align='left',rotate=0):
        size=h/.64453125*MM
        width=F.text_length(text,fontsize=size)/MM
        if align=='center':x-=width/2
        if align=='right':x-=width
        p=fitz.Point(x*MM,y*MM)
        self.p.insert_text(p,text,fontname='GOST',fontsize=size,morph=(p,fitz.Matrix(1,0,.26795,1,0,0)),rotate=rotate,color=(0,0,0))
        return width
    def dot(self,x,y,r=.7):self.p.draw_circle(fitz.Point(x*MM,y*MM),r*MM,color=(0,0,0),fill=(0,0,0))
    def arrow(self,tip,tail,size=2.5):
        dx=tail[0]-tip[0];dy=tail[1]-tip[1];L=math.hypot(dx,dy);dx/=L;dy/=L
        self.poly([tip,(tip[0]+size*dx+.28*size*dy,tip[1]+size*dy-.28*size*dx),(tip[0]+size*dx-.28*size*dy,tip[1]+size*dy+.28*size*dx)],width=.15,fill=(0,0,0),close=True)
    def leader(self,anchor,shelf,label,left=None):
        sx,sy=shelf;length=max(10,len(str(label))*3)
        if left is None:left=sx<anchor[0]
        end=(sx-length,sy) if left else (sx+length,sy)
        self.poly([anchor,(sx,sy),end],.18);self.dot(*anchor,.55)
        self.text((sx+end[0])/2,sy-1,str(label),5,align='center')
    def dimh(self,x1,x2,y,from1,from2,label):
        # Extension lines start exactly at the measured contour and cross the
        # dimension line.  Their far endpoint follows the side on which the
        # dimension is placed.
        for x,origin in ((x1,from1),(x2,from2)):
            direction=1 if y>origin else -1
            self.line((x,origin),(x,y+direction*2),.18)
        self.line((x1,y),(x2,y),.18);self.arrow((x1,y),(x2,y));self.arrow((x2,y),(x1,y))
        self.text((x1+x2)/2,y-1.5,label,3.5,align='center')
    def dimv(self,y1,y2,x,from1,from2,label):
        for y,origin in ((y1,from1),(y2,from2)):
            direction=1 if x>origin else -1
            self.line((origin,y),(x+direction*2,y),.18)
        self.line((x,y1),(x,y2),.18);self.arrow((x,y1),(x,y2));self.arrow((x,y2),(x,y1))
        self.text(x-1.5,(y1+y2)/2,label,3.5,rotate=90)
    def frame(self,num,total):
        self.rect(20,5,self.w-25,self.h-10,.6)
        # Main inscription form 1, 185 x 55; no unverified signatures or mass.
        x=self.w-190;y=self.h-60
        self.rect(x,y,185,55,.5)
        for yy in [5,10,15,20,25,30,35,40,45,50]:self.line((x,y+yy),(x+65,y+yy),.18)
        for xx in [7,17,40,55,65]:self.line((x+xx,y),(x+xx,y+55),.18)
        # Left signing fields (merge their middle columns visually by white field and reline).
        self.p.draw_rect(fitz.Rect((x+17)*MM,(y+15)*MM,(x+55)*MM,(y+55)*MM),color=None,fill=(1,1,1))
        for yy in [15,20,25,30,35,40,45,50,55]:self.line((x+17,y+yy),(x+55,y+yy),.18)
        self.line((x+40,y+15),(x+40,y+55),.18)
        self.p.draw_rect(fitz.Rect((x+.2)*MM,(y+15.2)*MM,(x+16.8)*MM,(y+54.8)*MM),color=None,fill=(1,1,1))
        for yy in [20,25,30,35,40,45,50]:self.line((x,y+yy),(x+17,y+yy),.18)
        self.line((x+65,y+15),(x+185,y+15),.5)
        self.line((x+135,y+15),(x+135,y+55),.5)
        self.line((x+135,y+20),(x+185,y+20),.18)
        self.line((x+135,y+35),(x+185,y+35),.18)
        self.line((x+135,y+40),(x+185,y+40),.18)
        for xx in [150,167]:self.line((x+xx,y+15),(x+xx,y+35),.18)
        self.line((x+150,y+35),(x+150,y+40),.18)
        self.text(x+125,y+10,'РЛ5.41.00.00.00 ВО',5,align='center')
        self.text(x+100,y+24,'Следящий привод',3.5,align='center')
        self.text(x+100,y+30,'возвратно-поступательного',2.5,align='center')
        self.text(x+100,y+35,'движения',3.5,align='center')
        self.text(x+100,y+46,'Чертеж общего вида',3.5,align='center')
        for xx,label in [(137,'Лит.'),(152,'Масса'),(169,'Масштаб')]:self.text(x+xx,y+19,label,2.5)
        self.text(x+176,y+29,'1:1',3.5,align='center')
        self.text(x+136,y+39,f'Лист {num}',2.5);self.text(x+152,y+39,f'Листов {total}',2.5)
        self.text(x+160,y+46,'МГТУ им. Н.Э. Баумана',2.5,align='center')
        self.text(x+160,y+52,'РЛ5',3.5,align='center')
        for xx,label in [(1,'Изм.'),(8,'Лист'),(18,'№ докум.'),(41,'Подп.'),(56,'Дата')]:self.text(x+xx,y+14,label,2.5)
        for yy,label in [(19,'Разраб.'),(24,'Пров.'),(29,'Т.контр.'),(44,'Н.контр.'),(49,'Утв.')]:self.text(x+1,y+yy,label,2.5)
        self.text(self.w-7,self.h-1.5,'Формат А1' if self.w>800 else 'Формат А4',2.5,align='right')
        self.rect(20,5,70,14,.35)
        self.text(87,9,'РЛ5.41.00.00.00 ВО',3.5,rotate=180)
    def view(self,data,x,y,scale,normal,xdir,sections=None):
        paths=data['visible'];pts=[q for p in paths for q in p]
        xmin=min(q[0] for q in pts);xmax=max(q[0] for q in pts);ymin=min(q[1] for q in pts);ymax=max(q[1] for q in pts)
        def xy(v):return x+(v[0]-xmin)*scale,y+(ymax-v[1])*scale
        ydir=(normal[1]*xdir[2]-normal[2]*xdir[1],normal[2]*xdir[0]-normal[0]*xdir[2],normal[0]*xdir[1]-normal[1]*xdir[0])
        def world(q):return xy((sum(a*b for a,b in zip(q,xdir)),sum(a*b for a,b in zip(q,ydir))))
        if sections:
            for k,sect in enumerate(sections):
                edges2=[[world(q) for q in p] for p in sect['edges']]
                self.hatch(edges2,{2:0,342:1,140:0,143:1,407:0}.get(sect['id'],sect['id']))
        for path in data.get('hidden',[]):self.poly([xy(v) for v in path],.15,'[3 2] 0')
        sh=self.p.new_shape()
        for path in paths:
            if len(path)>1:sh.draw_polyline([fitz.Point(*[a*MM for a in xy(v)]) for v in path])
        sh.finish(width=.5*MM,color=(0,0,0),closePath=False);sh.commit()
        # Restore visible tangent transition edges with thin continuous strokes.
        extra=data.get('extra_visible',[])
        if extra:
            sh=self.p.new_shape()
            for path in extra:
                if len(path)>1:sh.draw_polyline([fitz.Point(*[a*MM for a in xy(v)]) for v in path])
            sh.finish(width=.25*MM,color=(0,0,0),closePath=False);sh.commit()
        return world,(x,y,x+(xmax-xmin)*scale,y+(ymax-ymin)*scale)
    def hatch(self,paths,index):
        # Intersections of equally spaced diagonal lines with section loops, even/odd fill.
        s=1 if index%2 else -1
        segs=[];vv=[]
        for path in paths:
            for (x1,y1),(x2,y2) in zip(path,path[1:]):
                a=(x1,(y1-s*x1));b=(x2,(y2-s*x2));segs.append((a,b));vv +=[a[1],b[1]]
        if not vv:return
        sh=self.p.new_shape();count=0
        spacing=2.4+.4*(index%5)
        v=math.floor(min(vv)/spacing)*spacing
        while v<=max(vv):
            xs=[]
            for a,b in segs:
                if (a[1]<=v<b[1]) or (b[1]<=v<a[1]):xs.append(a[0]+(v-a[1])*(b[0]-a[0])/(b[1]-a[1]))
            xs.sort()
            for a,b in zip(xs[0::2],xs[1::2]):
                if b-a>.03:
                    sh.draw_line(fitz.Point(a*MM,(v+s*a)*MM),fitz.Point(b*MM,(v+s*b)*MM));count+=1
            v+=spacing

        if count:sh.finish(width=.15*MM,color=(0,0,0),closePath=False);sh.commit()
