from datetime import date

from pydantic import BaseModel, Field


class MaintenanceRequest(BaseModel):
    aircraft_part_id: str
    scenario_date: date
    replacement_interval_hours: float = Field(gt=0)
    hours_since_replacement: float = Field(ge=0)
    projected_daily_flight_hours: float = Field(gt=0)
    buffer_days: float = Field(ge=0)
    destination_region_id: str
    shipment_restriction_classification: str
    authorization_status: str
    condition: str = "New"


class SupplierOption(BaseModel):
    supplier_id: str
    supplier_name: str
    policy_decision: str
    conservative_lead_time_days: float | None
    latest_order_date: str | None
    result: str


class MaintenanceResponse(BaseModel):
    decision: str
    supplier_id: str | None
    supplier_name: str | None
    need_date: str | None
    latest_order_date: str | None
    lead_time_source: str | None
    options: list[SupplierOption]
