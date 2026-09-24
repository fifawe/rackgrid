import { apiClient } from "./client";
import { SupportTeam, SupportTeamInput } from "../types";

export async function listSupportTeams(): Promise<SupportTeam[]> {
  const { data } = await apiClient.get<SupportTeam[]>("/support-teams");
  return data;
}

export async function createSupportTeam(input: SupportTeamInput): Promise<SupportTeam> {
  const { data } = await apiClient.post<SupportTeam>("/support-teams", input);
  return data;
}

export async function updateSupportTeam(supportTeamId: number, input: SupportTeamInput): Promise<SupportTeam> {
  const { data } = await apiClient.put<SupportTeam>(`/support-teams/${supportTeamId}`, input);
  return data;
}

export async function deleteSupportTeam(supportTeamId: number): Promise<void> {
  await apiClient.delete(`/support-teams/${supportTeamId}`);
}
