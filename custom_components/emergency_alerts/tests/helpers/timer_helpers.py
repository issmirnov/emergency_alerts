"""Time manipulation utilities for testing timers."""

from datetime import datetime, timedelta
from typing import Callable, Any
from contextlib import contextmanager

try:
    from freezegun import freeze_time
    FREEZEGUN_AVAILABLE = True
except ImportError:
    FREEZEGUN_AVAILABLE = False
    try:
        from time_machine import travel
        TIME_MACHINE_AVAILABLE = True
    except ImportError:
        TIME_MACHINE_AVAILABLE = False


@contextmanager
def freeze_time_at(target_time: datetime | str):
    """Freeze time at a specific datetime."""
    if FREEZEGUN_AVAILABLE:
        with freeze_time(target_time):
            yield
    elif TIME_MACHINE_AVAILABLE:
        from time_machine import travel
        with travel(target_time):
            yield
    else:
        # No-op if neither library is available
        yield


@contextmanager
def advance_time(seconds: int):
    """Advance time by a number of seconds."""
    if FREEZEGUN_AVAILABLE:
        from freezegun import freeze_time
        current_time = datetime.now()
        target_time = current_time + timedelta(seconds=seconds)
        with freeze_time(target_time):
            yield
    elif TIME_MACHINE_AVAILABLE:
        from time_machine import travel
        current_time = datetime.now()
        target_time = current_time + timedelta(seconds=seconds)
        with travel(target_time):
            yield
    else:
        # No-op if neither library is available
        yield


def get_future_time(seconds: int) -> datetime:
    """Get a datetime that is N seconds in the future."""
    return datetime.now() + timedelta(seconds=seconds)


def get_past_time(seconds: int) -> datetime:
    """Get a datetime that is N seconds in the past."""
    return datetime.now() - timedelta(seconds=seconds)
