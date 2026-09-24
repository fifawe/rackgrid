"""Enumerations shared across the domain layer."""
from __future__ import annotations

from enum import Enum


class AssetStatus(str, Enum):
    ACTIVE = "Active"
    OFFLINE = "Offline"
    RETIRED = "Retired"


class VirtualPhysical(str, Enum):
    VIRTUAL = "Virtual"
    PHYSICAL = "Physical"
    UNKNOWN = "Unknown"


class TriggerSource(str, Enum):
    MANUAL = "MANUAL"
    INTERNAL_SCHEDULER = "INTERNAL_SCHEDULER"
    EXTERNAL = "EXTERNAL"


class CollectorRunStatus(str, Enum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class Technology(str, Enum):
    AUTOMATION = "Automation"
    BACKEND_SERVER = "Backend Server"
    DATABASE = "Database"
    DNS = "DNS"
    DHCP = "DHCP"
    IDENTITY_MANAGEMENT = "Identity Management"
    LOAD_BALANCER = "Load Balancer"
    MESSAGE_BROKER = "Message Broker"
    MIDDLEWARE = "Middleware"
    MONITORING = "Monitoring"
    PROXY = "Proxy"
    STORAGE = "Storage"
    WEB_APPLICATION = "Web Application"
    BACKUP = "Backup"
    CONTAINER_PLATFORM = "Container Platform"
    OTHER = "Other"


class UserRole(str, Enum):
    VIEWER = "Viewer"
    EDITOR = "Editor"
    ADMIN = "Admin"


# Fields the collector is authoritative for. The audit/discovery service
# must never allow these to be written by anything other than discovery.
COLLECTOR_OWNED_FIELDS = {
    "hostname",
    "serial_number",
    "primary_ip",
    "manufacturer",
    "model",
    "cpu_model",
    "cpu_count",
    "cpu_cores",
    "cpu_threads",
    "ram_gb",
    "os_distribution",
    "os_version",
    "kernel_version",
    "architecture",
    "uptime_seconds",
    "virtual_physical",
    "hypervisor",
}

# Fields owned exclusively by manual business metadata management.
# The collector must NEVER write to these.
BUSINESS_OWNED_FIELDS = {
    "asset_owner",
    "support_team",
    "application_name",
    "business_service",
    "environment",
    "site",
    "rack_number",
    "technology",
    "hw_support_expiry",
    "os_support_expiry",
    "status",
}

# Placeholder values BIOS/hypervisor vendors report when no real serial
# number was ever configured - seen in practice as a literal, IDENTICAL
# string ("Not Specified" is the common one) reported by every VM cloned
# from the same KVM/QEMU/Proxmox template. AssetMatchingService treats a
# non-empty serial_number as authoritative and matches on it before
# primary IP or hostname, so if one of these ever reaches it unfiltered,
# every host reporting it collides into a single asset record - each
# discovery overwriting the last one's data ("only the last host
# collected"). The collector (see collector/group_vars/all.yml's
# collector_invalid_serial_values) already filters these before they're
# ever submitted; this is defense-in-depth against any collector version,
# manual API call, or other data source that doesn't.
INVALID_SERIAL_NUMBERS = {
    "",
    "na",
    "n/a",
    "not specified",
    "not applicable",
    "none",
    "null",
    "default string",
    "system serial number",
    "to be filled by o.e.m.",
    "0000000000",
    "unknown",
}


def is_usable_identifier(value: str | None) -> bool:
    """True if `value` looks like a real, unique hardware identifier
    rather than empty input or a known BIOS/hypervisor placeholder."""
    if not value:
        return False
    return value.strip().lower() not in INVALID_SERIAL_NUMBERS


# Sentinel filter value meaning "assets with no value for this field at
# all" - the dashboard's "Unknown" OS-family bucket links through to
# GET /assets?os_distribution=__none__ rather than a literal string,
# since there's no real DB value that means "no OS recorded".
UNDEFINED_FILTER_VALUE = "__none__"
