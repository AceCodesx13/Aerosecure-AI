from fastapi import APIRouter

from ...schemas.prediction import PredictionRequest, PredictionResponse
from ...services.model_service import predict_delivery

router = APIRouter(tags=["Prediction"])


@router.post("/predict", response_model=PredictionResponse)
def create_prediction(request: PredictionRequest) -> PredictionResponse:
    return predict_delivery(request)