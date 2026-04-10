"""Test configuration for unit tests."""
import pytest


@pytest.fixture(autouse=True)
def no_network_calls():
    """Ensure no network calls are made during unit tests."""
    yield
