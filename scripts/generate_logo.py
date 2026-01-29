#!/usr/bin/env python3
"""
Generate a placeholder Recon Analytics logo.

This creates a simple navy banner with "RECON ANALYTICS" text.
Replace with actual logo by extracting from a branded document:
    python -c "from app.recon_formatter import ReconDocumentFormatter; \
               f = ReconDocumentFormatter(); \
               f.extract_logo('/path/to/branded.docx', '/app/assets/recon_logo.png')"
"""

import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow not installed. Run: pip install Pillow")
    sys.exit(1)


def generate_placeholder_logo(output_path: str, width: int = 1379, height: int = 128):
    """Generate a placeholder Recon Analytics logo."""
    # Brand colors
    navy = (0x20, 0x38, 0x64)  # #203864
    white = (255, 255, 255)

    # Create image with navy background
    img = Image.new("RGB", (width, height), navy)
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fall back to default
    text = "RECON ANALYTICS"
    font_size = 48

    try:
        # Try common system fonts
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, font_size)
                break
        if font is None:
            font = ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2

    # Draw text
    draw.text((x, y), text, fill=white, font=font)

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Generated placeholder logo: {output_path}")


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "assets/recon_logo.png"
    generate_placeholder_logo(output)
