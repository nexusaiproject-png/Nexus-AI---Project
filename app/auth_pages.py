from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["auth-pages"])


@router.get("/verify-email", response_class=HTMLResponse, include_in_schema=False)
def verify_email_page(token: str = Query(default="")) -> HTMLResponse:
    safe = token.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
    return HTMLResponse(f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Verify Nexus AI</title></head><body style='font-family:system-ui;max-width:520px;margin:60px auto;padding:24px'><h1>Verify your Nexus AI account</h1><p>Click the button to verify your email address.</p><button id='verify'>Verify email</button><p id='status'></p><script>const token={safe!r};document.getElementById('verify').onclick=async()=>{{const r=await fetch('/auth/verify-email',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{token}})}});const d=await r.json();document.getElementById('status').textContent=r.ok?'Email verified. You can now sign in.':(d.detail||'Verification failed.');}};</script></body></html>""")


@router.get("/reset-password", response_class=HTMLResponse, include_in_schema=False)
def reset_password_page(token: str = Query(default="")) -> HTMLResponse:
    safe = token.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
    return HTMLResponse(f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Reset Nexus AI password</title></head><body style='font-family:system-ui;max-width:520px;margin:60px auto;padding:24px'><h1>Reset your password</h1><input id='password' type='password' placeholder='New password' minlength='8' style='display:block;padding:10px;width:100%;margin:12px 0'><button id='reset'>Reset password</button><p id='status'></p><script>const token={safe!r};document.getElementById('reset').onclick=async()=>{{const password=document.getElementById('password').value;const r=await fetch('/auth/password-reset/confirm',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{token,password}})}});const d=await r.json();document.getElementById('status').textContent=r.ok?'Password reset successfully.':(d.detail||'Reset failed.');}};</script></body></html>""")
