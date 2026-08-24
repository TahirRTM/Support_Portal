"""Secure client IP resolution.

X-Forwarded-For is only honoured when the immediate peer is a configured trusted
proxy AND forwarded headers are explicitly enabled. Otherwise the raw socket
peer is used. This prevents trivial IP spoofing of the rate limiter.
"""
from __future__ import annotations

import ipaddress

from fastapi import Request

from app.core.config import get_settings


def _is_trusted(peer: str, trusted: list[str]) -> bool:
    try:
        ip = ipaddress.ip_address(peer)
    except ValueError:
        return False
    for entry in trusted:
        try:
            if "/" in entry:
                if ip in ipaddress.ip_network(entry, strict=False):
                    return True
            elif ip == ipaddress.ip_address(entry):
                return True
        except ValueError:
            continue
    return False


def resolve_client_ip(request: Request) -> str:
    settings = get_settings()
    peer = request.client.host if request.client else "0.0.0.0"
    if not settings.trust_forwarded_headers:
        return peer
    if not _is_trusted(peer, settings.trusted_proxies):
        return peer
    xff = request.headers.get("x-forwarded-for")
    if not xff:
        return peer
    # Take the left-most untrusted address in the chain.
    for candidate in [p.strip() for p in xff.split(",")]:
        if candidate and not _is_trusted(candidate, settings.trusted_proxies):
            try:
                ipaddress.ip_address(candidate)
                return candidate
            except ValueError:
                continue
    return peer
