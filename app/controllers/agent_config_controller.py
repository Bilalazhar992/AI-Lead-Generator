"""Thin HTTP controller for agent configuration operations."""

from app.services.agent_config_implementation import AgentConfigImplementation
from app.models.agent_config_schemas import (
    SelectTemplateRequest,
    UpdateAgentConfigRequest,
)
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES

_impl = AgentConfigImplementation()


class AgentConfigController:
    """Delegates all logic to AgentConfigImplementation."""

    async def select_template(
        self,
        product_id: str,
        data: SelectTemplateRequest,
        business_context: dict,
    ) -> dict:
        try:
            return await _impl.select_template(product_id, data, business_context)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def get_config(self, product_id: str, business_context: dict) -> dict:
        try:
            return await _impl.get_config(product_id, business_context)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def update_config(
        self,
        product_id: str,
        data: UpdateAgentConfigRequest,
        business_context: dict,
    ) -> dict:
        try:
            return await _impl.update_config(product_id, data, business_context)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )
