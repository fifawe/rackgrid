import React, { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import LanguageIcon from "@mui/icons-material/Language";
import { createSite, deleteSite, listSites, updateSite } from "../api/sites";
import { Site } from "../types";
import { useAuth } from "../context/AuthContext";

const EMPTY_FORM = { name: "", code: "", city: "" };

export default function SitesPage() {
  const { hasRole } = useAuth();
  const canEdit = hasRole("Editor");
  const canDelete = hasRole("Admin");

  const [sites, setSites] = useState<Site[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingSite, setEditingSite] = useState<Site | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    try {
      const data = await listSites();
      setSites(data);
    } catch {
      setError("Failed to load sites");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const openCreate = () => {
    setEditingSite(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setDialogOpen(true);
  };

  const openEdit = (site: Site) => {
    setEditingSite(site);
    setForm({ name: site.name, code: site.code ?? "", city: site.city ?? "" });
    setFormError(null);
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) {
      setFormError("Site name is required");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      const payload = { name: form.name.trim(), code: form.code.trim() || null, city: form.city.trim() || null };
      if (editingSite) {
        await updateSite(editingSite.site_id, payload);
      } else {
        await createSite(payload);
      }
      setDialogOpen(false);
      load();
    } catch (err: any) {
      setFormError(err?.response?.data?.detail ?? "Failed to save site");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (site: Site) => {
    if (!window.confirm(`Delete site "${site.name}"? This cannot be undone.`)) return;
    try {
      await deleteSite(site.site_id);
      load();
    } catch {
      setError("Failed to delete site");
    }
  };

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 2 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: "10px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "linear-gradient(135deg, #4f46e5, #0d9488)",
              color: "#fff",
            }}
          >
            <LanguageIcon />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ mb: 0 }}>
              Sites
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Manage the site directory used by the Site dropdown on every asset
            </Typography>
          </Box>
        </Box>
        {canEdit && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
            New Site
          </Button>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Site Name</TableCell>
              <TableCell>Code</TableCell>
              <TableCell>City</TableCell>
              {(canEdit || canDelete) && <TableCell align="right">Actions</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {sites.map((site) => (
              <TableRow key={site.site_id} hover>
                <TableCell sx={{ fontWeight: 600 }}>{site.name}</TableCell>
                <TableCell>{site.code ?? "-"}</TableCell>
                <TableCell>{site.city ?? "-"}</TableCell>
                {(canEdit || canDelete) && (
                  <TableCell align="right">
                    {canEdit && (
                      <IconButton size="small" onClick={() => openEdit(site)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    )}
                    {canDelete && (
                      <IconButton size="small" onClick={() => handleDelete(site)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    )}
                  </TableCell>
                )}
              </TableRow>
            ))}
            {sites.length === 0 && (
              <TableRow>
                <TableCell colSpan={canEdit || canDelete ? 4 : 3} align="center">
                  No sites yet
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>{editingSite ? "Edit Site" : "New Site"}</DialogTitle>
        <DialogContent>
          {formError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {formError}
            </Alert>
          )}
          <TextField
            autoFocus
            fullWidth
            label="Site Name"
            sx={{ mb: 2, mt: 1 }}
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <TextField
            fullWidth
            label="Code"
            sx={{ mb: 2 }}
            value={form.code}
            onChange={(e) => setForm({ ...form, code: e.target.value })}
          />
          <TextField
            fullWidth
            label="City"
            value={form.city}
            onChange={(e) => setForm({ ...form, city: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)} disabled={saving}>
            Cancel
          </Button>
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
