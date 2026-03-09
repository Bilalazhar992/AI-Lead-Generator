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
    async def update_user_details_by_user_id(user_id: ObjectId, data: dict) -> None:
        """Partial update on user_details — only the provided fields are written."""
        await UserQueries._details_col().update_one(
            {"user_id": user_id},
            {"$set": data},
        )

