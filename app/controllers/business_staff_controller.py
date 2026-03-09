"""Thin HTTP controller for business staff operations."""

from app.services.business_staff_implementation import BusinessStaffImplementation
from app.models.staff_schemas import InviteBusinessStaffRequest
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES

_impl = BusinessStaffImplementation()


class BusinessStaffController:
    """Delegates all logic to BusinessStaffImplementation."""

    async def invite(
        self, data: InviteBusinessStaffRequest, owner_user_id: str
    ) -> dict:
        try:
            return await _impl.invite(data, owner_user_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )
