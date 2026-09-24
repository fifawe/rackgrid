import { apiClient } from "./client";
import { AuditListResponse } from "../types";

export interface AuditListParams {
  asset_id?: number;
  field_name?: string;
  date_from?: string;
  date_to?: string;
  offset?: number;
  limit?: number;
}

export async function listAudit(params: AuditListParams): Promise<AuditListResponse> {
  const { data } = await apiClient.get<AuditListResponse>("/audit", { params });
  return data;
}
