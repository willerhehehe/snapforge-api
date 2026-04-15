from __future__ import annotations

import hmac

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from snapforge.config import settings
from snapforge.db import get_customer_by_api_key
from snapforge.session import create_session, clear_session

router = APIRouter()

STYLE = """*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}
.card{background:#1e293b;border:1px solid #334155;border-radius:16px;padding:48px;max-width:440px;width:100%;text-align:center}
h1{font-size:24px;font-weight:700;margin-bottom:8px}
p{color:#94a3b8;margin-bottom:24px;font-size:14px}
input{width:100%;padding:12px 16px;background:#0d1117;border:1px solid #334155;border-radius:8px;color:#e2e8f0;font-family:monospace;font-size:14px;margin-bottom:16px}
input:focus{outline:none;border-color:#3b82f6}
button{width:100%;padding:12px;background:#3b82f6;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer}
button:hover{background:#2563eb}
.error{color:#ef4444;font-size:13px;margin-bottom:16px;display:none}
.links{margin-top:24px;font-size:13px}.links a{color:#3b82f6;text-decoration:none;margin:0 8px}.links a:hover{text-decoration:underline}
.success{color:#10b981;font-size:13px;margin-bottom:16px;display:none}
.tabs{display:flex;gap:8px;margin-bottom:24px}.tab{flex:1;padding:8px;border-radius:8px;cursor:pointer;font-size:13px;font-weight:600;border:1px solid #334155;background:transparent;color:#94a3b8}
.tab.active{background:#3b82f620;color:#3b82f6;border-color:#3b82f6}
.panel{display:none}.panel.active{display:block}"""


@router.get("/login", response_class=HTMLResponse)
async def login_page(msg: str = Query(default="")):
    success_msg = ""
    if msg == "logout":
        success_msg = "已成功退出登录"

    return HTMLResponse(f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SnapForge — Login</title>
<style>{STYLE}</style></head><body><div class="card">
<h1>Login</h1>
<p>Enter your API Key or admin key to continue</p>
<div class="success" id="success">{success_msg}</div>
<div class="error" id="error"></div>
<form id="loginForm">
  <input type="text" id="apiKey" placeholder="sf_... or admin key" autocomplete="off" required>
  <button type="submit">Login</button>
</form>
<div class="links">
  <a href="/forgot-key">Forgot API Key?</a>
  <a href="/">Home</a>
  <a href="/docs">API Docs</a>
</div>
</div>
<script>
const success = document.getElementById('success');
if (success.textContent) success.style.display = 'block';
document.getElementById('loginForm').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const key = document.getElementById('apiKey').value.trim();
  const err = document.getElementById('error');
  err.style.display = 'none';
  const res = await fetch('/auth/login', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{api_key: key}})
  }});
  const data = await res.json();
  if (data.ok) {{
    window.location.href = data.redirect;
  }} else {{
    err.textContent = data.error;
    err.style.display = 'block';
  }}
}});
</script></body></html>""")


@router.post("/auth/login")
async def do_login(request: Request):
    body = await request.json()
    key = body.get("api_key", "").strip()

    from fastapi.responses import JSONResponse

    if settings.api_key and hmac.compare_digest(key, settings.api_key):
        resp = JSONResponse({"ok": True, "redirect": "/admin"})
        create_session(resp, key, role="admin")
        return resp

    customer = get_customer_by_api_key(key)
    if not customer:
        return {"ok": False, "error": "Invalid API Key"}

    resp = JSONResponse({"ok": True, "redirect": "/dashboard"})
    create_session(resp, key, role="user")
    return resp


@router.get("/logout")
async def logout():
    response = RedirectResponse("/login?msg=logout", status_code=303)
    clear_session(response)
    return response


@router.get("/forgot-key", response_class=HTMLResponse)
async def forgot_key_page():
    return HTMLResponse(f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SnapForge — Forgot API Key</title>
<style>{STYLE}</style></head><body><div class="card">
<h1>Forgot API Key</h1>
<p>Enter your registered email to receive your API Key</p>
<div class="error" id="error"></div>
<div class="success" id="success"></div>
<form id="forgotForm">
  <input type="email" id="email" placeholder="your@email.com" required>
  <button type="submit">Send API Key</button>
</form>
<div class="links">
  <a href="/login">Back to Login</a>
  <a href="/">Home</a>
</div>
</div>
<script>
document.getElementById('forgotForm').addEventListener('submit', async (e) => {{
  e.preventDefault();
  const email = document.getElementById('email').value.trim();
  const err = document.getElementById('error');
  const suc = document.getElementById('success');
  err.style.display = 'none';
  suc.style.display = 'none';
  const res = await fetch('/auth/forgot-key', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{email}})
  }});
  const data = await res.json();
  if (data.ok) {{
    suc.textContent = data.message;
    suc.style.display = 'block';
  }} else {{
    err.textContent = data.error;
    err.style.display = 'block';
  }}
}});
</script></body></html>""")


@router.post("/auth/forgot-key")
async def do_forgot_key(request: Request):
    body = await request.json()
    email = body.get("email", "").strip().lower()

    from snapforge.db import get_customer_by_email
    customer = get_customer_by_email(email)
    if not customer:
        return {"ok": False, "error": "No account found with this email"}

    from snapforge.services.email import send_api_key_email
    sent = send_api_key_email(email, customer["api_key"])
    if not sent:
        return {"ok": False, "error": "Email service is not configured. Please contact the administrator to recover your API Key."}

    return {"ok": True, "message": "API Key has been sent to your email. Check your inbox (or spam folder)."}
