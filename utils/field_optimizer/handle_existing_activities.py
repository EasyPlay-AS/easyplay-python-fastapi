import logging
from typing import Dict, List, Tuple, Optional
from pydantic import BaseModel

from models.field_optimizer.field_optimizer_payload import ExistingTeamActivity
from models.field_optimizer.field_optimizer_input import FieldOptimizerInput

logger = logging.getLogger(__name__)


class ProcessedActivity(BaseModel):
    """Represents a validated and mapped existing activity ready for AMPL variable fixing"""
    field_id: str
    group_id: str
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
    # Check if group exists
    group = next((g for g in field_optimizer_input.groups if g.id == activity.team_id), None)
    if not group:
        return False, f"Group with ID '{activity.team_id}' not found"

    # Check if field exists
    field = next((f for f in field_optimizer_input.fields if f.id == activity.stadium_id), None)
    if not field:
        return False, f"Field with ID '{activity.stadium_id}' not found"

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
            - aat_map: Dict[(field_id, group_id)] -> [relative_timeslot_indexes]
            - processed_activities: List of validated activities ready for AMPL fixing
    """
    aat_map: Dict[Tuple[str, str], List[int]] = {}
    processed_activities: List[ProcessedActivity] = []

    if len(existing_activities) == 0:
        return aat_map, processed_activities

    logger.info("Processing %d existing activities", len(existing_activities))

    for activity in existing_activities:
        field_id = activity.stadium_id
        group_id = activity.team_id

        # Validate activity references
        is_valid, error_msg = validate_existing_activity(activity, field_optimizer_input)
        if not is_valid:
            logger.warning("%s - skipping activity", error_msg)
            continue

        # Convert global timeslots to relative indexes
        start_idx, timeslot_indexes, skipped = convert_global_to_relative_timeslots(
            activity, timeslot_to_index_map
        )

        # Log skipped timeslots (outside optimization window)
        if len(skipped) > 0:
            logger.warning("%d timeslot(s) outside optimization window for '%s': %s", len(skipped), activity.team_name, skipped)

        # Skip if no valid timeslots
        if len(timeslot_indexes) == 0:
            logger.warning("Activity '%s' has no valid timeslots - skipping", activity.team_name)
            continue

        # Skip if start is outside window
        if start_idx is None:
            logger.warning("Start timeslot outside window for '%s' - skipping", activity.team_name)
            continue

        # Add to AAT map (for constraint exclusion)
        key = (field_id, group_id)
        if key not in aat_map:
            aat_map[key] = []
        aat_map[key].extend(timeslot_indexes)

        # Add to processed list (for variable fixing)
        processed_activities.append(ProcessedActivity(
            field_id=field_id,
            group_id=group_id,
            start_index=start_idx,
            timeslot_indexes=timeslot_indexes
        ))

        logger.info("  Fixed: '%s' on '%s' timeslots %d-%d (indexes %d-%d, size %d)",
                     activity.team_name, activity.stadium_name,
                     activity.start_timeslot,
                     activity.start_timeslot + activity.duration_slots - 1,
                     timeslot_indexes[0], timeslot_indexes[-1],
                     activity.size_required)

    # Sort and deduplicate all AAT sets
    for key in aat_map:
        aat_map[key] = sorted(set(aat_map[key]))

    logger.info("Successfully processed %d activities for fixing", len(processed_activities))

    # Check for capacity collisions among fixed activities (diagnostic only)
    try:
        _check_fixed_activity_collisions(existing_activities, field_optimizer_input, timeslot_to_index_map)
    except Exception:
        logger.exception("Failed to check fixed activity collisions")

    return aat_map, processed_activities


def _check_fixed_activity_collisions(
    existing_activities: List[ExistingTeamActivity],
    field_optimizer_input: FieldOptimizerInput,
    timeslot_to_index_map: Dict[int, int]
) -> None:
    """Log warnings when fixed existing activities exceed field capacity at any timeslot."""
    field_capacity = {f.id: f.size for f in field_optimizer_input.fields}
    group_size = {g.id: g.size_required for g in field_optimizer_input.groups}

    # Build demand per (field, timeslot_index)
    slot_demand: Dict[Tuple[str, int], int] = {}
    slot_activities: Dict[Tuple[str, int], List[str]] = {}

    for activity in existing_activities:
        field_id = activity.stadium_id
        if field_id not in field_capacity:
            continue
        size_req = group_size.get(activity.team_id, activity.size_required)

        for i in range(activity.duration_slots):
            global_slot = activity.start_timeslot + i
            idx = timeslot_to_index_map.get(global_slot)
            if idx is None:
                continue
            key = (field_id, idx)
            slot_demand[key] = slot_demand.get(key, 0) + size_req
            if key not in slot_activities:
                slot_activities[key] = []
            slot_activities[key].append(activity.team_name)

    for (field_id, idx), demand in slot_demand.items():
        capacity = field_capacity[field_id]
        if demand > capacity:
            teams = slot_activities[(field_id, idx)]
            field_name = next((f.name for f in field_optimizer_input.fields if f.id == field_id), field_id)
            logger.warning(
                "Capacity collision: field '%s' at index %d — demand %d > capacity %d (teams: %s)",
                field_name, idx, demand, capacity, ', '.join(teams)
            )
