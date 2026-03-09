from bson import ObjectId
from app.database import get_database


class SubscriptionQueries:
    """Database operations on `subscriptions` and `subscription_plans` collections."""

    @staticmethod
    def _col():
        return get_database()["subscriptions"]

    @staticmethod
    def _plans_col():
        return get_database()["subscription_plans"]

    # ── Plans ──────────────────────────────────────────────────────────

    @staticmethod
    async def find_plan_by_slug(slug: str) -> dict | None:
        return await SubscriptionQueries._plans_col().find_one({"slug": slug, "is_active": True})

    @staticmethod
    async def find_plan_by_id(plan_id: ObjectId) -> dict | None:
        return await SubscriptionQueries._plans_col().find_one({"_id": plan_id})

    @staticmethod
    async def find_all_active_plans() -> list:
        cursor = SubscriptionQueries._plans_col().find({"is_active": True}).sort("display_order", 1)
        return await cursor.to_list(length=None)

    # ── Subscriptions ──────────────────────────────────────────────────

    @staticmethod
    async def find_active_by_business(business_id: ObjectId) -> dict | None:
        return await SubscriptionQueries._col().find_one({"business_id": business_id})

    @staticmethod
    async def create_subscription(data: dict) -> dict:
        result = await SubscriptionQueries._col().insert_one(data)
        return await SubscriptionQueries._col().find_one({"_id": result.inserted_id})
