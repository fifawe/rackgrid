"""JWT issuing/decoding (implements application.services.auth_service.TokenIssuer)."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt

from app.infrastructure.config.settings import get_settings


class JwtTokenIssuer:
    def __init__(self, secret_key: Optional[str] = None, algorithm: Optional[str] = None):
        settings = get_settings()
        self._secret_key = secret_key or settings.secret_key
        self._algorithm = algorithm or settings.algorithm
        self._expire_minutes = settings.access_token_expire_minutes

    def issue(self, subject: str, role: str) -> str:
        expire = datetime.utcnow() + timedelta(minutes=self._expire_minutes)
        payload = {"sub": subject, "role": role, "exp": expire}
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def decode(self, token: str) -> dict:
        settings = get_settings()
        try:
            return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        except JWTError as exc:
            raise ValueError("Invalid or expired token") from exc
