# Development Guide

## Architecture Overview

The Recon Report Formatter converts markdown or structured JSON into branded Word documents (.docx) using python-docx. It runs as a FastAPI service inside Docker on a Hostinger VPS.

### Data Flow

```
Markdown/JSON input
  -> FastAPI endpoint (main.py)
    -> markdown_parser.py (if markdown input)
    -> generator.py (orchestrator)
      -> recon_formatter.py (python-docx formatting)
        -> .docx file
```

### Key Design Decisions

- **Inline formatting preserved through pipeline**: The markdown parser preserves `**bold**` and `*italic*` markers in text. The formatter's `_add_formatted_runs()` method parses these into separate Word runs with proper formatting.
- **Section-aware rendering**: Tables in "First-Time Disclosures" and "Strategic Shifts" sections render as prose paragraphs. Tables in "Guidance Changes", "Consumer Trends", "Financial Performance", and "Market Share" sections get conditional highlighting.
- **Caption auto-numbering**: Tables, figures, and charts are auto-numbered sequentially via `_caption_counters`.

## Project Structure

```
recon-report-formatter/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI HTTP server & endpoints
│   ├── models.py            # Pydantic data models
│   ├── recon_formatter.py   # Word document formatting (python-docx)
│   ├── markdown_parser.py   # Markdown -> DocumentRequest conversion
│   └── generator.py         # Orchestrates document generation
├── mcp_server/
│   ├── __init__.py
│   └── server.py            # MCP server for Claude integration
├── assets/                  # Logo and static assets
├── output/                  # Generated documents
├── Dockerfile               # HTTP API image
├── Dockerfile.mcp           # MCP server image
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run API server with hot reload
uvicorn app.main:app --reload --port 8000

# Run MCP server (for testing)
python -m mcp_server.server
```

## Inline Formatting Pipeline

### How it works

1. **markdown_parser.py** receives raw markdown text
2. For full-line bold/italic (`**entire line**` or `*entire line*`), it sets `bold=True`/`italic=True` flags on the `SectionContent`
3. For inline markers within a paragraph (e.g., `reported **685,000 customers**`), it preserves the `**` and `*` markers in the text
4. **generator.py** passes text and flags to `recon_formatter.py`
5. **recon_formatter.py** `_add_formatted_runs()` splits text on marker boundaries using regex, creating separate Word runs with appropriate `font.bold`/`font.italic` properties

### Critical: Do NOT strip markers in the parser

```python
# WRONG - was removed in v1.1.0
text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # Strips markers
text = re.sub(r"\*(.+?)\*", r"\1", text)       # Strips markers

# CORRECT - markers preserved for formatter
# (no stripping code - markers pass through to _add_formatted_runs)
```

### Regex tokenizer in _add_formatted_runs()

```python
tokens = re.split(r"(\*\*[^*]+?\*\*|\*[^*]+?\*)", text)
```

This splits text into segments:
- `**bold text**` -> bold run (markers stripped, `font.bold = True`)
- `*italic text*` -> italic run (markers stripped, `font.italic = True`)
- Everything else -> plain run

Used in both `add_paragraph()` and `add_table()` cell rendering.

## Deployment Checklist

```bash
# On VPS
cd /opt/recon-report-formatter
git pull origin main
docker compose down
docker compose up -d --build
docker compose ps                          # should show "healthy"
docker compose logs --tail=20 recon-api    # should show uvicorn started
curl http://localhost:8000/health           # should return {"status":"healthy"}
```

Always use `--build` when deploying code changes.

## Version History

| Version | Date     | Changes |
|---------|----------|---------|
| v1.0.0  | Jan 2026 | Initial deployment |
| v1.1.0  | Feb 2026 | Fixed inline markdown formatting: removed marker stripping in parser, added `_add_formatted_runs()` method, applied formatting to table cells |
