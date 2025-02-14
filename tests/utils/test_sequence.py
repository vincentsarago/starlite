from starlite.utils.sequence import find_index, unique


def test_find_index():
    assert find_index([1, 2], lambda x: x == 2) == 1
    assert find_index([1, 3], lambda x: x == 2) == -1


def test_unique():
    assert unique([1, 1, 1, 2]) == [1, 2]

    def x():
        pass

    def y():
        pass

    unique_functions = unique([x, x, y, y])
    assert unique_functions == [x, y] or unique_functions == [y, x]  # noqa: SIM109
    my_list = []
    assert sorted(unique([my_list, my_list, my_list])) == sorted([my_list])
