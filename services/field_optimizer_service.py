from datetime import datetime
from amplpy import AMPL
from models.field_optimizer.field_optimizer_payload import FieldOptimizerPayload
from models.field_optimizer.field_optimizer_result import FieldOptimizerResult
from utils.field_optimizer import (
    convert_payload_to_input,
    convert_ampl_x_values_to_allocations,
    convert_field_activities_to_result,
    convert_field_allocations_to_activities,
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

            aat_map = {}

            if len(existing_activities) > 0:
                print(f"Processing {len(existing_activities)} existing activities")

            for activity in existing_activities:
                field_name = activity.stadium_name
                group_name = activity.team_name

                group = next((g for g in field_optimizer_input.groups if g.name == group_name), None)
                if not group:
                    print(f"WARNING: Group '{group_name}' not found for existing activity - skipping")
                    continue

                timeslot_indices = []
                for i in range(activity.duration_slots):
                    global_timeslot = activity.start_timeslot + i
                    relative_idx = timeslot_to_index_map.get(global_timeslot)

                    if relative_idx is None:
                        print(f"WARNING: Timeslot {global_timeslot} outside optimization window for activity '{group_name}'")
                        continue

                    timeslot_indices.append(relative_idx)

                if len(timeslot_indices) == 0:
                    print(f"WARNING: Activity '{group_name}' has no valid timeslots - skipping")
                    continue

                key = (field_name, group_name)
                if key not in aat_map:
                    aat_map[key] = []
                aat_map[key].extend(timeslot_indices)

            for field in field_optimizer_input.fields:
                for group in field_optimizer_input.groups:
                    key = (field.name, group.name)
                    if key in aat_map:
                        sorted_unique_timeslots = sorted(set(aat_map[key]))
                        ampl.set["AAT"][field.name, group.name] = sorted_unique_timeslots
                    else:
                        ampl.set["AAT"][field.name, group.name] = []

            for activity in existing_activities:
                field_name = activity.stadium_name
                group_name = activity.team_name

                group = next((g for g in field_optimizer_input.groups if g.name == group_name), None)
                if not group:
                    continue

                start_global_timeslot = activity.start_timeslot
                start_idx = timeslot_to_index_map.get(start_global_timeslot)

                if start_idx is None:
                    continue

                try:
                    ampl.var["y"][field_name, group_name, start_idx].fix(1)
                except Exception as e:
                    print(f"ERROR: Could not fix y variable for {group_name}: {e}")
                    continue

                for i in range(activity.duration_slots):
                    global_timeslot = activity.start_timeslot + i
                    idx_relative = timeslot_to_index_map.get(global_timeslot)

                    if idx_relative is not None:
                        try:
                            ampl.var["x"][field_name, group_name, idx_relative].fix(1)
                        except Exception as e:
                            print(f"ERROR: Could not fix x variable for {group_name}: {e}")
            for field in field_optimizer_input.fields:
                ampl.set["UT"][field.name] = field.unavailable_start_times

            # Solve the model
            ampl.solve()

            # Check solve result
            solve_result = ampl.get_value("solve_result")
            if solve_result != "solved":
                return {
                    "result": "FAILURE",
                    "error": "Solver failed to solve the model"
                }

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
            # Handle errors gracefully
            return {
                "result": "FAILURE",
                "error": str(e)
            }
