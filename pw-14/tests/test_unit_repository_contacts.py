from datetime import date, datetime, timedelta
import unittest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.schemas.contacts import ContactSchema, ContactPutSchema, ContactUpdateSchema
from src.repository.contacts import (
    get_contacts,
    get_contact_by_id,
    get_contact_by_value,
    create_contact,
    update_contact,
    full_update_contact,
    delete_contact,
    get_upcoming_birthdays,
)


class TestAsyncContacts(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.db: AsyncSession = AsyncMock(
            spec=AsyncSession
        )  # (spec=AsyncSession) to mock all AsyncSession methods
        self.user: User = User(
            id=1,
            username="AlexDou",
            email="alexdou@mail.com",
            password="123456789",
            avatar="link_to_image",
            role="user",
            confirmed=True,
        )
        self.contact: Contact = Contact(
            id=1,
            first_name="first_name",
            last_name="last_name",
            email="test@example.com",
            phone_number="+380505554433",
            birth_date=datetime(day=12, month=5, year=2000),
            user_id=self.user.id,
        )

    # =========================================================

    async def test_get_contacts(self) -> None:
        """Test returning a paginated list of contacts for the user."""

        limit = 10
        offset = 0
        contacts = [self.contact]

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = contacts
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await get_contacts(
            limit=limit, offset=offset, user=self.user, db=self.db
        )

        self.db.execute.assert_awaited_once()
        self.assertEqual(result, contacts)
        self.assertTrue(hasattr(result[0], "id"))
        self.assertEqual(result[0].first_name, self.contact.first_name)
        self.assertEqual(result[0].last_name, self.contact.last_name)
        self.assertEqual(result[0].email, self.contact.email)
        self.assertEqual(result[0].phone_number, self.contact.phone_number)
        self.assertEqual(result[0].birth_date, self.contact.birth_date)
        self.assertEqual(result[0].user_id, self.contact.user_id)
        result_mock.scalars.assert_called_once()
        result_mock.scalars.return_value.all.assert_called_once()

    # =========================================================

    async def test_get_contacts_if_empty(self) -> None:
        """Test returning an empty list when the user has no contacts."""

        limit = 10
        offset = 0
        contacts = []

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = contacts
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await get_contacts(
            limit=limit, offset=offset, user=self.user, db=self.db
        )

        self.db.execute.assert_awaited_once()
        result_mock.scalars.assert_called_once()
        result_mock.scalars.return_value.all.assert_called_once()
        self.assertEqual(result, [])

    # =========================================================

    async def test_get_contact_by_id_if_found(self) -> None:
        """Test returning a contact by id when it exists for the user."""

        contact_id = self.contact.id
        contact = self.contact

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = contact
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await get_contact_by_id(
            contact_id=contact_id, user=self.user, db=self.db
        )

        self.db.execute.assert_awaited_once()
        self.assertEqual(result, contact)
        self.assertTrue(hasattr(result, "id"))
        self.assertEqual(result.first_name, self.contact.first_name)
        self.assertEqual(result.last_name, self.contact.last_name)
        self.assertEqual(result.email, self.contact.email)
        self.assertEqual(result.phone_number, self.contact.phone_number)
        self.assertEqual(result.birth_date, self.contact.birth_date)
        self.assertEqual(result.user_id, self.contact.user_id)
        result_mock.scalar_one_or_none.assert_called_once()

    # =========================================================

    async def test_get_contact_by_id_if_not_found(self) -> None:
        """Test returning None when no contact exists by id for the user."""

        contact_id = self.contact.id

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await get_contact_by_id(
            contact_id=contact_id, user=self.user, db=self.db
        )

        self.db.execute.assert_awaited_once()
        result_mock.scalar_one_or_none.assert_called_once()
        self.assertIsNone(result)

    # =========================================================

    async def test_get_contact_by_value_if_found(self) -> None:
        """Test returning contacts when searching by first name for the user."""

        contacts = [self.contact]

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = contacts
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await get_contact_by_value(
            user=self.user,
            db=self.db,
            first_name=self.contact.first_name,
        )

        self.db.execute.assert_awaited_once()
        self.assertEqual(result, contacts)
        self.assertTrue(hasattr(result[0], "id"))
        self.assertEqual(result[0].first_name, self.contact.first_name)
        self.assertEqual(result[0].last_name, self.contact.last_name)
        self.assertEqual(result[0].email, self.contact.email)
        self.assertEqual(result[0].phone_number, self.contact.phone_number)
        self.assertEqual(result[0].birth_date, self.contact.birth_date)
        self.assertEqual(result[0].user_id, self.contact.user_id)
        result_mock.scalars.assert_called_once()
        result_mock.scalars.return_value.all.assert_called_once()

    # =========================================================

    async def test_get_contact_by_value_if_not_found(self) -> None:
        """Test returning an empty list when no contacts match by first name for the user."""

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await get_contact_by_value(
            user=self.user,
            db=self.db,
            first_name=self.contact.first_name,
        )

        self.db.execute.assert_awaited_once()
        result_mock.scalars.assert_called_once()
        result_mock.scalars.return_value.all.assert_called_once()
        self.assertEqual(result, [])

    # =========================================================

    async def test_create_contact(self) -> None:
        """Test creating a contact for the user."""

        body = ContactSchema(
            first_name="user",
            last_name="user_last_name",
            email="user@example.com",
            phone_number="+380951112233",
            birth_date="23-07-1996",
        )

        result = await create_contact(body=body, user=self.user, db=self.db)

        # Get the Contact instance that was passed into db.add() to save to the database.
        added_contact = self.db.add.call_args.args[0]
        # Get the Contact instance that was passed into db.refresh().
        refreshed_contact = self.db.refresh.call_args.args[0]

        self.assertIsInstance(result, Contact)
        self.db.add.assert_called_once()
        self.db.commit.assert_awaited_once()
        self.db.refresh.assert_awaited_once()

        self.assertIs(refreshed_contact, added_contact)
        self.assertTrue(hasattr(result, "id"))

        self.assertEqual(added_contact.first_name, body.first_name)
        self.assertEqual(added_contact.last_name, body.last_name)
        self.assertEqual(added_contact.email, body.email)
        self.assertEqual(added_contact.phone_number, body.phone_number)
        self.assertEqual(added_contact.birth_date, body.birth_date)

        # =========================================================

    # =========================================================

    async def test_update_contact_if_found(self) -> None:
        """Test partially updating an existing contact for the user."""

        contact_id = self.user.id
        body = ContactUpdateSchema(
            first_name="user",
            last_name="user_last_name",
            email="user@example.com",
            phone_number="+380951112233",
            birth_date="23-07-1996",
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = self.contact
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await update_contact(
            contact_id=contact_id, body=body, user=self.user, db=self.db
        )

        # Get the Contact instance that was passed into db.refresh().
        refreshed_contact = self.db.refresh.call_args.args[0]

        self.assertIsInstance(result, Contact)
        self.db.execute.assert_awaited_once()
        self.db.commit.assert_awaited_once()
        self.db.refresh.assert_awaited_once()

        self.assertIsInstance(refreshed_contact, Contact)
        self.assertTrue(hasattr(result, "id"))

        self.assertEqual(refreshed_contact.first_name, body.first_name)
        self.assertEqual(refreshed_contact.last_name, body.last_name)
        self.assertEqual(refreshed_contact.email, body.email)
        self.assertEqual(refreshed_contact.phone_number, body.phone_number)
        self.assertEqual(refreshed_contact.birth_date, body.birth_date)

    # =========================================================

    async def test_update_contact_if_not_found(self) -> None:
        """Test returning None when the contact for partial update is not found."""

        contact_id = self.user.id
        body = ContactUpdateSchema(
            first_name="user",
            last_name="user_last_name",
            email="user@example.com",
            phone_number="+380951112233",
            birth_date="23-07-1996",
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await update_contact(
            contact_id=contact_id, body=body, user=self.user, db=self.db
        )

        self.db.commit.assert_not_called()
        self.db.refresh.assert_not_called()
        self.assertIsNone(result)

    # =========================================================

    async def test_full_update_contact_if_found(self) -> None:
        """Test fully updating an existing contact for the user."""

        contact_id = self.user.id
        body = ContactPutSchema(
            first_name="user",
            last_name="user_last_name",
            email="user@example.com",
            phone_number="+380951112233",
            birth_date="23-07-1996",
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = self.contact
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await full_update_contact(
            contact_id=contact_id, body=body, user=self.user, db=self.db
        )

        # Get the Contact instance that was passed into db.refresh().
        refreshed_contact = self.db.refresh.call_args.args[0]

        self.assertIsInstance(result, Contact)
        self.db.execute.assert_awaited_once()
        self.db.commit.assert_awaited_once()
        self.db.refresh.assert_awaited_once()

        self.assertIsInstance(refreshed_contact, Contact)
        self.assertTrue(hasattr(result, "id"))

        self.assertEqual(refreshed_contact.first_name, body.first_name)
        self.assertEqual(refreshed_contact.last_name, body.last_name)
        self.assertEqual(refreshed_contact.email, body.email)
        self.assertEqual(refreshed_contact.phone_number, body.phone_number)
        self.assertEqual(refreshed_contact.birth_date, body.birth_date)

    # =========================================================

    async def test_full_update_contact_if_not_found(self) -> None:
        """Test returning None when the contact for full update is not found."""

        contact_id = self.user.id
        body = ContactPutSchema(
            first_name="user",
            last_name="user_last_name",
            email="user@example.com",
            phone_number="+380951112233",
            birth_date="23-07-1996",
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await full_update_contact(
            contact_id=contact_id, body=body, user=self.user, db=self.db
        )

        self.db.execute.assert_awaited_once()
        self.db.commit.assert_not_called()
        self.db.refresh.assert_not_called()
        self.assertIsNone(result)

    # =========================================================

    async def test_delete_contact_if_found(self) -> None:
        """Test deleting an existing contact for the user."""

        contact_id = self.contact.id

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = self.contact
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await delete_contact(contact_id=contact_id, db=self.db, user=self.user)

        deleted_contact = self.db.delete.call_args.args[0]

        self.db.execute.assert_awaited_once()
        self.db.delete.assert_awaited_once()
        self.db.commit.assert_awaited_once()

        self.assertIsInstance(result, Contact)
        self.assertEqual(deleted_contact, result)

    # =========================================================

    async def test_delete_contact_if_not_found(self) -> None:
        """Test returning None when the contact to delete is not found."""

        contact_id = self.contact.id

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await delete_contact(contact_id=contact_id, db=self.db, user=self.user)

        self.db.execute.assert_awaited_once()
        self.db.delete.assert_not_called()
        self.db.commit.assert_not_called()

        self.assertIsNone(result)

    # =========================================================

    async def test_get_upcoming_birthdays_if_exist(self) -> None:
        """Test returning contacts with birthdays in the next seven days."""

        self.contact.birth_date = date.today() + timedelta(days=3)
        contacts = [self.contact]

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = contacts
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await get_upcoming_birthdays(db=self.db, user=self.user)

        result_mock.scalars.assert_called_once()
        result_mock.scalars.return_value.all.assert_called_once()

        self.db.execute.assert_awaited_once()
        self.assertIsInstance(result[0], Contact)
        self.assertEqual(result[0].first_name, self.contact.first_name)
        self.assertEqual(result[0].last_name, self.contact.last_name)
        self.assertEqual(result[0].email, self.contact.email)
        self.assertEqual(result[0].phone_number, self.contact.phone_number)
        self.assertEqual(result[0].birth_date, self.contact.birth_date)
        self.assertEqual(result[0].user_id, self.contact.user_id)

    # =========================================================

    async def test_get_upcoming_birthdays_if_not_exist(self) -> None:
        """Test returning an empty list when no upcoming birthdays exist."""

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await get_upcoming_birthdays(db=self.db, user=self.user)

        result_mock.scalars.assert_called_once()
        result_mock.scalars.return_value.all.assert_called_once()

        self.db.execute.assert_awaited_once()
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
