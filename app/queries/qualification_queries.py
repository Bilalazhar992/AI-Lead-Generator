"""Database operations on the `qualification_flows` collection (business-scoped)."""

from bson import ObjectId
from app.database import get_database


class QualificationQueries:
    """Queries for qualification flows — compound key (business_id, product_id)."""

    @staticmethod
    def _col():
        return get_database()["qualification_flows"]

    @staticmethod
    async def find_by_product(
        business_id: ObjectId, product_id: ObjectId
    ) -> dict | None:
        return await QualificationQueries._col().find_one({
            "business_id": business_id,
            "product_id": product_id,
        })

    @staticmethod
    async def create(data: dict) -> dict:
        result = await QualificationQueries._col().insert_one(data)
        return await QualificationQueries._col().find_one({"_id": result.inserted_id})

    @staticmethod
    async def update(
        business_id: ObjectId, product_id: ObjectId, data: dict
    ) -> dict | None:
        result = await QualificationQueries._col().update_one(
            {"business_id": business_id, "product_id": product_id},
            {"$set": data},
        )
        if result.matched_count == 0:
            return None
        return await QualificationQueries._col().find_one({
            "business_id": business_id,
            "product_id": product_id,
        })

    @staticmethod
    async def upsert(
        business_id: ObjectId, product_id: ObjectId, data: dict
    ) -> dict:
        """Insert if not exists, update if exists."""
        await QualificationQueries._col().update_one(
            {"business_id": business_id, "product_id": product_id},
            {"$set": data},
            upsert=True,
        )
        return await QualificationQueries._col().find_one({
            "business_id": business_id,
            "product_id": product_id,
        })

    @staticmethod
    async def delete_by_product(
        business_id: ObjectId, product_id: ObjectId
    ) -> bool:
        """Delete qualification flow for a product (cascade cleanup)."""
        result = await QualificationQueries._col().delete_one({
            "business_id": business_id,
            "product_id": product_id,
        })
        return result.deleted_count > 0
