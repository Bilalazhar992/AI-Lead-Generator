"""Database operations on the `products` collection.

All queries include `business_id` as a filter for tenant isolation.
"""

from bson import ObjectId
from app.database import get_database


class ProductQueries:
    """Database operations on `products` (business-scoped, tenant-isolated)."""

    @staticmethod
    def _col():
        return get_database()["products"]

    # ── Read ──────────────────────────────────────────────────────────

    @staticmethod
    async def find_by_id(product_id: ObjectId, business_id: ObjectId) -> dict | None:
        """Find a product by _id, scoped to the tenant's business_id."""
        return await ProductQueries._col().find_one({
            "_id": product_id,
            "business_id": business_id,
        })

    @staticmethod
    async def find_by_slug(slug: str, business_id: ObjectId) -> dict | None:
        return await ProductQueries._col().find_one({
            "slug": slug,
            "business_id": business_id,
        })

    @staticmethod
    async def find_all_by_business(business_id: ObjectId) -> list:
        """Return all products for a business, sorted by creation date."""
        cursor = ProductQueries._col().find(
            {"business_id": business_id}
        ).sort("created_at", -1)
        return await cursor.to_list(length=None)

    @staticmethod
    async def count_by_business(business_id: ObjectId) -> int:
        return await ProductQueries._col().count_documents({
            "business_id": business_id,
        })

    # ── Write ─────────────────────────────────────────────────────────

    @staticmethod
    async def create(data: dict) -> dict:
        result = await ProductQueries._col().insert_one(data)
        return await ProductQueries._col().find_one({"_id": result.inserted_id})

    @staticmethod
    async def update(
        product_id: ObjectId, business_id: ObjectId, data: dict
    ) -> dict | None:
        """Tenant-safe update: requires both _id and business_id to match."""
        result = await ProductQueries._col().update_one(
            {"_id": product_id, "business_id": business_id},
            {"$set": data},
        )
        if result.matched_count == 0:
            return None
        return await ProductQueries._col().find_one({
            "_id": product_id,
            "business_id": business_id,
        })

    @staticmethod
    async def delete(product_id: ObjectId, business_id: ObjectId) -> bool:
        """Tenant-safe hard delete. Returns True if a doc was deleted."""
        result = await ProductQueries._col().delete_one({
            "_id": product_id,
            "business_id": business_id,
        })
        return result.deleted_count > 0
