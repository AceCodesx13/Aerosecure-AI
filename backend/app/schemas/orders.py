from pydantic import BaseModel


class OrdersResponse(BaseModel):
    user: str
    role: str
    visible_count: int
    returned: int
    orders: list[dict[str, str]]
