"""Business logic for product CRUD (business-scoped).

Each product is an independent AI agent deployment. Products are
scoped to a business via business_id. The service enforces:
  - max_products limit from the subscription plan
  - auto-generated slugs with uniqueness retry
  - tenant-isolated reads/writes
"""

from datetime import datetime, timezone
from bson import ObjectId
from app.queries.product_queries import ProductQueries
from app.queries.agent_config_queries import AgentConfigQueries
from app.queries.qualification_queries import QualificationQueries
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES
from app.utils.slug_helper import generate_slug, make_unique_slug
from app.models.product_schemas import CreateProductRequest, UpdateProductRequest


def _serialize_product(p: dict) -> dict:
    """Convert a MongoDB product document to a JSON-safe dict."""
    return {
        "id": str(p["_id"]),
        "business_id": str(p["business_id"]),
        "name": p["name"],
        "slug": p["slug"],
        "description": p.get("description", ""),
        "website_url": p.get("website_url"),
        "is_active": p.get("is_active", True),
        "created_at": p["created_at"].isoformat() if p.get("created_at") else None,
        "updated_at": p["updated_at"].isoformat() if p.get("updated_at") else None,
    }


class ProductImplementation:
    """CRUD operations for business-scoped products."""

    async def create_product(
        self, data: CreateProductRequest, business_context: dict
    ) -> dict:
        """
        Create a product under the current business.
        - Enforces max_products from subscription plan.
        - Auto-generates a unique slug from the product name.
        """
        try:
            biz_id = business_context["business_id"]
            biz_slug = business_context["business_slug"]
            subscription = business_context.get("subscription")

            # ── Check product limit from subscription plan ───────────
            if subscription:
                from app.queries.subscription_queries import SubscriptionQueries
                plan = await SubscriptionQueries.find_plan_by_id(
                    subscription.get("plan_id")
                )
                if plan:
                    max_products = plan.get("max_products", 1)
                    current_count = await ProductQueries.count_by_business(biz_id)
                    if current_count >= max_products:
                        ResponseService.status = CODE.FORBIDDEN
                        return ResponseService.response_service(
                            STATUS.FAILURE, None, MESSAGES.PRODUCT_LIMIT_REACHED
                        )

            # ── Generate unique slug ─────────────────────────────────
            base_slug = generate_slug(data.name)
            slug = base_slug
            # If slug collision within this business, append random suffix
            if await ProductQueries.find_by_slug(slug, biz_id):
                slug = make_unique_slug(base_slug)

            now = datetime.now(timezone.utc)
            product = await ProductQueries.create({
                "business_id": biz_id,
                "business_slug": biz_slug,
                "name": data.name,
                "slug": slug,
                "description": data.description or "",
                "website_url": data.website_url,
                "is_active": data.is_active,
                "created_at": now,
                "updated_at": now,
            })

            ResponseService.status = CODE.CREATED
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"product": _serialize_product(product)},
                MESSAGES.PRODUCT_CREATED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def list_products(self, business_context: dict) -> dict:
        """List all products for the current business."""
        try:
            biz_id = business_context["business_id"]
            products = await ProductQueries.find_all_by_business(biz_id)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"products": [_serialize_product(p) for p in products]},
                MESSAGES.SUCCESS,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def get_product(self, product_id: str, business_context: dict) -> dict:
        """Get a single product by ID (tenant-isolated)."""
        try:
            biz_id = business_context["business_id"]
            product = await ProductQueries.find_by_id(ObjectId(product_id), biz_id)
            if not product:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.PRODUCT_NOT_FOUND
                )

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"product": _serialize_product(product)},
                MESSAGES.SUCCESS,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def update_product(
        self, product_id: str, data: UpdateProductRequest, business_context: dict
    ) -> dict:
        """Partial update — only non-null fields are written. Tenant-isolated."""
        try:
            biz_id = business_context["business_id"]
            prod_oid = ObjectId(product_id)

            existing = await ProductQueries.find_by_id(prod_oid, biz_id)
            if not existing:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.PRODUCT_NOT_FOUND
                )

            update_data = data.model_dump(exclude_none=True)
            if not update_data:
                ResponseService.status = CODE.BAD_REQUEST
                return ResponseService.response_service(
                    STATUS.FAILURE, None, MESSAGES.INVALID_PARAMETERS
                )

            # If name is changing, re-generate slug
            if "name" in update_data:
                base_slug = generate_slug(update_data["name"])
                slug = base_slug
                if await ProductQueries.find_by_slug(slug, biz_id):
                    # Only regenerate if it's a different product
                    slug_doc = await ProductQueries.find_by_slug(slug, biz_id)
                    if slug_doc and slug_doc["_id"] != prod_oid:
                        slug = make_unique_slug(base_slug)
                update_data["slug"] = slug

            update_data["updated_at"] = datetime.now(timezone.utc)
            updated = await ProductQueries.update(prod_oid, biz_id, update_data)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"product": _serialize_product(updated)},
                MESSAGES.PRODUCT_UPDATED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )

    async def delete_product(
        self, product_id: str, business_context: dict
    ) -> dict:
        """
        Delete a product and clean up its agent_config and qualification_flow.
        Tenant-isolated.
        """
        try:
            biz_id = business_context["business_id"]
            prod_oid = ObjectId(product_id)

            existing = await ProductQueries.find_by_id(prod_oid, biz_id)
            if not existing:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(
                    STATUS.NOT_FOUND, None, MESSAGES.PRODUCT_NOT_FOUND
                )

            # ── Clean up dependent resources ─────────────────────────
            await AgentConfigQueries.delete_by_product(biz_id, prod_oid)
            await QualificationQueries.delete_by_product(biz_id, prod_oid)

            # ── Delete the product ───────────────────────────────────
            await ProductQueries.delete(prod_oid, biz_id)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS, None, MESSAGES.PRODUCT_DELETED
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(
                STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION
            )
