from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

_client: AsyncIOMotorClient = None
_db = None


async def connect_to_mongo() -> None:
    """Open MongoDB connection, create indexes, and seed the super admin on first run."""
    global _client, _db
    _client = AsyncIOMotorClient(settings.MONGODB_URL)
    _db = _client[settings.DATABASE_NAME]
    await _ensure_indexes()
    await _seed_subscription_plans()
    await _seed_super_admin()


async def close_mongo_connection() -> None:
    """Close the MongoDB connection gracefully."""
    global _client
    if _client:
        _client.close()


def get_database():
    """Return the active database instance."""
    return _db


async def _ensure_indexes() -> None:
    """Create all required collection indexes."""
    # ── Platform: auth ────────────────────────────────────────────────
    await _db["users"].create_index("email", unique=True)
    await _db["user_details"].create_index("user_id", unique=True)

    # Access token blacklist — TTL auto-deletes expired entries
    await _db["token_blacklist"].create_index("jti", unique=True)
    await _db["token_blacklist"].create_index("expires_at", expireAfterSeconds=0)

    # Refresh tokens — TTL auto-deletes expired entries
    await _db["refresh_tokens"].create_index("jti", unique=True)
    await _db["refresh_tokens"].create_index("user_id")
    await _db["refresh_tokens"].create_index("expires_at", expireAfterSeconds=0)

    # ── Platform: business & billing ──────────────────────────────────
    await _db["businesses"].create_index("slug", unique=True)
    await _db["businesses"].create_index("owner_user_id", unique=True)
    await _db["subscriptions"].create_index("business_id", unique=True)
    await _db["subscription_plans"].create_index("slug", unique=True)

    # ── Business-scoped: products ─────────────────────────────────────
    await _db["products"].create_index(
        [("business_id", 1), ("slug", 1)], unique=True
    )


async def _seed_subscription_plans() -> None:
    """Insert the default plan catalog once if no plans exist yet."""
    from datetime import datetime, timezone

    count = await _db["subscription_plans"].count_documents({})
    if count > 0:
        return

    now = datetime.now(timezone.utc)
    plans = [
        {
            "name": "Free Trial",
            "slug": "free-trial",
            "price_monthly_pkr": 0,
            "price_annual_pkr": 0,
            "max_products": 1,
            "max_leads_per_month": 50,
            "max_ai_messages_per_month": 100,
            "max_team_members": 1,
            "whatsapp_enabled": False,
            "widget_enabled": True,
            "remove_branding": False,
            "is_active": True,
            "display_order": 0,
            "created_by": None,
            "created_at": now,
        },
        {
            "name": "Starter",
            "slug": "starter",
            "price_monthly_pkr": 4999,
            "price_annual_pkr": 49999,
            "max_products": 2,
            "max_leads_per_month": 500,
            "max_ai_messages_per_month": 1000,
            "max_team_members": 3,
            "whatsapp_enabled": True,
            "widget_enabled": True,
            "remove_branding": False,
            "is_active": True,
            "display_order": 1,
            "created_by": None,
            "created_at": now,
        },
        {
            "name": "Growth",
            "slug": "growth",
            "price_monthly_pkr": 9999,
            "price_annual_pkr": 99999,
            "max_products": 5,
            "max_leads_per_month": 2000,
            "max_ai_messages_per_month": 5000,
            "max_team_members": 10,
            "whatsapp_enabled": True,
            "widget_enabled": True,
            "remove_branding": True,
            "is_active": True,
            "display_order": 2,
            "created_by": None,
            "created_at": now,
        },
    ]
    await _db["subscription_plans"].insert_many(plans)
    print(f"[Seed] {len(plans)} subscription plans created")


async def _seed_super_admin() -> None:
    """Insert the super admin once if it does not already exist."""
    from datetime import datetime, timezone
    from passlib.context import CryptContext
    from app.queries.user_queries import UserQueries
    from app.utils.constants import ROLES, ROLE_DEFAULT_PERMISSIONS

    exists = await UserQueries.find_by_email(settings.SUPER_ADMIN_EMAIL)
    if exists:
        return

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    now = datetime.now(timezone.utc)
    user = await UserQueries.create_user({
        "email": settings.SUPER_ADMIN_EMAIL,
        "password_hash": pwd_context.hash(settings.SUPER_ADMIN_PASSWORD),
        "first_name": settings.SUPER_ADMIN_FIRST_NAME,
        "last_name": settings.SUPER_ADMIN_LAST_NAME,
        "role": ROLES.SUPER_ADMIN,
        "permissions": ROLE_DEFAULT_PERMISSIONS[ROLES.SUPER_ADMIN],
        "is_active": True,
        "last_login_at": None,
        "created_at": now,
        "updated_at": now,
    })
    await UserQueries.create_user_details({
        "user_id": user["_id"],
        "phone": None,
        "avatar_url": None,
        "language": "en",
        "created_at": now,
        "updated_at": now,
    })
    print(f"[Seed] Super admin created → {settings.SUPER_ADMIN_EMAIL}")
