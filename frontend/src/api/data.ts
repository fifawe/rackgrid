import { apiClient } from "./client";
import { ImportResult } from "../types";

/**
 * Downloads a ZIP bundle containing the full inventory (inventory.csv)
 * and the complete audit log (audit_log.csv). Same auth-blob-download
 * pattern as downloadAssetsCsv() in api/assets.ts.
 */
export async function downloadInventoryBundle(): Promise<void> {
  const response = await apiClient.get("/data/export", { responseType: "blob" });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;

  const disposition: string | undefined = response.headers?.["content-disposition"];
  const match = disposition?.match(/filename=([^;]+)/);
  link.setAttribute("download", match?.[1]?.trim() ?? "asset_inventory_export.zip");

  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

/**
 * Uploads a CSV built to the same column schema as the inventory export
 * and creates/updates assets from it. See InventoryImportService on the
 * backend for the full set of matching/overwrite/blank-cell rules.
 */
export async function importInventoryCsv(file: File): Promise<ImportResult> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post<ImportResult>("/data/import", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
