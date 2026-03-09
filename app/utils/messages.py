"""Message constants used across the application"""


class MESSAGES:
    """Response messages"""

    # Generic
    SUCCESS = 'Operation completed successfully'
    EXCEPTION = 'Something went wrong. Please try again later'
    INVALID_PARAMETERS = 'Required parameters are missing or invalid'
    PERMISSION_DENIED = 'You do not have permission to perform this action'
    UNAUTHORIZED = 'You are not authorized to perform this action'
    NOT_FOUND = 'The requested resource was not found'
    ALREADY_EXISTS = 'Resource already exists'
    VALIDATION_ERROR = 'Validation failed. Please check the provided data'

    # Auth
    USER_CREATED = 'Account created successfully'
    USER_ALREADY_EXISTS = 'An account with this email already exists'
    INVALID_CREDENTIALS = 'Invalid email or password'
    ACCOUNT_INACTIVE = 'Your account has been deactivated. Please contact support'
    SIGNIN_SUCCESS = 'Signed in successfully'
    SIGNOUT_SUCCESS = 'Signed out successfully'
    TOKEN_REFRESHED = 'Token refreshed successfully'
    INVALID_REFRESH_TOKEN = 'Invalid or expired refresh token'
    REFRESH_TOKEN_REVOKED = 'Refresh token has been revoked'

    # Business
    BUSINESS_CREATED = 'Business profile created successfully'
    BUSINESS_ALREADY_EXISTS = 'A business profile already exists for this account'
    BUSINESS_NOT_FOUND = 'Business profile not found'
    BUSINESS_UPDATED = 'Business profile updated successfully'

