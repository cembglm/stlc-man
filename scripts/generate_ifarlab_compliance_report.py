"""Generate the reviewed DOCX form of the ASRLab compliance report."""

from pathlib import Path
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "ASRLAB_STLC_UYUMLULUK_RAPORU_2026-11-24.md"
OUTPUT = ROOT / "docs" / "ASRLAB_STLC_UYUMLULUK_RAPORU_2026-11-24.docx"


def shade(cell, color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd")) or OxmlElement("w:shd")
    shd.set(qn("w:fill"), color)
    tc_pr.append(shd)


def borders(table):
    tbl_pr = table._tbl.tblPr
    element = tbl_pr.find(qn("w:tblBorders")) or OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = OxmlElement(f"w:{edge}")
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), "4")
        node.set(qn("w:color"), "D9D9D9")
        element.append(node)
    tbl_pr.append(element)


def set_repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    tr_pr.append(repeat)


def add_inline(paragraph, text):
    parts = re.split(r"(`[^`]+`|\*\*[^*]+\*\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(45, 55, 72)
        elif part.startswith("**"):
            paragraph.add_run(part[2:-2]).bold = True
        else:
            paragraph.add_run(part)


def build():
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(0.75)
    section.left_margin = section.right_margin = Inches(0.8)

    normal = doc.styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor(31, 41, 55)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.12
    for name, size in (("Title", 26), ("Heading 1", 17), ("Heading 2", 13)):
        style = doc.styles[name]
        style.font.name = "Aptos Display"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(14 if name != "Title" else 0)
        style.paragraph_format.space_after = Pt(7)
        style.paragraph_format.keep_with_next = True
        p_pr = style._element.get_or_add_pPr()
        border = p_pr.find(qn("w:pBdr"))
        if border is not None:
            p_pr.remove(border)

    title = lines[0].lstrip("# ")
    p = doc.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.add_run(title)
    subtitle = doc.add_paragraph()
    subtitle.add_run("Dijital ikiz doğrulaması için kod, test ve uygunluk değerlendirmesi").italic = True
    subtitle.paragraph_format.space_after = Pt(20)
    for meta in lines[2:5]:
        if meta.strip():
            p = doc.add_paragraph()
            add_inline(p, meta.replace("  ", ""))
    doc.add_page_break()

    i = 5
    while i < len(lines):
        raw = lines[i]
        text = raw.strip()
        if not text:
            i += 1
            continue
        if text.startswith("## "):
            doc.add_heading(text[3:], level=1)
        elif text.startswith("### "):
            doc.add_heading(text[4:], level=2)
        elif text.startswith("| "):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append([cell.strip() for cell in lines[i].strip().strip("|").split("|")])
                i += 1
            i -= 1
            rows = [block[0]] + block[2:]
            table = doc.add_table(rows=len(rows), cols=len(rows[0]))
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = True
            borders(table)
            set_repeat_header(table.rows[0])
            for r_idx, row in enumerate(rows):
                for c_idx, value in enumerate(row):
                    cell = table.cell(r_idx, c_idx)
                    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                    cell.text = ""
                    add_inline(cell.paragraphs[0], value)
                    cell.paragraphs[0].paragraph_format.space_after = Pt(2)
                    if r_idx == 0:
                        shade(cell, "1F4E78")
                        for run in cell.paragraphs[0].runs:
                            run.font.color.rgb = RGBColor(255, 255, 255)
                            run.bold = True
                    elif r_idx % 2 == 0:
                        shade(cell, "F2F6FA")
            doc.add_paragraph().paragraph_format.space_after = Pt(2)
        elif re.match(r"^\d+\. ", text):
            p = doc.add_paragraph(style="List Number")
            add_inline(p, re.sub(r"^\d+\. ", "", text))
        elif text.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            add_inline(p, text[2:])
        else:
            p = doc.add_paragraph()
            add_inline(p, text)
        i += 1

    footer = doc.sections[0].footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("ASRLab STLC Manager Uygunluk Raporu  |  24 Kasım 2026").font.size = Pt(8)
    doc.core_properties.title = title
    doc.core_properties.subject = "STLC Manager IFARLAB dijital ikiz uyumluluk değerlendirmesi"
    doc.core_properties.author = "ASRLab"
    doc.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    print(build())
