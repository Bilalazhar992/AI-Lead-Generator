"""Message constants used across the application."""


class MESSAGES:
    """Response messages."""

    # Generic
    SUCCESS = "Operation completed successfully"
    EXCEPTION = "Something went wrong. Please try again later"
    INVALID_PARAMETERS = "Required parameters are missing or invalid"
    PERMISSION_DENIED = "You do not have permission to perform this action"
    UNAUTHORIZED = "You are not authorized to perform this action"
    NOT_FOUND = "The requested resource was not found"
    ALREADY_EXISTS = "Resource already exists"
    VALIDATION_ERROR = "Validation failed. Please check the provided data"

    # Auth
    USER_CREATED = "Account created successfully"
    USER_ALREADY_EXISTS = "An account with this email already exists"
    INVALID_CREDENTIALS = "Invalid email or password"
    ACCOUNT_INACTIVE = "Your account has been deactivated. Please contact support"
    SIGNIN_SUCCESS = "Signed in successfully"
    SIGNOUT_SUCCESS = "Signed out successfully"
    TOKEN_REFRESHED = "Token refreshed successfully"
    INVALID_REFRESH_TOKEN = "Invalid or expired refresh token"
    REFRESH_TOKEN_REVOKED = "Refresh token has been revoked"

    # Business
    BUSINESS_CREATED = "Business created successfully"
    BUSINESS_NOT_FOUND = "Business not found"
    BUSINESS_UPDATED = "Business updated successfully"
    BUSINESS_DELETED = "Business deleted successfully"

    # Staff
    STAFF_INVITED = "Staff member invited successfully"
    STAFF_EMAIL_EXISTS = "An account with this email already exists"
    INVALID_PERMISSIONS = "One or more permissions are not valid for this role"
    INVALID_DEPARTMENT = "Invalid department value"
    TEAM_LIMIT_REACHED = "Your subscription plan team member limit has been reached"

    # Products
    PRODUCT_CREATED = "Product created successfully"
    PRODUCT_UPDATED = "Product updated successfully"
    PRODUCT_DELETED = "Product and its configurations deleted successfully"
    PRODUCT_NOT_FOUND = "Product not found"
    PRODUCT_SLUG_EXISTS = "A product with this slug already exists in your business"
    PRODUCT_LIMIT_REACHED = "Your subscription plan product limit has been reached"
    PRODUCTS_FETCHED = "Products retrieved successfully"
    PRODUCT_FETCHED = "Product retrieved successfully"

    # Subscription Plans
    PLAN_CREATED = "Subscription plan created successfully"
    PLAN_UPDATED = "Subscription plan updated successfully"
    PLAN_DEACTIVATED = "Subscription plan deactivated successfully"
    PLAN_NOT_FOUND = "Subscription plan not found"
    PLAN_SLUG_EXISTS = "A subscription plan with this slug already exists"

    # AI Templates
    TEMPLATE_CREATED = "AI template created successfully"
    TEMPLATE_UPDATED = "AI template updated successfully"
    TEMPLATE_NOT_FOUND = "AI template not found"
    TEMPLATE_ID_EXISTS = "An AI template with this template_id already exists"

    # Agent Config
    AGENT_CONFIG_SAVED = "Agent configuration saved successfully"
    AGENT_CONFIG_NOT_FOUND = "Agent configuration not found for this product"

    # Qualification Flows
    QUALIFICATION_SAVED = "Qualification flow saved successfully"
    QUALIFICATION_NOT_FOUND = "Qualification flow not found for this product"

    # Profile
    PROFILE_UPDATED = "Profile updated successfully"

    # Staff management
    STAFF_NOT_FOUND = "Staff member not found"
    PERMISSIONS_UPDATED = "Permissions updated successfully"
    STAFF_STATUS_UPDATED = "Staff account status updated successfully"

    # Business admin
    BUSINESS_STATUS_UPDATED = "Business status updated successfully"

    # Subscriptions
    SUBSCRIPTION_NOT_FOUND = "No active subscription found for this business"
    SUBSCRIPTION_CHANGED = "Subscription plan changed successfully"
    SUBSCRIPTION_CANCELLED = "Subscription cancelled successfully"
    SUBSCRIPTION_ALREADY_CANCELLED = "Subscription is already cancelled"
