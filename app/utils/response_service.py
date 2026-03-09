from typing import Any, Optional, Union
from enum import Enum


class StatusCode:
    """HTTP Status Codes"""
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500


class StatusType(str, Enum):
    """Response status types (legacy enum, use STATUS constants from constants.py)"""
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    EXCEPTION = "EXCEPTION"
    FAILURE = "FAILURE"


class ResponseService:
    """Service for formatting API responses"""
    
    status: int = StatusCode.OK
    
    @staticmethod
    def response_service(
        state: Union[str, StatusType],
        response_data: Any,
        message: str
    ) -> dict:
        """
        Format response in standard structure
        
        Args:
            state: Status type (SUCCESS, ERROR, EXCEPTION, etc.)
            response_data: The data to be returned
            message: Response message
            
        Returns:
            Formatted response dictionary
        """
        response_obj = {
            "metadata": {
                "status": state.value if isinstance(state, StatusType) else state,
                "message": message,
                "responseCode": ResponseService.status,
            },
            "payload": {
                "data": response_data,
            },
        }
        return response_obj
    
    @staticmethod
    def success_response(
        data: Any,
        message: str = "Operation successful",
        status_code: int = StatusCode.OK
    ) -> dict:
        """Helper method for success responses"""
        ResponseService.status = status_code
        return ResponseService.response_service(
            StatusType.SUCCESS,
            data,
            message
        )
    
    @staticmethod
    def error_response(
        error: str,
        message: str = "An error occurred",
        status_code: int = StatusCode.BAD_REQUEST
    ) -> dict:
        """Helper method for error responses"""
        ResponseService.status = status_code
        return ResponseService.response_service(
            StatusType.ERROR,
            error,
            message
        )
    
    @staticmethod
    def exception_response(
        error: str,
        message: str = "Exception occurred",
        status_code: int = StatusCode.INTERNAL_SERVER_ERROR
    ) -> dict:
        """Helper method for exception responses"""
        ResponseService.status = status_code
        return ResponseService.response_service(
            StatusType.EXCEPTION,
            error,
            message
        )

