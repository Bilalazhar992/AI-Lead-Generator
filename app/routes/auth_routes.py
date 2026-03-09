from fastapi import APIRouter, Depends
from app.controllers.user_controller import UserController
from app.models.user_schemas import SignupRequest, SigninRequest, TokenRefreshRequest
from app.utils.auth_dependency import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
_controller = UserController()


@router.post("/signup", status_code=201)
async def signup(data: SignupRequest):
    """Register a new business owner account."""
    return await _controller.signup(data)


@router.post("/signin")
async def signin(data: SigninRequest):
    """Authenticate and receive an access + refresh token pair."""
    return await _controller.signin(data)


@router.post("/refresh-token")
async def refresh_token(data: TokenRefreshRequest):
    """Exchange a valid refresh token for a new rotated token pair."""
    return await _controller.refresh_token(data)


@router.post("/signout")
async def signout(current_user: dict = Depends(get_current_user)):
    """Revoke the active session (blacklists access token + all refresh tokens)."""
    return await _controller.signout(current_user)
