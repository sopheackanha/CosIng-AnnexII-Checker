"""
OCR Service for extracting text from images using Tesseract.
"""
from io import BytesIO
from pathlib import Path
import os
from PIL import Image
import pytesseract
import logging

logger = logging.getLogger(__name__)

# Attempt to locate Tesseract on Windows when it is not on PATH
_default_windows_paths = [
    Path(r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"),
    Path(r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe"),
]
_tesseract_env = os.environ.get("TESSERACT_CMD")
if _tesseract_env and Path(_tesseract_env).exists():
    pytesseract.pytesseract.tesseract_cmd = _tesseract_env
else:
    for candidate in _default_windows_paths:
        if candidate.exists():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            break


class OCRError(Exception):
    """Raised when OCR processing fails"""
    pass


def extract_text_from_image(file_obj, lang: str = 'eng') -> str:
    """
    Extract text from an image file-like object using pytesseract.
    
    Args:
        file_obj: File-like object, bytes, or path to image
        lang: Language code for OCR (default: 'eng' for English)
        
    Returns:
        Extracted text as string
        
    Raises:
        OCRError: If OCR processing fails critically
    """
    try:
        # Handle different input types
        if hasattr(file_obj, "read"):
            data = file_obj.read()
        else:
            data = file_obj
        
        # Open image
        if isinstance(data, (bytes, bytearray)):
            img = Image.open(BytesIO(data))
        else:
            img = Image.open(file_obj)
        
        # Convert to RGB if necessary
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        
        # Perform OCR
        text = pytesseract.image_to_string(img, lang=lang)
        
        if not text or not text.strip():
            logger.warning("No text could be extracted from image")
            return ""
        
        logger.info(f"Successfully extracted {len(text)} characters from image")
        return text.strip()
        
    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract is not installed or not in PATH")
        raise OCRError(
            "OCR engine not available. Please ensure Tesseract is installed."
        )
    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}")
        # Return empty string for graceful degradation
        return ""


def is_tesseract_available() -> bool:
    """
    Check if Tesseract OCR is available on the system.
    
    Returns:
        True if Tesseract is available, False otherwise
    """
    try:
        pytesseract.get_tesseract_version()
        return True
    except (pytesseract.TesseractNotFoundError, Exception):
        return False
