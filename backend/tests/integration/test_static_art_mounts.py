"""Regression tests: generated-art static mounts must serve the SAME
directories the routes write to. A path mismatch here means every
generated portrait/scene URL 404s even though the file exists."""
import os

from app.main import create_app
from app.api.routes.game import SCENE_IMAGES_DIR
from app.api.routes.characters import PORTRAITS_DIR


def _mount_dir(app, name: str) -> str:
    for route in app.routes:
        if getattr(route, "name", None) == name:
            return os.path.abspath(route.app.directory)
    raise AssertionError(f"static mount {name!r} not found")


def test_scene_images_mount_serves_write_dir():
    app = create_app()
    assert _mount_dir(app, "scene-images") == os.path.abspath(SCENE_IMAGES_DIR)


def test_portraits_mount_serves_write_dir():
    app = create_app()
    assert _mount_dir(app, "portraits") == os.path.abspath(PORTRAITS_DIR)


def test_generated_scene_file_is_served(tmp_path):
    """A file written into SCENE_IMAGES_DIR is retrievable at its URL."""
    from starlette.testclient import TestClient

    os.makedirs(SCENE_IMAGES_DIR, exist_ok=True)
    probe = os.path.join(SCENE_IMAGES_DIR, "_test_probe.jpg")
    with open(probe, "wb") as f:
        f.write(b"\xff\xd8\xff\xe0test")
    try:
        client = TestClient(create_app())
        res = client.get("/api/scene-images/_test_probe.jpg")
        assert res.status_code == 200
    finally:
        os.remove(probe)
