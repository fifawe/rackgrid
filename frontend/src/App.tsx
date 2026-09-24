import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { SettingsProvider } from "./context/SettingsContext";
import ProtectedRoute from "./components/common/ProtectedRoute";
import Layout from "./components/layout/Layout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import InventoryPage from "./pages/InventoryPage";
import AssetDetailsPage from "./pages/AssetDetailsPage";
import AuditPage from "./pages/AuditPage";
import JobManagementPage from "./pages/JobManagementPage";
import SitesPage from "./pages/SitesPage";
import SupportTeamsPage from "./pages/SupportTeamsPage";
import SettingsPage from "./pages/SettingsPage";
import DataTransferPage from "./pages/DataTransferPage";

export default function App() {
  return (
    <BrowserRouter>
      <SettingsProvider>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<DashboardPage />} />
              <Route path="inventory" element={<InventoryPage />} />
              <Route path="inventory/:assetId" element={<AssetDetailsPage />} />
              <Route path="sites" element={<SitesPage />} />
              <Route path="support-teams" element={<SupportTeamsPage />} />
              <Route path="audit" element={<AuditPage />} />
              <Route path="jobs" element={<JobManagementPage />} />
              <Route path="data" element={<DataTransferPage />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </SettingsProvider>
    </BrowserRouter>
  );
}
