import React, { useRef, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import ImportExportIcon from "@mui/icons-material/ImportExport";
import DownloadIcon from "@mui/icons-material/Download";
import UploadFileIcon from "@mui/icons-material/UploadFile";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import { downloadInventoryBundle, importInventoryCsv } from "../api/data";
import { downloadAssetsCsv } from "../api/assets";
import { ImportResult } from "../types";
import { useAuth } from "../context/AuthContext";

export default function DataTransferPage() {
  const { hasRole } = useAuth();
  const canImport = hasRole("Editor");

  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleExportBundle = async () => {
    setExporting(true);
    setExportError(null);
    try {
      await downloadInventoryBundle();
    } catch {
      setExportError("Failed to export the inventory bundle");
    } finally {
      setExporting(false);
    }
  };

  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    setImportError(null);
    setResult(null);
    try {
      const data = await importInventoryCsv(file);
      setResult(data);
    } catch (err: any) {
      setImportError(err?.response?.data?.detail ?? "Failed to import the CSV file");
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  return (
    <Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 3 }}>
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
          <ImportExportIcon />
        </Box>
        <Box>
          <Typography variant="h4" sx={{ mb: 0 }}>
            Import / Export
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Download the full inventory and audit history, or bulk create/update assets from a CSV
          </Typography>
        </Box>
      </Box>

      <Paper sx={{ p: 3, mb: 3, maxWidth: 640 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
          Export
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Downloads a ZIP containing <code>inventory.csv</code> (full hardware, OS, and business detail
          for every asset) and <code>audit_log.csv</code> (the complete field-change history).
        </Typography>
        {exportError && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setExportError(null)}>
            {exportError}
          </Alert>
        )}
        <Stack direction="row" spacing={1.5}>
          <Button
            variant="contained"
            startIcon={exporting ? <CircularProgress size={16} color="inherit" /> : <DownloadIcon />}
            disabled={exporting}
            onClick={handleExportBundle}
          >
            Download Export Bundle (ZIP)
          </Button>
          <Button variant="outlined" startIcon={<DownloadIcon />} onClick={() => downloadAssetsCsv({})}>
            Inventory Only (CSV)
          </Button>
        </Stack>
      </Paper>

      <Paper sx={{ p: 3, maxWidth: 640 }}>
        <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
          Import
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Upload a CSV built to the same column layout the export above writes (export, edit in a
          spreadsheet, and re-import works out of the box).
        </Typography>
        <Alert severity="warning" sx={{ mb: 2 }}>
          A row whose Hostname / Serial Number / Primary IP doesn't match an existing asset{" "}
          <strong>creates a new asset</strong>. A row that does match can overwrite that asset's
          hardware and OS fields as well as its business metadata - not just business metadata. A{" "}
          <strong>blank cell on a matched row is left unchanged</strong> rather than clearing the
          existing value, so a partially-filled CSV won't wipe out data you didn't mean to touch.
        </Alert>

        {!canImport ? (
          <Alert severity="info">You need Editor access to import inventory data.</Alert>
        ) : (
          <>
            {importError && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setImportError(null)}>
                {importError}
              </Alert>
            )}
            <input ref={fileInputRef} type="file" accept=".csv" hidden onChange={handleFileSelected} />
            <Button
              variant="contained"
              startIcon={importing ? <CircularProgress size={16} color="inherit" /> : <UploadFileIcon />}
              disabled={importing}
              onClick={() => fileInputRef.current?.click()}
            >
              Choose CSV to Import
            </Button>

            {result && (
              <Box sx={{ mt: 3 }}>
                <Stack direction="row" spacing={1.5} sx={{ mb: 2 }}>
                  <Chip
                    icon={<CheckCircleIcon />}
                    color="success"
                    variant="outlined"
                    label={`${result.created} created`}
                  />
                  <Chip
                    icon={<CheckCircleIcon />}
                    color="primary"
                    variant="outlined"
                    label={`${result.updated} updated`}
                  />
                  {result.errors.length > 0 && (
                    <Chip
                      icon={<ErrorOutlineIcon />}
                      color="error"
                      variant="outlined"
                      label={`${result.errors.length} row${result.errors.length === 1 ? "" : "s"} skipped`}
                    />
                  )}
                </Stack>

                {result.errors.length > 0 && (
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Row</TableCell>
                          <TableCell>Error</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {result.errors.map((e, idx) => (
                          <TableRow key={idx}>
                            <TableCell>{e.row}</TableCell>
                            <TableCell>{e.message}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </Box>
            )}
          </>
        )}
      </Paper>
    </Box>
  );
}
