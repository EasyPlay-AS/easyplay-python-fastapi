from models.field_optimizer.time_slot import TimeSlot


def get_timeslot_ids_by_week_day(
    timeslots: list[TimeSlot],
) -> list[list[int]]:
    timeslot_ids_by_week_day: list[list[int]] = []
    unique_week_day_indexes = set()

    for timeslot in timeslots:
        unique_week_day_indexes.add(timeslot.week_day_index)

    unique_week_day_indexes = sorted(unique_week_day_indexes)

    for week_day_index in unique_week_day_indexes:
        week_day_timeslots_ids = [
            timeslot.id
            for timeslot in timeslots
            if timeslot.week_day_index == week_day_index
        ]
        timeslot_ids_by_week_day.append(week_day_timeslots_ids)

    return timeslot_ids_by_week_day
