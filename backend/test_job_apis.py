"""Quick script to test external job API responses."""

import json

from app.adapters.job_sources.adzuna_adapter import create_adzuna_adapter
from app.adapters.job_sources.remoteok_adapter import create_remoteok_adapter
from app.core.config import settings


def test_adzuna():
    print("\n" + "=" * 80)
    print("TESTING ADZUNA API")
    print("=" * 80)

    adapter = create_adzuna_adapter(
        app_id=settings.ADZUNA_APP_ID,
        api_key=settings.ADZUNA_API_KEY,
        country="ca",
    )

    print("\n" + "=" * 80)
    print("Test 1: No location filter")
    print("Python jobs, no location")
    jobs = adapter.fetch_jobs(query="python", location=None, limit=5)
    print(f"Fetched {len(jobs)} jobs")
    if jobs:
        print(json.dumps(jobs[0], indent=2, default=str))

    print("\n" + "=" * 80)
    print("Test 2: Specific city")
    print("Javascript jobs in New York")
    jobs = adapter.fetch_jobs(query="python", location="New York", limit=5)
    print(f"Fetched {len(jobs)} jobs")
    if jobs:
        print(json.dumps(jobs[0], indent=2, default=str))

    print("\n" + "=" * 80)
    print("Test 3: Broader search term")
    print("Software engineer, no location")
    jobs = adapter.fetch_jobs(query="software engineer", location=None, limit=5)
    print(f"Fetched {len(jobs)} jobs")
    if jobs:
        print(json.dumps(jobs[0], indent=2, default=str))


def test_remoteok():
    """Test RemoteOK API."""
    print("\n" + "=" * 80)
    print("TESTING REMOTEOK API")
    print("=" * 80)

    adapter = create_remoteok_adapter()

    jobs = adapter.fetch_jobs(query="python, canada", limit=1)

    print(f"\nFetched {len(jobs)} jobs from RemoteOK:\n")

    for i, job in enumerate(jobs, 1):
        print(f"\n--- Job {i} ---")
        print(json.dumps(job, indent=2, default=str))


if __name__ == "__main__":
    try:
        test_adzuna()
    except Exception as e:
        print(f"\nAdzuna Error: {e}")

    # try:
    #     test_remoteok()
    # except Exception as e:
    #     print(f"\nRemoteOK Error: {e}")
