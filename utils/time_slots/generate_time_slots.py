from utils.datetime import convert_time_to_datetime


def generate_time_slots(
    start_time: str,
    end_time: str,
    min_interval: int
) -> list[str]:
    """
    Generate a list of time slots between start_time and end_time with given interval.

    Args:
        start_time: Start time in HH:MM format
        end_time: End time in HH:MM format
        min_interval: Interval in minutes (15, 30 or 60)

    Returns:
        List of time strings in HH:MM format
    """
    valid_min_intervals = [15, 30, 60]
    if min_interval not in valid_min_intervals:
        raise ValueError("min_interval must be 15, 30 or 60")

    slots = []
    start_datetime = convert_time_to_datetime(start_time)
    end_datetime = convert_time_to_datetime(end_time)

    current_slot = start_datetime
    while current_slot <= end_datetime:
        slots.append(current_slot.strftime("%H:%M"))

        # Calculate new minute value and handle overflow
        new_minute = current_slot.minute + min_interval
        new_hour = current_slot.hour + new_minute // 60
        new_minute = new_minute % 60

        # Handle hour overflow (hours can go beyond 23)
        if new_hour >= 24:
            # If we go beyond 23:59, we should stop the loop
            # This happens when we've generated all slots for the day
            break

        current_slot = current_slot.replace(
            hour=new_hour,
            minute=new_minute
        )

    return slots
