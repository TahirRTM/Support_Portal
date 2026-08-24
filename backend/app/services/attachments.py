"""Secure attachment validation + scan + store pipeline.

Flow: validate (name/ext/mime/magic/size) -> scan (ClamAV) -> store -> record.
Rejected files never become downloadable and generate an audit event upstream.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

from app.core.exceptions import ValidationError
from app.providers.storage import get_storage
from app.services.clamav import scan_bytes

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf", ".txt", ".log",
    ".csv", ".doc", ".docx", ".xls", ".xlsx", ".zip",
}
ALLOWED_MIME = {
    "image/png", "image/jpeg", "image/gif", "image/webp", "application/pdf",
    "text/plain", "text/csv", "application/msword", "application/zip",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
DANGEROUS_EXTENSIONS = {
    ".exe", ".dll", ".bat", ".cmd", ".sh", ".js", ".jar", ".msi", ".scr",
    ".ps1", ".vbs", ".com", ".app", ".php", ".py",
}

# Magic-byte signatures for a few common types.
_MAGIC = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"%PDF-": "application/pdf",
    b"PK\x03\x04": "application/zip",  # also docx/xlsx
}


@dataclass(slots=True)
class ValidatedAttachment:
    original_filename: str
    content_type: str
    size_bytes: int
    storage_key: str
    sha256: str
    scan_signature: str | None


def _safe_filename(name: str) -> str:
    base = os.path.basename(name or "").replace("\x00", "")
    if not base or base in (".", ".."):
        raise ValidationError("Invalid filename.", code="bad_filename")
    if "/" in base or "\\" in base:
        raise ValidationError("Invalid filename.", code="bad_filename")
    return base[:400]


def _detect_magic(data: bytes) -> str | None:
    for sig, mime in _MAGIC.items():
        if data.startswith(sig):
            return mime
    return None


def validate_only(filename: str, content_type: str, data: bytes) -> None:
    """Synchronous validation (no I/O). Raises ValidationError on rejection."""
    name = _safe_filename(filename)
    ext = os.path.splitext(name)[1].lower()
    if ext in DANGEROUS_EXTENSIONS:
        raise ValidationError("File type not permitted.", code="dangerous_extension")
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError("File type not allowed.", code="extension_not_allowed")
    if content_type not in ALLOWED_MIME:
        raise ValidationError("Content type not allowed.", code="mime_not_allowed")
    if len(data) == 0:
        raise ValidationError("Empty file.", code="empty_file")
    if len(data) > MAX_ATTACHMENT_BYTES:
        raise ValidationError("File too large.", code="file_too_large")
    if b"\x00" in data[:8] and _detect_magic(data) is None:
        # Null bytes near the head with no known signature: suspicious.
        raise ValidationError("Malformed file.", code="null_bytes")
    magic = _detect_magic(data)
    # If we recognize a signature it must be consistent with a text/zip/image/pdf
    # family; a declared image that isn't one is rejected (MIME spoofing guard).
    if content_type.startswith("image/") and magic and not magic.startswith("image/"):
        raise ValidationError("File content does not match type.", code="mime_spoof")
    if content_type == "application/pdf" and magic and magic != "application/pdf":
        raise ValidationError("File content does not match type.", code="mime_spoof")


async def process_upload(filename: str, content_type: str, data: bytes) -> ValidatedAttachment:
    validate_only(filename, content_type, data)
    scan = await scan_bytes(data)
    if not scan.clean:
        raise ValidationError(
            "File failed security scan.", code="malware_detected",
            extra={"signature": scan.signature} if scan.signature else None,
        )
    ext = os.path.splitext(_safe_filename(filename))[1].lower()
    storage = get_storage()
    key = await storage.save(data, suffix=ext)
    return ValidatedAttachment(
        original_filename=_safe_filename(filename),
        content_type=content_type,
        size_bytes=len(data),
        storage_key=key,
        sha256=hashlib.sha256(data).hexdigest(),
        scan_signature=scan.signature,
    )
