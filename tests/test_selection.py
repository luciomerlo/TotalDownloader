from totaldownloader.selection import parse_selection


def test_empty_selects_all():
    assert parse_selection("", 3) == [0, 1, 2]


def test_todos_selects_all():
    assert parse_selection("todos", 3) == [0, 1, 2]


def test_specific_indices():
    assert parse_selection("1,3", 3) == [0, 2]


def test_out_of_range_indices_are_ignored():
    assert parse_selection("1,9", 3) == [0]


def test_garbage_falls_back_to_all():
    assert parse_selection("no", 3) == [0, 1, 2]
