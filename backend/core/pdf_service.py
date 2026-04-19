"""
Офіційний Акт перевірки — генератор PDF.
Кирилиця підтримується через шрифти DejaVuSerif, що зберігаються в backend/fonts/.
"""
import io
import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, HRFlowable, KeepTogether,
)

# ── Compat stubs (imported by views.py) ──────────────────────────────────────
FONT_PATH = ""
def register_fonts(): pass

# ── Шрифти: DejaVuSerif (підтримує кирилицю) ─────────────────────────────────
_FONT   = "Helvetica"
_FONT_B = "Helvetica-Bold"
_CYRILLIC = False

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_FONTS_DIR = os.path.join(_BASE_DIR, "..", "fonts")

_CANDIDATES = [
    (
        os.path.join(_FONTS_DIR, "DejaVuSerif.ttf"),
        os.path.join(_FONTS_DIR, "DejaVuSerif-Bold.ttf"),
    ),
    # системні шрифти як запасний варіант
    (
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf",
    ),
    (
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    ),
]

for _r, _b in _CANDIDATES:
    if os.path.isfile(_r) and os.path.isfile(_b):
        try:
            pdfmetrics.registerFont(TTFont("CyrFont",      _r))
            pdfmetrics.registerFont(TTFont("CyrFont-Bold", _b))
            _FONT, _FONT_B, _CYRILLIC = "CyrFont", "CyrFont-Bold", True
        except Exception:
            pass
        break

def _tr(v) -> str:
    if v is None:
        return "Н/Д"
    s = str(v).strip()
    return s if s else "Н/Д"

# ── Мітки проблем (українською) ───────────────────────────────────────────────
PROBLEM_LABELS = {
    "edrpou_of_land_user":                     "Невідповідність ЄДРПОУ землекористувача",
    "land_user":                               "Невідповідність назви землекористувача/власника",
    "location":                                "Розбіжність у місцезнаходженні/адресі",
    "area":                                    "Розбіжність у площі об'єкта",
    "date_of_state_registration_of_ownership": "Невідповідність дати держреєстрації права",
    "share_of_ownership":                      "Розбіжність у частці права власності",
    "purpose":                                 "Невідповідність у цільовому призначенні",
    "missing_owner":                           "Відсутня інформація про власника",
}
def _lbl(k): return PROBLEM_LABELS.get(k, k.replace("_", " ").title())

BK = colors.black


# ── Колонтитули ───────────────────────────────────────────────────────────────
def _page_decorator(doc_number: str, date_str: str):
    def _draw(canvas, doc):
        canvas.saveState()
        W, H = A4
        MX = 20 * mm

        canvas.setStrokeColor(BK)
        canvas.setLineWidth(1.5)
        canvas.line(MX, H - 14 * mm, W - MX, H - 14 * mm)
        canvas.setLineWidth(0.3)
        canvas.line(MX, H - 15.5 * mm, W - MX, H - 15.5 * mm)

        canvas.setFillColor(BK)
        canvas.setFont(_FONT_B, 8)
        canvas.drawCentredString(
            W / 2, H - 11 * mm,
            "ВІДДІЛ УПРАВЛІННЯ АКТИВАМИ — ОБ'ЄДНАНА ТЕРИТОРІАЛЬНА ГРОМАДА")

        canvas.setLineWidth(1.0)
        canvas.line(MX, 16 * mm, W - MX, 16 * mm)
        canvas.setLineWidth(0.3)
        canvas.line(MX, 17.3 * mm, W - MX, 17.3 * mm)

        canvas.setFont(_FONT, 7.5)
        canvas.drawString(MX, 12 * mm,
            f"Акт перевірки №{doc_number}   |   Дата: {date_str}")
        canvas.drawRightString(W - MX, 12 * mm, f"Стор. {doc.page}")

        canvas.restoreState()
    return _draw


# ── Допоміжна функція стилів ──────────────────────────────────────────────────
def _s(name, size=11, bold=False, align=0, sb=0, sa=4, indent=0, leading=None):
    return ParagraphStyle(
        name,
        fontName=_FONT_B if bold else _FONT,
        fontSize=size,
        textColor=BK,
        alignment=align,
        spaceBefore=sb,
        spaceAfter=sa,
        leftIndent=indent,
        leading=leading or round(size * 1.45),
    )

def HR(thick=0.5, sb=3, sa=3):
    return HRFlowable(
        width="100%", thickness=thick, color=BK,
        spaceBefore=sb * mm, spaceAfter=sa * mm)


# ── Основна функція ───────────────────────────────────────────────────────────
def generate_audit_pdf(report, records_qs) -> bytes:
    records   = list(records_qs)
    total     = len(records)
    n_bad     = sum(1 for r in records if r.problems)
    n_ok      = total - n_bad
    report_id = str(report.id)
    short_id  = report_id[:8].upper()
    now       = datetime.utcnow()
    date_str  = now.strftime("%d.%m.%Y")
    ts_str    = now.strftime("%Y-%m-%d %H:%M UTC")

    buf = io.BytesIO()
    W, H = A4
    MX, CW = 20 * mm, W - 40 * mm

    frame = Frame(MX, 22 * mm, CW, H - 44 * mm,
                  leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        pageTemplates=[PageTemplate(
            id="main", frames=[frame],
            onPage=_page_decorator(short_id, date_str))],
        leftMargin=MX, rightMargin=MX,
        topMargin=22 * mm, bottomMargin=26 * mm,
    )

    sTitle  = _s("t",  size=17, bold=True, align=1, sb=4, sa=2)
    sSub    = _s("s",  size=10,            align=1, sb=0, sa=3)
    sMeta   = _s("m",  size=10, bold=True, align=1, sb=0, sa=8)
    sSec    = _s("sc", size=11, bold=True, sb=7, sa=3)
    sBodyJ  = _s("bj", size=10, align=4,  sb=0, sa=3, leading=15)
    sItem   = _s("it", size=10, sb=0, sa=3, indent=6)
    sRec    = _s("rh", size=11, bold=True, sb=7, sa=2)
    sLabel  = _s("gl", size=9,  sb=3, sa=1)
    sVal    = _s("v",  size=10, sb=0, sa=3, indent=4)
    sStatus = _s("st", size=10, bold=True, sb=0, sa=2, indent=6)
    sSig    = _s("sig",size=10, sb=0, sa=5)

    story = []

    # 1. Заголовок
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("АКТ ПЕРЕВІРКИ", sTitle))
    story.append(Paragraph(
        "звірки даних земельного та майнового реєстрів", sSub))
    story.append(Paragraph(
        f"Акт №\u00a0<b>{short_id}</b>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        f"Дата:\u00a0<b>{date_str}</b>", sMeta))
    story.append(HR(thick=1.5, sb=2, sa=4))

    # 2. Загальні відомості
    story.append(Paragraph("1.  ЗАГАЛЬНІ ВІДОМОСТІ", sSec))
    story.append(Paragraph(
        "Цей Акт перевірки складено Відділом управління активами Об'єднаної "
        "територіальної громади (ОТГ) у відповідності до встановленого порядку "
        "крос-перевірки даних земельного реєстру (Державний геокадастр) та реєстру "
        "майнових прав (Державний реєстр речових прав на нерухоме майно). "
        "Метою перевірки є виявлення розбіжностей між двома джерелами даних і "
        "позначення записів, що потребують подальшого уточнення або виправлення.",
        sBodyJ))
    story.append(Paragraph(
        f"Ідентифікатор звіту: <b>{report_id}</b>.   "
        f"Дата та час формування: <b>{ts_str}</b>.",
        sBodyJ))

    # 3. Зведені результати
    story.append(HR(thick=0.5, sb=4, sa=2))
    story.append(Paragraph("2.  ЗВЕДЕНІ РЕЗУЛЬТАТИ ПЕРЕВІРКИ", sSec))
    story.append(Paragraph(
        f"Усього перевірено записів:                    <b>{total}</b>", sItem))
    story.append(Paragraph(
        f"Записів із виявленими розбіжностями:          <b>{n_bad}</b>", sItem))
    story.append(Paragraph(
        f"Записів без розбіжностей (узгоджені дані):    <b>{n_ok}</b>", sItem))
    if total:
        pct = round(n_bad / total * 100, 1)
        story.append(Paragraph(
            f"Загальний відсоток розбіжностей:               <b>{pct}%</b>", sItem))

    freq: dict = {}
    for rec in records:
        for p in (rec.problems or []):
            freq[p] = freq.get(p, 0) + 1

    if freq:
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph("Розподіл типів розбіжностей:", sLabel))
        for i, (key, count) in enumerate(
                sorted(freq.items(), key=lambda x: x[1], reverse=True), 1):
            pct_p = round(count / total * 100, 1) if total else 0
            story.append(Paragraph(
                f"{i}.  {_lbl(key)}  [{count} запис(ів) / {pct_p}%]", sItem))

    # 4. Детальний перелік записів
    story.append(HR(thick=0.5, sb=4, sa=2))
    story.append(Paragraph("3.  ДЕТАЛЬНИЙ ПЕРЕЛІК ЗАПИСІВ", sSec))
    story.append(Paragraph(
        "У цьому розділі наведено кожен перевірений запис із даними з обох реєстрів "
        "та, за наявності, переліком виявлених розбіжностей, що потребують виправлення.",
        sBodyJ))
    story.append(Spacer(1, 2 * mm))

    for idx, rec in enumerate(records, 1):
        land  = rec.land_data     or {}
        prop  = rec.property_data or {}
        probs = rec.problems      or []
        cadastral = _tr(land.get("cadastral_number"))

        block = [Paragraph(
            f"Запис {idx}  |  Кадастровий №: {cadastral}", sRec)]

        if probs:
            block.append(Paragraph(
                f"Статус перевірки: ВИЯВЛЕНО РОЗБІЖНОСТІ ({len(probs)} проблем(и))",
                sStatus))
            for p in probs:
                block.append(Paragraph(f"   —  {_lbl(p)}", sStatus))
        else:
            block.append(Paragraph(
                "Статус перевірки: УЗГОДЖЕНО — розбіжностей не виявлено", sStatus))

        block.append(Spacer(1, 1.5 * mm))

        block.append(Paragraph("Земельний реєстр (Державний геокадастр):", sLabel))
        for lbl, val in [
            ("Землекористувач / оператор",          land.get("land_user")),
            ("ЄДРПОУ / ІПН",                        land.get("edrpou_of_land_user")),
            ("Місцезнаходження",                    land.get("location")),
            ("Площа (кв. м)",                       land.get("area")),
            ("Цільове призначення",                 land.get("purpose")),
            ("Форма власності",                     land.get("form_of_ownership")),
            ("Дата держреєстрації права",           land.get("date_of_state_registration_of_ownership")),
            ("Код КОАТУУ",                          land.get("koatuu")),
        ]:
            v = _tr(val)
            if v != "Н/Д":
                block.append(Paragraph(f"{lbl}:  <b>{v}</b>", sVal))

        block.append(Spacer(1, 1.5 * mm))
        block.append(Paragraph("Реєстр майнових прав:", sLabel))
        for lbl, val in [
            ("Платник податку (власник)",           prop.get("name_of_the_taxpayer")),
            ("Податковий номер (ЄДРПОУ/ІПН)",       prop.get("tax_number_of_pp")),
            ("Адреса об'єкта",                      prop.get("address_of_the_object")),
            ("Загальна площа (кв. м)",              prop.get("total_area")),
            ("Тип об'єкта",                         prop.get("type_of_object")),
            ("Вид спільної власності",              prop.get("type_of_joint_ownership")),
            ("Дата держреєстрації права",           prop.get("date_of_state_registration_of_ownership")),
        ]:
            v = _tr(val)
            if v != "Н/Д":
                block.append(Paragraph(f"{lbl}:  <b>{v}</b>", sVal))

        story.append(KeepTogether(block))
        if idx < len(records):
            story.append(HR(thick=0.3, sb=2, sa=1))

    # 5. Висновки та рекомендації
    story.append(HR(thick=0.5, sb=5, sa=2))
    story.append(Paragraph("4.  ВИСНОВКИ ТА РЕКОМЕНДАЦІЇ", sSec))
    if n_bad == 0:
        conc = (
            "За результатами перевірки розбіжностей між земельним реєстром та реєстром "
            "майнових прав у переглянутому масиві даних не виявлено. Усі записи є "
            "узгодженими і не потребують коригувальних дій на цей момент."
        )
    else:
        conc = (
            f"За результатами перевірки розбіжності виявлено у {n_bad} з {total} записів "
            f"({round(n_bad / total * 100, 1) if total else 0}%). Записи, позначені у "
            "Розділі 3, підлягають розгляду відповідальними реєстраційними службовцями. "
            "Виправлення мають бути подані до відповідних державних органів відповідно до "
            "чинного законодавства про державну реєстрацію прав на землю та нерухоме майно."
        )
    story.append(Paragraph(conc, sBodyJ))

    # Блок підписів
    story.append(Spacer(1, 6 * mm))
    story.append(HR(thick=0.5, sb=0, sa=3))
    story.append(Paragraph("Склав:  Відділ управління активами", sSig))
    story.append(Paragraph(
        f"Підпис: _______________________     Дата: {date_str}", sSig))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("Перевірив та затвердив:  Начальник відділу", sSig))
    story.append(Paragraph(
        "Підпис: _______________________     Дата: _______________", sSig))
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("Офіційна печатка:  М.П.  ________________________", sSig))

    doc.build(story)
    return buf.getvalue()


# ── Сумісність зі старим кодом ────────────────────────────────────────────────
class PDFGenerator:
    def generate_report_pdf(self, report, records):
        return generate_audit_pdf(report, records)
