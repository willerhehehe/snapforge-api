from __future__ import annotations

from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from snapforge.session import get_session
from snapforge.db import (
    get_all_customers, set_customer_tier, reset_usage,
    regenerate_api_key, delete_customer,
)

router = APIRouter()


def _require_admin(request: Request):
    session = get_session(request)
    if not session or session.get("role") != "admin":
        return None
    return session


@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    if not _require_admin(request):
        return RedirectResponse("/login", status_code=303)

    customers = get_all_customers()
    rows = ""
    for c in customers:
        pct = round(c["requests_used"] / c["requests_limit"] * 100, 1) if c["requests_limit"] > 0 else 0
        bar_color = "#10b981" if pct < 80 else "#f59e0b" if pct < 100 else "#ef4444"
        tier_colors = {"free": "#94a3b8", "pro": "#3b82f6", "business": "#8b5cf6"}
        tier_color = tier_colors.get(c["tier"], "#94a3b8")
        cid = int(c['id'])
        email_esc = escape(c['email'])
        tier_esc = escape(c['tier'].upper())
        key_esc = escape(c['api_key'])
        rows += f"""<tr>
<td>{cid}</td>
<td>{email_esc}</td>
<td><span style="color:{tier_color};font-weight:600">{tier_esc}</span></td>
<td>
  <div style="display:flex;align-items:center;gap:8px">
    <span>{c['requests_used']:,}/{c['requests_limit']:,}</span>
    <div style="flex:1;background:#334155;border-radius:4px;height:6px;min-width:60px;overflow:hidden">
      <div style="width:{min(pct,100)}%;height:100%;background:{bar_color};border-radius:4px"></div>
    </div>
  </div>
</td>
<td style="font-family:monospace;font-size:11px;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="{key_esc}">{key_esc}</td>
<td>{escape(c['created_at'][:10])}</td>
<td>
  <select onchange="setTier({cid},this.value)" style="background:#0d1117;color:#e2e8f0;border:1px solid #334155;border-radius:4px;padding:2px 4px;font-size:12px">
    <option value="free" {"selected" if c["tier"]=="free" else ""}>Free</option>
    <option value="pro" {"selected" if c["tier"]=="pro" else ""}>Pro</option>
    <option value="business" {"selected" if c["tier"]=="business" else ""}>Business</option>
  </select>
  <button onclick="resetUsage({cid})" class="btn-sm" title="Reset usage">↻</button>
  <button onclick="regenKey({cid})" class="btn-sm" title="Regenerate key">🔑</button>
  <button onclick="deleteUser({cid})" class="btn-sm btn-danger" title="Delete">✕</button>
</td></tr>"""

    return HTMLResponse(f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SnapForge — Admin</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;padding:24px}}
.container{{max-width:1100px;margin:0 auto}}
h1{{font-size:24px;font-weight:700;margin-bottom:4px}}
.sub{{color:#94a3b8;font-size:14px;margin-bottom:24px}}
.nav{{margin-bottom:24px;font-size:14px}}.nav a{{color:#3b82f6;text-decoration:none;margin-right:16px}}.nav a:hover{{text-decoration:underline}}
.stats{{display:flex;gap:16px;margin-bottom:24px}}
.stat-card{{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px;flex:1;text-align:center}}
.stat-num{{font-size:28px;font-weight:800}}.stat-label{{font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-top:4px}}
table{{width:100%;background:#1e293b;border:1px solid #334155;border-radius:12px;border-collapse:collapse;overflow:hidden}}
th{{background:#0d1117;padding:12px 16px;text-align:left;font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px}}
td{{padding:10px 16px;border-top:1px solid #334155;font-size:13px}}
tr:hover{{background:#334155}}
.btn-sm{{background:#334155;color:#e2e8f0;border:none;border-radius:4px;padding:3px 8px;cursor:pointer;font-size:12px;margin-left:4px}}
.btn-sm:hover{{background:#475569}}
.btn-danger{{color:#ef4444}}.btn-danger:hover{{background:#ef444420}}
.toast{{position:fixed;bottom:24px;right:24px;background:#1e293b;border:1px solid #334155;border-radius:8px;padding:12px 24px;font-size:14px;display:none;z-index:100}}
</style></head><body><div class="container">
<div class="nav"><a href="/">Home</a><a href="/docs">API Docs</a><a href="/logout">Logout</a></div>
<h1>Admin Panel</h1>
<p class="sub">{len(customers)} registered users</p>
<div class="stats">
  <div class="stat-card"><div class="stat-num">{len(customers)}</div><div class="stat-label">Total Users</div></div>
  <div class="stat-card"><div class="stat-num">{sum(1 for c in customers if c['tier']=='free')}</div><div class="stat-label">Free</div></div>
  <div class="stat-card"><div class="stat-num">{sum(1 for c in customers if c['tier']=='pro')}</div><div class="stat-label">Pro</div></div>
  <div class="stat-card"><div class="stat-num">{sum(1 for c in customers if c['tier']=='business')}</div><div class="stat-label">Business</div></div>
  <div class="stat-card"><div class="stat-num">{sum(c['requests_used'] for c in customers):,}</div><div class="stat-label">Total Requests</div></div>
</div>
<table>
<thead><tr><th>#</th><th>Email</th><th>Tier</th><th>Usage</th><th>API Key</th><th>Created</th><th>Actions</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<div class="toast" id="toast"></div>
</div>
<script>
function toast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 3000);
}}
async function api(action, id, extra) {{
  const res = await fetch('/admin/api', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{action, id, ...extra}})
  }});
  const data = await res.json();
  if (data.ok) {{ toast(data.message); setTimeout(() => location.reload(), 500); }}
  else toast('Error: ' + (data.error || 'Unknown'));
}}
function setTier(id, tier) {{ api('set_tier', id, {{tier}}); }}
function resetUsage(id) {{ if(confirm('Reset usage for this user?')) api('reset_usage', id); }}
function regenKey(id) {{ if(confirm('Regenerate API key? The old key will stop working.')) api('regen_key', id); }}
function deleteUser(id) {{ if(confirm('Delete this user? This cannot be undone.')) api('delete', id); }}
</script></body></html>""")


@router.post("/admin/api")
async def admin_api(request: Request):
    if not _require_admin(request):
        return JSONResponse({"ok": False, "error": "Unauthorized"}, status_code=401)

    body = await request.json()
    action = body.get("action")
    cid = body.get("id")

    if not isinstance(cid, int) or cid < 1:
        return {"ok": False, "error": "Invalid customer ID"}

    if action == "set_tier":
        tier = body.get("tier", "free")
        if tier not in ("free", "pro", "business"):
            return {"ok": False, "error": "Invalid tier"}
        set_customer_tier(cid, tier)
        return {"ok": True, "message": f"Tier updated to {tier.upper()}"}

    elif action == "reset_usage":
        reset_usage(cid)
        return {"ok": True, "message": "Usage reset to 0"}

    elif action == "regen_key":
        new_key = regenerate_api_key(cid)
        return {"ok": True, "message": f"New key: {new_key}"}

    elif action == "delete":
        delete_customer(cid)
        return {"ok": True, "message": "User deleted"}

    return {"ok": False, "error": "Unknown action"}
