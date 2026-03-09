from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from app.utils.jwt_handler import decode_token
from app.queries.token_queries import TokenQueries
from app.utils.constants import CODE

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    FastAPI dependency that validates the Bearer access token.
    - Verifies signature, expiry, and token type.
    - Checks the jti is not blacklisted (signed out).
    Returns the decoded token payload on success.
    """
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=CODE.UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=CODE.UNAUTHORIZED, detail="Invalid token type")

    if await TokenQueries.is_blacklisted(payload.get("jti")):
        raise HTTPException(status_code=CODE.UNAUTHORIZED, detail="Token has been revoked")

    return payload


def require_permission(permission: str):
    """
    FastAPI dependency factory that enforces a required permission.
    Usage: Depends(require_permission(PERMISSIONS.MANAGE_PRODUCTS))
    """
    async def _check(current_user: dict = Depends(get_current_user)) -> dict:
        if permission not in current_user.get("permissions", []):
            raise HTTPException(status_code=CODE.FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return _check


def require_role(*roles: str):
    """
    FastAPI dependency factory that restricts a route to specific roles.
    Usage: Depends(require_role(ROLES.BUSINESS_OWNER))
           Depends(require_role(ROLES.SUPER_ADMIN, ROLES.PLATFORM_STAFF))
    """
    async def _check(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in roles:
            raise HTTPException(status_code=CODE.FORBIDDEN, detail="Access denied for your role")
        return current_user
    return _check
