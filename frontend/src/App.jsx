import { Navigate, Route, Routes} from "react-router-dom";
import { Paper, Stack, Typography } from "@mui/material";
import AppLayout from "./app/AppLayout.jsx";
import OrdersPage from "./features/orders/OrdersPage.jsx";
import PredictionPage from "./features/prediction/PredictionPage.jsx";
import SupplierRecommendationPage from "./features/supplier-recommendation/SupplierRecommendationPage.jsx";

function PlaceholderPage({ title, description }) {
  return (
    <Stack spacing={2}>
      <div>
        <Typography variant="overline" color="secondary.main">
          AEROSECURE AI
        </Typography>
        <Typography variant="h4" component="h1" fontWeight={700}>
          {title}
        </Typography>
        <Typography color="text.secondary" sx={{ mt: 1 }}>
          {description}
        </Typography>
      </div>

      <Paper variant="outlined" sx={{ p: 3 }}>
        <Typography color="text.secondary">
          This page is ready for its content.
        </Typography>
      </Paper>
    </Stack>
  );
}

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/orders" replace />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/prediction" element={<PredictionPage />} />
        <Route
          path="/supplier-recommendation"
          element={<SupplierRecommendationPage />}
        />
        <Route path="*" element={<Navigate to="/orders" replace />} />
      </Route>
    </Routes>
  );
}