"""
Official Audit Act — PDF generator.
Styled as a formal government/municipal document with:
  - Document header (organisation, act number, date)
  - Numbered sections
  - Summary table of discrepancies
  - Per-record evidence section
  - Signature block
Ukrainian text is transliterated to Latin so Helvetica renders it correctly.
"""
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, HRFlowable, KeepTogether,
)

# ── Compat stubs ─────────────────────────────────────────────────────────────
FONT_PATH = ""
def register_fonts(): pass

# ── Ukrainian → Latin transliteration (DSTU 9112:2021) ───────────────────────
_UA = {
    'А':'A','Б':'B','В':'V','Г':'H','Ґ':'G','Д':'D','Е':'E','Є':'Ye',
    'Ж':'Zh','З':'Z','И':'Y','І':'I','Ї':'Yi','Й':'Y','К':'K','Л':'L',
    'М':'M','Н':'N','О':'O','П':'P','Р':'R','С':'S','Т':'T','У':'U',
    'Ф':'F','Х':'Kh','Ц':'Ts','Ч':'Ch','Ш':'Sh','Щ':'Shch','Ь':'',
    'Ю':'Yu','Я':'Ya',
    'а':'a','б':'b','в':'v','г':'h','ґ':'g','д':'d','е':'e','є':'ye',
    'ж':'zh','з':'z','и':'y','і':'i','ї':'yi','й':'y','к':'k','л':'l',
    'м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u',
    'ф':'f','х':'kh','ц':'ts','ч':'ch','ш':'sh','щ':'shch','ь':'',
    'ю':'yu','я':'ya',
    'Э':'E','э':'e','Ъ':'','ъ':'','Ы':'Y','ы':'y','Ё':'Yo','ё':'yo',
}
def _tr(v) -> str:
    if v is None: return "N/A"
    s = str(v).strip()
    return ("".join(_UA.get(c, c) for c in s)) if s else "N/A"

# ── Problem labels ────────────────────────────────────────────────────────────
PROBLEM_LABELS = {
    "edrpou_of_land_user":                     "Organization ID (EDRPOU) mismatch",
    "land_user":                               "Land user / owner name mismatch",
    "location":                                "Location / address discrepancy",
    "area":                                    "Area value discrepancy",
    "date_of_state_registration_of_ownership": "Registration date mismatch",
    "share_of_ownership":                      "Ownership share mismatch",
    "purpose":                                 "Land usage purpose mismatch",
    "missing_owner":                           "Owner information missing",
}
def _lbl(k): return PROBLEM_LABELS.get(k, k.replace("_"," ").title())

# ── Colours ───────────────────────────────────────────────────────────────────
BLACK  = colors.black
NAVY   = colors.HexColor("#1B3A6B")
GRAY   = colors.HexColor("#555555")
LGRAY  = colors.HexColor("#888888")
RED    = colors.HexColor("#C0392B")
GREEN  = colors.HexColor("#1A6B3A")
LINE   = colors.HexColor("#AAAAAA")
BG     = colors.HexColor("#F5F7FA")
WHITE  = colors.white


# ── Page decorator: header + footer ──────────────────────────────────────────
def _page_decorator(doc_number: str, date_str: str):
    def _draw(canvas, doc):
        canvas.saveState()
        W, H = A4
        MX = 20*mm

        # Top double-line rule
        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(2.5)
        canvas.line(MX, H - 15*mm, W - MX, H - 15*mm)
        canvas.setLineWidth(0.5)
        canvas.line(MX, H - 16.5*mm, W - MX, H - 16.5*mm)

        # Organisation name (centred)
        canvas.setFillColor(NAVY)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawCentredString(W/2, H - 12*mm,
            "UNIFIED TERRITORIAL COMMUNITY - ASSET MANAGEMENT DEPARTMENT")

        # Bottom rule + footer
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(MX, 18*mm, W - MX, 18*mm)
        canvas.setLineWidth(1.5)
        canvas.setStrokeColor(NAVY)
        canvas.line(MX, 17.2*mm, W - MX, 17.2*mm)

        canvas.setFillColor(LGRAY)
        canvas.setFont("Helvetica", 7)
        canvas.drawString(MX, 13*mm,
            f"Audit Act No. {doc_number}   |   Date: {date_str}")
        canvas.drawRightString(W - MX, 13*mm, f"Page {doc.page}")

        canvas.restoreState()
    return _draw


# ── Helpers ───────────────────────────────────────────────────────────────────
def _style(name, font="Helvetica", size=10, clr=BLACK,
           bold=False, align=0, sb=0, sa=3, indent=0, leading=None):
    return ParagraphStyle(
        name,
        fontName="Helvetica-Bold" if bold else font,
        fontSize=size,
        textColor=clr,
        alignment=align,          # 0=left, 1=centre, 2=right, 4=justify
        spaceBefore=sb,
        spaceAfter=sa,
        leftIndent=indent,
        leading=leading or round(size * 1.45),
    )

def HR(thick=0.5, clr="#AAAAAA", sb=3, sa=3):
    return HRFlowable(width="100%", thickness=thick,
                      color=colors.HexColor(clr),
                      spaceBefore=sb*mm, spaceAfter=sa*mm)


# ── Main builder ──────────────────────────────────────────────────────────────
def generate_audit_pdf(report, records_qs) -> bytes:
    records      = list(records_qs)
    total        = len(records)
    n_bad        = sum(1 for r in records if r.problems)
    n_ok         = total - n_bad
    report_id    = str(report.id)
    short_id     = report_id[:8].upper()
    now          = datetime.utcnow()
    date_str     = now.strftime("%d %B %Y")
    ts_str       = now.strftime("%Y-%m-%d %H:%M UTC")
    doc_number   = short_id

    buf = io.BytesIO()
    W, H = A4
    MX = 20*mm
    CW = W - 2*MX

    frame = Frame(MX, 24*mm, CW, H - 44*mm,
                  leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    tmpl = PageTemplate(
        id="main", frames=[frame],
        onPage=_page_decorator(doc_number, date_str),
    )
    doc = BaseDocTemplate(
        buf, pagesize=A4, pageTemplates=[tmpl],
        leftMargin=MX, rightMargin=MX,
        topMargin=22*mm, bottomMargin=28*mm,
    )

    # ── Style set ─────────────────────────────────────────────────────────────
    sCentre   = _style("ctr",  size=9,  clr=NAVY,   align=1, bold=True,  sb=2, sa=1)
    sCentreS  = _style("ctrs", size=8,  clr=LGRAY,  align=1,             sb=0, sa=6)
    sDocTitle = _style("dt",   size=15, clr=NAVY,   align=1, bold=True,  sb=4, sa=2)
    sDocSub   = _style("ds",   size=9,  clr=GRAY,   align=1,             sb=0, sa=8)
    sSec      = _style("sec",  size=10, clr=NAVY,   bold=True, sb=6, sa=3)
    sBodyJ    = _style("bj",   size=9,  clr=BLACK,  align=4, sb=0, sa=2, leading=14)
    sItem     = _style("it",   size=9,  clr=BLACK,  sb=0, sa=2, indent=5)
    sRecHdr   = _style("rh",   size=9.5,clr=NAVY,   bold=True, sb=6, sa=2)
    sLabel    = _style("lbl",  size=7.5,clr=LGRAY,  sb=3, sa=0)
    sValB     = _style("vb",   size=9,  clr=BLACK,  bold=False, sb=0, sa=2, indent=3)
    sProblem  = _style("pb",   size=9,  clr=RED,    bold=True,  sb=0, sa=2, indent=5)
    sClean    = _style("cl",   size=9,  clr=GREEN,  bold=True,  sb=0, sa=3)
    sSmall    = _style("sm",   size=7.5,clr=LGRAY,  align=4,    sb=4, sa=0)

    story = []

    # ── 1. Document header ────────────────────────────────────────────────────
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("AUDIT ACT", sDocTitle))
    story.append(Paragraph(
        "on the verification of land and property registry data", sDocSub))

    # Meta line (No. / Date)
    story.append(Paragraph(
        f"Act No.&nbsp;&nbsp;<b>{doc_number}</b>"
        f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        f"Date:&nbsp;&nbsp;<b>{date_str}</b>",
        sCentre))
    story.append(HR(thick=1.5, clr="#1B3A6B", sb=2, sa=4))

    # ── 2. Preamble ───────────────────────────────────────────────────────────
    story.append(Paragraph("1.  GENERAL INFORMATION", sSec))
    story.append(Paragraph(
        "This Audit Act has been prepared by the Asset Management Department of the "
        "Unified Territorial Community (UTC) in accordance with the established procedures "
        "for cross-verification of land registry data (State Geocadastre) and property "
        "rights registry data (State Registry of Real Property Rights). "
        "The purpose of this audit is to identify discrepancies between the two data sources "
        "and to flag records requiring further verification or corrective action.",
        sBodyJ))
    story.append(Paragraph(
        f"System-generated report identifier: <b>{report_id}</b>. "
        f"Generation timestamp: <b>{ts_str}</b>.",
        sBodyJ))

    # ── 3. Summary ────────────────────────────────────────────────────────────
    story.append(HR(thick=0.5, clr="#CCCCCC", sb=4, sa=2))
    story.append(Paragraph("2.  SUMMARY OF FINDINGS", sSec))

    story.append(Paragraph(
        f"Total asset records reviewed:  <b>{total}</b>", sItem))
    story.append(Paragraph(
        f"Records with identified discrepancies:  <b>{n_bad}</b>", sItem))
    story.append(Paragraph(
        f"Records with full data consistency:  <b>{n_ok}</b>", sItem))
    if total:
        pct = round(n_bad / total * 100, 1)
        story.append(Paragraph(
            f"Overall discrepancy rate:  <b>{pct}%</b>", sItem))

    # Discrepancy breakdown
    freq: dict = {}
    for rec in records:
        for p in (rec.problems or []):
            freq[p] = freq.get(p, 0) + 1

    if freq:
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(
            "Distribution of discrepancy types:", sLabel))
        for i, (key, count) in enumerate(
                sorted(freq.items(), key=lambda x: x[1], reverse=True), 1):
            pct_p = round(count / total * 100, 1) if total else 0
            story.append(Paragraph(
                f"{i}.  {_lbl(key)} "
                f"[{count} record(s) / {pct_p}% of total]",
                sItem))

    # ── 4. Record evidence ────────────────────────────────────────────────────
    story.append(HR(thick=0.5, clr="#CCCCCC", sb=4, sa=2))
    story.append(Paragraph("3.  RECORD-BY-RECORD AUDIT EVIDENCE", sSec))
    story.append(Paragraph(
        "The following section lists each audited record with the relevant data "
        "extracted from both registries and, where applicable, the identified "
        "discrepancies requiring corrective attention.", sBodyJ))
    story.append(Spacer(1, 2*mm))

    for idx, rec in enumerate(records, 1):
        land  = rec.land_data     or {}
        prop  = rec.property_data or {}
        probs = rec.problems      or []
        cadastral = _tr(land.get("cadastral_number"))

        block = []

        # Record heading
        block.append(Paragraph(
            f"Record {idx}  |  Cadastral Number: {cadastral}",
            sRecHdr))

        # Status
        if probs:
            block.append(Paragraph(
                f"Audit Status: DISCREPANCIES IDENTIFIED ({len(probs)} issue(s))",
                sProblem))
            for p in probs:
                block.append(Paragraph(f"\u2022  {_lbl(p)}", sProblem))
        else:
            block.append(Paragraph(
                "Audit Status: CONSISTENT - no discrepancies found", sClean))

        block.append(Spacer(1, 1.5*mm))

        # Land registry data
        block.append(Paragraph("Land Registry data (State Geocadastre):", sLabel))
        land_fields = [
            ("Land user / operator",         land.get("land_user")),
            ("EDRPOU / tax ID",              land.get("edrpou_of_land_user")),
            ("Location",                     land.get("location")),
            ("Area (sq. m.)",                land.get("area")),
            ("Designated purpose",           land.get("purpose")),
            ("Form of ownership",            land.get("form_of_ownership")),
            ("Date of ownership registration", land.get("date_of_state_registration_of_ownership")),
            ("Record number",                land.get("record_number_of_ownership")),
            ("KOATUU code",                  land.get("koatuu")),
        ]
        for lbl, val in land_fields:
            v = _tr(val)
            if v != "N/A":
                block.append(Paragraph(f"{lbl}:  <b>{v}</b>", sValB))

        block.append(Spacer(1, 1.5*mm))

        # Property registry data
        block.append(Paragraph(
            "Property Rights Registry (State Registry of Real Property Rights):", sLabel))
        prop_fields = [
            ("Taxpayer (owner)",              prop.get("name_of_the_taxpayer")),
            ("Tax number (EDRPOU / IPN)",     prop.get("tax_number_of_pp")),
            ("Object address",                prop.get("address_of_the_object")),
            ("Total area (sq. m.)",           prop.get("total_area")),
            ("Type of object",                prop.get("type_of_object")),
            ("Type of joint ownership",       prop.get("type_of_joint_ownership")),
            ("Date of ownership registration", prop.get("date_of_state_registration_of_ownership")),
        ]
        for lbl, val in prop_fields:
            v = _tr(val)
            if v != "N/A":
                block.append(Paragraph(f"{lbl}:  <b>{v}</b>", sValB))

        story.append(KeepTogether(block) if idx <= 5 else None or block[0])
        if idx > 5 or True:
            for item in block[1:]:
                story.append(item)

        if idx < len(records):
            story.append(HR(thick=0.3, clr="#DDDDDD", sb=2, sa=1))

    # ── 5. Conclusions ────────────────────────────────────────────────────────
    story.append(HR(thick=0.5, clr="#CCCCCC", sb=5, sa=2))
    story.append(Paragraph("4.  CONCLUSIONS AND RECOMMENDATIONS", sSec))
    if n_bad == 0:
        conclusion = (
            "The audit has found no discrepancies between the land registry and "
            "the property rights registry for the reviewed dataset. "
            "All records are consistent and require no corrective action at this time."
        )
    else:
        conclusion = (
            f"The audit has identified discrepancies in {n_bad} out of {total} "
            f"records ({round(n_bad/total*100,1) if total else 0}%). "
            "Records flagged in Section 3 require review by the responsible registry "
            "officers. Corrective entries must be submitted to the relevant state "
            "authorities in accordance with the applicable legislation on state "
            "registration of land rights and real property rights."
        )
    story.append(Paragraph(conclusion, sBodyJ))

    # ── 6. Signature block ────────────────────────────────────────────────────
    story.append(HR(thick=0.5, clr="#CCCCCC", sb=5, sa=3))
    story.append(Paragraph("5.  AUTHORISATION", sSec))

    sig_left_style  = _style("sl", size=9, clr=BLACK, sb=0, sa=1)
    sig_right_style = _style("sr", size=9, clr=BLACK, sb=0, sa=1, align=2)

    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Prepared by:  Asset Management Department", sig_left_style))
    story.append(Paragraph(
        f"Signature: _________________________     Date: {date_str}",
        sig_left_style))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Reviewed and approved by:  Head of Department", sig_left_style))
    story.append(Paragraph(
        f"Signature: _________________________     Date: _______________",
        sig_left_style))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Official seal of the Unified Territorial Community:",
        sig_left_style))
    story.append(Paragraph(
        "M.P.  ___________________________", sig_left_style))

    # ── 7. Legal footer note ──────────────────────────────────────────────────
    story.append(HR(thick=1.5, clr="#1B3A6B", sb=6, sa=2))
    story.append(Paragraph(
        "This document was generated automatically by the Asset Registry Audit Information System. "
        "It constitutes an official internal audit record of the Unified Territorial Community. "
        "Unauthorised disclosure or reproduction of this document is prohibited. "
        "Ukrainian-language data fields have been transliterated to Latin script for "
        "typographical compatibility of this electronic copy.",
        sSmall))

    doc.build(story)
    return buf.getvalue()


# ── Legacy shim ───────────────────────────────────────────────────────────────
class PDFGenerator:
    def generate_report_pdf(self, report, records):
        return generate_audit_pdf(report, records)
