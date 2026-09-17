from totaldownloader.torrent import TorrentFile


def test_ext_from_simple_path():
    assert TorrentFile(index=0, path="Season1/Episode01.mkv", size=100).ext == "mkv"


def test_ext_without_extension():
    assert TorrentFile(index=0, path="README", size=10).ext == "?"
