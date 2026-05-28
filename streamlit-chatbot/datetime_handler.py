"""
datetime_handler.py - Real-time date and time utilities.

Fetches accurate current date, time, and day from the system clock
so the chatbot always responds with correct temporal information.
"""

from datetime import datetime

# Keywords that indicate the user is asking about date or time
_DATE_KEYWORDS = ["date", "today", "day", "month", "year", "tomorrow", "yesterday"]
_TIME_KEYWORDS = ["time", "clock", "hour", "minute", "second", "now"]
_ALL_KEYWORDS = _DATE_KEYWORDS + _TIME_KEYWORDS


def get_current_datetime_info() -> dict:
    """
    Return a dict with human-readable date/time fields from the system clock.

    Returns:
        dict with keys: date, time, day, full_datetime, iso
    """
    now = datetime.now()
    return {
        "date": now.strftime("%B %d, %Y"),           # e.g. May 27, 2026
        "time": now.strftime("%I:%M %p"),             # e.g. 10:45 AM
        "day": now.strftime("%A"),                    # e.g. Wednesday
        "full_datetime": now.strftime("%A, %B %d, %Y at %I:%M %p"),
        "iso": now.isoformat(),
    }


def is_datetime_query(text: str) -> bool:
    """
    Return True if the user's message appears to be asking about date or time.

    Args:
        text: Raw user input string.

    Returns:
        bool
    """
    text_lower = text.lower()
    return any(kw in text_lower for kw in _ALL_KEYWORDS)


def build_datetime_context() -> str:
    """
    Build a system-level context string with the current real date and time.
    Injected into the system prompt so Gemini always answers accurately.

    Returns:
        str: Formatted datetime context block.
    """
    info = get_current_datetime_info()
    return (
        f"[Real-time system information]\n"
        f"Current date : {info['date']}\n"
        f"Current day  : {info['day']}\n"
        f"Current time : {info['time']}\n"
        f"Full         : {info['full_datetime']}\n"
        f"Always use the above values when the user asks about today's date, "
        f"current time, or what day it is. Do not guess or use training data dates.\n"
    )
