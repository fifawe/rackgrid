export type AssetStatus = "Active" | "Offline" | "Retired";

export type Technology =
  | "Automation"
  | "Backend Server"
  | "Database"
  | "DNS"
  | "DHCP"
  | "Identity Management"
  | "Load Balancer"
  | "Message Broker"
  | "Middleware"
  | "Monitoring"
  | "Proxy"
  | "Storage"
  | "Web Application"
  | "Backup"
  | "Container Platform"
  | "Other";

export const TECHNOLOGY_OPTIONS: Technology[] = [
  "Automation",
  "Backend Server",
  "Database",
  "DNS",
  "DHCP",
  "Identity Management",
  "Load Balancer",
  "Message Broker",
  "Middleware",
  "Monitoring",
  "Proxy",
  "Storage",
  "Web Application",
  "Backup",
  "Container Platform",
  "Other",
];

export const ENVIRONMENT_OPTIONS: string[] = ["Production", "Staging", "Development", "DR", "Test"];

// Sentinel filter value meaning "assets with no value recorded for this
// field at all" - mirrors the backend's UNDEFINED_FILTER_VALUE. Used when
// the Dashboard's "Unknown" OS Family pie slice links through to a
// filtered Inventory list, since there's no real OS value meaning "none".
export const UNDEFINED_FILTER_VALUE = "__none__";

export interface AssetSummary {
  asset_id: number;
  hostname: string;
  primary_ip: string | null;
  technology: string | null;
  environment: string | null;
  asset_owner: string | null;
  status: string;
  last_seen: string | null;
}

export interface AssetListResponse {
  items: AssetSummary[];
  total: number;
  offset: number;
  limit: number;
}

export interface StorageOut {
  storage_id: number | null;
  device_name: string;
  filesystem_type: string | null;
  mount_point: string | null;
  capacity_gb: number | null;
}

export interface NetworkOut {
  network_id: number | null;
  interface_name: string;
  ip_address: string | null;
  mac_address: string | null;
}

export interface BusinessMetadata {
  asset_owner: string | null;
  support_team: string | null;
  application_name: string | null;
  business_service: string | null;
  environment: string | null;
  site: string | null;
  rack_number: string | null;
  // Free text on the backend (not enum-constrained) so the "dropdown with
  // option to add new" UX can save a value outside TECHNOLOGY_OPTIONS.
  technology: string | null;
  hw_support_expiry: string | null;
  os_support_expiry: string | null;
  status: AssetStatus;
}

export interface BusinessMetadataUpdate {
  asset_owner?: string | null;
  support_team?: string | null;
  application_name?: string | null;
  business_service?: string | null;
  environment?: string | null;
  site?: string | null;
  rack_number?: string | null;
  technology?: string | null;
  hw_support_expiry?: string | null;
  os_support_expiry?: string | null;
  status?: AssetStatus;
}

export interface BulkBusinessMetadataUpdate extends BusinessMetadataUpdate {
  asset_ids: number[];
}

export interface BulkUpdateResult {
  updated: number;
  asset_ids: number[];
}

export interface FieldOptions {
  support_team: string[];
  asset_owner: string[];
  site: string[];
  technology: string[];
  environment: string[];
}

export interface Site {
  site_id: number;
  name: string;
  code: string | null;
  city: string | null;
}

export interface SiteInput {
  name: string;
  code: string | null;
  city: string | null;
}

export interface SupportTeam {
  support_team_id: number;
  name: string;
  contact_number: string | null;
  email: string | null;
  location: string | null;
  notes: string | null;
}

export interface SupportTeamInput {
  name: string;
  contact_number: string | null;
  email: string | null;
  location: string | null;
  notes: string | null;
}

export interface AssetAttachment {
  attachment_id: number;
  original_filename: string;
  content_type: string | null;
  file_size: number | null;
  uploaded_by: string | null;
  uploaded_at: string;
}

export interface PublicSettings {
  platform_title: string;
  logo_url: string | null;
  version: string;
}

export interface AssetDetail {
  asset_id: number;
  hostname: string;
  serial_number: string | null;
  primary_ip: string | null;
  manufacturer: string | null;
  model: string | null;
  cpu_model: string | null;
  cpu_count: number | null;
  cpu_cores: number | null;
  cpu_threads: number | null;
  ram_gb: number | null;
  os_distribution: string | null;
  os_version: string | null;
  kernel_version: string | null;
  architecture: string | null;
  uptime_seconds: number | null;
  virtual_physical: string | null;
  hypervisor: string | null;
  first_seen: string | null;
  last_seen: string | null;
  last_collection: string | null;
  storage: StorageOut[];
  network: NetworkOut[];
  business: BusinessMetadata | null;
}

export interface AuditRecord {
  audit_id: number | null;
  asset_id: number;
  collector_run_id: number | null;
  field_name: string;
  old_value: string | null;
  new_value: string | null;
  change_timestamp: string;
  source: string;
}

export interface AuditListResponse {
  items: AuditRecord[];
  total: number;
  offset: number;
  limit: number;
}

export interface ExpiringSupportItem {
  asset_id: number;
  hostname: string;
  support_type: "Hardware" | "OS";
  expiry_date: string;
  days_remaining: number;
}

export interface DashboardSummary {
  total_assets: number;
  active_assets: number;
  offline_assets: number;
  retired_assets: number;
  physical_assets: number;
  virtual_assets: number;
  by_technology: Record<string, number>;
  by_site: Record<string, number>;
  by_environment: Record<string, number>;
  by_os_family: Record<string, number>;
  by_manufacturer: Record<string, number>;
  // Collapses everything past the top 9 most common models into an
  // "Other" bucket server-side, since Model can have far higher
  // cardinality than the dashboard's other dimensions - see
  // SqlAlchemyAssetRepository._top_n_with_other().
  by_model: Record<string, number>;
  expiring_support_count: number;
  expiring_support: ExpiringSupportItem[];
}

export interface HardwareOptions {
  manufacturer: string[];
  model: string[];
}

export interface ImportRowError {
  row: number;
  message: string;
}

export interface ImportResult {
  created: number;
  updated: number;
  errors: ImportRowError[];
}

export interface CollectorRun {
  run_id: number | null;
  start_time: string;
  end_time: string | null;
  status: string;
  assets_processed: number;
  success_count: number;
  failure_count: number;
  trigger_source: string;
}

export interface RunHistoryResponse {
  items: CollectorRun[];
  total: number;
  offset: number;
  limit: number;
}

export interface ScheduledJob {
  id: string;
  next_run_time: string | null;
}
