"""Routes for per-product AI agent configuration.

All routes require MANAGE_PRODUCTS permission:
  - business_owner   → passes automatically (implicit full access)
  - business_staff   → must have manage_products in their permissions list

Flow:
  POST  → select a template (replicates defaults → creates agent_config)
  GET   → read current config
  PATCH → customise individual fields

URL pattern: /api/businesses/{business_id}/products/{product_id}/agent-config
"""

from fastapi import APIRouter, Depends
from app.controllers.agent_config_controller import AgentConfigController
from app.models.agent_config_schemas import (
    SelectTemplateRequest,
    UpdateAgentConfigRequest,
)
from app.utils.business_dependency import require_business_permission
from app.utils.constants import PERMISSIONS

router = APIRouter(prefix="/api/businesses", tags=["Agent Config"])
_controller = AgentConfigController()


@router.post("/{business_id}/products/{product_id}/agent-config", status_code=201)
async def select_template(
    business_id: str,
    product_id: str,
    data: SelectTemplateRequest,
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_PRODUCTS)),
):
    """Select an AI template and initialise agent config with template defaults."""
    return await _controller.select_template(product_id, data, biz)


@router.get("/{business_id}/products/{product_id}/agent-config")
async def get_config(
    business_id: str,
    product_id: str,
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_PRODUCTS)),
):
    """Get the AI agent config for a product."""
    return await _controller.get_config(product_id, biz)


@router.patch("/{business_id}/products/{product_id}/agent-config")
async def update_config(
    business_id: str,
    product_id: str,
    data: UpdateAgentConfigRequest,
    biz: dict = Depends(require_business_permission(PERMISSIONS.MANAGE_PRODUCTS)),
):
    """Customise individual fields of the agent config."""
    return await _controller.update_config(product_id, data, biz)
