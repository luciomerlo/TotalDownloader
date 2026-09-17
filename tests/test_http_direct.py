from totaldownloader.http_direct import HttpTarget, filename_from_url, list_http_target


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
