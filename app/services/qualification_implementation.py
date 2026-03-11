"""Business logic for per-product lead qualification flows.

Each product gets one qualification flow that defines the questions,
scoring thresholds (hot / warm / cold), and trigger rules.
The service auto-computes `max_possible_score` from question options.
"""

from datetime import datetime, timezone
from bson import ObjectId
from app.queries.qualification_queries import QualificationQueries
from app.queries.product_queries import ProductQueries
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES
from app.models.qualification_schemas import (
    CreateQualificationFlowRequest,
    UpdateQualificationFlowRequest,
)


def _compute_max_score(questions: list[dict]) -> float:
    """Sum the highest option score for each question."""
    total = 0.0
    for q in questions:
        if q.get("options"):
            total += max(opt["score"] for opt in q["options"])
        elif q.get("text_score_default") is not None:
            total += q["text_score_default"]
    return total


def _serialize_flow(f: dict) -> dict:
    """Convert a MongoDB qualification_flows document to a JSON-safe dict."""
    return {
        "id": str(f["_id"]),
        "business_id": str(f["business_id"]),
        "product_id": str(f["product_id"]),
        "is_enabled": f.get("is_enabled", False),
        "trigger_type": f.get("trigger_type"),
        "trigger_keywords": f.get("trigger_keywords", []),
        "questions": f.get("questions", []),
        "max_possible_score": f.get("max_possible_score", 0),
        "hot_threshold": f.get("hot_threshold"),
        "warm_threshold": f.get("warm_threshold"),
        "hot_lead_action": f.get("hot_lead_action"),
        "warm_lead_action": f.get("warm_lead_action"),
        "cold_lead_action": f.get("cold_lead_action"),
        "created_at": f["created_at"].isoformat() if f.get("created_at") else None,
        "updated_at": f["updated_at"].isoformat() if f.get("updated_at") else None,
    }


class QualificationImplementation:
    """Manage the qualification flow for a specific product."""

    async def create_or_update_flow(
        self,
        product_id: str,
        data: CreateQualificationFlowRequest,
        business_context: dict,
    ) -> dict:
        try:
            biz_id = business_context["business_id"]
            biz_slug = business_context["business_slug"]
            prod_oid = ObjectId(product_id)

            # ── Verify product ownership ─────────────────────────────
            product = await ProductQueries.find_by_id(prod_oid, biz_id)
            if not product:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.PRODUCT_NOT_FOUND
                )

            # Serialize questions and compute max score
            questions_data = [q.model_dump() for q in data.questions]
            max_score = _compute_max_score(questions_data)

            now = datetime.now(timezone.utc)
            flow = await QualificationQueries.upsert(biz_id, prod_oid, {
                "business_id": biz_id,
                "business_slug": biz_slug,
                "product_id": prod_oid,
                "is_enabled": data.is_enabled,
                "trigger_type": data.trigger_type,
                "trigger_keywords": data.trigger_keywords,
                "questions": questions_data,
                "max_possible_score": max_score,
                "hot_threshold": data.hot_threshold,
                "warm_threshold": data.warm_threshold,
                "hot_lead_action": data.hot_lead_action,
                "warm_lead_action": data.warm_lead_action,
                "cold_lead_action": data.cold_lead_action,
                "created_at": now,
                "updated_at": now,
            })

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"qualification_flow": _serialize_flow(flow)},
                MESSAGES.QUALIFICATION_SAVED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def get_flow(self, product_id: str, business_context: dict) -> dict:
        try:
            biz_id = business_context["business_id"]
            prod_oid = ObjectId(product_id)

            product = await ProductQueries.find_by_id(prod_oid, biz_id)
            if not product:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.PRODUCT_NOT_FOUND
                )

            flow = await QualificationQueries.find_by_product(biz_id, prod_oid)
            if not flow:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.QUALIFICATION_NOT_FOUND
                )

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"qualification_flow": _serialize_flow(flow)},
                MESSAGES.SUCCESS,
            )

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
            biz_id = business_context["business_id"]
            prod_oid = ObjectId(product_id)

            product = await ProductQueries.find_by_id(prod_oid, biz_id)
            if not product:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.PRODUCT_NOT_FOUND
                )

            existing = await QualificationQueries.find_by_product(biz_id, prod_oid)
            if not existing:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.QUALIFICATION_NOT_FOUND
                )

            update_data = data.model_dump(exclude_none=True)
            if not update_data:
                ResponseService.status = CODE.BAD_REQUEST
                return ResponseService.response_service(
                    STATUS.FAILURE, None, MESSAGES.INVALID_PARAMETERS
                )

            # Serialize questions + recompute max score if questions changed
            if "questions" in update_data:
                update_data["questions"] = [
                    q.model_dump() if hasattr(q, "model_dump") else q
                    for q in update_data["questions"]
                ]
                update_data["max_possible_score"] = _compute_max_score(
                    update_data["questions"]
                )

            update_data["updated_at"] = datetime.now(timezone.utc)
            updated = await QualificationQueries.update(biz_id, prod_oid, update_data)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"qualification_flow": _serialize_flow(updated)},
                MESSAGES.QUALIFICATION_SAVED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )
