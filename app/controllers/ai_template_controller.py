"""Thin HTTP controller for AI template operations."""

from app.services.ai_template_implementation import AITemplateImplementation
from app.models.ai_template_schemas import CreateTemplateRequest, UpdateTemplateRequest
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES

_impl = AITemplateImplementation()


class AITemplateController:
    """Delegates all logic to AITemplateImplementation."""

    async def create_template(
        self, data: CreateTemplateRequest, created_by: str
    ) -> dict:
        try:
            return await _impl.create_template(data, created_by)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def list_active_templates(self) -> dict:
        try:
            return await _impl.list_active_templates()
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def get_template(self, template_obj_id: str) -> dict:
        try:
            return await _impl.get_template(template_obj_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def update_template(
        self, template_obj_id: str, data: UpdateTemplateRequest
    ) -> dict:
        try:
            return await _impl.update_template(template_obj_id, data)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )
