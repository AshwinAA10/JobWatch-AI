#!/usr/bin/env python3
"""Automated post-deployment smoke test suite.

Probes root metadata, liveness, and database readiness endpoints to verify
that a deployed environment is operational.
"""

import argparse
import sys
import urllib.error
import urllib.request
import json


def probe_endpoint(url: str, expected_status: int = 200) -> bool:
    print(f"Probing {url} ... ", end="")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "JobWatch-SmokeTest/1.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.getcode()
            body = response.read().decode("utf-8")
            if status == expected_status:
                print(f"[OK] (HTTP {status})")
                return True
            else:
                print(f"[FAIL] (Expected {expected_status}, got {status})")
                return False
    except urllib.error.HTTPError as exc:
        print(f"[FAIL] (HTTP {exc.code})")
        return False
    except Exception as exc:
        print(f"[FAIL] ({exc})")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="JobWatch AI Post-Deployment Smoke Tests")
    parser.add_argument("--target-url", default="http://localhost:8000", help="Base backend API URL to probe")
    args = parser.parse_args()

    base_url = args.target_url.rstrip("/")
    print("=" * 60)
    print(f"JobWatch AI — Smoke Tests for: {base_url}")
    print("=" * 60)

    tests = [
        f"{base_url}/",
        f"{base_url}/health",
        f"{base_url}/health/live",
        f"{base_url}/health/ready",
        f"{base_url}/api/v1/metrics",
    ]

    results = [probe_endpoint(url) for url in tests]

    print("-" * 60)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"Smoke Test Results: {passed}/{total} passed.")

    if passed == total:
        print("[PASS] Deployment verification succeeded.")
        return 0
    else:
        print("[FAIL] Deployment verification encountered errors.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
