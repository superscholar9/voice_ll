#!/usr/bin/env python
"""Standalone script to clean up expired cover assets.

Can be run manually for maintenance or testing:
    python scripts/cleanup_cover_assets.py
    python scripts/cleanup_cover_assets.py --dry-run
    python scripts/cleanup_cover_assets.py --ttl-hours 48
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.tasks.cleanup_tasks import cleanup_expired_assets


def main():
    """Run cleanup with command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Clean up expired cover asset directories"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--ttl-hours",
        type=int,
        default=None,
        help="Override TTL in hours (default: from COVER_RESULT_TTL_HOURS config)"
    )

    args = parser.parse_args()

    print(f"Running cleanup (dry_run={args.dry_run}, ttl_hours={args.ttl_hours or 'default'})")
    print("-" * 60)

    result = cleanup_expired_assets(ttl_hours=args.ttl_hours, dry_run=args.dry_run)

    print("-" * 60)
    print(f"Results:")
    print(f"  Expired jobs deleted: {result['deleted_count']}")
    print(f"  Orphaned dirs deleted: {result['orphaned_count']}")
    print(f"  Space freed: {result['freed_bytes'] / (1024 * 1024):.2f} MB")

    if args.dry_run:
        print("\n[DRY RUN] No files were actually deleted.")


if __name__ == "__main__":
    main()
