"""
MCP Server for Recon Analytics Document Generation.

This server exposes tools for generating professional Word documents
with Recon Analytics branding via the Model Context Protocol.
"""

import base64
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from app.models import (
    DocumentRequest,
    DocumentSection,
    SectionContent,
    TableData,
    TableHighlight,
)
from app.generator import generate_document
from app.markdown_parser import parse_markdown

# Configuration
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/app/output")
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# Create MCP server
server = Server("recon-document-generator")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="generate_recon_document",
            description="""Generate a professional Word document with Recon Analytics branding.

Use this tool when you need to create market analysis reports, research documents,
or any document requiring Recon Analytics brand standards including:
- Navy headers and accents
- Gray text (#595959)
- Conditional table highlighting (green for positive, red for negative)
- Page numbers
- Full-width footer with logo and URL

The document will include:
- Title block with optional subtitle, author, and date
- Table of Contents (optional)
- Sections with headings (H2, H3, H4)
- Formatted tables with captions
- Proper Calibri Light typography throughout""",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Document title (will be displayed in ALL CAPS)",
                    },
                    "subtitle": {
                        "type": "string",
                        "description": "Optional subtitle displayed in italics",
                    },
                    "author": {
                        "type": "string",
                        "description": "Author name (prefixed with 'By:')",
                    },
                    "date": {
                        "type": "string",
                        "description": "Document date (e.g., 'January 2026')",
                    },
                    "include_toc": {
                        "type": "boolean",
                        "description": "Include Table of Contents (default: true)",
                        "default": True,
                    },
                    "sections": {
                        "type": "array",
                        "description": "Document sections",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Section title",
                                },
                                "level": {
                                    "type": "integer",
                                    "description": "Heading level: 2=section, 3=subsection, 4=minor",
                                    "default": 2,
                                },
                                "content": {
                                    "type": "array",
                                    "description": "Section content items",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "type": {
                                                "type": "string",
                                                "enum": [
                                                    "paragraph",
                                                    "table",
                                                    "subsection",
                                                    "minor_heading",
                                                ],
                                                "description": "Content type",
                                            },
                                            "text": {
                                                "type": "string",
                                                "description": "Text for paragraph/heading",
                                            },
                                            "italic": {
                                                "type": "boolean",
                                                "description": "Italic text (for paragraph)",
                                            },
                                            "bold": {
                                                "type": "boolean",
                                                "description": "Bold text (for paragraph)",
                                            },
                                            "table": {
                                                "type": "object",
                                                "description": "Table definition",
                                                "properties": {
                                                    "caption": {
                                                        "type": "string",
                                                        "description": "Table caption",
                                                    },
                                                    "headers": {
                                                        "type": "array",
                                                        "items": {"type": "string"},
                                                        "description": "Column headers",
                                                    },
                                                    "rows": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "array",
                                                            "items": {"type": "string"},
                                                        },
                                                        "description": "Table data rows",
                                                    },
                                                    "numeric_columns": {
                                                        "type": "array",
                                                        "items": {"type": "integer"},
                                                        "description": "Column indices to right-align",
                                                    },
                                                    "highlights": {
                                                        "type": "array",
                                                        "items": {
                                                            "type": "object",
                                                            "properties": {
                                                                "row": {
                                                                    "type": "integer"
                                                                },
                                                                "col": {
                                                                    "type": "integer"
                                                                },
                                                                "type": {
                                                                    "type": "string",
                                                                    "enum": [
                                                                        "positive",
                                                                        "negative",
                                                                    ],
                                                                },
                                                            },
                                                        },
                                                        "description": "Cell highlights",
                                                    },
                                                },
                                            },
                                        },
                                    },
                                },
                            },
                            "required": ["title"],
                        },
                    },
                },
                "required": ["title"],
            },
        ),
        Tool(
            name="generate_recon_document_from_markdown",
            description="""Generate a Recon Analytics Word document from Markdown content.

Use this tool when you have markdown-formatted content that needs to be converted
to a professional Word document with Recon Analytics branding.

Supported markdown features:
- # H1 (document title)
- ## H2 (sections with bottom border)
- ### H3 (subsections)
- #### H4 (minor headings)
- Regular paragraphs
- Markdown tables (| Header | Header |)
- Auto-detection of numeric columns for right-alignment
- Auto-detection of positive/negative values for highlighting""",
            inputSchema={
                "type": "object",
                "properties": {
                    "markdown": {
                        "type": "string",
                        "description": "Markdown content to convert",
                    },
                    "title": {
                        "type": "string",
                        "description": "Override document title (optional)",
                    },
                    "author": {
                        "type": "string",
                        "description": "Author name",
                    },
                    "date": {
                        "type": "string",
                        "description": "Document date",
                    },
                    "include_toc": {
                        "type": "boolean",
                        "description": "Include Table of Contents (default: true)",
                        "default": True,
                    },
                },
                "required": ["markdown"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "generate_recon_document":
            return await _generate_from_json(arguments)
        elif name == "generate_recon_document_from_markdown":
            return await _generate_from_markdown(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _generate_from_json(arguments: dict) -> list[TextContent]:
    """Generate document from structured JSON."""
    # Convert arguments to DocumentRequest
    sections = []
    for section_data in arguments.get("sections", []):
        content_items = []
        for content_data in section_data.get("content", []):
            content_type = content_data.get("type", "paragraph")

            if content_type == "table" and "table" in content_data:
                table_data = content_data["table"]
                highlights = None
                if "highlights" in table_data:
                    highlights = [
                        TableHighlight(
                            row=h["row"], col=h["col"], type=h["type"]
                        )
                        for h in table_data["highlights"]
                    ]

                table = TableData(
                    caption=table_data.get("caption"),
                    headers=table_data.get("headers", []),
                    rows=table_data.get("rows", []),
                    numeric_columns=table_data.get("numeric_columns"),
                    highlights=highlights,
                )
                content_items.append(SectionContent(type="table", table=table))
            else:
                content_items.append(
                    SectionContent(
                        type=content_type,
                        text=content_data.get("text"),
                        italic=content_data.get("italic", False),
                        bold=content_data.get("bold", False),
                    )
                )

        sections.append(
            DocumentSection(
                title=section_data["title"],
                level=section_data.get("level", 2),
                content=content_items,
            )
        )

    request = DocumentRequest(
        title=arguments["title"],
        subtitle=arguments.get("subtitle"),
        author=arguments.get("author"),
        date=arguments.get("date"),
        include_toc=arguments.get("include_toc", True),
        sections=sections,
    )

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recon_report_{timestamp}_{uuid.uuid4().hex[:6]}.docx"

    # Generate document
    output_path = generate_document(
        request=request,
        output_dir=OUTPUT_DIR,
        filename=filename,
    )

    # Read and encode the file
    with open(output_path, "rb") as f:
        file_base64 = base64.b64encode(f.read()).decode("utf-8")

    result = {
        "success": True,
        "filename": filename,
        "path": output_path,
        "file_base64": file_base64,
        "message": f"Document generated successfully: {filename}",
    }

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def _generate_from_markdown(arguments: dict) -> list[TextContent]:
    """Generate document from markdown."""
    # Parse markdown to document request
    doc_request = parse_markdown(
        markdown=arguments["markdown"],
        title_override=arguments.get("title"),
        author=arguments.get("author"),
        date=arguments.get("date"),
        include_toc=arguments.get("include_toc", True),
    )

    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recon_report_{timestamp}_{uuid.uuid4().hex[:6]}.docx"

    # Generate document
    output_path = generate_document(
        request=doc_request,
        output_dir=OUTPUT_DIR,
        filename=filename,
    )

    # Read and encode the file
    with open(output_path, "rb") as f:
        file_base64 = base64.b64encode(f.read()).decode("utf-8")

    result = {
        "success": True,
        "filename": filename,
        "path": output_path,
        "file_base64": file_base64,
        "message": f"Document generated successfully: {filename}",
    }

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
