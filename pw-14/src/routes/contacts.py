from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter

from src.repository import contacts as repository_contacts
from src.schemas.contacts import (
    ContactSchema,
    ContactPutSchema,
    ContactUpdateSchema,
    ContactResponse,
)
from src.database.db import get_db
from src.entity.models import User, Role
from src.services.auth import auth_service
from src.services.role import RoleAccess
from src.config.rate_limiters import contacts_base_limiter

router = APIRouter(
    prefix="/contacts",
    tags=["contacts"],
    # Apply rate limiting to all endpoints in this router: max 10 requests per 60 seconds.
    dependencies=[Depends(RateLimiter(limiter=contacts_base_limiter))],
)


# Reusable RBAC dependency for read endpoints; allows admin/moderator/user roles.
allowed_operation_get = RoleAccess([Role.admin, Role.moderator, Role.user])
allowed_operation_create = RoleAccess([Role.admin, Role.moderator, Role.user])
allowed_operation_update = RoleAccess([Role.admin, Role.moderator, Role.user])
allowed_operation_delete = RoleAccess([Role.admin, Role.moderator, Role.user])
admin_only = RoleAccess([Role.admin])


# Get paginated list of all contacts.
@router.get(
    "/all",
    response_model=list[ContactResponse],
    response_description="Success",
    dependencies=[Depends(allowed_operation_get)],
)
async def get_contacts(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    contacts = await repository_contacts.get_contacts(
        offset=offset, limit=limit, db=db, user=user
    )
    return contacts


# Get contacts with birthdays in the next 7 days.
@router.get(
    "/upcoming-birthdays",
    response_model=list[ContactResponse],
    response_description="Success",
    description="Get a list of contacts with birthdays for the next 7 days",
    dependencies=[Depends(allowed_operation_get)],
)
async def get_upcoming_birthdays(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    contacts = await repository_contacts.get_upcoming_birthdays(db=db, user=user)
    return contacts


# Get one contact by id.
@router.get(
    "/{contact_id}",
    response_model=ContactResponse,
    response_description="Success",
    dependencies=[Depends(allowed_operation_get)],
)
async def get_contact_by_id(
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    contact = await repository_contacts.get_contact_by_id(
        contact_id=contact_id, db=db, user=user
    )
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return contact


# Search contacts by first name, last name, or email.
@router.get(
    "/",
    response_model=list[ContactResponse],
    response_description="Success",
    dependencies=[Depends(allowed_operation_get)],
)
async def get_contact_by_value(
    first_name: str | None = Query(default=None),
    last_name: str | None = Query(default=None),
    email: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    contact = await repository_contacts.get_contact_by_value(
        first_name=first_name, last_name=last_name, email=email, db=db, user=user
    )
    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return contact


# Fully update a contact (PUT).
@router.put(
    "/{contact_id}",
    response_model=ContactResponse,
    response_description="Success",
    description="Update all contact fields",
    dependencies=[Depends(allowed_operation_update)],
)
async def full_update_contact(
    body: ContactPutSchema,
    contact_id: int = Path(ge=1, description="The contact ID you want to change"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    contact = await repository_contacts.full_update_contact(
        contact_id=contact_id, body=body, db=db, user=user
    )
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return contact


# Partially update a contact (PATCH).
@router.patch(
    "/{contact_id}",
    response_model=ContactResponse,
    response_description="Success",
    description="Update any field or fields",
    dependencies=[Depends(allowed_operation_update)],
)
async def partial_update_contact(
    body: ContactUpdateSchema,
    contact_id: int = Path(ge=1, description="The contact ID you want to change"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    contact = await repository_contacts.update_contact(
        contact_id=contact_id, body=body, db=db, user=user
    )
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return contact


# Create a new contact.
@router.post(
    "/",
    response_model=ContactResponse,
    response_description="Successfully created",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operation_create)],
)
async def create_contact(
    body: ContactSchema,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    contact = await repository_contacts.create_contact(body=body, db=db, user=user)
    return contact


# Delete a contact by id.
@router.delete(
    "/{contact_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Contact successfully deleted",
    dependencies=[Depends(allowed_operation_delete)],
)
async def delete_contact(
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user),
):
    contact = await repository_contacts.delete_contact(
        contact_id=contact_id, db=db, user=user
    )
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
