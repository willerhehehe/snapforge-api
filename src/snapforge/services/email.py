from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from snapforge.config import settings


def send_api_key_email(to_email: str, api_key: str) -> bool:
    if not settings.smtp_user or not settings.smtp_password:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your SnapForge API Key"
    msg["From"] = f"SnapForge <{settings.smtp_user}>"
    msg["To"] = to_email

    html = f"""\
<html><body style="font-family:-apple-system,sans-serif;background:#0f172a;padding:40px">
<div style="max-width:500px;margin:0 auto;background:#1e293b;border:1px solid #334155;border-radius:16px;padding:40px;color:#e2e8f0">
<h2 style="margin:0 0 8px;font-size:20px">Your SnapForge API Key</h2>
<p style="color:#94a3b8;margin:0 0 24px;font-size:14px">Here is your API key. Keep it safe!</p>
<div style="background:#0d1117;border:1px solid #334155;border-radius:8px;padding:16px;font-family:monospace;font-size:14px;word-break:break-all;color:#3b82f6">{api_key}</div>
<p style="color:#94a3b8;font-size:13px;margin:24px 0 0">Include this as <code style="background:#0d1117;padding:2px 6px;border-radius:3px">X-API-Key</code> header in every request.</p>
<p style="color:#94a3b8;font-size:13px;margin:16px 0 0">Login at your dashboard: <a href="{settings.base_url or 'https://snapforge-api-production.up.railway.app'}/login" style="color:#3b82f6">SnapForge Login</a></p>
</div></body></html>"""

    msg.attach(MIMEText(f"Your SnapForge API Key: {api_key}", "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, to_email, msg.as_string())
        return True
    except Exception:
        return False
