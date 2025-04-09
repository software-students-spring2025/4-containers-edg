import pytest
from unittest.mock import MagicMock, patch
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        with flask_app.app_context():
            yield client

def test_home_redirects_to_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_get(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"login" in response.data.lower()


def test_attendance_requires_login(client):
    response = client.get("/attendance", follow_redirects=True)
    assert b"login" in response.data.lower()


def test_admin_login_wrong_password(client):
    response = client.post("/admin/login", data={"password": "wrong"}, follow_redirects=True)
    assert b"invalid admin password" in response.data.lower()


def test_signin_page(client):
    response = client.get("/signin")
    assert response.status_code == 200
    assert b"signin" in response.data.lower()


@patch("app.get_db")
def test_login_post_redirect(mock_get_db, client):
    mock_attendance = MagicMock()
    mock_attendance.find.return_value.sort.return_value = []

    mock_db = MagicMock()
    mock_db.attendance = mock_attendance

    mock_get_db.return_value = mock_db

    response = client.post("/login", data={"user_id": "testuser"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"attendance" in response.data.lower()


@patch("app.get_db")
def test_admin_login_correct_password(mock_get_db, client):
    mock_attendance = MagicMock()
    mock_attendance.find.return_value.sort.return_value = []

    mock_users = MagicMock()
    mock_users.find.return_value = []

    mock_db = MagicMock()
    mock_db.attendance = mock_attendance
    mock_db.users = mock_users
    mock_get_db.return_value = mock_db

    response = client.post("/admin/login", data={"password": "admin123"}, follow_redirects=True)
    assert b"attendance" in response.data.lower()



@patch("app.render_template")
@patch("app.get_db")
def test_signin_success(mock_get_db, mock_render, client):
    mock_users = MagicMock()
    mock_users.find_one.return_value = {"user_id": "demo_user", "name": "Demo"}

    mock_db = MagicMock()
    mock_db.users = mock_users
    mock_get_db.return_value = mock_db

    mock_render.return_value = b"signin success"

    response = client.get("/signin/success/demo_user")
    assert response.status_code == 200
    assert b"signin success" in response.data



