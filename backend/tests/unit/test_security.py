"""Unit tests for security routines: filename sanitization, password hashing."""

from app.core.security import (
    generate_secure_token,
    hash_password,
    sanitize_filename,
    verify_password,
)


def test_sanitize_filename_traversal():
    assert sanitize_filename("../../../../etc/passwd") == "etc_passwd"
    assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "windows_system32_cmd.exe"
    assert sanitize_filename("safe_document.pdf") == "safe_document.pdf"
    assert sanitize_filename("file\x00with\x00null.pdf") == "filewithnull.pdf"
    assert sanitize_filename("   ") == "sanitized_file"
    assert sanitize_filename("") == "unnamed_file"


def test_password_hashing_and_verification():
    raw_password = "SuperSecretPassword123!"
    hashed = hash_password(raw_password)

    assert hashed.startswith("pbkdf2:sha256:")
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False
    assert verify_password("", hashed) is False


def test_secure_token_generation():
    token1 = generate_secure_token(32)
    token2 = generate_secure_token(32)
    assert len(token1) > 20
    assert token1 != token2
