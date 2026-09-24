import React from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  AppBar,
  Avatar,
  Box,
  Chip,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import StorageIcon from "@mui/icons-material/Storage";
import HistoryIcon from "@mui/icons-material/History";
import ScheduleIcon from "@mui/icons-material/Schedule";
import LogoutIcon from "@mui/icons-material/Logout";
import DnsIcon from "@mui/icons-material/Dns";
import LanguageIcon from "@mui/icons-material/Language";
import SupportAgentIcon from "@mui/icons-material/SupportAgent";
import SettingsIcon from "@mui/icons-material/Settings";
import ImportExportIcon from "@mui/icons-material/ImportExport";
import { useAuth } from "../../context/AuthContext";
import { useSettings } from "../../context/SettingsContext";

const DRAWER_WIDTH = 232;

const NAV_ITEMS = [
  { label: "Dashboard", path: "/", icon: <DashboardIcon /> },
  { label: "Inventory", path: "/inventory", icon: <StorageIcon /> },
  { label: "Sites", path: "/sites", icon: <LanguageIcon /> },
  { label: "Support Team", path: "/support-teams", icon: <SupportAgentIcon /> },
  { label: "Audit", path: "/audit", icon: <HistoryIcon /> },
  { label: "Jobs", path: "/jobs", icon: <ScheduleIcon /> },
  { label: "Import / Export", path: "/data", icon: <ImportExportIcon /> },
];

// Settings is available to every role (Change Password, Dark Mode) - only
// the Platform Branding section within the page itself is Admin-gated.
const SETTINGS_NAV_ITEM = { label: "Settings", path: "/settings", icon: <SettingsIcon /> };

function initials(name: string | null | undefined): string {
  if (!name) return "?";
  return name.slice(0, 2).toUpperCase();
}

export default function Layout() {
  const { username, role, logout } = useAuth();
  const { settings } = useSettings();
  const navigate = useNavigate();

  return (
    <Box sx={{ display: "flex" }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          backgroundColor: "background.paper",
          color: "text.primary",
        }}
      >
        <Toolbar sx={{ justifyContent: "space-between" }}>
          <Stack direction="row" alignItems="center" spacing={1.5}>
            {settings.logo_url ? (
              <Box
                component="img"
                src={settings.logo_url}
                alt={settings.platform_title}
                sx={{ width: 34, height: 34, borderRadius: "10px", objectFit: "contain" }}
              />
            ) : (
              <Box
                sx={{
                  width: 34,
                  height: 34,
                  borderRadius: "10px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: "linear-gradient(135deg, #4f46e5, #0d9488)",
                  color: "#fff",
                }}
              >
                <DnsIcon fontSize="small" />
              </Box>
            )}
            <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 700 }}>
              {settings.platform_title}
            </Typography>
          </Stack>
          <Stack direction="row" alignItems="center" spacing={1.5}>
            <Chip
              size="small"
              label={role}
              color="primary"
              variant="outlined"
              sx={{ fontWeight: 600, borderRadius: "8px" }}
            />
            <Avatar sx={{ width: 32, height: 32, bgcolor: "primary.main", fontSize: 13 }}>
              {initials(username)}
            </Avatar>
            <Typography variant="body2" color="text.secondary">
              {username}
            </Typography>
            <Tooltip title="Log out">
              <IconButton
                color="inherit"
                onClick={() => {
                  logout();
                  navigate("/login");
                }}
              >
                <LogoutIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: DRAWER_WIDTH, boxSizing: "border-box" },
        }}
      >
        <Toolbar />
        <Divider />
        <List sx={{ px: 1.5, py: 2 }}>
          {NAV_ITEMS.map((item) => (
            <ListItemButton
              key={item.path}
              component={NavLink}
              to={item.path}
              end={item.path === "/"}
              sx={{
                borderRadius: "10px",
                mb: 0.5,
                color: "text.secondary",
                "&.active": {
                  backgroundColor: "primary.main",
                  color: "#fff",
                  "& .MuiListItemIcon-root": { color: "#fff" },
                  "&:hover": { backgroundColor: "primary.dark" },
                },
              }}
            >
              <ListItemIcon sx={{ minWidth: 36, color: "text.secondary" }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} primaryTypographyProps={{ fontWeight: 600, fontSize: 14 }} />
            </ListItemButton>
          ))}
          <Divider sx={{ my: 1 }} />
          <ListItemButton
            key={SETTINGS_NAV_ITEM.path}
            component={NavLink}
            to={SETTINGS_NAV_ITEM.path}
            sx={{
              borderRadius: "10px",
              mb: 0.5,
              color: "text.secondary",
              "&.active": {
                backgroundColor: "primary.main",
                color: "#fff",
                "& .MuiListItemIcon-root": { color: "#fff" },
                "&:hover": { backgroundColor: "primary.dark" },
              },
            }}
          >
            <ListItemIcon sx={{ minWidth: 36, color: "text.secondary" }}>{SETTINGS_NAV_ITEM.icon}</ListItemIcon>
            <ListItemText
              primary={SETTINGS_NAV_ITEM.label}
              primaryTypographyProps={{ fontWeight: 600, fontSize: 14 }}
            />
          </ListItemButton>
        </List>
      </Drawer>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: `calc(100% - ${DRAWER_WIDTH}px)`,
          minHeight: "100vh",
          backgroundColor: "background.default",
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}
