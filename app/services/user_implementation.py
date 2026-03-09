from datetime import datetime, timedelta, timezone
from bson import ObjectId
from jose import JWTError
from passlib.context import CryptContext
from app.config import settings
from app.queries.user_queries import UserQueries
from app.queries.refresh_token_queries import RefreshTokenQueries
from app.queries.token_queries import TokenQueries
from app.utils.jwt_handler import create_access_token, create_refresh_token, decode_token
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS, ROLES, ROLE_DEFAULT_PERMISSIONS
from app.utils.messages import MESSAGES
from app.models.user_schemas import SignupRequest, SigninRequest, TokenRefreshRequest

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _serialize_user(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "role": user["role"],
        "permissions": user.get("permissions", []),
        "is_active": user["is_active"],
    }


def _token_payload(user: dict) -> dict:
    return {
        "sub": str(user["_id"]),
        "email": user["email"],
        "role": user["role"],
        "permissions": user.get("permissions", []),
    }


async def _issue_tokens(user: dict) -> tuple[str, str]:
    """Generate an access + refresh token pair and persist the refresh jti."""
    access_token = create_access_token(_token_payload(user))
    refresh_token, jti = create_refresh_token({"sub": str(user["_id"])})
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    await RefreshTokenQueries.create({
        "user_id": user["_id"],
        "jti": jti,
        "expires_at": expires_at,
        "is_revoked": False,
        "created_at": datetime.now(timezone.utc),
    })
    return access_token, refresh_token


class UserImplementation:
    """Business logic for user authentication (all roles)."""

    async def signup(self, data: SignupRequest) -> dict:
        try:
            if await UserQueries.find_by_email(data.email):
                ResponseService.status = CODE.CONFLICT
                return ResponseService.response_service(STATUS.DUPLICATE, None, MESSAGES.USER_ALREADY_EXISTS)

            now = datetime.now(timezone.utc)
            user = await UserQueries.create_user({
                "email": data.email,
                "password_hash": _pwd_context.hash(data.password),
                "first_name": data.first_name,
                "last_name": data.last_name,
                "role": ROLES.BUSINESS_OWNER,
                "permissions": ROLE_DEFAULT_PERMISSIONS[ROLES.BUSINESS_OWNER],
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

            access_token, refresh_token = await _issue_tokens(user)
            ResponseService.status = CODE.CREATED
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "user": _serialize_user(user)},
                MESSAGES.USER_CREATED,
            )
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def signin(self, data: SigninRequest) -> dict:
        try:
            user = await UserQueries.find_by_email(data.email)

            if not user or not _pwd_context.verify(data.password, user["password_hash"]):
                ResponseService.status = CODE.UNAUTHORIZED
                return ResponseService.response_service(STATUS.UNAUTHORIZED, None, MESSAGES.INVALID_CREDENTIALS)

            if not user["is_active"]:
                ResponseService.status = CODE.FORBIDDEN
                return ResponseService.response_service(STATUS.ACCOUNT_BLOCKED, None, MESSAGES.ACCOUNT_INACTIVE)

            await UserQueries.update_last_login(user["_id"])
            access_token, refresh_token = await _issue_tokens(user)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "user": _serialize_user(user)},
                MESSAGES.SIGNIN_SUCCESS,
            )
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def refresh_token(self, data: TokenRefreshRequest) -> dict:
        try:
            try:
                payload = decode_token(data.refresh_token)
            except JWTError:
                ResponseService.status = CODE.UNAUTHORIZED
                return ResponseService.response_service(STATUS.UNAUTHORIZED, None, MESSAGES.INVALID_REFRESH_TOKEN)

            if payload.get("type") != "refresh":
                ResponseService.status = CODE.UNAUTHORIZED
                return ResponseService.response_service(STATUS.UNAUTHORIZED, None, MESSAGES.INVALID_REFRESH_TOKEN)

            stored = await RefreshTokenQueries.find_valid(payload["jti"])
            if not stored:
                ResponseService.status = CODE.UNAUTHORIZED
                return ResponseService.response_service(STATUS.UNAUTHORIZED, None, MESSAGES.REFRESH_TOKEN_REVOKED)

            user = await UserQueries.find_by_id(ObjectId(payload["sub"]))
            if not user or not user["is_active"]:
                ResponseService.status = CODE.UNAUTHORIZED
                return ResponseService.response_service(STATUS.UNAUTHORIZED, None, MESSAGES.INVALID_CREDENTIALS)

            # Rotate: revoke old token, issue new pair
            await RefreshTokenQueries.revoke(payload["jti"])
            access_token, new_refresh_token = await _issue_tokens(user)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"access_token": access_token, "refresh_token": new_refresh_token, "token_type": "bearer"},
                MESSAGES.TOKEN_REFRESHED,
            )
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def signout(self, access_payload: dict) -> dict:
        try:
            # Blacklist the access token so it cannot be reused before it expires
            exp_ts = access_payload.get("exp")
            expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
            await TokenQueries.blacklist(access_payload["jti"], expires_at)

            # Revoke all refresh tokens for this user (signs out all devices)
            await RefreshTokenQueries.revoke_all_for_user(ObjectId(access_payload["sub"]))

            ResponseService.status = CODE.OK
            return ResponseService.response_service(STATUS.SUCCESS, None, MESSAGES.SIGNOUT_SUCCESS)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

