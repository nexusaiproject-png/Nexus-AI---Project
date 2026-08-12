import json
import urllib.error

import pytest

from app import email_service


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_production_requires_email_configuration(monkeypatch):
    monkeypatch.setenv("NEXUS_ENV", "production")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("EMAIL_FROM", raising=False)

    with pytest.raises(email_service.EmailDeliveryError, match="not configured"):
        email_service.send_email("user@example.com", "Test", "<p>Test</p>")


def test_send_email_posts_expected_resend_payload(monkeypatch):
    monkeypatch.setenv("NEXUS_ENV", "production")
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    monkeypatch.setenv("EMAIL_FROM", "Nexus AI <onboarding@resend.dev>")

    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(request.headers)
        captured["payload"] = json.loads(request.data.decode())
        return FakeResponse()

    monkeypatch.setattr(email_service.urllib.request, "urlopen", fake_urlopen)

    email_service.send_email("user@example.com", "Hello", "<p>Welcome</p>")

    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["timeout"] == 10
    assert captured["headers"]["Authorization"] == "Bearer re_test_key"
    assert captured["payload"] == {
        "from": "Nexus AI <onboarding@resend.dev>",
        "to": ["user@example.com"],
        "subject": "Hello",
        "html": "<p>Welcome</p>",
    }


def test_verification_email_uses_public_url(monkeypatch):
    monkeypatch.setenv("NEXUS_PUBLIC_URL", "https://nexus.example.com/")
    captured = {}

    def fake_send(to, subject, html):
        captured.update(to=to, subject=subject, html=html)

    monkeypatch.setattr(email_service, "send_email", fake_send)
    email_service.send_verification_email("user@example.com", "User", "token-123")

    assert captured["to"] == "user@example.com"
    assert captured["subject"] == "Verify your Nexus AI account"
    assert "https://nexus.example.com/verify-email?token=token-123" in captured["html"]


def test_provider_http_and_network_errors_are_wrapped(monkeypatch):
    monkeypatch.setenv("NEXUS_ENV", "production")
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key")
    monkeypatch.setenv("EMAIL_FROM", "Nexus AI <onboarding@resend.dev>")

    def http_error(*_args, **_kwargs):
        raise urllib.error.HTTPError("https://api.resend.com/emails", 403, "forbidden", {}, None)

    monkeypatch.setattr(email_service.urllib.request, "urlopen", http_error)
    with pytest.raises(email_service.EmailDeliveryError, match="HTTP 403"):
        email_service.send_email("user@example.com", "Test", "<p>Test</p>")

    def network_error(*_args, **_kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(email_service.urllib.request, "urlopen", network_error)
    with pytest.raises(email_service.EmailDeliveryError, match="unreachable"):
        email_service.send_email("user@example.com", "Test", "<p>Test</p>")
