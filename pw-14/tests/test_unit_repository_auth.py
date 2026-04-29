from datetime import datetime
import unittest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import RefreshToken, PasswordResetToken, User
from src.repository.auth import (
    add_refresh_token,
    get_refresh_token_by_token,
    update_refresh_token,
    delete_refresh_tokens_by_user_id,
    delete_refresh_token_by_token,
    add_password_reset_token,
    get_password_reset_token,
    update_used_status_password_reset_token,
)


class TestAsyncAuthToken(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.db: AsyncSession = AsyncMock(
            spec=AsyncSession
        )  # (spec=AsyncSession) to mock all AsyncSession methods
        self.refresh_token = "refresh_token"
        self.user: User = User(
            id=1,
        )

    # =========================================================

    async def test_add_refresh_token(self) -> None:
        """Test adding a refresh token to the database for a user."""

        token = self.refresh_token
        user_id = self.user.id

        record = await add_refresh_token(token, user_id, self.db)

        self.assertIsInstance(record, RefreshToken)
        self.assertEqual(record.rf_token, token)
        self.assertEqual(record.user_id, user_id)
        self.db.add.assert_called_once_with(record)
        self.db.commit.assert_awaited_once()
        self.db.refresh.assert_awaited_once_with(record)

    # =========================================================

    async def test_get_refresh_token_by_token_if_found(self) -> None:
        """Test getting an existing refresh token from the database by token value."""

        token = self.refresh_token

        refresh_token = RefreshToken(rf_token=token, user_id=self.user.id)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = refresh_token
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await get_refresh_token_by_token(token, self.db)

        self.assertIsInstance(result, RefreshToken)
        self.assertEqual(result.rf_token, token)
        self.assertEqual(result.user_id, self.user.id)
        self.db.execute.assert_awaited_once()

    # =========================================================

    async def test_get_refresh_token_by_token_if_not_found(self) -> None:
        """Test returning None when refresh token is not found by token value."""

        token = self.refresh_token

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await get_refresh_token_by_token(token, self.db)

        self.assertIsNone(result)
        self.db.execute.assert_awaited_once()

    # =========================================================

    async def test_update_refresh_token_if_found(self) -> None:
        """Test updating an existing refresh token in the database."""

        old_token = "old_refresh_token"
        new_token = "new_refresh_token"

        old_refresh_token = RefreshToken(rf_token=old_token, user_id=self.user.id)
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = old_refresh_token
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await update_refresh_token(
            old_token=old_token, new_token=new_token, db=self.db
        )

        self.assertIsInstance(result, RefreshToken)
        self.assertEqual(result.rf_token, new_token)
        self.db.commit.assert_awaited_once()
        self.db.refresh.assert_called_with(result)

    # =========================================================

    async def test_update_refresh_token_if_not_found(self) -> None:
        """Test returning None when refresh token to update is not found."""

        old_token = "old_refresh_token"
        new_token = "new_refresh_token"

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await update_refresh_token(
            old_token=old_token, new_token=new_token, db=self.db
        )

        self.assertIsNone(result)

    # =========================================================

    async def test_delete_refresh_tokens_by_user_id(self) -> None:
        """Test deleting refresh tokens for a user by executing a bulk delete statement."""

        user_id = self.user.id
        self.db.execute = AsyncMock()

        await delete_refresh_tokens_by_user_id(user_id=user_id, db=self.db)

        self.db.execute.assert_awaited_once()
        self.db.commit.assert_awaited_once()

    # =========================================================

    async def test_delete_refresh_token_by_token_if_found(self) -> None:
        """Test returning True when a refresh token is deleted by token value."""

        token = self.refresh_token

        result_mock = MagicMock()
        # rowcount is the number of database rows affected by the DELETE statement.
        result_mock.rowcount = 1
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await delete_refresh_token_by_token(token=token, db=self.db)

        self.assertTrue(result)
        self.db.execute.assert_awaited_once()
        self.db.commit.assert_awaited_once()

    # =========================================================

    async def test_delete_refresh_token_by_token_if_not_found(self) -> None:
        """Test returning False when no refresh token is found for deletion."""

        token = self.refresh_token

        result_mock = MagicMock()
        # rowcount is 0 when the DELETE statement did not match any database rows.
        result_mock.rowcount = 0
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await delete_refresh_token_by_token(token=token, db=self.db)

        self.assertFalse(result)
        self.db.execute.assert_awaited_once()
        self.db.commit.assert_awaited_once()

    # =========================================================

    async def test_add_password_reset_token_if_not_found(self) -> None:
        """Test creating a password reset token when no token exists for the user."""

        user_id = self.user.id
        token_hash = "token_hash"
        expires_at = datetime.now()

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.db.execute = AsyncMock(return_value=result_mock)

        await add_password_reset_token(
            user_id=user_id, token_hash=token_hash, expires_at=expires_at, db=self.db
        )

        # Get the PasswordResetToken instance that was passed into db.add() to save to the database.
        added_token = self.db.add.call_args.args[0]
        # Get the PasswordResetToken instance that was passed into db.refresh().
        refreshed_token = self.db.refresh.call_args.args[0]

        self.db.execute.assert_awaited_once()
        self.db.add.assert_called_once()
        self.db.commit.assert_awaited_once()
        self.db.refresh.assert_awaited_once()

        self.assertIs(refreshed_token, added_token)

        self.assertIsInstance(added_token, PasswordResetToken)
        self.assertEqual(added_token.user_id, user_id)
        self.assertEqual(added_token.token_hash, token_hash)
        self.assertEqual(added_token.expires_at, expires_at)
        self.assertIsNone(added_token.used_at)

    # =========================================================

    async def test_add_password_reset_token_if_found(self) -> None:
        """Test updating an existing password reset token for the user."""

        user_id = self.user.id
        old_token_hash = "old_token_hash"
        old_expires_at = datetime.now()
        old_used_at = datetime.now()
        new_token_hash = "new_token_hash"
        new_expires_at = datetime.now()

        found_reset_token = PasswordResetToken(
            id=1,
            user_id=user_id,
            token_hash=old_token_hash,
            expires_at=old_expires_at,
            used_at=old_used_at,
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = found_reset_token
        self.db.execute = AsyncMock(return_value=result_mock)

        await add_password_reset_token(
            user_id=user_id,
            token_hash=new_token_hash,
            expires_at=new_expires_at,
            db=self.db,
        )

        # Get the PasswordResetToken instance that was passed into db.refresh().
        refreshed_token = self.db.refresh.call_args.args[0]

        self.db.execute.assert_awaited_once()
        self.db.add.assert_not_called()

        self.db.commit.assert_awaited_once()
        self.db.refresh.assert_awaited_once()

        self.assertIsInstance(refreshed_token, PasswordResetToken)
        self.assertEqual(refreshed_token.user_id, user_id)
        self.assertEqual(refreshed_token.token_hash, new_token_hash)
        self.assertEqual(refreshed_token.expires_at, new_expires_at)
        self.assertIsNone(refreshed_token.used_at)

    # =========================================================

    async def test_get_password_reset_token_if_found(self) -> None:
        """Test returning a password reset token when it exists by token hash."""

        token_hash = "token_hash"

        found_reset_token = PasswordResetToken(
            id=1,
            user_id=self.user.id,
            token_hash=token_hash,
            expires_at=datetime.now(),
            used_at=datetime.now(),
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = found_reset_token
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await get_password_reset_token(token_hash=token_hash, db=self.db)

        self.db.execute.assert_awaited_once()
        self.assertIsInstance(result, PasswordResetToken)
        self.assertEqual(found_reset_token.user_id, result.user_id)
        self.assertEqual(found_reset_token.token_hash, result.token_hash)
        self.assertEqual(found_reset_token.expires_at, result.expires_at)
        self.assertEqual(found_reset_token.used_at, result.used_at)
        self.assertTrue(hasattr(result, "id"))

    # =========================================================

    async def test_get_password_reset_token_if_not_found(self) -> None:
        """Test returning None when no password reset token exists by token hash."""

        token_hash = "token_hash"

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await get_password_reset_token(token_hash=token_hash, db=self.db)

        self.db.execute.assert_awaited_once()
        self.assertIsNone(result)

    # =========================================================

    async def test_update_used_status_password_reset_token_if_found(self) -> None:
        """Test marking an existing password reset token as used."""

        token_hash = "token_hash"

        found_reset_token = PasswordResetToken(
            id=1,
            user_id=self.user.id,
            token_hash=token_hash,
            expires_at=datetime.now(),
            used_at=None,
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = found_reset_token
        self.db.execute = AsyncMock(return_value=result_mock)

        await update_used_status_password_reset_token(
            token_hash=token_hash,
            db=self.db,
        )

        # Get the PasswordResetToken instance that was passed into db.refresh().
        refreshed_token = self.db.refresh.call_args.args[0]

        self.db.execute.assert_awaited_once()
        self.db.commit.assert_awaited_once()
        self.db.refresh.assert_awaited_once()

        # Checking that this is the same object in memory in which we change the value in used_at
        self.assertIs(refreshed_token, found_reset_token)

        self.assertIsInstance(refreshed_token, PasswordResetToken)
        self.assertEqual(refreshed_token.user_id, found_reset_token.user_id)
        self.assertEqual(refreshed_token.token_hash, found_reset_token.token_hash)
        self.assertEqual(refreshed_token.expires_at, found_reset_token.expires_at)
        self.assertIsNotNone(refreshed_token.used_at)
        self.assertTrue(hasattr(refreshed_token, "id"))

    # =========================================================

    async def test_update_used_status_password_reset_token_if_not_found(self) -> None:
        """Test doing nothing when password reset token is not found."""

        token_hash = "token_hash"

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        self.db.execute = AsyncMock(return_value=result_mock)

        result = await update_used_status_password_reset_token(
            token_hash=token_hash,
            db=self.db,
        )

        self.assertIsNone(result)
        self.db.execute.assert_awaited_once()
        self.db.commit.assert_not_awaited()
        self.db.refresh.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
