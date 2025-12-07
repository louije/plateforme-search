#!/usr/bin/env python3
"""
Extract structures and services from data-inclusion dataset.
Uses local swiper data if available, otherwise downloads from data.gouv.fr.
"""

import json
import requests
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
SWIPER_DATA = Path(__file__).parent.parent / "swiper" / "data"

# data.gouv.fr dataset URLs (consolidated data-inclusion)
STRUCTURES_URL = "https://www.data.gouv.fr/fr/datasets/r/8f9e4bdb-cf77-4d33-b75e-b2a2057c5e26"
SERVICES_URL = "https://www.data.gouv.fr/fr/datasets/r/d6a05d0c-124c-4846-b016-613a0593cbb1"


def download_json(url, description):
    """Download JSON from URL with progress indication."""
    print(f"Downloading {description}...")
    response = requests.get(url, stream=True)
    response.raise_for_status()

    # Get content length if available
    total = response.headers.get('content-length')
    if total:
        total = int(total)
        print(f"  Size: {total / 1024 / 1024:.1f} MB")

    content = response.content
    return json.loads(content)


def load_or_download_structures():
    """Load structures from swiper or download from data.gouv.fr."""
    swiper_path = SWIPER_DATA / "structures.json"

    if swiper_path.exists():
        print("Loading structures from swiper...")
        with open(swiper_path, encoding="utf-8") as f:
            return json.load(f)
    else:
        print("Swiper data not found, downloading from data.gouv.fr...")
        return download_json(STRUCTURES_URL, "structures")


def load_or_download_services():
    """Load services from swiper or download from data.gouv.fr."""
    swiper_path = SWIPER_DATA / "services.json"

    if swiper_path.exists():
        print("Loading services from swiper...")
        with open(swiper_path, encoding="utf-8") as f:
            return json.load(f)
    else:
        print("Swiper data not found, downloading from data.gouv.fr...")
        return download_json(SERVICES_URL, "services")


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
    raw = load_or_download_structures()
    print(f"  Loaded {len(raw)} structures")

    structures = [transform_structure(s) for s in raw]

    output_path = DATA_DIR / "structures.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(structures, f, ensure_ascii=False)

    print(f"  Saved {len(structures)} structures to {output_path}")
    return structures


def extract_services():
    """Extract and transform services."""
    raw = load_or_download_services()
    print(f"  Loaded {len(raw)} services")

    services = [transform_service(s) for s in raw]

    output_path = DATA_DIR / "services.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(services, f, ensure_ascii=False)

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
