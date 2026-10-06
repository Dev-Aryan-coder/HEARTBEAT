import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Add root to path
sys.path.append(os.getcwd())

from image_processing.dna_tag_generator import generate_dna_tag

def create_test_image(path: str):
    """Creates a local test image for verification."""
    print(f"Creating test image: {path}...")
    # Create 200x100 red image
    img = Image.new('RGB', (200, 100), color=(255, 0, 0))
    d = ImageDraw.Draw(img)
    
    # Simple text (using default font as we don't know accessible paths)
    try:
        d.text((10, 10), "HEARTBEAT OCR TEST", fill=(255, 255, 255))
    except:
        pass # In case drawing fails, we still have the image
        
    img.save(path)
    print("Test image saved locally.")

def test_phase6():
    print("--- Phase 6 Verification: Image Processing (Local) ---")
    
    test_img_path = "test_vision.png"
    create_test_image(test_img_path)
    
    # Run the generator
    print("\nProcessing Image locally (OCR + Metadata)...")
    try:
        dna_tag = generate_dna_tag(test_img_path)
        print(f"DNA Tag Generated: \n{dna_tag}")
        
        # Basic validations
        if "200x100" in dna_tag and "PNG" in dna_tag:
            print("\n✅ Metadata Verification OK")
        if "Colors:" in dna_tag:
            print("✅ Color Profile OK")
        if "Text:" in dna_tag:
             print("✅ DNA Tag Format OK")
             
    except Exception as e:
        print(f"❌ Local vision failed: {e}")
    finally:
        # Cleanup
        if os.path.exists(test_img_path):
            os.remove(test_img_path)
            
    print("\n--- Phase 6 Verification Complete ---")

if __name__ == "__main__":
    test_phase6()
