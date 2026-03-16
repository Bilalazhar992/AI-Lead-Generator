from app.services.user_implementation import UserImplementation
from app.models.user_schemas import SignupRequest, SigninRequest, TokenRefreshRequest
from app.utils.response_service import ResponseService
from app.utils.constants import CODE, STATUS
from app.utils.messages import MESSAGES

_impl = UserImplementation()


class UserController:
    

    async def signup(self, data: SignupRequest) -> dict:
        try:
            return await _impl.signup(data)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def signin(self, data: SigninRequest) -> dict:
        try:
            return await _impl.signin(data)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def refresh_token(self, data: TokenRefreshRequest) -> dict:
        try:
            return await _impl.refresh_token(data)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

    async def signout(self, access_payload: dict) -> dict:
        try:
            return await _impl.signout(access_payload)
        except Exception as error:
            ResponseService.status = CODE.INTERNAL_SERVER_ERROR
            return ResponseService.response_service(STATUS.EXCEPTION, str(error), MESSAGES.EXCEPTION)

