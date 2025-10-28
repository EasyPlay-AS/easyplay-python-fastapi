import itertools
from pydantic import BaseModel

from models.field_optimizer.field_optimizer_payload import FieldOptimizerPayload
from models.field_optimizer.field_optimizer_input import FieldOptimizerInput, Field, Group
from models.field_optimizer.time_slot import TimeSlot

from utils.time_slots import (
    generate_time_slots_in_range, get_timeslot_ids_by_week_day
)
from utils.common import create_number_to_index_mapping
from .convert_time_range_to_timeslot_ids import convert_time_range_to_timeslot_ids

TIME_SLOT_DURATION_MINUTES = 15


class ConvertedPayload(BaseModel):
    field_optimizer_input: FieldOptimizerInput
    time_slots_in_range: list[TimeSlot]
    index_to_timeslot_map: dict[int, int]
    time_slot_duration_minutes: int


def convert_payload_to_input(
        payload: FieldOptimizerPayload
) -> ConvertedPayload:
    time_slots_in_range = generate_time_slots_in_range(
        payload.start_time, payload.end_time, TIME_SLOT_DURATION_MINUTES)

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

        groups.append(Group(
            name=team.name,
            minimum_number_of_activities=team.min_number_of_activities,
            maximum_number_of_activities=team.max_number_of_activities,
            possible_start_times=possible_start_times,
            preferred_start_times=preferred_start_times,
            preferred_start_time_activity_1=0,
            preferred_start_time_activity_2=0,
            size_required=team.size_required,
            duration=team.duration,
            priority=team.priority
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
        time_slot_duration_minutes=TIME_SLOT_DURATION_MINUTES
    )
