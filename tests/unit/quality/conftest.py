"""Pytest configuration for quality unit tests."""

from unittest import mock

import pytest


@pytest.fixture
def mock_neo4j_connection():
    """Create mock Neo4j connection for testing."""
    connection = mock.MagicMock()
    connection.database = "neo4j"
    return connection
