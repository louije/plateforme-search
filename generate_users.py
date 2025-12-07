#!/usr/bin/env python3
"""
Generate diverse users distributed across structures.
Creates ~500,000 users with French, European, and African names.
Ensures ~100 users per SIAE (500 total for 5 SIAEs).
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker

DATA_DIR = Path(__file__).parent / "data"

# Initialize Faker with multiple locales
fake_fr = Faker("fr_FR")
fake_de = Faker("de_DE")
fake_it = Faker("it_IT")
fake_es = Faker("es_ES")
fake_pt = Faker("pt_PT")
fake_nl = Faker("nl_NL")
fake_pl = Faker("pl_PL")

EUROPEAN_FAKERS = [fake_fr, fake_de, fake_it, fake_es, fake_pt, fake_nl, fake_pl]

# African names (Faker has limited African locale support)
AFRICAN_FIRST_NAMES = [
    # West African
    "Amadou", "Fatou", "Moussa", "Aissatou", "Ibrahima", "Mariama", "Ousmane", "Aminata",
    "Mamadou", "Kadiatou", "Seydou", "Fatoumata", "Boubacar", "Mariam", "Abdoulaye", "Adama",
    "Cheikh", "Ndeye", "Modou", "Awa", "Lamine", "Binta", "Souleymane", "Rama",
    # North African
    "Mohamed", "Fatima", "Ahmed", "Khadija", "Youssef", "Amina", "Omar", "Zineb",
    "Karim", "Leila", "Hassan", "Nadia", "Rachid", "Samira", "Samir", "Houda",
    "Khalid", "Salma", "Mehdi", "Imane", "Amine", "Sara", "Hamza", "Yasmine",
    # Central/East African
    "Emmanuel", "Grace", "Patrick", "Esther", "Jean-Pierre", "Marie-Claire", "Olivier", "Claudine",
    "Innocent", "Jeanne", "Faustin", "Chantal", "Bosco", "Solange", "Pacifique", "Yvonne",
    # Southern African
    "Thabo", "Nomvula", "Sipho", "Zanele", "Mandla", "Lindiwe", "Bongani", "Thandiwe",
]

AFRICAN_LAST_NAMES = [
    # West African
    "Diallo", "Ba", "Diop", "Ndiaye", "Sow", "Fall", "Sy", "Gueye",
    "Camara", "Barry", "Traore", "Toure", "Coulibaly", "Keita", "Kone", "Sangare",
    "Cisse", "Dembele", "Diarra", "Sylla", "Bah", "Fofana", "Sidibe", "Sane",
    # North African
    "Benali", "Bouzid", "Khelifi", "Amrani", "Belkacem", "Mansouri", "Cherif", "Bouaziz",
    "Lahlou", "Bennani", "Alaoui", "Tazi", "Idrissi", "Fassi", "Berrada", "Sqalli",
    # Central/East African
    "Habimana", "Uwimana", "Mugabo", "Niyonzima", "Ndayisaba", "Hakizimana", "Nshimiyimana", "Kabera",
    "Mwangi", "Kamau", "Njoroge", "Ochieng", "Otieno", "Wanjiku", "Kariuki", "Kimani",
    # Southern African
    "Dlamini", "Nkosi", "Mthembu", "Zulu", "Ndlovu", "Khumalo", "Moyo", "Ncube",
]


def load_siaes():
    """Load SIAEs from extracted data."""
    siaes_path = DATA_DIR / "siaes.json"
    if not siaes_path.exists():
        raise FileNotFoundError("siaes.json not found. Run extract.py first.")
    with open(siaes_path, encoding="utf-8") as f:
        return json.load(f)


def load_structures():
    """Load all structures."""
    structures_path = DATA_DIR / "structures.json"
    if not structures_path.exists():
        raise FileNotFoundError("structures.json not found. Run extract.py first.")
    with open(structures_path, encoding="utf-8") as f:
        return json.load(f)


def random_name():
    """Generate a random name from various origins."""
    origin = random.choices(
        ["french", "european", "african"],
        weights=[0.5, 0.25, 0.25],  # 50% French, 25% European, 25% African
        k=1
    )[0]

    if origin == "french":
        return fake_fr.first_name(), fake_fr.last_name()
    elif origin == "european":
        faker = random.choice(EUROPEAN_FAKERS)
        return faker.first_name(), faker.last_name()
    else:  # african
        return random.choice(AFRICAN_FIRST_NAMES), random.choice(AFRICAN_LAST_NAMES)


def generate_user(user_id, structure, is_professional=False):
    """Generate a single user."""
    first_name, last_name = random_name()
    start_date = fake_fr.date_between(start_date="-3y", end_date="today")
    creation_date = start_date - timedelta(days=random.randint(1, 30))

    return {
        "id": f"user_{user_id:06d}",
        "first_name": first_name,
        "last_name": last_name,
        "is_professional": is_professional,
        "structure_id": structure.get("id"),
        "structure_name": structure.get("name", "Unknown"),
        "start_date": start_date.isoformat(),
        "creation_date": creation_date.isoformat(),
    }


def generate_all_users(total_users=500000, users_per_siae=100):
    """Generate users distributed across structures."""
    siaes = load_siaes()
    all_structures = load_structures()

    # Filter out SIAEs from general structures
    siae_ids = {s["id"] for s in siaes}
    other_structures = [s for s in all_structures if s["id"] not in siae_ids and s.get("name")]

    if len(siaes) < 5:
        print(f"Warning: Only {len(siaes)} SIAEs found, expected 5")

    users = []
    user_id = 1

    # Phase 1: Generate SIAE users (100 per SIAE)
    print(f"Generating {users_per_siae} users for each of {len(siaes[:5])} SIAEs...")
    for siae in siaes[:5]:
        # 5 professionals per SIAE
        for _ in range(5):
            users.append(generate_user(user_id, siae, is_professional=True))
            user_id += 1

        # Rest are beneficiaries
        for _ in range(users_per_siae - 5):
            users.append(generate_user(user_id, siae, is_professional=False))
            user_id += 1

    siae_users_count = len(users)
    print(f"  Created {siae_users_count} SIAE users")

    # Phase 2: Generate users for other structures
    remaining = total_users - siae_users_count
    print(f"Generating {remaining:,} users across {len(other_structures):,} other structures...")

    # Distribute users across other structures
    batch_size = 10000
    structures_cycle = other_structures * ((remaining // len(other_structures)) + 1)

    for i in range(remaining):
        structure = structures_cycle[i % len(other_structures)]
        is_pro = random.random() < 0.05  # 5% professionals
        users.append(generate_user(user_id, structure, is_professional=is_pro))
        user_id += 1

        if (i + 1) % batch_size == 0:
            print(f"  Generated {siae_users_count + i + 1:,} / {total_users:,} users...")

    # Save to file
    output_path = DATA_DIR / "users.json"
    print(f"Saving {len(users):,} users to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False)

    # Stats
    pros = sum(1 for u in users if u["is_professional"])
    print(f"\nGenerated {len(users):,} users:")
    print(f"  - {pros:,} professionals ({100*pros/len(users):.1f}%)")
    print(f"  - {len(users)-pros:,} beneficiaries")

    print(f"\nSIAE distribution:")
    for siae in siaes[:5]:
        count = sum(1 for u in users if u["structure_id"] == siae["id"])
        print(f"  {siae['name'][:40]}: {count} users")

    return users


if __name__ == "__main__":
    generate_all_users()
