from datetime import datetime


def convert_time_to_datetime(time_str: str) -> datetime:
    """
    Convert a time string (HH:MM) to a datetime object with today's date.
    """
    hours, minutes = map(int, time_str.split(":"))
    date = datetime.now().replace(hour=hours, minute=minutes, second=0, microsecond=0)
    return date
