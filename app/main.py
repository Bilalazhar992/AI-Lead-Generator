from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection
from app.routes.auth_routes import router as auth_router
from app.routes.business_routes import router as business_router
from app.routes.platform_staff_routes import router as platform_staff_router
from app.routes.business_staff_routes import router as business_staff_router
from app.routes.subscription_plan_routes import router as subscription_plan_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(business_router)
app.include_router(platform_staff_router)
app.include_router(business_staff_router)
app.include_router(subscription_plan_router)


# ── Health ───────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}", "version": settings.APP_VERSION}


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)

