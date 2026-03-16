"""Own-profile routes — available to every authenticated user.

GET  /api/me  → returns user record + user_details merged
PATCH /api/me → updates name (users) and/or phone/avatar/language (user_details)

Any role can call these endpoints. The JWT itself identifies the user.
"""

from fastapi import APIRouter, Depends
from app.controllers.profile_controller import ProfileController
from app.models.user_schemas import UpdateProfileRequest
from app.utils.auth_dependency import get_current_user

router = APIRouter(prefix="/api/me", tags=["Profile"])
_controller = ProfileController()


@router.get("")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Get the signed-in user's own profile."""
    return await _controller.get_me(current_user["sub"])


@router.patch("")
async def update_profile(
    data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Update own profile fields.
    - first_name / last_name  → core identity (users collection)
    - phone / avatar_url / language  → extended profile (user_details collection)
    """
    return await _controller.update_me(current_user["sub"], data)
