"""ClamAV integration abstraction (INSTREAM over clamd TCP).

When ClamAV is disabled or unreachable, scanning fails closed for uploads
(rejects rather than silently approving) unless explicitly disabled in config.
"""
from __future__ import annotations

import asyncio
import struct
from dataclasses import dataclass

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass(slots=True)
class ScanResult:
    clean: bool
    signature: str | None = None
    error: str | None = None


async def scan_bytes(data: bytes) -> ScanResult:
    s = get_settings()
    if not s.clamav_enabled:
        # Explicitly disabled (e.g. local dev): treat as clean but record it.
        return ScanResult(clean=True, signature="scan_disabled")
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(s.clamav_host, s.clamav_port), timeout=10
        )
        writer.write(b"zINSTREAM\x00")
        chunk = data
        writer.write(struct.pack("!L", len(chunk)) + chunk)
        writer.write(struct.pack("!L", 0))
        await writer.drain()
        resp = await asyncio.wait_for(reader.read(4096), timeout=30)
        writer.close()
        text = resp.decode(errors="replace")
        if "OK" in text and "FOUND" not in text:
            return ScanResult(clean=True)
        if "FOUND" in text:
            sig = text.split(":", 1)[-1].replace("FOUND", "").strip()
            return ScanResult(clean=False, signature=sig)
        return ScanResult(clean=False, error=text.strip())
    except Exception as exc:  # pragma: no cover - network dependent
        log.warning("clamav_unreachable", error=str(exc))
        # Fail closed: unknown scan status must not approve the file.
        return ScanResult(clean=False, error="scanner_unavailable")
