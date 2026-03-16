from app.services.profile_implementation import ProfileImplementation
from app.models.user_schemas import UpdateProfileRequest
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES

_impl = ProfileImplementation()


class ProfileController:

    async def get_me(self, user_id: str) -> dict:
        try:
            return await _impl.get_me(user_id)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def update_me(self, user_id: str, data: UpdateProfileRequest) -> dict:
        try:
            return await _impl.update_me(user_id, data)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)
