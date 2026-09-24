import React, { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import { getRunHistory, listJobs, runNow, setSchedule } from "../api/jobs";
import { CollectorRun, ScheduledJob } from "../types";
import { useAuth } from "../context/AuthContext";

const STATUS_COLOR: Record<string, "success" | "error" | "warning" | "default"> = {
  SUCCESS: "success",
  FAILED: "error",
  PARTIAL: "warning",
  RUNNING: "default",
};

export default function JobManagementPage() {
  const { hasRole } = useAuth();
  const [jobs, setJobs] = useState<ScheduledJob[]>([]);
  const [history, setHistory] = useState<CollectorRun[]>([]);
  const [cron, setCron] = useState("0 2 * * *");
  const [message, setMessage] = useState<string | null>(null);

  const refresh = async () => {
    const [jobList, historyResp] = await Promise.all([listJobs(), getRunHistory(0, 20)]);
    setJobs(jobList);
    setHistory(historyResp.items);
  };

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleRunNow = async () => {
    setMessage(null);
    try {
      await runNow();
      setMessage("Collector run triggered");
      setTimeout(refresh, 2000);
    } catch {
      setMessage("Failed to trigger run - check your permissions");
    }
  };

  const handleSchedule = async () => {
    setMessage(null);
    try {
      await setSchedule(cron);
      setMessage("Schedule updated");
      refresh();
    } catch {
      setMessage("Failed to update schedule - check your permissions");
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Job Management
      </Typography>

      {message && (
        <Alert sx={{ mb: 2 }} onClose={() => setMessage(null)}>
          {message}
        </Alert>
      )}

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Scheduled Jobs
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Job ID</TableCell>
                  <TableCell>Next Run</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {jobs.map((j) => (
                  <TableRow key={j.id}>
                    <TableCell>{j.id}</TableCell>
                    <TableCell>{j.next_run_time ? new Date(j.next_run_time).toLocaleString() : "-"}</TableCell>
                  </TableRow>
                ))}
                {jobs.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={2} align="center">
                      No scheduled jobs
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>

            <Box sx={{ mt: 2, display: "flex", gap: 2, alignItems: "center" }}>
              <Button
                variant="contained"
                startIcon={<PlayArrowIcon />}
                onClick={handleRunNow}
                disabled={!hasRole("Editor")}
              >
                Run Now
              </Button>
            </Box>

            {hasRole("Admin") && (
              <Box sx={{ mt: 3, display: "flex", gap: 2, alignItems: "center" }}>
                <TextField
                  label="Cron Expression"
                  value={cron}
                  onChange={(e) => setCron(e.target.value)}
                  helperText="minute hour day month weekday"
                  size="small"
                />
                <Button variant="outlined" onClick={handleSchedule}>
                  Update Schedule
                </Button>
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Run History
            </Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Run ID</TableCell>
                  <TableCell>Started</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Processed</TableCell>
                  <TableCell>Trigger</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {history.map((run) => (
                  <TableRow key={run.run_id}>
                    <TableCell>{run.run_id}</TableCell>
                    <TableCell>{new Date(run.start_time).toLocaleString()}</TableCell>
                    <TableCell>
                      <Chip
                        label={run.status}
                        size="small"
                        color={STATUS_COLOR[run.status] ?? "default"}
                      />
                    </TableCell>
                    <TableCell>
                      {run.success_count}/{run.assets_processed} ok
                    </TableCell>
                    <TableCell>{run.trigger_source}</TableCell>
                  </TableRow>
                ))}
                {history.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} align="center">
                      No runs yet
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
