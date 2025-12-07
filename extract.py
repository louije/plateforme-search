#!/usr/bin/env python3
"""
Extract structures and services from data-inclusion dataset.
Uses local swiper data if available, otherwise downloads from data.gouv.fr.
"""

import json
import re
import requests
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
SWIPER_DATA = Path(__file__).parent.parent / "swiper" / "data"

# data.gouv.fr dataset ID for data-inclusion
DATASET_ID = "6233723c2c1e4a54af2f6b2d"
DATASET_API_URL = f"https://www.data.gouv.fr/api/1/datasets/{DATASET_ID}/"


def find_resource_url(dataset, pattern):
    """Find a resource URL by matching title against a regex pattern."""
    for resource in dataset.get("resources", []):
        if re.match(pattern, resource.get("title", "")):
            return resource.get("url")
    raise ValueError(f"No resource found matching pattern: {pattern}")


def get_resource_urls():
    """Fetch dataset metadata and extract resource URLs dynamically."""
    print("Fetching dataset metadata from data.gouv.fr...")
    response = requests.get(DATASET_API_URL)
    response.raise_for_status()
    dataset = response.json()

    structures_url = find_resource_url(dataset, r"^structures-inclusion.*\.json$")
    services_url = find_resource_url(dataset, r"^services-inclusion.*\.json$")

    return structures_url, services_url


def download_json(url, description):
    """Download JSON from URL with progress indication."""
    print(f"Downloading {description}...")
    # Long timeout: 30s connect, 5min read (for large files)
    response = requests.get(url, timeout=(30, 300))
    response.raise_for_status()
    print(f"  Size: {len(response.content) / 1024 / 1024:.1f} MB")
    return response.json()


def get_data_source():
    """Check if swiper data exists, return source type and URLs if needed."""
    swiper_structures = SWIPER_DATA / "structures.json"
    swiper_services = SWIPER_DATA / "services.json"

    if swiper_structures.exists() and swiper_services.exists():
        return "swiper", None, None

    structures_url, services_url = get_resource_urls()
    return "download", structures_url, services_url


def load_structures_raw(source, url=None):
    """Load raw structures data."""
    if source == "swiper":
        with open(SWIPER_DATA / "structures.json", encoding="utf-8") as f:
            return json.load(f)
    return download_json(url, "structures (~80MB)")


def load_services_raw(source, url=None):
    """Load raw services data."""
    if source == "swiper":
        with open(SWIPER_DATA / "services.json", encoding="utf-8") as f:
            return json.load(f)
    return download_json(url, "services (~175MB)")


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


def save_structures(raw_structures):
    """Transform and save structures."""
    structures = [transform_structure(s) for s in raw_structures]
    output_path = DATA_DIR / "structures.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(structures, f, ensure_ascii=False)
    return structures


def save_services(raw_services):
    """Transform and save services."""
    services = [transform_service(s) for s in raw_services]
    output_path = DATA_DIR / "services.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(services, f, ensure_ascii=False)
    return services


def extract_all():
    """Extract and transform structures and services."""
    source, structures_url, services_url = get_data_source()

    raw_structures = load_structures_raw(source, structures_url)
    print(f"  Loaded {len(raw_structures)} structures")
    structures = save_structures(raw_structures)

    raw_services = load_services_raw(source, services_url)
    print(f"  Loaded {len(raw_services)} services")
    services = save_services(raw_services)

    return structures, services


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
    structures, services = extract_all()
    identify_siaes(structures)
    print("\nDone!")
