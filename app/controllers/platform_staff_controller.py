from app.services.platform_staff_implementation import PlatformStaffImplementation
from app.models.staff_schemas import (
    InvitePlatformStaffRequest,
    UpdatePlatformStaffPermissionsRequest,
    UpdateStaffStatusRequest,
)
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES

_impl = PlatformStaffImplementation()


class PlatformStaffController:

    async def invite(self, data: InvitePlatformStaffRequest) -> dict:
        try:
            return await _impl.invite(data)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def list_staff(self) -> dict:
        try:
            return await _impl.list_staff()
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def update_permissions(
        self, user_id: str, data: UpdatePlatformStaffPermissionsRequest
    ) -> dict:
        try:
            return await _impl.update_permissions(user_id, data)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def update_status(self, user_id: str, data: UpdateStaffStatusRequest) -> dict:
        try:
            return await _impl.update_status(user_id, data)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)
