from app.services.business_staff_implementation import BusinessStaffImplementation
from app.models.staff_schemas import (
    InviteBusinessStaffRequest,
    UpdateBusinessStaffPermissionsRequest,
    UpdateStaffStatusRequest,
)
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES

_impl = BusinessStaffImplementation()


class BusinessStaffController:

    async def invite(
        self, data: InviteBusinessStaffRequest, owner_user_id: str, business_id: str
    ) -> dict:
        try:
            return await _impl.invite(data, owner_user_id, business_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def list_staff(self, biz: dict) -> dict:
        try:
            return await _impl.list_staff(biz)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def update_permissions(
        self, user_id: str, data: UpdateBusinessStaffPermissionsRequest, biz: dict
    ) -> dict:
        try:
            return await _impl.update_permissions(user_id, data, biz)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def update_status(
        self, user_id: str, data: UpdateStaffStatusRequest, biz: dict
    ) -> dict:
        try:
            return await _impl.update_status(user_id, data, biz)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )
