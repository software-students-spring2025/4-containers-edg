"""Flask application for face recognition operations using DeepFace.

This module provides endpoints for adding, verifying, updating, and deleting faces
using a DeepFace service implementation.
"""

from flask import Flask, jsonify, request
from src.deepface_service import DeepFaceService

app = Flask(__name__)

df = DeepFaceService()


@app.route("/")
def index():
    """Return a welcome message for the root endpoint."""
    return "Welcome to the Machine Learning Client"


@app.route("/faces", methods=["POST"])
def add_face():
    """Add a new face to the database.

    Requires a JSON payload with 'img' (base64 image) and 'name' fields.
    """
    json_data = request.get_json()

    if "img" not in json_data or "name" not in json_data:
        return (
            jsonify(
                {"success": False, "message": "Missing required fields (img, name)"}
            ),
            400,
        )

    img = json_data["img"]
    name = json_data["name"]
    res = df.add_face(img, name)

    return res, 201


@app.route("/faces/verify", methods=["POST"])
def verify_face():
    """Verify a face against stored faces in the database.

    Requires a JSON payload with 'img' (base64 image) field.
    """
    json_data = request.get_json()

    if "img" not in json_data:
        return (
            jsonify({"success": False, "message": "Missing required fields (img)"}),
            400,
        )

    img = json_data["img"]
    res = df.verify_face(img)

    return res, 200


@app.route("/faces/<face_id>", methods=["DELETE"])
def delete_face(face_id):
    """Delete a face from the database by its ID.

    Args:
        face_id: The ID of the face to delete.
    """
    res = df.delete_face(face_id)

    return res, 200


@app.route("/faces/<face_id>", methods=["PUT"])
def update_face(face_id):
    """Update an existing face in the database.

    Args:
        face_id: The ID of the face to update.

    Requires a JSON payload with 'img' (base64 image) and 'name' fields.
    """
    json_data = request.get_json()

    if "img" not in json_data or "name" not in json_data:
        return (
            jsonify(
                {"success": False, "message": "Missing required fields (img, name)"}
            ),
            400,
        )

    img = json_data["img"]
    name = json_data["name"]

    res = df.replace_face(img, name, face_id)

    return res, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005)
