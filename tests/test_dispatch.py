from totaldownloader.dispatch import detect_source_type


def test_magnet_link_is_torrent():
    assert detect_source_type("magnet:?xt=urn:btih:abc123") == "torrent"


def test_torrent_file_is_torrent():
    assert detect_source_type("https://example.com/file.torrent") == "torrent"


def test_youtube_url_is_media():
    assert detect_source_type("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "media"


def test_generic_url_is_http():
    assert detect_source_type("https://example.com/archivo.zip") == "http"
