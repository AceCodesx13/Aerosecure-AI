from ..schemas.prediction import PredictionRequest, PredictionResponse


def predict_delivery(request: PredictionRequest) -> PredictionResponse:
    # Temporary placeholder until the trained model is connected
    predicted_days = request.quoted_lead_time_days
    conservative_days = predicted_days + 5

    return PredictionResponse(
        predicted_delivery_days=predicted_days,
        conservative_delivery_days=conservative_days,
        model_source="temporary-placeholder",
    )