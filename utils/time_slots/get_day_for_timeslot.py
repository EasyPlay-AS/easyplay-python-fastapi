def get_day_for_timeslot(timeslot_id: int, timeslot_ids: list[list[int]]) -> int:
    """
    Find which day (index) a timeslot belongs to.

    Args:
        timeslot_id: The ID of the timeslot
        timeslot_ids: List of lists, where each sublist represents timeslots for a day

    Returns:
        The index of the day the timeslot belongs to
    """
    for day_idx, day_timeslots in enumerate(timeslot_ids):
        if timeslot_id in day_timeslots:
            return day_idx
    raise ValueError(f"Timeslot {timeslot_id} not found in any day")
