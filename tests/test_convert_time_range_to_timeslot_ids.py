
from models.field_optimizer.field_optimizer_payload import TimeRange
from utils.field_optimizer import (
    convert_time_range_to_timeslot_ids
)


TIME_SLOT_DURATION_MINUTES = 15


def test_with_all_days():
    # Arrange
    time_range = TimeRange(
        start_time="17:00",
        end_time="18:00",
        day_indexes=[0, 1, 2, 3, 4, 5, 6]
    )

    # Act
    timeslot_ids = convert_time_range_to_timeslot_ids(time_range)

    # Assert
    expected_timeslot_ids = [
        1, 2, 3, 4,
        5, 6, 7, 8,
        9, 10, 11, 12,
        13, 14, 15, 16,
        17, 18, 19, 20,
        21, 22, 23, 24,
        25, 26, 27, 28
    ]
    assert timeslot_ids == expected_timeslot_ids


def test_with_limited_days():
    # Arrange
    time_range = TimeRange(
        start_time="17:00",
        end_time="18:00",
        day_indexes=[1, 2, 3]
    )

    # Act
    timeslot_ids = convert_time_range_to_timeslot_ids(time_range)

    # Assert
    expected_timeslot_ids = [
        1, 2, 3, 4,
        5, 6, 7, 8,
        9, 10, 11, 12,
    ]

    assert timeslot_ids == expected_timeslot_ids
