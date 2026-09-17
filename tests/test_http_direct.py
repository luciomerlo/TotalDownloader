from totaldownloader.http_direct import filename_from_url


def test_filename_from_simple_url():
    assert filename_from_url("https://example.com/archivo.zip") == "archivo.zip"


def test_filename_from_url_with_encoding():
    assert filename_from_url("https://example.com/mi%20archivo.zip") == "mi archivo.zip"


def test_filename_from_url_without_path_falls_back():
    assert filename_from_url("https://example.com/") == "download.bin"
