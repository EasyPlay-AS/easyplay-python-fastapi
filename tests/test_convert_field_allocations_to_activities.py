from utils.field_optimizer.convert_field_allocations_to_activities import (
    convert_field_allocations_to_activities
)
from models.field_optimizer.field_allocation import FieldAllocation
from models.field_optimizer.field_activity import FieldActivity


TIMESLOT_IDS = [
    [1, 2, 3],  # Day 1 timeslots
    [4, 5, 6],  # Day 2 timeslots
    [7, 8, 9],  # ...
    [10, 11, 12],
    [13, 14, 15],
    [16, 17, 18],
    [19, 20, 21],
    [22, 23, 24],
]


def test_single_activity():
    # Arrange
    field_allocations = [
        FieldAllocation(field="field1", group="group1", timeslot_id=1, size=1),
        FieldAllocation(field="field1", group="group1", timeslot_id=2, size=1),
        FieldAllocation(field="field1", group="group1", timeslot_id=3, size=1),
    ]

    # Act
    activities = convert_field_allocations_to_activities(
        field_allocations, TIMESLOT_IDS)

    # Assert
    expected_activities = [
        FieldActivity(field="field1", group="group1",
                      start_timeslot=1, end_timeslot=3, duration=3, size=1),
    ]
    assert activities == expected_activities


def test_multiple_fields():
    # Arrange
    field_allocations = [
        FieldAllocation(field="field1", group="group1", timeslot_id=1, size=1),
        FieldAllocation(field="field1", group="group1", timeslot_id=2, size=1),
        FieldAllocation(field="field1", group="group1", timeslot_id=3, size=1),
        FieldAllocation(field="field2", group="group2", timeslot_id=1, size=1),
        FieldAllocation(field="field2", group="group2", timeslot_id=2, size=1),
        FieldAllocation(field="field2", group="group2", timeslot_id=3, size=1),
    ]

    # Act
    activities = convert_field_allocations_to_activities(
        field_allocations, TIMESLOT_IDS)

    # Assert
    expected_activities = [
        FieldActivity(field="field1", group="group1",
                      start_timeslot=1, end_timeslot=3, duration=3, size=1),
        FieldActivity(field="field2", group="group2",
                      start_timeslot=1, end_timeslot=3, duration=3, size=1),
    ]
    assert activities == expected_activities


def test_allocations_across_day_boundaries():
    # Arrange
    field_allocations = [
        FieldAllocation(field="field1", group="group1", timeslot_id=1, size=1),
        FieldAllocation(field="field1", group="group1", timeslot_id=2, size=1),
        FieldAllocation(field="field1", group="group1", timeslot_id=3, size=1),
        FieldAllocation(field="field1", group="group1", timeslot_id=4, size=1),
        FieldAllocation(field="field1", group="group1", timeslot_id=5, size=1),
        FieldAllocation(field="field1", group="group1", timeslot_id=6, size=1),
    ]

    # Act
    activities = convert_field_allocations_to_activities(
        field_allocations, TIMESLOT_IDS)

    # Assert
    expected_activities = [
        FieldActivity(field="field1", group="group1",
                      start_timeslot=1, end_timeslot=3, duration=3, size=1),
        FieldActivity(field="field1", group="group1",
                      start_timeslot=4, end_timeslot=6, duration=3, size=1),
    ]
    assert activities == expected_activities
