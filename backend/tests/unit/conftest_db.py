"""
Conftest for database model tests - isolated from main app.
"""
import pytest


# Don't import anything from the app at pytest collection time
# to avoid triggering the Pydantic error in other parts of the app
