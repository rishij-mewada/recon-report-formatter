"""
Pydantic models for Recon Analytics document generation API.
"""

from typing import Optional
from pydantic import BaseModel, Field


class TableHighlight(BaseModel):
    """Highlight definition for a table cell."""

    row: int = Field(..., description="Row index (0-based, excludes header)")
    col: int = Field(..., description="Column index (0-based)")
    type: str = Field(
        ..., description="Highlight type: 'positive' (green) or 'negative' (red)"
    )


class TableData(BaseModel):
    """Table definition for the document."""

    caption: Optional[str] = Field(
        None, description="Table caption (auto-numbered as 'Table X: caption')"
    )
    headers: list[str] = Field(..., description="Column headers")
    rows: list[list[str]] = Field(..., description="Table data rows")
    numeric_columns: Optional[list[int]] = Field(
        None, description="Column indices to right-align (0-based)"
    )
    highlights: Optional[list[TableHighlight]] = Field(
        None, description="Cells to highlight"
    )
    column_widths: Optional[list[int]] = Field(
        None, description="Column widths in DXA units"
    )


class FigureData(BaseModel):
    """Figure/image definition for the document."""

    description: str = Field(
        ..., description="Figure caption (auto-numbered as 'Figure X: description')"
    )
    image_base64: str = Field(..., description="Base64 encoded image data")
    width_inches: float = Field(6.0, description="Image width in inches")


class ChartData(BaseModel):
    """Chart definition for the document."""

    description: str = Field(
        ..., description="Chart caption (auto-numbered as 'Chart X: description')"
    )
    image_base64: str = Field(..., description="Base64 encoded chart image data")
    width_inches: float = Field(6.0, description="Chart width in inches")


class SectionContent(BaseModel):
    """Content item within a section."""

    type: str = Field(
        ...,
        description="Content type: 'paragraph', 'table', 'figure', 'chart', 'subsection', 'minor_heading'",
    )
    text: Optional[str] = Field(None, description="Text content (for paragraph/heading)")
    italic: Optional[bool] = Field(False, description="Italic text (for paragraph)")
    bold: Optional[bool] = Field(False, description="Bold text (for paragraph)")
    table: Optional[TableData] = Field(None, description="Table data (for table type)")
    figure: Optional[FigureData] = Field(
        None, description="Figure data (for figure type)"
    )
    chart: Optional[ChartData] = Field(None, description="Chart data (for chart type)")


class DocumentSection(BaseModel):
    """Section definition for the document."""

    title: str = Field(..., description="Section title")
    level: int = Field(
        2, description="Heading level: 2 for section, 3 for subsection, 4 for minor"
    )
    content: list[SectionContent] = Field(
        default_factory=list, description="Section content items"
    )


class DocumentRequest(BaseModel):
    """Request model for document generation."""

    title: str = Field(..., description="Document title (will be ALL CAPS)")
    subtitle: Optional[str] = Field(None, description="Document subtitle (italic)")
    author: Optional[str] = Field(None, description="Author name")
    date: Optional[str] = Field(None, description="Document date")
    include_toc: bool = Field(True, description="Include Table of Contents")
    sections: list[DocumentSection] = Field(
        default_factory=list, description="Document sections"
    )
    logo_base64: Optional[str] = Field(
        None, description="Base64 encoded logo image for footer"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Rhode Island Market Analysis",
                    "subtitle": "3-Year Market Share Trends",
                    "author": "Roger Entner, Analyst & Founder",
                    "date": "January 2026",
                    "include_toc": True,
                    "sections": [
                        {
                            "title": "1. Executive Summary",
                            "level": 2,
                            "content": [
                                {
                                    "type": "paragraph",
                                    "text": "T-Mobile has executed a dramatic takeover of Rhode Island wireless.",
                                }
                            ],
                        },
                        {
                            "title": "2. Market Share",
                            "level": 2,
                            "content": [
                                {
                                    "type": "subsection",
                                    "text": "2.1 Wireless Market",
                                },
                                {
                                    "type": "table",
                                    "table": {
                                        "caption": "Rhode Island Wireless Market Share Trend",
                                        "headers": [
                                            "Provider",
                                            "2023",
                                            "2024",
                                            "2025",
                                            "Change",
                                        ],
                                        "rows": [
                                            [
                                                "T-Mobile",
                                                "24.8%",
                                                "29.3%",
                                                "32.4%",
                                                "+7.6pp",
                                            ],
                                            [
                                                "Verizon",
                                                "42.4%",
                                                "36.2%",
                                                "27.3%",
                                                "-15.1pp",
                                            ],
                                        ],
                                        "numeric_columns": [1, 2, 3, 4],
                                        "highlights": [
                                            {"row": 0, "col": 4, "type": "positive"},
                                            {"row": 1, "col": 4, "type": "negative"},
                                        ],
                                    },
                                },
                            ],
                        },
                    ],
                }
            ]
        }
    }


class DocumentResponse(BaseModel):
    """Response model for document generation."""

    success: bool = Field(..., description="Whether generation was successful")
    filename: str = Field(..., description="Generated filename")
    download_url: Optional[str] = Field(None, description="URL to download the document")
    file_base64: Optional[str] = Field(
        None, description="Base64 encoded document (if return_base64 is true)"
    )
    error: Optional[str] = Field(None, description="Error message if generation failed")


class MarkdownRequest(BaseModel):
    """Request model for markdown-to-document conversion."""

    markdown: str = Field(..., description="Markdown content to convert")
    title: Optional[str] = Field(None, description="Override document title")
    author: Optional[str] = Field(None, description="Author name")
    date: Optional[str] = Field(None, description="Document date")
    include_toc: bool = Field(True, description="Include Table of Contents")
    logo_base64: Optional[str] = Field(
        None, description="Base64 encoded logo image for footer"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "markdown": """# Market Analysis Report

## Executive Summary

T-Mobile has executed a dramatic takeover of Rhode Island wireless.

## Market Share

### Wireless Market

| Provider | 2023 | 2024 | 2025 | Change |
|----------|------|------|------|--------|
| T-Mobile | 24.8% | 29.3% | 32.4% | +7.6pp |
| Verizon | 42.4% | 36.2% | 27.3% | -15.1pp |

## Methodology

Data source: Recon Analytics Consumer Telecom Survey.
""",
                    "author": "Roger Entner",
                    "date": "January 2026",
                    "include_toc": True,
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
