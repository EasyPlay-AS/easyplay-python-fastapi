from typing import Dict, List, Tuple, Optional
from pydantic import BaseModel

from models.field_optimizer.field_optimizer_payload import ExistingTeamActivity
from models.field_optimizer.field_optimizer_input import FieldOptimizerInput


class ProcessedActivity(BaseModel):
    """Represents a validated and mapped existing activity ready for AMPL variable fixing"""
    field_name: str
    group_name: str
    start_index: int
    timeslot_indexes: List[int] 


def validate_existing_activity(
    activity: ExistingTeamActivity,
    field_optimizer_input: FieldOptimizerInput
) -> Tuple[bool, Optional[str]]:
    """
    Validates that the activity has valid references to field and group.

    Args:
        activity: The existing team activity to validate
        field_optimizer_input: The optimizer input containing fields and groups

    Returns:
        (is_valid, error_message): Tuple where is_valid is True if activity is valid,
                                   and error_message contains the error if not valid
    """
    # Check if group exists (group.name now contains team ID)
    group = next((g for g in field_optimizer_input.groups if g.name == activity.team_id), None)
    if not group:
        return False, f"Group '{activity.team_name}' (ID: {activity.team_id}) not found"

    # Check if field exists (field.name now contains stadium ID)
    field = next((f for f in field_optimizer_input.fields if f.name == activity.stadium_id), None)
    if not field:
        return False, f"Field '{activity.stadium_name}' (ID: {activity.stadium_id}) not found"

    return True, None


def convert_global_to_relative_timeslots(
    activity: ExistingTeamActivity,
    timeslot_to_index_map: Dict[int, int]
) -> Tuple[Optional[int], List[int], List[int]]:
    """
    Converts global timeslot IDs to relative indexes within the optimization window.

    Args:
        activity: The existing team activity with global timeslot IDs
        timeslot_to_index_map: Mapping from global timeslot ID to relative index

    Returns:
        (start_index, valid_timeslot_indexes, skipped_timeslots):
            - start_index: Relative index of activity start (None if outside window)
            - valid_timeslot_indexes: List of relative indexes for occupied timeslots
            - skipped_timeslots: List of global timeslot IDs that are outside window
    """
    start_index = timeslot_to_index_map.get(activity.start_timeslot)

    timeslot_indexes = []
    skipped_timeslots = []

    for i in range(activity.duration_slots):
        global_timeslot = activity.start_timeslot + i
        relative_idx = timeslot_to_index_map.get(global_timeslot)

        if relative_idx is None:
            skipped_timeslots.append(global_timeslot)
        else:
            timeslot_indexes.append(relative_idx)

    return start_index, timeslot_indexes, skipped_timeslots


def build_aat_map(
    existing_activities: List[ExistingTeamActivity],
    field_optimizer_input: FieldOptimizerInput,
    timeslot_to_index_map: Dict[int, int]
) -> Tuple[Dict[Tuple[str, str], List[int]], List[ProcessedActivity]]:
    """
    Builds AAT (Already Assigned Timeslots) map and list of processed activities.

    This function validates existing activities, converts their global timeslot IDs
    to relative indexes, and prepares data structures for AMPL integration.

    Args:
        existing_activities: List of existing team activities to process
        field_optimizer_input: The optimizer input containing fields and groups
        timeslot_to_index_map: Mapping from global timeslot ID to relative index

    Returns:
        (aat_map, processed_activities):
            - aat_map: Dict[(field_name, group_name)] -> [relative_timeslot_indexes]
            - processed_activities: List of validated activities ready for AMPL fixing
    """
    aat_map: Dict[Tuple[str, str], List[int]] = {}
    processed_activities: List[ProcessedActivity] = []

    if len(existing_activities) == 0:
        return aat_map, processed_activities

    print(f"Processing {len(existing_activities)} existing activities")

    for activity in existing_activities:
        # Use IDs instead of names (matching the field_optimizer_input structure)
        field_id = activity.stadium_id
        group_id = activity.team_id

        # Validate activity references
        is_valid, error_msg = validate_existing_activity(activity, field_optimizer_input)
        if not is_valid:
            print(f"WARNING: {error_msg} - skipping activity")
            continue

        # Convert global timeslots to relative indexes
        start_idx, timeslot_indexes, skipped = convert_global_to_relative_timeslots(
            activity, timeslot_to_index_map
        )

        # Log skipped timeslots (outside optimization window)
        if len(skipped) > 0:
            print(f"WARNING: {len(skipped)} timeslot(s) outside optimization window for '{activity.team_name}' (ID: {group_id}): {skipped}")

        # Skip if no valid timeslots
        if len(timeslot_indexes) == 0:
            print(f"WARNING: Activity '{activity.team_name}' (ID: {group_id}) has no valid timeslots - skipping")
            continue

        # Skip if start is outside window
        if start_idx is None:
            print(f"WARNING: Start timeslot outside window for '{activity.team_name}' (ID: {group_id}) - skipping")
            continue

        # Add to AAT map (for constraint exclusion) - using IDs as keys
        key = (field_id, group_id)
        if key not in aat_map:
            aat_map[key] = []
        aat_map[key].extend(timeslot_indexes)

        # Add to processed list (for variable fixing) - using IDs
        processed_activities.append(ProcessedActivity(
            field_name=field_id,
            group_name=group_id,
            start_index=start_idx,
            timeslot_indexes=timeslot_indexes
        ))

    # Sort and deduplicate all AAT sets
    for key in aat_map:
        aat_map[key] = sorted(set(aat_map[key]))

    print(f"Successfully processed {len(processed_activities)} activities for fixing")

    return aat_map, processed_activities
