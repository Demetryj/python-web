from datetime import date
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select

from tests.conftest import TestingSessionLocal, test_user

from main import app
from src.routes.contacts import (
    allowed_operation_create,
    allowed_operation_get,
    allowed_operation_update,
    allowed_operation_delete,
)
from src.entity.models import Contact, User
from src.config.messages import HTTPExceptionMessages

PREFIX = "/api/contacts"


@pytest.fixture(scope="module")
def mock_contacts_role_access():
    """Bypass contacts RBAC dependencies for endpoint behavior tests."""

    async def override_role_access():
        return None

    role_dependencies = (
        allowed_operation_create,
        allowed_operation_get,
        allowed_operation_update,
        allowed_operation_delete,
    )

    for dependency in role_dependencies:
        app.dependency_overrides[dependency] = override_role_access

    yield

    for dependency in role_dependencies:
        app.dependency_overrides.pop(dependency, None)


@pytest_asyncio.fixture()
async def existing_contact() -> Contact:
    """Create and return a contact that belongs to the default test user."""

    async with TestingSessionLocal() as session:
        # The endpoint returns only contacts owned by the authenticated user,
        # so the fixture attaches the contact to the same user as get_token.
        result = await session.execute(
            select(User).where(User.email == test_user["email"])
        )
        user = result.scalar_one()

        contact = Contact(
            first_name="John",
            last_name="Doe",
            email=f"john.doe.{uuid4().hex}@mail.com",
            phone_number="+380671234567",
            birth_date=date(1990, 1, 1),
            user_id=user.id,
        )

        session.add(contact)
        await session.commit()
        await session.refresh(contact)

        return contact


def test_get_all_contacts(
    client, get_token, mock_contacts_role_access, existing_contact
) -> None:
    """Test that an authenticated user can get a list of their contacts."""

    token = get_token
    headers = {"Authorization": f"Bearer {token}"}
    test_contact: Contact = existing_contact

    response = client.get(f"{PREFIX}/all", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert any(contact["id"] == test_contact.id for contact in data)


def test_get_upcoming_birthdays(client, get_token, mock_contacts_role_access) -> None:
    """Test that an authenticated user can get upcoming birthday contacts."""

    token = get_token
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"{PREFIX}/upcoming-birthdays", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)


def test_get_contact_by_id_if_found(
    client, get_token, mock_contacts_role_access, existing_contact
) -> None:
    """Test that an authenticated user can get one existing contact by id."""

    token = get_token
    headers = {"Authorization": f"Bearer {token}"}
    test_contact: Contact = existing_contact

    response = client.get(f"{PREFIX}/{test_contact.id}", headers=headers)

    assert response.status_code == 200, response.text

    data = response.json()
    assert isinstance(data, dict)
    assert data["id"] == test_contact.id
    assert data["email"] == test_contact.email
    assert data["first_name"] == test_contact.first_name
    assert data["last_name"] == test_contact.last_name


def test_get_contact_by_id_if_not_found(
    client,
    get_token,
    mock_contacts_role_access,
) -> None:
    """Test that requesting a missing contact by id returns 404."""

    missing_contact_id = 10000
    headers = {"Authorization": f"Bearer {get_token}"}

    response = client.get(f"{PREFIX}/{missing_contact_id}", headers=headers)

    assert response.status_code == 404, response.text
    assert response.json() == {"detail": HTTPExceptionMessages.not_found.value}


def test_get_contact_by_value_if_found(
    client, get_token, mock_contacts_role_access, existing_contact
) -> None:
    """Test that an authenticated user can find contacts by first name."""

    headers = {"Authorization": f"Bearer {get_token}"}
    test_contact: Contact = existing_contact

    response = client.get(
        f"{PREFIX}?first_name={test_contact.first_name}", headers=headers
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    # Search by first name can return several contacts, so assert against the
    # exact contact created by the fixture instead of relying on list order.
    matched_contact = next(
        (contact for contact in data if contact["id"] == test_contact.id),
        None,
    )
    assert matched_contact is not None

    assert matched_contact["email"] == test_contact.email
    assert matched_contact["first_name"] == test_contact.first_name
    assert matched_contact["last_name"] == test_contact.last_name


def test_get_contact_by_value_if_not_found(
    client,
    get_token,
    mock_contacts_role_access,
) -> None:
    """Test that searching contacts by missing first name returns 404."""

    missing_value = "missing-contact-name"
    headers = {"Authorization": f"Bearer {get_token}"}

    response = client.get(f"{PREFIX}?first_name={missing_value}", headers=headers)

    assert response.status_code == 404, response.text
    assert response.json() == {"detail": HTTPExceptionMessages.not_found.value}


def test_full_update_contact_if_found(
    client, get_token, mock_contacts_role_access, existing_contact
) -> None:
    """Test that an authenticated user can fully update an existing contact."""

    headers = {"Authorization": f"Bearer {get_token}"}
    test_contact: Contact = existing_contact
    body = {
        "first_name": "Alex",
        "last_name": "Snow",
        "email": "alex.snow@mail.com",
        "phone_number": "+380507775533",
        "birth_date": "12-10-1980",
    }

    response = client.put(
        f"{PREFIX}/{test_contact.id}",
        headers=headers,
        json=body,
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["email"] == body["email"]
    assert data["first_name"] == body["first_name"]
    assert data["last_name"] == body["last_name"]
    assert data["birth_date"] == body["birth_date"]


def test_full_update_contact_if_not_found(
    client, get_token, mock_contacts_role_access
) -> None:
    """Test that fully updating a missing contact returns 404."""

    missing_id = 1000000
    headers = {"Authorization": f"Bearer {get_token}"}
    body = {
        "first_name": "Alex",
        "last_name": "Snow",
        "email": "alex.snow@mail.com",
        "phone_number": "+380507775533",
        "birth_date": "12-10-1980",
    }

    response = client.put(
        f"{PREFIX}/{missing_id}",
        headers=headers,
        json=body,
    )

    assert response.status_code == 404, response.text
    assert response.json() == {"detail": HTTPExceptionMessages.not_found.value}


def test_partial_update_contact_if_found(
    client, get_token, mock_contacts_role_access, existing_contact
) -> None:
    """Test that an authenticated user can partially update an existing contact."""

    headers = {"Authorization": f"Bearer {get_token}"}
    test_contact: Contact = existing_contact
    body = {
        "first_name": "Alex",
        "last_name": "Yellow",
        "email": "alex777@mail.com",
    }

    response = client.patch(
        f"{PREFIX}/{test_contact.id}",
        headers=headers,
        json=body,
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["email"] == body["email"]
    assert data["first_name"] == body["first_name"]
    assert data["last_name"] == body["last_name"]


def test_partial_update_contact_if_not_found(
    client, get_token, mock_contacts_role_access
) -> None:
    """Test that partially updating a missing contact returns 404."""

    missing_id = 1000000
    headers = {"Authorization": f"Bearer {get_token}"}
    body = {
        "first_name": "Alex",
        "last_name": "Yellow",
        "email": "alex777@mail.com",
    }

    response = client.patch(
        f"{PREFIX}/{missing_id}",
        headers=headers,
        json=body,
    )

    assert response.status_code == 404, response.text
    assert response.json() == {"detail": HTTPExceptionMessages.not_found.value}


def test_create_contact(client, get_token, mock_contacts_role_access) -> None:
    """Test that an authenticated user can create a new contact."""

    headers = {"Authorization": f"Bearer {get_token}"}
    body = {
        "first_name": "Jack ",
        "last_name": "Sparrow",
        "email": "sparrow@mail.com",
        "phone_number": "+380981110011",
        "birth_date": "21-11-1968",
    }

    response = client.post(
        f"{PREFIX}",
        headers=headers,
        json=body,
    )

    assert response.status_code == 201, response.text
    data = response.json()

    assert "id" in data
    assert data["email"] == body["email"]
    assert data["first_name"] == body["first_name"]
    assert data["last_name"] == body["last_name"]
    assert data["birth_date"] == body["birth_date"]


def test_delete_contact_if_found(
    client, get_token, mock_contacts_role_access, existing_contact
) -> None:
    """Test that an authenticated user can delete an existing contact."""

    headers = {"Authorization": f"Bearer {get_token}"}

    response = client.delete(f"{PREFIX}/{existing_contact.id}", headers=headers)

    assert response.status_code == 204, response.text


def test_delete_contact_if_not_found(
    client, get_token, mock_contacts_role_access, existing_contact
) -> None:
    """Test that deleting a missing contact returns 404."""

    missing_id = 1000000
    headers = {"Authorization": f"Bearer {get_token}"}

    response = client.delete(f"{PREFIX}/{missing_id}", headers=headers)

    assert response.status_code == 404, response.text

    data = response.json()
    assert data["detail"] == HTTPExceptionMessages.not_found.value
