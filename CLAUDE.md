# Universal Search Prototype - Development Brief

## 1. Project Overview

This document provides a comprehensive specification for developing a universal search prototype that enables users to search across multiple entity types (users, structures, and services) through a single interface. The system will use Meilisearch for fast, real-time search capabilities with intelligent result grouping and filtering.

### 1.1 Technical Stack

- **Backend:** Flask (Python) - prototype environment
- **Search Engine:** Single Meilisearch instance with multiple indexes
- **Hosting:** Docker Compose (local) or Railway (cloud)
- **Development Path:** Flask prototype → Django production

---

## 2. Data Model

The system will operate with three distinct Meilisearch indexes, each optimized for different entity types.
Each entity has an id field.

### 2.1 Users Index

| Field | Type | Description |
|-------|------|-------------|
| first_name | String | User's first name |
| last_name | String | User's last name |
| is_professional | Boolean | Distinguishes professional users (true) from end users/beneficiaries (false) |
| structure | Reference | Link to associated structure/company |
| start_date | Date | User's start date |
| creation_date | Date | Record creation timestamp |

#### Data Distribution

- 100 total users distributed across 5 SIAEs (20 users per SIAE)
- 5 professional users (1 per SIAE)
- 95 end users (19 per SIAE)
- Realistic French names (diverse but authentic)
- Users are job seekers (job categories not important for prototype)
- **Note:** To be updated with actual data at a later stage

### 2.2 Structures Index

| Field | Type | Description |
|-------|------|-------------|
| name | String | Structure/company name |
| location | Object | Address + latitude/longitude coordinates |
| type | String | Structure category/classification |
| long_description | Text | Detailed description for full-text search |

#### Data Requirements

- Several hundred structures from the French data inclusion dataset
- Among them, 5 SIAEs (inclusive companies) for user attachment
- In the data-inclusion dataset, SIAEs are structures from source emplois-de-linclusion whose lien_source begins with "https://emplois.inclusion.beta.gouv.fr/company/"

### 2.3 Services Index

| Field | Type | Description |
|-------|------|-------------|
| name | String | Service name |
| type | String | Service category |
| theme | String | Service theme classification (from dataset) |
| structure_id | Reference | Link to parent structure |
| long_description | Text | Detailed description including structure data for enhanced search |

### 2.4 Data Sources

- **Structures & Services:** French "data inclusion" dataset from data.gouv.fr (open access JSON/CSV)
- **Data Extraction Tool:** Existing prototype called "swiper", which can be found at ../swiper.
- **Users:** Generated fake data with realistic French names

**Swiper Application Repository:** it's at ../swiper or https://github.com/louije/swiper.

---

## 3. Search Functionality

### 3.1 Core Search Behavior

- **Default Mode:** Multi-search across all 3 indexes simultaneously
- **Search Type:** Real-time search-as-you-type behavior (Meilisearch optimized)
- **Result Grouping:** Results grouped by type (Users, Structures, Services)
- **Type Order:** Consistent ordering - do not mix result types
- **Quality Control:** Hide entire sections if results are poor quality or irrelevant

### 3.2 Search Interface Design

#### Autocomplete Dropdown Layout

- **Large dropdown with two-column layout:**
  - Left column (narrow): Category labels - "Users", "Structures", "Services"
  - Right column (wide): 3 results + "show all (X more results)" link
- **Filter Controls:** Radio button/tag selector above results to filter by category
- **Result Interaction:** 
  - Basic info shown in autocomplete dropdown
  - Click → detailed page with all available data + back button

#### Smart Result Display

- Default: 3 results per type
- Boost to 10 results if search intent for a specific type is detected
- Build in flexibility to experiment and optimize display strategies

### 3.3 Intent Detection (Future Enhancement)

- **Keyword Patterns:** Analyze search terms to infer intent (e.g., "John Smith" → person, "restaurant" → structure)
- **Result Scoring:** If one type scores significantly higher, boost that type's display
- **Configurable Word Lists:** Maintain lists of words that convey certain search intents

### 3.4 API Structure

#### Endpoint 1: Quick Search/Autocomplete

- **Output:** JSON response
- **Parameters:** Filter parameters for type selection (radio button state)
- **Use case:** Real-time autocomplete dropdown

#### Endpoint 2: Full Results Page

- **Output:** HTML response
- **Features:** Advanced filtering, pagination, detailed views
- **Use case:** Complete search experience when user clicks "show all"

---

## 4. Meilisearch Configuration

### 4.1 Essential Features

- **Typo Tolerance:** Configure appropriate typo tolerance levels per word length
- **Synonym Management:** Configurable synonym lists for job-seeking context (to be defined later)
- **Ranking Rules:** Optimize for exact matches vs proximity vs typo tolerance
- **French Language:** Stop words handling and language-specific optimization
- **Searchable Attributes:** Configure which fields are searchable per index
- **Highlighting:** Enable for UI display

### 4.2 Filtering Configuration

- **Structure Type Filtering:** Enable filtering by structure category
- **Service Theme Filtering:** Enable filtering by service theme classification
- **Faceted Search:** Configure facet distribution to show result counts per filter option

### 4.3 Multi-Search Implementation

Use Meilisearch's multi-search endpoint (`/multi-search`) to:
- Query all indexes in a single HTTP request
- Benefit from concurrent query execution
- Reduce network overhead and latency

---

## 5. Security & Privacy Model

### 5.1 User Visibility Rules

- **Core Principle:** Users can only search/find users from their own structure
- **Implementation:** Filter search results based on current user's structure membership
- **Prototype Simulation:** Dropdown selector to simulate different users/structures

### 5.2 User Types

| Type | is_professional | Description |
|------|-----------------|-------------|
| Professional Users | true | Have accounts, provide services, actual product users |
| End Users | false | Service beneficiaries, no accounts |

---

## 6. UI/UX Specifications

### 6.1 Main Search Interface

```
┌─────────────────────────────────────────────────────────┐
│  [User/Structure Selector ▼]                            │
├─────────────────────────────────────────────────────────┤
│  🔍 Search...                                           │
├─────────────────────────────────────────────────────────┤
│  ○ All  ○ Users  ○ Structures  ○ Services              │
├─────────────────────────────────────────────────────────┤
│  Users        │  • Result 1                             │
│               │  • Result 2                             │
│               │  • Result 3                             │
│               │  → show all (12 more)                   │
├───────────────┼─────────────────────────────────────────┤
│  Structures   │  • Result 1                             │
│               │  • Result 2                             │
│               │  • Result 3                             │
│               │  → show all (45 more)                   │
├───────────────┼─────────────────────────────────────────┤
│  Services     │  • Result 1                             │
│               │  • Result 2                             │
│               │  • Result 3                             │
│               │  → show all (23 more)                   │
└───────────────┴─────────────────────────────────────────┘
```

### 6.2 Full Results Page

- Triggered by "show all" link
- Advanced filters (structure type, service theme)
- Pagination
- Detailed result cards

### 6.3 Detail Page

- All available data for the selected entity
- Back button to return to search
- Basic layout for prototype

---

## 7. Future Enhancements (Post-Prototype)

### 7.1 Geographic Search

- Rank results by proximity to user location
- Filter by geographic area
- Uses Meilisearch's built-in geosearch capabilities
- **Status:** Deferred - structures have location data but feature not needed for prototype

### 7.2 Smart Intent Detection

- Automatic detection of search type based on query analysis
- Machine learning-based ranking optimization

### 7.3 Advanced Synonym Configuration

- Domain-specific synonyms for job seeking, housing, social services
- Example patterns: "hébergement", "logement", "social" for housing-related searches

---

## 8. Development Notes

### 8.1 Prototype Priorities

1. Basic multi-search functionality across all indexes
2. Autocomplete UI with grouped results
3. Type filtering (radio buttons)
4. Full results page with basic filtering
5. Detail pages for each entity type

### 8.2 Data Generation Tasks

1. Extract structures and services from data inclusion dataset using swiper tool
2. Generate 100 fake users with French names
3. Distribute users across 5 SIAEs
4. Link services to structures

### 8.3 Configuration Tasks

1. Set up Meilisearch indexes with appropriate schemas
2. Configure searchable attributes per index
3. Configure filterable attributes (type, theme)
4. Set up faceted search for filter counts
5. Configure typo tolerance and French stop words

---

## Appendix A: Meilisearch Index Configuration

### Users Index Settings

```json
{
  "searchableAttributes": ["first_name", "last_name"],
  "filterableAttributes": ["structure", "is_professional"],
  "sortableAttributes": ["creation_date", "start_date"]
}
```

### Structures Index Settings

```json
{
  "searchableAttributes": ["name", "long_description"],
  "filterableAttributes": ["type"],
  "sortableAttributes": ["name"]
}
```

### Services Index Settings

```json
{
  "searchableAttributes": ["name", "long_description"],
  "filterableAttributes": ["type", "theme", "structure_id"],
  "sortableAttributes": ["name"]
}
```

---

## Appendix B: Sample API Responses

### Quick Search Response (JSON)

```json
{
  "users": {
    "hits": [...],
    "estimatedTotalHits": 12,
    "displayed": 3
  },
  "structures": {
    "hits": [...],
    "estimatedTotalHits": 45,
    "displayed": 3
  },
  "services": {
    "hits": [...],
    "estimatedTotalHits": 23,
    "displayed": 3
  },
  "query": "search term",
  "processingTimeMs": 12
}
```

---

*Document Version: 1.0*  
*Last Updated: 2025-12-07*
