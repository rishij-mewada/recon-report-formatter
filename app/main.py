"""
FastAPI server for Recon Analytics document generation.

Provides HTTP endpoints for n8n and other webhook integrations.
"""

import base64
import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    DocumentRequest,
    DocumentResponse,
    MarkdownRequest,
    HealthResponse,
)
from .generator import generate_document
from .markdown_parser import parse_markdown

# Configuration
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/app/output")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "")  # Optional API key for authentication

# Ensure output directory exists
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

# Create FastAPI app
app = FastAPI(
    title="Recon Analytics Document Generator",
    description="Generate professional Word documents with Recon Analytics branding",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware for web integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_api_key(api_key: str | None) -> bool:
    """Verify API key if configured."""
    if not API_KEY:
        return True
    return api_key == API_KEY


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with service info."""
    return HealthResponse(status="ok", version="1.0.0")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", version="1.0.0")


@app.post("/generate", response_model=DocumentResponse)
async def generate_from_json(
    request: DocumentRequest,
    return_base64: bool = False,
    api_key: str | None = None,
):
    """
    Generate a Recon Analytics document from structured JSON.

    This endpoint accepts a structured document definition and generates
    a professionally formatted Word document.

    - **title**: Document title (will be ALL CAPS)
    - **subtitle**: Optional subtitle (italic)
    - **author**: Optional author name
    - **date**: Optional document date
    - **include_toc**: Whether to include Table of Contents
    - **sections**: List of document sections with content
    - **logo_base64**: Optional base64 logo for footer
    """
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recon_report_{timestamp}_{uuid.uuid4().hex[:6]}.docx"

        # Generate document
        output_path = generate_document(
            request=request,
            output_dir=OUTPUT_DIR,
            filename=filename,
        )

        response = DocumentResponse(
            success=True,
            filename=filename,
            download_url=f"{BASE_URL}/download/{filename}",
        )

        # Optionally include base64 encoded file
        if return_base64:
            with open(output_path, "rb") as f:
                response.file_base64 = base64.b64encode(f.read()).decode("utf-8")

        return response

    except Exception as e:
        return DocumentResponse(
            success=False,
            filename="",
            error=str(e),
        )


@app.post("/generate-from-markdown", response_model=DocumentResponse)
async def generate_from_markdown(
    request: MarkdownRequest,
    return_base64: bool = False,
    api_key: str | None = None,
):
    """
    Generate a Recon Analytics document from Markdown content.

    This endpoint parses markdown content and converts it to a
    professionally formatted Word document.

    Supported markdown features:
    - # H1 (document title)
    - ## H2 (sections)
    - ### H3 (subsections)
    - #### H4 (minor headings)
    - Paragraphs
    - Markdown tables (with auto-detection of numeric columns)
    """
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        # Parse markdown to document request
        doc_request = parse_markdown(
            markdown=request.markdown,
            title_override=request.title,
            author=request.author,
            date=request.date,
            include_toc=request.include_toc,
        )

        # Add logo if provided
        doc_request.logo_base64 = request.logo_base64

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recon_report_{timestamp}_{uuid.uuid4().hex[:6]}.docx"

        # Generate document
        output_path = generate_document(
            request=doc_request,
            output_dir=OUTPUT_DIR,
            filename=filename,
        )

        response = DocumentResponse(
            success=True,
            filename=filename,
            download_url=f"{BASE_URL}/download/{filename}",
        )

        # Optionally include base64 encoded file
        if return_base64:
            with open(output_path, "rb") as f:
                response.file_base64 = base64.b64encode(f.read()).decode("utf-8")

        return response

    except Exception as e:
        return DocumentResponse(
            success=False,
            filename="",
            error=str(e),
        )


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download a generated document."""
    # Sanitize filename to prevent directory traversal
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(OUTPUT_DIR, safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.delete("/cleanup")
async def cleanup_old_files(max_age_hours: int = 24, api_key: str | None = None):
    """
    Clean up old generated files.

    - **max_age_hours**: Delete files older than this (default: 24 hours)
    """
    if not verify_api_key(api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    import time

    deleted = 0
    now = time.time()
    max_age_seconds = max_age_hours * 3600

    for filename in os.listdir(OUTPUT_DIR):
        file_path = os.path.join(OUTPUT_DIR, filename)
        if os.path.isfile(file_path):
            file_age = now - os.path.getmtime(file_path)
            if file_age > max_age_seconds:
                os.remove(file_path)
                deleted += 1

    return JSONResponse({"deleted": deleted, "max_age_hours": max_age_hours})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
