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
    await _seed_ai_templates()


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

    # ── Platform: AI templates ────────────────────────────────────
    await _db["ai_templates"].create_index("template_id", unique=True)

    # ── Business: products ────────────────────────────────────────
    await _db["products"].create_index(
        [("business_id", 1), ("slug", 1)], unique=True
    )

    # ── Business: agent configs ───────────────────────────────────
    await _db["agent_configs"].create_index(
        [("business_id", 1), ("product_id", 1)], unique=True
    )

    # ── Business: qualification flows ─────────────────────────────
    await _db["qualification_flows"].create_index(
        [("business_id", 1), ("product_id", 1)], unique=True
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
    from app.utils.password_helper import hash_password
    from app.queries.user_queries import UserQueries
    from app.utils.constants import ROLES, ROLE_DEFAULT_PERMISSIONS

    exists = await UserQueries.find_by_email(settings.SUPER_ADMIN_EMAIL)
    if exists:
        return

    now = datetime.now(timezone.utc)
    user = await UserQueries.create_user({
        "email": settings.SUPER_ADMIN_EMAIL,
        "password_hash": hash_password(settings.SUPER_ADMIN_PASSWORD),
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


async def _seed_ai_templates() -> None:
    """Insert default AI agent templates once if none exist yet."""
    from datetime import datetime, timezone

    count = await _db["ai_templates"].count_documents({})
    if count > 0:
        return

    now = datetime.now(timezone.utc)
    templates = [
        {
            "template_id": "default_agent",
            "name": "General Lead Generation",
            "description": "A versatile AI agent for capturing and qualifying leads across industries.",
            "icon": "🎯",
            "system_prompt_template": (
                "You are {company_name}'s AI assistant for {product_name}. "
                "Your tone is {tone}. Your goal is to {primary_goal}. "
                "Product description: {product_description}. "
                "Target audience: {target_audience}. "
                "Greet users warmly, answer their questions about the product, "
                "qualify them through natural conversation, and guide qualified "
                "leads toward booking a meeting."
            ),
            "default_tone": "friendly",
            "default_personality_traits": ["helpful", "enthusiastic", "concise"],
            "default_primary_goal": "book_meeting",
            "default_greeting_message": "Hi there! 👋 I'm here to help you learn more about our product. How can I assist you today?",
            "default_fallback_message": "I'm not sure I understood that. Could you rephrase your question?",
            "default_meeting_cta_message": "Would you like to schedule a quick call to discuss this further?",
            "default_avoid_topics": ["politics", "religion", "competitors"],
            "default_handoff_keywords": ["speak to human", "real person", "manager"],
            "suggested_questions": [
                {
                    "question_text": "What is your budget range?",
                    "type": "single_choice",
                    "options": [
                        {"label": "Under 50K PKR", "score": 1},
                        {"label": "50K - 200K PKR", "score": 3},
                        {"label": "200K+ PKR", "score": 5},
                    ],
                    "is_required": True,
                },
                {
                    "question_text": "When are you looking to get started?",
                    "type": "single_choice",
                    "options": [
                        {"label": "Immediately", "score": 5},
                        {"label": "Within a month", "score": 3},
                        {"label": "Just exploring", "score": 1},
                    ],
                    "is_required": True,
                },
            ],
            "is_active": True,
            "created_by": None,
            "created_at": now,
            "updated_at": now,
        },
        {
            "template_id": "real_estate_agent",
            "name": "Real Estate Agent",
            "description": "Specialized AI agent for real estate businesses — property inquiries, viewings, and buyer qualification.",
            "icon": "🏠",
            "system_prompt_template": (
                "You are {company_name}'s real estate AI assistant for {product_name}. "
                "Your tone is {tone}. You help potential buyers and renters find "
                "properties. Product description: {product_description}. "
                "Ask about their preferred location, budget, property type, and "
                "timeline. Qualify them and suggest booking a viewing."
            ),
            "default_tone": "professional",
            "default_personality_traits": ["knowledgeable", "patient", "detail-oriented"],
            "default_primary_goal": "book_meeting",
            "default_greeting_message": "Welcome! 🏡 Looking for your dream property? I can help you find the perfect match. What are you looking for?",
            "default_fallback_message": "Let me connect you with one of our property specialists for that question.",
            "default_meeting_cta_message": "I'd love to arrange a viewing for you. Shall I check our available slots?",
            "default_avoid_topics": ["legal advice", "mortgage calculations"],
            "default_handoff_keywords": ["speak to agent", "real person", "broker"],
            "suggested_questions": [
                {
                    "question_text": "What type of property are you looking for?",
                    "type": "single_choice",
                    "options": [
                        {"label": "Residential (House/Apartment)", "score": 3},
                        {"label": "Commercial (Office/Shop)", "score": 4},
                        {"label": "Plot / Land", "score": 5},
                    ],
                    "is_required": True,
                },
                {
                    "question_text": "What is your budget range?",
                    "type": "single_choice",
                    "options": [
                        {"label": "Under 50 Lac", "score": 2},
                        {"label": "50 Lac - 2 Crore", "score": 4},
                        {"label": "2 Crore+", "score": 5},
                    ],
                    "is_required": True,
                },
            ],
            "is_active": True,
            "created_by": None,
            "created_at": now,
            "updated_at": now,
        },
    ]

    await _db["ai_templates"].insert_many(templates)
    print(f"[Seed] {len(templates)} AI templates created")
