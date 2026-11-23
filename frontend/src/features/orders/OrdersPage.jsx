import { useEffect, useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Chip,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { DataGrid } from "@mui/x-data-grid";

const API_LIMIT = 500;
const DASHBOARD_USER = "dashboard-user";

function formatLabel(value) {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatRole(role) {
  if (role === "administrator") {
    return "Admin";
  }

  return role.charAt(0).toUpperCase() + role.slice(1);
}

function SummaryCard({ label, value, detail, highlight = false }) {
  return (
    <Paper
      variant="outlined"
      sx={{
        p: { xs: 2, md: 2.5 },
        borderTop: 3,
        borderTopColor: highlight ? "secondary.main" : "divider",
        background: (theme) =>
            highlight
                ? `linear-gradient(120deg, ${theme.palette.background.paper} 55%, ${
                    theme.palette.mode === "dark" ? "rgba(22,140,140,0.18)" : "#eef8f7"
                })`
                : theme.palette.background.paper,
      }}
    >
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>

      <Typography
        variant="h4"
        component="p"
        fontWeight={700}
        sx={{
          mt: 1,
          color: highlight ? "primary.main" : "text.primary",
        }}
      >
        {value}
      </Typography>

      <Typography variant="caption" color="text.secondary">
        {detail}
      </Typography>
    </Paper>
  );
}

export default function OrdersPage() {
  const { role } = useOutletContext();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function loadOrders() {
      setLoading(true);
      setError("");
      setData(null);

      try {
        const response = await fetch(`/api/orders?limit=${API_LIMIT}`, {
          headers: {
            "x-user": DASHBOARD_USER,
            "x-role": role,
          },
          signal: controller.signal,
        });

        const result = await response.json().catch(() => null);

        if (!response.ok) {
          throw new Error(
            result?.detail ?? `Request failed (${response.status})`,
          );
        }

        setData(result);
      } catch (requestError) {
        if (requestError.name !== "AbortError") {
          setError(requestError.message || "Could not load orders.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadOrders();

    return () => controller.abort();
  }, [role, reloadKey]);

  const rows = useMemo(
    () =>
      (data?.orders ?? []).map((order, index) => ({
        ...order,
        id: order.order_id ?? order.id ?? `${role}-${index}`,
      })),
    [data, role],
  );

  const columns = useMemo(
    () =>
      Object.keys(data?.orders?.[0] ?? {}).map((field) => ({
        field,
        headerName: formatLabel(field),
        flex: 1,
        minWidth: 140,
      })),
    [data],
  );

  const roleLabel = formatRole(role);

  return (
    <Stack spacing={3}>
      <Box
        sx={{
          display: "flex",
          alignItems: { xs: "flex-start", sm: "center" },
          justifyContent: "space-between",
          gap: 2,
          flexWrap: "wrap",
        }}
      >
        <Box>
          <Typography variant="overline" color="secondary.main">
            OPERATIONS OVERVIEW
          </Typography>
          <Typography variant="h4" component="h1" fontWeight={700}>
            Orders
          </Typography>
          <Typography color="text.secondary" sx={{ mt: 0.5 }}>
            View orders available to the selected role.
          </Typography>
        </Box>

        <Stack direction="row" spacing={1} alignItems="center">
          <Chip
            label={`${roleLabel} view`}
            color="primary"
            variant="outlined"
          />
          <Button
            variant="outlined"
            onClick={() => setReloadKey((key) => key + 1)}
            disabled={loading}
          >
            Refresh
          </Button>
        </Stack>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}

      <Box
        sx={{
          display: "grid",
          gridTemplateColumns: { xs: "1fr", sm: "repeat(2, 1fr)" },
          gap: 2,
        }}
      >
        <SummaryCard
          label="Orders visible to this role"
          value={data ? data.visible_count.toLocaleString() : "—"}
          detail={`Total available to the ${roleLabel} role`}
          highlight
        />
        <SummaryCard
          label="Rows loaded"
          value={data ? data.returned.toLocaleString() : "—"}
          detail={`Up to ${API_LIMIT} rows are loaded into the table`}
        />
      </Box>

      <Paper variant="outlined" sx={{ overflow: "hidden" }}>
        <Box
          sx={{
            display: "flex",
            alignItems: { xs: "flex-start", sm: "center" },
            justifyContent: "space-between",
            gap: 1,
            flexWrap: "wrap",
            px: { xs: 2, md: 2.5 },
            py: 2,
            borderBottom: 1,
            borderColor: "divider",
          }}
        >
          <Box>
            <Typography variant="h6">Order records</Typography>
            <Typography variant="body2" color="text.secondary">
              {data
                ? `Showing ${data.returned.toLocaleString()} of ${data.visible_count.toLocaleString()} orders available to this role`
                : "Loading order records…"}
            </Typography>
          </Box>

          {data && (
            <Typography variant="caption" color="text.secondary">
              Role: {roleLabel}
            </Typography>
          )}
        </Box>

        <Box sx={{ height: 560, width: "100%" }}>
          <DataGrid
            rows={rows}
            columns={columns}
            loading={loading}
            pageSizeOptions={[10, 25, 50]}
            initialState={{
              pagination: { paginationModel: { pageSize: 25, page: 0 } },
            }}
            disableRowSelectionOnClick
            sx={{
                border: 0,
                "& .MuiDataGrid-cell": {
                    borderColor: "divider",
                },
            }}
          />
        </Box>
      </Paper>
    </Stack>
  );
}