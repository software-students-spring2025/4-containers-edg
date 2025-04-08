import pytest
from unittest.mock import patch
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.testing = True
    return flask_app.test_client()


def test_redirect_to_login(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"login" in response.data.lower()


def test_user_login(client):
    with client.session_transaction() as sess:
        sess.clear()
    response = client.post("/login", data={"user_id": "testuser"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"attendance" in response.data.lower()


@patch("app.db.attendance")
def test_attendance_display(mock_attendance, client):
    mock_attendance.find.return_value.sort.return_value = [
        {"user_id": "testuser", "timestamp": "now"}
    ]
    with client.session_transaction() as sess:
        sess["user_id"] = "testuser"
    response = client.get("/attendance")
    assert response.status_code == 200
    assert b"testuser" in response.data


def test_admin_login_page_loads(client):
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert b"admin" in response.data.lower()


def test_admin_login_wrong_password(client):
    response = client.post("/admin/login", data={"password": "wrong"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"invalid" in response.data.lower()


def test_logout_clears_session(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "testuser"
    response = client.get("/logout", follow_redirects=True)
    assert b"testuser" not in response.data


@patch("app.db.users")
def test_admin_add_user_existing(mock_users, client):
    mock_users.find_one.return_value = {"user_id": "existing"}
    with client.session_transaction() as sess:
        sess["admin"] = True
    response = client.post("/admin/add", data={"user_id": "existing", "name": "John"}, follow_redirects=True)
    assert b"already exists" in response.data


@patch("app.db.users")
def test_admin_add_user_new(mock_users, client):
    mock_users.find_one.return_value = None
    with client.session_transaction() as sess:
        sess["admin"] = True
    response = client.post("/admin/add", data={"user_id": "newuser", "name": "Jane"}, follow_redirects=False)
    assert response.status_code == 302
    assert "/admin/enroll/newuser" in response.headers["Location"]
    mock_users.insert_one.assert_called_once()


@patch("app.db.users")
def test_enroll_page(mock_users, client):
    mock_users.find_one.return_value = {"user_id": "user123", "name": "Test"}
    with client.session_transaction() as sess:
        sess["admin"] = True
    response = client.get("/admin/enroll/user123")
    assert response.status_code == 200
    assert b"user123" in response.data


@patch("app.db.attendance")
def test_process_signin(mock_attendance, client):
    response = client.post("/process_signin", follow_redirects=True)
    assert b"success" in response.data.lower()
    mock_attendance.insert_one.assert_called_once()


@patch("app.db.users")
def test_signin_success(mock_users, client):
    mock_users.find_one.return_value = {"user_id": "demo_user", "name": "Demo"}
    response = client.get("/signin/success/demo_user")
    assert response.status_code == 200
    assert b"demo" in response.data.lower()

