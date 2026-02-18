import json
import traceback
from datetime import datetime
from typing import Generator
from amplpy import AMPL
from models.field_optimizer.field_optimizer_payload import FieldOptimizerPayload
from models.field_optimizer.field_optimizer_result import (
    FieldOptimizerResult,
    ActivitiesNotGenerated,
    Team,
)
from models.field_optimizer.field_optimizer_input import Group
from utils.field_optimizer import (
    convert_payload_to_input,
    convert_ampl_x_values_to_allocations,
    convert_field_activities_to_result,
    convert_field_allocations_to_activities,
    build_aat_map,
)


def _extract_shortfall_info(
    ampl: AMPL,
    groups: list[Group],
) -> list[ActivitiesNotGenerated]:
    """Read min_activity_shortfall from the solved AMPL model.
    Returns groups with nonzero shortfall."""
    result = []

    activity_counts: dict[str, int] = {}
    try:
        y_values = ampl.get_variable("y").get_values().to_dict()
        for (f, g, t), value in y_values.items():
            if value > 0.5:
                activity_counts[g] = activity_counts.get(g, 0) + 1
    except Exception:
        pass

    shortfall_values: dict = {}
    try:
        shortfall_values = ampl.get_variable(
            "min_activity_shortfall").get_values().to_dict()
    except Exception:
        pass

    for group in groups:
        shortfall_value = shortfall_values.get(
            group.id, shortfall_values.get((group.id,), 0)
        )
        if shortfall_value and shortfall_value > 1e-6:
            result.append(ActivitiesNotGenerated(
                team=Team(id=group.id, name=group.name),
                activities=activity_counts.get(group.id, 0),
                missing_activities=float(shortfall_value),
            ))

    return result


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
        auto_incompatible_same_day = converted_payload.auto_incompatible_same_day
        auto_incompatible_same_time = converted_payload.auto_incompatible_same_time

        try:
            # Initialize AMPL with SCIP solver
            ampl = AMPL()
            ampl.option["solver"] = "scip"

            # Load the model file
            ampl.read("./ampl/field_optimizer.mod")

            # ------
            # Set data from JSON payload instead of reading .dat file
            # ------

            # Set basic sets
            ampl.set["F"] = [
                field.id for field in field_optimizer_input.fields]
            ampl.set["G"] = [
                group.id for group in field_optimizer_input.groups]

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

            # --- Handle existing activities FIRST so we can expand AT[g] ---
            aat_map, processed_activities = build_aat_map(
                existing_activities=existing_activities,
                field_optimizer_input=field_optimizer_input,
                timeslot_to_index_map=timeslot_to_index_map
            )

            # Include predefined activities' start times in AT[g] to avoid
            # infeasibility: their y-variables are fixed to 1, but the
            # activity_can_not_start constraint forces y=0 for times not
            # in AT[g]. This does NOT allow the solver to place new
            # activities here — only prevents conflict with the fixed values.
            for activity in processed_activities:
                group = next(
                    (g for g in field_optimizer_input.groups
                     if g.id == activity.group_id), None
                )
                if group and activity.start_index not in group.possible_start_times:
                    group.possible_start_times.append(activity.start_index)
                    group.possible_start_times.sort()

            # Set available starting times for each group (AT)
            for group in field_optimizer_input.groups:
                ampl.set["AT"][group.id] = group.possible_start_times

            # Set preferred starting times for each group (PT)
            for group in field_optimizer_input.groups:
                ampl.set["PT"][group.id] = group.preferred_start_times

            # Set preferred fields for each group (PF)
            for group in field_optimizer_input.groups:
                ampl.set["PF"][group.id] = group.preferred_field_ids

            # Set group parameters
            for group in field_optimizer_input.groups:
                ampl.param["d"][group.id] = group.duration
                ampl.param["n_min"][group.id] = group.minimum_number_of_activities
                ampl.param["n_max"][group.id] = group.maximum_number_of_activities
                ampl.param["size_req"][group.id] = group.size_required
                ampl.param["prio"][group.id] = group.priority
                ampl.param["p_st1"][group.id] = group.preferred_start_time_activity_1
                ampl.param["p_st2"][group.id] = group.preferred_start_time_activity_2
                ampl.param["p_early_starts"][group.id] = group.p_early_starts

            # Set field parameters
            for field in field_optimizer_input.fields:
                ampl.param["size"][field.id] = field.size

            # Set incompatible groups (teams that should not have simultaneous activities)
            # Include auto-generated pairs from predefined activity subgroups
            incomp_same_time = list(payload.incompatible_groups or [])
            incomp_same_time.extend(auto_incompatible_same_time)
            ampl.set["INCOMPATIBLE_GROUPS_SAME_TIME"] = incomp_same_time

            # Set incompatible groups same day (subgroups from same team)
            # Include auto-generated pairs from predefined activity subgroups
            incomp_same_day = list(payload.incompatible_groups_same_day or [])
            incomp_same_day.extend(auto_incompatible_same_day)
            ampl.set["INCOMPATIBLE_GROUPS_SAME_DAY"] = incomp_same_day

            # Set AAT (Already Assigned Timeslots) for existing activities
            for field in field_optimizer_input.fields:
                for group in field_optimizer_input.groups:
                    key = (field.id, group.id)
                    if key in aat_map:
                        ampl.set["AAT"][field.id, group.id] = aat_map[key]
                    else:
                        ampl.set["AAT"][field.id, group.id] = []

            # Fix x and y variables for existing activities
            for activity in processed_activities:
                try:
                    ampl.var["y"][activity.field_id,
                                  activity.group_id, activity.start_index].fix(1)
                except Exception as e:
                    print(
                        f"ERROR: Could not fix y variable for {activity.group_id}: {e}")
                    continue

                for idx in activity.timeslot_indexes:
                    try:
                        ampl.var["x"][activity.field_id,
                                      activity.group_id, idx].fix(1)
                    except Exception as e:
                        print(
                            f"ERROR: Could not fix x variable for {activity.group_id} at index {idx}: {e}")

            # Set unavailable times for each field (UT)
            for field in field_optimizer_input.fields:
                ampl.set["UT"][field.id] = field.unavailable_start_times

            # Solve the model with progressive limits:
            # 1) 10s, prove optimality (gap 0)
            # 2) 20s, within 5% OR within 100 points (absgap handles negative objectives)
            # 3) 30s, return best found (safety net)
            solve_iterations = [
                {"time": 10, "gap": 0},
                {"time": 20, "gap": 0.05, "absgap": 100},
                {"time": 30, "gap": 1, "absgap": 100},
            ]

            solve_result = None
            preference_score_value = None
            for iteration in solve_iterations:
                scip_opts = f"lim:time={iteration['time']} lim:gap={iteration['gap']}"
                if "absgap" in iteration:
                    scip_opts += f" lim:absgap={iteration['absgap']}"
                ampl.option["scip_options"] = scip_opts
                ampl.solve()

                solve_result = ampl.get_value("solve_result")
                if solve_result == "infeasible":
                    break

                try:
                    preference_score = ampl.obj["preference_score"]
                    preference_score_value = preference_score.value()
                except Exception:
                    preference_score_value = None

                # Break if solver proved optimality (even if score is negative
                # due to soft constraint penalties — that is still a valid solution)
                if solve_result == "solved":
                    break

            # 1. Infeasible solution
            if solve_result == "infeasible":
                end_time = datetime.now()
                duration_ms = round(
                    (end_time - start_time).total_seconds() * 1000, 2)
                return FieldOptimizerResult(
                    result="infeasible",
                    duration_ms=duration_ms,
                    preference_score=None,
                    activities=[]
                )

            # 2. No objective value (solver error / edge case)
            if preference_score_value is None:
                end_time = datetime.now()
                duration_ms = round(
                    (end_time - start_time).total_seconds() * 1000, 2)
                return FieldOptimizerResult(
                    result="no_objective_value",
                    duration_ms=duration_ms,
                    preference_score=None,
                    activities=[]
                )

            # 3. Solved (possibly with shortfall from soft constraints)
            field_allocations = convert_ampl_x_values_to_allocations(
                ampl, field_optimizer_input.groups)

            existing_allocation_keys = set()
            for activity in processed_activities:
                for idx in activity.timeslot_indexes:
                    existing_allocation_keys.add(
                        (activity.field_id, activity.group_id, idx))

            field_allocations = [
                alloc for alloc in field_allocations
                if (alloc.field, alloc.group, alloc.timeslot_id)
                not in existing_allocation_keys
            ]

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

            activities_not_generated = _extract_shortfall_info(
                ampl, field_optimizer_input.groups
            )

            end_time = datetime.now()
            duration_ms = round(
                (end_time - start_time).total_seconds() * 1000, 2)

            return FieldOptimizerResult(
                result="solved",
                duration_ms=duration_ms,
                preference_score=preference_score_value,
                activities=result_activities,
                activities_not_generated=activities_not_generated if activities_not_generated else None,
            )
        except Exception as e:
            print(f"ERROR: {e}", flush=True)
            traceback.print_exc()
            end_time = datetime.now()
            duration_ms = round(
                (end_time - start_time).total_seconds() * 1000, 2)
            return FieldOptimizerResult(
                result="failure",
                duration_ms=duration_ms,
                preference_score=None,
                activities=[],
                error_message=str(e),
            )

    @staticmethod
    def _setup_ampl(payload: FieldOptimizerPayload):
        """Shared AMPL setup used by both solve() and solve_stream().
        Returns (ampl, converted_payload, processed_activities) tuple."""
        converted_payload = convert_payload_to_input(payload)

        field_optimizer_input = converted_payload.field_optimizer_input
        timeslot_to_index_map = converted_payload.timeslot_to_index_map
        existing_activities = converted_payload.existing_activities
        auto_incompatible_same_day = converted_payload.auto_incompatible_same_day
        auto_incompatible_same_time = converted_payload.auto_incompatible_same_time

        ampl = AMPL()
        ampl.option["solver"] = "scip"
        ampl.read("./ampl/field_optimizer.mod")

        ampl.set["F"] = [
            field.id for field in field_optimizer_input.fields]
        ampl.set["G"] = [
            group.id for group in field_optimizer_input.groups]

        all_timeslots = []
        for day_slots in field_optimizer_input.time_slots:
            all_timeslots.extend(day_slots)
        ampl.set["T"] = all_timeslots

        days = list(range(1, len(field_optimizer_input.time_slots) + 1))
        ampl.set["D"] = days

        for day_idx, day_slots in enumerate(field_optimizer_input.time_slots, start=1):
            ampl.set["DT"][day_idx] = day_slots

        day_start_timeslots: list[int] = [
            day_slots[0]
            for day_slots in field_optimizer_input.time_slots
        ]
        ampl.set["ST"] = day_start_timeslots

        aat_map, processed_activities = build_aat_map(
            existing_activities=existing_activities,
            field_optimizer_input=field_optimizer_input,
            timeslot_to_index_map=timeslot_to_index_map
        )

        for activity in processed_activities:
            group = next(
                (g for g in field_optimizer_input.groups
                 if g.id == activity.group_id), None
            )
            if group and activity.start_index not in group.possible_start_times:
                group.possible_start_times.append(activity.start_index)
                group.possible_start_times.sort()

        for group in field_optimizer_input.groups:
            ampl.set["AT"][group.id] = group.possible_start_times
        for group in field_optimizer_input.groups:
            ampl.set["PT"][group.id] = group.preferred_start_times
        for group in field_optimizer_input.groups:
            ampl.set["PF"][group.id] = group.preferred_field_ids

        for group in field_optimizer_input.groups:
            ampl.param["d"][group.id] = group.duration
            ampl.param["n_min"][group.id] = group.minimum_number_of_activities
            ampl.param["n_max"][group.id] = group.maximum_number_of_activities
            ampl.param["size_req"][group.id] = group.size_required
            ampl.param["prio"][group.id] = group.priority
            ampl.param["p_st1"][group.id] = group.preferred_start_time_activity_1
            ampl.param["p_st2"][group.id] = group.preferred_start_time_activity_2
            ampl.param["p_early_starts"][group.id] = group.p_early_starts

        for field in field_optimizer_input.fields:
            ampl.param["size"][field.id] = field.size

        incomp_same_time = list(payload.incompatible_groups or [])
        incomp_same_time.extend(auto_incompatible_same_time)
        ampl.set["INCOMPATIBLE_GROUPS_SAME_TIME"] = incomp_same_time

        incomp_same_day = list(payload.incompatible_groups_same_day or [])
        incomp_same_day.extend(auto_incompatible_same_day)
        ampl.set["INCOMPATIBLE_GROUPS_SAME_DAY"] = incomp_same_day

        for field in field_optimizer_input.fields:
            for group in field_optimizer_input.groups:
                key = (field.id, group.id)
                if key in aat_map:
                    ampl.set["AAT"][field.id, group.id] = aat_map[key]
                else:
                    ampl.set["AAT"][field.id, group.id] = []

        for activity in processed_activities:
            try:
                ampl.var["y"][activity.field_id,
                              activity.group_id, activity.start_index].fix(1)
            except Exception as e:
                print(
                    f"ERROR: Could not fix y variable for {activity.group_id}: {e}")
                continue

            for idx in activity.timeslot_indexes:
                try:
                    ampl.var["x"][activity.field_id,
                                  activity.group_id, idx].fix(1)
                except Exception as e:
                    print(
                        f"ERROR: Could not fix x variable for {activity.group_id} at index {idx}: {e}")

        for field in field_optimizer_input.fields:
            ampl.set["UT"][field.id] = field.unavailable_start_times

        return ampl, converted_payload, processed_activities

    @staticmethod
    def _build_result(
        ampl: AMPL,
        payload: FieldOptimizerPayload,
        converted_payload,
        processed_activities,
        solve_result: str,
        preference_score_value: float | None,
        start_time: datetime,
    ) -> FieldOptimizerResult:
        """Shared result-building logic used by both solve() and solve_stream()."""
        field_optimizer_input = converted_payload.field_optimizer_input
        time_slots_in_range = converted_payload.time_slots_in_range
        index_to_timeslot_map = converted_payload.index_to_timeslot_map
        time_slot_duration_minutes = converted_payload.time_slot_duration_minutes

        if solve_result == "infeasible":
            end_time = datetime.now()
            duration_ms = round(
                (end_time - start_time).total_seconds() * 1000, 2)
            return FieldOptimizerResult(
                result="infeasible",
                duration_ms=duration_ms,
                preference_score=None,
                activities=[]
            )

        if preference_score_value is None:
            end_time = datetime.now()
            duration_ms = round(
                (end_time - start_time).total_seconds() * 1000, 2)
            return FieldOptimizerResult(
                result="no_objective_value",
                duration_ms=duration_ms,
                preference_score=None,
                activities=[]
            )

        field_allocations = convert_ampl_x_values_to_allocations(
            ampl, field_optimizer_input.groups)

        existing_allocation_keys = set()
        for activity in processed_activities:
            for idx in activity.timeslot_indexes:
                existing_allocation_keys.add(
                    (activity.field_id, activity.group_id, idx))

        field_allocations = [
            alloc for alloc in field_allocations
            if (alloc.field, alloc.group, alloc.timeslot_id)
            not in existing_allocation_keys
        ]

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

        activities_not_generated = _extract_shortfall_info(
            ampl, field_optimizer_input.groups
        )

        end_time = datetime.now()
        duration_ms = round(
            (end_time - start_time).total_seconds() * 1000, 2)

        return FieldOptimizerResult(
            result="solved",
            duration_ms=duration_ms,
            preference_score=preference_score_value,
            activities=result_activities,
            activities_not_generated=activities_not_generated if activities_not_generated else None,
        )

    @staticmethod
    def _sse_event(data: dict) -> str:
        """Format a dict as an SSE event string."""
        return f"data: {json.dumps(data)}\n\n"

    @staticmethod
    def solve_stream(payload: FieldOptimizerPayload) -> Generator[str, None, None]:
        """Generator that yields SSE events during optimization.
        Events: started, iteration_start, iteration_complete, result, error."""
        start_time = datetime.now()

        try:
            ampl, converted_payload, processed_activities = \
                FieldOptimizerService._setup_ampl(payload)

            field_optimizer_input = converted_payload.field_optimizer_input

            elapsed_ms = round(
                (datetime.now() - start_time).total_seconds() * 1000, 2)
            yield FieldOptimizerService._sse_event({
                "type": "started",
                "total_iterations": 3,
                "team_count": len(field_optimizer_input.groups),
                "stadium_count": len(field_optimizer_input.fields),
                "elapsed_ms": elapsed_ms,
            })

            solve_iterations = [
                {"time": 10, "gap": 0},
                {"time": 20, "gap": 0.05, "absgap": 100},
                {"time": 30, "gap": 1, "absgap": 100},
            ]

            solve_result = None
            preference_score_value = None

            for i, iteration in enumerate(solve_iterations):
                yield FieldOptimizerService._sse_event({
                    "type": "iteration_start",
                    "iteration": i + 1,
                    "total_iterations": len(solve_iterations),
                    "time_limit": iteration["time"],
                    "gap_limit": iteration["gap"],
                })

                scip_opts = f"lim:time={iteration['time']} lim:gap={iteration['gap']}"
                if "absgap" in iteration:
                    scip_opts += f" lim:absgap={iteration['absgap']}"
                ampl.option["scip_options"] = scip_opts
                ampl.solve()

                solve_result = ampl.get_value("solve_result")

                try:
                    preference_score = ampl.obj["preference_score"]
                    preference_score_value = preference_score.value()
                except Exception:
                    preference_score_value = None

                elapsed_ms = round(
                    (datetime.now() - start_time).total_seconds() * 1000, 2)
                yield FieldOptimizerService._sse_event({
                    "type": "iteration_complete",
                    "iteration": i + 1,
                    "total_iterations": len(solve_iterations),
                    "solve_result": solve_result,
                    "preference_score": preference_score_value,
                    "elapsed_ms": elapsed_ms,
                })

                if solve_result == "infeasible":
                    break
                if solve_result == "solved":
                    break

            result = FieldOptimizerService._build_result(
                ampl, payload, converted_payload, processed_activities,
                solve_result, preference_score_value, start_time,
            )

            yield FieldOptimizerService._sse_event({
                "type": "result",
                "data": result.model_dump(),
            })

        except Exception as e:
            print(f"ERROR: {e}", flush=True)
            traceback.print_exc()
            elapsed_ms = round(
                (datetime.now() - start_time).total_seconds() * 1000, 2)
            yield FieldOptimizerService._sse_event({
                "type": "error",
                "message": str(e),
                "elapsed_ms": elapsed_ms,
            })
