"""Thin HTTP controller for platform staff operations."""

from app.services.platform_staff_implementation import PlatformStaffImplementation
from app.models.staff_schemas import InvitePlatformStaffRequest
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES

_impl = PlatformStaffImplementation()


class PlatformStaffController:
    """Delegates all logic to PlatformStaffImplementation."""

    async def invite(self, data: InvitePlatformStaffRequest) -> dict:
        try:
            return await _impl.invite(data)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )
