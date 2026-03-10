from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_database


class ProductQueries:
    """Database operations on the `products` collection.
    Every query is scoped by business_id for tenant isolation."""

    @staticmethod
    def _col():
        return get_database()["products"]

    @staticmethod
    async def create(data: dict) -> dict:
        result = await ProductQueries._col().insert_one(data)
        return await ProductQueries._col().find_one({"_id": result.inserted_id})

    @staticmethod
    async def find_all_by_business(business_id: ObjectId) -> list:
        cursor = ProductQueries._col().find({"business_id": business_id}).sort("created_at", -1)
        return await cursor.to_list(length=None)

    @staticmethod
    async def find_by_id(business_id: ObjectId, product_id: ObjectId) -> dict | None:
        return await ProductQueries._col().find_one({
            "_id": product_id,
            "business_id": business_id,
        })

    @staticmethod
    async def find_by_slug(business_id: ObjectId, slug: str) -> dict | None:
        return await ProductQueries._col().find_one({
            "business_id": business_id,
            "slug": slug,
        })

    @staticmethod
    async def slug_exists(business_id: ObjectId, slug: str) -> bool:
        doc = await ProductQueries._col().find_one(
            {"business_id": business_id, "slug": slug}, {"_id": 1}
        )
        return doc is not None

    @staticmethod
    async def count_by_business(business_id: ObjectId) -> int:
        return await ProductQueries._col().count_documents({"business_id": business_id})

    @staticmethod
    async def update(business_id: ObjectId, product_id: ObjectId, data: dict) -> dict | None:
        data["updated_at"] = datetime.now(timezone.utc)
        result = await ProductQueries._col().update_one(
            {"_id": product_id, "business_id": business_id},
            {"$set": data},
        )
        if result.matched_count == 0:
            return None
        return await ProductQueries._col().find_one({"_id": product_id})

    @staticmethod
    async def delete(business_id: ObjectId, product_id: ObjectId) -> bool:
        result = await ProductQueries._col().delete_one({
            "_id": product_id,
            "business_id": business_id,
        })
        return result.deleted_count > 0
