"""Business logic for AI template management.

Accessible to super_admin and platform_staff with MANAGE_AI_TEMPLATES permission.
Business owners can list active templates (read-only) to pick one during agent config.
"""

from datetime import datetime, timezone
from bson import ObjectId
from app.queries.ai_template_queries import AITemplateQueries
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES
from app.models.ai_template_schemas import CreateTemplateRequest, UpdateTemplateRequest


def _serialize_template(t: dict) -> dict:
    """Convert a MongoDB ai_templates document to a JSON-safe dict."""
    return {
        "id": str(t["_id"]),
        "template_id": t["template_id"],
        "name": t["name"],
        "description": t["description"],
        "icon": t.get("icon"),
        "system_prompt_template": t["system_prompt_template"],
        "default_tone": t["default_tone"],
        "default_personality_traits": t.get("default_personality_traits", []),
        "default_primary_goal": t["default_primary_goal"],
        "default_greeting_message": t["default_greeting_message"],
        "default_fallback_message": t["default_fallback_message"],
        "default_meeting_cta_message": t.get("default_meeting_cta_message"),
        "default_avoid_topics": t.get("default_avoid_topics", []),
        "default_handoff_keywords": t.get("default_handoff_keywords", []),
        "suggested_questions": t.get("suggested_questions", []),
        "is_active": t["is_active"],
        "created_by": str(t["created_by"]) if t.get("created_by") else None,
        "created_at": t["created_at"].isoformat() if t.get("created_at") else None,
        "updated_at": t["updated_at"].isoformat() if t.get("updated_at") else None,
    }


class AITemplateImplementation:
    """CRUD operations for AI agent templates."""

    async def create_template(
        self, data: CreateTemplateRequest, created_by: str
    ) -> dict:
        try:
            # ── Check template_id uniqueness ─────────────────────────
            existing = await AITemplateQueries.find_by_template_id(data.template_id)
            if existing:
                ResponseService.status = CODE.CONFLICT
                return ResponseService.response_service(
                    STATUS.DUPLICATE, None, MESSAGES.TEMPLATE_ID_EXISTS
                )

            now = datetime.now(timezone.utc)
            template = await AITemplateQueries.create({
                "template_id": data.template_id,
                "name": data.name,
                "description": data.description,
                "icon": data.icon,
                "system_prompt_template": data.system_prompt_template,
                "default_tone": data.default_tone,
                "default_personality_traits": data.default_personality_traits,
                "default_personality_traits": data.default_personality_traits,
                "default_primary_goal": data.default_primary_goal,
                "default_greeting_message": data.default_greeting_message,
                "default_fallback_message": data.default_fallback_message,
                "default_meeting_cta_message": data.default_meeting_cta_message,
                "default_avoid_topics": data.default_avoid_topics,
                "default_handoff_keywords": data.default_handoff_keywords,
                "suggested_questions": [
                    q.model_dump() for q in data.suggested_questions
                ],
                "is_active": data.is_active,
                "created_by": ObjectId(created_by),
                "created_at": now,
                "updated_at": now,
            })

            ResponseService.status = CODE.CREATED
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"template": _serialize_template(template)},
                MESSAGES.TEMPLATE_CREATED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def list_active_templates(self) -> dict:
        """Return all active templates. Used by business owners during agent config."""
        try:
            templates = await AITemplateQueries.find_all_active()

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"templates": [_serialize_template(t) for t in templates]},
                MESSAGES.SUCCESS,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def get_template(self, template_obj_id: str) -> dict:
        try:
            template = await AITemplateQueries.find_by_id(ObjectId(template_obj_id))
            if not template:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.TEMPLATE_NOT_FOUND
                )

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"template": _serialize_template(template)},
                MESSAGES.SUCCESS,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def update_template(
        self, template_obj_id: str, data: UpdateTemplateRequest
    ) -> dict:
        try:
            obj_id = ObjectId(template_obj_id)

            existing = await AITemplateQueries.find_by_id(obj_id)
            if not existing:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.TEMPLATE_NOT_FOUND
                )

            update_data = data.model_dump(exclude_none=True)
            if not update_data:
                ResponseService.status = CODE.BAD_REQUEST
                return ResponseService.response_service(
                    STATUS.FAILURE, None, MESSAGES.INVALID_PARAMETERS
                )

            # Serialize nested suggested_questions if present
            if "suggested_questions" in update_data:
                update_data["suggested_questions"] = [
                    q.model_dump() if hasattr(q, "model_dump") else q
                    for q in update_data["suggested_questions"]
                ]

            update_data["updated_at"] = datetime.now(timezone.utc)
            updated = await AITemplateQueries.update(obj_id, update_data)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"template": _serialize_template(updated)},
                MESSAGES.TEMPLATE_UPDATED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )
