#!/usr/bin/env python3
"""
Index all data into Meilisearch.
Creates and configures indexes for users, structures, and services.
"""

import json
from pathlib import Path
import meilisearch
from config import CONFIG

DATA_DIR = Path(__file__).parent / "data"


def get_client():
    """Get Meilisearch client."""
    return meilisearch.Client(
        CONFIG["MEILISEARCH_URL"],
        CONFIG["MEILISEARCH_KEY"]
    )


def wait_and_check(client, task_uid):
    """Wait for a Meilisearch task and raise if it didn't succeed."""
    result = client.wait_for_task(task_uid, timeout_in_ms=120000, interval_in_ms=200)
    status = getattr(result, "status", None)
    if status != "succeeded":
        error = getattr(result, "error", None)
        raise RuntimeError(f"Meilisearch task {task_uid} status={status}: {error}")
    return result


def load_json(filename):
    """Load JSON file from data directory."""
    path = DATA_DIR / filename
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def index_users(client):
    """Index users with appropriate settings."""
    print("Indexing users...")
    users = load_json("users.json")

    index = client.index("users")

    # Configure index settings
    index.update_settings({
        "searchableAttributes": ["first_name", "last_name"],
        "filterableAttributes": ["structure_id", "is_professional"],
        "sortableAttributes": ["creation_date", "start_date"],
    })

    # Add in batches (specify primary key to avoid ambiguity with structure_id)
    batch_size = 10000
    for i in range(0, len(users), batch_size):
        batch = users[i:i + batch_size]
        task = index.add_documents(batch, primary_key="id")
        wait_and_check(client, task.task_uid)
        print(f"  Indexed {min(i + batch_size, len(users)):,}/{len(users):,} users")

    print(f"  Total: {len(users):,} users indexed")


def index_structures(client):
    """Index structures with appropriate settings."""
    print("Indexing structures...")
    structures = load_json("structures.json")

    index = client.index("structures")

    index.update_settings({
        "searchableAttributes": ["name", "description", "commune"],
        "filterableAttributes": ["type", "source", "code_postal"],
        "sortableAttributes": ["name"],
    })

    # Add in batches
    batch_size = 1000
    for i in range(0, len(structures), batch_size):
        batch = structures[i:i + batch_size]
        task = index.add_documents(batch, primary_key="id")
        wait_and_check(client, task.task_uid)
        print(f"  Indexed {min(i + batch_size, len(structures))}/{len(structures)} structures")

    print(f"  Total: {len(structures)} structures indexed")


def index_services(client):
    """Index services with appropriate settings."""
    print("Indexing services...")
    services = load_json("services.json")

    index = client.index("services")

    index.update_settings({
        "searchableAttributes": ["name", "description"],
        "filterableAttributes": ["type", "theme", "structure_id"],
        "sortableAttributes": ["name"],
    })

    # Add in batches (specify primary key to avoid ambiguity with structure_id)
    batch_size = 1000
    for i in range(0, len(services), batch_size):
        batch = services[i:i + batch_size]
        task = index.add_documents(batch, primary_key="id")
        wait_and_check(client, task.task_uid)
        print(f"  Indexed {min(i + batch_size, len(services))}/{len(services)} services")

    print(f"  Total: {len(services)} services indexed")


def clear_indexes(client):
    """Delete all indexes to start fresh."""
    print("Clearing existing indexes...")
    for name in ["users", "structures", "services"]:
        try:
            client.index(name).delete()
            print(f"  Deleted {name}")
        except Exception:
            pass  # Index doesn't exist


if __name__ == "__main__":
    client = get_client()
    clear_indexes(client)
    index_users(client)
    index_structures(client)
    index_services(client)
    print("\nDone!")
