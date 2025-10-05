"""
Timezone utilities for Asia/Almaty (UTC+5) timezone handling
"""
from datetime import datetime, timedelta
import pytz
from config.settings import settings


# Astana timezone
ASTANA_TZ = pytz.timezone(settings.TIMEZONE)


def get_current_time_astana() -> datetime:
    """
    Get current time in Asia/Almaty timezone

    Returns:
        datetime: Current time in Astana timezone
    """
    return datetime.now(ASTANA_TZ)


def is_working_hours(dt: datetime = None) -> bool:
    """
    Check if given datetime is within working hours (10:00-18:00 Astana time)

    Args:
        dt: Datetime to check (defaults to current time)

    Returns:
        bool: True if within working hours, False otherwise
    """
    if dt is None:
        dt = get_current_time_astana()

    # Convert to Astana timezone if not already
    if dt.tzinfo is None:
        dt = ASTANA_TZ.localize(dt)
    else:
        dt = dt.astimezone(ASTANA_TZ)

    # Check if weekday (Monday=0, Sunday=6)
    if not is_working_day(dt):
        return False

    # Check if within working hours
    hour = dt.hour
    return settings.WORKING_HOURS_START <= hour < settings.WORKING_HOURS_END


def is_working_day(dt: datetime = None) -> bool:
    """
    Check if given datetime is a working day (Monday-Friday)

    Args:
        dt: Datetime to check (defaults to current time)

    Returns:
        bool: True if working day, False if weekend
    """
    if dt is None:
        dt = get_current_time_astana()

    # Monday=0, Sunday=6
    return dt.weekday() < 5


def get_next_working_time(dt: datetime = None) -> datetime:
    """
    Get next available working time (10:00-18:00, Mon-Fri)

    Args:
        dt: Starting datetime (defaults to current time)

    Returns:
        datetime: Next available working time
    """
    if dt is None:
        dt = get_current_time_astana()

    # Convert to Astana timezone if not already
    if dt.tzinfo is None:
        dt = ASTANA_TZ.localize(dt)
    else:
        dt = dt.astimezone(ASTANA_TZ)

    # If already in working hours, return as is
    if is_working_hours(dt):
        return dt

    # If after working hours (>= 18:00), move to next day 10:00
    if dt.hour >= settings.WORKING_HOURS_END:
        next_day = dt + timedelta(days=1)
        dt = dt.replace(hour=settings.WORKING_HOURS_START, minute=0, second=0, microsecond=0)
        dt = dt + timedelta(days=1)

    # If before working hours (< 10:00), set to 10:00 same day
    elif dt.hour < settings.WORKING_HOURS_START:
        dt = dt.replace(hour=settings.WORKING_HOURS_START, minute=0, second=0, microsecond=0)

    # Skip weekends
    while not is_working_day(dt):
        dt = dt + timedelta(days=1)

    return dt


def format_datetime_for_user(dt: datetime) -> str:
    """
    Format datetime for user display in Russian

    Args:
        dt: Datetime to format

    Returns:
        str: Formatted string like "15 октября в 14:30"
    """
    # Convert to Astana timezone
    if dt.tzinfo is None:
        dt = ASTANA_TZ.localize(dt)
    else:
        dt = dt.astimezone(ASTANA_TZ)

    # Month names in Russian
    months_ru = {
        1: "января", 2: "февраля", 3: "марта", 4: "апреля",
        5: "мая", 6: "июня", 7: "июля", 8: "августа",
        9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
    }

    day = dt.day
    month = months_ru[dt.month]
    time_str = dt.strftime("%H:%M")

    return f"{day} {month} в {time_str}"


def hours_since(dt: datetime) -> int:
    """
    Calculate hours passed since given datetime

    Args:
        dt: Past datetime

    Returns:
        int: Hours passed
    """
    if dt.tzinfo is None:
        dt = ASTANA_TZ.localize(dt)

    current = get_current_time_astana()
    delta = current - dt
    return int(delta.total_seconds() / 3600)
