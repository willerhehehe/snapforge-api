# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SnapForge API is a file-processing micro-SaaS built with FastAPI. It provides screenshot capture, QR code generation, OG image creation, image processing, and HTML-to-PDF conversion via a REST API.

## Development Commands

```bash
# Install (with dev tools)
pip install -e ".[dev]"

# Dev server
uvicorn snapforge.main:app --reload

# Production
uvicorn snapforge.main:app --host 0.0.0.0 --port 8080

# Lint
ruff check src/

# Run tests
pytest

# MCP server (for Claude integration)
snapforge-mcp

# Install Playwright browser (required for screenshots/PDF)
playwright install chromium
```

## Architecture

**Entry point**: `src/snapforge/main.py` — `create_app()` builds the FastAPI app. The lifespan handler initializes the database and starts the Playwright browser pool.

**Routing**: All API endpoints live under `/api/v1/`. Routers are in `src/snapforge/routers/`. Non-API routes (billing webhooks, auth, admin, dashboard) mount at the root.

**Services layer** (`src/snapforge/services/`): Business logic separated from routes. `BrowserManager` is a singleton managing a shared Playwright browser instance — accessed via `get_browser_manager()`.

**Database**: Raw SQLite with WAL mode (`src/snapforge/db.py`). No ORM. Two tables: `customers` (users + API keys + quotas) and `subscriptions`. DB file lives at `src/snapforge/data/snapforge.db`.

**Auth**: API endpoints use `X-API-Key` header verified in `src/snapforge/auth.py`. Dashboard/admin use HMAC-SHA256 signed session cookies (`src/snapforge/session.py`). Admin is identified by matching the configured `SNAPFORGE_API_KEY`.

**Billing**: Dual payment provider support (Stripe legacy + Paddle current). Webhook-driven — `billing.py` handles subscription lifecycle events and auto-upgrades tiers. The `stripe_customer_id` column is reused for Paddle customer IDs.

**Tier system**: free (100 req/month), pro (10k), business (100k). Quota enforcement happens atomically in `increment_usage()` via a single UPDATE with WHERE clause.

## Configuration

All env vars are prefixed with `SNAPFORGE_` and managed via pydantic-settings in `src/snapforge/config.py`. See `.env.example` for the template.

## Key Conventions

- Python 3.11+, ruff for linting (line-length 120)
- Async FastAPI handlers, but SQLite calls are synchronous (acceptable for single-file DB)
- Binary responses (images, PDFs) returned as `StreamingResponse` with appropriate content types
- API key format: `sf_` prefix + 48 hex chars
- Templates are server-rendered HTML (no frontend framework), located in `src/snapforge/templates/`
