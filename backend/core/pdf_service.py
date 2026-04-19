import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import urllib.request

# Global font registration
FONT_PATH = "/tmp/DejaVuSans.ttf"
FONT_URL = "https://github.com/mushfiq/reportlab-fonts/raw/master/DejaVuSans.ttf"

def register_fonts():
    """Register a font that supports Ukrainian characters."""
    try:
        # Try to download if doesn't exist
        if not os.path.exists(FONT_PATH):
            urllib.request.urlretrieve(FONT_URL, FONT_PATH)
        
        pdfmetrics.registerFont(TTFont('DejaVuSans', FONT_PATH))
        return 'DejaVuSans'
    except Exception as e:
        print(f"Font registration failed: {e}")
        return 'Helvetica' # Fallback (no Cyrillic support)

class PDFGenerator:
    def __init__(self):
        self.font_name = register_fonts()
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name='UAText',
            fontName=self.font_name,
            fontSize=10,
            leading=12
        ))
        self.styles.add(ParagraphStyle(
            name='UATitle',
            fontName=self.font_name,
            fontSize=16,
            leading=20,
            alignment=1, # Center
            spaceAfter=20
        ))

    def generate_report_pdf(self, report, records):
        """Generate a PDF for a single report."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        # Title
        elements.append(Paragraph(f"Звіт про аудиторську перевірку №{str(report.id)[:8]}", self.styles['UATitle']))
        elements.append(Paragraph(f"Дата створення: {report.id.clock_seq if hasattr(report.id, 'clock_seq') else ''}", self.styles['UAText']))
        elements.append(Spacer(1, 12))

        # Table Header
        data = [[
            Paragraph("Кадастровий / ІПН", self.styles['UAText']),
            Paragraph("Місцерозташування", self.styles['UAText']),
            Paragraph("Проблеми", self.styles['UAText'])
        ]]

        # Table Rows (limit to 100 for basic version)
        for record in records[:100]:
            land = record.land_data if record.land_data else {}
            prop = record.property_data if record.property_data else {}
            
            identifier = land.get('cadastral_number') or prop.get('tax_number_of_pp') or "N/A"
            location = land.get('location') or prop.get('address_of_the_object') or "N/A"
            problems_str = ", ".join(record.problems) if record.problems else "Немає"

            data.append([
                Paragraph(str(identifier), self.styles['UAText']),
                Paragraph(str(location), self.styles['UAText']),
                Paragraph(problems_str, self.styles['UAText'])
            ])

        # Create Table
        table = Table(data, colWidths=[150, 200, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        # Highlight problems in red (example check)
        for i, record in enumerate(records[:100]):
            if record.problems:
                table.setStyle(TableStyle([
                    ('BACKGROUND', (2, i+1), (2, i+1), colors.lightpink),
                ]))

        elements.append(table)
        doc.build(elements)
        
        pdf_content = buffer.getvalue()
        buffer.close()
        return pdf_content
