"""Cifrado reversible para claves API (Dooblo) por empresa, usando clave derivada de JWT."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

_FERNET: Fernet | None = None


def _fernet() -> Fernet:
    global _FERNET
    if _FERNET is None:
        # Fernet: 32 bytes urlsafe base64
        raw = hashlib.sha256((settings.JWT_SECRET_KEY or "").encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(raw)
        _FERNET = Fernet(key)
    return _FERNET


def encrypt_secret(plain: str) -> str:
    return _fernet().encrypt(plain.encode("utf-8")).decode("ascii")


def decrypt_secret(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as e:
        raise ValueError("No se pudo descifrar la clave (claves rotadas o datos corruptos).") from e
