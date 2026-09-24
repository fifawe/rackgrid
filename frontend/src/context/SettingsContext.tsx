import React, { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getPublicSettings } from "../api/settings";
import { PublicSettings } from "../types";

const DEFAULT_SETTINGS: PublicSettings = {
  platform_title: "Asset Inventory Platform",
  logo_url: null,
  version: "",
};

interface SettingsContextValue {
  settings: PublicSettings;
  refresh: () => Promise<void>;
}

const SettingsContext = createContext<SettingsContextValue | undefined>(undefined);

/**
 * Fetches the platform's branding (title/logo) and running version once
 * on load and shares it app-wide - the sidebar, the login page (reached
 * before anyone is signed in, which is why GET /settings/public itself
 * requires no auth), and the Dashboard's version caption all read from
 * here instead of each doing their own fetch.
 */
export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<PublicSettings>(DEFAULT_SETTINGS);

  const refresh = useCallback(async () => {
    try {
      const data = await getPublicSettings();
      setSettings(data);
    } catch {
      // Non-fatal: the app still works with the default title/no logo.
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return <SettingsContext.Provider value={{ settings, refresh }}>{children}</SettingsContext.Provider>;
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used within SettingsProvider");
  return ctx;
}
