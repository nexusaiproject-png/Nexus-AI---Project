from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


class EmailDeliveryError(RuntimeError):
    pass


def _config() -> tuple[str, str, str]:
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    sender = os.getenv("EMAIL_FROM", "").strip()
    public_url = os.getenv("NEXUS_PUBLIC_URL", "https://nexus-ai-bbm7.onrender.com").rstrip("/")
    return api_key, sender, public_url


def send_email(to: str, subject: str, html: str) -> None:
    api_key, sender, _ = _config()
    if not api_key or not sender:
        if os.getenv("NEXUS_ENV", "development") == "production":
            raise EmailDeliveryError("email delivery is not configured")
        return
    payload = json.dumps({"from": sender, "to": [to], "subject": subject, "html": html}).encode()
    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            if response.status < 200 or response.status >= 300:
                raise EmailDeliveryError(f"email provider returned HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        raise EmailDeliveryError(f"email provider returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise EmailDeliveryError("email provider is unreachable") from exc


def send_verification_email(to: str, name: str, token: str) -> None:
    _, _, public_url = _config()
    link = f"{public_url}/verify-email?token={token}"
    send_email(
        to,
        "Verify your Nexus AI account",
        f"<p>Hello {name},</p><p>Verify your Nexus AI account by clicking <a href=\"{link}\">this link</a>.</p>",
    )


def send_password_reset_email(to: str, name: str, token: str) -> None:
    _, _, public_url = _config()
    link = f"{public_url}/reset-password?token={token}"
    send_email(
        to,
        "Reset your Nexus AI password",
        f"<p>Hello {name},</p><p>Reset your password by clicking <a href=\"{link}\">this link</a>. This link expires in one hour.</p>",
    )
