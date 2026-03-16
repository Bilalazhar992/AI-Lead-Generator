from datetime import datetime, timezone
from bson import ObjectId
from app.database import get_database


class SubscriptionQueries:
    """Database operations on `subscriptions`, `subscription_plans`, and `subscription_history`."""

    @staticmethod
    def _col():
        return get_database()["subscriptions"]

    @staticmethod
    def _plans_col():
        return get_database()["subscription_plans"]

    @staticmethod
    def _history_col():
        return get_database()["subscription_history"]

    # ── Plans ──────────────────────────────────────────────────────────

    @staticmethod
    async def find_plan_by_slug(slug: str) -> dict | None:
        return await SubscriptionQueries._plans_col().find_one({"slug": slug, "is_active": True})

    @staticmethod
    async def find_plan_by_slug_any(slug: str) -> dict | None:
        """Find plan by slug regardless of is_active status (for uniqueness check)."""
        return await SubscriptionQueries._plans_col().find_one({"slug": slug})

    @staticmethod
    async def find_plan_by_id(plan_id: ObjectId) -> dict | None:
        return await SubscriptionQueries._plans_col().find_one({"_id": plan_id})

    @staticmethod
    async def find_all_active_plans() -> list:
        cursor = SubscriptionQueries._plans_col().find({"is_active": True}).sort("display_order", 1)
        return await cursor.to_list(length=None)

    @staticmethod
    async def create_plan(data: dict) -> dict:
        result = await SubscriptionQueries._plans_col().insert_one(data)
        return await SubscriptionQueries._plans_col().find_one({"_id": result.inserted_id})

    @staticmethod
    async def update_plan(plan_id: ObjectId, data: dict) -> dict | None:
        result = await SubscriptionQueries._plans_col().update_one(
            {"_id": plan_id}, {"$set": data}
        )
        if result.matched_count == 0:
            return None
        return await SubscriptionQueries._plans_col().find_one({"_id": plan_id})

    @staticmethod
    async def deactivate_plan(plan_id: ObjectId) -> bool:
        """Soft-delete: sets is_active to False. Returns True if a doc was updated."""
        result = await SubscriptionQueries._plans_col().update_one(
            {"_id": plan_id}, {"$set": {"is_active": False}}
        )
        return result.modified_count > 0

    # ── Subscriptions ──────────────────────────────────────────────────

    @staticmethod
    async def find_active_by_business(business_id: ObjectId) -> dict | None:
        return await SubscriptionQueries._col().find_one({"business_id": business_id})

    @staticmethod
    async def find_by_business_ids(business_ids: list[ObjectId]) -> list[dict]:
        """Batch-fetch active subscriptions for multiple businesses in one query."""
        cursor = SubscriptionQueries._col().find({"business_id": {"$in": business_ids}})
        return await cursor.to_list(length=None)

    @staticmethod
    async def create_subscription(data: dict) -> dict:
        result = await SubscriptionQueries._col().insert_one(data)
        return await SubscriptionQueries._col().find_one({"_id": result.inserted_id})

    @staticmethod
    async def update_active_subscription(business_id: ObjectId, fields: dict) -> dict | None:
        """
        Overwrite specific fields on the active subscription document.
        Always stamps updated_at. Returns the updated document, or None if not found.
        """
        fields["updated_at"] = datetime.now(timezone.utc)
        result = await SubscriptionQueries._col().update_one(
            {"business_id": business_id},
            {"$set": fields},
        )
        if result.matched_count == 0:
            return None
        return await SubscriptionQueries._col().find_one({"business_id": business_id})

    @staticmethod
    async def delete_by_business(business_id: ObjectId) -> None:
        """Remove all subscription records linked to a business."""
        await SubscriptionQueries._col().delete_many({"business_id": business_id})

    # ── Subscription history ────────────────────────────────────────────

    @staticmethod
    async def archive_subscription(data: dict) -> None:
        """Append a snapshot of the current subscription to subscription_history."""
        await SubscriptionQueries._history_col().insert_one(data)

    @staticmethod
    async def find_history_by_business(business_id: ObjectId) -> list[dict]:
        """Return all historical subscription records for a business, newest first."""
        cursor = SubscriptionQueries._history_col().find(
            {"business_id": business_id}
        ).sort("archived_at", -1)
        return await cursor.to_list(length=None)
