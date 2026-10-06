import pytesseract
from PIL import Image
import logging
from heartbeat.config import get_config

# Configure logging
logger = logging.getLogger("HEARTBEAT_OCR")

def extract_text_from_image(image_path: str) -> str:
    """ISSUE 14.1 FIX: Extract text from image using a configurable tesseract path."""
    try:
        config = get_config()
        # Set tesseract path from config
        pytesseract.pytesseract.tesseract_cmd = config.tesseract_cmd
        
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        logger.error(f"OCR Extraction Failed for {image_path}: {str(e)}")
        return ""

# Export alias for backward and inter-module compatibility
extract_text = extract_text_from_image
