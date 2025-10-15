from models.field_optimizer.time_slot import TimeSlot
from utils.time_slots import generate_time_slots


def generate_time_slots_for_week(min_interval: int) -> list[TimeSlot]:
    """
    Generate time slots for all 7 days of the week with given interval.

    Args:
        min_interval: Interval in minutes (15, 30 or 60)

    Returns:
        List of TimeSlot objects for the entire week
    """
    start_time = "00:00"
    end_time = "23:59"
    time_slots = generate_time_slots(start_time, end_time, min_interval)

    days = 7
    current_time_slot = 1

    time_slots_map = []

    for i in range(days):
        for current_time in time_slots:
            time_slots_map.append(TimeSlot(
                id=current_time_slot,
                time=current_time,
                week_day_index=i,
                duration_minutes=min_interval
            ))
            current_time_slot += 1

    return time_slots_map
