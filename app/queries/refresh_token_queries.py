from bson import ObjectId
from app.database import get_database


class RefreshTokenQueries:
    """Database operations on the `refresh_tokens` collection."""

    @staticmethod
    def _col():
        return get_database()["refresh_tokens"]

    @staticmethod
    async def create(data: dict) -> None:
        await RefreshTokenQueries._col().insert_one(data)

    @staticmethod
    async def find_valid(jti: str) -> dict | None:
        """Return a non-revoked refresh token by its jti."""
        return await RefreshTokenQueries._col().find_one({"jti": jti, "is_revoked": False})

    @staticmethod
    async def revoke(jti: str) -> None:
        await RefreshTokenQueries._col().update_one(
            {"jti": jti}, {"$set": {"is_revoked": True}}
        )

    @staticmethod
    async def revoke_all_for_user(user_id: ObjectId) -> None:
        """Revoke every active refresh token for a user (full signout / all devices)."""
        await RefreshTokenQueries._col().update_many(
            {"user_id": user_id, "is_revoked": False},
            {"$set": {"is_revoked": True}},
        )
