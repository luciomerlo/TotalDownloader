from totaldownloader.media import describe_format


def test_describe_format_uses_resolution():
    assert describe_format({"resolution": "1920x1080", "vcodec": "avc1"}) == "1920x1080"


def test_describe_format_audio_only():
    assert describe_format({"resolution": "audio only", "vcodec": "none", "acodec": "mp4a"}) == "audio"


def test_describe_format_video_without_resolution():
    assert describe_format({"vcodec": "avc1", "acodec": "none"}) == "video"


def test_describe_format_unknown():
    assert describe_format({"vcodec": "none", "acodec": "none"}) == "?"
