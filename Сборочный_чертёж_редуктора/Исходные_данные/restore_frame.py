"""Restore only the vector grid of the existing drawing's main inscription."""
from pathlib import Path
import fitz

MM = 72 / 25.4
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TEMPLATE = ROOT / 'Чертёж_общего_вида/Исходные_данные/Редакция_2/Основная_надпись_по_образцу.pdf'


def restore_stamp_frame(page):
    target = fitz.Rect(651 * MM, 534 * MM, 836 * MM, 589 * MM)
    with fitz.open(TEMPLATE) as template:
        source = template[0]
        scale = min(target.width / source.rect.width, target.height / source.rect.height)
        ox = target.x0 + (target.width - source.rect.width * scale) / 2
        oy = target.y0 + (target.height - source.rect.height * scale) / 2
        segments = {}
        # The template is a cropped native PDF. Its top border lies just
        # outside its crop; keep the original grid coordinates, widths and
        # column layout, but join its outer ends to the sheet frame.
        for drawing in source.get_drawings():
            if drawing['type'] not in ('s', 'fs'):
                continue
            for item in drawing['items']:
                if item[0] != 'l':
                    continue
                a, b = item[1:]
                x0, y0, x1, y1 = (v / MM for v in (*a, *b))
                if min(x0, x1) < -.5 or max(x0, x1) > 185.5:
                    continue
                if min(y0, y1) < -.5 or max(y0, y1) > 55.5:
                    continue
                if abs(x0-x1) > .001 and abs(y0-y1) > .001:
                    continue
                if abs(x0-x1) + abs(y0-y1) < 4.9:
                    continue
                ends = []
                for x, y in ((x0, y0), (x1, y1)):
                    px = min(target.x1, max(target.x0, ox + x * MM * scale))
                    py = min(target.y1, max(target.y0, oy + y * MM * scale))
                    if y > 54:
                        py = target.y1
                    ends.append((px, py))
                key = tuple(sorted(ends))
                segments[key] = drawing['width'] * scale
        shape = page.new_shape()
        for ends, width in segments.items():
            shape.draw_line(fitz.Point(*ends[0]), fitz.Point(*ends[1]))
            shape.finish(color=(0, 0, 0), width=width, closePath=False)
        shape.commit()
        return len(segments)


if __name__ == '__main__':
    folder = HERE.parent
    original = folder / 'Редуктор_сборочный_чертёж_А1.pdf'
    output = folder / 'Редуктор_сборочный_чертёж_А1_рамка.pdf'
    with fitz.open(original) as document:
        count = restore_stamp_frame(document[0])
        document.save(output, garbage=4, deflate=True)
        document[0].get_pixmap(matrix=fitz.Matrix(.8, .8), alpha=False).save(folder / 'Предпросмотр_рамка.png')
        stamp = fitz.Rect(646 * MM, 529 * MM, 840 * MM, 594 * MM)
        document[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), clip=stamp, alpha=False).save(folder / 'Штамп_рамка.png')
    print(f'{output}: restored {count} grid segments')
