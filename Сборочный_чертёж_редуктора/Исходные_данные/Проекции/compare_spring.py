import json,fitz
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
for name,path in [('old',ROOT/'Чертёж_общего_вида/Исходные_данные/Редакция_2/Проекции/front_clean.json'),('new',Path(__file__).parent/'front.json')]:
    v=json.loads(path.read_text());doc=fitz.open();p=doc.new_page(width=450,height=210);sh=p.new_shape()
    for arr in ['visible','extra_visible']:
        for poly in v.get(arr,[]):
            if len(poly)>1 and all(5<q[0]<26 and 11<q[1]<19 for q in poly):
                sh.draw_polyline([fitz.Point((q[0]-5)*20,200-(q[1]-10)*20) for q in poly])
    sh.finish(width=1.6,color=(0,0,0));sh.commit();p.get_pixmap().save(Path(__file__).parent/f'spring_{name}.png')
