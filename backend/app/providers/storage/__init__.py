"""Storage abstraction: local FS (dev) and S3-compatible (prod).

Physical paths are never returned to clients; callers receive opaque storage
keys and use protected download endpoints / signed URLs.
"""
from __future__ import annotations

import abc
import os
import uuid

from app.core.config import get_settings


class StorageBackend(abc.ABC):
    @abc.abstractmethod
    async def save(self, data: bytes, *, suffix: str) -> str: ...
    @abc.abstractmethod
    async def load(self, key: str) -> bytes: ...
    @abc.abstractmethod
    async def delete(self, key: str) -> None: ...


class LocalStorage(StorageBackend):
    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def _path(self, key: str) -> str:
        # Prevent traversal: keys are opaque and validated to a flat namespace.
        if "/" in key or ".." in key or "\\" in key:
            raise ValueError("invalid storage key")
        return os.path.join(self.base_dir, key)

    async def save(self, data: bytes, *, suffix: str) -> str:
        key = f"{uuid.uuid4().hex}{suffix}"
        with open(self._path(key), "wb") as f:
            f.write(data)
        return key

    async def load(self, key: str) -> bytes:
        with open(self._path(key), "rb") as f:
            return f.read()

    async def delete(self, key: str) -> None:
        try:
            os.remove(self._path(key))
        except FileNotFoundError:
            pass


class S3Storage(StorageBackend):
    """S3-compatible storage. Uses boto3 when available/configured."""

    def __init__(self) -> None:
        self.s = get_settings()

    def _client(self):  # pragma: no cover - requires boto3 + network
        import boto3  # type: ignore
        return boto3.client("s3", endpoint_url=self.s.s3_endpoint_url or None,
                            region_name=self.s.s3_region)

    async def save(self, data: bytes, *, suffix: str) -> str:  # pragma: no cover
        key = f"{uuid.uuid4().hex}{suffix}"
        self._client().put_object(Bucket=self.s.s3_bucket, Key=key, Body=data)
        return key

    async def load(self, key: str) -> bytes:  # pragma: no cover
        obj = self._client().get_object(Bucket=self.s.s3_bucket, Key=key)
        return obj["Body"].read()

    async def delete(self, key: str) -> None:  # pragma: no cover
        self._client().delete_object(Bucket=self.s.s3_bucket, Key=key)


def get_storage() -> StorageBackend:
    s = get_settings()
    if s.storage_backend == "s3":
        return S3Storage()
    return LocalStorage(s.storage_local_dir)
