import unittest
from unittest.mock import MagicMock, patch
from app.schemas.search import SearchResult
from app.services.spotify_client import search_spotify_track
from app.services.orchestrator.source_discovery import select_best_candidate

class TestSpotifyCandidateSelection(unittest.TestCase):

    def setUp(self):
        self.results = [
            SearchResult(id="vid1", title="Happy Birthday (Live Concert 2022)", artist="User1", provider="YouTube", difficulty="Intermediate", hasMidi=False, hasChords=False, duration=210, popularity=50000),
            SearchResult(id="vid2", title="Happy Birthday - Single", artist="Singer - Topic", provider="YouTube", difficulty="Beginner", hasMidi=False, hasChords=False, duration=122, popularity=1000000),
            SearchResult(id="vid3", title="Happy Birthday Official Video", artist="Singer", provider="YouTube", difficulty="Beginner", hasMidi=False, hasChords=False, duration=124, popularity=5000000),
            SearchResult(id="vid4", title="Happy Birthday 1 Hour Loop", artist="Looper", provider="YouTube", difficulty="Beginner", hasMidi=False, hasChords=False, duration=3600, popularity=200000),
        ]

    def test_spotify_duration_match_tolerance(self):
        spotify_meta = {
            "title": "Happy Birthday to You",
            "artist": "Singer",
            "duration_ms": 123000, # 123 seconds
            "album": "Classic Tunes"
        }
        # vid2 is 122s (|122 - 123| = 1s <= 3s) and artist ends with "- Topic"
        # vid3 is 124s (|124 - 123| = 1s <= 3s)
        selected = select_best_candidate(self.results, spotify_metadata=spotify_meta)
        self.assertIsNotNone(selected)
        self.assertEqual(selected.id, "vid2")
        self.assertFalse(getattr(selected, "low_confidence_match", True))

    def test_spotify_duration_no_match_fallback(self):
        spotify_meta = {
            "title": "Happy Birthday",
            "artist": "Singer",
            "duration_ms": 50000, # 50 seconds (none of our results match within 3s)
            "album": "Classic Tunes"
        }
        selected = select_best_candidate(self.results, spotify_metadata=spotify_meta)
        self.assertIsNotNone(selected)
        self.assertTrue(getattr(selected, "low_confidence_match", False))

    @patch("app.services.spotify_client.requests.post")
    @patch("app.services.spotify_client.requests.get")
    def test_search_spotify_track(self, mock_get, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"access_token": "fake_token"}

        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "tracks": {
                "items": [
                    {
                        "name": "Shape of You",
                        "artists": [{"name": "Ed Sheeran"}],
                        "duration_ms": 233712,
                        "album": {"name": "÷ (Divide)"},
                        "id": "1301WleyT98MSxVHPZCA6M",
                        "external_urls": {"spotify": "https://open.spotify.com/track/1301WleyT98MSxVHPZCA6M"}
                    }
                ]
            }
        }

        res = search_spotify_track("Shape of You", token="fake_token")
        self.assertIsNotNone(res)
        self.assertEqual(res["title"], "Shape of You")
        self.assertEqual(res["artist"], "Ed Sheeran")
        self.assertEqual(res["duration_ms"], 233712)
        self.assertEqual(res["album"], "÷ (Divide)")

if __name__ == "__main__":
    unittest.main()
