"""
Security utilities for RAGaaS.

Handles API key generation, hashing, verification,
and input sanitization.
"""

from __future__ import annotations

import re
import secrets
import string
from pathlib import PurePosixPath

import bcrypt


# == API Key Generation ==

_KEY_ALPHABET = string.ascii_letters + string.digits
_KEY_LENGTH = 32  # Characters after prefix
_KEY_PREFIX = "rgs_live_"
_PREFIX_DISPLAY_LENGTH = 8  # Chars of the random part shown in dashboard


def generate_api_key(prefix: str = _KEY_PREFIX) -> tuple[str, str, str]:
    """
    Generate a new API key.

    Returns:
        (raw_key, key_hash, display_prefix)
        - raw_key: the full key to show the user ONCE (e.g. rgs_live_abc123...)
        - key_hash: bcrypt hash to store in the database
        - display_prefix: first 8 chars of the random part for dashboard display
    """
    random_part = "".join(secrets.choice(_KEY_ALPHABET) for _ in range(_KEY_LENGTH))
    raw_key = f"{prefix}{random_part}"
    key_hash = hash_api_key(raw_key)
    display_prefix = f"{prefix}{random_part[:_PREFIX_DISPLAY_LENGTH]}..."
    return raw_key, key_hash, display_prefix


def hash_api_key(raw_key: str) -> str:
    """Hash an API key using bcrypt."""
    return bcrypt.hashpw(raw_key.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """Verify a raw API key against its stored bcrypt hash."""
    try:
        return bcrypt.checkpw(raw_key.encode("utf-8"), stored_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# == Input Sanitization ==

# Namespace: alphanumeric, hyphens, underscores only, max 64 chars
_NAMESPACE_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-_]{0,63}$")

# Filename: strip path traversal, limit characters
_UNSAFE_FILENAME_CHARS = re.compile(r"[^a-zA-Z0-9._\-\s]")


def validate_namespace_name(name: str) -> bool:
    """Validate that a namespace name is safe and within constraints."""
    return bool(_NAMESPACE_PATTERN.match(name))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal and injection.

    - Strips directory components
    - Removes unsafe characters
    - Limits length to 255 chars
    - Falls back to 'unnamed_file' if empty
    """
    # Strip any directory path
    name = PurePosixPath(filename).name

    # Remove unsafe characters
    name = _UNSAFE_FILENAME_CHARS.sub("_", name)

    # Collapse consecutive underscores
    name = re.sub(r"_+", "_", name).strip("_")

    # Limit length
    if len(name) > 255:
        stem = name[:240]
        ext = name[name.rfind(".") :] if "." in name else ""
        name = f"{stem}{ext}"

    return name or "unnamed_file"


def sanitize_query(query: str, max_length: int = 2000) -> str:
    """
    Sanitize a user query string.

    - Strips leading/trailing whitespace
    - Truncates to max_length
    - Removes null bytes
    """
    query = query.strip().replace("\x00", "")
    return query[:max_length]
