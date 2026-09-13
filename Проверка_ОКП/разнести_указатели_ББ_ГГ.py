#!/usr/bin/env python3
"""Разносит вынесенные указатели сечений Б–Б и Г–Г на сборочном
чертеже привода. Исходную геометрию чертежа не трогает.

Прежние указатели в этом PDF хранятся в отдельных content streams
xref 30…53. Скрипт исключает только их из /Contents и добавляет новый
векторный поток. Шрифт SectionGOST переиспользуется из исходного PDF.
"""

from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Исправить" / "СБ_Сборочный_чертеж_привода.pdf"
OUTPUT = ROOT / "Исправленные_PDF" / "Сборочный_чертёж_указатели_ББ_ГГ_разнесены.pdf"

# Высота листа в PDF points. Координаты content stream — от левого нижнего угла.
PAGE_H = 1193.52


def pdf_y(top_y: float) -> float:
    return PAGE_H - top_y


def stroke(x: float, top_y: float, half_height: float = 12.5) -> str:
    y = pdf_y(top_y)
    return (
        "q\n"
        f"{x:.2f} {y + half_height:.2f} m\n"
        f"{x:.2f} {y - half_height:.2f} l\n"
        "2.8 w\n0 0 0 RG S\nQ\n"
    )


def right_arrow(x: float, top_y: float) -> str:
    """Стрелка Б: направление взгляда сохранено вправо."""
    y = pdf_y(top_y)
    return (
        "q\n"
        f"560.64 {y:.2f} m\n{x:.2f} {y:.2f} l\n"
        ".48 w\n0 0 0 RG S\nQ\n"
        "q\n"
        f"{x:.2f} {y:.2f} m\n"
        f"{x - 21:.2f} {y - 3:.2f} l\n"
        f"{x - 19:.2f} {y:.2f} l\n"
        f"{x - 21:.2f} {y + 3:.2f} l\n"
        ".48 w\nh\n0 0 0 RG 0 0 0 rg B\nQ\n"
    )


def left_arrow(x: float, line_x: float, top_y: float) -> str:
    """Стрелка Г: направление взгляда сохранено влево."""
    y = pdf_y(top_y)
    return (
        "q\n"
        f"{line_x:.2f} {y:.2f} m\n{x:.2f} {y:.2f} l\n"
        ".48 w\n0 0 0 RG S\nQ\n"
        "q\n"
        f"{x:.2f} {y:.2f} m\n"
        f"{x + 8:.2f} {y + 1.5:.2f} l\n"
        f"{x + 8:.2f} {y - 1.5:.2f} l\n"
        ".48 w\nh\n0 0 0 RG 0 0 0 rg B\nQ\n"
    )


def letter(x: float, tm_y: float, glyph_hex: str) -> str:
    return (
        "q\nBT\n"
        f"1 0 0 1 {x:.2f} {tm_y:.2f} Tm\n"
        f"/SectionGOST 41.46 Tf 0 0 0 RG 0 0 0 rg [<{glyph_hex}>]TJ\n"
        "ET\nQ\n"
    )


def build_overlay() -> bytes:
    chunks: list[str] = []

    # Б–Б: та же вертикальная секущая плоскость x=603.12.
    # Верхний конец вынесен над обводом, нижний — под размерами вида.
    b_top = 170.0
    chunks += [stroke(603.12, b_top), right_arrow(603.12, b_top)]
    chunks += [letter(575.0, pdf_y(b_top) + 14.0, "018d")]

    b_bottom = 580.0
    chunks += [stroke(603.12, b_bottom, 13.0), right_arrow(603.12, b_bottom)]
    chunks += [letter(550.0, pdf_y(b_bottom) - 34.0, "018d")]

    # Г–Г, первое место (левый микропереключатель), плоскость x=286.32.
    g1_top = 300.0
    chunks += [stroke(286.32, g1_top, 12.0), left_arrow(286.32, 302.32, g1_top)]
    chunks += [letter(312.0, pdf_y(g1_top) + 10.0, "018f")]

    g1_bottom = 600.0
    chunks += [stroke(286.32, g1_bottom, 11.5), left_arrow(286.32, 302.32, g1_bottom)]
    chunks += [letter(312.0, pdf_y(g1_bottom) - 11.0, "018f")]

    # Г–Г, второе место (правый микропереключатель), плоскость x=574.32.
    # На x=574 внешний обвод корпуса доходит почти до y=200. Конец
    # вынесен в верхнее свободное поле, чтобы штрих и стрелка не касались деталей.
    g2_top = 90.0
    chunks += [stroke(574.32, g2_top, 12.0), left_arrow(574.32, 590.32, g2_top)]
    chunks += [letter(548.0, pdf_y(g2_top) + 2.0, "018f")]

    g2_bottom = 640.0
    chunks += [stroke(574.32, g2_bottom, 11.5), left_arrow(574.32, 590.32, g2_bottom)]
    chunks += [letter(617.0, pdf_y(g2_bottom) - 18.0, "018f")]

    return "".join(chunks).encode("ascii")


def main() -> None:
    doc = fitz.open(SOURCE)
    page = doc[0]

    # Исключаем только прежние векторные указатели Б/Г. Все потоки до 30 и с 54 сохраняются.
    kept = [xref for xref in page.get_contents() if not 30 <= xref <= 53]

    overlay_xref = doc.get_new_xref()
    doc.update_object(overlay_xref, "<<>>")
    doc.update_stream(overlay_xref, build_overlay(), compress=True)
    kept.append(overlay_xref)

    contents = "[ " + " ".join(f"{xref} 0 R" for xref in kept) + " ]"
    doc.xref_set_key(page.xref, "Contents", contents)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT, garbage=0, clean=False, deflate=True)
    doc.close()
    print(OUTPUT)


if __name__ == "__main__":
    main()
