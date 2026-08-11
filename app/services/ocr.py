import re
from PIL import Image
import pytesseract
from io import BytesIO

# Optional PDF support
try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except Exception:
    PDF2IMAGE_AVAILABLE = False

# Regex patterns for Tunisian invoice fields (simple heuristics)
PATTERNS = {
    'rc': re.compile(r"N\s*°?\s*RC\s*[:\-\s]*([A-Z0-9]+)", re.IGNORECASE),
    'ice': re.compile(r"ICE\s*[:\-\s]*([0-9A-Z]+)", re.IGNORECASE),
    'tva_id': re.compile(r"Identifiant\s*Fiscal\s*[:\-\s]*([0-9A-Z]+)", re.IGNORECASE),
    'date': re.compile(r"(\d{2}[\/\-]\d{2}[\/\-]\d{4})"),
    'montant_ht': re.compile(r"Montant\s*HT\s*[:\-\s]*([0-9\.,]+)", re.IGNORECASE),
    'total_ttc': re.compile(r"Total\s*(?:TTC)?\s*[:\-\s]*([0-9\.,]+)", re.IGNORECASE),
    'taux_tva': re.compile(r"(\d{1,2}(?:[\.,]\d+)?)[\s]*%"),
}


def _extract_text_from_image(img: Image.Image):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    text = pytesseract.image_to_string(img, lang='fra')
    return text


def ocr_extract(file_bytes: bytes):
    """
    Extrait le texte d'une image ou PDF et tente d'identifier les champs principaux.
    Retourne un dict avec les champs trouvés.
    - If a PDF is provided and pdf2image is available, convert first page to image.
    """
    # Detect PDF by header
    is_pdf = file_bytes[:4] == b'%PDF'

    images = []

    if is_pdf:
        if not PDF2IMAGE_AVAILABLE:
            return {"error": "Le support PDF nécessite pdf2image et poppler (non disponibles)."}
        try:
            pages = convert_from_bytes(file_bytes, first_page=1, last_page=1)
            if not pages:
                return {"error": "Impossible de convertir le PDF en image."}
            images = pages
        except Exception as e:
            return {"error": f"Erreur conversion PDF: {e}"}
    else:
        try:
            img = Image.open(BytesIO(file_bytes))
            images = [img]
        except Exception:
            return {"error": "Impossible d'ouvrir l'image fournie."}

    # Combine OCR results from first image/page
    text = _extract_text_from_image(images[0])

    data = {
        'raw_text': text,
        'rc': None,
        'ice': None,
        'tva_id': None,
        'date': None,
        'montant_ht': None,
        'total_ttc': None,
        'taux_tva': None
    }

    for key, pattern in PATTERNS.items():
        m = pattern.search(text)
        if m:
            data[key] = m.group(1).strip()

    # Normalize numbers
    for num_field in ['montant_ht', 'total_ttc', 'taux_tva']:
        if data.get(num_field):
            v = data[num_field].replace(' ', '').replace(',', '.')
            try:
                data[num_field] = float(v)
            except Exception:
                pass

    return data
