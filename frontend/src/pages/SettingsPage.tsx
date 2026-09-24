import React, { useRef, useState } from "react";
import {
  Alert,
  Avatar,
  Box,
  Button,
  Divider,
  FormControlLabel,
  Paper,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import SettingsIcon from "@mui/icons-material/Settings";
import UploadIcon from "@mui/icons-material/Upload";
import DeleteIcon from "@mui/icons-material/Delete";
import LockIcon from "@mui/icons-material/Lock";
import PaletteIcon from "@mui/icons-material/Palette";
import BrandingWatermarkIcon from "@mui/icons-material/BrandingWatermark";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";
import { deleteLogo, updatePlatformTitle, uploadLogo } from "../api/settings";
import { changePassword } from "../api/auth";
import { useSettings } from "../context/SettingsContext";
import { useAuth } from "../context/AuthContext";
import { useThemeMode } from "../context/ThemeModeContext";

function SectionHeader({ icon, title, subtitle }: { icon: React.ReactNode; title: string; subtitle: string }) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 2 }}>
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
          flexShrink: 0,
        }}
      >
        {icon}
      </Box>
      <Box>
        <Typography variant="h4" sx={{ mb: 0 }}>
          {title}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {subtitle}
        </Typography>
      </Box>
    </Box>
  );
}

function AccountSection() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleChangePassword = async () => {
    setMessage(null);
    setError(null);
    if (newPassword.length < 8) {
      setError("New password must be at least 8 characters");
      return;
    }
    if (newPassword !== confirmPassword) {
      setError("New password and confirmation do not match");
      return;
    }
    setSaving(true);
    try {
      await changePassword(currentPassword, newPassword);
      setMessage("Password changed");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Failed to change password");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Paper sx={{ p: 3, mb: 3, maxWidth: 520 }}>
      <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 2 }}>
        Change Password
      </Typography>
      {message && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setMessage(null)}>
          {message}
        </Alert>
      )}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      <Stack spacing={2}>
        <TextField
          fullWidth
          type="password"
          label="Current Password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
        />
        <TextField
          fullWidth
          type="password"
          label="New Password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          helperText="At least 8 characters"
        />
        <TextField
          fullWidth
          type="password"
          label="Confirm New Password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
        />
        <Box>
          <Button
            variant="contained"
            disabled={saving || !currentPassword || !newPassword}
            onClick={handleChangePassword}
          >
            Update Password
          </Button>
        </Box>
      </Stack>
    </Paper>
  );
}

function AppearanceSection() {
  const { mode, toggleMode } = useThemeMode();
  return (
    <Paper sx={{ p: 3, mb: 3, maxWidth: 520 }}>
      <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 2 }}>
        Appearance
      </Typography>
      <FormControlLabel
        control={<Switch checked={mode === "dark"} onChange={toggleMode} />}
        label={
          <Stack direction="row" alignItems="center" spacing={1}>
            {mode === "dark" ? <DarkModeIcon fontSize="small" /> : <LightModeIcon fontSize="small" />}
            <Typography variant="body2">{mode === "dark" ? "Dark mode" : "Light mode"}</Typography>
          </Stack>
        }
      />
      <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.5 }}>
        Remembered on this device only
      </Typography>
    </Paper>
  );
}

function BrandingSection() {
  const { settings, refresh } = useSettings();
  const [title, setTitle] = useState(settings.platform_title);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSaveTitle = async () => {
    if (!title.trim()) {
      setError("Platform title is required");
      return;
    }
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      await updatePlatformTitle(title.trim());
      await refresh();
      setMessage("Platform title saved");
    } catch {
      setError("Failed to save platform title");
    } finally {
      setSaving(false);
    }
  };

  const handleLogoSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    setMessage(null);
    try {
      await uploadLogo(file);
      await refresh();
      setMessage("Logo updated");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Failed to upload logo");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleRemoveLogo = async () => {
    setUploading(true);
    setError(null);
    setMessage(null);
    try {
      await deleteLogo();
      await refresh();
      setMessage("Logo removed");
    } catch {
      setError("Failed to remove logo");
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      <Divider sx={{ my: 3, maxWidth: 520 }} />
      <SectionHeader
        icon={<BrandingWatermarkIcon />}
        title="Platform Branding"
        subtitle="Customize the platform's title and logo shown in the sidebar and login page"
      />
      {message && (
        <Alert severity="success" sx={{ mb: 2, maxWidth: 520 }} onClose={() => setMessage(null)}>
          {message}
        </Alert>
      )}
      {error && (
        <Alert severity="error" sx={{ mb: 2, maxWidth: 520 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3, maxWidth: 520 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 2 }}>
          Platform Title
        </Typography>
        <Stack direction="row" spacing={2} alignItems="flex-start">
          <TextField
            fullWidth
            label="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            helperText="Shown in the sidebar header and on the login page"
          />
          <Button variant="contained" onClick={handleSaveTitle} disabled={saving} sx={{ mt: 0.25 }}>
            Save
          </Button>
        </Stack>
      </Paper>

      <Paper sx={{ p: 3, maxWidth: 520 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 2 }}>
          Logo
        </Typography>
        <Stack direction="row" spacing={2} alignItems="center">
          <Avatar
            variant="rounded"
            src={settings.logo_url ?? undefined}
            sx={{ width: 56, height: 56, bgcolor: "grey.100" }}
          >
            {!settings.logo_url && <SettingsIcon color="disabled" />}
          </Avatar>
          <Box>
            <input
              ref={fileInputRef}
              type="file"
              accept=".png,.jpg,.jpeg,.svg"
              hidden
              onChange={handleLogoSelected}
            />
            <Stack direction="row" spacing={1}>
              <Button
                variant="outlined"
                startIcon={<UploadIcon />}
                disabled={uploading}
                onClick={() => fileInputRef.current?.click()}
              >
                Upload Logo
              </Button>
              {settings.logo_url && (
                <Button
                  variant="text"
                  color="error"
                  startIcon={<DeleteIcon />}
                  disabled={uploading}
                  onClick={handleRemoveLogo}
                >
                  Remove
                </Button>
              )}
            </Stack>
            <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.5 }}>
              PNG, JPG or SVG, up to 5 MB
            </Typography>
          </Box>
        </Stack>
      </Paper>
    </>
  );
}

export default function SettingsPage() {
  const { hasRole } = useAuth();

  return (
    <Box>
      <SectionHeader
        icon={<SettingsIcon />}
        title="Settings"
        subtitle="Manage your account and how the platform looks"
      />

      <Typography variant="h6" sx={{ fontWeight: 700, mb: 1, display: "flex", alignItems: "center", gap: 1 }}>
        <LockIcon fontSize="small" /> My Account
      </Typography>
      <AccountSection />

      <Typography variant="h6" sx={{ fontWeight: 700, mb: 1, display: "flex", alignItems: "center", gap: 1 }}>
        <PaletteIcon fontSize="small" /> Appearance
      </Typography>
      <AppearanceSection />

      {hasRole("Admin") && <BrandingSection />}
    </Box>
  );
}
