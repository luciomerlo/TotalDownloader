from totaldownloader.http_direct import HttpTarget, filename_from_url, list_http_target, split_ranges


def test_filename_from_simple_url():
    assert filename_from_url("https://example.com/archivo.zip") == "archivo.zip"


def test_filename_from_url_with_encoding():
    assert filename_from_url("https://example.com/mi%20archivo.zip") == "mi archivo.zip"


def test_filename_from_url_without_path_falls_back():
    assert filename_from_url("https://example.com/") == "download.bin"


def test_list_http_target_ext():
    target = list_http_target("https://example.com/archivo.zip")
    assert target == HttpTarget(filename="archivo.zip")
    assert target.ext == "zip"


def test_split_ranges_even():
    assert split_ranges(100, 4) == [(0, 24), (25, 49), (50, 74), (75, 99)]


def test_split_ranges_uneven_last_gets_remainder():
    assert split_ranges(10, 3) == [(0, 2), (3, 5), (6, 9)]


def test_split_ranges_single_part():
    assert split_ranges(50, 1) == [(0, 49)]


def test_split_ranges_covers_whole_file_without_gaps():
    total = 137
    ranges = split_ranges(total, 5)
    assert ranges[0][0] == 0
    assert ranges[-1][1] == total - 1
    for (_, end), (next_start, _) in zip(ranges, ranges[1:], strict=False):
        assert next_start == end + 1
