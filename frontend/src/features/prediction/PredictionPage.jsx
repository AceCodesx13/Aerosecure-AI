import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

const initialForm = {
  aircraft_model_id: "",
  part_category_id: "",
  supplier_id: "",
  condition: "New",
  origin_region_id: "",
  destination_region_id: "",
  quantity_ordered: "1",
  stock_at_acceptance: "0",
  supplier_backlog_days: "0",
  quoted_lead_time_days: "0",
  route_transit_days: "0",
  route_customs_days: "0",
  order_month: String(new Date().getMonth() + 1),
};

const textFields = [
  { name: "aircraft_model_id", label: "Aircraft model ID" },
  { name: "part_category_id", label: "Part category ID" },
  { name: "supplier_id", label: "Supplier ID" },
  { name: "condition", label: "Condition" },
  { name: "origin_region_id", label: "Origin region ID" },
  { name: "destination_region_id", label: "Destination region ID" },
];

const numberFields = [
  { name: "quantity_ordered", label: "Quantity ordered", min: 1, step: 1 },
  { name: "stock_at_acceptance", label: "Stock at acceptance", min: 0, step: 1 },
  {
    name: "supplier_backlog_days",
    label: "Supplier backlog (days)",
    min: 0,
    step: "any",
  },
  {
    name: "quoted_lead_time_days",
    label: "Quoted lead time (days)",
    min: 0,
    step: "any",
  },
  {
    name: "route_transit_days",
    label: "Route transit time (days)",
    min: 0,
    step: "any",
  },
  {
    name: "route_customs_days",
    label: "Route customs time (days)",
    min: 0,
    step: "any",
  },
  { name: "order_month", label: "Order month", min: 1, max: 12, step: 1 },
];

function formatDays(value) {
  if (value == null || !Number.isFinite(Number(value))) {
    return "—";
  }

  return Number(value).toLocaleString(undefined, {
    maximumFractionDigits: 2,
  });
}

function formatSource(source) {
  if (source === "temporary-placeholder") {
    return "Temporary placeholder";
  }

  if (!source) {
    return "Unknown source";
  }

  return source
    .replaceAll("-", " ")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function PredictionMetric({ label, value, accent, description }) {
  return (
    <Paper
      variant="outlined"
      sx={{
        p: { xs: 2.5, md: 3 },
        height: "100%",
        bgcolor: "background.paper",
        borderTop: 3,
        borderTopColor: accent,
      }}
    >
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>

      <Typography
        variant="h3"
        component="p"
        fontWeight={700}
        sx={{ color: accent, mt: 1, letterSpacing: "-0.04em" }}
      >
        {formatDays(value)}
      </Typography>

      <Typography variant="body2" color="text.secondary">
        days
      </Typography>

      <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 2 }}>
        {description}
      </Typography>
    </Paper>
  );
}

export default function PredictionPage() {
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

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
      quantity_ordered: Number(form.quantity_ordered),
      stock_at_acceptance: Number(form.stock_at_acceptance),
      supplier_backlog_days: Number(form.supplier_backlog_days),
      quoted_lead_time_days: Number(form.quoted_lead_time_days),
      route_transit_days: Number(form.route_transit_days),
      route_customs_days: Number(form.route_customs_days),
      order_month: Number(form.order_month),
    };

    try {
      const response = await fetch("/api/predict", {
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
      setError(requestError.message || "Could not get a prediction.");
    } finally {
      setLoading(false);
    }
  }

  const isPlaceholder = result?.model_source === "temporary-placeholder";

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="overline" color="secondary.main">
          AEROSECURE AI
        </Typography>
        <Typography variant="h4" component="h1" fontWeight={700}>
          Delivery Prediction
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 0.5 }}>
          Enter supplier and route details to estimate delivery time.
        </Typography>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}

      <Paper
        component="form"
        variant="outlined"
        onSubmit={handleSubmit}
        sx={{ p: { xs: 2, md: 3 } }}
      >
        <Stack spacing={3}>
          <Box>
            <Typography variant="h6">Order details</Typography>
            <Typography variant="body2" color="text.secondary">
              Enter the order, supplier, and route information.
            </Typography>
          </Box>

          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: { xs: "1fr", sm: "repeat(2, 1fr)" },
              gap: 2,
            }}
          >
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
                inputProps={{
                  min: field.min,
                  max: field.max,
                  step: field.step,
                }}
                required
                fullWidth
              />
            ))}
          </Box>

          <Box>
            <Button type="submit" variant="contained" disabled={loading}>
              {loading ? "Getting prediction…" : "Get prediction"}
            </Button>
          </Box>
        </Stack>
      </Paper>

      {result && (
        <Paper variant="outlined" sx={{ overflow: "hidden" }}>
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: 2,
              p: { xs: 2, md: 3 },
              background:
                "linear-gradient(110deg, rgba(22,140,140,0.08), rgba(23,50,77,0.03))",
            }}
          >
            <Box>
              <Typography variant="overline" color="secondary.main">
                PREDICTION RESULT
              </Typography>
              <Typography variant="h5" fontWeight={700}>
                Estimated delivery time
              </Typography>
            </Box>

            <Chip
              label={formatSource(result.model_source)}
              color={isPlaceholder ? "warning" : "success"}
              variant="outlined"
              sx={{ fontWeight: 600 }}
            />
          </Box>

          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: { xs: "1fr", sm: "repeat(2, 1fr)" },
              gap: 2,
              p: { xs: 2, md: 3 },
            }}
          >
            <PredictionMetric
              label="Predicted delivery"
              value={result.predicted_delivery_days}
              accent="secondary.main"
              description="Estimated delivery time returned by the backend."
            />
            <PredictionMetric
              label="Conservative estimate"
              value={result.conservative_delivery_days}
              accent="primary.main"
              description="A cautious estimate returned by the backend."
            />
          </Box>

          {isPlaceholder && (
            <Box sx={{ px: { xs: 2, md: 3 }, pb: 2 }}>
              <Alert severity="info">
                This result uses the temporary placeholder service.
              </Alert>
            </Box>
          )}
        </Paper>
      )}
    </Stack>
  );
}