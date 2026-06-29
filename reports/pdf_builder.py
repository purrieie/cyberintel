"""
Generates a C-FALCON-branded multi-section threat advisory PDF from the
structured fields returned by the analysis model. Sections render only when
the article supports them; empty sections are skipped.
"""
import os
from datetime import datetime

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, KeepTogether, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

NAVY = HexColor("#0C2A44")
RED = HexColor("#E82319")
LABEL_BG = HexColor("#CADAE0")
ALT_ROW = HexColor("#DFE8F0")
LIGHT_ROW = HexColor("#F4F6F9")
PINK_HI = HexColor("#FDEBE9")
INK = HexColor("#1A1A1A")
GREY = HexColor("#6B6B6B")
HEADER_TXT = HexColor("#C8412F")

ASSETS = os.path.join(os.path.dirname(__file__), "assets")
GRAMAX = os.path.join(ASSETS, "gramax.png")
CFALCON = os.path.join(ASSETS, "cfalcon.png")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "pdfs")

SEV_COLOR = {
    "critical": "#C0392B", "high": "#E82319", "medium": "#E67E22",
    "low": "#27AE60", "informational": "#7F8C8D", "unknown": "#7F8C8D",
}

DOC_TITLE = "Threat Advisory"
REF_PREFIX = "CI-ADV"


def _styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("MastSub2", fontName="Helvetica", fontSize=9, leading=12.5, textColor=GREY))
    s.add(ParagraphStyle("Sec", fontName="Helvetica-Bold", fontSize=13.5, leading=16, textColor=NAVY, spaceBefore=4, spaceAfter=2))
    s.add(ParagraphStyle("SubSec", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=NAVY, spaceBefore=2))
    s.add(ParagraphStyle("CIBody", fontName="Helvetica", fontSize=9.5, leading=15, textColor=INK, alignment=TA_LEFT))
    s.add(ParagraphStyle("CIBullet", fontName="Helvetica", fontSize=9.5, leading=14, textColor=INK))
    s.add(ParagraphStyle("CellLabel", fontName="Helvetica", fontSize=8.5, leading=11, textColor=GREY))
    s.add(ParagraphStyle("CellVal", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=HEADER_TXT))
    s.add(ParagraphStyle("THead", fontName="Helvetica-Bold", fontSize=8.5, leading=11, textColor=white))
    s.add(ParagraphStyle("TCell", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=INK))
    s.add(ParagraphStyle("Disc", fontName="Helvetica", fontSize=8, leading=11, textColor=GREY))
    return s


def _fmt_list(value):
    if isinstance(value, list):
        return [str(i) for i in value if str(i).strip()]
    if value is None:
        return []
    return [str(value)]


class _Doc(BaseDocTemplate):
    def __init__(self, path, meta, **kwargs):
        super().__init__(path, pagesize=A4, topMargin=46 * mm, bottomMargin=20 * mm,
                         leftMargin=16 * mm, rightMargin=16 * mm, **kwargs)
        self.meta = meta
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="body")
        self.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=self._decorate)])

    def _decorate(self, canvas, doc):
        width, height = A4
        band_h = 40 * mm
        canvas.setFillColor(NAVY)
        canvas.rect(0, height - band_h, width, band_h, fill=1, stroke=0)
        canvas.setFillColor(RED)
        canvas.rect(0, height - band_h - 2.2 * mm, width, 2.2 * mm, fill=1, stroke=0)

        try:
            from reportlab.lib.utils import ImageReader
            if os.path.exists(GRAMAX):
                g = ImageReader(GRAMAX)
                gw = 32 * mm
                gh = gw * 130 / 602
                canvas.drawImage(g, 16 * mm, height - 10 * mm - gh, gw, gh, mask="auto")
            if os.path.exists(CFALCON):
                c = ImageReader(CFALCON)
                cw = 24 * mm
                ch = cw * 605 / 700
                canvas.drawImage(c, width - 16 * mm - cw, height - 8 * mm - ch, cw, ch, mask="auto")
        except Exception:
            pass

        if doc.page == 1:
            canvas.setFillColor(white)
            canvas.setFont("Helvetica-Bold", 8.5)
            canvas.drawCentredString(width / 2, height - 7 * mm, doc.meta["ref"])
            from reportlab.lib.utils import simpleSplit
            canvas.setFont("Helvetica-Bold", 15)
            lines = simpleSplit(doc.meta["title"], "Helvetica-Bold", 15, width - 70 * mm)
            ty = height - 23 * mm
            for line in lines[:2]:
                canvas.drawString(16 * mm, ty, line)
                ty -= 6 * mm

        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, width, 12 * mm, fill=1, stroke=0)
        canvas.setFillColor(RED)
        canvas.rect(0, 12 * mm, width, 1 * mm, fill=1, stroke=0)
        canvas.setFillColor(white)
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(16 * mm, 4.5 * mm,
                          "(c) %s CyberIntel | Confidential - For Authorised Recipients Only" % datetime.now().year)
        canvas.drawRightString(width - 16 * mm, 4.5 * mm, "Page %d" % doc.page)
        if doc.page > 1:
            canvas.setFillColor(white)
            canvas.setFont("Helvetica", 7.5)
            canvas.drawRightString(width - 16 * mm, height - 9 * mm, doc.meta["title"][:70])


def build_article_pdf(article: dict, fields: dict) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    st = _styles()

    title = article.get("title") or DOC_TITLE
    ref = "%s-%s" % (REF_PREFIX, str(article.get("id", "0000")).zfill(4))
    severity = (fields.get("severity") or "Unknown").strip()
    sev_hex = SEV_COLOR.get(severity.lower(), "#7F8C8D")

    safe = "".join(c for c in title[:48] if c.isalnum() or c in " -_").strip().replace(" ", "_")
    path = os.path.join(OUTPUT_DIR, f"{article.get('id', '0')}_{safe}.pdf")

    doc = _Doc(path, meta={"ref": ref, "title": title})
    flow = []

    flow.append(Spacer(1, 1 * mm))
    flow.append(Paragraph(
        "<b>CyberIntel Threat Advisory</b> - automated analysis of source reporting: "
        "affected systems, actor attribution, and recommended actions.", st["MastSub2"]))
    flow.append(Spacer(1, 5 * mm))

    # ---- Intelligence Snapshot (expanded) ----
    flow.append(_band("INTELLIGENCE SNAPSHOT", st))
    rows = [
        ("Issued by", "CyberIntel"),
        ("Date", datetime.now().strftime("%d %B %Y")),
        ("Source", article.get("source", "-")),
        ("Region", fields.get("region") or "Unknown"),
        ("Threat Level", severity.upper()),
        ("Focus", fields.get("focus") or "Unknown"),
        ("Motivations", fields.get("motivations") or "Unknown"),
        ("Prominent Actors", ", ".join(_fmt_list(fields.get("threat_actors"))) or "-"),
        ("Primary Tactics", fields.get("primary_tactics") or "Unknown"),
        ("Affected Systems / Vendors", ", ".join(_fmt_list(fields.get("affected_systems"))) or "-"),
        ("CVEs", ", ".join(_fmt_list(fields.get("cves"))) or "None identified"),
        ("Reference", article.get("url", "-")),
        ("Classification", "For Authorised Recipients"),
    ]
    td = [[Paragraph(l, st["CellLabel"]), Paragraph(str(v), st["CellVal"])] for l, v in rows]
    t = Table(td, colWidths=[46 * mm, 132 * mm])
    ts = [
        ("BACKGROUND", (0, 0), (0, -1), LABEL_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, white),
    ]
    for i in range(len(rows)):
        ts.append(("BACKGROUND", (1, i), (1, i), ALT_ROW if i % 2 == 0 else LIGHT_ROW))
    ti = 4  # Threat Level row
    ts.append(("BACKGROUND", (1, ti), (1, ti), PINK_HI))
    ts.append(("TEXTCOLOR", (1, ti), (1, ti), HexColor(sev_hex)))
    t.setStyle(TableStyle(ts))
    flow.append(t)
    flow.append(Spacer(1, 7 * mm))

    # ---- Executive Summary ----
    flow.append(_section("Executive Summary", st))
    flow.append(Paragraph(fields.get("summary") or "No summary available.", st["CIBody"]))
    flow.append(Spacer(1, 3 * mm))
    flow.append(_chip_row(severity, sev_hex, fields))
    flow.append(Spacer(1, 6 * mm))

    # ---- Threat Actor Profiles ----
    profiles = fields.get("actor_profiles") or []
    if profiles:
        flow.append(_section("Threat Actor Profiles &amp; Operational Structure", st))
        for p in profiles:
            block = [Paragraph(p.get("name") or "Unknown Actor", st["SubSec"])]
            if p.get("description"):
                block.append(Paragraph(p["description"], st["CIBody"]))
            if p.get("capabilities"):
                block.append(Paragraph("<b>Capabilities:</b> " + str(p["capabilities"]), st["CIBody"]))
            if p.get("confirmed_activities"):
                block.append(Paragraph("<b>Confirmed Activities:</b> " + str(p["confirmed_activities"]), st["CIBody"]))
            block.append(Spacer(1, 3 * mm))
            flow.append(KeepTogether(block))
        flow.append(Spacer(1, 3 * mm))

    # ---- Critical Infrastructure & Sector Impacts (table) ----
    impacts = fields.get("sector_impacts") or []
    if impacts:
        flow.append(_section("Critical Infrastructure &amp; Notable Sector Impacts", st))
        header = ["Sector", "Targeted Entity / System", "Actor", "Impact / Method"]
        data = [[Paragraph(h, st["THead"]) for h in header]]
        for r in impacts:
            data.append([
                Paragraph(str(r.get("sector") or "-"), st["TCell"]),
                Paragraph(str(r.get("target") or "-"), st["TCell"]),
                Paragraph(str(r.get("actor") or "-"), st["TCell"]),
                Paragraph(str(r.get("impact") or "-"), st["TCell"]),
            ])
        flow.append(_grid(data, [30 * mm, 56 * mm, 30 * mm, 62 * mm]))
        flow.append(Spacer(1, 5 * mm))

    # ---- Attack Vectors & TTPs (table) ----
    vectors = fields.get("attack_vectors") or []
    if vectors:
        flow.append(_section("Initial Access Vectors &amp; TTPs", st))
        data = [[Paragraph("Threat Actor", st["THead"]), Paragraph("Documented Attack Vectors &amp; TTPs", st["THead"])]]
        for r in vectors:
            data.append([
                Paragraph(str(r.get("actor") or "General"), st["TCell"]),
                Paragraph(str(r.get("ttps") or "-"), st["TCell"]),
            ])
        flow.append(_grid(data, [44 * mm, 134 * mm]))
        flow.append(Spacer(1, 5 * mm))

    # ---- Detection Measures & Mitigation ----
    measures = fields.get("detection_measures") or []
    if measures:
        flow.append(_section("Detection Measures &amp; Mitigation Strategy", st))
        for m in measures:
            line = "<b>%s.</b> %s" % (
                (m.get("control") or "Control"),
                (m.get("description") or ""),
            )
            flow.append(_check_para(line, st))
        flow.append(Spacer(1, 5 * mm))

    # ---- Strategic Recommendations ----
    recs = fields.get("recommendations") or []
    if recs:
        flow.append(_section("CyberIntel Strategic Recommendations", st))
        for r in recs:
            line = "<b>%s.</b> %s" % (
                (r.get("title") or "Recommendation"),
                (r.get("description") or ""),
            )
            flow.append(_check_para(line, st))
        flow.append(Spacer(1, 5 * mm))

    # ---- Disclaimer & Classification ----
    flow.append(_section("Disclaimer &amp; Classification", st))
    flow.append(Paragraph(
        "This advisory is generated by CyberIntel through automated analysis of "
        "publicly available source reporting and is provided for situational "
        "awareness only. It does not constitute legal, operational, or security "
        "advice. CyberIntel makes no warranty as to the completeness or accuracy "
        "of the underlying source material. Recipients should independently verify "
        "findings before acting on them.", st["Disc"]))
    flow.append(Spacer(1, 2 * mm))
    flow.append(Paragraph(
        "<b>Classification:</b> For Authorised Recipients Only &nbsp;|&nbsp; "
        "<b>Distribution:</b> Internal use; do not forward outside the intended "
        "recipient organisation. &nbsp;|&nbsp; <b>Contact:</b> intel@cyberintel.local",
        st["Disc"]))

    doc.build(flow)
    return path


def _band(text, st):
    style = ParagraphStyle("band", fontName="Helvetica-Bold", fontSize=9.5, textColor=white, leading=13)
    t = Table([[Paragraph(text, style)]], colWidths=[178 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _section(title, st):
    t = Table([[Paragraph(title, st["Sec"])]], colWidths=[178 * mm])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.7, HexColor("#D0D0D0")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return KeepTogether([t, Spacer(1, 3 * mm)])


def _grid(data, col_widths):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, HexColor("#C8D2DC")),
        ("GRID", (0, 0), (-1, -1), 0.25, HexColor("#C8D2DC")),
    ]
    for i in range(1, len(data)):
        if i % 2 == 1:
            style.append(("BACKGROUND", (0, i), (-1, i), LIGHT_ROW))
        else:
            style.append(("BACKGROUND", (0, i), (-1, i), ALT_ROW))
    t.setStyle(TableStyle(style))
    return t


def _check_para(html_text, st):
    rows = [[
        Paragraph('<font color="#1F8A4C">&#10003;</font>', st["CIBullet"]),
        Paragraph(html_text, st["CIBullet"]),
    ]]
    t = Table(rows, colWidths=[7 * mm, 171 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (0, -1), 4),
        ("RIGHTPADDING", (0, 0), (0, -1), 0),
        ("LEFTPADDING", (1, 0), (1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _chip_row(severity, sev_hex, fields):
    sev_p = Paragraph(
        '<font color="white"><b>&nbsp;&#9632; THREAT LEVEL: %s&nbsp;</b></font>' % severity.upper(),
        ParagraphStyle("c1", fontSize=8, leading=14, backColor=HexColor(sev_hex)))
    focus_txt = (fields.get("focus") or "Threat Intelligence & Mitigation").upper()
    focus_p = Paragraph(
        "<b>&nbsp;FOCUS: %s&nbsp;</b>" % focus_txt,
        ParagraphStyle("c2", fontSize=8, leading=14, backColor=HexColor("#E8EEF5"), textColor=NAVY))
    t = Table([[sev_p, focus_p]], colWidths=[62 * mm, 116 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t