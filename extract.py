#!/usr/bin/env python3
"""
Extract structures and services from data-inclusion dataset.
Uses cached data if fresh, swiper data if available, otherwise downloads from data.gouv.fr.
"""

import json
import re
import time
import requests
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
SWIPER_DATA = Path(__file__).parent.parent / "swiper" / "data"
CACHE_MAX_AGE_DAYS = 5

# data.gouv.fr dataset ID for data-inclusion
DATASET_ID = "6233723c2c1e4a54af2f6b2d"
DATASET_API_URL = f"https://www.data.gouv.fr/api/1/datasets/{DATASET_ID}/"


def is_cache_fresh(filepath, max_age_days=CACHE_MAX_AGE_DAYS):
    """Check if a cached file exists and is less than max_age_days old."""
    if not filepath.exists():
        return False
    age_seconds = time.time() - filepath.stat().st_mtime
    age_days = age_seconds / (24 * 3600)
    return age_days < max_age_days


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
    """Check data source: cache (if fresh), swiper, or download."""
    cached_structures = DATA_DIR / "structures_raw.json"
    cached_services = DATA_DIR / "services_raw.json"

    # Check for fresh cache first
    if is_cache_fresh(cached_structures) and is_cache_fresh(cached_services):
        return "cache", None, None

    # Check for swiper data
    swiper_structures = SWIPER_DATA / "structures.json"
    swiper_services = SWIPER_DATA / "services.json"
    if swiper_structures.exists() and swiper_services.exists():
        return "swiper", None, None

    # Need to download
    structures_url, services_url = get_resource_urls()
    return "download", structures_url, services_url


def load_structures_raw(source, url=None):
    """Load raw structures data."""
    cached = DATA_DIR / "structures_raw.json"

    if source == "cache":
        print(f"  Using cached structures ({(time.time() - cached.stat().st_mtime) / 3600:.1f}h old)")
        with open(cached, encoding="utf-8") as f:
            return json.load(f)

    if source == "swiper":
        with open(SWIPER_DATA / "structures.json", encoding="utf-8") as f:
            return json.load(f)

    # Download and cache
    data = download_json(url, "structures (~80MB)")
    with open(cached, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return data


def load_services_raw(source, url=None):
    """Load raw services data."""
    cached = DATA_DIR / "services_raw.json"

    if source == "cache":
        print(f"  Using cached services ({(time.time() - cached.stat().st_mtime) / 3600:.1f}h old)")
        with open(cached, encoding="utf-8") as f:
            return json.load(f)

    if source == "swiper":
        with open(SWIPER_DATA / "services.json", encoding="utf-8") as f:
            return json.load(f)

    # Download and cache
    data = download_json(url, "services (~175MB)")
    with open(cached, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return data


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


HARDCODED_SIAES = [
    {"id": "00125c43-3d7b-411a-ac1d-b590d3ac782b", "name": "FLAMBOYANT PAYSAGE", "type": "EI", "commune": "Les TROIS-ILETS", "code_postal": "97229"},
    {"id": "0018e483-7c68-4f21-8eac-d87ce41b2730", "name": "Assoc agriservices castres", "type": "AI", "commune": "CASTRES", "code_postal": "81100"},
    {"id": "0058278a-f865-4284-8a4d-f269c42df52e", "name": "Association Maison Accueil Solidarité (M.A.S)", "type": "ACI", "commune": "Marconne", "code_postal": "62140"},
    {"id": "00e143c6-f807-4396-8a7c-1f5373326c59", "name": "Cooperative d'initiative jeunes", "type": "EITI", "commune": "Pointe-à-Pitre", "code_postal": "97110"},
    {"id": "010fd63c-d8c6-4d81-96ea-636584a44d71", "name": "G-eco", "type": "EA", "commune": "Cenon", "code_postal": "33150"},
]


def get_siaes():
    """Return hardcoded SIAEs list."""
    return HARDCODED_SIAES


if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    structures, services = extract_all()
    print(f"  Using {len(get_siaes())} hardcoded SIAEs")
    print("\nDone!")
