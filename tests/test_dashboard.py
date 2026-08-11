from pathlib import Path

from fastapi.testclient import TestClient

from main import app

ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_page_exists():
    page = ROOT / "web" / "dashboard.html"
    assert page.is_file()
    html = page.read_text()
    for text in ["Home", "AI Chat", "Calendar", "Tasks", "Files", "Meetings", "Automations", "Developer Agent", "Usage", "Billing", "Settings"]:
        assert text in html


def test_dashboard_route_serves_page():
    with TestClient(app) as client:
        response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Nexus AI Workspace" in response.text


def test_dashboard_links_billing_and_settings():
    html = (ROOT / "web" / "dashboard.html").read_text()
    assert "/web/billing.html" in html
    assert "/web/settings.html" in html
    assert "fetch('/usage')" in html
    assert "fetch('/billing/subscription')" in html
