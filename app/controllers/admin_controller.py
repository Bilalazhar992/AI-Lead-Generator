from app.services.admin_implementation import AdminImplementation
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES

_impl = AdminImplementation()


class AdminController:

    async def list_businesses(self) -> dict:
        try:
            return await _impl.list_businesses()
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_business(self, business_id: str) -> dict:
        try:
            return await _impl.get_business(business_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_business_subscription(self, business_id: str) -> dict:
        try:
            return await _impl.get_business_subscription(business_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_business_products(self, business_id: str) -> dict:
        try:
            return await _impl.get_business_products(business_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    

    async def get_business_staff(self, business_id: str) -> dict:
        try:
            return await _impl.get_business_staff(business_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)
