import React, { useEffect, useState } from "react";
import {
  Box,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { listAudit } from "../api/audit";
import { AuditRecord } from "../types";

export default function AuditPage() {
  const [items, setItems] = useState<AuditRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [assetId, setAssetId] = useState("");
  const [fieldName, setFieldName] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  useEffect(() => {
    listAudit({
      asset_id: assetId ? Number(assetId) : undefined,
      field_name: fieldName || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      offset: page * rowsPerPage,
      limit: rowsPerPage,
    }).then((data) => {
      setItems(data.items);
      setTotal(data.total);
    });
  }, [assetId, fieldName, dateFrom, dateTo, page, rowsPerPage]);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Audit History
      </Typography>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              label="Asset ID"
              value={assetId}
              onChange={(e) => {
                setPage(0);
                setAssetId(e.target.value);
              }}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              label="Field Name"
              value={fieldName}
              onChange={(e) => {
                setPage(0);
                setFieldName(e.target.value);
              }}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              label="From"
              type="date"
              InputLabelProps={{ shrink: true }}
              value={dateFrom}
              onChange={(e) => {
                setPage(0);
                setDateFrom(e.target.value);
              }}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              label="To"
              type="date"
              InputLabelProps={{ shrink: true }}
              value={dateTo}
              onChange={(e) => {
                setPage(0);
                setDateTo(e.target.value);
              }}
            />
          </Grid>
        </Grid>
      </Paper>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Asset ID</TableCell>
              <TableCell>Field</TableCell>
              <TableCell>Old Value</TableCell>
              <TableCell>New Value</TableCell>
              <TableCell>Date</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((a) => (
              <TableRow key={a.audit_id}>
                <TableCell>{a.asset_id}</TableCell>
                <TableCell>{a.field_name}</TableCell>
                <TableCell>{a.old_value ?? "-"}</TableCell>
                <TableCell>{a.new_value ?? "-"}</TableCell>
                <TableCell>{new Date(a.change_timestamp).toLocaleString()}</TableCell>
              </TableRow>
            ))}
            {items.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  No audit records found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      </TableContainer>
    </Box>
  );
}
