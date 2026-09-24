import React, { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Tab,
  Tabs,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import DnsIcon from "@mui/icons-material/Dns";
import DeveloperBoardIcon from "@mui/icons-material/DeveloperBoard";
import TerminalIcon from "@mui/icons-material/Terminal";
import StorageIcon from "@mui/icons-material/Storage";
import SettingsEthernetIcon from "@mui/icons-material/SettingsEthernet";
import BusinessCenterIcon from "@mui/icons-material/BusinessCenter";
import AttachFileIcon from "@mui/icons-material/AttachFile";
import HistoryIcon from "@mui/icons-material/History";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import DownloadIcon from "@mui/icons-material/Download";
import DeleteIcon from "@mui/icons-material/Delete";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import { getAsset, getFieldOptions, updateBusinessMetadata } from "../api/assets";
import { listAudit } from "../api/audit";
import { listSupportTeams } from "../api/supportTeams";
import { deleteAttachment, downloadAttachment, listAttachments, uploadAttachment } from "../api/attachments";
import {
  AssetAttachment,
  AssetDetail,
  AuditRecord,
  ENVIRONMENT_OPTIONS,
  FieldOptions,
  SupportTeam,
  TECHNOLOGY_OPTIONS,
} from "../types";
import StatusChip from "../components/common/StatusChip";
import FieldAutocomplete from "../components/common/FieldAutocomplete";
import { useAuth } from "../context/AuthContext";

const EMPTY_FIELD_OPTIONS: FieldOptions = {
  support_team: [],
  asset_owner: [],
  site: [],
  technology: [...TECHNOLOGY_OPTIONS],
  environment: [],
};

const ACCEPTED_ATTACHMENT_TYPES = ".pdf,.docx,.xlsx,.png,.jpg,.jpeg";

function TabPanel({ value, index, children }: { value: number; index: number; children: React.ReactNode }) {
  if (value !== index) return null;
  return <Box sx={{ py: 2 }}>{children}</Box>;
}

/** A small icon-badge + title/subtitle header, matching the visual
 * language used atop the Sites and Support Team pages - gives each tab's
 * content a consistent, clearly-labeled entry point instead of dropping
 * straight into a bare grid of fields. */
function SectionHeader({
  icon,
  title,
  subtitle,
}: {
  icon: React.ReactNode;
  title: string;
  subtitle?: string;
}) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 2 }}>
      <Box
        sx={{
          width: 34,
          height: 34,
          borderRadius: "9px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "linear-gradient(135deg, #4f46e5, #0d9488)",
          color: "#fff",
          flexShrink: 0,
        }}
      >
        {icon}
      </Box>
      <Box>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </Box>
    </Box>
  );
}

function formatFileSize(bytes: number | null): string {
  if (bytes == null) return "-";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function AssetDetailsPage() {
  const { assetId } = useParams();
  const { hasRole } = useAuth();
  const [asset, setAsset] = useState<AssetDetail | null>(null);
  const [audit, setAudit] = useState<AuditRecord[]>([]);
  const [tab, setTab] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [fieldOptions, setFieldOptions] = useState<FieldOptions>(EMPTY_FIELD_OPTIONS);
  const [supportTeams, setSupportTeams] = useState<SupportTeam[]>([]);
  const [attachments, setAttachments] = useState<AssetAttachment[]>([]);
  const [attachmentError, setAttachmentError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const canEdit = hasRole("Editor");

  const load = async () => {
    if (!assetId) return;
    try {
      const data = await getAsset(Number(assetId));
      setAsset(data);
      setForm({
        asset_owner: data.business?.asset_owner ?? "",
        support_team: data.business?.support_team ?? "",
        application_name: data.business?.application_name ?? "",
        business_service: data.business?.business_service ?? "",
        environment: data.business?.environment ?? "",
        site: data.business?.site ?? "",
        rack_number: data.business?.rack_number ?? "",
        technology: data.business?.technology ?? "",
        hw_support_expiry: data.business?.hw_support_expiry ?? "",
        os_support_expiry: data.business?.os_support_expiry ?? "",
        status: data.business?.status ?? "Active",
      });
      const auditData = await listAudit({ asset_id: Number(assetId), limit: 100 });
      setAudit(auditData.items);
    } catch {
      setError("Failed to load asset");
    }
  };

  const loadFieldOptions = async () => {
    try {
      const options = await getFieldOptions();
      setFieldOptions(options);
    } catch {
      // Non-fatal: the form still works with plain free-text entry.
    }
  };

  const loadSupportTeams = async () => {
    try {
      setSupportTeams(await listSupportTeams());
    } catch {
      // Non-fatal: the Support Team dropdown just shows no options.
    }
  };

  const loadAttachments = async () => {
    if (!assetId) return;
    try {
      setAttachments(await listAttachments(Number(assetId)));
    } catch {
      setAttachmentError("Failed to load attachments");
    }
  };

  useEffect(() => {
    load();
    loadFieldOptions();
    loadSupportTeams();
    loadAttachments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assetId]);

  const handleSave = async () => {
    if (!assetId) return;
    setSaveMessage(null);
    try {
      await updateBusinessMetadata(Number(assetId), {
        ...form,
        technology: form.technology || null,
        hw_support_expiry: form.hw_support_expiry || null,
        os_support_expiry: form.os_support_expiry || null,
      } as any);
      setSaveMessage("Business metadata saved");
      load();
      loadFieldOptions();
    } catch {
      setSaveMessage("Failed to save - check your permissions");
    }
  };

  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !assetId) return;
    setUploading(true);
    setAttachmentError(null);
    try {
      await uploadAttachment(Number(assetId), file);
      loadAttachments();
    } catch (err: any) {
      setAttachmentError(err?.response?.data?.detail ?? "Failed to upload file");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDeleteAttachment = async (attachment: AssetAttachment) => {
    if (!assetId) return;
    if (!window.confirm(`Delete "${attachment.original_filename}"? This cannot be undone.`)) return;
    try {
      await deleteAttachment(Number(assetId), attachment.attachment_id);
      loadAttachments();
    } catch {
      setAttachmentError("Failed to delete attachment");
    }
  };

  const handleDownloadAttachment = (attachment: AssetAttachment) => {
    if (!assetId) return;
    downloadAttachment(Number(assetId), attachment.attachment_id, attachment.original_filename);
  };

  if (error) return <Alert severity="error">{error}</Alert>;
  if (!asset)
    return (
      <Box sx={{ display: "flex", justifyContent: "center", mt: 8 }}>
        <CircularProgress />
      </Box>
    );

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 1 }}>
        <Typography variant="h4">{asset.hostname}</Typography>
        {asset.business && <StatusChip status={asset.business.status} />}
        <Chip label={asset.virtual_physical ?? "Unknown"} variant="outlined" size="small" />
      </Box>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        {asset.primary_ip} · Serial: {asset.serial_number ?? "-"} · Last seen:{" "}
        {asset.last_seen ? new Date(asset.last_seen).toLocaleString() : "-"}
      </Typography>

      <Tabs
        value={tab}
        onChange={(_, v) => setTab(v)}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ borderBottom: 1, borderColor: "divider", mb: 1 }}
      >
        <Tab icon={<DeveloperBoardIcon fontSize="small" />} iconPosition="start" label="Hardware" />
        <Tab icon={<TerminalIcon fontSize="small" />} iconPosition="start" label="Operating System" />
        <Tab icon={<StorageIcon fontSize="small" />} iconPosition="start" label="Storage" />
        <Tab icon={<SettingsEthernetIcon fontSize="small" />} iconPosition="start" label="Network" />
        <Tab icon={<BusinessCenterIcon fontSize="small" />} iconPosition="start" label="Business Metadata" />
        <Tab
          icon={<AttachFileIcon fontSize="small" />}
          iconPosition="start"
          label={`Attachments${attachments.length > 0 ? ` (${attachments.length})` : ""}`}
        />
        <Tab icon={<HistoryIcon fontSize="small" />} iconPosition="start" label="Audit History" />
      </Tabs>

      <TabPanel value={tab} index={0}>
        <Paper sx={{ p: 3 }}>
          <SectionHeader icon={<DeveloperBoardIcon fontSize="small" />} title="Hardware" />
          <Grid container spacing={3}>
            <Grid item xs={6} sm={3}>
              <Typography variant="overline" color="text.secondary">Manufacturer</Typography>
              <Typography>{asset.manufacturer ?? "-"}</Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="overline" color="text.secondary">Model</Typography>
              <Typography>{asset.model ?? "-"}</Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="overline" color="text.secondary">CPU Model</Typography>
              <Typography>{asset.cpu_model ?? "-"}</Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="overline" color="text.secondary">CPU (count/cores/threads)</Typography>
              <Typography>
                {asset.cpu_count ?? "-"} / {asset.cpu_cores ?? "-"} / {asset.cpu_threads ?? "-"}
              </Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="overline" color="text.secondary">RAM (GB)</Typography>
              <Typography>{asset.ram_gb ?? "-"}</Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="overline" color="text.secondary">Hypervisor</Typography>
              <Typography>{asset.hypervisor ?? "-"}</Typography>
            </Grid>
          </Grid>
        </Paper>
      </TabPanel>

      <TabPanel value={tab} index={1}>
        <Paper sx={{ p: 3 }}>
          <SectionHeader icon={<TerminalIcon fontSize="small" />} title="Operating System" />
          <Grid container spacing={3}>
            <Grid item xs={6} sm={3}>
              <Typography variant="overline" color="text.secondary">Distribution</Typography>
              <Typography>{asset.os_distribution ?? "-"}</Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="overline" color="text.secondary">Version</Typography>
              <Typography>{asset.os_version ?? "-"}</Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="overline" color="text.secondary">Kernel</Typography>
              <Typography>{asset.kernel_version ?? "-"}</Typography>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Typography variant="overline" color="text.secondary">Architecture</Typography>
              <Typography>{asset.architecture ?? "-"}</Typography>
            </Grid>
          </Grid>
        </Paper>
      </TabPanel>

      <TabPanel value={tab} index={2}>
        <Paper sx={{ p: 3 }}>
          <SectionHeader icon={<StorageIcon fontSize="small" />} title="Storage" />
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Device</TableCell>
                <TableCell>Filesystem</TableCell>
                <TableCell>Mount Point</TableCell>
                <TableCell>Capacity (GB)</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {asset.storage.map((s, i) => (
                <TableRow key={i} hover>
                  <TableCell>{s.device_name}</TableCell>
                  <TableCell>{s.filesystem_type ?? "-"}</TableCell>
                  <TableCell>{s.mount_point ?? "-"}</TableCell>
                  <TableCell>{s.capacity_gb ?? "-"}</TableCell>
                </TableRow>
              ))}
              {asset.storage.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} align="center">
                    No storage devices recorded
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Paper>
      </TabPanel>

      <TabPanel value={tab} index={3}>
        <Paper sx={{ p: 3 }}>
          <SectionHeader icon={<SettingsEthernetIcon fontSize="small" />} title="Network" />
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Interface</TableCell>
                <TableCell>IP Address</TableCell>
                <TableCell>MAC Address</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {asset.network.map((n, i) => (
                <TableRow key={i} hover>
                  <TableCell>{n.interface_name}</TableCell>
                  <TableCell>{n.ip_address ?? "-"}</TableCell>
                  <TableCell>{n.mac_address ?? "-"}</TableCell>
                </TableRow>
              ))}
              {asset.network.length === 0 && (
                <TableRow>
                  <TableCell colSpan={3} align="center">
                    No network interfaces recorded
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Paper>
      </TabPanel>

      <TabPanel value={tab} index={4}>
        <Paper sx={{ p: 3 }}>
          <SectionHeader icon={<BusinessCenterIcon fontSize="small" />} title="Business Metadata" />
          {saveMessage && <Alert sx={{ mb: 2 }}>{saveMessage}</Alert>}
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <FieldAutocomplete
                label="Asset Owner"
                disabled={!canEdit}
                options={fieldOptions.asset_owner}
                value={form.asset_owner || null}
                onChange={(v) => setForm({ ...form, asset_owner: v ?? "" })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth disabled={!canEdit}>
                <InputLabel>Support Team</InputLabel>
                <Select
                  label="Support Team"
                  value={form.support_team}
                  onChange={(e) => setForm({ ...form, support_team: e.target.value })}
                >
                  <MenuItem value="">
                    <em>None</em>
                  </MenuItem>
                  {supportTeams.map((team) => (
                    <MenuItem key={team.support_team_id} value={team.name}>
                      {team.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Application Name"
                disabled={!canEdit}
                value={form.application_name}
                onChange={(e) => setForm({ ...form, application_name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Business Service"
                disabled={!canEdit}
                value={form.business_service}
                onChange={(e) => setForm({ ...form, business_service: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth disabled={!canEdit}>
                <InputLabel>Environment</InputLabel>
                <Select
                  label="Environment"
                  value={form.environment}
                  onChange={(e) => setForm({ ...form, environment: e.target.value })}
                >
                  <MenuItem value="">
                    <em>None</em>
                  </MenuItem>
                  {ENVIRONMENT_OPTIONS.map((env) => (
                    <MenuItem key={env} value={env}>
                      {env}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FieldAutocomplete
                label="Technology"
                disabled={!canEdit}
                options={fieldOptions.technology}
                value={form.technology || null}
                onChange={(v) => setForm({ ...form, technology: v ?? "" })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth disabled={!canEdit}>
                <InputLabel>Status</InputLabel>
                <Select
                  label="Status"
                  value={form.status}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                >
                  <MenuItem value="Active">Active</MenuItem>
                  <MenuItem value="Offline">Offline</MenuItem>
                  <MenuItem value="Retired">Retired</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="HW Support Expiry"
                type="date"
                disabled={!canEdit}
                InputLabelProps={{ shrink: true }}
                value={form.hw_support_expiry}
                onChange={(e) => setForm({ ...form, hw_support_expiry: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="OS Support Expiry"
                type="date"
                disabled={!canEdit}
                InputLabelProps={{ shrink: true }}
                value={form.os_support_expiry}
                onChange={(e) => setForm({ ...form, os_support_expiry: e.target.value })}
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}>
            <DnsIcon fontSize="small" color="action" />
            <Typography variant="subtitle1">Server Location</Typography>
          </Box>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={4}>
              <FieldAutocomplete
                label="Site"
                disabled={!canEdit}
                options={fieldOptions.site}
                value={form.site || null}
                onChange={(v) => setForm({ ...form, site: v ?? "" })}
                helperText="Manage the full Site directory (code, city) on the Sites page"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Rack Number"
                placeholder="e.g. R-12-U18"
                disabled={!canEdit}
                value={form.rack_number}
                onChange={(e) => setForm({ ...form, rack_number: e.target.value })}
              />
            </Grid>
          </Grid>

          {canEdit && (
            <Button variant="contained" sx={{ mt: 3 }} onClick={handleSave}>
              Save Business Metadata
            </Button>
          )}
        </Paper>
      </TabPanel>

      <TabPanel value={tab} index={5}>
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", mb: 2 }}>
            <SectionHeader
              icon={<AttachFileIcon fontSize="small" />}
              title="Attachments"
              subtitle="Design documents and other reference files for this asset"
            />
            {canEdit && (
              <Box>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={ACCEPTED_ATTACHMENT_TYPES}
                  hidden
                  onChange={handleFileSelected}
                />
                <Button
                  variant="contained"
                  size="small"
                  startIcon={<UploadFileIcon />}
                  disabled={uploading}
                  onClick={() => fileInputRef.current?.click()}
                >
                  {uploading ? "Uploading..." : "Upload File"}
                </Button>
              </Box>
            )}
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 2 }}>
            Accepted types: PDF, DOCX, XLSX, PNG, JPG
          </Typography>

          {attachmentError && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setAttachmentError(null)}>
              {attachmentError}
            </Alert>
          )}

          <List disablePadding>
            {attachments.map((a) => (
              <ListItem
                key={a.attachment_id}
                divider
                secondaryAction={
                  <Box sx={{ display: "flex", gap: 0.5 }}>
                    <Tooltip title="Download">
                      <IconButton edge="end" size="small" onClick={() => handleDownloadAttachment(a)}>
                        <DownloadIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    {canEdit && (
                      <Tooltip title="Delete">
                        <IconButton edge="end" size="small" onClick={() => handleDeleteAttachment(a)}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                }
              >
                <ListItemIcon sx={{ minWidth: 36 }}>
                  <InsertDriveFileIcon color="action" />
                </ListItemIcon>
                <ListItemText
                  primary={a.original_filename}
                  secondary={`${formatFileSize(a.file_size)} · uploaded ${new Date(a.uploaded_at).toLocaleString()}${
                    a.uploaded_by ? ` by ${a.uploaded_by}` : ""
                  }`}
                />
              </ListItem>
            ))}
            {attachments.length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: "center" }}>
                No attachments yet
              </Typography>
            )}
          </List>
        </Paper>
      </TabPanel>

      <TabPanel value={tab} index={6}>
        <Paper sx={{ p: 3 }}>
          <SectionHeader icon={<HistoryIcon fontSize="small" />} title="Audit History" />
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Field</TableCell>
                <TableCell>Old Value</TableCell>
                <TableCell>New Value</TableCell>
                <TableCell>Date</TableCell>
                <TableCell>Source</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {audit.map((a) => (
                <TableRow key={a.audit_id} hover>
                  <TableCell>{a.field_name}</TableCell>
                  <TableCell>{a.old_value ?? "-"}</TableCell>
                  <TableCell>{a.new_value ?? "-"}</TableCell>
                  <TableCell>{new Date(a.change_timestamp).toLocaleString()}</TableCell>
                  <TableCell>{a.source}</TableCell>
                </TableRow>
              ))}
              {audit.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    No changes recorded yet
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Paper>
      </TabPanel>
    </Box>
  );
}
