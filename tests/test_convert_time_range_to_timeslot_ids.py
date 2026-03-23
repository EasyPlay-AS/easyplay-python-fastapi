from utils.field_optimizer.convert_time_range_to_timeslot_ids import (
    convert_time_range_to_timeslot_ids,
    convert_time_ranges_to_timeslot_ids,
)
from models.field_optimizer.field_optimizer_payload import TimeRange
from utils.time_slots.generate_time_slots_in_range import generate_time_slots_in_range
from utils.time_slots.get_timeslot_ids_by_week_day import get_timeslot_ids_by_week_day
from utils.common import create_number_to_index_mapping
import itertools


def _build_timeslot_map(start_time: str, end_time: str):
    """Helper to build a timeslot_to_index_map for a given time window."""
    time_slots = generate_time_slots_in_range(start_time, end_time, 15)
    ids_by_day = get_timeslot_ids_by_week_day(time_slots)
    all_ids = list(itertools.chain(*ids_by_day))
    mapping = create_number_to_index_mapping(all_ids)
    return mapping['number_to_index_map']


def test_with_all_days():
    timeslot_map = _build_timeslot_map("17:00", "18:00")
    time_range = TimeRange(
        start_time="17:00",
        end_time="18:00",
        day_indexes=[0, 1, 2, 3, 4, 5, 6]
    )

    timeslot_ids = convert_time_range_to_timeslot_ids(
        time_range, timeslot_map)

    # 4 slots per day * 7 days = 28
    assert len(timeslot_ids) == 28


def test_with_limited_days():
    timeslot_map = _build_timeslot_map("17:00", "18:00")
    time_range = TimeRange(
        start_time="17:00",
        end_time="18:00",
        day_indexes=[1, 2, 3]
    )

    timeslot_ids = convert_time_range_to_timeslot_ids(
        time_range, timeslot_map)

    # 4 slots per day * 3 days = 12
    assert len(timeslot_ids) == 12


def test_duration_filter_blocks_late_starts():
    """A 90-min activity (6 slots) with end_time=22:00 should not start after 20:30."""
    timeslot_map = _build_timeslot_map("16:00", "22:00")
    time_range = TimeRange(
        start_time="16:00",
        end_time="22:00",
        day_indexes=[0]  # Monday only
    )

    # Without duration filter (duration_slots=1, default 15-min)
    ids_no_filter = convert_time_range_to_timeslot_ids(
        time_range, timeslot_map, duration_slots=1)
    # Last slot should be 21:45 (the slot starting at 21:45, ending at 22:00)
    assert len(ids_no_filter) == 24  # 6 hours * 4 slots/hour

    # With duration filter (90 min = 6 slots)
    ids_filtered = convert_time_range_to_timeslot_ids(
        time_range, timeslot_map, duration_slots=6)
    # Last valid start: 20:30 (20:30 + 90min = 22:00)
    # 16:00 to 20:30 = 4.5 hours = 18 slots + 1 = 19
    assert len(ids_filtered) == 19  # 16:00, 16:15, ..., 20:15, 20:30


def test_duration_filter_boundary_exact():
    """An activity ending exactly at end_time should be allowed."""
    timeslot_map = _build_timeslot_map("16:00", "22:00")
    time_range = TimeRange(
        start_time="20:00",
        end_time="22:00",
        day_indexes=[0]
    )

    # 30 min activity (2 slots): last valid start = 21:30
    ids = convert_time_range_to_timeslot_ids(
        time_range, timeslot_map, duration_slots=2)
    # 20:00, 20:15, 20:30, 20:45, 21:00, 21:15, 21:30 = 7 slots
    assert len(ids) == 7


def test_duration_filter_with_multiple_ranges():
    """Plural function should also apply duration filtering."""
    timeslot_map = _build_timeslot_map("16:00", "22:00")
    ranges = [
        TimeRange(start_time="16:00", end_time="18:00", day_indexes=[0]),
        TimeRange(start_time="16:00", end_time="22:00", day_indexes=[1]),
    ]

    # 60 min activity (4 slots)
    ids = convert_time_ranges_to_timeslot_ids(
        ranges, timeslot_map, duration_slots=4)

    # Monday 16:00-18:00: last valid start = 17:00 → 5 slots (16:00..17:00)
    # Tuesday 16:00-22:00: last valid start = 21:00 → 21 slots (16:00..21:00)
    # Total unique = 5 + 21 = 26
    assert len(ids) == 26


def test_duration_exceeds_window_returns_empty():
    """When duration is longer than the window, no start times are valid."""
    timeslot_map = _build_timeslot_map("16:00", "22:00")
    time_range = TimeRange(
        start_time="17:00",
        end_time="18:00",
        day_indexes=[0]
    )

    # 90 min activity in a 60 min window → no valid starts
    ids = convert_time_range_to_timeslot_ids(
        time_range, timeslot_map, duration_slots=6)
    assert len(ids) == 0


def test_duration_equals_window():
    """When duration exactly fills the window, only the first slot is valid."""
    timeslot_map = _build_timeslot_map("16:00", "22:00")
    time_range = TimeRange(
        start_time="17:00",
        end_time="18:00",
        day_indexes=[0]
    )

    # 60 min activity in a 60 min window → only 17:00 is valid
    ids = convert_time_range_to_timeslot_ids(
        time_range, timeslot_map, duration_slots=4)
    assert len(ids) == 1
