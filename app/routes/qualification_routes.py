"""Routes for per-product lead qualification flows.

All routes require MANAGE_PRODUCTS permission:
  - business_owner   → passes automatically (implicit full access)
  - business_staff   → must have manage_products in their permissions list
"""

from fastapi import APIRouter, Depends
from app.controllers.qualification_controller import QualificationController
from app.models.qualification_schemas import (
    CreateQualificationFlowRequest,
    UpdateQualificationFlowRequest,
)
from app.utils.business_dependency import require_business_permission
from app.utils.constants import PERMISSIONS

router = APIRouter(prefix="/api/products", tags=["Qualification Flows"])
_controller = QualificationController()


@router.put("/{product_id}/qualification")
async def create_or_update_flow(
    product_id: str,
    data: CreateQualificationFlowRequest,
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_PRODUCTS)),
):
    """Create or replace the qualification flow for a product."""
    return await _controller.create_or_update_flow(product_id, data, biz)


@router.get("/{product_id}/qualification")
async def get_flow(
    product_id: str,
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_PRODUCTS)),
):
    """Get the qualification flow for a product."""
    return await _controller.get_flow(product_id, biz)


@router.patch("/{product_id}/qualification")
async def update_flow(
    product_id: str,
    data: UpdateQualificationFlowRequest,
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_PRODUCTS)),
):
    """Partial update of the qualification flow for a product."""
    return await _controller.update_flow(product_id, data, biz)
