"""
run_load_tests.py — Automated load test runner at all task.md-specified levels.

Runs Locust in headless mode at each concurrency level and saves
CSV results to backend/tests/load/results/

Usage:
    python backend/tests/load/run_load_tests.py
"""

import subprocess
import os
import sys

# All test levels from task.md
LEVELS = [
    {"users": 100,   "spawn_rate": 10,  "duration": "60s",  "name": "baseline"},
    {"users": 500,   "spawn_rate": 50,  "duration": "120s", "name": "moderate"},
    {"users": 1000,  "spawn_rate": 100, "duration": "120s", "name": "high"},
    {"users": 5000,  "spawn_rate": 500, "duration": "180s", "name": "stress"},
    {"users": 10000, "spawn_rate": 1000, "duration": "180s", "name": "peak"},
]

HOST = os.getenv("LOCUST_HOST", "http://localhost:8000")
LOCUSTFILE = os.path.join(os.path.dirname(__file__), "locustfile.py")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


def run_level(level: dict):
    """Run a single load test level."""
    name = level["name"]
    csv_prefix = os.path.join(RESULTS_DIR, name)

    print(f"\n{'='*60}")
    print(f"  Running: {name} ({level['users']} users, {level['duration']})")
    print(f"{'='*60}\n")

    cmd = [
        sys.executable, "-m", "locust",
        "-f", LOCUSTFILE,
        "--host", HOST,
        "--headless",
        "-u", str(level["users"]),
        "-r", str(level["spawn_rate"]),
        "--run-time", level["duration"],
        "--csv", csv_prefix,
        "--csv-full-history",
        "--html", f"{csv_prefix}_report.html",
    ]

    result = subprocess.run(cmd, capture_output=False)
    if result.returncode == 0:
        print(f"\n✅ {name} test complete. Results: {csv_prefix}_stats.csv")
    else:
        print(f"\n⚠️  {name} test finished with exit code {result.returncode}")


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print("Prompt Polisher — Load Testing Suite")
    print(f"Target: {HOST}")
    print(f"Results directory: {RESULTS_DIR}")

    if len(sys.argv) > 1:
        # Run a specific level by name
        target = sys.argv[1].lower()
        level = next((l for l in LEVELS if l["name"] == target), None)
        if level:
            run_level(level)
        else:
            print(f"Unknown level: {target}")
            print(f"Available: {', '.join(str(l['name']) for l in LEVELS)}")
            sys.exit(1)
    else:
        # Run all levels sequentially
        for level in LEVELS:
            run_level(level)

    print("\n🏁 All load tests complete!")
    print(f"📊 Reports saved to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
