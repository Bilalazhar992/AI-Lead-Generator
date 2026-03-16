

from app.services.subscription_plan_implementation import SubscriptionPlanImplementation
from app.models.subscription_schemas import CreatePlanRequest, UpdatePlanRequest
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES

_impl = SubscriptionPlanImplementation()


class SubscriptionPlanController:
    

    async def create_plan(self, data: CreatePlanRequest, created_by: str) -> dict:
        try:
            return await _impl.create_plan(data, created_by)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def list_active_plans(self) -> dict:
        try:
            return await _impl.list_active_plans()
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def get_plan(self, plan_id: str) -> dict:
        try:
            return await _impl.get_plan(plan_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def update_plan(self, plan_id: str, data: UpdatePlanRequest) -> dict:
        try:
            return await _impl.update_plan(plan_id, data)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def deactivate_plan(self, plan_id: str) -> dict:
        try:
            return await _impl.deactivate_plan(plan_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )
