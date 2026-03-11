"""Database operations on the `ai_templates` collection."""

from bson import ObjectId
from app.database import get_database


class AITemplateQueries:
    """Queries for managing AI agent templates (platform-level)."""

    @staticmethod
    def _col():
        return get_database()["ai_templates"]

    @staticmethod
    async def find_by_template_id(template_id: str) -> dict | None:
        return await AITemplateQueries._col().find_one({"template_id": template_id})

    @staticmethod
    async def find_by_id(obj_id: ObjectId) -> dict | None:
        return await AITemplateQueries._col().find_one({"_id": obj_id})

    @staticmethod
    async def find_all_active() -> list:
        cursor = AITemplateQueries._col().find({"is_active": True})
        return await cursor.to_list(length=None)

    @staticmethod
    async def create(data: dict) -> dict:
        result = await AITemplateQueries._col().insert_one(data)
        return await AITemplateQueries._col().find_one({"_id": result.inserted_id})

    @staticmethod
    async def update(obj_id: ObjectId, data: dict) -> dict | None:
        result = await AITemplateQueries._col().update_one(
            {"_id": obj_id}, {"$set": data}
        )
        if result.matched_count == 0:
            return None
        return await AITemplateQueries._col().find_one({"_id": obj_id})
