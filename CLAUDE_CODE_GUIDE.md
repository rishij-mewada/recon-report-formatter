# Guide for Claude Code Sessions

## Project Overview

**Project**: recon-report-formatter
**VPS Location**: `/opt/recon-report-formatter`
**Purpose**: Convert markdown to branded Recon Analytics Word documents
**Stack**: Python 3.12, FastAPI, python-docx, Docker
**Integration**: n8n workflows on same VPS

## Key Files

| File | Purpose | Safe to modify? |
|------|---------|-----------------|
| `app/markdown_parser.py` | Parse markdown structure | Yes |
| `app/recon_formatter.py` | Format Word document | Yes |
| `app/generator.py` | Orchestrate conversion | Yes |
| `app/models.py` | Pydantic data models | Yes |
| `app/main.py` | FastAPI endpoints | Carefully |
| `docker-compose.yml` | Container config | Carefully |
| `Dockerfile` | Build instructions | Carefully |
| `requirements.txt` | Dependencies | Yes |
| `.env` | Secrets (not in git) | Never share |

## You Cannot SSH to the VPS

Claude Code runs locally on the user's Windows machine. You cannot:
- Execute commands on the VPS directly
- Access Docker containers remotely
- Deploy code automatically

**Workflow**:
1. Make code changes locally
2. Commit and push to GitHub
3. Provide deployment commands for the user to run on VPS
4. User pastes output back for analysis

### Deployment Commands Template

```
Your code is ready. To deploy on the VPS:

1. SSH to VPS: `ssh root@<vps-ip>`
2. Navigate: `cd /opt/recon-report-formatter`
3. Pull changes: `git pull origin <branch-name>`
4. Rebuild:
   docker compose down
   docker compose up -d --build
5. Verify:
   docker compose ps
   docker compose logs --tail=20 recon-api
   curl http://localhost:8000/health
```

## Critical Code: Don't Break This

### markdown_parser.py - Inline marker preservation

The parser must NOT strip `**bold**` and `*italic*` markers from paragraph text. They are preserved so the formatter can process them into actual Word formatting.

```python
# This stripping code was intentionally REMOVED. Do not re-add it.
# text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
# text = re.sub(r"\*(.+?)\*", r"\1", text)
```

### recon_formatter.py - _add_formatted_runs()

This method parses inline markers and creates separate Word runs with proper formatting. It is used by both `add_paragraph()` and table cell rendering in `add_table()`.

```python
def _add_formatted_runs(self, para, text, base_bold=False, base_italic=False):
    tokens = re.split(r"(\*\*[^*]+?\*\*|\*[^*]+?\*)", text)
    # **bold** -> run.font.bold = True
    # *italic* -> run.font.italic = True
    # plain text -> default formatting
```

## Git Branch Info

- **main**: Production branch, deployed on VPS
- **claude/docker-text-to-word-kHgEp**: Feature branch with formatting fixes

Feature branches should be merged to main before deploying.

## Common Issues

**"Changes aren't showing after deploy"**
-> User forgot `--build` flag. Must use: `docker compose up -d --build`

**"command not found: docker compose"**
-> Try `docker-compose` (with hyphen) for older Docker versions

**"the attribute `version` is obsolete"**
-> Warning only in docker-compose.yml, safe to ignore

**"Bold/italic markers showing as literal text"**
-> Check that markdown_parser.py is NOT stripping markers (see critical code above)

## Testing

### Quick API test (user runs on VPS)

```bash
curl -X POST http://localhost:8000/generate-from-markdown \
  -H "Content-Type: application/json" \
  -d '{
    "markdown": "# Test\n\n## Section\n\nThis has **bold text** and *italic text* inline.",
    "author": "Test",
    "date": "2026"
  }'
```

### Success Criteria

- `docker compose ps` shows "healthy" status
- `curl http://localhost:8000/health` returns JSON
- Generated Word docs show **bold** without literal `**` characters
- Generated Word docs show *italic* without literal `*` characters
