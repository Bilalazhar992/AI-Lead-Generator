"""Database operations on the `agent_configs` collection (business-scoped)."""

from bson import ObjectId
from app.database import get_database


class AgentConfigQueries:
    """Queries for agent configuration — compound key (business_id, product_id)."""

    @staticmethod
    def _col():
        return get_database()["agent_configs"]

    @staticmethod
    async def find_by_product(
        business_id: ObjectId, product_id: ObjectId
    ) -> dict | None:
        return await AgentConfigQueries._col().find_one({
            "business_id": business_id,
            "product_id": product_id,
        })

    @staticmethod
    async def create(data: dict) -> dict:
        result = await AgentConfigQueries._col().insert_one(data)
        return await AgentConfigQueries._col().find_one({"_id": result.inserted_id})

    @staticmethod
    async def update(
        business_id: ObjectId, product_id: ObjectId, data: dict
    ) -> dict | None:
        result = await AgentConfigQueries._col().update_one(
            {"business_id": business_id, "product_id": product_id},
            {"$set": data},
        )
        if result.matched_count == 0:
            return None
        return await AgentConfigQueries._col().find_one({
            "business_id": business_id,
            "product_id": product_id,
        })

    @staticmethod
    async def upsert(
        business_id: ObjectId, product_id: ObjectId, data: dict
    ) -> dict:
        """Insert if not exists, update if exists."""
        await AgentConfigQueries._col().update_one(
            {"business_id": business_id, "product_id": product_id},
            {"$set": data},
            upsert=True,
        )
        return await AgentConfigQueries._col().find_one({
            "business_id": business_id,
            "product_id": product_id,
        })

    @staticmethod
    async def delete_by_product(
        business_id: ObjectId, product_id: ObjectId
    ) -> bool:
        """Delete agent config for a product (cascade cleanup)."""
        result = await AgentConfigQueries._col().delete_one({
            "business_id": business_id,
            "product_id": product_id,
        })
        return result.deleted_count > 0
