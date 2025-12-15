from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
import jwt
from jwt.exceptions import DecodeError
from passlib.context import CryptContext

from shared.core.config import settings
from shared.utils.exceptions import InvalidTokenException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: str, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    secret_key = settings.JWT_SECRET_KEY

    try:
        encoded_jwt = jwt.encode(
            to_encode, secret_key, algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error to generate access token",
        )


def decode_token(token: str) -> dict:
    try:
        secret_key = settings.JWT_SECRET_KEY
        payload = jwt.decode(token, secret_key, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except DecodeError:
        raise InvalidTokenException()


def decode_token_no_verify(token: str) -> dict:
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except DecodeError:
        raise InvalidTokenException()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # bcrypt solo soporta 72 bytes; truncar evita ValueError
    if plain_password is None:
        return False
    truncated = plain_password[:72]
    try:
        return pwd_context.verify(truncated, hashed_password)
    except ValueError:
        # cualquier problema al verificar → credenciales inválidas
        return False


def get_password_hash(password: str) -> str:
    # misma truncación al hashear para mantener simetría
    truncated = password[:72]
    return pwd_context.hash(truncated)
