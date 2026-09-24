import { apiClient } from "./client";
import {
  AssetDetail,
  AssetListResponse,
  BulkBusinessMetadataUpdate,
  BulkUpdateResult,
  BusinessMetadata,
  BusinessMetadataUpdate,
  FieldOptions,
  HardwareOptions,
} from "../types";

export interface AssetListParams {
  search?: string;
  technology?: string;
  environment?: string;
  status?: string;
  site?: string;
  os_distribution?: string;
  manufacturer?: string;
  model?: string;
  sort_by?: string;
  sort_dir?: string;
  offset?: number;
  limit?: number;
}

export async function listAssets(params: AssetListParams): Promise<AssetListResponse> {
  const { data } = await apiClient.get<AssetListResponse>("/assets", { params });
  return data;
}

export async function getAsset(assetId: number): Promise<AssetDetail> {
  const { data } = await apiClient.get<AssetDetail>(`/assets/${assetId}`);
  return data;
}

export async function updateBusinessMetadata(
  assetId: number,
  updates: BusinessMetadataUpdate
): Promise<BusinessMetadata> {
  const { data } = await apiClient.put<BusinessMetadata>(`/assets/${assetId}/business`, updates);
  return data;
}

/** Existing distinct values for the dropdown-with-add-new fields (Support
 * Team, Asset Owner, Site, Technology, Environment), used as Autocomplete
 * suggestions - typing something new and saving it makes it show up here
 * next time. */
export async function getFieldOptions(): Promise<FieldOptions> {
  const { data } = await apiClient.get<FieldOptions>("/assets/field-options");
  return data;
}

/** Distinct Manufacturer/Model values currently in the inventory, for the
 * Inventory page's filter dropdowns. */
export async function getHardwareOptions(): Promise<HardwareOptions> {
  const { data } = await apiClient.get<HardwareOptions>("/assets/hardware-options");
  return data;
}

/** Applies the same business-metadata field changes to many assets at
 * once (Inventory page "Bulk Edit"). */
export async function bulkUpdateBusinessMetadata(
  updates: BulkBusinessMetadataUpdate
): Promise<BulkUpdateResult> {
  const { data } = await apiClient.put<BulkUpdateResult>("/assets/bulk-business", updates);
  return data;
}

/**
 * Downloads the filtered inventory as a CSV file.
 *
 * The export endpoint requires the same JWT bearer auth as everything
 * else, which a plain `<a href>` can't attach - so this fetches the
 * CSV as a blob through the authenticated apiClient and triggers the
 * browser's save dialog manually.
 */
export async function downloadAssetsCsv(params: AssetListParams): Promise<void> {
  const response = await apiClient.get("/assets/export.csv", {
    params,
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", "asset_inventory.csv");
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
