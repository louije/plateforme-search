# Universal Search Prototype - Design Document

## Overview

A universal search prototype enabling users to search across users, structures, and services through a single interface using Meilisearch.

**Stack:** Flask + Meilisearch + HTMX + Docker Compose

## Project Structure

```
plateforme-search/
├── app.py                    # Flask app, routes, search logic
├── config.py                 # Configuration (limits, Meilisearch URL, etc.)
├── extract.py                # Data extraction from data.gouv.fr
├── index.py                  # Meilisearch indexing script
├── generate_users.py         # Fake user generation
├── templates/
│   ├── base.html
│   ├── search.html           # Main search page with autocomplete
│   ├── partials/
│   │   └── dropdown.html     # Autocomplete dropdown partial
│   ├── results.html          # Full results page
│   └── detail.html           # Entity detail page
├── static/
│   └── style.css
├── docker-compose.yml        # Flask + Meilisearch services
├── Dockerfile
├── requirements.txt
└── CLAUDE.md
```

## Configuration

Configurable via environment variables or `config.py`:

```python
CONFIG = {
    "MEILISEARCH_URL": "http://search:7700",
    "MEILISEARCH_KEY": "masterKey",
    "AUTOCOMPLETE_LIMIT": 3,      # Results per type in dropdown
    "FILTERED_LIMIT": 10,         # Results when type filter active
    "RESULTS_PAGE_LIMIT": 20,     # Results per page on full results
}
```

## Routes

| Route | Method | Returns | Purpose |
|-------|--------|---------|---------|
| `/` | GET | HTML | Main search page |
| `/search` | GET | HTML partial | Autocomplete dropdown (HTMX) |
| `/results` | GET | HTML | Full results page with filters |
| `/users/<id>` | GET | HTML | User detail |
| `/structures/<id>` | GET | HTML | Structure detail |
| `/services/<id>` | GET | HTML | Service detail |
| `/set-context` | GET | redirect | Set user context (session) |

## HTMX Integration

**Search flow:**
1. User types in search input
2. `hx-get="/search?q=..."` fires after 300ms debounce
3. Server queries all 3 Meilisearch indexes via multi-search
4. Returns HTML partial with grouped results
5. HTMX swaps it into the dropdown container

**Type filtering:** Radio buttons include `hx-include` to send type param. When set, only that index is queried with higher limit.

## Data Models

### Users Index

```python
{
    "id": "user_001",
    "first_name": "Marie",
    "last_name": "Dupont",
    "is_professional": False,
    "structure_id": "siae_001",
    "structure_name": "Eureka Emplois Services",
    "start_date": "2024-03-15",
    "creation_date": "2024-03-10"
}
```

**Meilisearch settings:**
- Searchable: `first_name`, `last_name`
- Filterable: `structure_id`, `is_professional`
- Sortable: `creation_date`, `start_date`

### Structures Index

```python
{
    "id": "struct_1009",
    "name": "Eureka Emplois Services",
    "type": "AI",
    "address": "46 rue de Saint-Malo, Montfort-sur-Meu",
    "latitude": 48.1234,
    "longitude": -1.9567,
    "description": "Structure d'Insertion par l'Activité Économique...",
    "source": "emplois-de-linclusion",
    "lien_source": "https://emplois.inclusion.beta.gouv.fr/company/..."
}
```

**Meilisearch settings:**
- Searchable: `name`, `description`
- Filterable: `type`, `source`
- Sortable: `name`

### Services Index

```python
{
    "id": "serv_5001",
    "name": "Accompagnement vers l'emploi",
    "type": "accompagnement",
    "theme": "emploi",
    "structure_id": "struct_1009",
    "structure_name": "Eureka Emplois Services",
    "description": "Aide à la recherche d'emploi..."
}
```

**Meilisearch settings:**
- Searchable: `name`, `description`
- Filterable: `type`, `theme`, `structure_id`
- Sortable: `name`

## SIAE Identification

Structures are SIAEs when:
- `source` = `"emplois-de-linclusion"`
- `lien_source` starts with `"https://emplois.inclusion.beta.gouv.fr/company/"`

5 SIAEs will be selected for user attachment.

## User Context & Privacy

- Dropdown at top simulates "logged in" user/structure
- Stored in Flask session
- User searches filtered by `structure_id` matching context
- Professional users see all users in their structure
- End users (beneficiaries) are searchable but don't log in

## Data Pipeline

1. **extract.py**: Downloads data-inclusion dataset from data.gouv.fr API
2. **generate_users.py**: Creates 100 fake French users (5 professionals, 95 beneficiaries) across 5 SIAEs
3. **index.py**: Loads all data into Meilisearch with proper settings

## Docker Services

```yaml
services:
  web:
    build: .
    ports:
      - "5000:5000"
    depends_on:
      - search
    environment:
      - MEILISEARCH_URL=http://search:7700

  search:
    image: getmeili/meilisearch:v1.6
    ports:
      - "7700:7700"
    volumes:
      - meili_data:/meili_data
    environment:
      - MEILI_MASTER_KEY=masterKey
```

## UI Components

**Autocomplete dropdown layout:**
```
┌─────────────┬────────────────────────────────┐
│ Utilisateurs│ Marie Dupont                   │
│             │ Jean Martin                    │
│             │ → voir tous (12)               │
├─────────────┼────────────────────────────────┤
│ Structures  │ Eureka Emplois Services        │
│             │ Emmaüs Solidarité              │
│             │ → voir tous (45)               │
├─────────────┼────────────────────────────────┤
│ Services    │ Accompagnement emploi          │
│             │ Formation numérique            │
│             │ → voir tous (23)               │
└─────────────┴────────────────────────────────┘
```

Sections with 0 results are hidden.

---

*Design validated: 2025-12-07*
