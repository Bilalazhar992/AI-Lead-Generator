"""Routes for AI template management.

Admin routes (create, update) require MANAGE_AI_TEMPLATES permission —
accessible to super_admin and platform_staff with that permission.
List/get routes require authentication (any role) so business owners
can browse templates when configuring their agent.
"""

from fastapi import APIRouter, Depends
from app.controllers.ai_template_controller import AITemplateController
from app.models.ai_template_schemas import CreateTemplateRequest, UpdateTemplateRequest
from app.utils.auth_dependency import require_permission, get_current_user
from app.utils.constants import PERMISSIONS

router = APIRouter(tags=["AI Templates"])
_controller = AITemplateController()


# ── Admin routes (permission-gated) ──────────────────────────────────────

@router.post("/api/admin/ai-templates", status_code=201)
async def create_template(
    data: CreateTemplateRequest,
    current_user: dict = Depends(require_permission(PERMISSIONS.MANAGE_AI_TEMPLATES)),
):
    """Create a new AI agent template (requires manage_ai_templates permission)."""
    return await _controller.create_template(data, current_user["sub"])


@router.put("/api/admin/ai-templates/{template_id}")
async def update_template(
    template_id: str,
    data: UpdateTemplateRequest,
    current_user: dict = Depends(require_permission(PERMISSIONS.MANAGE_AI_TEMPLATES)),
):
    """Update an AI template (requires manage_ai_templates permission)."""
    return await _controller.update_template(template_id, data)


# ── Authenticated routes (any role) ─────────────────────────────────────

@router.get("/api/ai-templates")
async def list_templates(
    current_user: dict = Depends(get_current_user),
):
    """List all active AI templates (any authenticated user)."""
    return await _controller.list_active_templates()


@router.get("/api/ai-templates/{template_id}")
async def get_template(
    template_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get a single AI template by ID (any authenticated user)."""
    return await _controller.get_template(template_id)
