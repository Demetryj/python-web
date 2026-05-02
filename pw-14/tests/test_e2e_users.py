from unittest.mock import MagicMock


from tests.conftest import test_user

PREFIX = "/api/user"


def test_get_me(client, get_token) -> None:
    """Test that an authenticated user can get their own profile data."""

    token = get_token
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"{PREFIX}/me", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == test_user["email"]


def test_update_avatar(client, get_token, monkeypatch) -> None:
    """Test that an authenticated user can upload and update their avatar."""

    mock_upload = MagicMock(return_value={"version": "123456"})
    monkeypatch.setattr("cloudinary.uploader.upload", mock_upload)

    headers = {"Authorization": f"Bearer {get_token}"}
    files = {
        "file": (
            "avatar.png",
            b"fake image content",
            "image/png",
        )
    }

    response = client.patch(
        f"{PREFIX}/update-avatar",
        headers=headers,
        files=files,
    )

    assert response.status_code == 200, response.text

    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["avatar"] is not None

    mock_upload.assert_called_once()
