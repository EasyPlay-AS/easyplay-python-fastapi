from datetime import datetime
from amplpy import AMPL
from models.field_optimizer.field_optimizer_payload import FieldOptimizerPayload
from models.field_optimizer.field_optimizer_result import FieldOptimizerResult
from utils.field_optimizer import (
    convert_payload_to_input,
    convert_ampl_x_values_to_allocations,
    convert_field_activities_to_result,
    convert_field_allocations_to_activities,
    build_aat_map,
)


class FieldOptimizerService:

    @staticmethod
    def solve(payload: FieldOptimizerPayload) -> FieldOptimizerResult:
        start_time = datetime.now()
        converted_payload = convert_payload_to_input(payload)

        field_optimizer_input = converted_payload.field_optimizer_input
        time_slots_in_range = converted_payload.time_slots_in_range
        index_to_timeslot_map = converted_payload.index_to_timeslot_map
        timeslot_to_index_map = converted_payload.timeslot_to_index_map
        time_slot_duration_minutes = converted_payload.time_slot_duration_minutes
        existing_activities = converted_payload.existing_activities

        try:
            # Initialize AMPL with SCIP solver
            ampl = AMPL()
            ampl.option["solver"] = "scip"

            # Time limit in seconds
            ampl.option["mp_options"] = "lim:time=30"

            # Load the model file
            ampl.read("./ampl/field_optimizer.mod")

            # ------
            # Set data from JSON payload instead of reading .dat file
            # ------

            # Set basic sets
            ampl.set["F"] = [
                field.name for field in field_optimizer_input.fields]
            ampl.set["G"] = [
                group.name for group in field_optimizer_input.groups]

            # Flatten all time slots for set T
            all_timeslots = []
            for day_slots in field_optimizer_input.time_slots:
                all_timeslots.extend(day_slots)
            ampl.set["T"] = all_timeslots

            # Set up days (explicitly set D)
            days = list(range(1, len(field_optimizer_input.time_slots) + 1))
            ampl.set["D"] = days

            # Set timeslots for each day (DT)
            for day_idx, day_slots in enumerate(field_optimizer_input.time_slots, start=1):
                ampl.set["DT"][day_idx] = day_slots

            # Get the first timeslot for each day
            day_start_timeslots: list[int] = [
                day_slots[0]
                for day_slots in field_optimizer_input.time_slots
            ]

            # Set start timeslots for each day (ST)
            ampl.set["ST"] = day_start_timeslots

            # Set available starting times for each group (AT)
            for group in field_optimizer_input.groups:
                ampl.set["AT"][group.name] = group.possible_start_times

            # Set preferred starting times for each group (PT)
            for group in field_optimizer_input.groups:
                ampl.set["PT"][group.name] = group.preferred_start_times

            # Set preferred fields for each group (PF)
            for group in field_optimizer_input.groups:
                ampl.set["PF"][group.name] = group.preferred_field_names

            # Set group parameters
            for group in field_optimizer_input.groups:
                ampl.param["d"][group.name] = group.duration
                ampl.param["n_min"][group.name] = group.minimum_number_of_activities
                ampl.param["n_max"][group.name] = group.maximum_number_of_activities
                ampl.param["size_req"][group.name] = group.size_required
                ampl.param["prio"][group.name] = group.priority
                ampl.param["p_st1"][group.name] = group.preferred_start_time_activity_1
                ampl.param["p_st2"][group.name] = group.preferred_start_time_activity_2

            # Set field parameters
            for field in field_optimizer_input.fields:
                ampl.param["size"][field.name] = field.size

            # Set incompatible groups (teams that should not have simultaneous activities)
            if payload.incompatible_groups:
                incompatible_pairs = []
                for team_id_1, team_id_2 in payload.incompatible_groups:
                    team_1 = next(
                        (t for t in payload.teams if t.id == team_id_1), None)
                    team_2 = next(
                        (t for t in payload.teams if t.id == team_id_2), None)

                    if team_1 and team_2:
                        incompatible_pairs.append((team_1.name, team_2.name))

                ampl.set["INCOMPATIBLE_GROUPS"] = incompatible_pairs
            else:
                ampl.set["INCOMPATIBLE_GROUPS"] = []

            # Handle existing activities (AAT - Already Assigned Times)
            aat_map, processed_activities = build_aat_map(
                existing_activities=existing_activities,
                field_optimizer_input=field_optimizer_input,
                timeslot_to_index_map=timeslot_to_index_map
            )

            for field in field_optimizer_input.fields:
                for group in field_optimizer_input.groups:
                    key = (field.name, group.name)
                    if key in aat_map:
                        ampl.set["AAT"][field.name, group.name] = aat_map[key]
                    else:
                        ampl.set["AAT"][field.name, group.name] = []

            for activity in processed_activities:
                try:
                    ampl.var["y"][activity.field_name,
                                  activity.group_name, activity.start_index].fix(1)
                except Exception as e:
                    print(
                        f"ERROR: Could not fix y variable for {activity.group_name}: {e}")
                    continue

                for idx in activity.timeslot_indexes:
                    try:
                        ampl.var["x"][activity.field_name,
                                      activity.group_name, idx].fix(1)
                    except Exception as e:
                        print(
                            f"ERROR: Could not fix x variable for {activity.group_name} at index {idx}: {e}")

            # Set unavailable times for each field (UT)
            for field in field_optimizer_input.fields:
                ampl.set["UT"][field.name] = field.unavailable_start_times

            # Solve the model
            ampl.solve()

            # Check solve result
            solve_result = ampl.get_value("solve_result")
            if solve_result != "solved":
                end_time = datetime.now()
                duration_ms = round(
                    (end_time - start_time).total_seconds() * 1000, 2)
                return FieldOptimizerResult(
                    result="FAILURE",
                    duration_ms=duration_ms,
                    preference_score=0.0,
                    activities=[]
                )

            preference_score = ampl.obj["preference_score"]
            preference_score_value = preference_score.value()

            # Extract allocations: which fields and timeslots are occupied by which groups
            field_allocations = convert_ampl_x_values_to_allocations(
                ampl, field_optimizer_input.groups)

            field_activities = convert_field_allocations_to_activities(
                field_allocations,
                field_optimizer_input.time_slots
            )

            result_activities = convert_field_activities_to_result(
                payload=payload,
                field_activities=field_activities,
                time_slot_duration_minutes=time_slot_duration_minutes,
                time_slots_in_range=time_slots_in_range,
                index_to_timeslot_map=index_to_timeslot_map
            )

            end_time = datetime.now()
            duration_ms = round(
                (end_time - start_time).total_seconds() * 1000, 2)

            return FieldOptimizerResult(
                result="SUCCESS",
                duration_ms=duration_ms,
                preference_score=preference_score_value,
                activities=result_activities
            )
        except Exception as e:
            print(f"ERROR: {e}")
            end_time = datetime.now()
            duration_ms = round(
                (end_time - start_time).total_seconds() * 1000, 2)
            return FieldOptimizerResult(
                result="FAILURE",
                duration_ms=duration_ms,
                preference_score=0.0,
                activities=[]
            )
