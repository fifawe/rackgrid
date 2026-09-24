import React, { useEffect, useState } from "react";
import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  TextField,
  Typography,
} from "@mui/material";
import { bulkUpdateBusinessMetadata } from "../../api/assets";
import { listSupportTeams } from "../../api/supportTeams";
import { BulkBusinessMetadataUpdate, ENVIRONMENT_OPTIONS, FieldOptions, SupportTeam } from "../../types";
import FieldAutocomplete from "./FieldAutocomplete";

interface BulkEditDialogProps {
  open: boolean;
  assetIds: number[];
  fieldOptions: FieldOptions;
  onClose: () => void;
  onSaved: () => void;
}

/**
 * Applies the same business-metadata changes to every selected asset at
 * once. Only fields the user actually touches are sent - an untouched
 * field is left as-is on every asset (see BulkBusinessMetadataUpdate on
 * the backend), so leaving everything blank and hitting Save is a no-op
 * rather than a mass-clear.
 */
export default function BulkEditDialog({ open, assetIds, fieldOptions, onClose, onSaved }: BulkEditDialogProps) {
  const [form, setForm] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [supportTeams, setSupportTeams] = useState<SupportTeam[]>([]);

  useEffect(() => {
    listSupportTeams()
      .then(setSupportTeams)
      .catch(() => undefined);
  }, []);

  const handleClose = () => {
    setForm({});
    setError(null);
    onClose();
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload: BulkBusinessMetadataUpdate = { asset_ids: assetIds };
      Object.entries(form).forEach(([key, value]) => {
        if (value) (payload as any)[key] = value;
      });
      await bulkUpdateBusinessMetadata(payload);
      setForm({});
      onSaved();
    } catch {
      setError("Failed to apply bulk edit - check your permissions and try again");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Bulk Edit {assetIds.length} Host{assetIds.length === 1 ? "" : "s"}</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Only the fields you fill in below will be changed. Everything left blank stays as-is on each
          selected host.
        </Typography>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Support Team</InputLabel>
              <Select
                label="Support Team"
                value={form.support_team || ""}
                onChange={(e) => setForm({ ...form, support_team: e.target.value })}
              >
                <MenuItem value="">Leave unchanged</MenuItem>
                {supportTeams.map((team) => (
                  <MenuItem key={team.support_team_id} value={team.name}>
                    {team.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <FieldAutocomplete
              label="Asset Owner"
              options={fieldOptions.asset_owner}
              value={form.asset_owner || null}
              onChange={(v) => setForm({ ...form, asset_owner: v ?? "" })}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FieldAutocomplete
              label="Site"
              options={fieldOptions.site}
              value={form.site || null}
              onChange={(v) => setForm({ ...form, site: v ?? "" })}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Rack Number"
              placeholder="e.g. R-12-U18"
              value={form.rack_number || ""}
              onChange={(e) => setForm({ ...form, rack_number: e.target.value })}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FieldAutocomplete
              label="Technology"
              options={fieldOptions.technology}
              value={form.technology || null}
              onChange={(v) => setForm({ ...form, technology: v ?? "" })}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Environment</InputLabel>
              <Select
                label="Environment"
                value={form.environment || ""}
                onChange={(e) => setForm({ ...form, environment: e.target.value })}
              >
                <MenuItem value="">Leave unchanged</MenuItem>
                {ENVIRONMENT_OPTIONS.map((env) => (
                  <MenuItem key={env} value={env}>
                    {env}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                label="Status"
                value={form.status || ""}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
              >
                <MenuItem value="">Leave unchanged</MenuItem>
                <MenuItem value="Active">Active</MenuItem>
                <MenuItem value="Offline">Offline</MenuItem>
                <MenuItem value="Retired">Retired</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={saving}>
          Cancel
        </Button>
        <Button variant="contained" onClick={handleSave} disabled={saving}>
          Apply to {assetIds.length} Host{assetIds.length === 1 ? "" : "s"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
