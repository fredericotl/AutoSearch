from datetime import datetime
from app.core.clock import now

def test_now_returns_naive_datetime():
    current_time = now()
    assert isinstance(current_time, datetime)
    assert current_time.tzinfo is None