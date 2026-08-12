from __future__ import annotations

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["auth-pages"])


_STYLE = """
:root{font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#e8ecf7;background:#080b12;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;padding:24px;background:radial-gradient(circle at 80% 0,#17203a 0,#080b12 45%)}
.card{width:min(460px,100%);background:#101622e8;border:1px solid #202a3d;border-radius:20px;padding:28px;box-shadow:0 20px 70px #0007}
h1{margin:0 0 8px;font-size:28px}.sub{margin:0 0 24px;color:#8995aa}.brand{font-weight:800;letter-spacing:.04em;margin-bottom:22px}
label{display:block;font-size:13px;color:#aeb8c9;margin:14px 0 6px}input{width:100%;padding:12px 13px;border:1px solid #2a3449;border-radius:10px;background:#0c111b;color:#fff;outline:none}input:focus{border-color:#5d7cff}
button{width:100%;margin-top:18px;border:0;border-radius:11px;padding:12px;background:#5d7cff;color:#fff;font-weight:700;cursor:pointer}.link{display:block;text-align:center;margin-top:16px;color:#9fb8ff;text-decoration:none}.status{min-height:22px;margin-top:14px;font-size:13px;color:#ff9d9d}.success{color:#8fe0ad}.hidden{display:none}
"""


def _page(title: str, body: str, script: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{title}</title><style>{_STYLE}</style></head><body><main class='card'><div class='brand'>NEXUS AI</div>{body}</main><script>{script}</script></body></html>"""
    )


@router.get("/signup", response_class=HTMLResponse, include_in_schema=False)
def signup_page() -> HTMLResponse:
    body = """
<h1>Create your account</h1><p class='sub'>Start your Nexus AI workspace.</p>
<form id='signup-form'>
<label for='name'>Name</label><input id='name' name='name' autocomplete='name' required>
<label for='email'>Email</label><input id='email' name='email' type='email' autocomplete='email' required>
<label for='password'>Password</label><input id='password' name='password' type='password' minlength='8' autocomplete='new-password' required>
<button>Create account</button><p id='status' class='status' role='status'></p>
</form><a class='link' href='/login'>Already have an account? Sign in</a>
"""
    script = """
const form=document.getElementById('signup-form'),status=document.getElementById('status');
form.onsubmit=async e=>{e.preventDefault();status.className='status';status.textContent='Creating your account…';
const payload={name:document.getElementById('name').value.trim(),email:document.getElementById('email').value.trim(),password:document.getElementById('password').value};
try{const r=await fetch('/auth/signup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const d=await r.json();
if(!r.ok){status.textContent=d.detail||'Sign up failed.';return}status.className='status success';status.textContent='Account created. Check your email to verify your address, then sign in.';form.querySelector('button').disabled=true;}
catch(_){status.textContent='Unable to reach Nexus AI. Please try again.'}};
"""
    return _page("Create account · Nexus AI", body, script)


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login_page() -> HTMLResponse:
    body = """
<h1>Welcome back</h1><p class='sub'>Sign in to your Nexus AI workspace.</p>
<form id='login-form'>
<label for='email'>Email</label><input id='email' name='email' type='email' autocomplete='email' required>
<label for='password'>Password</label><input id='password' name='password' type='password' autocomplete='current-password' required>
<button>Sign in</button><p id='status' class='status' role='status'></p>
</form><a class='link' href='/forgot-password'>Forgot your password?</a><a class='link' href='/signup'>Create an account</a>
"""
    script = """
const form=document.getElementById('login-form'),status=document.getElementById('status');
form.onsubmit=async e=>{e.preventDefault();status.className='status';status.textContent='Signing in…';
const payload={email:document.getElementById('email').value.trim(),password:document.getElementById('password').value};
try{const r=await fetch('/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const d=await r.json();
if(!r.ok){status.textContent=d.detail||'Sign in failed.';return}window.location.href='/ui';}
catch(_){status.textContent='Unable to reach Nexus AI. Please try again.'}};
"""
    return _page("Sign in · Nexus AI", body, script)


@router.get("/forgot-password", response_class=HTMLResponse, include_in_schema=False)
def forgot_password_page() -> HTMLResponse:
    body = """
<h1>Reset your password</h1><p class='sub'>Enter your email and we will send a reset link if the account exists.</p>
<form id='forgot-form'><label for='email'>Email</label><input id='email' type='email' autocomplete='email' required>
<button>Send reset email</button><p id='status' class='status' role='status'></p></form><a class='link' href='/login'>Back to sign in</a>
"""
    script = """
const form=document.getElementById('forgot-form'),status=document.getElementById('status');
form.onsubmit=async e=>{e.preventDefault();status.className='status';status.textContent='Sending…';
try{const r=await fetch('/auth/password-reset/request',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('email').value.trim()})});const d=await r.json();
if(!r.ok){status.textContent=d.detail||'Unable to send reset email.';return}status.className='status success';status.textContent='If that email is registered, a password reset link has been sent.';}
catch(_){status.textContent='Unable to reach Nexus AI. Please try again.'}};
"""
    return _page("Reset password · Nexus AI", body, script)


@router.get("/verify-email", response_class=HTMLResponse, include_in_schema=False)
def verify_email_page(token: str = Query(default="")) -> HTMLResponse:
    safe = token.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
    return _page(
        "Verify email · Nexus AI",
        "<h1>Verify your email</h1><p class='sub'>Confirm your email address to activate your Nexus AI account.</p><button id='verify'>Verify email</button><p id='status' class='status' role='status'></p><a class='link' href='/login'>Back to sign in</a>",
        f"""
const token={safe!r},button=document.getElementById('verify'),status=document.getElementById('status');
button.onclick=async()=>{{button.disabled=true;status.textContent='Verifying…';
try{{const r=await fetch('/auth/verify-email',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{token}})}});const d=await r.json();
if(!r.ok){{status.textContent=d.detail||'Verification failed.';button.disabled=false;return}}status.className='status success';status.textContent='Email verified. You can now sign in.';button.className='hidden';}}
catch(_){{status.textContent='Unable to reach Nexus AI. Please try again.';button.disabled=false;}}}};
""",
    )


@router.get("/reset-password", response_class=HTMLResponse, include_in_schema=False)
def reset_password_page(token: str = Query(default="")) -> HTMLResponse:
    safe = token.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
    return _page(
        "Reset password · Nexus AI",
        "<h1>Choose a new password</h1><p class='sub'>Your new password must be at least 8 characters.</p><form id='reset-form'><label for='password'>New password</label><input id='password' type='password' minlength='8' autocomplete='new-password' required><button>Reset password</button><p id='status' class='status' role='status'></p></form><a class='link' href='/login'>Back to sign in</a>",
        f"""
const token={safe!r},form=document.getElementById('reset-form'),status=document.getElementById('status');
form.onsubmit=async e=>{{e.preventDefault();status.textContent='Resetting…';
try{{const r=await fetch('/auth/password-reset/confirm',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{token,password:document.getElementById('password').value}})}});const d=await r.json();
if(!r.ok){{status.textContent=d.detail||'Reset failed.';return}}status.className='status success';status.textContent='Password reset successfully. You can now sign in.';form.querySelector('button').disabled=true;}}
catch(_){{status.textContent='Unable to reach Nexus AI. Please try again.';}}}};
""",
    )
