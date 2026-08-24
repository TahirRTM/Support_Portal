"""Argon2id password hashing with timing-safe verification."""
from __future__ import annotations

from argon2 import PasswordHasher
from argon2 import exceptions as argon2_exc

# Argon2id parameters tuned for interactive auth.
_hasher = PasswordHasher(time_cost=3, memory_cost=64 * 1024, parallelism=2)

# Precomputed hash used to equalize timing for unknown users (anti-enumeration).
_DUMMY_HASH = _hasher.hash("timing-equalization-placeholder")


def hash_password(raw: str) -> str:
    return _hasher.hash(raw)


def verify_password(raw: str, stored_hash: str | None) -> bool:
    target = stored_hash or _DUMMY_HASH
    try:
        _hasher.verify(target, raw)
        return stored_hash is not None
    except (argon2_exc.VerifyMismatchError, argon2_exc.VerificationError,
            argon2_exc.InvalidHash):
        return False


def needs_rehash(stored_hash: str) -> bool:
    try:
        return _hasher.check_needs_rehash(stored_hash)
    except argon2_exc.InvalidHash:
        return True
