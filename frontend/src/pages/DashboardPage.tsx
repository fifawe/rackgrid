import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Box,
  Card,
  CardContent,
  Chip,
  Grid,
  Typography,
  CircularProgress,
  Alert,
  AlertTitle,
  Stack,
} from "@mui/material";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid } from "recharts";
import DnsIcon from "@mui/icons-material/Dns";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CloudOffIcon from "@mui/icons-material/CloudOff";
import ArchiveIcon from "@mui/icons-material/Archive";
import DeveloperBoardIcon from "@mui/icons-material/DeveloperBoard";
import CloudQueueIcon from "@mui/icons-material/CloudQueue";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import { getDashboardSummary } from "../api/dashboard";
import { DashboardSummary, ExpiringSupportItem, UNDEFINED_FILTER_VALUE } from "../types";
import { useSettings } from "../context/SettingsContext";

const COLORS = ["#4f46e5", "#0d9488", "#f59e0b", "#e11d48", "#8b5cf6", "#16a34a", "#0ea5e9", "#64748b"];

interface StatCardProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  accent: string;
}

function StatCard({ label, value, icon, accent }: StatCardProps) {
  return (
    <Grid item xs={12} sm={6} md={2}>
      <Card sx={{ height: "100%" }}>
        <CardContent>
          <Stack direction="row" alignItems="center" spacing={1.5}>
            <Box
              sx={{
                width: 40,
                height: 40,
                borderRadius: "10px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: `${accent}1a`,
                color: accent,
                flexShrink: 0,
              }}
            >
              {icon}
            </Box>
            <Box sx={{ minWidth: 0 }}>
              <Typography variant="body2" color="text.secondary" noWrap>
                {label}
              </Typography>
              <Typography variant="h5" sx={{ fontWeight: 700 }}>
                {value}
              </Typography>
            </Box>
          </Stack>
        </CardContent>
      </Card>
    </Grid>
  );
}

function toChartData(record: Record<string, number>) {
  return Object.entries(record).map(([name, value]) => ({ name, value }));
}

function ChartCard({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <Card sx={{ height: "100%" }}>
      <CardContent>
        <Typography variant="h6" sx={{ fontWeight: 700 }}>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {subtitle}
          </Typography>
        )}
        {children}
      </CardContent>
    </Card>
  );
}

function daysLabel(days: number): string {
  if (days < 0) return `expired ${Math.abs(days)}d ago`;
  if (days === 0) return "expires today";
  return `${days}d left`;
}

function SupportExpiryAlert({ items, count }: { items: ExpiringSupportItem[]; count: number }) {
  const navigate = useNavigate();
  if (count === 0) return null;

  const shown = items.slice(0, 6);
  const extra = count - shown.length;

  return (
    <Alert
      severity="warning"
      icon={<WarningAmberIcon />}
      sx={{ mb: 3, "& .MuiAlert-message": { width: "100%" } }}
    >
      <AlertTitle sx={{ fontWeight: 700 }}>
        {count} support {count === 1 ? "date" : "dates"} expiring within 60 days
      </AlertTitle>
      <Stack direction="row" flexWrap="wrap" gap={1} sx={{ mt: 0.5 }}>
        {shown.map((item) => (
          <Chip
            key={`${item.asset_id}-${item.support_type}`}
            size="small"
            clickable
            onClick={() => navigate(`/inventory/${item.asset_id}`)}
            color={item.days_remaining < 0 ? "error" : "warning"}
            variant="outlined"
            label={`${item.hostname} · ${item.support_type} · ${daysLabel(item.days_remaining)}`}
          />
        ))}
        {extra > 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ alignSelf: "center" }}>
            +{extra} more
          </Typography>
        )}
      </Stack>
    </Alert>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const { settings } = useSettings();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboardSummary()
      .then(setSummary)
      .catch(() => setError("Failed to load dashboard summary"));
  }, []);

  if (error) return <Alert severity="error">{error}</Alert>;
  if (!summary)
    return (
      <Box sx={{ display: "flex", justifyContent: "center", mt: 8 }}>
        <CircularProgress />
      </Box>
    );

  return (
    <Box>
      <Box sx={{ mb: 3, display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            {settings.platform_title} Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            A live view of every server tracked in the inventory
          </Typography>
        </Box>
        {settings.version && (
          <Typography variant="caption" color="text.secondary">
            v{settings.version}
          </Typography>
        )}
      </Box>

      <SupportExpiryAlert items={summary.expiring_support} count={summary.expiring_support_count} />

      <Grid container spacing={2} sx={{ mb: 4 }}>
        <StatCard label="Total Assets" value={summary.total_assets} icon={<DnsIcon />} accent="#4f46e5" />
        <StatCard label="Active" value={summary.active_assets} icon={<CheckCircleIcon />} accent="#16a34a" />
        <StatCard label="Offline" value={summary.offline_assets} icon={<CloudOffIcon />} accent="#e11d48" />
        <StatCard label="Retired" value={summary.retired_assets} icon={<ArchiveIcon />} accent="#64748b" />
        <StatCard
          label="Physical"
          value={summary.physical_assets}
          icon={<DeveloperBoardIcon />}
          accent="#f59e0b"
        />
        <StatCard label="Virtual" value={summary.virtual_assets} icon={<CloudQueueIcon />} accent="#0d9488" />
      </Grid>

      <Grid container spacing={2}>
        <Grid item xs={12} md={6}>
          <ChartCard
            title="By Technology"
            subtitle="Distribution of servers by assigned technology - click a slice to view those hosts"
          >
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={toChartData(summary.by_technology)}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={2}
                  cursor="pointer"
                  onClick={(entry: any) =>
                    navigate(`/inventory?technology=${encodeURIComponent(entry.name)}`)
                  }
                >
                  {toChartData(summary.by_technology).map((_, index) => (
                    <Cell key={index} fill={COLORS[index % COLORS.length]} stroke="none" />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid rgba(30,27,46,0.08)" }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <ChartCard
            title="By OS Family"
            subtitle="Distribution of servers by operating system - click a slice to view those hosts"
          >
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={toChartData(summary.by_os_family)}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={2}
                  cursor="pointer"
                  onClick={(entry: any) => {
                    // "Unknown" isn't a real OS value in the DB - it's how
                    // the dashboard labels hosts with no OS recorded - so
                    // it links through via the "__none__" sentinel filter
                    // rather than the literal string "Unknown".
                    const value = entry.name === "Unknown" ? UNDEFINED_FILTER_VALUE : entry.name;
                    navigate(`/inventory?os_distribution=${encodeURIComponent(value)}`);
                  }}
                >
                  {toChartData(summary.by_os_family).map((_, index) => (
                    <Cell key={index} fill={COLORS[(index + 3) % COLORS.length]} stroke="none" />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid rgba(30,27,46,0.08)" }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <ChartCard title="By Site" subtitle="Server count per physical location">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={toChartData(summary.by_site)}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(30,27,46,0.08)" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid rgba(30,27,46,0.08)" }} />
                <Bar dataKey="value" fill="#4f46e5" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <ChartCard title="By Environment" subtitle="Server count per environment">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={toChartData(summary.by_environment)}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(30,27,46,0.08)" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid rgba(30,27,46,0.08)" }} />
                <Bar dataKey="value" fill="#0d9488" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <ChartCard
            title="By Manufacturer"
            subtitle="Distribution of servers by hardware manufacturer - click a slice to view those hosts"
          >
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={toChartData(summary.by_manufacturer)}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={2}
                  cursor="pointer"
                  onClick={(entry: any) => {
                    const value = entry.name === "Unknown" ? UNDEFINED_FILTER_VALUE : entry.name;
                    navigate(`/inventory?manufacturer=${encodeURIComponent(value)}`);
                  }}
                >
                  {toChartData(summary.by_manufacturer).map((_, index) => (
                    <Cell key={index} fill={COLORS[(index + 5) % COLORS.length]} stroke="none" />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid rgba(30,27,46,0.08)" }} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <ChartCard
            title="By Model"
            subtitle={
              'Top hardware models by server count (long tail collapsed into "Other") - ' +
              'click a bar to view those hosts'
            }
          >
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={toChartData(summary.by_model)} margin={{ bottom: 24 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(30,27,46,0.08)" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11 }}
                  angle={-25}
                  textAnchor="end"
                  interval={0}
                  height={50}
                />
                <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid rgba(30,27,46,0.08)" }} />
                <Bar
                  dataKey="value"
                  radius={[6, 6, 0, 0]}
                  onClick={(entry: any) => {
                    // "Other" collapses many real models into one bucket -
                    // there's no single value to filter Inventory by, so
                    // it's intentionally not clickable (see the backend's
                    // _top_n_with_other()).
                    if (!entry || entry.name === "Other") return;
                    const value = entry.name === "Unknown" ? UNDEFINED_FILTER_VALUE : entry.name;
                    navigate(`/inventory?model=${encodeURIComponent(value)}`);
                  }}
                >
                  {toChartData(summary.by_model).map((entry, index) => (
                    <Cell
                      key={index}
                      fill={entry.name === "Other" ? "#94a3b8" : COLORS[(index + 1) % COLORS.length]}
                      cursor={entry.name === "Other" ? "default" : "pointer"}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </Grid>
      </Grid>
    </Box>
  );
}
