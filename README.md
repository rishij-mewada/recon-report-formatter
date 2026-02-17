# Recon Report Formatter

A Docker-based service for generating professional Word documents with Recon Analytics branding. Supports both HTTP API (for n8n workflows) and MCP server (for Claude integration).

## Features

- **Professional Formatting**: Navy headers, gray text, conditional highlighting
- **HTTP API**: RESTful endpoints for n8n and webhook integrations
- **MCP Server**: Claude MCP tool for AI-assisted document generation
- **Markdown Support**: Convert markdown to branded documents
- **Auto Table of Contents**: Automatically generated and linked
- **Conditional Highlighting**: Green for positive values, red for negative

## Quick Start

### 1. Clone and Configure

```bash
git clone <repository-url>
cd recon-report-formatter

# Copy and edit environment variables
cp .env.example .env
# Edit .env to set your VPS URL and optional API key
```

### 2. Build and Run with Docker

```bash
# Build and start the HTTP API server
docker-compose up -d

# View logs
docker-compose logs -f recon-api
```

The API will be available at `http://your-vps-ip:8000`.

### 3. Test the Service

```bash
# Health check
curl http://localhost:8000/health

# View API documentation
# Open http://localhost:8000/docs in your browser
```

## API Endpoints

### POST /generate

Generate a document from structured JSON.

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Rhode Island Market Analysis",
    "subtitle": "3-Year Market Share Trends",
    "author": "Roger Entner, Analyst & Founder",
    "date": "January 2026",
    "include_toc": true,
    "sections": [
      {
        "title": "1. Executive Summary",
        "level": 2,
        "content": [
          {
            "type": "paragraph",
            "text": "T-Mobile has executed a dramatic takeover of Rhode Island wireless."
          }
        ]
      },
      {
        "title": "2. Market Share",
        "level": 2,
        "content": [
          {
            "type": "subsection",
            "text": "2.1 Wireless Market"
          },
          {
            "type": "table",
            "table": {
              "caption": "Rhode Island Wireless Market Share Trend",
              "headers": ["Provider", "2023", "2024", "2025", "Change"],
              "rows": [
                ["T-Mobile", "24.8%", "29.3%", "32.4%", "+7.6pp"],
                ["Verizon", "42.4%", "36.2%", "27.3%", "-15.1pp"]
              ],
              "numeric_columns": [1, 2, 3, 4],
              "highlights": [
                {"row": 0, "col": 4, "type": "positive"},
                {"row": 1, "col": 4, "type": "negative"}
              ]
            }
          }
        ]
      }
    ]
  }'
```

### POST /generate-from-markdown

Generate a document from markdown content.

```bash
curl -X POST http://localhost:8000/generate-from-markdown \
  -H "Content-Type: application/json" \
  -d '{
    "markdown": "# Market Analysis\n\n## Executive Summary\n\nT-Mobile leads the market.\n\n## Data\n\n| Provider | Share |\n|----------|-------|\n| T-Mobile | 32% |\n| Verizon | 27% |",
    "author": "Roger Entner",
    "date": "January 2026"
  }'
```

### GET /download/{filename}

Download a generated document.

```bash
curl -O http://localhost:8000/download/recon_report_20260127_123456.docx
```

### Response Format

```json
{
  "success": true,
  "filename": "recon_report_20260127_123456_abc123.docx",
  "download_url": "http://your-vps-ip:8000/download/recon_report_20260127_123456_abc123.docx",
  "file_base64": null,
  "error": null
}
```

Add `?return_base64=true` to get the file content as base64.

## n8n Integration

### HTTP Request Node Configuration

1. Add an HTTP Request node
2. Configure:
   - **Method**: POST
   - **URL**: `http://your-vps-ip:8000/generate`
   - **Body Content Type**: JSON
   - **JSON Body**: Your document structure

### Example n8n Workflow

```json
{
  "nodes": [
    {
      "name": "Generate Recon Report",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "http://your-vps-ip:8000/generate",
        "bodyContentType": "json",
        "body": "={{ $json.documentData }}"
      }
    }
  ]
}
```

## Claude MCP Integration

### Local MCP Server Setup

1. Install dependencies locally:

```bash
pip install -r requirements.txt
```

2. Add to your Claude MCP configuration (`~/.config/claude/mcp.json`):

```json
{
  "mcpServers": {
    "recon-document": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/path/to/recon-report-formatter"
    }
  }
}
```

3. Or use the HTTP API from Claude with custom tools that call the endpoints.

### MCP Tools

**generate_recon_document**: Generate from structured JSON

```json
{
  "title": "Market Analysis",
  "author": "Analyst Name",
  "date": "January 2026",
  "sections": [...]
}
```

**generate_recon_document_from_markdown**: Generate from markdown

```json
{
  "markdown": "# Title\n\n## Section\n\nContent...",
  "author": "Analyst Name"
}
```

## Document Structure

### JSON Schema

```
{
  title: string,           // Document title (ALL CAPS)
  subtitle?: string,       // Italic subtitle
  author?: string,         // "By: {author}"
  date?: string,           // Document date
  include_toc: boolean,    // Include Table of Contents
  sections: [
    {
      title: string,       // Section heading
      level: 2|3|4,        // H2=section, H3=subsection, H4=minor
      content: [
        { type: "paragraph", text: string, italic?: bool, bold?: bool },
        { type: "subsection", text: string },
        { type: "minor_heading", text: string },
        { type: "table", table: TableData }
      ]
    }
  ],
  logo_base64?: string     // Footer logo (base64 PNG)
}
```

### Table Definition

```json
{
  "caption": "Table description",
  "headers": ["Col1", "Col2", "Col3"],
  "rows": [
    ["Data1", "Data2", "Data3"],
    ["Data4", "Data5", "Data6"]
  ],
  "numeric_columns": [1, 2],
  "highlights": [
    {"row": 0, "col": 2, "type": "positive"},
    {"row": 1, "col": 2, "type": "negative"}
  ]
}
```

## Brand Standards

| Element | Style |
|---------|-------|
| Title | Calibri Light 16pt, ALL CAPS, #595959 |
| Section (H2) | Calibri Light 12pt Bold, gray bottom border |
| Subsection (H3) | Calibri Light 12pt Bold |
| Body Text | Calibri Light 11pt, #595959 |
| Table Header | White on Navy (#203864) |
| Table Data | #595959 with #CCCCCC borders |
| Positive Highlight | Green (#E2EFDA) |
| Negative Highlight | Red (#FCE4D6) |

## VPS Deployment (Hostinger)

### Prerequisites

- Docker and Docker Compose installed
- Port 8000 open in firewall
- Domain or static IP

### Initial Setup

```bash
# SSH to your VPS
ssh user@your-vps-ip

# Clone repository
git clone https://github.com/rishij-mewada/recon-report-formatter /opt/recon-report-formatter
cd /opt/recon-report-formatter

# Configure
cp .env.example .env
nano .env  # Set BASE_URL=http://your-domain:8000

# Start service
docker compose up -d

# Enable auto-start on boot
docker update --restart unless-stopped recon-document-api
```

### Deploying Updates

```bash
# SSH to VPS
ssh user@your-vps-ip
cd /opt/recon-report-formatter

# Pull latest changes
git pull origin main

# Rebuild and restart (--build is required for code changes)
docker compose down
docker compose up -d --build

# Verify deployment
docker compose ps
docker compose logs --tail=20 recon-api
curl http://localhost:8000/health
```

**Important**: Always use `--build` when deploying code changes. A plain `docker compose restart` reuses the old image and won't pick up new code.

### Merging Feature Branches

```bash
git checkout main
git merge <feature-branch>
git push origin main
```

### Nginx Reverse Proxy (Optional)

```nginx
server {
    listen 80;
    server_name docs.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Security

- Set `API_KEY` in `.env` for authentication
- Use HTTPS with Let's Encrypt
- Configure firewall to only allow necessary ports

## File Cleanup

Generated documents are stored in `/app/output`. Clean up old files:

```bash
# Via API (deletes files older than 24 hours)
curl -X DELETE "http://localhost:8000/cleanup?max_age_hours=24"

# Or set up a cron job in the container
```

## Development

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run API server
uvicorn app.main:app --reload --port 8000

# Run MCP server (for testing)
python -m mcp_server.server
```

### Project Structure

```
recon-report-formatter/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI HTTP server
│   ├── models.py            # Pydantic models
│   ├── recon_formatter.py   # Document generation
│   ├── markdown_parser.py   # Markdown conversion
│   └── generator.py         # Generation service
├── mcp_server/
│   ├── __init__.py
│   └── server.py            # MCP server
├── assets/                  # Logo and assets
├── output/                  # Generated documents
├── Dockerfile               # HTTP API image
├── Dockerfile.mcp           # MCP server image
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## License

Proprietary - Recon Analytics
