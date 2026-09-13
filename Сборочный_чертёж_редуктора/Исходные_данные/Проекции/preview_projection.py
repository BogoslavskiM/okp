import sys,json
from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'Чертёж_общего_вида/Исходные_данные/Редакция_2'))
from okp_pdf_helpers import Sheet,MM
folder=Path(__file__).resolve().parent
for name in sys.argv[1:]:
    v=json.loads((folder/f'{name}.json').read_text());meta=v['metadata']
    doc=fitz.open();sheet=Sheet(doc,240,210)
    world,bounds=sheet.view(v,10,10,2,meta['normal'],meta['xdir'],v.get('sections'))
    sheet.p.get_pixmap(matrix=fitz.Matrix(1.7,1.7)).save(folder/f'{name}_preview.png')
    doc.close()
