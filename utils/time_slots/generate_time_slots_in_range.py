from models.field_optimizer.time_slot import TimeSlot
from utils.time_slots import generate_time_slots_for_week
from utils.datetime import is_time_between


def generate_time_slots_in_range(
    start_time: str,
    end_time: str,
    min_interval: int
) -> list[TimeSlot]:
    """
    Get filtered time slots within a specific time range for all days of the week.

    Args:
        start_time: Start time in HH:MM format
        end_time: End time in HH:MM format
        min_interval: Interval in minutes (15, 30 or 60)

    Returns:
        List of TimeSlot objects filtered by time range
    """
    all_weekly_time_slots = generate_time_slots_for_week(min_interval)
    available_time_slots = [
        time_slot for time_slot in all_weekly_time_slots
        if is_time_between(time_slot.time, start_time, end_time)
    ]

    return available_time_slots
