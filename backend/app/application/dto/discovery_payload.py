"""DTOs representing the collector discovery payload (see
PROJECT_SPEC.md > Discovery Payload Specification)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HardwareDTO:
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    cpu_model: Optional[str] = None
    cpu_count: Optional[int] = None
    cpu_cores: Optional[int] = None
    cpu_threads: Optional[int] = None
    ram_gb: Optional[float] = None


@dataclass
class OsDTO:
    distribution: Optional[str] = None
    version: Optional[str] = None
    kernel: Optional[str] = None
    architecture: Optional[str] = None
    uptime_seconds: Optional[int] = None


@dataclass
class VirtualizationDTO:
    role: Optional[str] = None
    hypervisor: Optional[str] = None


@dataclass
class StorageDTO:
    device_name: str
    filesystem_type: Optional[str] = None
    mount_point: Optional[str] = None
    capacity_gb: Optional[float] = None


@dataclass
class NetworkDTO:
    interface_name: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None


@dataclass
class DiscoveryPayloadDTO:
    hostname: str
    serial_number: Optional[str] = None
    primary_ip: Optional[str] = None
    hardware: HardwareDTO = field(default_factory=HardwareDTO)
    os: OsDTO = field(default_factory=OsDTO)
    virtualization: VirtualizationDTO = field(default_factory=VirtualizationDTO)
    storage: List[StorageDTO] = field(default_factory=list)
    network: List[NetworkDTO] = field(default_factory=list)
    collector_run_id: Optional[int] = None
