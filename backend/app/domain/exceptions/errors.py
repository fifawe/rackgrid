"""Domain-level exceptions. These carry no HTTP knowledge - the API layer
translates them into the appropriate response."""
from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain errors."""


class AssetNotFoundError(DomainError):
    def __init__(self, asset_id: int):
        self.asset_id = asset_id
        super().__init__(f"Asset {asset_id} not found")


class InvalidDiscoveryPayloadError(DomainError):
    def __init__(self, message: str):
        super().__init__(message)


class BusinessFieldProtectedError(DomainError):
    """Raised if discovery attempts to write a business-owned field."""

    def __init__(self, field_name: str):
        self.field_name = field_name
        super().__init__(f"Field '{field_name}' is business-owned and cannot be set by discovery")


class AuthenticationError(DomainError):
    pass


class AuthorizationError(DomainError):
    def __init__(self, required_role: str):
        self.required_role = required_role
        super().__init__(f"Requires role: {required_role}")
