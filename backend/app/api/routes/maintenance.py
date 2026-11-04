from fastapi import APIRouter

from ...schemas.maintenance import MaintenanceRequest, MaintenanceResponse
from ...services.maintenance_service import recommend

router = APIRouter(tags=["Maintenance"])


@router.post("/maintenance/recommend", response_model=MaintenanceResponse)
def recommend_supplier(request: MaintenanceRequest) -> MaintenanceResponse:
    return recommend(request)
