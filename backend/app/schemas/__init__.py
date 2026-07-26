# backend/app/schemas/__init__.py
"""Pydantic schemas for the Songs domain.
The package aggregates all schema modules and provides convenient imports.
"""

from .lookups import *
from .song import *
from .song_file import *
from .song_difficulty import *
from .song_technique import *
from .song_skill import *
from .song_event import *
from .song_ground_truth import *
from .song_analytics import *
