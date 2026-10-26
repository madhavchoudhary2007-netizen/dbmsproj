#!/usr/bin/env python3
"""Verify initial JavaScript gzip size <= 170 KB for every app route."""

import argparse
from pathlib import Path
import sys

from bundle_assets import route_gzip_sizes


LIMIT = 170 * 1024
BASE_DIR = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--next-dir",
        type=Path,
        default=BASE_DIR / "frontend" / ".next",
        help="Next.js build directory (defaults to frontend/.next)",
    )
    args = parser.parse_args()

    try:
        sizes = route_gzip_sizes(args.next_dir)
    except (OSError, ValueError) as exc:
        print(f"Error: invalid or missing bundle evidence: {exc}")
        return 1

    oversized = []
    for route, size in sorted(sizes.items()):
        status = "FAILED" if size > LIMIT else "PASS"
        print(f"{status}: Route {route} initial JS {size} bytes ({size / 1024:.2f} KB)")
        if size > LIMIT:
            oversized.append(route)

    maximum = max(sizes.values())
    print(
        f"Checked {len(sizes)} routes; max: {maximum} bytes "
        f"({maximum / 1024:.2f} KB); limit: 170 KB ({LIMIT} bytes)."
    )
    return 1 if oversized else 0


if __name__ == "__main__":
    sys.exit(main())
