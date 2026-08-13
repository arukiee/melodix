"""
Database Scaling Benchmark Script (Phase 2C)
Measures query latency, import throughput, timeline building, and mission generation
across progressive song library sizes (50, 100, 250, 500 songs).
"""
import time
import resource
import os
import statistics
from typing import List, Dict, Any

from app.core.database import SessionLocal, engine
from app.models.song import Song
from app.services.music_engine.converters.timeline_builder import TimelineBuilder
from app.services.music_engine.converters.mission_builder import MissionBuilder

TITLES = [
    "Minuet in G Major", "Moonlight Sonata", "Fur Elise", "Clair de Lune",
    "Canon in D", "Nocturne Op. 9 No. 2", "Prelude in C Major", "Turkish March",
    "Gymnopédie No. 1", "Waltz in A Minor", "The Entertainer", "Maple Leaf Rag",
    "Sonata Facile", "Hungarian Dance No. 5", "Spring Song", "Liebestraum No. 3"
]

COMPOSERS = [
    "J.S. Bach", "L.v. Beethoven", "C. Debussy", "J. Pachelbel",
    "F. Chopin", "W.A. Mozart", "E. Satie", "S. Joplin", "F. Liszt"
]

DIFFICULTIES = ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5"]
CATEGORIES = ["Beginner Foundation", "Baroque Masters", "Romantic Phrasing", "Classical Sonatinas", "Modern Expressions"]


def _generate_synthetic_song(index: int) -> Dict[str, Any]:
    """Generates realistic synthetic song data package."""
    title = f"{TITLES[index % len(TITLES)]} #{index + 1}"
    composer = COMPOSERS[index % len(COMPOSERS)]
    difficulty = DIFFICULTIES[index % len(DIFFICULTIES)]
    category = CATEGORIES[index % len(CATEGORIES)]
    
    notes = [
        {"note": "C4", "duration": 1.0, "measure": 0},
        {"note": "E4", "duration": 1.0, "measure": 0},
        {"note": "G4", "duration": 1.0, "measure": 0},
        {"note": "C5", "duration": 1.0, "measure": 0},
        {"note": "B4", "duration": 1.0, "measure": 1},
        {"note": "A4", "duration": 1.0, "measure": 1},
        {"note": "G4", "duration": 2.0, "measure": 1},
    ]

    parsed_package = {
        "title": title,
        "composer": composer,
        "bpm": 80 + (index % 60),
        "key_signature": "C Major",
        "time_signature": "4/4",
        "notes": notes
    }

    missions = MissionBuilder.generate_missions(parsed_package)

    return {
        "title": title,
        "composer": composer,
        "difficulty": difficulty,
        "bpm": 80 + (index % 60),
        "key_signature": "C Major",
        "time_signature": "4/4",
        "educational_category": category,
        "missions": missions,
        "parsed_package": parsed_package
    }


def run_scaling_benchmark():
    db = SessionLocal()
    tiers = [50, 100, 250, 500]

    print("\n==========================================================")
    print("           MELODIX DATABASE SCALING BENCHMARK             ")
    print("==========================================================\n")

    # Clean previous benchmark test entries
    db.query(Song).filter(Song.title.like("%#%")).delete(synchronize_session=False)
    db.commit()

    report_data = []

    try:
        current_inserted = 0
        for target_count in tiers:
            needed = target_count - current_inserted
            
            # 1. Measure DB Insert / Import Throughput
            start_insert = time.perf_counter()
            songs_to_add = []
            packages = []

            for i in range(current_inserted, target_count):
                pkg = _generate_synthetic_song(i)
                packages.append(pkg["parsed_package"])
                song = Song(
                    title=pkg["title"],
                    composer=pkg["composer"],
                    difficulty=pkg["difficulty"],
                    bpm=pkg["bpm"],
                    key_signature=pkg["key_signature"],
                    time_signature=pkg["time_signature"],
                    educational_category=pkg["educational_category"],
                    missions=pkg["missions"]
                )
                songs_to_add.append(song)

            db.add_all(songs_to_add)
            db.commit()
            insert_elapsed = (time.perf_counter() - start_insert) * 1000.0  # ms
            avg_import_per_song = insert_elapsed / needed

            current_inserted = target_count

            # 2. Measure Curriculum Query Latency (List 20 songs with pagination)
            query_latencies = []
            for _ in range(30):
                t0 = time.perf_counter()
                res = db.query(Song).filter(Song.difficulty == "Level 1").limit(20).all()
                t1 = time.perf_counter()
                query_latencies.append((t1 - t0) * 1000.0)

            avg_query_ms = statistics.mean(query_latencies)
            p95_query_ms = sorted(query_latencies)[int(len(query_latencies) * 0.95)]

            # 3. Measure Title Search Performance
            search_latencies = []
            for _ in range(30):
                t0 = time.perf_counter()
                res = db.query(Song).filter(Song.title.ilike("%Sonata%")).all()
                t1 = time.perf_counter()
                search_latencies.append((t1 - t0) * 1000.0)

            avg_search_ms = statistics.mean(search_latencies)

            # 4. Measure Timeline Building Performance
            timeline_latencies = []
            for pkg in packages[:20]:
                t0 = time.perf_counter()
                TimelineBuilder.build_expected_events(pkg)
                t1 = time.perf_counter()
                timeline_latencies.append((t1 - t0) * 1000.0)

            avg_timeline_ms = statistics.mean(timeline_latencies)

            # 5. Measure Mission Generation Performance
            mission_latencies = []
            for pkg in packages[:20]:
                t0 = time.perf_counter()
                MissionBuilder.generate_missions(pkg)
                t1 = time.perf_counter()
                mission_latencies.append((t1 - t0) * 1000.0)

            avg_mission_ms = statistics.mean(mission_latencies)

            # 6. Memory usage (maxrss in KB on Linux/Mac)
            mem_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0

            tier_report = {
                "songs": target_count,
                "import_avg_ms": avg_import_per_song,
                "query_avg_ms": avg_query_ms,
                "query_p95_ms": p95_query_ms,
                "search_avg_ms": avg_search_ms,
                "timeline_avg_ms": avg_timeline_ms,
                "mission_avg_ms": avg_mission_ms,
                "mem_mb": mem_mb
            }
            report_data.append(tier_report)

            print(f"✅ Tier {target_count:3d} Songs | Import: {avg_import_per_song:5.2f} ms/song | "
                  f"Query Avg: {avg_query_ms:5.2f} ms (p95: {p95_query_ms:5.2f} ms) | "
                  f"Search: {avg_search_ms:5.2f} ms | Timeline: {avg_timeline_ms:5.3f} ms | "
                  f"RAM: {mem_mb:5.1f} MB")

        print("\n==========================================================")
        print("                DATABASE SCALING SUMMARY                  ")
        print("==========================================================")
        print(f"{'Tier':<10} {'Import/Song':<14} {'Query (Avg/p95)':<18} {'Search (Avg)':<14} {'RAM':<10}")
        print("----------------------------------------------------------")
        for r in report_data:
            print(f"{r['songs']:<10} {r['import_avg_ms']:5.2f} ms        "
                  f"{r['query_avg_ms']:5.2f} / {r['query_p95_ms']:5.2f} ms      "
                  f"{r['search_avg_ms']:5.2f} ms       {r['mem_mb']:5.1f} MB")
        print("==========================================================\n")

    finally:
        # Cleanup synthetic test songs
        db.query(Song).filter(Song.title.like("%#%")).delete(synchronize_session=False)
        db.commit()
        db.close()


if __name__ == "__main__":
    run_scaling_benchmark()
