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
    """Generate a Recon Analytics logo matching brand standards.

    Creates a light gray banner with navy wave symbol and "RECON ANALYTICS" text.
    """
    # Brand colors
    navy = (0x20, 0x38, 0x64)  # #203864
    light_gray = (0xE8, 0xE8, 0xE8)  # Light gray background

    # Create image with light gray background
    img = Image.new("RGB", (width, height), light_gray)
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fall back to default
    font_size = 42
    small_font_size = 38

    try:
        # Try common system fonts
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        font = None
        small_font = None
        for path in font_paths:
            if os.path.exists(path):
                font = ImageFont.truetype(path, font_size)
                small_font = ImageFont.truetype(path, small_font_size)
                break
        if font is None:
            font = ImageFont.load_default()
            small_font = font
    except Exception:
        font = ImageFont.load_default()
        small_font = font

    # Draw the wave/checkmark symbol on the left
    # Simple stylized wave shape
    wave_start_x = 40
    wave_y_center = height // 2

    # Draw a stylized wave using lines (simplified logo mark)
    wave_points = [
        (wave_start_x, wave_y_center + 15),
        (wave_start_x + 25, wave_y_center - 25),
        (wave_start_x + 50, wave_y_center + 5),
    ]
    # Draw thick lines for the wave
    for i in range(len(wave_points) - 1):
        draw.line([wave_points[i], wave_points[i + 1]], fill=navy, width=6)

    # Draw "RECON" text
    text_x = wave_start_x + 70
    recon_text = "RECON"
    draw.text((text_x, height // 2 - 35), recon_text, fill=navy, font=font)

    # Draw "ANALYTICS" text below RECON
    analytics_text = "ANALYTICS"
    draw.text((text_x, height // 2 + 5), analytics_text, fill=navy, font=small_font)

    # Save
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    img.save(output_path, "PNG")
    print(f"Generated Recon Analytics logo: {output_path}")


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "assets/recon_logo.png"
    generate_placeholder_logo(output)
