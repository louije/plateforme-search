#!/usr/bin/env python3
"""
Generate fake French users distributed across SIAEs.
Creates 100 users: 5 professionals (1 per SIAE) + 95 beneficiaries.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker

DATA_DIR = Path(__file__).parent / "data"
fake = Faker("fr_FR")


def load_siaes():
    """Load SIAEs from extracted data."""
    siaes_path = DATA_DIR / "siaes.json"
    if not siaes_path.exists():
        raise FileNotFoundError(
            "siaes.json not found. Run extract.py first."
        )

    with open(siaes_path, encoding="utf-8") as f:
        return json.load(f)


def generate_user(user_id, structure, is_professional=False):
    """Generate a single user."""
    start_date = fake.date_between(start_date="-2y", end_date="today")
    creation_date = start_date - timedelta(days=random.randint(1, 30))

    return {
        "id": f"user_{user_id:03d}",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "is_professional": is_professional,
        "structure_id": structure.get("id"),
        "structure_name": structure.get("name", "Unknown"),
        "start_date": start_date.isoformat(),
        "creation_date": creation_date.isoformat(),
    }


def generate_all_users():
    """Generate 100 users across 5 SIAEs."""
    siaes = load_siaes()

    if len(siaes) < 5:
        print(f"Warning: Only {len(siaes)} SIAEs found, expected 5")

    users = []
    user_id = 1

    for i, siae in enumerate(siaes[:5]):
        # 1 professional per SIAE
        users.append(generate_user(user_id, siae, is_professional=True))
        user_id += 1

        # 19 beneficiaries per SIAE
        for _ in range(19):
            users.append(generate_user(user_id, siae, is_professional=False))
            user_id += 1

    output_path = DATA_DIR / "users.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

    pros = sum(1 for u in users if u["is_professional"])
    print(f"Generated {len(users)} users ({pros} professionals, {len(users) - pros} beneficiaries)")
    print(f"Saved to {output_path}")

    # Show distribution
    print("\nDistribution by SIAE:")
    for siae in siaes[:5]:
        count = sum(1 for u in users if u["structure_id"] == siae["id"])
        print(f"  {siae['name'][:40]}: {count} users")

    return users


if __name__ == "__main__":
    generate_all_users()
