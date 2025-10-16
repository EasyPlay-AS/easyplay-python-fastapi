from models.field_optimizer.field_allocation import FieldAllocation
from models.field_optimizer.field_activity import FieldActivity


def get_day_for_timeslot(timeslot_id: int, timeslot_ids: list[list[int]]) -> int:
    """Find which day (index) a timeslot belongs to."""
    for day_idx, day_timeslots in enumerate(timeslot_ids):
        if timeslot_id in day_timeslots:
            return day_idx
    return -1  # Not found


def convert_field_allocations_to_activities(
    field_allocations: list[FieldAllocation],
    timeslot_ids: list[list[int]]
) -> list[FieldActivity]:
    """
    Convert field allocations to activities by grouping consecutive timeslots
    for the same group on the same field into activity blocks.
    Activities are split at day boundaries (when timeslots are not on the same day).

    Args:
        field_allocations: List of FieldAllocation objects
        timeslot_ids: List of lists, where each sublist represents timeslots for a day

    Returns:
        List of FieldActivity objects representing grouped activities
    """
    if not field_allocations:
        return []

    # Sort by field, group, then timeslot to ensure proper grouping
    sorted_data = sorted(field_allocations, key=lambda x: (
        x.field, x.group, x.timeslot_id))

    activities = []
    current_activity = None

    for item in sorted_data:
        field = item.field
        group = item.group
        timeslot_id = item.timeslot_id
        size = item.size

        if current_activity is None:
            # Start a new block
            current_activity = {
                'field': field,
                'group': group,
                'start_timeslot': timeslot_id,
                'end_timeslot': timeslot_id,
                'size': size
            }
        elif (current_activity['field'] == field and
              current_activity['group'] == group and
              timeslot_id == current_activity['end_timeslot'] + 1):
            # Check if this consecutive timeslot is on the same day
            current_day = get_day_for_timeslot(
                current_activity['end_timeslot'], timeslot_ids)
            new_day = get_day_for_timeslot(timeslot_id, timeslot_ids)

            if current_day == new_day:
                # Extend current block (consecutive timeslot on same day)
                current_activity['end_timeslot'] = timeslot_id
            else:
                # Finish current block and start a new one (crossed day boundary)
                activities.append(FieldActivity(
                    field=current_activity['field'],
                    group=current_activity['group'],
                    start_timeslot=current_activity['start_timeslot'],
                    end_timeslot=current_activity['end_timeslot'],
                    duration=current_activity['end_timeslot'] -
                    current_activity['start_timeslot'] + 1,
                    size=current_activity['size']
                ))

                current_activity = {
                    'field': field,
                    'group': group,
                    'start_timeslot': timeslot_id,
                    'end_timeslot': timeslot_id,
                    'size': size
                }
        else:
            # Finish current block and start a new one
            activities.append(FieldActivity(
                field=current_activity['field'],
                group=current_activity['group'],
                start_timeslot=current_activity['start_timeslot'],
                end_timeslot=current_activity['end_timeslot'],
                duration=current_activity['end_timeslot'] -
                current_activity['start_timeslot'] + 1,
                size=current_activity['size']
            ))

            current_activity = {
                'field': field,
                'group': group,
                'start_timeslot': timeslot_id,
                'end_timeslot': timeslot_id,
                'size': size
            }

    # Don't forget the last block
    if current_activity is not None:
        activities.append(FieldActivity(
            field=current_activity['field'],
            group=current_activity['group'],
            start_timeslot=current_activity['start_timeslot'],
            end_timeslot=current_activity['end_timeslot'],
            duration=current_activity['end_timeslot'] -
            current_activity['start_timeslot'] + 1,
            size=current_activity['size']
        ))

    return activities
