from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_database


class UserQueries:
    """Database operations on `users` and `user_details` collections."""

    @staticmethod
    def _col():
        return get_database()["users"]

    @staticmethod
    def _details_col():
        return get_database()["user_details"]

    @staticmethod
    async def find_by_email(email: str) -> dict | None:
        return await UserQueries._col().find_one({"email": email})

    @staticmethod
    async def find_by_id(user_id: ObjectId) -> dict | None:
        return await UserQueries._col().find_one({"_id": user_id})

    @staticmethod
    async def create_user(data: dict) -> dict:
        result = await UserQueries._col().insert_one(data)
        return await UserQueries._col().find_one({"_id": result.inserted_id})

    @staticmethod
    async def create_user_details(data: dict) -> None:
        await UserQueries._details_col().insert_one(data)

    @staticmethod
    async def update_last_login(user_id: ObjectId) -> None:
        now = datetime.now(timezone.utc)
        await UserQueries._col().update_one(
            {"_id": user_id},
            {"$set": {"last_login_at": now, "updated_at": now}},
        )

    @staticmethod
    async def count_staff_by_business(business_id: ObjectId) -> int:
        """Count business_staff members linked to a business (via user_details)."""
        return await UserQueries._details_col().count_documents(
            {"business_id": business_id}
        )

    @staticmethod
    async def find_user_details(user_id: ObjectId) -> dict | None:
        """Get user_details document by user_id."""
        return await UserQueries._details_col().find_one({"user_id": user_id})

    @staticmethod
    async def update_user(user_id: ObjectId, data: dict) -> dict | None:
        """Partial update on the users doc. Returns the updated document, or None if not found."""
        data["updated_at"] = datetime.now(timezone.utc)
        result = await UserQueries._col().update_one({"_id": user_id}, {"$set": data})
        if result.matched_count == 0:
            return None
        return await UserQueries._col().find_one({"_id": user_id})

    @staticmethod
    async def update_user_details(user_id: ObjectId, data: dict) -> None:
        """Partial update on user_details — only the provided fields are written."""
        data["updated_at"] = datetime.now(timezone.utc)
        await UserQueries._details_col().update_one({"user_id": user_id}, {"$set": data})

    @staticmethod
    async def find_all_by_role(role: str) -> list[dict]:
        """Return all users with the given role."""
        cursor = UserQueries._col().find({"role": role})
        return await cursor.to_list(length=None)

    @staticmethod
    async def find_staff_details_by_business(business_id: ObjectId) -> list[dict]:
        """Return all user_details docs linked to a business (business_staff members)."""
        cursor = UserQueries._details_col().find({"business_id": business_id})
        return await cursor.to_list(length=None)

    @staticmethod
    async def find_users_by_ids(user_ids: list[ObjectId]) -> list[dict]:
        """Batch-fetch user documents by a list of _ids in one query."""
        cursor = UserQueries._col().find({"_id": {"$in": user_ids}})
        return await cursor.to_list(length=None)

