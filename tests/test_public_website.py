from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


def test_public_pages_exist():
    for name in ["index.html", "login.html", "signup.html", "verify.html", "reset.html", "onboarding.html", "privacy.html", "terms.html", "contact.html", "styles.css"]:
        assert (WEB / name).is_file()


def test_landing_contains_required_sections():
    html = (WEB / "index.html").read_text()
    for text in ["Features", "Pricing", "FAQ", "Log in", "Get started"]:
        assert text in html
    for href in ["/web/privacy.html", "/web/terms.html", "/web/contact.html"]:
        assert href in html


def test_auth_pages_connect_to_api():
    for name in ["login.html", "signup.html", "verify.html", "reset.html", "onboarding.html"]:
        html = (WEB / name).read_text()
        assert "/auth/" in html


def test_auth_forms_have_required_fields():
    login = (WEB / "login.html").read_text()
    signup = (WEB / "signup.html").read_text()
    assert 'type="email"' in login and 'type="password"' in login
    assert 'name="name"' in signup and 'type="email"' in signup
    assert 'minlength="8"' in signup
