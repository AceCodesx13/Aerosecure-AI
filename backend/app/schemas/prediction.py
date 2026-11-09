from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    aircraft_model_id: str
    part_category_id: str
    supplier_id: str
    condition: str
    origin_region_id: str
    destination_region_id: str

    quantity_ordered: int = Field(gt=0)
    stock_at_acceptance: int = Field(ge=0)
    supplier_backlog_days: float = Field(ge=0)
    quoted_lead_time_days: float = Field(ge=0)
    route_transit_days: float = Field(ge=0)
    route_customs_days: float = Field(ge=0)
    order_month: int = Field(ge=1, le=12)


class PredictionResponse(BaseModel):
    predicted_delivery_days: float
    conservative_delivery_days: float
    model_source: str