"""
Pytest configuration and shared fixtures for jirakit tests.

This module provides common fixtures and utilities for testing the jirakit library.
All HTTP requests are mocked to avoid hitting the real Jira API during tests.
"""

import pytest
from unittest.mock import Mock, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def mock_response():
    """
    Create a mock HTTP response object.

    Returns:
        Mock: A mock response object with common methods.
    """
    response = Mock()
    response.status_code = 200
    response.ok = True
    response.raise_for_status = Mock()
    return response


@pytest.fixture
def mock_client():
    """
    Create a mock JiraClient instance.

    Returns:
        Mock: A mock JiraClient with mocked HTTP methods.
    """
    from jirakit import JiraClient

    client = Mock(spec=JiraClient)
    client.base_url = "https://test.atlassian.net"
    client.username = "test@example.com"
    client.password = "test_token"

    # Mock HTTP methods
    client.get = Mock()
    client.post = Mock()
    client.put = Mock()
    client.delete = Mock()

    return client


@pytest.fixture
def sample_user_data():
    """
    Sample user data from /myself endpoint.

    Returns:
        dict: Sample user data.
    """
    return {
        "accountId": "123456:abcdef-1234-5678",
        "accountType": "atlassian",
        "displayName": "Test User",
        "emailAddress": "test@example.com",
        "active": True,
    }


@pytest.fixture
def sample_project_data():
    """
    Sample project data.

    Returns:
        dict: Sample project data.
    """
    return {
        "id": "10000",
        "key": "TEST",
        "name": "Test Project",
        "description": "A test project",
        "projectTypeKey": "software",
    }


@pytest.fixture
def sample_issue_type_data():
    """
    Sample issue type data.

    Returns:
        dict: Sample issue type data.
    """
    return {
        "id": "10001",
        "name": "Bug",
        "description": "A bug issue type",
        "subtask": False,
        "hierarchyLevel": 0,
    }


@pytest.fixture
def sample_field_data():
    """
    Sample custom field data.

    Returns:
        dict: Sample field data.
    """
    return {
        "id": "customfield_10001",
        "name": "Test Field",
        "description": "A test custom field",
        "custom": True,
        "schema": {"type": "string"},
    }


@pytest.fixture
def sample_screen_data():
    """
    Sample screen data.

    Returns:
        dict: Sample screen data.
    """
    return {"id": "10000", "name": "Test Screen", "description": "A test screen"}


@pytest.fixture
def sample_workflow_data():
    """
    Sample workflow data.

    Returns:
        dict: Sample workflow data.
    """
    return {
        "id": {"entityId": "workflow-123", "name": "Test Workflow"},
        "name": "Test Workflow",
        "description": "A test workflow",
        "default": False,
        "steps": [],
    }


@pytest.fixture
def sample_status_data():
    """
    Sample status data.

    Returns:
        dict: Sample status data.
    """
    return {
        "id": "1",
        "name": "Open",
        "description": "The issue is open",
        "statusCategory": "TODO",
        "scope": {"type": "GLOBAL"},
        "usages": [],
        "workflowUsages": [],
    }


@pytest.fixture
def sample_group_data():
    """
    Sample group data.

    Returns:
        dict: Sample group data.
    """
    return {"name": "test-group", "groupId": "group-123"}


@pytest.fixture
def sample_issue_data():
    """
    Sample issue data.

    Returns:
        dict: Sample issue data.
    """
    return {
        "id": "10000",
        "key": "TEST-1",
        "fields": {
            "summary": "Test Issue",
            "description": "A test issue",
            "issuetype": {"id": "10001", "name": "Bug"},
            "project": {"id": "10000", "key": "TEST"},
            "status": {"id": "1", "name": "Open"},
        },
    }


@pytest.fixture
def paginated_response_factory():
    """
    Factory fixture for creating paginated API responses.

    Returns:
        callable: Function that creates paginated responses.
    """

    def create_paginated_response(values, start_at=0, max_results=50, is_last=True):
        """
        Create a paginated response.

        Args:
            values (list): List of values to return.
            start_at (int): Starting index.
            max_results (int): Maximum results per page.
            is_last (bool): Whether this is the last page.

        Returns:
            dict: Paginated response data.
        """
        return {
            "startAt": start_at,
            "maxResults": max_results,
            "total": len(values),
            "isLast": is_last,
            "values": values,
        }

    return create_paginated_response
