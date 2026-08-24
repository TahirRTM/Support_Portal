from app.security.passwords import hash_password, verify_password


def test_hash_and_verify():
    h = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", h)
    assert not verify_password("wrong", h)


def test_verify_none_is_timing_safe_false():
    # Unknown user path: still returns False without raising.
    assert verify_password("anything", None) is False
