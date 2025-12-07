#!/usr/bin/env python3
"""
Setup script for initializing data on Railway or fresh deployment.
Downloads data, generates users, and indexes into Meilisearch.

Usage:
    python setup_data.py [--users N]

Options:
    --users N    Number of users to generate (default: 10000 for Railway)
"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description="Setup data for deployment")
    parser.add_argument("--users", type=int, default=10000,
                        help="Number of users to generate (default: 10000)")
    args = parser.parse_args()

    print("=" * 50)
    print("STEP 1: Extracting structures and services")
    print("=" * 50)
    import extract
    extract.DATA_DIR.mkdir(exist_ok=True)
    structures, services = extract.extract_all()
    extract.identify_siaes(structures)

    print("\n" + "=" * 50)
    print(f"STEP 2: Generating {args.users:,} users")
    print("=" * 50)
    import generate_users
    generate_users.generate_all_users(total_users=args.users, users_per_siae=100)

    print("\n" + "=" * 50)
    print("STEP 3: Indexing into Meilisearch")
    print("=" * 50)
    from config import CONFIG
    print(f"  URL: {CONFIG['MEILISEARCH_URL']}")
    print(f"  Key: {CONFIG['MEILISEARCH_KEY'][:8]}..." if CONFIG['MEILISEARCH_KEY'] else "  Key: (none)")

    import index
    client = index.get_client()

    # Test connection
    print("  Testing connection...")
    try:
        health = client.health()
        print(f"  Status: {health['status']}")
    except Exception as e:
        print(f"  ERROR: Cannot connect to Meilisearch: {e}")
        sys.exit(1)

    index.clear_indexes(client)
    index.index_users(client)
    index.index_structures(client)
    index.index_services(client)

    print("\n" + "=" * 50)
    print("SETUP COMPLETE!")
    print("=" * 50)


if __name__ == "__main__":
    main()
