"""Pydantic schemas for asset inventory endpoints."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator

from app.domain.value_objects.enums import AssetStatus


class StorageOut(BaseModel):
    storage_id: Optional[int] = None
    device_name: str
    filesystem_type: Optional[str] = None
    mount_point: Optional[str] = None
    capacity_gb: Optional[float] = None

    model_config = {"from_attributes": True}


class NetworkOut(BaseModel):
    network_id: Optional[int] = None
    interface_name: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None

    model_config = {"from_attributes": True}


class BusinessMetadataOut(BaseModel):
    asset_owner: Optional[str] = None
    support_team: Optional[str] = None
    application_name: Optional[str] = None
    business_service: Optional[str] = None
    environment: Optional[str] = None
    site: Optional[str] = None
    rack_number: Optional[str] = None
    technology: Optional[str] = None
    hw_support_expiry: Optional[date] = None
    os_support_expiry: Optional[date] = None
    status: AssetStatus = AssetStatus.ACTIVE


class BusinessMetadataUpdate(BaseModel):
    asset_owner: Optional[str] = None
    support_team: Optional[str] = None
    application_name: Optional[str] = None
    business_service: Optional[str] = None
    environment: Optional[str] = None
    site: Optional[str] = None
    rack_number: Optional[str] = None
    technology: Optional[str] = None
    hw_support_expiry: Optional[date] = None
    os_support_expiry: Optional[date] = None
    status: Optional[AssetStatus] = None

    def to_update_dict(self) -> dict:
        return {k: v for k, v in self.model_dump().items() if v is not None}


class BulkBusinessMetadataUpdate(BaseModel):
    """Same field set as BusinessMetadataUpdate, applied to many assets at
    once. asset_ids selects the target assets; every other populated field
    is written to each of them (fields left as None are left untouched)."""

    asset_ids: List[int]
    asset_owner: Optional[str] = None
    support_team: Optional[str] = None
    application_name: Optional[str] = None
    business_service: Optional[str] = None
    environment: Optional[str] = None
    site: Optional[str] = None
    rack_number: Optional[str] = None
    technology: Optional[str] = None
    hw_support_expiry: Optional[date] = None
    os_support_expiry: Optional[date] = None
    status: Optional[AssetStatus] = None

    def to_update_dict(self) -> dict:
        return {
            k: v
            for k, v in self.model_dump().items()
            if v is not None and k != "asset_ids"
        }


class BulkUpdateResult(BaseModel):
    updated: int
    asset_ids: List[int]


class FieldOptionsOut(BaseModel):
    support_team: List[str] = []
    asset_owner: List[str] = []
    site: List[str] = []
    technology: List[str] = []
    environment: List[str] = []


class HardwareOptionsOut(BaseModel):
    manufacturer: List[str] = []
    model: List[str] = []


class AssetSummaryOut(BaseModel):
    asset_id: int
    hostname: str
    primary_ip: Optional[str] = None
    technology: Optional[str] = None
    environment: Optional[str] = None
    asset_owner: Optional[str] = None
    status: str
    last_seen: Optional[datetime] = None


class AssetListResponse(BaseModel):
    items: List[AssetSummaryOut]
    total: int
    offset: int
    limit: int


class AssetDetailOut(BaseModel):
    asset_id: int
    hostname: str
    serial_number: Optional[str] = None
    primary_ip: Optional[str] = None

    manufacturer: Optional[str] = None
    model: Optional[str] = None
    cpu_model: Optional[str] = None
    cpu_count: Optional[int] = None
    cpu_cores: Optional[int] = None
    cpu_threads: Optional[int] = None
    ram_gb: Optional[float] = None

    os_distribution: Optional[str] = None
    os_version: Optional[str] = None
    kernel_version: Optional[str] = None
    architecture: Optional[str] = None
    uptime_seconds: Optional[int] = None

    virtual_physical: Optional[str] = None
    hypervisor: Optional[str] = None

    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    last_collection: Optional[datetime] = None

    storage: List[StorageOut] = []
    network: List[NetworkOut] = []
    business: Optional[BusinessMetadataOut] = None
