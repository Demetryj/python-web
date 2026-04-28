import logging
from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.config.settings import settings
from src.services.auth import auth_service

logger = logging.getLogger(__name__)


config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME="Contacts Systems",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


# Reusable sender for email verification and password reset messages.
async def send_email(
    email: EmailStr,
    username: str,
    host: str,
    token: str,
    subject: str,
    template_name: str,
) -> None:
    """Send an HTML email using the provided subject, template, and token."""
    try:
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token,
            },
            subtype=MessageType.html,
        )

        smtp_server = FastMail(config)
        await smtp_server.send_message(message=message, template_name=template_name)
    except ConnectionErrors as err:
        logger.exception(err)
