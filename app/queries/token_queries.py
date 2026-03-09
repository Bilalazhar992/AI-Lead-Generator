from datetime import datetime
from app.database import get_database


class TokenQueries:
    """Operations on the `token_blacklist` collection."""

    @staticmethod
    def _col():
        return get_database()["token_blacklist"]

    @staticmethod
    async def blacklist(jti: str, expires_at: datetime) -> None:
        """Add a token jti to the blacklist.  The TTL index removes it automatically after expiry."""
        await TokenQueries._col().insert_one({"jti": jti, "expires_at": expires_at})

    @staticmethod
    async def is_blacklisted(jti: str) -> bool:
        """Return True if the jti exists in the blacklist."""
        doc = await TokenQueries._col().find_one({"jti": jti})
        return doc is not None
