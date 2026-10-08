import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.song import Song
import uuid

def mock_get_current_user():
    return User(id=uuid.uuid4(), email="test@example.com", is_active=True)

def mock_get_db():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    return db

app.dependency_overrides[get_current_user] = mock_get_current_user
app.dependency_overrides[get_db] = mock_get_db

class TestSpotifyEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    @patch("app.services.spotify_client.search_spotify_tracks")
    def test_search_songs_spotify(self, mock_spotify_search):
        mock_spotify_search.return_value = [
            {
                "title": "Shape of You",
                "artist": "Ed Sheeran",
                "duration_ms": 233712,
                "album": "÷ (Divide)",
                "album_art_url": "https://i.scdn.co/image/ab67616d0000b273ba5db46f4b838ef6027e6f96",
                "spotify_id": "1301WleyT98MSxVHPZCA6M",
            }
        ]

        response = self.client.get("/songs/search?q=Shape+of+You")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        
        # Verify 100% of YouTube metadata is absent
        item = data[0]
        self.assertEqual(item["provider"], "Spotify")
        self.assertEqual(item["thumbnailUrl"], "https://i.scdn.co/image/ab67616d0000b273ba5db46f4b838ef6027e6f96")
        self.assertNotIn("youtube", str(item).lower())
        self.assertNotIn("channel", str(item).lower())
        self.assertNotIn("video", str(item).lower())

    @patch("app.services.orchestrator.source_discovery.SourceDiscoveryService.discover_and_analyze")
    def test_select_spotify_track(self, mock_discover):
        mock_job_id = uuid.uuid4()
        mock_discover.return_value = mock_job_id

        payload = {
            "spotify_track_id": "1301WleyT98MSxVHPZCA6M",
            "title": "Shape of You",
            "artist": "Ed Sheeran",
            "album": "÷ (Divide)",
            "duration_ms": 233712,
            "album_art_url": "https://i.scdn.co/image/ab67616d0000b273ba5db46f4b838ef6027e6f96"
        }

        response = self.client.post("/songs/select", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIsNotNone(data["song_id"])
        self.assertEqual(data["processing_job_id"], str(mock_job_id))
        
        # Confirm payload contains ZERO YouTube metadata
        self.assertNotIn("youtube", str(data).lower())
        self.assertNotIn("channel", str(data).lower())
        self.assertNotIn("video", str(data).lower())

if __name__ == "__main__":
    unittest.main()

