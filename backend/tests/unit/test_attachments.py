import pytest
from app.core.exceptions import ValidationError
from app.services.attachments import validate_only

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


def test_accepts_valid_png():
    validate_only("shot.png", "image/png", PNG)


def test_rejects_executable():
    with pytest.raises(ValidationError):
        validate_only("virus.exe", "image/png", PNG)


def test_rejects_path_traversal_name():
    with pytest.raises(ValidationError):
        validate_only("../../etc/passwd", "text/plain", b"hello")


def test_rejects_mime_spoof():
    with pytest.raises(ValidationError):
        validate_only("fake.png", "image/png", b"%PDF-1.4 not a png")


def test_rejects_oversize():
    with pytest.raises(ValidationError):
        validate_only("big.png", "image/png", b"\x89PNG\r\n\x1a\n" + b"0" * (11 * 1024 * 1024))
