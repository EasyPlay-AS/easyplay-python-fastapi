import itertools
from pydantic import BaseModel

from models.field_optimizer.field_optimizer_payload import FieldOptimizerPayload, ExistingTeamActivity
from models.field_optimizer.field_optimizer_input import FieldOptimizerInput, Field, Group
from models.field_optimizer.time_slot import TimeSlot

from utils.time_slots import (
    generate_time_slots_in_range, get_timeslot_ids_by_week_day
)
from utils.common import create_number_to_index_mapping
from .convert_time_range_to_timeslot_ids import convert_time_range_to_timeslot_ids

TIME_SLOT_DURATION_MINUTES = 15
SLOTS_PER_DAY = (24 * 60) // TIME_SLOT_DURATION_MINUTES  # 96


def compute_effective_time_window(
    start_time: str,
    end_time: str,
    existing_activities: list[ExistingTeamActivity]
) -> tuple[str, str]:
    """
    Expands the optimization time window to include times of predefined activities.

    Predefined activities may fall outside the user's normal time window
    (e.g., a Saturday 10:00 activity when the window is 16:00-22:00).
    The solver needs these timeslots in T to fix x/y variables.
    """
    if not existing_activities:
        return start_time, end_time

    def time_str_to_minutes(t: str) -> int:
        h, m = t.split(":")
        return int(h) * 60 + int(m)

    def minutes_to_time_str(minutes: int) -> str:
        h = minutes // 60
        m = minutes % 60
        return f"{h:02d}:{m:02d}"

    effective_start = time_str_to_minutes(start_time)
    effective_end = time_str_to_minutes(end_time)

    for activity in existing_activities:
        # Derive time-of-day from global timeslot ID
        start_slot_in_day = (activity.start_timeslot - 1) % SLOTS_PER_DAY
        start_minutes = start_slot_in_day * TIME_SLOT_DURATION_MINUTES

        end_slot_in_day = (activity.end_timeslot - 1) % SLOTS_PER_DAY
        end_minutes = end_slot_in_day * TIME_SLOT_DURATION_MINUTES

        if start_minutes < effective_start:
            effective_start = start_minutes
        if end_minutes > effective_end:
            effective_end = end_minutes

    return minutes_to_time_str(effective_start), minutes_to_time_str(effective_end)


class ConvertedPayload(BaseModel):
    field_optimizer_input: FieldOptimizerInput
    time_slots_in_range: list[TimeSlot]
    index_to_timeslot_map: dict[int, int]
    timeslot_to_index_map: dict[int, int]
    time_slot_duration_minutes: int
    existing_activities: list[ExistingTeamActivity]


def convert_payload_to_input(
        payload: FieldOptimizerPayload
) -> ConvertedPayload:
    # Expand time window to include predefined activities that may fall outside
    # the user's normal window (e.g., weekend 10:00 when window is 16:00-22:00)
    effective_start_time, effective_end_time = compute_effective_time_window(
        payload.start_time, payload.end_time, payload.existing_team_activities
    )

    time_slots_in_range = generate_time_slots_in_range(
        effective_start_time, effective_end_time, TIME_SLOT_DURATION_MINUTES)

    timeslot_ids_by_week_day = get_timeslot_ids_by_week_day(
        time_slots_in_range)
    timeslot_ids = list(itertools.chain(*timeslot_ids_by_week_day))

    mapping = create_number_to_index_mapping(timeslot_ids)
    timeslot_to_index_map = mapping['number_to_index_map']
    index_to_timeslot_map = mapping['index_to_number_map']

    fields = []
    for stadium in payload.stadiums:
        unavailable_indexes = [
            timeslot_to_index_map[timeslot_id]
            for timeslot_id in stadium.unavailable_start_times
            if timeslot_id in timeslot_to_index_map
        ]

        fields.append(Field(
            id=stadium.id,
            name=stadium.name,
            size=stadium.size,
            unavailable_start_times=unavailable_indexes
        ))

    groups = []
    for team in payload.teams:
        possible_start_times = convert_time_range_to_timeslot_ids(
            team.time_range, timeslot_to_index_map)

        # TODO: when ready, use "team.preferred_start_times"
        preferred_start_times = []

        preferred_field_ids = team.preferred_stadium_ids

        groups.append(Group(
            id=team.id,
            name=team.name,
            minimum_number_of_activities=team.min_number_of_activities,
            maximum_number_of_activities=team.max_number_of_activities,
            possible_start_times=possible_start_times,
            preferred_start_times=preferred_start_times,
            preferred_start_time_activity_1=0,
            preferred_start_time_activity_2=0,
            size_required=team.size_required,
            duration=team.duration,
            priority=team.priority,
            preferred_field_ids=preferred_field_ids,
            p_early_starts=team.p_early_starts or 0
        ))

    timeslot_ids_indexes = [
        [timeslot_to_index_map[timeslot_id] for timeslot_id in timeslot_ids]
        for timeslot_ids in timeslot_ids_by_week_day
    ]

    return ConvertedPayload(
        field_optimizer_input=FieldOptimizerInput(
            fields=fields,
            groups=groups,
            time_slots=timeslot_ids_indexes
        ),
        time_slots_in_range=time_slots_in_range,
        index_to_timeslot_map=index_to_timeslot_map,
        timeslot_to_index_map=timeslot_to_index_map,
        time_slot_duration_minutes=TIME_SLOT_DURATION_MINUTES,
        existing_activities=payload.existing_team_activities
    )
