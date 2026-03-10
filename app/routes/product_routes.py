from fastapi import APIRouter, Depends
from app.controllers.product_controller import ProductController
from app.models.product_schemas import CreateProductRequest, UpdateProductRequest
from app.utils.auth_dependency import require_role
from app.utils.business_dependency import get_business_context
from app.utils.constants import ROLES

router = APIRouter(prefix="/api/products", tags=["Products"])
_controller = ProductController()


@router.post("", status_code=201)
async def create_product(
    data: CreateProductRequest,
    ctx: dict = Depends(get_business_context),
):
    """Create a new product (AI agent deployment) for this business."""
    return await _controller.create_product(data, ctx)


@router.get("")
async def get_all_products(
    ctx: dict = Depends(get_business_context),
):
    """List all products belonging to the caller's business."""
    return await _controller.get_all_products(ctx)


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    ctx: dict = Depends(get_business_context),
):
    """Get a single product by ID."""
    return await _controller.get_product(product_id, ctx)


@router.put("/{product_id}")
async def update_product(
    product_id: str,
    data: UpdateProductRequest,
    ctx: dict = Depends(get_business_context),
):
    """Update an existing product."""
    return await _controller.update_product(product_id, data, ctx)


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    ctx: dict = Depends(get_business_context),
):
    """Delete a product and all its associated configurations."""
    return await _controller.delete_product(product_id, ctx)
