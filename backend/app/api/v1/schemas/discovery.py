"""Pydantic schemas for the collector discovery payload (POST /api/v1/discovery)."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class HardwareSchema(BaseModel):
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    cpu_model: Optional[str] = None
    cpu_count: Optional[int] = None
    cpu_cores: Optional[int] = None
    cpu_threads: Optional[int] = None
    ram_gb: Optional[float] = None


class OsSchema(BaseModel):
    distribution: Optional[str] = None
    version: Optional[str] = None
    kernel: Optional[str] = None
    architecture: Optional[str] = None
    uptime_seconds: Optional[int] = None


class VirtualizationSchema(BaseModel):
    role: Optional[str] = None
    hypervisor: Optional[str] = None


class StorageSchema(BaseModel):
    device_name: str
    filesystem_type: Optional[str] = None
    mount_point: Optional[str] = None
    capacity_gb: Optional[float] = None


class NetworkSchema(BaseModel):
    interface_name: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None


class DiscoveryPayloadSchema(BaseModel):
    hostname: str = Field(..., min_length=1)
    serial_number: Optional[str] = None
    primary_ip: Optional[str] = None

    hardware: HardwareSchema = HardwareSchema()
    os: OsSchema = OsSchema()
    virtualization: VirtualizationSchema = VirtualizationSchema()

    storage: List[StorageSchema] = []
    network: List[NetworkSchema] = []

    collector_run_id: Optional[int] = None


class DiscoveryResponseSchema(BaseModel):
    asset_id: int
    hostname: str
    created: bool
