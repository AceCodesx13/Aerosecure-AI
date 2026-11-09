import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";

function getTodayDate() {
  const date = new Date();
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 10);
}

const initialForm = {
  aircraft_part_id: "",
  scenario_date: getTodayDate(),
  replacement_interval_hours: "",
  hours_since_replacement: "",
  projected_daily_flight_hours: "",
  buffer_days: "",
  destination_region_id: "",
  shipment_restriction_classification: "",
  authorization_status: "",
  condition: "New",
};

const textFields = [
  { name: "aircraft_part_id", label: "Aircraft part ID" },
  { name: "destination_region_id", label: "Destination region ID" },
  {
    name: "shipment_restriction_classification",
    label: "Shipment restriction classification",
  },
  { name: "authorization_status", label: "Authorization status" },
  { name: "condition", label: "Condition" },
];

const numberFields = [
  {
    name: "replacement_interval_hours",
    label: "Replacement interval (hours)",
    min: 0.01,
  },
  {
    name: "hours_since_replacement",
    label: "Hours since replacement",
    min: 0,
  },
  {
    name: "projected_daily_flight_hours",
    label: "Projected daily flight hours",
    min: 0.01,
  },
  { name: "buffer_days", label: "Buffer (days)", min: 0 },
];

function displayOrDash(value) {
  return value ?? "—";
}

function displayDays(value) {
  return value == null ? "—" : `${value} days`;
}

function getDecisionStatus(result) {
  if (result.decision === "Recommend") {
    return {
      label: "Recommend",
      color: "success",
      background: "#edf7f1",
      description: "A supplier meets the current policy and timing criteria.",
    };
  }

  const options = result.options ?? [];
  const allBlocked =
    options.length > 0 &&
    options.every((option) => option.policy_decision === "Blocked");

  if (allBlocked) {
    return {
      label: "Blocked",
      color: "error",
      background: "#fdf0f0",
      description: "Shipment policy blocks all evaluated suppliers.",
    };
  }

  const reason = result.decision.replace(/^Escalate:\s*/, "");

  return {
    label: "Escalate",
    color: "warning",
    background: "#fff7e8",
    description: reason ? `${reason}.` : "The request needs further review.",
  };
}

export default function SupplierRecommendationPage() {
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const decisionStatus = result ? getDecisionStatus(result) : null;
  const selectedOption = result?.options?.find(
    (option) => option.supplier_id === result.supplier_id,
  );

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    const payload = {
      ...form,
      replacement_interval_hours: Number(form.replacement_interval_hours),
      hours_since_replacement: Number(form.hours_since_replacement),
      projected_daily_flight_hours: Number(
        form.projected_daily_flight_hours,
      ),
      buffer_days: Number(form.buffer_days),
    };

    try {
      const response = await fetch("/api/maintenance/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const responseBody = await response.json().catch(() => null);

      if (!response.ok) {
        const detail = responseBody?.detail;
        const message = Array.isArray(detail)
          ? detail.map((issue) => issue.msg).join("; ")
          : detail || `Request failed (${response.status})`;

        throw new Error(message);
      }

      setResult(responseBody);
    } catch (requestError) {
      setError(
        requestError.message || "Could not get a supplier recommendation.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="overline" color="secondary.main">
          AEROSECURE AI
        </Typography>
        <Typography variant="h4" component="h1" fontWeight={700}>
          Supplier Recommendation
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 0.5 }}>
          Enter maintenance and shipment details to compare supplier options.
        </Typography>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}

      <Paper
        component="form"
        variant="outlined"
        onSubmit={handleSubmit}
        sx={{ p: 3 }}
      >
        <Stack spacing={3}>
          <Typography variant="h6">Maintenance details</Typography>

          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: { xs: "1fr", sm: "repeat(2, 1fr)" },
              gap: 2,
            }}
          >
            <TextField
              name="scenario_date"
              label="Scenario date"
              type="date"
              value={form.scenario_date}
              onChange={handleChange}
              slotProps={{ inputLabel: { shrink: true } }}
              required
              fullWidth
            />

            {textFields.map((field) => (
              <TextField
                key={field.name}
                name={field.name}
                label={field.label}
                value={form[field.name]}
                onChange={handleChange}
                required
                fullWidth
              />
            ))}

            {numberFields.map((field) => (
              <TextField
                key={field.name}
                name={field.name}
                label={field.label}
                type="number"
                value={form[field.name]}
                onChange={handleChange}
                inputProps={{ min: field.min, step: "any" }}
                required
                fullWidth
              />
            ))}
          </Box>

          <Button type="submit" variant="contained" disabled={loading}>
            {loading ? "Getting recommendation…" : "Recommend supplier"}
          </Button>
        </Stack>
      </Paper>

      {result && (
        <Stack spacing={2}>
          <Paper
            variant="outlined"
            sx={{
              p: { xs: 2, md: 3 },
              borderLeft: 4,
              borderLeftColor: `${decisionStatus.color}.main`,
              bgcolor: (theme) =>
                theme.palette.mode === "dark"
                    ? "background.paper"
                    : decisionStatus.background,
            }}
          >
            <Stack
              direction="row"
              alignItems="center"
              justifyContent="space-between"
              flexWrap="wrap"
              gap={1}
            >
              <Typography variant="h5" fontWeight={700}>
                {result.decision}
              </Typography>
              <Chip
                label={decisionStatus.label}
                color={decisionStatus.color}
                sx={{ fontWeight: 700 }}
              />
            </Stack>

            <Typography color="text.secondary" sx={{ mt: 0.5 }}>
              {decisionStatus.description}
            </Typography>

            {result.supplier_name || result.supplier_id ? (
              <Paper
                variant="outlined"
                sx={{ mt: 2, p: 2, bgcolor: "background.paper" }}
              >
                <Typography variant="overline" color="text.secondary">
                  {result.decision === "Recommend"
                    ? "Recommended supplier"
                    : "Fastest available supplier"}
                </Typography>
                <Typography variant="h6">
                  {result.supplier_name ?? result.supplier_id}
                </Typography>

                <Box
                  sx={{
                    display: "grid",
                    gridTemplateColumns: {
                      xs: "1fr",
                      sm: "repeat(4, 1fr)",
                    },
                    gap: 2,
                    mt: 2,
                  }}
                >
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Need date
                    </Typography>
                    <Typography fontWeight={600}>
                      {displayOrDash(result.need_date)}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Latest order date
                    </Typography>
                    <Typography fontWeight={600}>
                      {displayOrDash(result.latest_order_date)}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Conservative lead time
                    </Typography>
                    <Typography fontWeight={600}>
                      {displayDays(
                        selectedOption?.conservative_lead_time_days,
                      )}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Lead-time source
                    </Typography>
                    <Typography fontWeight={600}>
                      {displayOrDash(result.lead_time_source)}
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            ) : (
              <Alert severity={decisionStatus.color} sx={{ mt: 2 }}>
                No supplier was selected.
              </Alert>
            )}
          </Paper>

          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="h6" sx={{ p: 1 }}>
              Supplier options
            </Typography>

            {result.options?.length ? (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Supplier</TableCell>
                      <TableCell>Policy decision</TableCell>
                      <TableCell>Conservative lead time</TableCell>
                      <TableCell>Latest order date</TableCell>
                      <TableCell>Result</TableCell>
                    </TableRow>
                  </TableHead>

                  <TableBody>
                    {result.options.map((option, index) => (
                      <TableRow
                        key={`${option.supplier_id}-${index}`}
                        hover
                      >
                        <TableCell>
                          {option.supplier_name ?? option.supplier_id}
                        </TableCell>
                        <TableCell>{option.policy_decision}</TableCell>
                        <TableCell>
                          {displayDays(
                            option.conservative_lead_time_days,
                          )}
                        </TableCell>
                        <TableCell>
                          {displayOrDash(option.latest_order_date)}
                        </TableCell>
                        <TableCell>{option.result}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Typography color="text.secondary" sx={{ p: 1 }}>
                No supplier options were returned.
              </Typography>
            )}
          </Paper>
        </Stack>
      )}
    </Stack>
  );
}