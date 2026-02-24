from models.field_optimizer.field_activity import FieldActivity
from models.field_optimizer.field_optimizer_result import Activity, Stadium, Team
from models.field_optimizer.time_slot import TimeSlot
from models.field_optimizer.field_optimizer_payload import FieldOptimizerPayload
from utils.datetime import add_minutes_to_time_string


def convert_field_activities_to_result(
    payload: FieldOptimizerPayload,
    field_activities: list[FieldActivity],
    time_slot_duration_minutes: int,
    time_slots_in_range: list[TimeSlot],
    index_to_timeslot_map: dict[int, int]
) -> list[Activity]:
    """
    Convert field activities to result activities by mapping team and stadium data
    and calculating proper start/end times.

    Args:
        field_activities: List of FieldActivity objects from the optimizer
        payload: The original payload containing teams and stadiums
        time_slot_duration_minutes: Duration of each time slot in minutes
        time_slots_in_range: List of all available time slots   
        index_to_timeslot_map: Mapping from index to timeslot ID

    Returns:
        List of Activity objects for the result
    """
    activities = []

    for activity in field_activities:
        # Find the team (auto-subgroups like "id__existing_0" map back to parent)
        group_id = activity.group
        if "__existing_" in group_id:
            group_id = group_id.split("__existing_")[0]
        if group_id.startswith("__busyblock_"):
            continue  

        team = next(
            (team for team in payload.teams if team.id == group_id), None)
        if not team:
            raise ValueError(f"Team with ID '{activity.group}' not found")

        # Find the stadium
        stadium = next(
            (stadium for stadium in payload.stadiums if stadium.id == activity.field), None)
        if not stadium:
            raise ValueError(f"Stadium with ID '{activity.field}' not found")

        # Map consecutive time slot IDs to actual time slot IDs
        mapped_start_time_slot = index_to_timeslot_map.get(
            activity.start_timeslot)
        if mapped_start_time_slot is None:
            raise ValueError("Start time slot mapping not found")

        start_time_slot = next(
            (ts for ts in time_slots_in_range if ts.id == mapped_start_time_slot), None)
        if not start_time_slot:
            raise ValueError("Start time not found")

        mapped_end_time_slot = index_to_timeslot_map.get(
            activity.end_timeslot)
        if mapped_end_time_slot is None:
            raise ValueError("End time slot mapping not found")

        end_time_slot = next(
            (ts for ts in time_slots_in_range if ts.id == mapped_end_time_slot), None)
        if not end_time_slot:
            raise ValueError("End time not found")

        # Calculate adjusted end time by adding time slot duration
        adjusted_end_time = add_minutes_to_time_string(
            end_time_slot.time,
            time_slot_duration_minutes
        )

        # Create the activity result
        result_activity = Activity(
            stadium=Stadium(
                id=stadium.id,
                name=stadium.name
            ),
            team=Team(
                id=team.id,
                name=team.name
            ),
            index_week_day=start_time_slot.week_day_index,
            start_time=start_time_slot.time,
            end_time=adjusted_end_time,
            size=activity.size
        )

        activities.append(result_activity)

    return activities
