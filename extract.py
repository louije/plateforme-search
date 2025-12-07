#!/usr/bin/env python3
"""
Extract structures and services from swiper data.
Transforms and saves to local data/ directory.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
SWIPER_DATA = Path(__file__).parent.parent / "swiper" / "data"


def load_swiper_structures():
    """Load structures from swiper data."""
    path = SWIPER_DATA / "structures.json"
    if not path.exists():
        raise FileNotFoundError(f"Swiper data not found at {path}")

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_swiper_services():
    """Load services from swiper data."""
    path = SWIPER_DATA / "services.json"
    if not path.exists():
        raise FileNotFoundError(f"Swiper data not found at {path}")

    with open(path, encoding="utf-8") as f:
        return json.load(f)


def transform_structure(s):
    """Transform structure to our schema."""
    geo = s.get("_geo", {}) or {}
    return {
        "id": s.get("id"),
        "name": s.get("nom", ""),
        "type": s.get("typologie", ""),
        "address": s.get("adresse", ""),
        "commune": s.get("commune", ""),
        "code_postal": s.get("code_postal", ""),
        "latitude": geo.get("lat"),
        "longitude": geo.get("lng"),
        "description": s.get("presentation_detail") or s.get("presentation_resume", ""),
        "source": s.get("source", ""),
        "lien_source": s.get("lien_source", ""),
        "telephone": s.get("telephone", ""),
        "courriel": s.get("courriel", ""),
        "site_web": s.get("site_web", ""),
    }


def transform_service(s):
    """Transform service to our schema."""
    return {
        "id": s.get("id"),
        "name": s.get("nom", ""),
        "type": s.get("types", []),
        "theme": s.get("thematiques", []),
        "structure_id": s.get("structure_id", ""),
        "description": s.get("presentation_detail") or s.get("presentation_resume", ""),
        "frais": s.get("frais", []),
        "modes_accueil": s.get("modes_accueil", []),
    }


def extract_structures():
    """Extract and transform structures."""
    print("Loading structures from swiper...")
    raw = load_swiper_structures()
    print(f"  Loaded {len(raw)} structures")

    structures = [transform_structure(s) for s in raw]

    output_path = DATA_DIR / "structures.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(structures, f, ensure_ascii=False, indent=2)

    print(f"  Saved {len(structures)} structures to {output_path}")
    return structures


def extract_services():
    """Extract and transform services."""
    print("Loading services from swiper...")
    raw = load_swiper_services()
    print(f"  Loaded {len(raw)} services")

    services = [transform_service(s) for s in raw]

    output_path = DATA_DIR / "services.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(services, f, ensure_ascii=False, indent=2)

    print(f"  Saved {len(services)} services to {output_path}")
    return services


def identify_siaes(structures):
    """Identify SIAEs from structures list."""
    # SIAEs are from emplois-de-linclusion with /siae/ in lien_source
    siaes = [
        s for s in structures
        if s.get("source") == "emplois-de-linclusion"
        and "/siae/" in (s.get("lien_source") or "")
    ]

    # Take 5 diverse SIAEs (different types if possible)
    types_seen = set()
    selected = []
    for s in siaes:
        t = s.get("type", "")
        if t not in types_seen and len(selected) < 5:
            selected.append(s)
            types_seen.add(t)

    # Fill up to 5 if not enough diverse types
    if len(selected) < 5:
        for s in siaes:
            if s not in selected and len(selected) < 5:
                selected.append(s)

    output_path = DATA_DIR / "siaes.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)

    print(f"  Identified {len(siaes)} SIAEs total, selected 5:")
    for s in selected:
        print(f"    - {s['name']} ({s['type']})")

    return selected


if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    structures = extract_structures()
    services = extract_services()
    identify_siaes(structures)
    print("\nDone!")
