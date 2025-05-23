"""Test configuration and fixtures for the machine learning client."""

import os
import sys
from unittest.mock import patch, MagicMock
import pytest

# Mock necessary modules before any tests are imported
sys.modules["deepface"] = MagicMock()
sys.modules["deepface.DeepFace"] = MagicMock()
sys.modules["pymongo"] = MagicMock()
sys.modules["pymongo.MongoClient"] = MagicMock()
sys.modules["bson"] = MagicMock()
sys.modules["bson.objectid"] = MagicMock()


# Set environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_variables():
    """Set environment variables for testing."""
    with patch.dict(
        os.environ,
        {"MONGO_URI": "mongodb://localhost:27017/", "DEEPFACE_THRESHOLD": "10"},
    ):
        yield
