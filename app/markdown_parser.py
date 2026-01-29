"""
Markdown parser for converting markdown to Recon document structure.
"""

import re
from typing import Optional
from .models import (
    DocumentRequest,
    DocumentSection,
    SectionContent,
    TableData,
    TableHighlight,
)

# Sections that should have conditional highlighting on +/- values
HIGHLIGHT_ENABLED_SECTIONS = {
    "guidance changes",
    "consumer trends",
    "financial performance",
    "market share",
}

# Sections where tables should be rendered as prose with bullet points
PROSE_SECTIONS = {
    "first-time disclosures",
    "strategic shifts",
}


def should_enable_highlighting(section_name: str, subsection_name: str = None) -> bool:
    """Check if the current section/subsection should have table highlighting."""
    section_lower = section_name.lower() if section_name else ""
    subsection_lower = subsection_name.lower() if subsection_name else ""

    for enabled_section in HIGHLIGHT_ENABLED_SECTIONS:
        if enabled_section in section_lower or enabled_section in subsection_lower:
            return True
    return False


def should_render_as_prose(section_name: str, subsection_name: str = None) -> bool:
    """Check if tables in this section should be rendered as prose."""
    section_lower = section_name.lower() if section_name else ""
    subsection_lower = subsection_name.lower() if subsection_name else ""

    for prose_section in PROSE_SECTIONS:
        if prose_section in section_lower or prose_section in subsection_lower:
            return True
    return False


def convert_table_to_prose(table_lines: list[str]) -> list[SectionContent]:
    """
    Convert a markdown table to prose format with bold labels.

    Each row becomes a paragraph with the first column bolded as the label,
    followed by the remaining columns as descriptive text.
    """
    if len(table_lines) < 3:
        return []

    # Parse headers
    header_line = table_lines[0].strip()
    headers = [cell.strip() for cell in header_line.split("|")[1:-1]]

    # Parse data rows (skip separator line at index 1)
    content_items = []
    for line in table_lines[2:]:
        line = line.strip()
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.split("|")[1:-1]]

        if not cells:
            continue

        # First cell is typically the topic/label (may already have **bold**)
        label = cells[0]
        # Remove existing bold markers if present
        label = re.sub(r"\*\*(.+?)\*\*", r"\1", label)

        # Build prose from remaining cells with their header context
        prose_parts = []
        for i, cell in enumerate(cells[1:], start=1):
            if cell and i < len(headers):
                header = headers[i]
                # Clean up cell content - remove bold markers
                cell_clean = re.sub(r"\*\*(.+?)\*\*", r"\1", cell)
                prose_parts.append(f"{header}: {cell_clean}")

        # Construct the paragraph text
        if prose_parts:
            prose_text = f"**{label}** — " + " | ".join(prose_parts)
        else:
            prose_text = f"**{label}**"

        content_items.append(
            SectionContent(type="paragraph", text=prose_text, bold=False, italic=False)
        )

    return content_items


def parse_markdown_table(lines: list[str], enable_highlighting: bool = True) -> Optional[TableData]:
    """Parse a markdown table into TableData.

    Args:
        lines: Lines of markdown table
        enable_highlighting: If False, no conditional highlighting is applied
    """
    if len(lines) < 2:
        return None

    # Parse header row
    header_line = lines[0].strip()
    if not header_line.startswith("|"):
        return None

    headers = [cell.strip() for cell in header_line.split("|")[1:-1]]

    # Skip separator row (line 1)
    if len(lines) < 3:
        return None

    # Parse data rows
    rows = []
    highlights = []
    numeric_columns = []

    for row_idx, line in enumerate(lines[2:]):
        line = line.strip()
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        rows.append(cells)

        # Detect numeric columns and highlights
        for col_idx, cell in enumerate(cells):
            # Check if cell looks numeric (percentage, number, currency)
            if re.match(r"^[-+]?[\d,.%$]+[%pp]*$", cell.replace(" ", "")):
                if col_idx not in numeric_columns:
                    numeric_columns.append(col_idx)

            # Only apply highlighting if enabled for this section
            if enable_highlighting:
                # Detect positive/negative values for highlights
                if cell.startswith("+") and ("%" in cell or "pp" in cell):
                    highlights.append(
                        TableHighlight(row=row_idx, col=col_idx, type="positive")
                    )
                elif cell.startswith("-") and ("%" in cell or "pp" in cell):
                    highlights.append(
                        TableHighlight(row=row_idx, col=col_idx, type="negative")
                    )

    return TableData(
        caption=None,  # Will be set from preceding text if available
        headers=headers,
        rows=rows,
        numeric_columns=numeric_columns if numeric_columns else None,
        highlights=highlights if highlights else None,
    )


def parse_markdown(
    markdown: str,
    title_override: Optional[str] = None,
    author: Optional[str] = None,
    date: Optional[str] = None,
    include_toc: bool = True,
) -> DocumentRequest:
    """
    Parse markdown content into a DocumentRequest.

    Supports:
    - # H1 (document title)
    - ## H2 (sections)
    - ### H3 (subsections)
    - #### H4 (minor headings)
    - Paragraphs
    - Markdown tables
    - **bold** and *italic* (converted to plain text with formatting flags)

    Section-aware behavior:
    - "First-Time Disclosures" and "Strategic Shifts" tables become prose
    - Only "Guidance Changes", "Consumer Trends", "Financial Performance",
      "Market Share" tables get conditional highlighting
    """
    lines = markdown.split("\n")
    title = title_override
    subtitle = None
    sections: list[DocumentSection] = []
    current_section: Optional[DocumentSection] = None
    current_content: list[SectionContent] = []
    pending_caption = None

    # Track current section/subsection names for context-aware rendering
    current_section_name = ""
    current_subsection_name = ""

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # H1 - Document title
        if line.startswith("# ") and not line.startswith("## "):
            if not title:
                title = line[2:].strip()
            i += 1
            continue

        # H2 - Section
        if line.startswith("## "):
            # Save previous section
            if current_section:
                current_section.content = current_content
                sections.append(current_section)

            section_title = line[3:].strip()
            current_section_name = section_title
            current_subsection_name = ""  # Reset subsection when new section starts
            current_section = DocumentSection(title=section_title, level=2, content=[])
            current_content = []
            i += 1
            continue

        # H3 - Subsection
        if line.startswith("### "):
            subsection_title = line[4:].strip()
            current_subsection_name = subsection_title
            current_content.append(
                SectionContent(type="subsection", text=subsection_title)
            )
            i += 1
            continue

        # H4 - Minor heading
        if line.startswith("#### "):
            minor_title = line[5:].strip()
            current_content.append(
                SectionContent(type="minor_heading", text=minor_title)
            )
            i += 1
            continue

        # Table detection
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1

            # Check if this section's tables should be rendered as prose
            if should_render_as_prose(current_section_name, current_subsection_name):
                prose_items = convert_table_to_prose(table_lines)
                current_content.extend(prose_items)
                pending_caption = None  # Don't use caption for prose
            else:
                # Determine if highlighting should be enabled for this table
                enable_highlighting = should_enable_highlighting(
                    current_section_name, current_subsection_name
                )
                table_data = parse_markdown_table(table_lines, enable_highlighting)
                if table_data:
                    # Check if previous line was a potential caption
                    if pending_caption:
                        table_data.caption = pending_caption
                        pending_caption = None
                    current_content.append(SectionContent(type="table", table=table_data))
            continue

        # Check for table caption pattern (e.g., "Table 1: Description" or just description before table)
        if re.match(r"^(Table|Figure|Chart)\s+\d+:", line, re.IGNORECASE):
            # Extract just the description part
            match = re.match(r"^(?:Table|Figure|Chart)\s+\d+:\s*(.+)$", line, re.IGNORECASE)
            if match:
                pending_caption = match.group(1).strip()
            i += 1
            continue

        # Regular paragraph
        # Check for bold/italic markers
        is_italic = line.startswith("*") and line.endswith("*") and not line.startswith("**")
        is_bold = line.startswith("**") and line.endswith("**")

        text = line
        if is_italic:
            text = line.strip("*")
        elif is_bold:
            text = line.strip("*")

        # Clean up inline formatting for display
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # Remove bold markers
        text = re.sub(r"\*(.+?)\*", r"\1", text)  # Remove italic markers

        # Check if this might be a caption for an upcoming table
        if i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
            pending_caption = text
        else:
            current_content.append(
                SectionContent(
                    type="paragraph", text=text, italic=is_italic, bold=is_bold
                )
            )

        i += 1

    # Save last section
    if current_section:
        current_section.content = current_content
        sections.append(current_section)

    # If no title found, use a default
    if not title:
        title = "Untitled Document"

    return DocumentRequest(
        title=title,
        subtitle=subtitle,
        author=author,
        date=date,
        include_toc=include_toc,
        sections=sections,
    )
