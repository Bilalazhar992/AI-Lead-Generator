from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_database


class BusinessQueries:
    """Database operations on the `businesses` collection."""

    @staticmethod
    def _col():
        return get_database()["businesses"]

    @staticmethod
    async def find_by_owner(owner_user_id: ObjectId) -> dict | None:
        return await BusinessQueries._col().find_one({"owner_user_id": owner_user_id})

    @staticmethod
    async def find_by_id(business_id: ObjectId) -> dict | None:
        return await BusinessQueries._col().find_one({"_id": business_id})

    @staticmethod
    async def find_by_slug(slug: str) -> dict | None:
        return await BusinessQueries._col().find_one({"slug": slug})

    @staticmethod
    async def slug_exists(slug: str) -> bool:
        doc = await BusinessQueries._col().find_one({"slug": slug}, {"_id": 1})
        return doc is not None

    @staticmethod
    async def create_business(data: dict) -> dict:
        result = await BusinessQueries._col().insert_one(data)
        return await BusinessQueries._col().find_one({"_id": result.inserted_id})

    @staticmethod
    async def update_business(business_id: ObjectId, data: dict) -> dict:
        data["updated_at"] = datetime.now(timezone.utc)
        await BusinessQueries._col().update_one({"_id": business_id}, {"$set": data})
        return await BusinessQueries._col().find_one({"_id": business_id})

    @staticmethod
    async def update_by_owner(business_id: ObjectId, owner_user_id: ObjectId, data: dict) -> dict | None:
        """
        Ownership-safe update: the MongoDB filter requires BOTH _id AND owner_user_id
        to match. If either is wrong the update is a no-op and None is returned.
        """
        data["updated_at"] = datetime.now(timezone.utc)
        result = await BusinessQueries._col().update_one(
            {"_id": business_id, "owner_user_id": owner_user_id},
            {"$set": data},
        )
        if result.matched_count == 0:
            return None
        return await BusinessQueries._col().find_one({"_id": business_id})
