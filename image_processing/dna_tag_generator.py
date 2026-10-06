from .ocr_extractor import extract_text
from .metadata_reader import get_image_info

def generate_dna_tag(image_path: str) -> str:
    """Combines OCR text and metadata into a natural-language image description."""
    # 1. Get OCR Text (Local)
    ocr_text = extract_text(image_path)

    # 2. Get Image Metadata (Local)
    info = get_image_info(image_path)

    if not info:
        return "Image processing failed."

    # Build a natural-language description the AI can understand
    parts = []

    # Image format & size
    size = info.get('size', 'Unknown')
    fmt = info.get('format', 'image')
    parts.append(f"This is a {size} {fmt} image.")

    # Color palette (translate RGB tuples to color names)
    colors_raw = info.get('colors', '')
    if colors_raw and colors_raw != 'Unknown':
        # Convert "(255, 255, 255)" tuples to readable format
        colors_clean = colors_raw.replace('(', '').replace(')', '').replace(', ', ' ')
        parts.append(f"The dominant colors in this image are: {colors_clean}.")

    # OCR text found in the image
    if ocr_text.strip():
        parts.append(f"The following text was extracted from the image:\n\"{ocr_text.strip()}\"")
    else:
        parts.append("No readable text was detected in this image (it may be a photo, screenshot, or illustration).")

    return "\n".join(parts)
