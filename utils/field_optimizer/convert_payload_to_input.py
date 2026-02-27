import itertools
import logging
from pydantic import BaseModel
from models.field_optimizer.field_optimizer_payload import FieldOptimizerPayload, ExistingTeamActivity
from models.field_optimizer.field_optimizer_input import FieldOptimizerInput, Field, Group
from models.field_optimizer.time_slot import TimeSlot

from utils.time_slots import (
    generate_time_slots_in_range, get_timeslot_ids_by_week_day
)
from utils.common import create_number_to_index_mapping
from .convert_time_range_to_timeslot_ids import convert_time_range_to_timeslot_ids, convert_time_ranges_to_timeslot_ids

TIME_SLOT_DURATION_MINUTES = 15
SLOTS_PER_DAY = (24 * 60) // TIME_SLOT_DURATION_MINUTES  # 96
logger = logging.getLogger(__name__)


def compute_effective_time_window(
    start_time: str,
    end_time: str,
    existing_activities: list[ExistingTeamActivity],
    payload: FieldOptimizerPayload | None = None
) -> tuple[str, str]:
    """
    Expands the optimization time window to include times of predefined activities.

    Predefined activities may fall outside the user's normal time window
    (e.g., a Saturday 10:00 activity when the window is 16:00-22:00).
    The solver needs these timeslots in T to fix x/y variables.
    """
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

    # Expand window to include team time_ranges (e.g., weekend times)
    if payload:
        for team in payload.teams:
            ranges = team.time_ranges or [team.time_range]
            for tr in ranges:
                tr_start = time_str_to_minutes(tr.start_time)
                tr_end = time_str_to_minutes(tr.end_time)
                if tr_start < effective_start:
                    effective_start = tr_start
                if tr_end > effective_end:
                    effective_end = tr_end

    return minutes_to_time_str(effective_start), minutes_to_time_str(effective_end)


def split_groups_for_existing_activities(
    groups: list[Group],
    existing_activities: list[ExistingTeamActivity],
    timeslot_to_index_map: dict[int, int]
) -> tuple[list[Group], list[ExistingTeamActivity], list[list[str]], list[list[str]]]:
    """
    When a predefined activity has a different size_required or duration than
    its group, create an auto-subgroup so the AMPL model uses the correct
    per-group parameters (size_req[g], d[g]) for that activity.

    Returns:
        (updated_groups, updated_activities,
         new_incompatible_same_day, new_incompatible_same_time)
    """
    if not existing_activities:
        return groups, existing_activities, [], []

    group_map = {g.id: g for g in groups}
    new_groups: list[Group] = []
    updated_activities = list(existing_activities)
    new_incompatible_same_day: list[list[str]] = []
    new_incompatible_same_time: list[list[str]] = []
    subgroup_counter: dict[str, int] = {}

    for i, activity in enumerate(updated_activities):
        parent = group_map.get(activity.team_id)
        if not parent:
            continue

        size_match = activity.size_required == parent.size_required
        duration_match = activity.duration_slots == parent.duration
        if size_match and duration_match:
            continue

        # Derive start index for the subgroup's possible_start_times
        start_idx = timeslot_to_index_map.get(activity.start_timeslot)
        if start_idx is None:
            continue

        # Create auto-subgroup with the activity's actual size and duration
        counter = subgroup_counter.get(parent.id, 0)
        subgroup_id = f"{parent.id}__existing_{counter}"
        subgroup_counter[parent.id] = counter + 1

        new_group = Group(
            id=subgroup_id,
            name=f"{parent.name} (predefined)",
            minimum_number_of_activities=1,
            maximum_number_of_activities=1,
            possible_start_times=[start_idx],
            preferred_start_times=[],
            preferred_start_time_activity_1=0,
            preferred_start_time_activity_2=0,
            size_required=activity.size_required,
            duration=activity.duration_slots,
            priority=parent.priority,
            preferred_field_ids=parent.preferred_field_ids,
            p_early_starts=parent.p_early_starts
        )
        new_groups.append(new_group)
        group_map[subgroup_id] = new_group

        # Reduce parent's activity count
        parent.minimum_number_of_activities = max(0, parent.minimum_number_of_activities - 1)
        parent.maximum_number_of_activities = max(0, parent.maximum_number_of_activities - 1)

        # Reassign activity to subgroup
        updated_activities[i] = ExistingTeamActivity(
            team_id=subgroup_id,
            team_name=activity.team_name,
            stadium_id=activity.stadium_id,
            stadium_name=activity.stadium_name,
            start_timeslot=activity.start_timeslot,
            end_timeslot=activity.end_timeslot,
            duration_slots=activity.duration_slots,
            size_required=activity.size_required
        )

        # Incompatibility: parent and subgroup shouldn't overlap
        new_incompatible_same_day.append([parent.id, subgroup_id])
        new_incompatible_same_time.append([parent.id, subgroup_id])

        mismatch_details = []
        if not size_match:
            mismatch_details.append(f"size {parent.size_required}->{activity.size_required}")
        if not duration_match:
            mismatch_details.append(f"duration {parent.duration}->{activity.duration_slots}")
        logger.info("Auto-subgroup '%s' for '%s' on field '%s' at slot %d (%s)",
                     subgroup_id, activity.team_name, activity.stadium_name,
                     activity.start_timeslot, ', '.join(mismatch_details))

    all_groups = groups + new_groups
    return all_groups, updated_activities, new_incompatible_same_day, new_incompatible_same_time


class ConvertedPayload(BaseModel):
    field_optimizer_input: FieldOptimizerInput
    time_slots_in_range: list[TimeSlot]
    index_to_timeslot_map: dict[int, int]
    timeslot_to_index_map: dict[int, int]
    time_slot_duration_minutes: int
    existing_activities: list[ExistingTeamActivity]
    auto_incompatible_same_day: list[list[str]]
    auto_incompatible_same_time: list[list[str]]


def convert_payload_to_input(
        payload: FieldOptimizerPayload
) -> ConvertedPayload:
    # Expand time window to include predefined activities that may fall outside
    # the user's normal window (e.g., weekend 10:00 when window is 16:00-22:00)
    effective_start_time, effective_end_time = compute_effective_time_window(
        payload.start_time, payload.end_time, payload.existing_team_activities, payload
    )

    if effective_start_time != payload.start_time or effective_end_time != payload.end_time:
        logger.info("Time window expanded: %s-%s -> %s-%s",
                     payload.start_time, payload.end_time, effective_start_time, effective_end_time)

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
        if team.time_ranges:
            possible_start_times = convert_time_ranges_to_timeslot_ids(
                team.time_ranges, timeslot_to_index_map)
        else:
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

    # Auto-split groups when predefined activities have different size/duration
    groups, updated_existing, auto_incomp_day, auto_incomp_time = (
        split_groups_for_existing_activities(
            groups, payload.existing_team_activities, timeslot_to_index_map
        )
    )

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
        existing_activities=updated_existing,
        auto_incompatible_same_day=auto_incomp_day,
        auto_incompatible_same_time=auto_incomp_time
    )
