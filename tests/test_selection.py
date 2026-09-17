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


def test_extension_selects_matching_items():
    exts = ["mp4", "webm", "mp4", "m4a"]
    assert parse_selection("mp4", 4, exts) == [0, 2]


def test_extension_is_case_insensitive():
    exts = ["MP4", "webm"]
    assert parse_selection("mp4", 2, exts) == [0]


def test_mixed_index_and_extension():
    exts = ["mp4", "webm", "m4a"]
    assert parse_selection("2,m4a", 3, exts) == [1, 2]


def test_unknown_extension_falls_back_to_all():
    exts = ["mp4", "webm"]
    assert parse_selection("srt", 2, exts) == [0, 1]
