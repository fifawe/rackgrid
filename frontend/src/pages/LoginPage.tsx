import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Alert, Avatar, Box, Button, Paper, Stack, TextField, Typography } from "@mui/material";
import DnsIcon from "@mui/icons-material/Dns";
import { useAuth } from "../context/AuthContext";
import { useSettings } from "../context/SettingsContext";

export default function LoginPage() {
  const { login } = useAuth();
  const { settings } = useSettings();
  const navigate = useNavigate();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      navigate("/");
    } catch {
      setError("Invalid username or password");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        bgcolor: "grey.100",
      }}
    >
      <Paper sx={{ p: 4, width: 360 }} elevation={3}>
        <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 1 }}>
          <Avatar
            variant="rounded"
            src={settings.logo_url ?? undefined}
            sx={{
              width: 40,
              height: 40,
              background: settings.logo_url ? undefined : "linear-gradient(135deg, #4f46e5, #0d9488)",
            }}
          >
            {!settings.logo_url && <DnsIcon fontSize="small" />}
          </Avatar>
          <Typography variant="h5" sx={{ mb: 0 }}>
            {settings.platform_title}
          </Typography>
        </Stack>
        <Typography variant="body2" color="text.secondary" gutterBottom>
          Sign in with your local account
        </Typography>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2, display: "flex", flexDirection: "column", gap: 2 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoFocus
            required
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <Button type="submit" variant="contained" disabled={submitting}>
            {submitting ? "Signing in..." : "Sign In"}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
