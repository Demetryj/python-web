"""Database operations for user-scoped contacts."""

from datetime import date

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.schemas.contacts import (
    ContactSchema,
    ContactPutSchema,
    ContactUpdateSchema,
)

# All contact queries in this module are user-scoped:
# each user can access and manage only their own contacts.


async def get_contacts(
    limit: int, offset: int, db: AsyncSession, user: User
) -> list[Contact]:
    """Return a paginated list of contacts for a user.

    :param limit: Maximum number of contacts to return.
    :type limit: int
    :param offset: Number of contacts to skip.
    :type offset: int
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :param user: Owner user instance.
    :type user: User
    :return: User-scoped contacts.
    :rtype: list[Contact]
    """
    stmt = select(Contact).where(Contact.user_id == user.id).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_contact_by_id(
    contact_id: int, db: AsyncSession, user: User
) -> Contact | None:
    """Return one contact by id for a user.

    :param contact_id: Contact identifier.
    :type contact_id: int
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :param user: Owner user instance.
    :type user: User
    :return: Contact when found, otherwise ``None``.
    :rtype: Contact | None
    """
    stmt = select(Contact).where(
        and_(Contact.id == contact_id, Contact.user_id == user.id)
    )
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    return contact


async def get_contact_by_value(
    db: AsyncSession,
    user: User,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
) -> list[Contact]:
    """Search contacts by first name, last name, or email.

    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :param user: Owner user instance.
    :type user: User
    :param first_name: Optional first name search value.
    :type first_name: str | None
    :param last_name: Optional last name search value.
    :type last_name: str | None
    :param email: Optional email search value.
    :type email: str | None
    :return: Matching contacts.
    :rtype: list[Contact]
    """
    stmt = None

    if first_name:
        stmt = select(Contact).where(
            and_(
                Contact.user_id == user.id, Contact.first_name.ilike(f"%{first_name}%")
            )
        )
    elif last_name:
        stmt = select(Contact).where(
            and_(Contact.user_id == user.id, Contact.last_name.ilike(f"%{last_name}%"))
        )
    elif email:
        stmt = select(Contact).where(
            and_(Contact.user_id == user.id, Contact.email.ilike(f"%{email}%"))
        )

    if stmt is not None:
        result = await db.execute(stmt)
        return result.scalars().all()
    return []


async def create_contact(body: ContactSchema, db: AsyncSession, user: User) -> Contact:
    """Create a new contact for a user.

    :param body: Contact creation payload.
    :type body: ContactSchema
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :param user: Owner user instance.
    :type user: User
    :return: Created contact.
    :rtype: Contact
    """
    contact = Contact(
        **body.model_dump(exclude_unset=True), user=user
    )  # (first_name=body.first_name, email=body.email)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(
    contact_id: int, body: ContactUpdateSchema, db: AsyncSession, user: User
) -> Contact | None:
    """Partially update an existing contact by id.

    :param contact_id: Contact identifier.
    :type contact_id: int
    :param body: Partial contact update payload.
    :type body: ContactUpdateSchema
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :param user: Owner user instance.
    :type user: User
    :return: Updated contact when found, otherwise ``None``.
    :rtype: Contact | None
    """
    stmt = select(Contact).where(
        and_(Contact.id == contact_id, Contact.user_id == user.id)
    )
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()

    if contact:
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(contact, key, value)
        await db.commit()
        await db.refresh(contact)

    return contact


async def full_update_contact(
    contact_id: int, body: ContactPutSchema, db: AsyncSession, user: User
) -> Contact | None:
    """Fully update an existing contact by id.

    :param contact_id: Contact identifier.
    :type contact_id: int
    :param body: Complete contact update payload.
    :type body: ContactPutSchema
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :param user: Owner user instance.
    :type user: User
    :return: Updated contact when found, otherwise ``None``.
    :rtype: Contact | None
    """
    stmt = select(Contact).where(
        and_(Contact.id == contact_id, Contact.user_id == user.id)
    )
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()

    if contact:
        for key, value in body.model_dump().items():
            setattr(contact, key, value)
        await db.commit()
        await db.refresh(contact)

    return contact


async def delete_contact(
    contact_id: int, db: AsyncSession, user: User
) -> Contact | None:
    """Delete a contact by id.

    :param contact_id: Contact identifier.
    :type contact_id: int
    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :param user: Owner user instance.
    :type user: User
    :return: Deleted contact when found, otherwise ``None``.
    :rtype: Contact | None
    """
    stmt = select(Contact).filter_by(id=contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()

    if contact:
        await db.delete(contact)
        await db.commit()

    return contact


async def get_upcoming_birthdays(db: AsyncSession, user: User) -> list[Contact]:
    """Return contacts with birthdays in the next seven days.

    :param db: SQLAlchemy asynchronous database session.
    :type db: AsyncSession
    :param user: Owner user instance.
    :type user: User
    :return: Contacts whose next birthday is within seven days.
    :rtype: list[Contact]
    """
    today = date.today()
    days_ahead = 7

    stmt = select(Contact).where(Contact.user_id == user.id)
    result = await db.execute(stmt)
    contacts = result.scalars().all()

    upcoming_contacts: list[Contact] = []

    for contact in contacts:
        birth_date = contact.birth_date

        try:
            next_birthday = date(today.year, birth_date.month, birth_date.day)
        except ValueError:
            # Handle Feb 29 in non-leap years.
            next_birthday = date(today.year, 2, 28)

        if next_birthday < today:
            try:
                next_birthday = date(today.year + 1, birth_date.month, birth_date.day)
            except ValueError:
                next_birthday = date(today.year + 1, 2, 28)

        if 0 <= (next_birthday - today).days <= days_ahead:
            upcoming_contacts.append(contact)

    return upcoming_contacts
