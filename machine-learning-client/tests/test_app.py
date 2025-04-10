"""Tests for the Flask application endpoints."""

# pylint: disable=redefined-outer-name
# ^ This is disabled because pytest fixtures are intentionally redefined in test functions
import json
import sys
from unittest.mock import MagicMock, patch
import pytest

# Mock the deepface module before it's imported
sys.modules["deepface"] = MagicMock()
sys.modules["deepface.DeepFace"] = MagicMock()

# Import app after mocking dependencies
# pylint: disable=wrong-import-position
from app import app

# pylint: enable=wrong-import-position


@pytest.fixture
def client():
    """Create a test client fixture for Flask app testing."""
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


def test_index_route(client):
    """Test the index route returns the expected welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.data == b"Welcome to the Machine Learning Client"


@patch("app.df")
def test_add_face_success(mock_df, client):
    """Test successfully adding a face to the database."""
    # Mock the DeepFaceService response
    mock_df.add_face.return_value = {
        "success": True,
        "face_id": "123456789",
        "message": "Face added successfully",
    }

    # Test data
    test_data = {"img": "base64_encoded_image", "name": "Test Person"}

    response = client.post(
        "/faces", data=json.dumps(test_data), content_type="application/json"
    )

    assert response.status_code == 201
    assert json.loads(response.data) == {
        "success": True,
        "face_id": "123456789",
        "message": "Face added successfully",
    }
    mock_df.add_face.assert_called_once_with("base64_encoded_image", "Test Person")


@patch("app.df")
def test_add_face_missing_fields(mock_df, client):
    """Test adding a face with missing required fields."""
    # Test with missing name
    test_data = {"img": "base64_encoded_image"}
    response = client.post(
        "/faces", data=json.dumps(test_data), content_type="application/json"
    )

    assert response.status_code == 400
    assert json.loads(response.data) == {
        "success": False,
        "message": "Missing required fields (img, name)",
    }

    # Test with missing img
    test_data = {"name": "Test Person"}
    response = client.post(
        "/faces", data=json.dumps(test_data), content_type="application/json"
    )

    assert response.status_code == 400
    assert json.loads(response.data) == {
        "success": False,
        "message": "Missing required fields (img, name)",
    }

    # Verify mock was not called
    mock_df.add_face.assert_not_called()


@patch("app.df")
def test_verify_face_success(mock_df, client):
    """Test successfully verifying a face."""
    # Mock the DeepFaceService response
    mock_df.verify_face.return_value = {
        "success": True,
        "verified": True,
        "match": {"_id": "123456789", "name": "Test Person", "distance": 5.0},
    }

    # Test data
    test_data = {"img": "base64_encoded_image"}

    response = client.post(
        "/faces/verify", data=json.dumps(test_data), content_type="application/json"
    )

    assert response.status_code == 200
    assert json.loads(response.data) == {
        "success": True,
        "verified": True,
        "match": {"_id": "123456789", "name": "Test Person", "distance": 5.0},
    }
    mock_df.verify_face.assert_called_once_with("base64_encoded_image")


@patch("app.df")
def test_verify_face_missing_fields(mock_df, client):
    """Test verifying a face with missing required fields."""
    # Test with missing img
    test_data = {}
    response = client.post(
        "/faces/verify", data=json.dumps(test_data), content_type="application/json"
    )

    assert response.status_code == 400
    assert json.loads(response.data) == {
        "success": False,
        "message": "Missing required fields (img)",
    }

    # Verify mock was not called
    mock_df.verify_face.assert_not_called()


@patch("app.df")
def test_delete_face_success(mock_df, client):
    """Test successfully deleting a face from the database."""
    # Mock the DeepFaceService response
    mock_df.delete_face.return_value = {
        "success": True,
        "message": "Face deleted successfully",
    }

    response = client.delete("/faces/123456789")

    assert response.status_code == 200
    assert json.loads(response.data) == {
        "success": True,
        "message": "Face deleted successfully",
    }
    mock_df.delete_face.assert_called_once_with("123456789")


@patch("app.df")
def test_update_face_success(mock_df, client):
    """Test successfully replacing a face in the database."""
    # Mock the DeepFaceService response
    mock_df.replace_face.return_value = {
        "success": True,
        "face_id": "123456789",
        "message": "Face updated successfully",
    }

    # Test data
    test_data = {"img": "base64_encoded_image", "name": "Updated Person"}

    response = client.put(
        "/faces/123456789", data=json.dumps(test_data), content_type="application/json"
    )

    assert response.status_code == 200
    assert json.loads(response.data) == {
        "success": True,
        "face_id": "123456789",
        "message": "Face updated successfully",
    }
    mock_df.replace_face.assert_called_once_with(
        "base64_encoded_image", "Updated Person", "123456789"
    )


@patch("app.df")
def test_update_face_missing_fields(mock_df, client):
    """Test updating a face with missing required fields."""
    # Test with missing name
    test_data = {"img": "base64_encoded_image"}
    response = client.put(
        "/faces/123456789", data=json.dumps(test_data), content_type="application/json"
    )

    assert response.status_code == 400
    assert json.loads(response.data) == {
        "success": False,
        "message": "Missing required fields (img, name)",
    }

    # Test with missing img
    test_data = {"name": "Updated Person"}
    response = client.put(
        "/faces/123456789", data=json.dumps(test_data), content_type="application/json"
    )

    assert response.status_code == 400
    assert json.loads(response.data) == {
        "success": False,
        "message": "Missing required fields (img, name)",
    }

    # Verify mock was not called
    mock_df.replace_face.assert_not_called()
