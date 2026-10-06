from PIL import Image
import os
from typing import Dict, Any

def get_image_info(image_path: str) -> Dict[str, Any]:
    """Extracts size, format and dominant colors locally using Pillow."""
    if not os.path.exists(image_path):
        return {}
    
    try:
        with Image.open(image_path) as img:
            info = {
                "size": f"{img.size[0]}x{img.size[1]}",
                "format": img.format.upper(),
                "mode": img.mode
            }
            
            # Extract basic color profile (Top 3 colors)
            # Resize for speed and get colors
            small_img = img.resize((50, 50)).convert("RGB")
            colors = small_img.getcolors(2500)
            if colors:
                colors.sort(key=lambda x: x[0], reverse=True)
                top_colors = [str(c[1]) for c in colors[:3]]
                info["colors"] = ", ".join(top_colors)
            else:
                info["colors"] = "Unknown"
                
            return info
    except Exception as e:
        print(f"Metadata Error: {e}")
        return {}
