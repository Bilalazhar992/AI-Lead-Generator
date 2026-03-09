"""Constants used across the application"""


class STATUS:
    """Response status types"""
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    ACCEPTED = 'ACCEPTED'
    NOT_ACCEPTED = 'NOT_ACCEPTED'
    EXCEPTION = 'EXCEPTION'
    NOT_FOUND = 'NOT_FOUND'
    UNAUTHORIZED = 'UNAUTHORIZED'
    FORBIDDEN = 'FORBIDDEN'
    VALIDATION_ERROR = 'VALIDATION_ERROR'
    CONFLICT = 'CONFLICT'
    TOKEN_EXPIRED = 'TOKEN_EXPIRED'
    ACCOUNT_DELETED = 'ACCOUNT_DELETED'
    ACCOUNT_BLOCKED = 'ACCOUNT_BLOCKED'
    DUPLICATE = 'DUPLICATE'
    BAD_REQUEST = 'BAD_REQUEST'


class CODE:
    """HTTP Status Codes"""
    # 2xx Success
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NON_AUTHORITATIVE_INFORMATION = 203
    NO_CONTENT = 204
    RESET_CONTENT = 205
    PARTIAL_CONTENT = 206
    
    # 3xx Redirection
    MULTIPLE_CHOICES = 300
    MOVED_PERMANENTLY = 301
    FOUND = 302
    SEE_OTHER = 303
    NOT_MODIFIED = 304
    TEMPORARY_REDIRECT = 307
    PERMANENT_REDIRECT = 308
    
    # 4xx Client Errors
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    PAYMENT_REQUIRED = 402
    FORBIDDEN = 403
    RECORD_NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    GONE = 410
    LENGTH_REQUIRED = 411
    TOKEN = 412
    PAYLOAD_TOO_LARGE = 413
    URI_TOO_LONG = 414
    UNSUPPORTED_MEDIA_TYPE = 415
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    
    # Custom Codes (Application Specific)
    DELETE_ACCOUNT = 440         # Account scheduled for deletion
    ADMIN_BLOCK = 441            # Admin has blocked the user
    EMAIL_NOT_VERIFIED = 442     # Email exists but not verified
    ACCOUNT_INACTIVE = 443       # Account is inactive
    ALREADY_EXISTS = 444         # Duplicate entry
    
    # 5xx Server Errors
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


class PASSWORD:
    """Password validation constants"""
    MESSAGE_FORMAT = 'Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one digit, and one special character.'
    REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$'


class BUSINESS_STATUS:
    """Business account statuses"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


class SUBSCRIPTION_STATUS:
    """Subscription lifecycle statuses"""
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"


class ROLES:
    """User role identifiers"""
    SUPER_ADMIN = "super_admin"
    BUSINESS_OWNER = "business_owner"
    BUSINESS_STAFF = "business_staff"
    PLATFORM_STAFF = "platform_staff"


class PERMISSIONS:
    """Granular permission identifiers"""
    MANAGE_PRODUCTS = "manage_products"
    MANAGE_LEADS = "manage_leads"
    MANAGE_TEAM = "manage_team"
    MANAGE_BILLING = "manage_billing"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_SUBSCRIPTIONS = "manage_subscriptions"
    MANAGE_AI_TEMPLATES = "manage_ai_templates"
    MANAGE_PLATFORM_USERS = "manage_platform_users"
    MANAGE_BUSINESSES = "manage_businesses"


# Default permissions assigned to each role on account creation
ROLE_DEFAULT_PERMISSIONS: dict = {
    ROLES.SUPER_ADMIN: [
        PERMISSIONS.MANAGE_SUBSCRIPTIONS,
        PERMISSIONS.MANAGE_AI_TEMPLATES,
        PERMISSIONS.VIEW_BUSINESSES,
        PERMISSIONS.MANAGE_PLATFORM_USERS,
        PERMISSIONS.VIEW_ANALYTICS,
    ],
    ROLES.BUSINESS_OWNER: [
        PERMISSIONS.MANAGE_PRODUCTS,
        PERMISSIONS.MANAGE_LEADS,
        PERMISSIONS.MANAGE_TEAM,
        PERMISSIONS.MANAGE_BILLING,
        PERMISSIONS.VIEW_ANALYTICS,
    ],
    ROLES.BUSINESS_STAFF: [],
    ROLES.PLATFORM_STAFF: [],
}

