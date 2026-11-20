"""Exportación a Word (.docx) real con python-docx."""
import io

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH as AL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from modelo import ESTILOS, armar

TEMAS = ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme")


def _fuente(estilo, nombre, tam):
    estilo.font.name = nombre
    estilo.font.size = Pt(tam)
    rf = estilo.element.get_or_add_rPr().find(qn("w:rFonts"))
    for a in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rf.set(qn(a), nombre)
    for a in TEMAS:
        rf.attrib.pop(qn(a), None)


def _num_pagina(par):
    run = par.add_run()
    for tipo, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        if tipo:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tipo)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = txt
        run._r.append(el)


def construir_docx(e):
    f = e["formato"]
    c = ESTILOS[f]
    doc = Document()
    doc.core_properties.title = e.get("titulo", "")
    doc.core_properties.author = e.get("autor", "")
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = sec.top_margin = sec.bottom_margin = Cm(2.54)

    normal = doc.styles["Normal"]
    _fuente(normal, c["fuente"], c["tam"])
    h1 = doc.styles["Heading 1"]
    _fuente(h1, c["fuente"], c["tam"])
    h1.font.bold, h1.font.italic = True, False
    h1.font.color.rgb = RGBColor(0, 0, 0)
    for est in (normal, h1):
        pf = est.paragraph_format
        pf.line_spacing, pf.space_before, pf.space_after = c["inter"], Pt(0), Pt(c["despues"])

    if c["pie"]:
        p = sec.footer.paragraphs[0]
        p.alignment = AL.CENTER
    else:
        p = sec.header.paragraphs[0]
        p.alignment = AL.RIGHT
        if f == "MLA" and e.get("autor", "").strip():
            p.add_run(e["autor"].strip() + " ")
    _num_pagina(p)

    for b in armar(e):
        k = b[0]
        if k == "pagebreak":
            doc.add_page_break()
        elif k == "vacio":
            doc.add_paragraph()
        elif k == "h":
            p = doc.add_heading(b[1], level=1)
            p.alignment = AL.CENTER if c["centrar_h"] else AL.LEFT
        elif k in ("title", "center"):
            p = doc.add_paragraph()
            p.alignment = AL.CENTER
            p.add_run(b[1]).bold = (k == "title")
        elif k == "left":
            doc.add_paragraph(b[1]).alignment = AL.LEFT
        elif k == "p":
            p = doc.add_paragraph(b[1])
            if c["sangria"]:
                p.paragraph_format.first_line_indent = Cm(1.27)
            if c["just"]:
                p.alignment = AL.JUSTIFY
        elif k == "ref":
            p = doc.add_paragraph(b[1])
            p.paragraph_format.left_indent = Cm(1.27)
            p.paragraph_format.first_line_indent = Cm(-1.27)
            if f == "Chicago":
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.space_after = Pt(12)
            elif f == "Formato libre":
                p.paragraph_format.line_spacing = 1.0
                p.paragraph_format.space_after = Pt(6)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
