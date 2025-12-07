import os

CONFIG = {
    "MEILISEARCH_URL": os.getenv("MEILISEARCH_URL", "http://localhost:7700"),
    "MEILISEARCH_KEY": os.getenv("MEILISEARCH_KEY", "masterKey"),
    "AUTOCOMPLETE_LIMIT": int(os.getenv("AUTOCOMPLETE_LIMIT", "3")),
    "FILTERED_LIMIT": int(os.getenv("FILTERED_LIMIT", "10")),
    "RESULTS_PAGE_LIMIT": int(os.getenv("RESULTS_PAGE_LIMIT", "20")),
}
