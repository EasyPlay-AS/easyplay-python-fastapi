def create_number_to_index_mapping(
    numbers: list[int]
) -> dict[str, dict[int, int]]:
    sorted_numbers = sorted(numbers)
    number_to_index_map = {
        number: index + 1
        for index, number in enumerate(sorted_numbers)}
    index_to_number_map = {
        index + 1: number
        for index, number in enumerate(sorted_numbers)}

    return {
        'number_to_index_map': number_to_index_map,
        'index_to_number_map': index_to_number_map
    }
