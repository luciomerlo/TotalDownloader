"""Detección del tipo de fuente para enrutar al motor de descarga correcto."""

from yt_dlp.extractor import gen_extractor_classes

_media_extractors = None


def _get_media_extractors():
    global _media_extractors
    if _media_extractors is None:
        _media_extractors = [
            ie for ie in gen_extractor_classes() if ie.IE_NAME != "generic"
        ]
    return _media_extractors


def detect_source_type(source: str) -> str:
    if source.startswith("magnet:") or source.endswith(".torrent"):
        return "torrent"
    if any(ie.suitable(source) for ie in _get_media_extractors()):
        return "media"
    return "http"
