from app.services.business_implementation import BusinessImplementation
from app.models.business_schemas import BusinessCreateRequest, BusinessUpdateRequest
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES

_impl = BusinessImplementation()


class BusinessController:

    async def create_business(self, data: BusinessCreateRequest, owner_user_id: str) -> dict:
        try:
            return await _impl.create_business(data, owner_user_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_my_businesses(self, owner_user_id: str) -> dict:
        try:
            return await _impl.get_my_businesses(owner_user_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_business_by_id(self, business_id: str, owner_user_id: str) -> dict:
        try:
            return await _impl.get_business_by_id(business_id, owner_user_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def update_business(
        self, business_id: str, data: BusinessUpdateRequest, owner_user_id: str
    ) -> dict:
        try:
            return await _impl.update_business(business_id, data, owner_user_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def delete_business(self, business_id: str, current_user: dict) -> dict:
        try:
            return await _impl.delete_business(business_id, current_user)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_staff_business(self, staff_user_id: str) -> dict:
        try:
            return await _impl.get_staff_business(staff_user_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)
