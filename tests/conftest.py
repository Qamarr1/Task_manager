"""
Pytest configuration and shared fixtures
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

@pytest.fixture
def client():
    """Create test client with testing mode enabled"""
    app.config["TESTING"] = True
    
    with app.test_client() as client:
        yield client
