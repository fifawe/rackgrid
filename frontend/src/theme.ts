import { Theme, ThemeOptions, createTheme } from "@mui/material";

export type ThemeMode = "light" | "dark";

const SHARED: ThemeOptions = {
  shape: { borderRadius: 12 },
  typography: {
    fontFamily: [
      "Inter",
      "-apple-system",
      "BlinkMacSystemFont",
      "Segoe UI",
      "Roboto",
      "Helvetica Neue",
      "Arial",
      "sans-serif",
    ].join(","),
    h4: { fontWeight: 700, letterSpacing: -0.5 },
    h5: { fontWeight: 700, letterSpacing: -0.3 },
    h6: { fontWeight: 600 },
    subtitle1: { fontWeight: 600 },
    button: { fontWeight: 600, textTransform: "none" },
  },
};

/**
 * Builds the light or dark MUI theme. Shared shape/typography/component
 * "shape" overrides live in SHARED above; only the palette (and the few
 * component overrides whose colors are palette-dependent, like the table
 * header background) differ between modes.
 */
export function buildTheme(mode: ThemeMode): Theme {
  const isDark = mode === "dark";

  return createTheme({
    ...SHARED,
    palette: isDark
      ? {
          mode: "dark",
          primary: { main: "#818cf8", light: "#a5b4fc", dark: "#6366f1" },
          secondary: { main: "#2dd4bf", light: "#5eead4", dark: "#14b8a6" },
          background: { default: "#12131c", paper: "#1a1c29" },
          text: { primary: "#e9e9f2", secondary: "#a3a1b8" },
          divider: "rgba(255, 255, 255, 0.08)",
        }
      : {
          mode: "light",
          primary: { main: "#4f46e5", light: "#818cf8", dark: "#3730a3" },
          secondary: { main: "#0d9488", light: "#2dd4bf", dark: "#0f766e" },
          background: { default: "#f4f5fa", paper: "#ffffff" },
          text: { primary: "#1e1b2e", secondary: "#65647d" },
          divider: "rgba(30, 27, 46, 0.08)",
        },
    components: {
      MuiPaper: {
        styleOverrides: {
          root: { backgroundImage: "none" },
          rounded: { borderRadius: 14 },
        },
        defaultProps: { elevation: 0 },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 14,
            border: isDark ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(30, 27, 46, 0.07)",
            boxShadow: isDark ? "0 1px 3px rgba(0,0,0,0.3)" : "0 1px 3px rgba(30,27,46,0.06)",
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            boxShadow: isDark ? "0 1px 2px rgba(0,0,0,0.4)" : "0 1px 2px rgba(30,27,46,0.06)",
          },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            borderRight: isDark ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(30, 27, 46, 0.07)",
            backgroundImage: "none",
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: { borderRadius: 10, paddingLeft: 16, paddingRight: 16 },
          contained: { boxShadow: "none" },
        },
      },
      MuiChip: {
        styleOverrides: { root: { fontWeight: 600 } },
      },
      MuiTableCell: {
        styleOverrides: {
          head: {
            fontWeight: 700,
            color: isDark ? "#a3a1b8" : "#65647d",
            backgroundColor: isDark ? "#20222f" : "#f9f9fd",
          },
        },
      },
      MuiTableRow: {
        styleOverrides: {
          root: {
            "&:hover": {
              backgroundColor: isDark ? "rgba(129, 140, 248, 0.08)" : "rgba(79, 70, 229, 0.04)",
            },
          },
        },
      },
    },
  });
}
