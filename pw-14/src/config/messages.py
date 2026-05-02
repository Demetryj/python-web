import enum

class HTTPExceptionMessages(enum.Enum):
    not_found = "Not found"
    account_already_exists = "Account already exists"
    invalid_email_or_password = "Invalid email or password"
    email_not_confirmed = "Email not confirmed"
    verification_error = "Verification error"
    could_not_validate_token = "Could not validate token"
    
RESET_PASSWORD_EMAIL_EXITS = "If this email exists, password reset instructions were sent."
SUCCESS_TO_CREATE_NEW_PASSWORD = "Succes. You can create a new password."
INVALID_OR_EXPIRED_PASSWORD_RESET_TOKEN = "Invalid or expired password reset token"
EMAIL_ALREADY_CONFIRMED = "Your email is already confirmed."
CHECK_EMAIL_FOR_CONFIRMATION = "Check your email for confirmation."
EMAIL_CONFIRMED = "Email confirmed"