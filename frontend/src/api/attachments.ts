import { apiClient } from "./client";
import { AssetAttachment } from "../types";

export async function listAttachments(assetId: number): Promise<AssetAttachment[]> {
  const { data } = await apiClient.get<AssetAttachment[]>(`/assets/${assetId}/attachments`);
  return data;
}

export async function uploadAttachment(assetId: number, file: File): Promise<AssetAttachment> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post<AssetAttachment>(`/assets/${assetId}/attachments`, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function deleteAttachment(assetId: number, attachmentId: number): Promise<void> {
  await apiClient.delete(`/assets/${assetId}/attachments/${attachmentId}`);
}

/**
 * Downloads an attachment as a blob and triggers the browser's save
 * dialog - same pattern as downloadAssetsCsv, since the endpoint needs
 * the same JWT bearer auth a plain `<a href>` can't attach.
 */
export async function downloadAttachment(
  assetId: number,
  attachmentId: number,
  filename: string
): Promise<void> {
  const response = await apiClient.get(`/assets/${assetId}/attachments/${attachmentId}/download`, {
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
