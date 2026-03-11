from app.services.business_implementation import BusinessImplementation
from app.models.business_schemas import BusinessOnboardRequest, BusinessUpdateRequest
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES

_impl = BusinessImplementation()


class BusinessController:
    """Thin HTTP layer — delegates all logic to BusinessImplementation."""

    async def onboard(self, data: BusinessOnboardRequest, owner_user_id: str) -> dict:
        try:
            return await _impl.onboard(data, owner_user_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_my_business(self, owner_user_id: str) -> dict:
        try:
            return await _impl.get_my_business(owner_user_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def update_my_business(self, data: BusinessUpdateRequest, owner_user_id: str) -> dict:
        try:
            return await _impl.update_my_business(data, owner_user_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_all_businesses(self, current_user: dict) -> dict:
        try:
            return await _impl.get_all_businesses(current_user)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_staff_business(self, staff_user_id: str) -> dict:
        try:
            return await _impl.get_staff_business(staff_user_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)
