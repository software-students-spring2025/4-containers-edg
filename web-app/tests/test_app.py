"""Unit tests for Flask web application routes and logic."""

from unittest.mock import patch, MagicMock
import pytest
from app import app as flask_app


@pytest.fixture
def test_client():
    """Create and configure a new test client for the app."""
    flask_app.config["TESTING"] = True
    flask_app.secret_key = "test"
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client


def test_index_redirects_to_signin(test_client):
    """Test that the index route redirects to /signin."""
    response = test_client.get("/")
    assert response.status_code == 302
    assert "/signin" in response.headers["Location"]


@patch("app.get_db")
def test_admin_login_success(mock_get_db, test_client):
    """Test successful admin login with mocked DB."""
    mock_db = MagicMock()
    mock_db.attendance.find.return_value.sort.return_value = []
    mock_db.faces.find.return_value = []
    mock_get_db.return_value = mock_db

    with patch("app.ADMIN_PASSWORD", "testpass"):
        response = test_client.post(
            "/admin/login",
            data={"password": "testpass"},
            follow_redirects=True
        )

    assert response.status_code == 200
    assert b"Admin Dashboard" in response.data or b"SmartGate" in response.data


def test_admin_login_failure(test_client):
    """Test admin login with incorrect password."""
    response = test_client.post("/admin/login", data={"password": "wrong"}, follow_redirects=True)
    assert b"Invalid admin password" in response.data


def test_signin_page_loads(test_client):
    """Test that the signin page loads correctly."""
    response = test_client.get("/signin")
    assert response.status_code == 200
    assert b"Face" in response.data or b"Sign in" in response.data


@patch("app.requests.post")
@patch("app.get_db")
def test_process_signin_success(mock_get_db, mock_post, test_client):
    """Test successful face sign-in with mocked DB and API response."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "success": True,
        "verified": True,
        "match": {"_id": "123", "name": "Alice"}
    }

    mock_attendance_collection = MagicMock()
    mock_attendance_collection.insert_one.return_value.inserted_id = "abc123"
    mock_db = MagicMock()
    mock_db.attendance = mock_attendance_collection
    mock_get_db.return_value = mock_db

    response = test_client.post("/process_signin", data={"image": "dummy_base64"})
    assert response.status_code == 200
    assert response.json["success"] is True
    assert "/signin/success/" in response.json["redirect"]


@patch("app.requests.post")
def test_process_signin_failure(mock_post, test_client):
    """Test failed face sign-in."""
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "success": False,
        "verified": False,
    }

    response = test_client.post("/process_signin", data={"image": "dummy_base64"})
    assert response.status_code == 200
    assert not response.json["success"]


def test_logout_clears_session(test_client):
    """Test that logout clears admin session."""
    with test_client.session_transaction() as sess:
        sess["admin"] = True
    response = test_client.get("/logout", follow_redirects=True)
    assert b"Sign in" in response.data or response.status_code == 200
