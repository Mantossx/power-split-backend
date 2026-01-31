import os
import pytesseract
from PIL import Image
import io
import re
from dotenv import load_dotenv

load_dotenv()

tesseract_path = os.getenv("TESSERACT_PATH")
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path


def process_receipt(image_bytes: bytes):
    image = Image.open(io.BytesIO(image_bytes))

    text = pytesseract.image_to_string(image, lang='ind+eng', config='--psm 6')

    extracted_items = []
    lines = text.split('\n')

    ignore_keywords = [
        "Jalan", "Jl.", "Telp", "Bill", "Guest", "Dine In",
        "Sub Total", "Tax", "Pjk", "Service", "Pembulatan",
        "Total", "Non Tunai", "Edc", "Kembali", "Arigato",
        "Bento", "Whatsapp", "Email", "Call", "Summarecon"
    ]

    for line in lines:
        clean_line = line.strip()
        if not clean_line:
            continue

        if any(keyword.lower() in clean_line.lower() for keyword in ignore_keywords):
            continue

        match = re.search(r'^(\d+)\s+(.+)\s+([\d\.,]+)$', clean_line)

        if match:
            qty = match.group(1)
            item_name = match.group(2).strip()
            price_raw = match.group(3)

            price_clean = re.sub(r'\D', '', price_raw)

            if len(item_name) > 2 and price_clean.isdigit():
                extracted_items.append({
                    "qty": int(qty),
                    "name": item_name,
                    "price": float(price_clean)
                })

    return extracted_items