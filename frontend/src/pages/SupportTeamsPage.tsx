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
import SupportAgentIcon from "@mui/icons-material/SupportAgent";
import { createSupportTeam, deleteSupportTeam, listSupportTeams, updateSupportTeam } from "../api/supportTeams";
import { SupportTeam } from "../types";
import { useAuth } from "../context/AuthContext";

const EMPTY_FORM = { name: "", contact_number: "", email: "", location: "", notes: "" };

export default function SupportTeamsPage() {
  const { hasRole } = useAuth();
  const canEdit = hasRole("Editor");
  const canDelete = hasRole("Admin");

  const [teams, setTeams] = useState<SupportTeam[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingTeam, setEditingTeam] = useState<SupportTeam | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    try {
      const data = await listSupportTeams();
      setTeams(data);
    } catch {
      setError("Failed to load support teams");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const openCreate = () => {
    setEditingTeam(null);
    setForm(EMPTY_FORM);
    setFormError(null);
    setDialogOpen(true);
  };

  const openEdit = (team: SupportTeam) => {
    setEditingTeam(team);
    setForm({
      name: team.name,
      contact_number: team.contact_number ?? "",
      email: team.email ?? "",
      location: team.location ?? "",
      notes: team.notes ?? "",
    });
    setFormError(null);
    setDialogOpen(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) {
      setFormError("Support team name is required");
      return;
    }
    setSaving(true);
    setFormError(null);
    try {
      const payload = {
        name: form.name.trim(),
        contact_number: form.contact_number.trim() || null,
        email: form.email.trim() || null,
        location: form.location.trim() || null,
        notes: form.notes.trim() || null,
      };
      if (editingTeam) {
        await updateSupportTeam(editingTeam.support_team_id, payload);
      } else {
        await createSupportTeam(payload);
      }
      setDialogOpen(false);
      load();
    } catch (err: any) {
      setFormError(err?.response?.data?.detail ?? "Failed to save support team");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (team: SupportTeam) => {
    if (!window.confirm(`Delete support team "${team.name}"? This cannot be undone.`)) return;
    try {
      await deleteSupportTeam(team.support_team_id);
      load();
    } catch {
      setError("Failed to delete support team");
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
            <SupportAgentIcon />
          </Box>
          <Box>
            <Typography variant="h4" sx={{ mb: 0 }}>
              Support Team
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Manage the support team directory used by the Support Team dropdown on every asset
            </Typography>
          </Box>
        </Box>
        {canEdit && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
            New Support Team
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
              <TableCell>Name</TableCell>
              <TableCell>Contact Number</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Location</TableCell>
              <TableCell>Notes</TableCell>
              {(canEdit || canDelete) && <TableCell align="right">Actions</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {teams.map((team) => (
              <TableRow key={team.support_team_id} hover>
                <TableCell sx={{ fontWeight: 600 }}>{team.name}</TableCell>
                <TableCell>{team.contact_number ?? "-"}</TableCell>
                <TableCell>{team.email ?? "-"}</TableCell>
                <TableCell>{team.location ?? "-"}</TableCell>
                <TableCell sx={{ maxWidth: 260, whiteSpace: "pre-wrap" }}>{team.notes ?? "-"}</TableCell>
                {(canEdit || canDelete) && (
                  <TableCell align="right">
                    {canEdit && (
                      <IconButton size="small" onClick={() => openEdit(team)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    )}
                    {canDelete && (
                      <IconButton size="small" onClick={() => handleDelete(team)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    )}
                  </TableCell>
                )}
              </TableRow>
            ))}
            {teams.length === 0 && (
              <TableRow>
                <TableCell colSpan={canEdit || canDelete ? 6 : 5} align="center">
                  No support teams yet
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>{editingTeam ? "Edit Support Team" : "New Support Team"}</DialogTitle>
        <DialogContent>
          {formError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {formError}
            </Alert>
          )}
          <TextField
            autoFocus
            fullWidth
            label="Name"
            sx={{ mb: 2, mt: 1 }}
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
          />
          <TextField
            fullWidth
            label="Contact Number"
            sx={{ mb: 2 }}
            value={form.contact_number}
            onChange={(e) => setForm({ ...form, contact_number: e.target.value })}
          />
          <TextField
            fullWidth
            label="Email"
            type="email"
            sx={{ mb: 2 }}
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
          <TextField
            fullWidth
            label="Location"
            sx={{ mb: 2 }}
            value={form.location}
            onChange={(e) => setForm({ ...form, location: e.target.value })}
          />
          <TextField
            fullWidth
            label="Notes"
            multiline
            minRows={2}
            value={form.notes}
            onChange={(e) => setForm({ ...form, notes: e.target.value })}
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
