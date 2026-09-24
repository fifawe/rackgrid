import { apiClient } from "./client";
import { PublicSettings } from "../types";

/** Platform title + logo + running version. No auth required on the
 * backend (the login page needs it before anyone is signed in). */
export async function getPublicSettings(): Promise<PublicSettings> {
  const { data } = await apiClient.get<PublicSettings>("/settings/public");
  return data;
}

export async function updatePlatformTitle(platformTitle: string): Promise<PublicSettings> {
  const { data } = await apiClient.put<PublicSettings>("/settings/title", { platform_title: platformTitle });
  return data;
}

export async function uploadLogo(file: File): Promise<PublicSettings> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post<PublicSettings>("/settings/logo", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function deleteLogo(): Promise<PublicSettings> {
  const { data } = await apiClient.delete<PublicSettings>("/settings/logo");
  return data;
}
