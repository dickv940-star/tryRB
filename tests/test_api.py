import io

from fastapi.testclient import TestClient
from PIL import Image

import server


client = TestClient(server.app)
TOKEN = server.API_TOKEN


def make_png():
    image = Image.new("RGB", (8, 8), (220, 40, 30))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_health_is_available_without_token():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "tryRB"
    assert "birefnet-general" in response.json()["models"]


def test_remove_requires_bearer_token():
    response = client.post(
        "/api/remove",
        files={"file": ("photo.png", make_png(), "image/png")},
    )
    assert response.status_code == 401


def test_remove_rejects_invalid_token():
    response = client.post(
        "/api/remove",
        headers={"Authorization": "Bearer wrong-token"},
        files={"file": ("photo.png", make_png(), "image/png")},
    )
    assert response.status_code == 401


def test_remove_rejects_unsupported_media_type_before_inference():
    response = client.post(
        "/api/remove",
        headers={"Authorization": f"Bearer {TOKEN}"},
        files={"file": ("payload.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 415


def test_remove_rejects_unknown_model_before_inference():
    response = client.post(
        "/api/remove",
        headers={"Authorization": f"Bearer {TOKEN}"},
        data={"model": "not-a-real-model"},
        files={"file": ("photo.png", make_png(), "image/png")},
    )
    assert response.status_code == 400


def test_remove_rejects_corrupt_image_before_inference():
    response = client.post(
        "/api/remove",
        headers={"Authorization": f"Bearer {TOKEN}"},
        files={"file": ("photo.png", b"not really a png", "image/png")},
    )
    assert response.status_code == 400
