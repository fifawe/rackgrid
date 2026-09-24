import { apiClient } from "./client";
import { Site, SiteInput } from "../types";

export async function listSites(): Promise<Site[]> {
  const { data } = await apiClient.get<Site[]>("/sites");
  return data;
}

export async function createSite(input: SiteInput): Promise<Site> {
  const { data } = await apiClient.post<Site>("/sites", input);
  return data;
}

export async function updateSite(siteId: number, input: SiteInput): Promise<Site> {
  const { data } = await apiClient.put<Site>(`/sites/${siteId}`, input);
  return data;
}

export async function deleteSite(siteId: number): Promise<void> {
  await apiClient.delete(`/sites/${siteId}`);
}
