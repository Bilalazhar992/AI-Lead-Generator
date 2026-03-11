"""Business logic for per-product AI agent configuration.

Flow:
  1. select_template() — replicates all defaults from the AI template,
     fills in business-specific context (company_name, product info),
     and upserts the agent_config document.
  2. update_config()   — partial customization of individual fields.
  3. get_config()      — read the current config.
"""

from datetime import datetime, timezone
from bson import ObjectId
from app.queries.agent_config_queries import AgentConfigQueries
from app.queries.product_queries import ProductQueries
from app.queries.ai_template_queries import AITemplateQueries
from app.queries.business_queries import BusinessQueries
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES
from app.models.agent_config_schemas import (
    SelectTemplateRequest,
    UpdateAgentConfigRequest,
)


def _serialize_config(c: dict) -> dict:
    """Convert a MongoDB agent_configs document to a JSON-safe dict."""
    return {
        "id": str(c["_id"]),
        "business_id": str(c["business_id"]),
        "product_id": str(c["product_id"]),
        "template_id": c.get("template_id"),
        "company_name": c.get("company_name"),
        "product_name": c.get("product_name"),
        "product_description": c.get("product_description"),
        "target_audience": c.get("target_audience"),
        "pricing_info": c.get("pricing_info"),
        "tone": c.get("tone"),
        "personality_traits": c.get("personality_traits", []),
        "primary_goal": c.get("primary_goal"),
        "greeting_message": c.get("greeting_message"),
        "fallback_message": c.get("fallback_message"),
        "meeting_cta_message": c.get("meeting_cta_message"),
        "avoid_topics": c.get("avoid_topics", []),
        "never_say": c.get("never_say", []),
        "always_include": c.get("always_include", []),
        "handoff_enabled": c.get("handoff_enabled", False),
        "handoff_keywords": c.get("handoff_keywords", []),
        "handoff_after_messages": c.get("handoff_after_messages"),
        "handoff_message": c.get("handoff_message"),
        "created_at": c["created_at"].isoformat() if c.get("created_at") else None,
        "updated_at": c["updated_at"].isoformat() if c.get("updated_at") else None,
    }


class AgentConfigImplementation:
    """Manage the AI agent configuration for a specific product."""

    async def select_template(
        self,
        product_id: str,
        data: SelectTemplateRequest,
        business_context: dict,
    ) -> dict:
        """
        Select a template and create/replace the agent config for a product.

        Replicates all template defaults into the config and fills in
        business-level context (company name, product info).
        """
        try:
            biz_id = business_context["business_id"]
            biz_slug = business_context["business_slug"]
            prod_oid = ObjectId(product_id)

            # ── Verify product belongs to this business ──────────────
            product = await ProductQueries.find_by_id(prod_oid, biz_id)
            if not product:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.PRODUCT_NOT_FOUND
                )

            # ── Verify template exists and is active ─────────────────
            template = await AITemplateQueries.find_by_template_id(data.template_id)
            if not template or not template.get("is_active", False):
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.TEMPLATE_NOT_FOUND
                )

            # ── Resolve business info for context ────────────────────
            business = await BusinessQueries.find_by_id(biz_id)

            now = datetime.now(timezone.utc)

            # Replicate template defaults into the agent config
            config = await AgentConfigQueries.upsert(biz_id, prod_oid, {
                "business_id": biz_id,
                "business_slug": biz_slug,
                "product_id": prod_oid,
                "template_id": data.template_id,
                # Business context (from business + product)
                "company_name": business.get("business_name", "") if business else "",
                "product_name": product.get("name", ""),
                "product_description": product.get("description", ""),
                "target_audience": "",
                "pricing_info": "",
                # Replicated from template defaults
                "tone": template["default_tone"],
                "personality_traits": template.get("default_personality_traits", []),
                "primary_goal": template["default_primary_goal"],
                "greeting_message": template["default_greeting_message"],
                "fallback_message": template["default_fallback_message"],
                "meeting_cta_message": template.get("default_meeting_cta_message", ""),
                "avoid_topics": template.get("default_avoid_topics", []),
                "never_say": [],
                "always_include": [],
                "handoff_enabled": bool(template.get("default_handoff_keywords")),
                "handoff_keywords": template.get("default_handoff_keywords", []),
                "handoff_after_messages": None,
                "handoff_message": "",
                "created_at": now,
                "updated_at": now,
            })

            ResponseService.status = CODE.CREATED
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"agent_config": _serialize_config(config)},
                MESSAGES.AGENT_CONFIG_SAVED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def get_config(self, product_id: str, business_context: dict) -> dict:
        """Get the agent config for a product."""
        try:
            biz_id = business_context["business_id"]
            prod_oid = ObjectId(product_id)

            # ── Verify product belongs to this business ──────────────
            product = await ProductQueries.find_by_id(prod_oid, biz_id)
            if not product:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.PRODUCT_NOT_FOUND
                )

            config = await AgentConfigQueries.find_by_product(biz_id, prod_oid)
            if not config:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.AGENT_CONFIG_NOT_FOUND
                )

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"agent_config": _serialize_config(config)},
                MESSAGES.SUCCESS,
            )

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
        """
        Partial update on an existing agent config.
        If template_id is changed, re-select by calling select_template instead.
        """
        try:
            biz_id = business_context["business_id"]
            prod_oid = ObjectId(product_id)

            product = await ProductQueries.find_by_id(prod_oid, biz_id)
            if not product:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.PRODUCT_NOT_FOUND
                )

            existing = await AgentConfigQueries.find_by_product(biz_id, prod_oid)
            if not existing:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.AGENT_CONFIG_NOT_FOUND
                )

            update_data = data.model_dump(exclude_none=True)
            if not update_data:
                ResponseService.status = CODE.BAD_REQUEST
                return ResponseService.response_service(
                    STATUS.FAILURE, None, MESSAGES.INVALID_PARAMETERS
                )

            # If template_id is changing, re-replicate from the new template
            if "template_id" in update_data:
                template = await AITemplateQueries.find_by_template_id(
                    update_data["template_id"]
                )
                if not template or not template.get("is_active", False):
                    ResponseService.status = CODE.RECORD_NOT_FOUND
                    return ResponseService.response_service(
                        STATUS.NOT_FOUND, None, MESSAGES.TEMPLATE_NOT_FOUND
                    )
                # Re-replicate defaults (user can override individual fields in same PATCH)
                update_data.setdefault("tone", template["default_tone"])
                update_data.setdefault("personality_traits", template.get("default_personality_traits", []))
                update_data.setdefault("primary_goal", template["default_primary_goal"])
                update_data.setdefault("greeting_message", template["default_greeting_message"])
                update_data.setdefault("fallback_message", template["default_fallback_message"])
                update_data.setdefault("meeting_cta_message", template.get("default_meeting_cta_message", ""))
                update_data.setdefault("avoid_topics", template.get("default_avoid_topics", []))
                update_data.setdefault("handoff_keywords", template.get("default_handoff_keywords", []))

            update_data["updated_at"] = datetime.now(timezone.utc)
            updated = await AgentConfigQueries.update(biz_id, prod_oid, update_data)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"agent_config": _serialize_config(updated)},
                MESSAGES.AGENT_CONFIG_SAVED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )
