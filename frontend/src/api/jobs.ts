import { apiClient } from "./client";
import { RunHistoryResponse, ScheduledJob } from "../types";

export async function listJobs(): Promise<ScheduledJob[]> {
  const { data } = await apiClient.get<{ jobs: ScheduledJob[] }>("/jobs");
  return data.jobs;
}

export async function runNow(): Promise<void> {
  await apiClient.post("/jobs/run");
}

export async function setSchedule(cronExpression: string): Promise<void> {
  await apiClient.post("/jobs/schedule", { cron_expression: cronExpression });
}

export async function getRunHistory(offset = 0, limit = 20): Promise<RunHistoryResponse> {
  const { data } = await apiClient.get<RunHistoryResponse>("/jobs/history", {
    params: { offset, limit },
  });
  return data;
}
