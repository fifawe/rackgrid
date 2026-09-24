import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Box,
  Button,
  Checkbox,
  Chip,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TableSortLabel,
  TextField,
  Typography,
} from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import EditIcon from "@mui/icons-material/Edit";
import { downloadAssetsCsv, getFieldOptions, getHardwareOptions, listAssets } from "../api/assets";
import {
  AssetSummary,
  ENVIRONMENT_OPTIONS,
  FieldOptions,
  HardwareOptions,
  TECHNOLOGY_OPTIONS,
  UNDEFINED_FILTER_VALUE,
} from "../types";
import StatusChip from "../components/common/StatusChip";
import BulkEditDialog from "../components/common/BulkEditDialog";
import { useAuth } from "../context/AuthContext";

const STATUSES = ["Active", "Offline", "Retired"];

const EMPTY_FIELD_OPTIONS: FieldOptions = {
  support_team: [],
  asset_owner: [],
  site: [],
  technology: [...TECHNOLOGY_OPTIONS],
  environment: [],
};

const EMPTY_HARDWARE_OPTIONS: HardwareOptions = { manufacturer: [], model: [] };

export default function InventoryPage() {
  const navigate = useNavigate();
  const { hasRole } = useAuth();
  const [searchParams] = useSearchParams();
  const [items, setItems] = useState<AssetSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  // Arriving from a Dashboard chart click pre-fills these from the URL
  // (?technology=X / ?os_distribution=X, the latter possibly the
  // "__none__" sentinel for "no OS recorded").
  const [technology, setTechnology] = useState(searchParams.get("technology") || "");
  const [environment, setEnvironment] = useState(searchParams.get("environment") || "");
  const [status, setStatus] = useState("");
  const [osDistribution, setOsDistribution] = useState(searchParams.get("os_distribution") || "");
  const [manufacturer, setManufacturer] = useState(searchParams.get("manufacturer") || "");
  const [model, setModel] = useState(searchParams.get("model") || "");
  const [sortBy, setSortBy] = useState("hostname");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState<number[]>([]);
  const [bulkEditOpen, setBulkEditOpen] = useState(false);
  const [fieldOptions, setFieldOptions] = useState<FieldOptions>(EMPTY_FIELD_OPTIONS);
  const [hardwareOptions, setHardwareOptions] = useState<HardwareOptions>(EMPTY_HARDWARE_OPTIONS);
  const canEdit = hasRole("Editor");

  const params = {
    search: search || undefined,
    technology: technology || undefined,
    environment: environment || undefined,
    status: status || undefined,
    os_distribution: osDistribution || undefined,
    manufacturer: manufacturer || undefined,
    model: model || undefined,
    sort_by: sortBy,
    sort_dir: sortDir,
    offset: page * rowsPerPage,
    limit: rowsPerPage,
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const data = await listAssets(params);
      setItems(data.items);
      setTotal(data.total);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    setSelected([]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    search,
    technology,
    environment,
    status,
    osDistribution,
    manufacturer,
    model,
    sortBy,
    sortDir,
    page,
    rowsPerPage,
  ]);

  useEffect(() => {
    getFieldOptions()
      .then(setFieldOptions)
      .catch(() => undefined);
    getHardwareOptions()
      .then(setHardwareOptions)
      .catch(() => undefined);
  }, []);

  const toggleSelected = (assetId: number) => {
    setSelected((prev) =>
      prev.includes(assetId) ? prev.filter((id) => id !== assetId) : [...prev, assetId]
    );
  };

  const toggleSelectAllOnPage = () => {
    const pageIds = items.map((i) => i.asset_id);
    const allSelected = pageIds.length > 0 && pageIds.every((id) => selected.includes(id));
    setSelected((prev) =>
      allSelected ? prev.filter((id) => !pageIds.includes(id)) : Array.from(new Set([...prev, ...pageIds]))
    );
  };

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortBy(column);
      setSortDir("asc");
    }
  };

  const columns: { key: string; label: string; sortable?: boolean }[] = [
    { key: "hostname", label: "Hostname", sortable: true },
    { key: "primary_ip", label: "Primary IP", sortable: true },
    { key: "technology", label: "Technology" },
    { key: "environment", label: "Environment" },
    { key: "asset_owner", label: "Owner" },
    { key: "status", label: "Status" },
    { key: "last_seen", label: "Last Seen", sortable: true },
  ];

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1 }}>
        <Typography variant="h4" gutterBottom sx={{ mb: 0 }}>
          Asset Inventory
        </Typography>
        {canEdit && selected.length > 0 && (
          <Button variant="contained" startIcon={<EditIcon />} onClick={() => setBulkEditOpen(true)}>
            Bulk Edit ({selected.length})
          </Button>
        )}
      </Box>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              label="Search hostname / IP"
              value={search}
              onChange={(e) => {
                setPage(0);
                setSearch(e.target.value);
              }}
            />
          </Grid>
          <Grid item xs={6} sm={2}>
            <FormControl fullWidth>
              <InputLabel>Technology</InputLabel>
              <Select
                label="Technology"
                value={technology}
                onChange={(e) => {
                  setPage(0);
                  setTechnology(e.target.value);
                }}
              >
                <MenuItem value="">All</MenuItem>
                {TECHNOLOGY_OPTIONS.map((t) => (
                  <MenuItem key={t} value={t}>
                    {t}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={6} sm={2}>
            <FormControl fullWidth>
              <InputLabel>Environment</InputLabel>
              <Select
                label="Environment"
                value={environment}
                onChange={(e) => {
                  setPage(0);
                  setEnvironment(e.target.value);
                }}
              >
                <MenuItem value="">All</MenuItem>
                {ENVIRONMENT_OPTIONS.map((env) => (
                  <MenuItem key={env} value={env}>
                    {env}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={6} sm={2}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                label="Status"
                value={status}
                onChange={(e) => {
                  setPage(0);
                  setStatus(e.target.value);
                }}
              >
                <MenuItem value="">All</MenuItem>
                {STATUSES.map((s) => (
                  <MenuItem key={s} value={s}>
                    {s}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={6} sm={2}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={() => downloadAssetsCsv(params)}
            >
              Export CSV
            </Button>
          </Grid>
          <Grid item xs={6} sm={3}>
            <FormControl fullWidth>
              <InputLabel>Manufacturer</InputLabel>
              <Select
                label="Manufacturer"
                value={manufacturer}
                onChange={(e) => {
                  setPage(0);
                  setManufacturer(e.target.value);
                }}
              >
                <MenuItem value="">All</MenuItem>
                {hardwareOptions.manufacturer.map((m) => (
                  <MenuItem key={m} value={m}>
                    {m}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={6} sm={3}>
            <FormControl fullWidth>
              <InputLabel>Model</InputLabel>
              <Select
                label="Model"
                value={model}
                onChange={(e) => {
                  setPage(0);
                  setModel(e.target.value);
                }}
              >
                <MenuItem value="">All</MenuItem>
                {hardwareOptions.model.map((m) => (
                  <MenuItem key={m} value={m}>
                    {m}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>
        {(osDistribution || manufacturer || model) && (
          <Box sx={{ mt: 2, display: "flex", gap: 1, flexWrap: "wrap" }}>
            {osDistribution && (
              <Chip
                label={`OS Family: ${osDistribution === UNDEFINED_FILTER_VALUE ? "Unknown" : osDistribution}`}
                onDelete={() => {
                  setPage(0);
                  setOsDistribution("");
                }}
              />
            )}
            {manufacturer && (
              <Chip
                label={`Manufacturer: ${manufacturer === UNDEFINED_FILTER_VALUE ? "Unknown" : manufacturer}`}
                onDelete={() => {
                  setPage(0);
                  setManufacturer("");
                }}
              />
            )}
            {model && (
              <Chip
                label={`Model: ${model === UNDEFINED_FILTER_VALUE ? "Unknown" : model}`}
                onDelete={() => {
                  setPage(0);
                  setModel("");
                }}
              />
            )}
          </Box>
        )}
      </Paper>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              {canEdit && (
                <TableCell padding="checkbox">
                  <Checkbox
                    indeterminate={
                      selected.length > 0 &&
                      !items.every((i) => selected.includes(i.asset_id)) &&
                      items.some((i) => selected.includes(i.asset_id))
                    }
                    checked={items.length > 0 && items.every((i) => selected.includes(i.asset_id))}
                    onChange={toggleSelectAllOnPage}
                  />
                </TableCell>
              )}
              {columns.map((col) => (
                <TableCell key={col.key}>
                  {col.sortable ? (
                    <TableSortLabel
                      active={sortBy === col.key}
                      direction={sortBy === col.key ? sortDir : "asc"}
                      onClick={() => handleSort(col.key)}
                    >
                      {col.label}
                    </TableSortLabel>
                  ) : (
                    col.label
                  )}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((row) => (
              <TableRow
                key={row.asset_id}
                hover
                selected={selected.includes(row.asset_id)}
                sx={{ cursor: "pointer" }}
                onClick={() => navigate(`/inventory/${row.asset_id}`)}
              >
                {canEdit && (
                  <TableCell padding="checkbox" onClick={(e) => e.stopPropagation()}>
                    <Checkbox
                      checked={selected.includes(row.asset_id)}
                      onChange={() => toggleSelected(row.asset_id)}
                    />
                  </TableCell>
                )}
                <TableCell>{row.hostname}</TableCell>
                <TableCell>{row.primary_ip ?? "-"}</TableCell>
                <TableCell>{row.technology ?? "-"}</TableCell>
                <TableCell>{row.environment ?? "-"}</TableCell>
                <TableCell>{row.asset_owner ?? "-"}</TableCell>
                <TableCell>
                  <StatusChip status={row.status} />
                </TableCell>
                <TableCell>{row.last_seen ? new Date(row.last_seen).toLocaleString() : "-"}</TableCell>
              </TableRow>
            ))}
            {items.length === 0 && !loading && (
              <TableRow>
                <TableCell colSpan={columns.length + (canEdit ? 1 : 0)} align="center">
                  No assets found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      </TableContainer>

      {canEdit && (
        <BulkEditDialog
          open={bulkEditOpen}
          assetIds={selected}
          fieldOptions={fieldOptions}
          onClose={() => setBulkEditOpen(false)}
          onSaved={() => {
            setBulkEditOpen(false);
            setSelected([]);
            fetchData();
            getFieldOptions()
              .then(setFieldOptions)
              .catch(() => undefined);
          }}
        />
      )}
    </Box>
  );
}
