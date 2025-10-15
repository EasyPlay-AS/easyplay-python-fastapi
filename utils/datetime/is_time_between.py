from datetime import time


def is_time_between(time_str: str, from_time: str, to_time: str) -> bool:
    """
    Check if a time string is between two other time strings.
    Handles cases where the time range crosses midnight.

    Args:
        time_str: The time to check in HH:MM format
        from_time: The start time of the range in HH:MM format
        to_time: The end time of the range in HH:MM format

    Returns:
        True if the time is between the start and end times, False otherwise
    """
    t = time.fromisoformat(time_str)
    start = time.fromisoformat(from_time)
    end = time.fromisoformat(to_time)

    if start <= end:
        return start <= t < end
    else:
        return t >= start or t < end
