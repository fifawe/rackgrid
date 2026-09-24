"""Hardware value object collected by the discovery pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class HardwareInfo:
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    cpu_model: Optional[str] = None
    cpu_count: Optional[int] = None
    cpu_cores: Optional[int] = None
    cpu_threads: Optional[int] = None
    ram_gb: Optional[float] = None


@dataclass(frozen=True)
class OperatingSystemInfo:
    distribution: Optional[str] = None
    version: Optional[str] = None
    kernel: Optional[str] = None
    architecture: Optional[str] = None
    uptime_seconds: Optional[int] = None


@dataclass(frozen=True)
class VirtualizationInfo:
    role: Optional[str] = None  # "guest" | "host" | "physical"
    hypervisor: Optional[str] = None

    @property
    def virtual_physical(self) -> str:
        if self.role and self.role.lower() == "guest":
            return "Virtual"
        if self.role and self.role.lower() in ("host", "physical"):
            return "Physical"
        return "Unknown"
