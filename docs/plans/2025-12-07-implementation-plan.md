# Universal Search Prototype - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a universal search prototype with Flask + Meilisearch + HTMX that searches across users, structures, and services.

**Architecture:** Single Flask app with HTMX for real-time autocomplete. Meilisearch handles multi-index search. Data extracted from data.gouv.fr API, fake users generated with Faker.

**Tech Stack:** Flask, Meilisearch, HTMX, Docker Compose, Python Faker

---

## Task 1: Project Setup - Docker & Dependencies

**Files:**
- Create: `docker-compose.yml`
- Create: `Dockerfile`
- Create: `requirements.txt`
- Create: `config.py`

**Step 1: Create docker-compose.yml**

```yaml
services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - .:/app
    depends_on:
      - search
    environment:
      - FLASK_DEBUG=1
      - MEILISEARCH_URL=http://search:7700
      - MEILISEARCH_KEY=masterKey

  search:
    image: getmeili/meilisearch:v1.6
    ports:
      - "7700:7700"
    volumes:
      - meili_data:/meili_data
    environment:
      - MEILI_MASTER_KEY=masterKey

volumes:
  meili_data:
```

**Step 2: Create Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["flask", "run", "--host=0.0.0.0"]
```

**Step 3: Create requirements.txt**

```
flask==3.0.0
meilisearch==0.31.0
python-dotenv==1.0.0
requests==2.31.0
faker==22.0.0
```

**Step 4: Create config.py**

```python
import os

CONFIG = {
    "MEILISEARCH_URL": os.getenv("MEILISEARCH_URL", "http://localhost:7700"),
    "MEILISEARCH_KEY": os.getenv("MEILISEARCH_KEY", "masterKey"),
    "AUTOCOMPLETE_LIMIT": int(os.getenv("AUTOCOMPLETE_LIMIT", "3")),
    "FILTERED_LIMIT": int(os.getenv("FILTERED_LIMIT", "10")),
    "RESULTS_PAGE_LIMIT": int(os.getenv("RESULTS_PAGE_LIMIT", "20")),
}
```

**Step 5: Verify Docker setup**

Run: `docker compose up -d search`
Expected: Meilisearch running at http://localhost:7700

**Step 6: Commit**

```bash
git add docker-compose.yml Dockerfile requirements.txt config.py
git commit -m "Add Docker and project configuration"
```

---

## Task 2: Data Extraction Script

**Files:**
- Create: `extract.py`
- Create: `data/.gitkeep`

**Step 1: Create data directory**

```bash
mkdir -p data
touch data/.gitkeep
```

**Step 2: Create extract.py**

```python
#!/usr/bin/env python3
"""
Extract structures and services from data.gouv.fr data-inclusion API.
Downloads the consolidated dataset and saves to data/ directory.
"""

import json
import requests
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
STRUCTURES_URL = "https://www.data.gouv.fr/fr/datasets/r/5c69ef8e-04f3-4a8a-b1b5-c6e4d7e5b987"
SERVICES_URL = "https://www.data.gouv.fr/fr/datasets/r/8f0e0e7a-3c3b-4b1e-9c5d-1e9f0e0e7a3c"

# Alternative: use the API directly
API_BASE = "https://api.data.inclusion.beta.gouv.fr/api/v0"


def download_structures():
    """Download structures from data-inclusion API."""
    print("Downloading structures...")

    structures = []
    url = f"{API_BASE}/structures"
    params = {"size": 1000}

    while url:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        structures.extend(data.get("items", []))

        # Handle pagination
        next_page = data.get("next")
        if next_page and len(structures) < 5000:  # Limit for prototype
            url = next_page
            params = {}  # Next URL includes params
        else:
            url = None

        print(f"  Downloaded {len(structures)} structures...")

    output_path = DATA_DIR / "structures.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(structures, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(structures)} structures to {output_path}")
    return structures


def download_services():
    """Download services from data-inclusion API."""
    print("Downloading services...")

    services = []
    url = f"{API_BASE}/services"
    params = {"size": 1000}

    while url:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        services.extend(data.get("items", []))

        next_page = data.get("next")
        if next_page and len(services) < 10000:  # Limit for prototype
            url = next_page
            params = {}
        else:
            url = None

        print(f"  Downloaded {len(services)} services...")

    output_path = DATA_DIR / "services.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(services, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(services)} services to {output_path}")
    return services


def identify_siaes(structures):
    """Identify SIAEs from structures list."""
    siaes = [
        s for s in structures
        if s.get("source") == "emplois-de-linclusion"
        and s.get("lien_source", "").startswith("https://emplois.inclusion.beta.gouv.fr/company/")
    ]

    output_path = DATA_DIR / "siaes.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(siaes[:5], f, ensure_ascii=False, indent=2)  # Only first 5 for prototype

    print(f"Identified {len(siaes)} SIAEs, saved 5 to {output_path}")
    return siaes[:5]


if __name__ == "__main__":
    DATA_DIR.mkdir(exist_ok=True)
    structures = download_structures()
    services = download_services()
    identify_siaes(structures)
    print("Done!")
```

**Step 3: Test extraction script**

Run: `python extract.py`
Expected: Files created in data/ directory

**Step 4: Commit**

```bash
git add extract.py data/.gitkeep
git commit -m "Add data extraction script"
```

---

## Task 3: User Generation Script

**Files:**
- Create: `generate_users.py`

**Step 1: Create generate_users.py**

```python
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
    now = datetime.now()
    start_date = fake.date_between(start_date="-2y", end_date="today")
    creation_date = start_date - timedelta(days=random.randint(1, 30))

    return {
        "id": f"user_{user_id:03d}",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "is_professional": is_professional,
        "structure_id": structure.get("id", structure.get("_id")),
        "structure_name": structure.get("nom", structure.get("name", "Unknown")),
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

    print(f"Generated {len(users)} users ({sum(1 for u in users if u['is_professional'])} professionals)")
    print(f"Saved to {output_path}")
    return users


if __name__ == "__main__":
    generate_all_users()
```

**Step 2: Test user generation**

Run: `python generate_users.py`
Expected: data/users.json created with 100 users

**Step 3: Commit**

```bash
git add generate_users.py
git commit -m "Add user generation script"
```

---

## Task 4: Meilisearch Indexing Script

**Files:**
- Create: `index.py`

**Step 1: Create index.py**

```python
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

    # Add documents
    task = index.add_documents(users)
    client.wait_for_task(task.task_uid)

    print(f"  Indexed {len(users)} users")


def index_structures(client):
    """Index structures with appropriate settings."""
    print("Indexing structures...")
    structures = load_json("structures.json")

    # Transform to our schema
    docs = []
    for s in structures:
        doc = {
            "id": s.get("id", s.get("_id")),
            "name": s.get("nom", s.get("name", "")),
            "type": s.get("typologie", s.get("type", "")),
            "address": s.get("adresse", ""),
            "commune": s.get("commune", ""),
            "code_postal": s.get("code_postal", ""),
            "latitude": s.get("latitude"),
            "longitude": s.get("longitude"),
            "description": s.get("presentation_detail", s.get("presentation_resume", "")),
            "source": s.get("source", ""),
            "lien_source": s.get("lien_source", ""),
        }
        docs.append(doc)

    index = client.index("structures")

    index.update_settings({
        "searchableAttributes": ["name", "description", "commune"],
        "filterableAttributes": ["type", "source", "code_postal"],
        "sortableAttributes": ["name"],
    })

    # Add in batches
    batch_size = 1000
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        task = index.add_documents(batch)
        client.wait_for_task(task.task_uid)
        print(f"  Indexed {min(i + batch_size, len(docs))}/{len(docs)} structures")

    print(f"  Total: {len(docs)} structures indexed")


def index_services(client):
    """Index services with appropriate settings."""
    print("Indexing services...")
    services = load_json("services.json")

    # Transform to our schema
    docs = []
    for s in services:
        doc = {
            "id": s.get("id", s.get("_id")),
            "name": s.get("nom", s.get("name", "")),
            "type": s.get("types", []),
            "theme": s.get("thematiques", []),
            "structure_id": s.get("structure_id", ""),
            "description": s.get("presentation_detail", s.get("presentation_resume", "")),
        }
        docs.append(doc)

    index = client.index("services")

    index.update_settings({
        "searchableAttributes": ["name", "description"],
        "filterableAttributes": ["type", "theme", "structure_id"],
        "sortableAttributes": ["name"],
    })

    # Add in batches
    batch_size = 1000
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        task = index.add_documents(batch)
        client.wait_for_task(task.task_uid)
        print(f"  Indexed {min(i + batch_size, len(docs))}/{len(docs)} services")

    print(f"  Total: {len(docs)} services indexed")


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
    print("Done!")
```

**Step 2: Test indexing (requires Meilisearch running)**

Run: `docker compose up -d search && sleep 3 && python index.py`
Expected: All indexes created with data

**Step 3: Commit**

```bash
git add index.py
git commit -m "Add Meilisearch indexing script"
```

---

## Task 5: Flask App - Core Setup

**Files:**
- Create: `app.py`
- Create: `templates/base.html`

**Step 1: Create app.py with basic structure**

```python
#!/usr/bin/env python3
"""
Universal Search Flask Application.
"""

from flask import Flask, render_template, request, session, redirect, url_for
import meilisearch
from config import CONFIG

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-prod"


def get_search_client():
    """Get Meilisearch client."""
    return meilisearch.Client(
        CONFIG["MEILISEARCH_URL"],
        CONFIG["MEILISEARCH_KEY"]
    )


def get_current_context():
    """Get current user context from session."""
    return {
        "structure_id": session.get("structure_id"),
        "structure_name": session.get("structure_name", "Toutes structures"),
        "user_name": session.get("user_name", "Anonyme"),
    }


@app.route("/")
def index():
    """Main search page."""
    context = get_current_context()

    # Get available structures for context selector
    client = get_search_client()
    try:
        result = client.index("structures").search("", {"limit": 100})
        structures = result.get("hits", [])
    except Exception:
        structures = []

    return render_template(
        "search.html",
        context=context,
        structures=structures,
        config=CONFIG,
    )


@app.route("/search")
def search():
    """HTMX endpoint for autocomplete search."""
    query = request.args.get("q", "").strip()
    type_filter = request.args.get("type", "")
    context = get_current_context()

    if not query:
        return render_template("partials/dropdown.html", results=None)

    client = get_search_client()
    limit = CONFIG["FILTERED_LIMIT"] if type_filter else CONFIG["AUTOCOMPLETE_LIMIT"]

    # Build multi-search queries
    queries = []

    if not type_filter or type_filter == "users":
        user_query = {
            "indexUid": "users",
            "q": query,
            "limit": limit,
            "attributesToHighlight": ["first_name", "last_name"],
        }
        # Filter by structure if context set
        if context["structure_id"]:
            user_query["filter"] = f'structure_id = "{context["structure_id"]}"'
        queries.append(user_query)

    if not type_filter or type_filter == "structures":
        queries.append({
            "indexUid": "structures",
            "q": query,
            "limit": limit,
            "attributesToHighlight": ["name"],
        })

    if not type_filter or type_filter == "services":
        queries.append({
            "indexUid": "services",
            "q": query,
            "limit": limit,
            "attributesToHighlight": ["name"],
        })

    # Execute multi-search
    response = client.multi_search(queries)

    # Organize results by type
    results = {
        "users": {"hits": [], "estimatedTotalHits": 0},
        "structures": {"hits": [], "estimatedTotalHits": 0},
        "services": {"hits": [], "estimatedTotalHits": 0},
    }

    for r in response.get("results", []):
        index_uid = r.get("indexUid")
        if index_uid in results:
            results[index_uid] = {
                "hits": r.get("hits", []),
                "estimatedTotalHits": r.get("estimatedTotalHits", 0),
            }

    return render_template(
        "partials/dropdown.html",
        results=results,
        query=query,
        type_filter=type_filter,
        limit=limit,
    )


@app.route("/results")
def results():
    """Full results page with pagination."""
    query = request.args.get("q", "").strip()
    type_filter = request.args.get("type", "")
    page = int(request.args.get("page", 1))
    context = get_current_context()

    if not query:
        return redirect(url_for("index"))

    client = get_search_client()
    limit = CONFIG["RESULTS_PAGE_LIMIT"]
    offset = (page - 1) * limit

    # Determine which index to search
    index_name = type_filter if type_filter in ["users", "structures", "services"] else "structures"

    search_params = {
        "limit": limit,
        "offset": offset,
        "attributesToHighlight": ["*"],
    }

    # Apply structure filter for users
    if index_name == "users" and context["structure_id"]:
        search_params["filter"] = f'structure_id = "{context["structure_id"]}"'

    result = client.index(index_name).search(query, search_params)

    total = result.get("estimatedTotalHits", 0)
    total_pages = (total + limit - 1) // limit

    return render_template(
        "results.html",
        hits=result.get("hits", []),
        query=query,
        type_filter=type_filter,
        page=page,
        total=total,
        total_pages=total_pages,
        context=context,
    )


@app.route("/users/<id>")
def user_detail(id):
    """User detail page."""
    client = get_search_client()
    try:
        user = client.index("users").get_document(id)
    except Exception:
        return "User not found", 404

    return render_template("detail.html", entity=user, entity_type="user")


@app.route("/structures/<id>")
def structure_detail(id):
    """Structure detail page."""
    client = get_search_client()
    try:
        structure = client.index("structures").get_document(id)
    except Exception:
        return "Structure not found", 404

    return render_template("detail.html", entity=structure, entity_type="structure")


@app.route("/services/<id>")
def service_detail(id):
    """Service detail page."""
    client = get_search_client()
    try:
        service = client.index("services").get_document(id)
    except Exception:
        return "Service not found", 404

    return render_template("detail.html", entity=service, entity_type="service")


@app.route("/set-context")
def set_context():
    """Set user context (simulates login)."""
    structure_id = request.args.get("structure_id", "")
    structure_name = request.args.get("structure_name", "Toutes structures")
    user_name = request.args.get("user_name", "Anonyme")

    if structure_id:
        session["structure_id"] = structure_id
        session["structure_name"] = structure_name
        session["user_name"] = user_name
    else:
        session.pop("structure_id", None)
        session.pop("structure_name", None)
        session.pop("user_name", None)

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
```

**Step 2: Create templates/base.html**

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Recherche Universelle{% endblock %}</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <header>
        <h1><a href="{{ url_for('index') }}">Recherche Universelle</a></h1>
        <div class="context-info">
            Connecté: {{ context.user_name }} ({{ context.structure_name }})
        </div>
    </header>

    <main>
        {% block content %}{% endblock %}
    </main>

    <footer>
        <p>Prototype - Data Inclusion</p>
    </footer>
</body>
</html>
```

**Step 3: Commit**

```bash
mkdir -p templates static
git add app.py templates/base.html
git commit -m "Add Flask app core structure"
```

---

## Task 6: Templates - Search Page & Dropdown

**Files:**
- Create: `templates/search.html`
- Create: `templates/partials/dropdown.html`

**Step 1: Create templates/search.html**

```html
{% extends "base.html" %}

{% block content %}
<div class="search-container">
    <!-- Context selector -->
    <div class="context-selector">
        <label for="context">Vue:</label>
        <select id="context" onchange="setContext(this)">
            <option value="">Toutes structures</option>
            {% for s in structures %}
            <option value="{{ s.id }}"
                    data-name="{{ s.name }}"
                    {% if context.structure_id == s.id %}selected{% endif %}>
                {{ s.name }}
            </option>
            {% endfor %}
        </select>
    </div>

    <!-- Search input -->
    <div class="search-box">
        <input type="search"
               id="search-input"
               name="q"
               placeholder="Rechercher..."
               autocomplete="off"
               hx-get="{{ url_for('search') }}"
               hx-trigger="input changed delay:300ms, search"
               hx-target="#dropdown"
               hx-include="#type-filter">
    </div>

    <!-- Type filter -->
    <div id="type-filter" class="type-filter">
        <label>
            <input type="radio" name="type" value="" checked
                   hx-get="{{ url_for('search') }}"
                   hx-trigger="change"
                   hx-target="#dropdown"
                   hx-include="#search-input">
            Tous
        </label>
        <label>
            <input type="radio" name="type" value="users"
                   hx-get="{{ url_for('search') }}"
                   hx-trigger="change"
                   hx-target="#dropdown"
                   hx-include="#search-input">
            Utilisateurs
        </label>
        <label>
            <input type="radio" name="type" value="structures"
                   hx-get="{{ url_for('search') }}"
                   hx-trigger="change"
                   hx-target="#dropdown"
                   hx-include="#search-input">
            Structures
        </label>
        <label>
            <input type="radio" name="type" value="services"
                   hx-get="{{ url_for('search') }}"
                   hx-trigger="change"
                   hx-target="#dropdown"
                   hx-include="#search-input">
            Services
        </label>
    </div>

    <!-- Results dropdown -->
    <div id="dropdown" class="dropdown"></div>
</div>

<script>
function setContext(select) {
    const option = select.options[select.selectedIndex];
    const structureId = option.value;
    const structureName = option.dataset.name || 'Toutes structures';

    const url = new URL('{{ url_for("set_context") }}', window.location.origin);
    url.searchParams.set('structure_id', structureId);
    url.searchParams.set('structure_name', structureName);

    window.location.href = url.toString();
}
</script>
{% endblock %}
```

**Step 2: Create templates/partials/dropdown.html**

```html
{% if results %}
<div class="dropdown-content">
    {% if results.users.hits %}
    <div class="result-group">
        <div class="group-label">Utilisateurs</div>
        <div class="group-results">
            {% for hit in results.users.hits %}
            <a href="{{ url_for('user_detail', id=hit.id) }}" class="result-item">
                <span class="result-name">
                    {{ hit._formatted.first_name | safe }} {{ hit._formatted.last_name | safe }}
                </span>
                <span class="result-meta">{{ hit.structure_name }}</span>
            </a>
            {% endfor %}
            {% if results.users.estimatedTotalHits > limit %}
            <a href="{{ url_for('results', q=query, type='users') }}" class="show-all">
                → voir tous ({{ results.users.estimatedTotalHits }})
            </a>
            {% endif %}
        </div>
    </div>
    {% endif %}

    {% if results.structures.hits %}
    <div class="result-group">
        <div class="group-label">Structures</div>
        <div class="group-results">
            {% for hit in results.structures.hits %}
            <a href="{{ url_for('structure_detail', id=hit.id) }}" class="result-item">
                <span class="result-name">{{ hit._formatted.name | safe }}</span>
                <span class="result-meta">{{ hit.type }} - {{ hit.commune }}</span>
            </a>
            {% endfor %}
            {% if results.structures.estimatedTotalHits > limit %}
            <a href="{{ url_for('results', q=query, type='structures') }}" class="show-all">
                → voir tous ({{ results.structures.estimatedTotalHits }})
            </a>
            {% endif %}
        </div>
    </div>
    {% endif %}

    {% if results.services.hits %}
    <div class="result-group">
        <div class="group-label">Services</div>
        <div class="group-results">
            {% for hit in results.services.hits %}
            <a href="{{ url_for('service_detail', id=hit.id) }}" class="result-item">
                <span class="result-name">{{ hit._formatted.name | safe }}</span>
                <span class="result-meta">{{ hit.theme | join(', ') if hit.theme is iterable and hit.theme is not string else hit.theme }}</span>
            </a>
            {% endfor %}
            {% if results.services.estimatedTotalHits > limit %}
            <a href="{{ url_for('results', q=query, type='services') }}" class="show-all">
                → voir tous ({{ results.services.estimatedTotalHits }})
            </a>
            {% endif %}
        </div>
    </div>
    {% endif %}

    {% if not results.users.hits and not results.structures.hits and not results.services.hits %}
    <div class="no-results">Aucun résultat pour "{{ query }}"</div>
    {% endif %}
</div>
{% endif %}
```

**Step 3: Commit**

```bash
mkdir -p templates/partials
git add templates/search.html templates/partials/dropdown.html
git commit -m "Add search page and dropdown templates"
```

---

## Task 7: Templates - Results & Detail Pages

**Files:**
- Create: `templates/results.html`
- Create: `templates/detail.html`

**Step 1: Create templates/results.html**

```html
{% extends "base.html" %}

{% block title %}Résultats: {{ query }}{% endblock %}

{% block content %}
<div class="results-page">
    <div class="results-header">
        <a href="{{ url_for('index') }}" class="back-link">← Retour</a>
        <h2>Résultats pour "{{ query }}"</h2>
        <p>{{ total }} résultat(s) - {{ type_filter or 'tous types' }}</p>
    </div>

    <div class="results-list">
        {% for hit in hits %}
        <div class="result-card">
            {% if type_filter == 'users' %}
            <a href="{{ url_for('user_detail', id=hit.id) }}">
                <h3>{{ hit._formatted.first_name | safe }} {{ hit._formatted.last_name | safe }}</h3>
                <p>{{ hit.structure_name }}</p>
                <p class="meta">
                    {% if hit.is_professional %}Professionnel{% else %}Bénéficiaire{% endif %}
                    - Depuis {{ hit.start_date }}
                </p>
            </a>
            {% elif type_filter == 'services' %}
            <a href="{{ url_for('service_detail', id=hit.id) }}">
                <h3>{{ hit._formatted.name | safe }}</h3>
                <p>{{ hit.description[:200] }}...</p>
                <p class="meta">{{ hit.theme | join(', ') if hit.theme is iterable and hit.theme is not string else hit.theme }}</p>
            </a>
            {% else %}
            <a href="{{ url_for('structure_detail', id=hit.id) }}">
                <h3>{{ hit._formatted.name | safe }}</h3>
                <p>{{ hit.description[:200] if hit.description else '' }}...</p>
                <p class="meta">{{ hit.type }} - {{ hit.commune }}</p>
            </a>
            {% endif %}
        </div>
        {% endfor %}
    </div>

    {% if total_pages > 1 %}
    <div class="pagination">
        {% if page > 1 %}
        <a href="{{ url_for('results', q=query, type=type_filter, page=page-1) }}">← Précédent</a>
        {% endif %}

        <span>Page {{ page }} / {{ total_pages }}</span>

        {% if page < total_pages %}
        <a href="{{ url_for('results', q=query, type=type_filter, page=page+1) }}">Suivant →</a>
        {% endif %}
    </div>
    {% endif %}
</div>
{% endblock %}
```

**Step 2: Create templates/detail.html**

```html
{% extends "base.html" %}

{% block title %}{{ entity.name or (entity.first_name ~ ' ' ~ entity.last_name) }}{% endblock %}

{% block content %}
<div class="detail-page">
    <a href="{{ url_for('index') }}" class="back-link">← Retour à la recherche</a>

    {% if entity_type == 'user' %}
    <div class="entity-card">
        <h2>{{ entity.first_name }} {{ entity.last_name }}</h2>
        <dl>
            <dt>Structure</dt>
            <dd>{{ entity.structure_name }}</dd>

            <dt>Type</dt>
            <dd>{% if entity.is_professional %}Professionnel{% else %}Bénéficiaire{% endif %}</dd>

            <dt>Date de début</dt>
            <dd>{{ entity.start_date }}</dd>

            <dt>Date de création</dt>
            <dd>{{ entity.creation_date }}</dd>
        </dl>
    </div>

    {% elif entity_type == 'structure' %}
    <div class="entity-card">
        <h2>{{ entity.name }}</h2>
        <dl>
            <dt>Type</dt>
            <dd>{{ entity.type }}</dd>

            <dt>Adresse</dt>
            <dd>{{ entity.address }}, {{ entity.code_postal }} {{ entity.commune }}</dd>

            <dt>Description</dt>
            <dd>{{ entity.description }}</dd>

            {% if entity.lien_source %}
            <dt>Source</dt>
            <dd><a href="{{ entity.lien_source }}" target="_blank">{{ entity.source }}</a></dd>
            {% endif %}
        </dl>
    </div>

    {% elif entity_type == 'service' %}
    <div class="entity-card">
        <h2>{{ entity.name }}</h2>
        <dl>
            <dt>Type</dt>
            <dd>{{ entity.type | join(', ') if entity.type is iterable and entity.type is not string else entity.type }}</dd>

            <dt>Thème</dt>
            <dd>{{ entity.theme | join(', ') if entity.theme is iterable and entity.theme is not string else entity.theme }}</dd>

            <dt>Description</dt>
            <dd>{{ entity.description }}</dd>
        </dl>
    </div>
    {% endif %}
</div>
{% endblock %}
```

**Step 3: Commit**

```bash
git add templates/results.html templates/detail.html
git commit -m "Add results and detail page templates"
```

---

## Task 8: CSS Styling

**Files:**
- Create: `static/style.css`

**Step 1: Create static/style.css**

```css
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
}

header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px solid #eee;
}

header h1 a {
    text-decoration: none;
    color: #2563eb;
}

.context-info {
    font-size: 0.9em;
    color: #666;
}

/* Search Container */
.search-container {
    max-width: 600px;
    margin: 0 auto;
}

.context-selector {
    margin-bottom: 20px;
}

.context-selector select {
    padding: 8px 12px;
    font-size: 1em;
    border: 1px solid #ddd;
    border-radius: 4px;
    width: 100%;
}

.search-box input {
    width: 100%;
    padding: 15px 20px;
    font-size: 1.2em;
    border: 2px solid #2563eb;
    border-radius: 8px;
    outline: none;
}

.search-box input:focus {
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
}

/* Type Filter */
.type-filter {
    display: flex;
    gap: 15px;
    margin: 15px 0;
    flex-wrap: wrap;
}

.type-filter label {
    display: flex;
    align-items: center;
    gap: 5px;
    cursor: pointer;
    padding: 5px 10px;
    border-radius: 4px;
    transition: background 0.2s;
}

.type-filter label:hover {
    background: #f0f0f0;
}

/* Dropdown */
.dropdown {
    position: relative;
    margin-top: 5px;
}

.dropdown-content {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    overflow: hidden;
}

.result-group {
    display: flex;
    border-bottom: 1px solid #eee;
}

.result-group:last-child {
    border-bottom: none;
}

.group-label {
    width: 120px;
    padding: 15px;
    background: #f8f9fa;
    font-weight: 600;
    color: #666;
    flex-shrink: 0;
}

.group-results {
    flex: 1;
    padding: 10px 0;
}

.result-item {
    display: block;
    padding: 8px 15px;
    text-decoration: none;
    color: inherit;
    transition: background 0.2s;
}

.result-item:hover {
    background: #f0f7ff;
}

.result-name {
    display: block;
    font-weight: 500;
}

.result-name em {
    background: #fef08a;
    font-style: normal;
}

.result-meta {
    font-size: 0.85em;
    color: #666;
}

.show-all {
    display: block;
    padding: 8px 15px;
    color: #2563eb;
    text-decoration: none;
    font-size: 0.9em;
}

.show-all:hover {
    text-decoration: underline;
}

.no-results {
    padding: 20px;
    text-align: center;
    color: #666;
}

/* Results Page */
.results-page {
    max-width: 800px;
}

.results-header {
    margin-bottom: 20px;
}

.back-link {
    color: #2563eb;
    text-decoration: none;
    display: inline-block;
    margin-bottom: 10px;
}

.back-link:hover {
    text-decoration: underline;
}

.result-card {
    padding: 15px;
    border: 1px solid #eee;
    border-radius: 8px;
    margin-bottom: 10px;
    transition: box-shadow 0.2s;
}

.result-card:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.result-card a {
    text-decoration: none;
    color: inherit;
}

.result-card h3 {
    color: #2563eb;
    margin-bottom: 5px;
}

.result-card h3 em {
    background: #fef08a;
    font-style: normal;
}

.result-card .meta {
    font-size: 0.85em;
    color: #666;
    margin-top: 5px;
}

.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
    margin-top: 30px;
    padding: 20px;
}

.pagination a {
    color: #2563eb;
    text-decoration: none;
}

/* Detail Page */
.entity-card {
    background: #f8f9fa;
    padding: 30px;
    border-radius: 8px;
    margin-top: 20px;
}

.entity-card h2 {
    margin-bottom: 20px;
    color: #1e40af;
}

.entity-card dl {
    display: grid;
    grid-template-columns: 150px 1fr;
    gap: 10px;
}

.entity-card dt {
    font-weight: 600;
    color: #666;
}

.entity-card dd {
    margin: 0;
}

.entity-card a {
    color: #2563eb;
}

/* Footer */
footer {
    margin-top: 50px;
    padding-top: 20px;
    border-top: 1px solid #eee;
    text-align: center;
    color: #666;
    font-size: 0.9em;
}
```

**Step 2: Commit**

```bash
git add static/style.css
git commit -m "Add CSS styling"
```

---

## Task 9: Integration Test - Full Stack

**Step 1: Start all services**

```bash
docker compose up -d
```

**Step 2: Run data pipeline**

```bash
docker compose exec web python extract.py
docker compose exec web python generate_users.py
docker compose exec web python index.py
```

**Step 3: Verify search works**

Open http://localhost:5000 and:
1. Type a search query
2. Verify dropdown appears with results
3. Click "voir tous" to see full results
4. Click a result to see detail page
5. Change context selector and verify user filtering

**Step 4: Final commit**

```bash
git add .gitignore CLAUDE.md
git commit -m "Add project configuration files"
```

---

## Summary

**Total tasks:** 9

**Files created:**
- `docker-compose.yml` - Docker services
- `Dockerfile` - Flask container
- `requirements.txt` - Python dependencies
- `config.py` - Configurable settings
- `extract.py` - Data extraction
- `generate_users.py` - Fake user generation
- `index.py` - Meilisearch indexing
- `app.py` - Flask application
- `templates/base.html` - Base template
- `templates/search.html` - Search page
- `templates/partials/dropdown.html` - Autocomplete dropdown
- `templates/results.html` - Full results page
- `templates/detail.html` - Entity detail page
- `static/style.css` - Styling

**To run:**
```bash
docker compose up -d
python extract.py && python generate_users.py && python index.py
# Open http://localhost:5000
```
