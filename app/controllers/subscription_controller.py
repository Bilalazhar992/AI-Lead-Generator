from app.services.subscription_implementation import SubscriptionImplementation
from app.models.subscription_schemas import ChangePlanRequest
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES

_impl = SubscriptionImplementation()


class SubscriptionController:

    async def get_subscription(self, biz: dict) -> dict:
        try:
            return await _impl.get_subscription(biz)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def cancel_subscription(self, biz: dict) -> dict:
        try:
            return await _impl.cancel_subscription(biz)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def change_plan(self, biz: dict, data: ChangePlanRequest) -> dict:
        try:
            return await _impl.change_plan(biz, data)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)
