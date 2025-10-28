import itertools
from models.field_optimizer.field_optimizer_payload import TimeRange
from utils.time_slots.generate_time_slots_in_range import generate_time_slots_in_range
from utils.time_slots.get_timeslot_ids_by_week_day import get_timeslot_ids_by_week_day

TIME_SLOT_DURATION_MINUTES = 15


def convert_time_range_to_timeslot_ids(
    time_range: TimeRange,
    timeslot_to_index_map: dict[int, int]
) -> list[int]:
    """
    Convert a time range to a list of timeslot ids.

    Args:
        time_range: The time range to convert
        timeslot_to_index_map: The full mapping of timeslot ids to indexes
    Returns:
        A ordered list of timeslot ids mapped to indexes
    """

    time_slots_in_range = generate_time_slots_in_range(
        time_range.start_time, time_range.end_time, TIME_SLOT_DURATION_MINUTES)

    timeslot_ids_by_week_day = get_timeslot_ids_by_week_day(
        time_slots_in_range)

    timeslot_ids_by_day_index = [
        timeslot_ids_by_week_day[day_index]
        for day_index in sorted(time_range.day_indexes)
    ]

    timeslot_ids_flattened = list(itertools.chain(*timeslot_ids_by_day_index))
    timeslot_ids_indexes = [
        timeslot_to_index_map[timeslot_id]
        for timeslot_id in timeslot_ids_flattened
    ]

    return timeslot_ids_indexes
