from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from snapforge.db import get_customer_by_api_key, regenerate_api_key
from snapforge.session import get_session

router = APIRouter()


@router.get("/dashboard")
async def dashboard(request: Request) -> HTMLResponse:
    session = get_session(request)
    if not session:
        return RedirectResponse("/login", status_code=303)

    customer = get_customer_by_api_key(session["key"])
    if not customer:
        return RedirectResponse("/login", status_code=303)

    tier = customer["tier"].upper()
    used = customer["requests_used"]
    limit = customer["requests_limit"]
    pct = round(used / limit * 100, 1) if limit > 0 else 0
    bar_color = "#10b981" if pct < 80 else "#f59e0b" if pct < 100 else "#ef4444"
    api_key = customer["api_key"]
    email = customer["email"]

    return HTMLResponse(f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SnapForge — Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;padding:24px}}
.container{{max-width:600px;margin:0 auto}}
h1{{font-size:24px;font-weight:700;margin-bottom:24px}}
.card{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:24px;margin-bottom:16px}}
.card h3{{font-size:14px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px}}
.stat{{font-size:32px;font-weight:800;margin-bottom:4px}}
.sub{{font-size:14px;color:#94a3b8}}
.bar-bg{{background:#334155;border-radius:6px;height:12px;margin-top:12px;overflow:hidden}}
.bar-fill{{height:100%;border-radius:6px;transition:width .3s}}
.key{{background:#0d1117;border:1px solid #334155;border-radius:8px;padding:12px;font-family:monospace;font-size:13px;word-break:break-all;color:#3b82f6;position:relative}}
.badge{{display:inline-block;padding:4px 12px;border-radius:12px;font-size:13px;font-weight:600;margin-bottom:8px}}
.badge.free{{background:#33415520;color:#94a3b8}}.badge.pro{{background:#3b82f620;color:#3b82f6}}.badge.business{{background:#8b5cf620;color:#8b5cf6}}
.row{{display:flex;gap:16px}}.row .card{{flex:1}}
a{{color:#3b82f6;text-decoration:none}}a:hover{{text-decoration:underline}}
.nav{{margin-bottom:24px;font-size:14px}}.nav a{{margin-right:16px}}
.btn{{display:inline-block;padding:8px 16px;background:#334155;color:#e2e8f0;border:none;border-radius:8px;font-size:13px;cursor:pointer;margin-top:8px;text-decoration:none}}
.btn:hover{{background:#475569}}
.btn-primary{{background:#3b82f6;color:#fff}}.btn-primary:hover{{background:#2563eb}}
.toast{{position:fixed;bottom:24px;right:24px;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:12px 24px;font-size:14px;display:none;z-index:100}}
</style></head><body><div class="container">
<div class="nav"><a href="/">Home</a><a href="/docs">API Docs</a><a href="/logout">Logout</a></div>
<h1>Dashboard</h1>
<div class="row">
  <div class="card">
    <h3>Plan</h3>
    <div class="badge {tier.lower()}">{tier}</div>
    <div class="sub">{email}</div>
    {"<div style='margin-top:12px'><a href='/#pricing' class='btn btn-primary'>Upgrade Plan</a></div>" if tier == "FREE" else ""}
  </div>
  <div class="card">
    <h3>Usage This Month</h3>
    <div class="stat">{used:,} <span style="font-size:16px;font-weight:400;color:#94a3b8">/ {limit:,}</span></div>
    <div class="sub">{pct}% used</div>
    <div class="bar-bg"><div class="bar-fill" style="width:{min(pct, 100)}%;background:{bar_color}"></div></div>
  </div>
</div>
<div class="card">
  <h3>API Key</h3>
  <div class="key" id="keyDisplay">{api_key}</div>
  <div style="margin-top:12px;display:flex;gap:8px">
    <button class="btn" onclick="copyKey()">Copy</button>
    <button class="btn" onclick="regenKey()" style="color:#f59e0b">Regenerate Key</button>
  </div>
  <div class="sub" style="margin-top:8px">Include as <code style="background:#0d1117;padding:2px 6px;border-radius:3px">X-API-Key</code> header in every request</div>
</div>
<div class="card">
  <h3>Quick Test</h3>
  <div style="background:#0d1117;border-radius:8px;padding:12px;font-family:monospace;font-size:12px;overflow-x:auto;color:#c9d1d9">
    curl "https://snapforge-api-production.up.railway.app/api/v1/qr?data=hello" \\<br>
    &nbsp;&nbsp;-H "X-API-Key: {api_key}" -o qr.png
  </div>
</div>
{"<div class='card'><h3>Upgrade</h3><p class='sub'>Need more requests? <a href='/#pricing'>View plans</a></p></div>" if tier == "FREE" else ""}
<div class="toast" id="toast"></div>
</div>
<script>
function toast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 3000);
}}
function copyKey() {{
  navigator.clipboard.writeText(document.getElementById('keyDisplay').textContent);
  toast('API Key copied!');
}}
async function regenKey() {{
  if (!confirm('Regenerate your API Key? The old key will stop working immediately.')) return;
  const res = await fetch('/dashboard/regen-key', {{method: 'POST'}});
  const data = await res.json();
  if (data.ok) {{
    document.getElementById('keyDisplay').textContent = data.api_key;
    toast('New API Key generated!');
  }} else {{
    toast('Error: ' + data.error);
  }}
}}
</script></body></html>""")


@router.post("/dashboard/regen-key")
async def dashboard_regen_key(request: Request):
    session = get_session(request)
    if not session:
        return JSONResponse({"ok": False, "error": "Not logged in"}, status_code=401)

    customer = get_customer_by_api_key(session["key"])
    if not customer:
        return JSONResponse({"ok": False, "error": "Invalid session"}, status_code=401)

    new_key = regenerate_api_key(customer["id"])

    from snapforge.session import create_session
    resp = JSONResponse({"ok": True, "api_key": new_key})
    create_session(resp, new_key, role="user")
    return resp
