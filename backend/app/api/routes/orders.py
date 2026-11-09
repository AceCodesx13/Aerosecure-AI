from fastapi import APIRouter, Header, HTTPException, Query

from ...schemas.orders import OrdersResponse
from ...services import access_service

router = APIRouter(tags=["Orders"])


# TODO: replace headers with real login
@router.get("/orders", response_model=OrdersResponse)
def list_orders(
    x_user: str = Header(),
    x_role: str = Header(),
    limit: int = Query(default=50, ge=1, le=500),
) -> OrdersResponse:
    # log first so bad roles still get logged
    visible = access_service.get_orders_for(x_user, x_role)

    if not access_service.is_known_role(x_role):
        raise HTTPException(status_code=403, detail="Unknown role")

    return OrdersResponse(
        user=x_user,
        role=x_role,
        visible_count=len(visible),
        returned=min(limit, len(visible)),
        orders=visible[:limit],
    )
