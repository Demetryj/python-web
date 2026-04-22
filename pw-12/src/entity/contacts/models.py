from datetime import date

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, func, Column, DateTime, Date


# Base = declarative_base()
class Base(DeclarativeBase):
    pass


class LastModifiedMixin:
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


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
