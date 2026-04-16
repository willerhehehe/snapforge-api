# SnapForge API

**File processing API for developers & AI agents** — screenshots, QR codes, OG images, image processing, and PDF generation.

One backend, two interfaces: **REST API** for your apps, **MCP Server** for AI agents (Claude Code, Cursor, Windsurf, etc.)

[![Live Demo](https://img.shields.io/badge/Live-snapforge--api-blue)](https://snapforge-api-production.up.railway.app)
[![API Docs](https://img.shields.io/badge/API-Docs-green)](https://snapforge-api-production.up.railway.app/docs)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## Why SnapForge?

Most developers cobble together 5+ services for file processing: a screenshot API, a QR generator, an image CDN, a PDF converter... SnapForge replaces all of them with **one API key**.

For AI agent builders, SnapForge is the easiest way to give your agent **visual superpowers** — screenshots, image generation, and document creation — through MCP with zero HTTP complexity.

## MCP Server (for AI Agents)

Give your AI agent 8 file-processing tools in 30 seconds:

```bash
pip install snapforge-api
snapforge-mcp
```

Add to your Claude Code or Cursor config:

```json
{
  "mcpServers": {
    "snapforge": {
      "command": "snapforge-mcp"
    }
  }
}
```

That's it. Your agent can now:

| Tool | What it does |
|------|-------------|
| `take_screenshot` | Capture any webpage as PNG/JPG |
| `html_to_pdf` | Convert HTML to PDF documents |
| `generate_qr_code` | Styled QR codes (square/rounded/circle) |
| `generate_social_image` | OG images for social sharing |
| `resize_image_tool` | Resize with aspect ratio preservation |
| `convert_image_tool` | Convert between PNG/JPG/WebP |
| `compress_image_tool` | Reduce file size |
| `get_image_info_tool` | Extract image metadata |

### Example: Agent Conversation

```
You: Take a screenshot of https://github.com and generate a QR code linking to it

Agent: [calls take_screenshot] → screenshot.png (42KB, 1280x720)
       [calls generate_qr_code] → qr.png (8KB, 400x400, style=square)

Done! Screenshot and QR code saved.
```

## REST API

All endpoints require an `X-API-Key` header. [Get a free key](https://snapforge-api-production.up.railway.app/#pricing) (100 requests/month).

### Screenshot

```bash
curl "https://snapforge-api-production.up.railway.app/api/v1/screenshot?url=https://example.com" \
  -H "X-API-Key: YOUR_KEY" -o screenshot.png
```

### QR Code

```bash
curl "https://snapforge-api-production.up.railway.app/api/v1/qr?data=https://mysite.com&style=rounded&fg_color=%233b82f6" \
  -H "X-API-Key: YOUR_KEY" -o qr.png
```

### OG Image

```bash
curl "https://snapforge-api-production.up.railway.app/api/v1/og-image?title=My+Blog+Post&subtitle=Read+more" \
  -H "X-API-Key: YOUR_KEY" -o og.png
```

### HTML to PDF

```bash
curl -X POST "https://snapforge-api-production.up.railway.app/api/v1/pdf/from-html" \
  -H "X-API-Key: YOUR_KEY" -H "Content-Type: text/html" \
  -d "<h1>Invoice #1234</h1><p>Total: $99.00</p>" -o invoice.pdf
```

### Image Processing

```bash
# Resize
curl -X POST "https://snapforge-api-production.up.railway.app/api/v1/image/resize?width=800" \
  -H "X-API-Key: YOUR_KEY" -F "file=@photo.jpg" -o resized.jpg

# Convert to WebP
curl -X POST "https://snapforge-api-production.up.railway.app/api/v1/image/convert?output_format=webp" \
  -H "X-API-Key: YOUR_KEY" -F "file=@photo.png" -o photo.webp

# Compress
curl -X POST "https://snapforge-api-production.up.railway.app/api/v1/image/compress?quality=60" \
  -H "X-API-Key: YOUR_KEY" -F "file=@large.jpg" -o compressed.jpg
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/screenshot` | Webpage screenshot capture |
| GET | `/api/v1/qr` | QR code generation |
| POST | `/api/v1/qr` | QR code with logo upload |
| GET | `/api/v1/og-image` | Social sharing image |
| POST | `/api/v1/image/resize` | Image resizing |
| POST | `/api/v1/image/convert` | Format conversion |
| POST | `/api/v1/image/compress` | Image compression |
| POST | `/api/v1/image/info` | Image metadata |
| POST | `/api/v1/pdf/from-html` | HTML to PDF |

Full interactive docs: [snapforge-api-production.up.railway.app/docs](https://snapforge-api-production.up.railway.app/docs)

## Pricing

| Plan | Price | Requests/month | Rate Limit |
|------|-------|---------------|------------|
| **Free** | $0 | 100 | 10 req/min |
| **Pro** | $9/mo | 10,000 | 60 req/min |
| **Business** | $49/mo | 100,000 | 300 req/min |

[Get your API key](https://snapforge-api-production.up.railway.app/#pricing)

## Self-Hosting

```bash
git clone https://github.com/willerhehehe/snapforge-api.git
cd snapforge-api
pip install -e ".[dev]"
playwright install chromium

# Configure
cp .env.example .env
# Edit .env with your settings

# Run
uvicorn snapforge.main:app --reload
```

## Tech Stack

- **FastAPI** — async web framework
- **Playwright** — headless Chromium for screenshots & PDF
- **Pillow** — image processing
- **MCP** — Model Context Protocol for AI agent integration
- **SQLite** — zero-config database with WAL mode
- **Paddle** — payment processing

## Links

- [Live API](https://snapforge-api-production.up.railway.app)
- [API Documentation](https://snapforge-api-production.up.railway.app/docs)
- [MCP Server Setup](#mcp-server-for-ai-agents)
- [Get API Key](https://snapforge-api-production.up.railway.app/#pricing)
