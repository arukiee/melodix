"""
Lightweight Performance Profiler Module (Phase 2D)
Provides context-managed stage timing and latency statistics aggregation
(Average, Median, P95, P99, Max).
"""
import time
import statistics
from typing import Dict, List, Any
from contextlib import contextmanager

class WorkflowProfiler:
    def __init__(self):
        self.timings: Dict[str, List[float]] = {}

    @contextmanager
    def measure(self, stage_name: str):
        """Context manager to measure execution time of a stage in milliseconds."""
        t0 = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            self.timings.setdefault(stage_name, []).append(elapsed_ms)

    def compute_stats(self) -> Dict[str, Dict[str, float]]:
        """Computes Avg, Median, P95, P99, and Max latency for each stage."""
        stats = {}
        for stage, values in self.timings.items():
            if not values:
                continue
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            
            p95_idx = min(int(n * 0.95), n - 1)
            p99_idx = min(int(n * 0.99), n - 1)

            stats[stage] = {
                "count": n,
                "avg_ms": statistics.mean(sorted_vals),
                "median_ms": statistics.median(sorted_vals),
                "p95_ms": sorted_vals[p95_idx],
                "p99_ms": sorted_vals[p99_idx],
                "max_ms": max(sorted_vals)
            }
        return stats
