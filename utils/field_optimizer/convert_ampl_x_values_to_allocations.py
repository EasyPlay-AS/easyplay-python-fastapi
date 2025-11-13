from amplpy import AMPL
from models.field_optimizer.field_allocation import FieldAllocation
from models.field_optimizer.field_optimizer_input import Group


def convert_ampl_x_values_to_allocations(ampl: AMPL, groups: list[Group]) -> list[FieldAllocation]:
    x_var = ampl.get_variable("x")
    x_values = x_var.get_values()
    field_allocations = []

    # Create a lookup dictionary for group size requirements
    group_size_requirement_lookup = {
        group.id: group.size_required for group in groups}

    for index, value in x_values.to_dict().items():
        # Check if the binary variable is effectively "1"
        if value > 0.5:
            # Index contains the tuple (field, group, timeslot)
            f, g, t = index
            size = group_size_requirement_lookup.get(g, 0)

            field_allocations.append(FieldAllocation(
                field=f,
                group=g,
                timeslot_id=int(t),
                size=size
            ))

    return field_allocations
