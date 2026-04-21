import time
from playwright.sync_api import Page, expect


def test_register_positive(page: Page, live_server_url: str):
    """Register with valid unique data and verify success message."""
    unique = str(int(time.time()))
    username = f"testuser_{unique}"
    email = f"test_{unique}@example.com"
    password = "password123"

    page.goto(f"{live_server_url}/register")

    page.fill("#username", username)
    page.fill("#email", email)
    page.fill("#password", password)
    page.fill("#confirm-password", password)
    page.click("#submit-btn")

    expect(page.locator("#message")).to_have_class("success-msg")
    expect(page.locator("#message")).to_contain_text("success")


def test_register_negative_short_password(page: Page, live_server_url: str):
    """Short password should not produce a success state."""
    unique = str(int(time.time()))
    username = f"baduser_{unique}"
    email = f"bad_{unique}@example.com"

    page.goto(f"{live_server_url}/register")

    page.fill("#username", username)
    page.fill("#email", email)
    page.fill("#password", "123")
    page.fill("#confirm-password", "123")
    page.click("#submit-btn")

    expect(page).to_have_url(f"{live_server_url}/register")
    expect(page.locator("#message")).not_to_have_class("success-msg")


def test_login_positive(page: Page, live_server_url: str):
    """Register a new user, then log in successfully."""
    unique = str(int(time.time()))
    username = f"loginuser_{unique}"
    email = f"login_{unique}@example.com"
    password = "securepassword"

    page.goto(f"{live_server_url}/register")
    page.fill("#username", username)
    page.fill("#email", email)
    page.fill("#password", password)
    page.fill("#confirm-password", password)
    page.click("#submit-btn")

    expect(page.locator("#message")).to_have_class("success-msg")

    page.goto(f"{live_server_url}/login")
    page.fill("#email", email)
    page.fill("#password", password)
    page.click("#login-btn")

    expect(page.locator("#message")).to_have_class("success-msg")
    expect(page.locator("#message")).to_contain_text("Login successful")

    token = page.evaluate("localStorage.getItem('token')")
    assert token is not None
    assert len(token) > 0


def test_login_negative_wrong_password(page: Page, live_server_url: str):
    """Login with incorrect password and verify error message."""
    page.goto(f"{live_server_url}/login")

    page.fill("#email", "wronguser@example.com")
    page.fill("#password", "wrongpassword")
    page.click("#login-btn")

    expect(page.locator("#message")).to_have_class("error-msg")