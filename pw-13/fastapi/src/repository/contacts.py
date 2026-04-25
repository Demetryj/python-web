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

async def get_contacts(limit: int, offset: int, db: AsyncSession, user: User) -> list[Contact]:
    """Return a paginated list of contacts."""
    stmt = (
        select(Contact)
        .where(Contact.user_id == user.id)
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_contact_by_id(contact_id: int, db: AsyncSession, user: User) -> Contact | None:
    """Return one contact by id or None if not found."""
    stmt = select(Contact).where(
        and_(Contact.id == contact_id, Contact.user_id == user.id)
    )
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()
    return contact


async def get_contact_by_value(
    db: AsyncSession, user: User,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
) -> list[Contact]:
    """Search contacts by first name, last name, or email."""
    stmt = None

    if first_name:
        stmt = select(Contact).where(
            and_(Contact.user_id == user.id, Contact.first_name.ilike(f"%{first_name}%"))
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
    """Create a new contact and return it."""
    contact = Contact(**body.model_dump(exclude_unset=True), user=user) # (first_name=body.first_name, email=body.email)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(
    contact_id: int, body: ContactUpdateSchema, db: AsyncSession, user: User
) -> Contact | None:
    """Partially update an existing contact by id."""
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
    """Fully update an existing contact by id."""
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


async def delete_contact(contact_id: int, db: AsyncSession, user: User) -> Contact | None:
    """Delete a contact by id and return the deleted object."""
    stmt = select(Contact).filter_by(id == contact_id, user=user)
    result = await db.execute(stmt)
    contact = result.scalar_one_or_none()

    if contact:
        await db.delete(contact)
        await db.commit()

    return contact


async def get_upcoming_birthdays(db: AsyncSession, user: User) -> list[Contact]:
    """Return contacts with birthdays in the next 7 days (inclusive)."""
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
