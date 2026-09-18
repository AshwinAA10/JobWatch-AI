"""CLI development utility for testing job connectors directly.

Usage:
    python -m app.connectors.cli --source-type greenhouse --url https://boards.greenhouse.io/acme
    python -m app.connectors.cli --source-type lever --url https://jobs.lever.co/netflix
    python -m app.connectors.cli --source-type workday --url https://adobe.wd5.myworkdayjobs.com/en-US/external_careers
"""

import argparse
import asyncio
import json
import sys
import uuid
from app.connectors.exceptions import ConnectorError
from app.connectors.factory import ConnectorFactory
from app.models.career_source import CareerSource


async def run_connector(source_type: str, url: str, limit: int = 5) -> None:
    """Instantiate and execute connector for testing."""
    dummy_source = CareerSource(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        name=f"CLI Test {source_type.title()}",
        source_type=source_type,
        base_url=url,
        is_active=True,
    )

    try:
        connector = ConnectorFactory.create(dummy_source)
        print(f"[*] Initialized connector: {connector.__class__.__name__}")
        print(f"[*] Target base URL: {url}")
        print("[*] Fetching jobs...")

        jobs = await connector.fetch_jobs()
        print(f"[+] Successfully fetched {len(jobs)} normalized jobs.\n")

        display_count = min(len(jobs), limit)
        for idx, job in enumerate(jobs[:display_count], 1):
            print(f"--- Job #{idx} ---")
            print(f"ID:          {job.external_id}")
            print(f"Title:       {job.title}")
            print(f"Location:    {job.location}")
            print(f"Workplace:   {job.workplace_type}")
            print(f"Employment:  {job.employment_type}")
            print(f"Apply URL:   {job.application_url}")
            print(f"Source URL:  {job.source_url}")
            print(f"Posted At:   {job.posted_at}")
            print()

        if len(jobs) > display_count:
            print(f"... and {len(jobs) - display_count} more jobs.")

    except ConnectorError as err:
        print(f"[-] Connector Error: {err}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"[-] Unexpected Error: {exc}", file=sys.stderr)
        sys.exit(2)


def main() -> None:
    parser = argparse.ArgumentParser(description="JobWatch AI Connector Dev Test Harness")
    parser.add_argument(
        "--source-type",
        "-t",
        required=True,
        choices=["greenhouse", "lever", "workday"],
        help="Career portal provider type",
    )
    parser.add_argument(
        "--url",
        "-u",
        required=True,
        help="Career source base URL",
    )
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=5,
        help="Maximum number of sample jobs to print (default: 5)",
    )

    args = parser.parse_args()
    asyncio.run(run_connector(args.source_type, args.url, args.limit))


if __name__ == "__main__":
    main()
