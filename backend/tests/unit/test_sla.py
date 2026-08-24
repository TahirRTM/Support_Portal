from datetime import datetime, timezone
from app.services.sla import add_business_minutes


def test_within_same_business_day():
    start = datetime(2026, 8, 24, 9, 0, tzinfo=timezone.utc)  # Monday 09:00
    due = add_business_minutes(start, 120)
    assert due.hour == 11 and due.minute == 0


def test_rolls_over_weekend():
    start = datetime(2026, 8, 28, 16, 0, tzinfo=timezone.utc)  # Friday 16:00
    due = add_business_minutes(start, 120)  # 1h Fri + 1h Mon
    assert due.weekday() == 0  # Monday
