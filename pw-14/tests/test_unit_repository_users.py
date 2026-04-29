from datetime import date, datetime, timedelta
import unittest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.schemas.users import UserShchema
from src.repository.users import (
    get_user_by_email,
    create_user,
    confirm_email,
    update_avatar_url,
    update_user_password,
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
            confirmed=False,
        )

    # =========================================================

    async def test_get_user_by_email_if_found(self) -> None:
        """Test returning a user when the email exists."""

        user_email = self.user.email
        user = self.user

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await get_user_by_email(email=user_email, db=self.db)

        self.db.execute.assert_awaited_once()
        self.assertEqual(result, user)
        result_mock.scalar_one_or_none.assert_called_once()

    # =========================================================

    async def test_get_user_by_email_if_not_found(self) -> None:
        """Test returning None when the email does not exist."""

        user_email = self.user.email

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await get_user_by_email(email=user_email, db=self.db)

        self.db.execute.assert_awaited_once()
        self.assertIsNone(result)
        result_mock.scalar_one_or_none.assert_called_once()

    # =========================================================

    async def test_create_user(self) -> None:
        """Test creating a new user account."""

        body = UserShchema(
            username="new_user", email="new_user@mail.com", password="123456789"
        )

        result = await create_user(body=body, db=self.db)

        added_user = self.db.add.call_args.args[0]

        self.db.add.assert_called_once()
        self.db.commit.assert_awaited_once()
        self.db.refresh.assert_awaited_once_with(result)
        self.assertIsInstance(result, User)
        self.assertEqual(added_user, result)
        self.assertEqual(result.username, body.username)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.password, body.password)

    # =========================================================

    async def test_confirm_email_if_user_found(self) -> None:
        """Test confirming an existing user's email."""

        user_email = self.user.email
        user = self.user

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user
        self.db.execute = AsyncMock(return_value=result_mock)

        await confirm_email(email=user_email, db=self.db)

        self.db.execute.assert_awaited_once()
        result_mock.scalar_one_or_none.assert_called_once()

        self.db.commit.assert_awaited_once()
        self.db.refresh.assert_awaited_once_with(user)
        self.assertTrue(user.confirmed)

    # =========================================================

    async def test_confirm_email_if_user_not_found(self) -> None:
        """Test returning None when confirming a missing user's email."""

        user_email = self.user.email

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await confirm_email(email=user_email, db=self.db)

        self.db.execute.assert_awaited_once()
        result_mock.scalar_one_or_none.assert_called_once()

        self.db.commit.assert_not_called()
        self.db.refresh.assert_not_called()
        self.assertIsNone(result)

    # =========================================================

    async def test_update_avatar_url_if_user_found(self) -> None:
        """Test updating an existing user's avatar URL."""

        user_email = self.user.email
        avatar_url = "new_avatar_url"
        user = self.user

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await update_avatar_url(
            email=user_email, avatar_url=avatar_url, db=self.db
        )

        self.db.execute.assert_awaited_once()
        result_mock.scalar_one_or_none.assert_called_once()

        self.db.commit.assert_awaited_once()
        self.db.refresh.assert_awaited_once_with(user)
        self.assertIsInstance(result, User)
        self.assertEqual(result.avatar, avatar_url)

    # =========================================================

    async def test_update_avatar_url_if_user_not_found(self) -> None:
        """Test returning None when updating a missing user's avatar URL."""

        user_email = self.user.email
        avatar_url = "new_avatar_url"

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await update_avatar_url(
            email=user_email, avatar_url=avatar_url, db=self.db
        )

        self.db.execute.assert_awaited_once()
        result_mock.scalar_one_or_none.assert_called_once()

        self.db.commit.assert_not_called()
        self.db.refresh.assert_not_called()
        self.assertIsNone(result)

    # =========================================================

    async def testupdate_user_password_if_user_found(self) -> None:

        user_email = self.user.email
        hashed_password = "hashed_password"
        user = self.user

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await update_user_password(
            email=user_email, hashed_password=hashed_password, db=self.db
        )

        self.db.execute.assert_awaited_once()
        result_mock.scalar_one_or_none.assert_called_once()

        self.db.commit.assert_awaited_once()
        self.db.refresh.assert_awaited_once_with(user)
        self.assertIsInstance(result, User)
        self.assertEqual(result.password, hashed_password)

    # =========================================================

    async def testupdate_user_password_if_user_not_found(self) -> None:
        """Test returning None when updating a missing user's password hash."""

        user_email = self.user.email
        hashed_password = "hashed_password"

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await update_user_password(
            email=user_email, hashed_password=hashed_password, db=self.db
        )

        self.db.execute.assert_awaited_once()
        result_mock.scalar_one_or_none.assert_called_once()

        self.db.commit.assert_not_called()
        self.db.refresh.assert_not_called()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
