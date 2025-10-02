import pdfplumber
import pytesseract
from PIL import Image
from PyPDF2 import PdfReader

def extract_text_from_pdf(file):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception:
        text = ""
    return text.strip()

def extract_text_with_ocr(file):
    text = ""
    try:
        reader = PdfReader(file)
        for page in reader.pages:
            x_object = page.get("/Resources").get("/XObject")
            if x_object:
                for obj in x_object:
                    if x_object[obj]["/Subtype"] == "/Image":
                        size = (x_object[obj]["/Width"], x_object[obj]["/Height"])
                        data = x_object[obj].get_data()
                        img = Image.frombytes("RGB", size, data)
                        text += pytesseract.image_to_string(img)
    except Exception:
        text = ""
    return text.strip()

def extract_text_from_txt(file):
    return file.read().decode("utf-8", errors="ignore")
