from app.schemas.search import SearchFilter
from app.services.search.providers.youtube import resolve_search_limit


def test_default_youtube_limit_is_ten():
    assert resolve_search_limit() == 10


def test_respects_requested_limit_in_range():
    assert resolve_search_limit(filters=SearchFilter(limit=7)) == 7
    assert resolve_search_limit(filters=SearchFilter(limit=10)) == 10


def test_clamps_limit_to_supported_range():
    assert resolve_search_limit(filters=SearchFilter(limit=3)) == 7
    assert resolve_search_limit(filters=SearchFilter(limit=12)) == 10
