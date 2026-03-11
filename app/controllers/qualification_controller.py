"""Thin HTTP controller for qualification flow operations."""

from app.services.qualification_implementation import QualificationImplementation
from app.models.qualification_schemas import (
    CreateQualificationFlowRequest,
    UpdateQualificationFlowRequest,
)
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES

_impl = QualificationImplementation()


class QualificationController:
    """Delegates all logic to QualificationImplementation."""

    async def create_or_update_flow(
        self,
        product_id: str,
        data: CreateQualificationFlowRequest,
        business_context: dict,
    ) -> dict:
        try:
            return await _impl.create_or_update_flow(product_id, data, business_context)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def get_flow(self, product_id: str, business_context: dict) -> dict:
        try:
            return await _impl.get_flow(product_id, business_context)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def update_flow(
        self,
        product_id: str,
        data: UpdateQualificationFlowRequest,
        business_context: dict,
    ) -> dict:
        try:
            return await _impl.update_flow(product_id, data, business_context)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )
