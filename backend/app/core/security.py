"""Security utilities: input sanitization, file hashing, and credentials."""

import hashlib
import hmac
import re
import secrets
from pathlib import Path


def sanitize_filename(filename: str) -> str:
    """Sanitize uploaded filenames against path traversal, control chars, and reserved names."""
    if not filename:
        return "unnamed_file"

    # Remove null bytes and path separators
    cleaned = filename.replace("\x00", "").strip()
    cleaned = re.sub(r"[/\\]+", "_", cleaned)

    # Disallow leading dots to prevent hidden files and relative traversal
    cleaned = re.sub(r"^\.+", "", cleaned)

    # Allow alphanumeric, hyphens, underscores, dots, and common spaces
    cleaned = re.sub(r"[^\w\s\.-]", "_", cleaned)

    # Collapse multiple underscores/spaces
    cleaned = re.sub(r"[\s_]+", "_", cleaned).strip("._")

    return cleaned or "sanitized_file"


def calculate_file_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file on disk in 64KB chunks."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 with a secure random salt."""
    salt = secrets.token_bytes(16)
    iterations = 310000
    derived_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2:sha256:{iterations}${salt.hex()}${derived_key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a PBKDF2-HMAC-SHA256 hash."""
    try:
        algorithm, salt_hex, key_hex = hashed_password.split("$")
        parts = algorithm.split(":")
        iterations = int(parts[2])
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        candidate_key = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt, iterations
        )
        return hmac.compare_digest(candidate_key, expected_key)
    except Exception:
        return False


def generate_secure_token(nbytes: int = 32) -> str:
    """Generate a cryptographically secure random URL-safe token."""
    return secrets.token_urlsafe(nbytes)
