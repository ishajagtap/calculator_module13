"""End-to-end tests for Authentication (Register/Login) using Playwright."""
import pytest
from playwright.sync_api import Page, expect

def test_register_positive(page: Page, live_server_url: str):
    """Test successful user registration."""
    page.goto(f"{live_server_url}/register")
    
    page.fill("#username", "testuser_e2e")
    page.fill("#email", "test_e2e@example.com")
    page.fill("#password", "password123")
    page.fill("#confirm-password", "password123")
    page.click("#submit-btn")
    
    # Check for success message
    expect(page.locator("#message")).to_have_class("success-msg")
    expect(page.locator("#message")).to_contain_text("Account created successfully")


def test_register_negative_short_password(page: Page, live_server_url: str):
    """Test registration with a password that is too short (client-side validation)."""
    page.goto(f"{live_server_url}/register")
    
    page.fill("#username", "short_pass_user")
    page.fill("#email", "short@example.com")
    page.fill("#password", "123") # Too short
    page.fill("#confirm-password", "123")
    page.click("#submit-btn")
    
    # Check for client-side error hint
    expect(page.locator("#pass-error")).to_be_visible()
    expect(page.locator("#pass-error")).to_contain_text("at least 6 characters")


def test_login_positive(page: Page, live_server_url: str):
    """Test successful user login."""
    # First, ensure a user exists (we can use the one from test_register_positive if they run in order, 
    # but it's better to be independent or use a setup)
    # Registration for clean state
    page.goto(f"{live_server_url}/register")
    page.fill("#username", "loginuser")
    page.fill("#email", "login@example.com")
    page.fill("#password", "securepassword")
    page.fill("#confirm-password", "securepassword")
    page.click("#submit-btn")
    page.wait_for_url("**/login")
    
    # Now login
    page.fill("#email", "login@example.com")
    page.fill("#password", "securepassword")
    page.click("#login-btn")
    
    # Check for success message or redirection
    expect(page.locator("#message")).to_have_class("success-msg")
    expect(page.locator("#message")).to_contain_text("Login successful")
    
    # Verify token is in localStorage
    token = page.evaluate("localStorage.getItem('token')")
    assert token is not None


def test_login_negative_invalid_credentials(page: Page, live_server_url: str):
    """Test login with incorrect credentials."""
    page.goto(f"{live_server_url}/login")
    
    page.fill("#email", "wrong@example.com")
    page.fill("#password", "wrongpassword")
    page.click("#login-btn")
    
    # Check for error message
    expect(page.locator("#message")).to_have_class("error-msg")
    expect(page.locator("#message")).to_contain_text("Invalid email or password")
