from datetime import datetime
from amplpy import AMPL
from models.field_optimizer.field_optimizer_input import FieldOptimizerInput
from models.field_optimizer.field_optimizer_response import FieldOptimizerResponse
from models.field_optimizer.field_allocation import FieldAllocation
from utils.field_optimizer_utils import group_activities_by_consecutive_timeslots


class FieldOptimizerService:

    @staticmethod
    def solve(payload: FieldOptimizerInput) -> FieldOptimizerResponse:
        start_time = datetime.now()

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
            ampl.set["F"] = [field.name for field in payload.fields]
            ampl.set["G"] = [group.name for group in payload.groups]
            ampl.set["T"] = payload.time_slots

            # Set available starting times for each group (AT)
            for group in payload.groups:
                ampl.set["AT"][group.name] = group.possible_start_times

            # Set preferred starting times for each group (PT)
            for group in payload.groups:
                ampl.set["PT"][group.name] = group.preferred_start_times

            # Set unavailable times for each field (UT)
            for field in payload.fields:
                ampl.set["UT"][field.name] = field.unavailable_start_times

            # Set group parameters
            for group in payload.groups:
                ampl.param["d"][group.name] = group.duration
                ampl.param["n_min"][group.name] = group.minimum_number_of_activities
                ampl.param["n_max"][group.name] = group.maximum_number_of_activities
                ampl.param["size_req"][group.name] = group.size_required
                ampl.param["prio"][group.name] = group.priority
                ampl.param["p_st1"][group.name] = group.preferred_start_time_activity_1
                ampl.param["p_st2"][group.name] = group.preferred_start_time_activity_2

            # Set field parameters
            for field in payload.fields:
                ampl.param["size"][field.name] = field.size

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
            field_allocations: list[FieldAllocation] = []
            x_var = ampl.get_variable("x")
            x_values = x_var.get_values()
            for index, value in x_values.to_dict().items():  # `.to_dict()` converts the data to a dictionary
                if value > 0.5:  # Check if the binary variable is effectively "1"
                    # Index contains the tuple (field, group, timeslot)
                    f, g, t = index
                    field_allocations.append(FieldAllocation(
                        field=f,
                        group=g,
                        # Ensure timeslot returns as an integer
                        timeslot=int(t)
                    ))

            activities = group_activities_by_consecutive_timeslots(
                field_allocations)

            # Build the response
            end_time = datetime.now()
            duration_ms = round(
                (end_time - start_time).total_seconds() * 1000, 2)

            return FieldOptimizerResponse(
                result="SUCCESS",
                duration_ms=duration_ms,
                preference_score=preference_score_value,
                activities=activities,
            )
        except Exception as e:
            # Handle errors gracefully
            return {
                "result": "FAILURE",
                "error": str(e)
            }
