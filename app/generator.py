"""
Document generator service for Recon Analytics reports.
"""

import base64
import os
import tempfile
import uuid
from typing import Optional

from .recon_formatter import ReconDocumentFormatter
from .models import DocumentRequest, SectionContent

# Default logo path (bundled in Docker image at /app/assets/)
DEFAULT_LOGO_PATH = "/app/assets/recon_logo.png"


def decode_base64_image(base64_data: str, suffix: str = ".png") -> str:
    """Decode base64 image data and save to temp file."""
    # Handle data URL format
    if "," in base64_data:
        base64_data = base64_data.split(",")[1]

    image_data = base64.b64decode(base64_data)
    temp_path = tempfile.mktemp(suffix=suffix)
    with open(temp_path, "wb") as f:
        f.write(image_data)
    return temp_path


def generate_document(
    request: DocumentRequest,
    output_dir: str = "/tmp",
    filename: Optional[str] = None,
) -> str:
    """
    Generate a Recon Analytics Word document from the request.

    Args:
        request: DocumentRequest with document structure
        output_dir: Directory to save the document
        filename: Optional filename (generated if not provided)

    Returns:
        Path to the generated document
    """
    formatter = ReconDocumentFormatter()
    formatter.reset_caption_counters()
    formatter.setup_document()

    # Add page numbers
    formatter.add_page_number_header()

    # Add title block
    formatter.add_title_block(
        title=request.title,
        subtitle=request.subtitle,
        author=request.author,
        date=request.date,
    )

    # Add Table of Contents if requested
    if request.include_toc:
        formatter.add_table_of_contents()

    # Process sections
    for section in request.sections:
        # Add section heading based on level
        if section.level == 2:
            formatter.add_section_heading(section.title)
        elif section.level == 3:
            formatter.add_subsection(section.title)
        elif section.level == 4:
            formatter.add_minor_heading(section.title)

        # Process section content
        for content in section.content:
            _process_content(formatter, content)

    # Add footer with logo
    logo_path = None
    temp_logo = False

    if request.logo_base64:
        # Use provided logo (base64 encoded)
        logo_path = decode_base64_image(request.logo_base64)
        temp_logo = True
    elif os.path.exists(DEFAULT_LOGO_PATH):
        # Use default bundled logo
        logo_path = DEFAULT_LOGO_PATH
        temp_logo = False

    formatter.add_footer(logo_path)

    # Clean up temp logo file (only if we created it from base64)
    if temp_logo and logo_path and os.path.exists(logo_path):
        try:
            os.remove(logo_path)
        except Exception:
            pass

    # Generate filename if not provided
    if not filename:
        safe_title = "".join(
            c if c.isalnum() or c in " -_" else "_" for c in request.title
        )
        safe_title = safe_title.replace(" ", "_")[:50]
        filename = f"{safe_title}_{uuid.uuid4().hex[:8]}.docx"

    output_path = os.path.join(output_dir, filename)
    formatter.save(output_path)

    return output_path


def _process_content(formatter: ReconDocumentFormatter, content: SectionContent):
    """Process a single content item."""
    if content.type == "paragraph":
        formatter.add_paragraph(
            content.text or "",
            italic=content.italic or False,
            bold=content.bold or False,
        )

    elif content.type == "subsection":
        formatter.add_subsection(content.text or "")

    elif content.type == "minor_heading":
        formatter.add_minor_heading(content.text or "")

    elif content.type == "table" and content.table:
        table = content.table
        # Convert highlights from list to dict
        highlights = {}
        if table.highlights:
            for h in table.highlights:
                highlights[(h.row, h.col)] = h.type

        formatter.add_table(
            headers=table.headers,
            data=table.rows,
            col_widths=table.column_widths,
            highlights=highlights,
            numeric_cols=table.numeric_columns,
            caption=table.caption,
        )

    elif content.type == "figure" and content.figure:
        image_path = decode_base64_image(content.figure.image_base64)
        try:
            formatter.add_figure(
                image_path=image_path,
                description=content.figure.description,
                width_inches=content.figure.width_inches,
            )
        finally:
            if os.path.exists(image_path):
                os.remove(image_path)

    elif content.type == "chart" and content.chart:
        image_path = decode_base64_image(content.chart.image_base64)
        try:
            formatter.add_chart(
                image_path=image_path,
                description=content.chart.description,
                width_inches=content.chart.width_inches,
            )
        finally:
            if os.path.exists(image_path):
                os.remove(image_path)
