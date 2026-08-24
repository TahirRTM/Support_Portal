import os
os.environ.setdefault("ACCESS_TOKEN_SECRET", "unit-test-access-secret-please")
from app.security import otp


def test_length_and_numeric():
    code = otp.generate_otp()
    assert code.isdigit()
    assert len(code) == 6


def test_hash_is_bound_to_ticket():
    code = "123456"
    h1 = otp.hash_otp(code, ticket_id="a")
    h2 = otp.hash_otp(code, ticket_id="b")
    assert h1 != h2  # same code, different ticket => different hash


def test_verify_roundtrip():
    code = otp.generate_otp()
    h = otp.hash_otp(code, ticket_id="t1")
    assert otp.verify_otp(code, ticket_id="t1", stored_hash=h)
    assert not otp.verify_otp("000000", ticket_id="t1", stored_hash=h)
