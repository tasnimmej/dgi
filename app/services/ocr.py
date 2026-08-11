import re
from PIL import Image
import pytesseract
from io import BytesIO

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


def ocr_extract(image_bytes: bytes):
    """
    Extrait le texte d'une image et tente d'identifier les champs principaux.
    Retourne un dict avec les champs trouvés.
    """
    try:
        img = Image.open(BytesIO(image_bytes))
    except Exception:
        return {"error": "Impossible d'ouvrir l'image ou le PDF fourni."}

    # Convertir en RGB si nécessaire
    if img.mode != 'RGB':
        img = img.convert('RGB')

    text = pytesseract.image_to_string(img, lang='fra')

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
