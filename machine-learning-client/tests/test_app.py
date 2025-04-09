import json
import pytest
import sys
from unittest.mock import MagicMock, patch

# Mock the deepface module before it's imported
sys.modules["deepface"] = MagicMock()
sys.modules["deepface.DeepFace"] = MagicMock()

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.data == b"Welcome to the Machine Learning Client"


@patch("app.df")
def test_add_face_success(mock_df, client):
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

