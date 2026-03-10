from datetime import datetime, timezone
from bson import ObjectId
from app.queries.product_queries import ProductQueries
from app.utils.slug_helper import generate_slug, make_unique_slug
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS, PRODUCT_STATUS
from app.utils.messages import MESSAGES
from app.models.product_schemas import CreateProductRequest, UpdateProductRequest


def _serialize_product(p: dict) -> dict:
    return {
        "id": str(p["_id"]),
        "business_id": str(p["business_id"]),
        "slug": p["slug"],
        "name": p["name"],
        "description": p.get("description"),
        "website_url": p.get("website_url"),
        "status": p["status"],
        "created_by": str(p["created_by"]) if p.get("created_by") else None,
        "created_at": p["created_at"].isoformat(),
        "updated_at": p["updated_at"].isoformat(),
    }


class ProductImplementation:
    """Business logic for product CRUD with tenant isolation and plan limit enforcement."""

    async def create_product(self, data: CreateProductRequest, ctx: dict) -> dict:
        try:
            business_id = ctx["business_id"]
            business_slug = ctx["business_slug"]
            plan = ctx.get("plan")
            user_id = ctx["current_user"]["sub"]

            # Enforce max_products from subscription plan
            if plan:
                current_count = await ProductQueries.count_by_business(business_id)
                if current_count >= plan.get("max_products", 0):
                    ResponseService.status = CODE.FORBIDDEN
                    return ResponseService.response_service(STATUS.FORBIDDEN, None, MESSAGES.PRODUCT_LIMIT_REACHED)

            # Generate unique slug scoped to this business
            base_slug = generate_slug(data.name)
            slug = base_slug
            while await ProductQueries.slug_exists(business_id, slug):
                slug = make_unique_slug(base_slug)

            now = datetime.now(timezone.utc)
            product = await ProductQueries.create({
                "business_id": business_id,
                "business_slug": business_slug,
                "slug": slug,
                "name": data.name,
                "description": data.description,
                "website_url": data.website_url,
                "status": PRODUCT_STATUS.DRAFT,
                "created_by": ObjectId(user_id),
                "created_at": now,
                "updated_at": now,
            })

            ResponseService.status = CODE.CREATED
            return ResponseService.response_service(STATUS.SUCCESS, _serialize_product(product), MESSAGES.PRODUCT_CREATED)

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_all_products(self, ctx: dict) -> dict:
        try:
            business_id = ctx["business_id"]
            products = await ProductQueries.find_all_by_business(business_id)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                [_serialize_product(p) for p in products],
                MESSAGES.PRODUCTS_FETCHED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def get_product(self, product_id: str, ctx: dict) -> dict:
        try:
            business_id = ctx["business_id"]
            product = await ProductQueries.find_by_id(business_id, ObjectId(product_id))

            if not product:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(STATUS.NOT_FOUND, None, MESSAGES.PRODUCT_NOT_FOUND)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(STATUS.SUCCESS, _serialize_product(product), MESSAGES.PRODUCT_FETCHED)

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def update_product(self, product_id: str, data: UpdateProductRequest, ctx: dict) -> dict:
        try:
            business_id = ctx["business_id"]
            product = await ProductQueries.find_by_id(business_id, ObjectId(product_id))

            if not product:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(STATUS.NOT_FOUND, None, MESSAGES.PRODUCT_NOT_FOUND)

            update_data = {k: v for k, v in data.model_dump().items() if v is not None}
            if not update_data:
                ResponseService.status = CODE.BAD_REQUEST
                return ResponseService.response_service(STATUS.BAD_REQUEST, None, MESSAGES.INVALID_PARAMETERS)

            # Validate status value if provided
            if "status" in update_data and update_data["status"] not in PRODUCT_STATUS.ALL:
                ResponseService.status = CODE.BAD_REQUEST
                return ResponseService.response_service(
                    STATUS.BAD_REQUEST, None,
                    f"Invalid status. Must be one of: {', '.join(PRODUCT_STATUS.ALL)}",
                )

            # If name changed, regenerate slug
            if "name" in update_data:
                base_slug = generate_slug(update_data["name"])
                slug = base_slug
                existing = await ProductQueries.find_by_slug(business_id, slug)
                if existing and existing["_id"] != product["_id"]:
                    while await ProductQueries.slug_exists(business_id, slug):
                        slug = make_unique_slug(base_slug)
                else:
                    slug = base_slug
                update_data["slug"] = slug

            updated = await ProductQueries.update(business_id, ObjectId(product_id), update_data)
            if not updated:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(STATUS.NOT_FOUND, None, MESSAGES.PRODUCT_NOT_FOUND)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(STATUS.SUCCESS, _serialize_product(updated), MESSAGES.PRODUCT_UPDATED)

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def delete_product(self, product_id: str, ctx: dict) -> dict:
        try:
            business_id = ctx["business_id"]
            product = await ProductQueries.find_by_id(business_id, ObjectId(product_id))

            if not product:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(STATUS.NOT_FOUND, None, MESSAGES.PRODUCT_NOT_FOUND)

            await ProductQueries.delete(business_id, ObjectId(product_id))

            ResponseService.status = CODE.OK
            return ResponseService.response_service(STATUS.SUCCESS, None, MESSAGES.PRODUCT_DELETED)

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)
