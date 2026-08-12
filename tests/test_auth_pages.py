from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_signup_page_exposes_account_creation_form() -> None:
    response = client.get("/signup")

    assert response.status_code == 200
    assert "Create your account" in response.text
    assert "fetch('/auth/signup'" in response.text


def test_login_page_exposes_sign_in_form() -> None:
    response = client.get("/login")

    assert response.status_code == 200
    assert "Welcome back" in response.text
    assert "fetch('/auth/login'" in response.text


def test_forgot_password_page_exposes_reset_request_form() -> None:
    response = client.get("/forgot-password")

    assert response.status_code == 200
    assert "Reset your password" in response.text
    assert "fetch('/auth/password-reset/request'" in response.text


def test_verify_and_reset_pages_keep_tokenized_flows() -> None:
    verify = client.get("/verify-email?token=verify-token")
    reset = client.get("/reset-password?token=reset-token")

    assert verify.status_code == 200
    assert "Verify your email" in verify.text
    assert "verify-token" in verify.text
    assert reset.status_code == 200
    assert "Choose a new password" in reset.text
    assert "reset-token" in reset.text
