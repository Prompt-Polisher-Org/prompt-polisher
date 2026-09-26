"""
core/encryption.py — AES Fernet encryption for sensitive data at rest.

Task: Week 11-12 / Security Audit (task.md line 648)
  [x] Sensitive data encryption at rest

Uses the `cryptography` library's Fernet implementation (AES-128-CBC + HMAC-SHA256)
to transparently encrypt/decrypt sensitive fields before they hit PostgreSQL.

Usage:
    from app.core.encryption import encrypt_value, decrypt_value

    ciphertext = encrypt_value("sk-abc123...")   # → "gAAAAABk..."
    plaintext  = decrypt_value(ciphertext)       # → "sk-abc123..."
"""
import base64
import hashlib
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

# ── Key Management ────────────────────────────────────────────────────────────
# The ENCRYPTION_KEY env var should be a 32-byte URL-safe base64-encoded key.
# Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
#
# If not set, we derive a deterministic key from SECRET_KEY as a fallback
# (acceptable for a university project, NOT for production).


def _get_fernet() -> Fernet:
    """Get the Fernet cipher instance, creating it from environment variables."""
    encryption_key = os.getenv("ENCRYPTION_KEY")

    if encryption_key:
        # Use the explicit encryption key
        return Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)

    # Fallback: derive from SECRET_KEY
    secret_key = os.getenv("SECRET_KEY", "CHANGE_ME_to_a_long_random_secret_key_in_production")
    derived = hashlib.sha256(secret_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(derived)
    return Fernet(fernet_key)


# Module-level singleton
_fernet: Fernet | None = None


def _get_cipher() -> Fernet:
    """Lazy-initialize the Fernet cipher."""
    global _fernet
    if _fernet is None:
        _fernet = _get_fernet()
    return _fernet


# ── Public API ────────────────────────────────────────────────────────────────

def encrypt_value(plaintext: str) -> str:
    """
    Encrypt a plaintext string for database storage.

    Returns a URL-safe base64-encoded ciphertext string.
    """
    if not plaintext:
        return plaintext
    cipher = _get_cipher()
    return cipher.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_value(ciphertext: str) -> str:
    """
    Decrypt a ciphertext string retrieved from the database.

    Returns the original plaintext string.
    Raises ValueError if the ciphertext is invalid or tampered with.
    """
    if not ciphertext:
        return ciphertext
    cipher = _get_cipher()
    try:
        return cipher.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        logger.error("Failed to decrypt value — possible key mismatch or data corruption")
        raise ValueError("Decryption failed: invalid token or key mismatch")
"""

Encrypted column type for SQLAlchemy models.
"""
from sqlalchemy import String, TypeDecorator


class EncryptedString(TypeDecorator):
    """
    A SQLAlchemy column type that transparently encrypts/decrypts string values.

    Usage in a model:
        api_key: Mapped[str | None] = mapped_column(EncryptedString(500), nullable=True)

    In the database, the value is stored as a Fernet ciphertext (e.g. "gAAAAABk...").
    In Python, the value is always the original plaintext string.
    """
    impl = String
    cache_ok = True

    def __init__(self, length: int = 500, *args, **kwargs):
        super().__init__(*args, length=length, **kwargs)

    def process_bind_param(self, value, dialect):
        """Encrypt before saving to the database."""
        if value is not None:
            return encrypt_value(value)
        return value

    def process_result_value(self, value, dialect):
        """Decrypt after reading from the database."""
        if value is not None:
            try:
                return decrypt_value(value)
            except ValueError:
                return value  # Return raw if decryption fails (graceful degradation)
        return value
"""
Core encryption utilities are ready for use.
"""
