# pylint: disable=redefined-outer-name
"""Unit tests for Flask web application routes and logic."""
from unittest.mock import patch, MagicMock
from datetime import datetime
from bson import ObjectId
import requests
import pytest
from app import app as flask_app


@pytest.fixture(name="client_fixture")
def client():
    """Create and configure a new test client for the app."""
    flask_app.config["TESTING"] = True
    flask_app.secret_key = "test"
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client


def test_index_redirects_to_signin(client_fixture):
    """Test that the index route redirects to /signin."""
    response = client_fixture.get("/")
    assert response.status_code == 302
    assert "/signin" in response.headers["Location"]


@patch("app.get_db")
def test_admin_login_success(mock_get_db, client_fixture):
    """Test successful admin login with mocked DB."""
    mock_db = MagicMock()
    mock_db.attendance.find.return_value.sort.return_value = []
    mock_db.faces.find.return_value = []
    mock_get_db.return_value = mock_db

    with patch("app.ADMIN_PASSWORD", "testpass"):
        response = client_fixture.post(
            "/admin/login", data={"password": "testpass"}, follow_redirects=True
        )

    assert response.status_code == 200
    assert b"Admin Dashboard" in response.data or b"SmartGate" in response.data


def test_admin_login_failure(client_fixture):
    """Test admin login with incorrect password."""
    response = client_fixture.post(
        "/admin/login", data={"password": "wrong"}, follow_redirects=True
    )
    assert b"Invalid admin password" in response.data


def test_signin_page_loads(client_fixture):
    """Test that the signin page loads correctly."""
    response = client_fixture.get("/signin")
    assert response.status_code == 200
    assert b"Face" in response.data or b"Sign in" in response.data


@patch("app.requests.post")
@patch("app.get_db")
def test_process_signin_success(mock_get_db, mock_post, client_fixture):
    """Test successful face sign-in with mocked DB and API response."""
    # Use a valid ObjectId string (24-char hex)
    valid_face_id = str(ObjectId())

    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "success": True,
        "verified": True,
        "match": {"_id": valid_face_id, "name": "Alice"},
    }

    mock_attendance_collection = MagicMock()
    mock_attendance_collection.insert_one.return_value.inserted_id = ObjectId()
    mock_db = MagicMock()
    mock_db.attendance = mock_attendance_collection
    mock_get_db.return_value = mock_db

    response = client_fixture.post("/process_signin", data={"image": "dummy_base64"})
    assert response.status_code == 200
    assert response.json["success"] is True
    assert "/signin/success/" in response.json["redirect"]


@patch("app.requests.post")
def test_process_signin_failure(mock_post, client_fixture):
    """Test failed face sign-in."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "success": False,
        "verified": False,
    }

    response = client_fixture.post("/process_signin", data={"image": "dummy_base64"})
    assert response.status_code == 200
    assert not response.json["success"]


def test_logout_clears_session(client_fixture):
    """Test that logout clears admin session."""
    with client_fixture.session_transaction() as sess:
        sess["admin"] = True
    response = client_fixture.get("/logout", follow_redirects=True)
    assert b"Sign in" in response.data or response.status_code == 200


@patch("app.get_db")
def test_admin_delete_page_loads(mock_get_db, client_fixture):
    """Test that admin delete page loads and shows face list."""
    mock_faces = MagicMock()
    mock_faces.find.return_value = [
        {"_id": ObjectId(), "name": "Alice"},
        {"_id": ObjectId(), "name": "Bob"},
    ]
    mock_db = MagicMock()
    mock_db.faces = mock_faces
    mock_get_db.return_value = mock_db

    # Set admin session
    with client_fixture.session_transaction() as sess:
        sess["admin"] = True

    response = client_fixture.get("/admin/delete")
    assert response.status_code == 200
    assert b"Alice" in response.data or b"Bob" in response.data


@patch("app.get_db")
def test_delete_face_success(mock_get_db, client_fixture):
    """Test successful deletion of a face record."""
    mock_faces = MagicMock()
    mock_faces.delete_one.return_value.deleted_count = 1
    mock_db = MagicMock()
    mock_db.faces = mock_faces
    mock_get_db.return_value = mock_db

    # Set admin session
    with client_fixture.session_transaction() as sess:
        sess["admin"] = True

    fake_face_id = str(ObjectId())
    response = client_fixture.post(
        f"/admin/delete/{fake_face_id}", follow_redirects=True
    )

    assert response.status_code == 200
    assert b"Delete Face Records" in response.data
    mock_faces.delete_one.assert_called_once_with({"_id": ObjectId(fake_face_id)})


def test_admin_dashboard_unauthorized(client_fixture):
    """Test access to admin dashboard without auth redirects to login."""
    response = client_fixture.get("/admin", follow_redirects=False)
    assert response.status_code == 302
    assert "/admin/login" in response.headers["Location"]


@patch("app.get_db")
def test_admin_dashboard_authorized(mock_get_db, client_fixture):
    """Test authorized access to admin dashboard shows records."""
    mock_db = MagicMock()
    mock_db.attendance.find.return_value.sort.return_value = [
        {"_id": ObjectId(), "timestamp": datetime.now(), "face_id": ObjectId()}
    ]
    mock_db.faces.find.return_value = [{"_id": ObjectId(), "name": "Test User"}]
    mock_get_db.return_value = mock_db

    # Set admin session
    with client_fixture.session_transaction() as sess:
        sess["admin"] = True

    response = client_fixture.get("/admin")
    assert response.status_code == 200
    assert b"Admin Dashboard" in response.data or b"SmartGate" in response.data


@patch("app.get_db")
def test_admin_add_user_get(_, client_fixture):
    """Test admin add user page loads correctly."""
    # Set admin session
    with client_fixture.session_transaction() as sess:
        sess["admin"] = True

    response = client_fixture.get("/admin/add")
    assert response.status_code == 200
    assert b"Add New User" in response.data or b"Add Face" in response.data


@patch("app.requests.post")
@patch("app.get_db")
def test_process_signin_no_image(_, mock_post, client_fixture):
    """Test sign-in without image data returns error."""
    response = client_fixture.post("/process_signin", data={})
    assert response.status_code == 400
    assert not response.json["success"]
    assert "No image provided" in response.json["message"]
    mock_post.assert_not_called()


@patch("app.requests.post")
@patch("app.get_db")
def test_process_signin_api_error(_, mock_post, client_fixture):
    """Test handling of API error during signin."""
    mock_post.side_effect = requests.RequestException("Connection error")

    response = client_fixture.post("/process_signin", data={"image": "dummy_base64"})
    assert response.status_code == 200
    assert not response.json["success"]
    assert "Error connecting to DeepFace service" in response.json["message"]


@patch("app.get_db")
def test_signin_success_page(mock_get_db, client_fixture):
    """Test signin success page shows user info."""
    user_id = ObjectId()
    mock_db = MagicMock()
    mock_db.faces.find_one.return_value = {"_id": user_id, "name": "Test User"}
    mock_get_db.return_value = mock_db

    response = client_fixture.get(f"/signin/success/{str(user_id)}")
    assert response.status_code == 200
    assert b"Test User" in response.data or b"success" in response.data.lower()


@patch("app.get_db")
def test_attendance_page(mock_get_db, client_fixture):
    """Test attendance page shows user's records."""
    user_id = ObjectId()
    mock_db = MagicMock()
    mock_db.faces.find_one.return_value = {"_id": user_id, "name": "Test User"}
    mock_db.attendance.find.return_value.sort.return_value = [
        {"_id": ObjectId(), "timestamp": datetime.now(), "face_id": user_id}
    ]
    mock_get_db.return_value = mock_db

    response = client_fixture.get(f"/attendance/{str(user_id)}")
    assert response.status_code == 200
    assert b"Attendance" in response.data or b"Test User" in response.data


@patch("app.get_db")
def test_attendance_page_user_not_found(mock_get_db, client_fixture):
    """Test attendance page redirects when user not found."""
    user_id = ObjectId()
    mock_db = MagicMock()
    mock_db.faces.find_one.return_value = None
    mock_get_db.return_value = mock_db

    response = client_fixture.get(f"/attendance/{str(user_id)}")
    assert response.status_code == 302
    assert "/signin" in response.headers["Location"]


@patch("app.requests.post")
@patch("app.get_db")
def test_admin_add_user_missing_fields(
    mock_get_db, mock_requests, client_fixture
):  # pylint: disable=unused-argument
    """Test add user with missing fields shows error."""
    # Set admin session
    with client_fixture.session_transaction() as sess:
        sess["admin"] = True

    response = client_fixture.post(
        "/admin/add",
        data={"action": "add", "name": "", "image_data": "base64data"},  # Missing name
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Name and face image are required" in response.data
    mock_requests.assert_not_called()


@patch("app.requests.post")
def test_admin_add_user_api_error(mock_post, client_fixture):
    """Test handling API errors when adding a user."""
    # Set admin session
    with client_fixture.session_transaction() as sess:
        sess["admin"] = True

    mock_post.side_effect = requests.RequestException("API connection error")

    response = client_fixture.post(
        "/admin/add",
        data={"action": "add", "name": "New User", "image_data": "base64data"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Error connecting to DeepFace service" in response.data


@patch("app.requests.post")
@patch("app.get_db")
def test_admin_add_user_face_exists(mock_get_db, mock_post, client_fixture):
    """Test detecting existing face during add user."""
    # Set admin session
    with client_fixture.session_transaction() as sess:
        sess["admin"] = True

    # Mock the database
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    # Mock verify response with matched face
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "success": True,
        "verified": True,
        "match": {"_id": str(ObjectId()), "name": "Existing User"},
    }

    response = client_fixture.post(
        "/admin/add",
        data={"action": "add", "name": "New User", "image_data": "base64data"},
    )

    assert response.status_code == 200
    assert b"Existing User" in response.data


@patch("app.requests.post")
@patch("app.get_db")
def test_admin_add_user_success(mock_get_db, mock_post, client_fixture):
    """Test successful addition of new face."""
    # Set admin session
    with client_fixture.session_transaction() as sess:
        sess["admin"] = True

    # Mock the database
    mock_db = MagicMock()
    mock_db.attendance.find.return_value.sort.return_value = []
    mock_db.faces.find.return_value = []
    mock_get_db.return_value = mock_db

    # First verify returns not verified (face doesn't exist)
    # Then add returns success
    mock_post.side_effect = [
        MagicMock(status_code=200, json=lambda: {"success": True, "verified": False}),
        MagicMock(
            status_code=200, json=lambda: {"success": True, "id": str(ObjectId())}
        ),
    ]

    response = client_fixture.post(
        "/admin/add",
        data={"action": "add", "name": "New User", "image_data": "base64data"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert (
        b"added successfully" in response.data.lower()
        or b"success" in response.data.lower()
    )


@patch("app.requests.put")
@patch("app.get_db")
def test_admin_update_face_success(mock_get_db, mock_put, client_fixture):
    """Test successful update of existing face."""
    # Set admin session
    with client_fixture.session_transaction() as sess:
        sess["admin"] = True

    # Mock the database
    mock_db = MagicMock()
    mock_db.attendance.find.return_value.sort.return_value = []
    mock_db.faces.find.return_value = []
    mock_get_db.return_value = mock_db

    face_id = str(ObjectId())
    mock_put.return_value.status_code = 200
    mock_put.return_value.json.return_value = {"success": True, "id": face_id}

    response = client_fixture.post(
        "/admin/add",
        data={
            "action": "confirm",
            "name": "Updated User",
            "image_data": "base64data",
            "existing_face_id": face_id,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert (
        b"updated successfully" in response.data.lower()
        or b"success" in response.data.lower()
    )


@patch("app.requests.put")
@patch("app.get_db")
def test_admin_update_face_error(mock_get_db, mock_put, client_fixture):
    """Test error handling when updating face fails."""
    # Set admin session
    with client_fixture.session_transaction() as sess:
        sess["admin"] = True

    # Mock the database
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    face_id = str(ObjectId())
    mock_put.return_value.status_code = 200
    mock_put.return_value.json.return_value = {
        "success": False,
        "message": "Update failed",
    }

    response = client_fixture.post(
        "/admin/add",
        data={
            "action": "confirm",
            "name": "Updated User",
            "image_data": "base64data",
            "existing_face_id": face_id,
        },
    )

    assert response.status_code == 200
    assert b"Error updating face" in response.data


@patch("app.get_db")
def test_admin_add_user_invalid_action(mock_get_db, client_fixture):
    """Test handling of invalid action in admin add user form."""
    # Set admin session
    with client_fixture.session_transaction() as sess:
        sess["admin"] = True

    # Mock the database
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    response = client_fixture.post(
        "/admin/add",
        data={
            "action": "invalid_action",
            "name": "Test User",
            "image_data": "base64data",
        },
    )

    assert response.status_code == 200
    assert b"Invalid action" in response.data


@patch("app.get_db")
def test_admin_update_missing_face_id(mock_get_db, client_fixture):
    """Test handling of missing face ID during update."""
    # Set admin session
    with client_fixture.session_transaction() as sess:
        sess["admin"] = True

    # Mock the database
    mock_db = MagicMock()
    mock_get_db.return_value = mock_db

    response = client_fixture.post(
        "/admin/add",
        data={
            "action": "confirm",
            "name": "Updated User",
            "image_data": "base64data",
            # Missing existing_face_id
        },
    )

    assert response.status_code == 200
    assert b"Missing face information" in response.data


@patch("app.requests.post")
def test_process_signin_api_non_success(mock_post, client_fixture):
    """Test handling of API non-success status code during signin."""
    mock_post.return_value.status_code = 500

    response = client_fixture.post("/process_signin", data={"image": "dummy_base64"})
    assert response.status_code == 200
    assert not response.json["success"]
    assert "Error communicating with DeepFace API" in response.json["message"]


@patch("app.get_db")
def test_admin_delete_unauthorized(
    mock_get_db, client_fixture
):  # pylint: disable=unused-argument
    """Test unauthorized access to delete page redirects to login."""
    response = client_fixture.get("/admin/delete")
    assert response.status_code == 302
    assert "/admin/login" in response.headers["Location"]

    # Also test the post method to delete a face when unauthorized
    face_id = str(ObjectId())
    response = client_fixture.post(f"/admin/delete/{face_id}")
    assert response.status_code == 302
    assert "/admin/login" in response.headers["Location"]
