import React from "react";
import { Chip } from "@mui/material";

const COLORS: Record<string, "success" | "default" | "error"> = {
  Active: "success",
  Offline: "default",
  Retired: "error",
};

export default function StatusChip({ status }: { status: string }) {
  return <Chip label={status} color={COLORS[status] ?? "default"} size="small" />;
}
