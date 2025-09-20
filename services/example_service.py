from datetime import datetime
from amplpy import AMPL
from models.example.example_input import ExampleInput
from models.example.example_output import ExampleOutput


class ExampleService:

    @staticmethod
    def solve_a_b(payload: ExampleInput) -> ExampleOutput:
        start_time = datetime.now()

        try:
            # Initialize AMPL (no need to specify solver)
            ampl = AMPL()

            # Load the model file
            ampl.read("./ampl/a_b.mod")

            # Set the parameters from the payload
            ampl.param["a"] = payload.a
            ampl.param["b"] = payload.b

            # Solve the model
            ampl.solve()

            # Check solve status
            solve_result = ampl.get_value("solve_result")
            if solve_result != "solved":
                return {
                    "result": "FAILURE",
                    "error": "Solver failed to solve the model"
                }

            # Extract results - CORRECTED METHOD
            objective = ampl.obj["Objective"]
            objective_value = objective.value()

            # Build the response
            end_time = datetime.now()
            duration_ms = round(
                (end_time - start_time).total_seconds() * 1000, 2)

            output = ExampleOutput(
                result="SUCCESS",
                objective_value=objective_value,
                variable_values={},
                duration_ms=duration_ms,
            )
            return output
        except Exception as e:
            # Handle errors gracefully
            return {
                "result": "FAILURE",
                "error": str(e)
            }

    @staticmethod
    def solve_example(payload: ExampleInput) -> ExampleOutput:
        start_time = datetime.now()

        try:
            # Initialize AMPL with SCIP solver
            ampl = AMPL()
            ampl.option["solver"] = "scip"

            # Load the model file
            ampl.read("./ampl/example.mod")

            # Set the parameters from the payload
            ampl.param["a"] = payload.a
            ampl.param["b"] = payload.b

            # Solve the model
            ampl.solve()

            # Check solve result
            solve_result = ampl.get_value("solve_result")
            if solve_result != "solved":
                return {
                    "result": "FAILURE",
                    "error": "Solver failed to solve the model"
                }

            # Extract results
            objective = ampl.obj["Objective"]
            objective_value = objective.value()

            # Get variables - Iterate over the EntityMap to get all variable values
            variable_values = {
                "x": ampl.get_variable("x").value(),
            }

            # Build the response
            end_time = datetime.now()
            duration_ms = round(
                (end_time - start_time).total_seconds() * 1000, 2)

            output = ExampleOutput(
                result="SUCCESS",
                objective_value=objective_value,
                variable_values=variable_values,
                duration_ms=duration_ms,
            )
            return output

        except Exception as e:
            # Handle errors gracefully
            return {
                "result": "FAILURE",
                "error": str(e)
            }
