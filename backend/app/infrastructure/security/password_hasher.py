"""Bcrypt password hashing (implements application.services.auth_service.PasswordHasher).

Uses the `bcrypt` library directly rather than passlib: passlib is
effectively unmaintained and its bcrypt backend probing breaks against
bcrypt>=4.1 (AttributeError on bcrypt.__about__). Talking to bcrypt
directly avoids that fragile dependency chain entirely.
"""
from __future__ import annotations

import bcrypt

_BCRYPT_ROUNDS = 12


class BcryptPasswordHasher:
    def hash(self, plain_password: str) -> str:
        salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
        return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except ValueError:
            return False
