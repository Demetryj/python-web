from datetime import date, datetime
import enum 

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Enum, Boolean, Integer, String, func, Column, DateTime, Date, ForeignKey


# SQLAlchemy base class for declarative models.
class Base(DeclarativeBase):
    pass


# Mixin with technical timestamps for inherited models.
class LastModifiedMixin:
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# Contact entity in a user's address book.
class Contact(Base, LastModifiedMixin):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String(25), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    additional_data: Mapped[str | None] = mapped_column(
        String, nullable=True, default=None
    )
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    user: Mapped["User"] = relationship("User", backref="contacts", lazy="joined")
    
    
# Allowed user roles in the system.
class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"
    

# Application user and related refresh tokens.
class User(Base, LastModifiedMixin):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(60), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    password: Mapped[str]= mapped_column(String(255), nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(300), nullable=True)
    role: Mapped[Role] = mapped_column("role", Enum(Role), default=Role.user, nullable=False)
    # all: User operations cascade to tokens; delete-orphan: token without user is deleted on commit.
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        backref="user", cascade="all, delete-orphan"
    )
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    
# Separate table for refresh tokens: one user can sign in from multiple devices,
# so each device/session gets its own refresh token row.
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rf_token: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    

# Stores password reset JWT hashes and usage state to make reset links one-time.
class PasswordResetToken(Base, LastModifiedMixin):
    """One-time password reset token bound to a user and expiration time."""

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None)

    user: Mapped["User"] = relationship("User", backref="password_reset_tokens")


