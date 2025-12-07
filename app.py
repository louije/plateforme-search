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

    # Get available SIAEs for context selector
    client = get_search_client()
    try:
        result = client.index("structures").search(
            "",
            {
                "limit": 100,
                "filter": 'source = "emplois-de-linclusion"',
            }
        )
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
    context = get_current_context()
    try:
        user = client.index("users").get_document(id)
    except Exception:
        return "User not found", 404

    return render_template("detail.html", entity=user, entity_type="user", context=context)


@app.route("/structures/<id>")
def structure_detail(id):
    """Structure detail page."""
    client = get_search_client()
    context = get_current_context()
    try:
        structure = client.index("structures").get_document(id)
    except Exception:
        return "Structure not found", 404

    return render_template("detail.html", entity=structure, entity_type="structure", context=context)


@app.route("/services/<id>")
def service_detail(id):
    """Service detail page."""
    client = get_search_client()
    context = get_current_context()
    try:
        service = client.index("services").get_document(id)
    except Exception:
        return "Service not found", 404

    return render_template("detail.html", entity=service, entity_type="service", context=context)


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
