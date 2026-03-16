"""Own-profile management — available to every authenticated user regardless of role."""

from bson import ObjectId
from app.queries.user_queries import UserQueries
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES
from app.models.user_schemas import UpdateProfileRequest


def _serialize_profile(user: dict, details: dict | None) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "role": user["role"],
        "permissions": user.get("permissions", []),
        "is_active": user["is_active"],
        "last_login_at": user["last_login_at"].isoformat() if user.get("last_login_at") else None,
        # user_details fields (populated when the record exists)
        "phone": details.get("phone") if details else None,
        "avatar_url": details.get("avatar_url") if details else None,
        "language": details.get("language", "en") if details else "en",
    }


class ProfileImplementation:

    async def get_me(self, user_id: str) -> dict:
        """Return the signed-in user's profile and user_details."""
        try:
            user_oid = ObjectId(user_id)
            user = await UserQueries.find_by_id(user_oid)
            if not user:
                ResponseService.status = CODE.RECORD_NOT_FOUND
                return ResponseService.response_service(STATUS.NOT_FOUND, None, MESSAGES.NOT_FOUND)

            details = await UserQueries.find_user_details(user_oid)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"profile": _serialize_profile(user, details)},
                MESSAGES.SUCCESS,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def update_me(self, user_id: str, data: UpdateProfileRequest) -> dict:
        """
        Update the signed-in user's own name and/or profile details.
        - first_name / last_name  → written to `users`
        - phone / avatar_url / language  → written to `user_details`
        """
        try:
            user_oid = ObjectId(user_id)
            payload = data.model_dump(exclude_none=True)

            if not payload:
                ResponseService.status = CODE.BAD_REQUEST
                return ResponseService.response_service(
                    STATUS.BAD_REQUEST, None, MESSAGES.INVALID_PARAMETERS
                )

            # Split: user-level fields vs user_details-level fields
            user_fields = {k: payload[k] for k in ("first_name", "last_name") if k in payload}
            detail_fields = {k: payload[k] for k in ("phone", "avatar_url", "language") if k in payload}

            if user_fields:
                updated_user = await UserQueries.update_user(user_oid, user_fields)
                if not updated_user:
                    ResponseService.status = CODE.RECORD_NOT_FOUND
                    return ResponseService.response_service(
                        STATUS.NOT_FOUND, None, MESSAGES.NOT_FOUND
                    )
            else:
                updated_user = await UserQueries.find_by_id(user_oid)

            if detail_fields:
                await UserQueries.update_user_details(user_oid, detail_fields)

            details = await UserQueries.find_user_details(user_oid)

            ResponseService.status = CODE.OK
            return ResponseService.response_service(
                STATUS.SUCCESS,
                {"profile": _serialize_profile(updated_user, details)},
                MESSAGES.PROFILE_UPDATED,
            )

        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)
