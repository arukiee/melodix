"""
Automated Database & Timeline Scaling Tests (Phase 2C)
Asserts latency thresholds for DB queries, title searches, and timeline generation
as song library scales up to 500 records.
"""
import pytest
import statistics
import time
from app.core.database import SessionLocal
from app.models.song import Song
from app.services.music_engine.converters.timeline_builder import TimelineBuilder
from app.services.music_engine.converters.mission_builder import MissionBuilder


@pytest.fixture(scope="module")
def seeded_db():
    db = SessionLocal()
    # Seed 100 benchmark songs for automated test run
    songs = []
    for i in range(100):
        songs.append(
            Song(
                title=f"Benchmark Song #{i+1}",
                composer="Scaling Test",
                difficulty="Level 1" if i % 2 == 0 else "Level 2",
                bpm=60 + (i % 40),
                key_signature="C Major",
                time_signature="4/4",
                educational_category="Scaling Benchmark",
                missions=[]
            )
        )
    db.add_all(songs)
    db.commit()

    yield db

    # Teardown
    db.query(Song).filter(Song.composer == "Scaling Test").delete(synchronize_session=False)
    db.commit()
    db.close()


class TestDatabaseScalingSLAs:
    def test_curriculum_query_latency_under_50ms(self, seeded_db):
        """Filtered query for Level 1 songs should execute in < 50ms."""
        latencies = []
        for _ in range(10):
            t0 = time.perf_counter()
            seeded_db.query(Song).filter(Song.difficulty == "Level 1").limit(20).all()
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)

        avg_latency = statistics.mean(latencies)
        assert avg_latency < 50.0, f"Query latency was {avg_latency:.2f}ms (threshold: 50ms)"

    def test_title_search_latency_under_50ms(self, seeded_db):
        """ILike title search query should execute in < 50ms."""
        latencies = []
        for _ in range(10):
            t0 = time.perf_counter()
            seeded_db.query(Song).filter(Song.title.ilike("%Song #5%")).all()
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)

        avg_latency = statistics.mean(latencies)
        assert avg_latency < 50.0, f"Search latency was {avg_latency:.2f}ms (threshold: 50ms)"

    def test_timeline_generation_scaling_under_10ms(self):
        """Timeline generation for a 20-note package should complete in < 10ms."""
        parsed_pkg = {
            "bpm": 120,
            "notes": [{"note": f"C{i%3 + 4}", "duration": 1.0, "measure": i // 4} for i in range(20)]
        }
        t0 = time.perf_counter()
        events = TimelineBuilder.build_expected_events(parsed_pkg)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        assert len(events) == 20
        assert elapsed_ms < 10.0, f"Timeline build took {elapsed_ms:.2f}ms (threshold: 10ms)"

    def test_mission_generation_scaling_under_10ms(self):
        """Mission generation for a 20-note package should complete in < 10ms."""
        parsed_pkg = {
            "bpm": 120,
            "notes": [{"note": f"C{i%3 + 4}", "duration": 1.0, "measure": i // 4} for i in range(20)]
        }
        t0 = time.perf_counter()
        missions = MissionBuilder.generate_missions(parsed_pkg)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        assert len(missions) >= 2
        assert elapsed_ms < 10.0, f"Mission generation took {elapsed_ms:.2f}ms (threshold: 10ms)"
