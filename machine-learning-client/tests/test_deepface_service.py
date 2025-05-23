"""Tests for the DeepFaceService component."""

# pylint: disable=redefined-outer-name
# ^ This is disabled because pytest fixtures are intentionally redefined in test functions
import sys
from unittest.mock import patch, MagicMock
import pytest

# Mock the deepface module before it's imported
mock_deepface = MagicMock()
sys.modules["deepface"] = mock_deepface
sys.modules["deepface.DeepFace"] = MagicMock()


# Mock bson.objectid
class MockObjectId:
    """Mock implementation of MongoDB's ObjectId for testing."""

    def __init__(self, id_str):
        self.id_str = id_str

    def __str__(self):
        return self.id_str

    def __eq__(self, other):
        if isinstance(other, MockObjectId):
            return self.id_str == other.id_str
        return False


# Create the ObjectId function directly in the test file
ObjectId = MockObjectId

# Import the service after mocking dependencies
# pylint: disable=wrong-import-position
from src.deepface_service import DeepFaceService

# pylint: enable=wrong-import-position


@pytest.fixture
def mock_mongo_client():
    """Create a mock MongoDB client for testing."""
    with patch("src.deepface_service.MongoClient") as mock_client:
        # Setup mock database and collections
        mock_db = MagicMock()
        mock_faces_collection = MagicMock()
        mock_attendance_collection = MagicMock()

        # Configure client.db.collection chain
        mock_client.return_value.smart_gate = mock_db
        mock_db.faces = mock_faces_collection
        mock_db.attendance = mock_attendance_collection

        yield mock_client


@pytest.fixture
# pylint: disable=unused-argument
def deepface_service(mock_mongo_client):  # Required for fixture dependency
    """Create a DeepFaceService instance for testing."""
    with (
        patch("src.deepface_service.load_dotenv"),
        patch("src.deepface_service.os.getenv", return_value="10"),
    ):
        service = DeepFaceService()
        yield service


@patch("src.deepface_service.DeepFace")
def test_add_face_success(mock_deepface, deepface_service):
    """Test successfully adding a face to the database."""
    # Mock DeepFace.represent
    mock_embedding = {"embedding": [0.1, 0.2, 0.3]}
    mock_deepface.represent.return_value = [mock_embedding]

    # Mock MongoDB insert_one
    mock_inserted_id = ObjectId("6239121d1d9d3d6e8bbc66c0")
    deepface_service.faces.insert_one.return_value.inserted_id = mock_inserted_id

    # Call the method
    result = deepface_service.add_face("base64_image_data", "Test Person")

    # Assertions
    mock_deepface.represent.assert_called_once_with(
        img_path="base64_image_data", model_name="Facenet"
    )
    deepface_service.faces.insert_one.assert_called_once_with(
        {"name": "Test Person", "img_vectors": mock_embedding["embedding"]}
    )

    assert result == {
        "success": True,
        "face_id": str(mock_inserted_id),
        "message": "Face added successfully",
    }


@patch("src.deepface_service.DeepFace")
def test_add_face_error(mock_deepface, deepface_service):
    """Test handling errors when adding a face."""
    # Mock DeepFace.represent raising an exception
    mock_deepface.represent.side_effect = Exception("Test exception")

    # Call the method
    result = deepface_service.add_face("base64_image_data", "Test Person")

    # Assertions
    assert result == {"success": False, "message": "Error: Test exception"}


@patch("src.deepface_service.DeepFace")
# pylint: disable=unused-argument
def test_verify_face_no_stored_faces(
    mock_deepface, deepface_service
):  # mock_deepface not used
    """Test verifying a face when no faces are stored in the database."""
    # Mock empty database
    deepface_service.faces.find.return_value = []

    # Call the method
    result = deepface_service.verify_face("base64_image_data")

    # Assertions
    assert result == {
        "success": True,
        "verified": False,
        "message": "No matching face found",
    }


@patch("src.deepface_service.DeepFace")
@patch("src.deepface_service.np")
def test_verify_face_with_match(mock_np, mock_deepface, deepface_service):
    """Test verifying a face with a successful match."""
    # Mock DeepFace.represent
    mock_embedding = [0.1, 0.2, 0.3]
    mock_deepface.represent.return_value = [{"embedding": mock_embedding}]

    # Create two mock faces to test finding the best match
    mock_face_id1 = ObjectId("6239121d1d9d3d6e8bbc66c0")
    mock_face_id2 = ObjectId("6239121d1d9d3d6e8bbc66c1")

    mock_face1 = {
        "_id": mock_face_id1,
        "name": "Test Person 1",
        "img_vectors": [0.15, 0.25, 0.35],
    }

    mock_face2 = {
        "_id": mock_face_id2,
        "name": "Test Person 2",
        "img_vectors": [0.12, 0.22, 0.32],
    }

    # Mock database query with two faces
    deepface_service.faces.find.return_value = [mock_face1, mock_face2]

    # Mock numpy array to return different values for different calls
    def mock_array_side_effect(_):
        return MagicMock()

    mock_np.array.side_effect = mock_array_side_effect

    # Mock linalg.norm to return different distances in sequence (first higher, second lower)
    # This tests that we find the lowest distance face
    distances = [8.0, 5.0]  # 5.0 should be chosen as best match
    mock_np.linalg.norm.side_effect = distances

    # Call the method
    result = deepface_service.verify_face("base64_image_data")

    # Assertions
    assert mock_deepface.represent.call_count == 1
    assert mock_np.array.call_count >= 4  # 2 per face
    assert mock_np.linalg.norm.call_count == 2  # Once for each face

    # Check that we got a match result with the second (lower distance) face
    assert result["success"] is True
    assert result["verified"] is True
    assert result["match"]["_id"] == str(mock_face_id2)
    assert result["match"]["name"] == "Test Person 2"
    assert result["match"]["distance"] == 5.0


@patch("src.deepface_service.DeepFace")
@patch("src.deepface_service.np")
def test_verify_face_no_match_above_threshold(mock_np, mock_deepface, deepface_service):
    """Test verifying a face with no match due to distance above threshold."""
    # Mock DeepFace.represent
    mock_embedding = [0.1, 0.2, 0.3]
    mock_deepface.represent.return_value = [{"embedding": mock_embedding}]

    # Create mock stored face
    mock_face_id = ObjectId("6239121d1d9d3d6e8bbc66c0")
    mock_face = {
        "_id": mock_face_id,
        "name": "Test Person",
        "img_vectors": [0.9, 0.8, 0.7],  # Different values to make distance larger
    }

    # Mock database query
    deepface_service.faces.find.return_value = [mock_face]

    # Mock numpy operations
    mock_array = MagicMock()
    mock_np.array.side_effect = lambda x: mock_array
    mock_np.linalg.norm.return_value = 15.0  # Above threshold of 10

    # Call the method
    result = deepface_service.verify_face("base64_image_data")

    # Assertions
    assert mock_deepface.represent.call_count == 1
    assert mock_np.array.call_count >= 2
    assert mock_np.linalg.norm.call_count == 1

    # Check the no match result
    assert result["success"] is True
    assert result["verified"] is False
    assert "message" in result
    assert result["message"] == "No matching face found"


@patch("src.deepface_service.DeepFace")
def test_verify_face_error(mock_deepface, deepface_service):
    """Test handling errors when verifying a face."""
    # Ensure there are faces in the database first
    mock_face = {
        "_id": ObjectId("6239121d1d9d3d6e8bbc66c0"),
        "name": "Test Person",
        "img_vectors": [0.1, 0.2, 0.3],
    }

    deepface_service.faces.find.return_value = [mock_face]

    # Now mock DeepFace.represent to raise an exception
    mock_deepface.represent.side_effect = Exception("Test exception")

    # Call the method with the exception in place
    result = deepface_service.verify_face("base64_image_data")

    # Assertions - our code should catch the exception and return an error response
    assert result["success"] is False
    assert "Error:" in result["message"]


def test_delete_face_success(deepface_service):
    """Test successfully deleting a face from the database."""
    # Setup mock result with deleted_count
    face_result = MagicMock()
    face_result.deleted_count = 1
    deepface_service.faces.delete_one.return_value = face_result

    # Setup mock attendance result
    attendance_result = MagicMock()
    attendance_result.deleted_count = 3
    deepface_service.db.attendance.delete_many.return_value = attendance_result

    # Call the method
    result = deepface_service.delete_face("6239121d1d9d3d6e8bbc66c0")

    # Verify MongoDB was called with correct parameters
    deepface_service.faces.delete_one.assert_called_once()
    deepface_service.db.attendance.delete_many.assert_called_once_with(
        {"face_id": "6239121d1d9d3d6e8bbc66c0"}
    )

    # Assertions on the result
    assert result["success"] is True
    assert result["message"] == "Face and 3 attendance records deleted successfully"


def test_delete_face_not_found(deepface_service):
    """Test deleting a face that does not exist in the database."""
    # Mock MongoDB delete_one with no matching document
    mock_result = MagicMock()
    mock_result.deleted_count = 0
    deepface_service.faces.delete_one.return_value = mock_result

    # Call the method
    result = deepface_service.delete_face("6239121d1d9d3d6e8bbc66c0")

    # Assertions
    assert result == {"success": False, "message": "Face not found"}


def test_delete_face_error(deepface_service):
    """Test handling errors when deleting a face."""
    # Mock MongoDB delete_one raising an exception
    deepface_service.faces.delete_one.side_effect = Exception("Test exception")

    # Call the method
    result = deepface_service.delete_face("6239121d1d9d3d6e8bbc66c0")

    # Assertions
    assert result == {"success": False, "message": "Error: Test exception"}


@patch("src.deepface_service.DeepFace")
@patch("src.deepface_service.ObjectId", side_effect=lambda x: x)
def test_replace_face_success(mock_objectid, mock_deepface, deepface_service):
    """Test successfully replacing a face in the database."""
    # Setup test data
    face_id = "6239121d1d9d3d6e8bbc66c0"
    image_data = "base64_image_data"
    name = "Updated Person"
    # Mock DeepFace.represent
    mock_embedding = {"embedding": [0.4, 0.5, 0.6]}
    mock_deepface.represent.return_value = [mock_embedding]
    # Mock MongoDB find_one and update_one
    mock_face = {
        "_id": face_id,
        "name": "Original Person",
        "img_vectors": [0.1, 0.2, 0.3],
    }
    deepface_service.faces.find_one.return_value = mock_face
    mock_result = MagicMock()
    mock_result.modified_count = 1
    deepface_service.faces.update_one.return_value = mock_result
    # Call the method
    result = deepface_service.replace_face(image_data, name, face_id)

    # Assertions
    mock_deepface.represent.assert_called_once_with(
        img_path=image_data, model_name="Facenet"
    )
    mock_objectid.assert_called_with(face_id)
    deepface_service.faces.find_one.assert_called_once()

    assert result == {
        "success": True,
        "face_id": face_id,
        "message": "Face updated successfully",
    }


@patch("src.deepface_service.ObjectId", side_effect=lambda x: x)
def test_replace_face_not_found(mock_objectid, deepface_service):
    """Test replacing a face that does not exist in the database."""
    # Setup
    face_id = "6239121d1d9d3d6e8bbc66c0"
    image_data = "base64_image_data"
    name = "Updated Person"

    # Mock MongoDB find_one to return None (face not found)
    deepface_service.faces.find_one.return_value = None

    # Call the method
    result = deepface_service.replace_face(image_data, name, face_id)

    # Assertions
    mock_objectid.assert_called_with(face_id)
    deepface_service.faces.find_one.assert_called_once()
    deepface_service.faces.update_one.assert_not_called()

    assert result == {"success": False, "message": "Face not found"}


def test_replace_face_update_failed(deepface_service):
    """Test when MongoDB update fails during face replacement."""
    # Setup
    face_id = "6239121d1d9d3d6e8bbc66c0"
    image_data = "base64_image_data"
    name = "Updated Person"

    # Mock DeepFace.represent
    mock_embedding = {"embedding": [0.4, 0.5, 0.6]}
    with patch("src.deepface_service.DeepFace") as mock_deepface:
        mock_deepface.represent.return_value = [mock_embedding]

        # Mock MongoDB find_one
        mock_face = {
            "_id": ObjectId(face_id),
            "name": "Original Person",
            "img_vectors": [0.1, 0.2, 0.3],
        }
        deepface_service.faces.find_one.return_value = mock_face

        # Mock MongoDB update_one with no modified documents
        mock_result = MagicMock()
        mock_result.modified_count = 0
        deepface_service.faces.update_one.return_value = mock_result

        # Call the method
        result = deepface_service.replace_face(image_data, name, face_id)

        # Assertions
        assert result == {"success": False, "message": "Failed to update face"}


@patch("src.deepface_service.DeepFace")
def test_replace_face_error(mock_deepface, deepface_service):
    """Test handling errors when replacing a face."""
    # Setup
    face_id = "6239121d1d9d3d6e8bbc66c0"
    image_data = "base64_image_data"
    name = "Updated Person"

    # Mock DeepFace.represent raising an exception
    mock_deepface.represent.side_effect = Exception("Test exception")

    # Call the method
    result = deepface_service.replace_face(image_data, name, face_id)

    # Assertions
    assert result == {"success": False, "message": "Error: Test exception"}
