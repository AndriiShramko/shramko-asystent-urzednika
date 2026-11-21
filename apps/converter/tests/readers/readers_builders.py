"""Synthetic files for the reader tests, built in code (the image workflow sees no task set). Synthetic text only."""
from __future__ import annotations

import io
import zipfile

NSDECL = (
    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
    'xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" '
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
    'xmlns:v="urn:schemas-microsoft-com:vml" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"'
)
EMU = 12700

A4_SECT = ('<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
           '<w:pgMar w:top="567" w:right="567" w:bottom="567" w:left="567" w:header="0" w:footer="0" w:gutter="0"/>'
           '</w:sectPr>')


def docx_bytes(body: str, styles: str | None = None, footnotes: str | None = None, sect: str = A4_SECT) -> bytes:
    """A minimal Word package around the given body XML (paragraphs and tables, namespaces declared)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/'
                   'content-types"><Default Extension="xml" ContentType="application/xml"/><Override '
                   'PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.'
                   'wordprocessingml.document.main+xml"/></Types>')
        z.writestr("word/document.xml",
                   f'<?xml version="1.0" encoding="UTF-8"?><w:document {NSDECL}><w:body>{body}{sect}</w:body></w:document>')
        if styles is not None:
            z.writestr("word/styles.xml", f'<?xml version="1.0" encoding="UTF-8"?><w:styles {NSDECL}>{styles}</w:styles>')
        if footnotes is not None:
            z.writestr("word/footnotes.xml",
                       f'<?xml version="1.0" encoding="UTF-8"?><w:footnotes {NSDECL}>{footnotes}</w:footnotes>')
    return buf.getvalue()


def p(text: str = "", rpr: str = "", ppr: str = "") -> str:
    run = f'<w:r>{f"<w:rPr>{rpr}</w:rPr>" if rpr else ""}<w:t xml:space="preserve">{text}</w:t></w:r>' if text else ""
    return f'<w:p>{f"<w:pPr>{ppr}</w:pPr>" if ppr else ""}{run}</w:p>'


def anchor(x_pt: float, y_pt: float, w_pt: float, h_pt: float, inner: str, rel_h: str = "page",
           rel_v: str = "page") -> str:
    """A wp:anchor at an offset, holding a wps shape (inner = spPr + optional txbx)."""
    return (f'<wp:anchor simplePos="0" behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1" relativeHeight="1">'
            f'<wp:simplePos x="0" y="0"/>'
            f'<wp:positionH relativeFrom="{rel_h}"><wp:posOffset>{int(x_pt * EMU)}</wp:posOffset></wp:positionH>'
            f'<wp:positionV relativeFrom="{rel_v}"><wp:posOffset>{int(y_pt * EMU)}</wp:posOffset></wp:positionV>'
            f'<wp:extent cx="{int(w_pt * EMU)}" cy="{int(h_pt * EMU)}"/><wp:docPr id="1" name="s"/>'
            f'<a:graphic><a:graphicData uri="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">'
            f'<wps:wsp>{inner}</wps:wsp></a:graphicData></a:graphic></wp:anchor>')


def textbox(x_pt: float, y_pt: float, w_pt: float, h_pt: float, *paras: str, rel_h: str = "page",
            rel_v: str = "page", with_fallback: bool = True) -> str:
    """A text box as Word writes it: mc:Choice with the drawing, mc:Fallback with a VML copy of the same text."""
    content = "".join(paras)
    choice = anchor(x_pt, y_pt, w_pt, h_pt,
                    '<wps:cNvSpPr txBox="1"/><wps:spPr><a:prstGeom prst="rect"/></wps:spPr>'
                    f'<wps:txbx><w:txbxContent>{content}</w:txbxContent></wps:txbx><wps:bodyPr/>',
                    rel_h, rel_v)
    fallback = (f'<mc:Fallback><w:pict><v:shape><v:textbox><w:txbxContent>{content}</w:txbxContent></v:textbox>'
                f'</v:shape></w:pict></mc:Fallback>') if with_fallback else ""
    return (f'<w:r><mc:AlternateContent><mc:Choice Requires="wps"><w:drawing>{choice}</w:drawing></mc:Choice>'
            f'{fallback}</mc:AlternateContent></w:r>')


def shape(x_pt: float, y_pt: float, w_pt: float, h_pt: float, fill: str | None = "000000", outline: bool = False,
          prst: str = "rect") -> str:
    fill_xml = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else "<a:noFill/>"
    ln = '<a:ln w="9525"><a:solidFill><a:srgbClr val="000000"/></a:solidFill></a:ln>' if outline else \
        '<a:ln w="0"><a:noFill/></a:ln>'
    inner = f'<wps:cNvSpPr/><wps:spPr><a:prstGeom prst="{prst}"/>{fill_xml}{ln}</wps:spPr><wps:bodyPr/>'
    return f'<w:r><w:drawing>{anchor(x_pt, y_pt, w_pt, h_pt, inner)}</w:drawing></w:r>'


def pdf_bytes(draw) -> bytes:  # noqa: ANN001 - draw(canvas) draws pages; showPage between pages is the caller's
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4, invariant=1)
    draw(c)
    c.save()
    return buf.getvalue()
