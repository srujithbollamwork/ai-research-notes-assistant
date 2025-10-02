from fpdf import FPDF
import datetime

def save_text_as_pdf(title, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=title, ln=True, align="C")
    pdf.ln(10)

    for line in content.split("\n"):
        pdf.multi_cell(0, 10, line)

    filename = f"{title}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(filename)
    return filename
