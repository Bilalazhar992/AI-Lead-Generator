"""Routes for product CRUD (business-scoped).

All routes require MANAGE_PRODUCTS permission:
  - business_owner   → passes automatically (implicit full access)
  - business_staff   → must have manage_products in their permissions list
"""

from fastapi import APIRouter, Depends
from app.controllers.product_controller import ProductController
from app.models.product_schemas import CreateProductRequest, UpdateProductRequest
from app.utils.business_dependency import require_business_permission
from app.utils.constants import PERMISSIONS

router = APIRouter(prefix="/api/products", tags=["Products"])
_controller = ProductController()


@router.post("", status_code=201)
async def create_product(
    data: CreateProductRequest,
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_PRODUCTS)),
):
    """Create a new product (enforces subscription plan product limit)."""
    return await _controller.create_product(data, biz)


@router.get("")
async def list_products(
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_PRODUCTS)),
):
    """List all products for the current business."""
    return await _controller.list_products(biz)


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_PRODUCTS)),
):
    """Get a single product by ID."""
    return await _controller.get_product(product_id, biz)


@router.put("/{product_id}")
async def update_product(
    product_id: str,
    data: UpdateProductRequest,
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_PRODUCTS)),
):
    """Update a product. Slug is re-generated if name changes."""
    return await _controller.update_product(product_id, data, biz)


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_PRODUCTS)),
):
    """Delete a product and its agent config / qualification flow."""
    return await _controller.delete_product(product_id, biz)
