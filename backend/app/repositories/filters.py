# backend/app/repositories/filters.py
"""Utility functions for building flexible SQLAlchemy filter expressions.
These helpers are used by the repository ``list`` methods to apply
keyword search, sorting, pagination and arbitrary column filters without
modifying each repository implementation.
"""

from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import or_, asc, desc
from sqlalchemy.orm import Query

# ---------------------------------------------------------------------------
# Generic filter builder for the Song entity – can be extended for other models.
# ---------------------------------------------------------------------------

def apply_song_filters(query: Query, filters: Dict[str, Any] | None = None) -> Query:
    """Apply a dictionary of filters to a ``Song`` query.

    Supported keys:
        * ``title`` – exact match or partial (if ``%`` present).
        * ``instrument_id``, ``genre_id``, ``language_id`` – exact match.
        * ``is_public`` – boolean.
        * ``created_by`` – exact match.
        * ``keyword`` – searches ``title`` and ``subtitle`` using ILIKE.
        * ``order_by`` – field name optionally prefixed with ``-`` for DESC.
        * ``offset`` / ``limit`` – pagination.
    """
    if not filters:
        return query

    entity = query.column_descriptions[0]["entity"]

    # Exact column filters ---------------------------------------------------
    exact_fields = [
        "instrument_id",
        "genre_id",
        "language_id",
        "is_public",
        "created_by",
    ]
    for field in exact_fields:
        if (value := filters.get(field)) is not None:
            query = query.filter(getattr(entity, field) == value)

    # Title partial or exact match ------------------------------------------
    if (title := filters.get("title")) is not None:
        col = getattr(entity, "title")
        if "%" in title:
            query = query.filter(col.ilike(title))
        else:
            query = query.filter(col == title)

    # Keyword search across title & subtitle --------------------------------
    if (kw := filters.get("keyword")) is not None:
        query = query.filter(
            or_(entity.title.ilike(f"%{kw}%"), entity.subtitle.ilike(f"%{kw}%"))
        )

    # Sorting ---------------------------------------------------------------
    if (order := filters.get("order_by")) is not None:
        if order.startswith("-"):
            col = getattr(entity, order[1:])
            query = query.order_by(desc(col))
        else:
            col = getattr(entity, order)
            query = query.order_by(asc(col))

    # Pagination ------------------------------------------------------------
    offset = filters.get("offset", 0)
    limit = filters.get("limit", 100)
    query = query.offset(offset).limit(limit)

    return query

# ---------------------------------------------------------------------------
# Helper for generic lookup tables (instrument, genre, etc.)
# ---------------------------------------------------------------------------

def apply_lookup_filters(query: Query, filters: Dict[str, Any] | None = None) -> Query:
    """Apply simple equality filters for lookup tables.
    ``filters`` keys are column names; values are matched exactly.
    """
    if not filters:
        return query
    entity = query.column_descriptions[0]["entity"]
    for field, value in filters.items():
        query = query.filter(getattr(entity, field) == value)
    return query
