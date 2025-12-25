from io import BytesIO
from PIL import Image
import pytesseract

def extract_text_from_image(file_obj) -> str:
    """
    Extract text from an image file-like object using pytesseract if available.
    Returns empty string if OCR libs are missing.
    """
    try:
        if hasattr(file_obj, "read"):
            data = file_obj.read()
        else:
            data = file_obj
        img = Image.open(BytesIO(data) if isinstance(data, (bytes, bytearray)) else file_obj)
        text = pytesseract.image_to_string(img)
        return text or ""
    except Exception:
        return ""
