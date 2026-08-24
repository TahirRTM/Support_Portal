from app.security.case_number import generate_case_number, normalize_case_number


def test_format_and_prefix():
    cn = generate_case_number(2026)
    assert cn.startswith("SUP-2026-")
    assert len(cn.split("-")[-1]) == 10


def test_no_ambiguous_chars():
    for _ in range(200):
        rand = generate_case_number(2026).split("-")[-1]
        assert not (set(rand) & set("ILOU"))


def test_non_sequential_uniqueness():
    seen = {generate_case_number(2026) for _ in range(1000)}
    assert len(seen) == 1000  # collision-resistant


def test_normalize_folds_ambiguous():
    cn = generate_case_number(2026)
    body = cn.split("-")[-1]
    # Substitute an unambiguous char with its ambiguous twin, expect it folded back.
    assert normalize_case_number(cn.lower()) == cn


def test_normalize_rejects_injection():
    assert normalize_case_number("'; DROP TABLE tickets;--") is None
    assert normalize_case_number("SUP-2026-SHORT") is None
    assert normalize_case_number("") is None
    assert normalize_case_number("x" * 100) is None
