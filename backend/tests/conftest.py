"""Shared pytest fixtures.

Integration/e2e tests require PostgreSQL + Redis. When unavailable they are
skipped rather than failing, so the suite reflects the real environment.
"""
from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


def _has_db() -> bool:
    return bool(os.getenv("TEST_DATABASE_URL"))


requires_db = pytest.mark.skipif(not _has_db(), reason="no TEST_DATABASE_URL")
