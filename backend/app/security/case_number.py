"""Secure, collision-resistant, non-sequential Case Number generation.

Format: SUP-<YEAR>-<10 Crockford base32 chars>, e.g. SUP-2026-4KQ2R9TB7X.

- Non-sequential: derived from os.urandom, not a DB sequence.
- Collision-resistant: 50 bits of entropy; caller enforces DB uniqueness.
- Normalized on input: uppercased, ambiguous chars folded (I->1, O->0, etc.).
- Never encodes or exposes the internal DB id.
"""
from __future__ import annotations

import os
import re

_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # Crockford: no I L O U
_RANDOM_LEN = 10
_PREFIX = "SUP"

# Normalization map for user-entered case numbers.
_FOLD = str.maketrans({"I": "1", "L": "1", "O": "0", "U": "V"})
_VALID_RE = re.compile(rf"^{_PREFIX}-\d{{4}}-[{_ALPHABET}]{{{_RANDOM_LEN}}}$")


def generate_case_number(year: int) -> str:
    chars = []
    # Rejection-free: map each random byte into the 32-char alphabet.
    for b in os.urandom(_RANDOM_LEN):
        chars.append(_ALPHABET[b % 32])
    return f"{_PREFIX}-{year}-{''.join(chars)}"


def normalize_case_number(raw: str) -> str | None:
    """Normalize and validate. Returns canonical form or None if invalid.

    Rejects injected/ambiguous input so it can be safely used in queries.
    """
    if not raw or len(raw) > 32:
        return None
    cleaned = raw.strip().upper().replace(" ", "")
    # Only fold the random segment, not the whole string, to keep prefix/year.
    parts = cleaned.split("-")
    if len(parts) != 3:
        return None
    prefix, year, rand = parts
    rand = rand.translate(_FOLD)
    candidate = f"{prefix}-{year}-{rand}"
    if not _VALID_RE.match(candidate):
        return None
    return candidate
