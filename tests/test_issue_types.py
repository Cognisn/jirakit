"""
Unit tests for the Issue Types module.

Tests cover:
- IssueType class properties
- IssueTypes.create() method
- IssueTypes.delete() method
- IssueTypes.get_all() method
- IssueTypes.get_all_user_issue_types() method
- IssueTypeScheme class and operations
- IssueTypeScreenScheme class and operations
"""

import pytest
from unittest.mock import Mock
from jirakit.issues.types import IssueType, IssueTypes, IssueTypeScheme, IssueTypeScreenScheme


class TestIssueTypeClass:
    """Tests for the IssueType class."""

    def test_issue_type_initialisation(self, mock_client, sample_issue_type_data):
        """Test IssueType class initialisation."""
        issue_type = IssueType(sample_issue_type_data, mock_client)

        assert issue_type.detail == sample_issue_type_data
        assert issue_type.client == mock_client

    def test_issue_type_id_property(self, mock_client, sample_issue_type_data):
        """Test IssueType.id property."""
        issue_type = IssueType(sample_issue_type_data, mock_client)

        assert issue_type.id == sample_issue_type_data["id"]

    def test_issue_type_name_property(self, mock_client, sample_issue_type_data):
        """Test IssueType.name property."""
        issue_type = IssueType(sample_issue_type_data, mock_client)

        assert issue_type.name == sample_issue_type_data["name"]

    def test_issue_type_description_property(self, mock_client, sample_issue_type_data):
        """Test IssueType.description property."""
        issue_type = IssueType(sample_issue_type_data, mock_client)

        assert issue_type.description == sample_issue_type_data["description"]


class TestIssueTypesCreate:
    """Tests for IssueTypes.create() method."""

    def test_create_issue_type_success(self, mock_client, sample_issue_type_data):
        """Test successful issue type creation."""
        mock_response = Mock()
        mock_response.json.return_value = sample_issue_type_data
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response

        issue_types_manager = IssueTypes(mock_client)
        issue_type = issue_types_manager.create("Bug", "standard", "A bug issue type", 0)

        assert isinstance(issue_type, IssueType)
        assert issue_type.name == "Bug"
        mock_client.post.assert_called_once()

        # Verify correct API endpoint (v3)
        call_args = mock_client.post.call_args
        assert "/rest/api/3/issuetype" in call_args[0][0]

    def test_create_issue_type_with_different_types(self, mock_client, sample_issue_type_data):
        """Test creating issue types with different types."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response

        issue_types_manager = IssueTypes(mock_client)

        # Test standard type
        mock_response.json.return_value = {**sample_issue_type_data, "type": "standard"}
        issue_type = issue_types_manager.create("Task", "standard", "A task", 0)
        assert issue_type is not None

        # Test subtask type
        mock_response.json.return_value = {**sample_issue_type_data, "type": "subtask"}
        issue_type = issue_types_manager.create("Sub-task", "subtask", "A subtask", 1)
        assert issue_type is not None


class TestIssueTypesDelete:
    """Tests for IssueTypes.delete() method."""

    def test_delete_issue_type_success(self, mock_client, sample_issue_type_data):
        """Test successful issue type deletion."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_client.delete.return_value = mock_response

        issue_type = IssueType(sample_issue_type_data, mock_client)
        issue_types_manager = IssueTypes(mock_client)

        issue_types_manager.delete(issue_type)

        mock_client.delete.assert_called_once()

        # Verify correct API endpoint (v3)
        call_args = mock_client.delete.call_args
        assert "/rest/api/3/issuetype/" in call_args[0][0]
        assert sample_issue_type_data["id"] in call_args[0][0]


class TestIssueTypesGetAll:
    """Tests for IssueTypes.get_all() and get_all_user_issue_types() methods."""

    def test_get_all_user_issue_types(self, mock_client, sample_issue_type_data):
        """Test fetching all user issue types."""
        issue_types_data = [
            sample_issue_type_data,
            {**sample_issue_type_data, "id": "10002", "name": "Task"},
            {**sample_issue_type_data, "id": "10003", "name": "Story"}
        ]

        mock_response = Mock()
        mock_response.json.return_value = issue_types_data
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response

        issue_types_manager = IssueTypes(mock_client)
        issue_types = issue_types_manager.get_all_user_issue_types()

        assert len(issue_types) == 3
        assert all(isinstance(it, IssueType) for it in issue_types)
        assert issue_types[0].name == "Bug"
        assert issue_types[1].name == "Task"
        assert issue_types[2].name == "Story"

        # Verify correct API endpoint
        call_args = mock_client.get.call_args
        assert "/rest/api/3/issuetype" in call_args[0][0]

    def test_get_all_for_project(self, mock_client, sample_issue_type_data):
        """Test fetching issue types for a specific project."""
        issue_types_data = [sample_issue_type_data]

        mock_response = Mock()
        mock_response.json.return_value = issue_types_data
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response

        issue_types_manager = IssueTypes(mock_client)
        issue_types = issue_types_manager.get_all(project_id="10000")

        assert len(issue_types) == 1
        assert isinstance(issue_types[0], IssueType)

        # Verify correct API endpoint with project ID
        call_args = mock_client.get.call_args
        assert "/rest/api/3/issuetype/project" in call_args[0][0]
        assert "projectId=10000" in call_args[0][0]


class TestIssueTypeSchemeClass:
    """Tests for the IssueTypeScheme class."""

    def test_issue_type_scheme_initialisation(self, mock_client):
        """Test IssueTypeScheme class initialisation."""
        scheme_data = {
            "id": "10000",
            "name": "Test Scheme",
            "description": "A test scheme",
            "issueTypeIds": ["10001", "10002"]
        }

        scheme = IssueTypeScheme(scheme_data, mock_client)

        assert scheme.detail == scheme_data
        assert scheme.client == mock_client

    def test_issue_type_scheme_properties(self, mock_client):
        """Test IssueTypeScheme properties."""
        scheme_data = {
            "id": "10000",
            "name": "Test Scheme",
            "description": "A test scheme",
            "issueTypeIds": ["10001", "10002"]
        }

        scheme = IssueTypeScheme(scheme_data, mock_client)

        assert scheme.id == "10000"
        assert scheme.name == "Test Scheme"
        assert scheme.description == "A test scheme"

    def test_add_issue_types_to_scheme(self, mock_client, sample_issue_type_data):
        """Test adding issue types to scheme."""
        scheme_data = {
            "id": "10000",
            "name": "Test Scheme",
            "description": "A test scheme"
        }

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_client.put.return_value = mock_response

        scheme = IssueTypeScheme(scheme_data, mock_client)
        issue_type = IssueType(sample_issue_type_data, mock_client)

        scheme.add_issue_types([issue_type])

        mock_client.put.assert_called_once()

        # Verify correct API endpoint
        call_args = mock_client.put.call_args
        assert "/rest/api/3/issuetypescheme/" in call_args[0][0]
        assert "/issuetype" in call_args[0][0]


class TestIssueTypeScreenSchemeClass:
    """Tests for the IssueTypeScreenScheme class."""

    def test_issue_type_screen_scheme_initialisation(self, mock_client):
        """Test IssueTypeScreenScheme class initialisation."""
        scheme_data = {
            "id": "10000",
            "name": "Test Screen Scheme",
            "description": "A test screen scheme"
        }

        scheme = IssueTypeScreenScheme(scheme_data, mock_client)

        assert scheme.detail == scheme_data
        assert scheme.client == mock_client

    def test_issue_type_screen_scheme_properties(self, mock_client):
        """Test IssueTypeScreenScheme properties."""
        scheme_data = {
            "id": "10000",
            "name": "Test Screen Scheme",
            "description": "A test screen scheme"
        }

        scheme = IssueTypeScreenScheme(scheme_data, mock_client)

        assert scheme.id == "10000"
        assert scheme.name == "Test Screen Scheme"
        assert scheme.description == "A test screen scheme"


class TestIssueTypesSchemeOperations:
    """Tests for issue type scheme operations."""

    def test_create_issue_type_scheme(self, mock_client):
        """Test creating an issue type scheme."""
        scheme_data = {
            "id": "10000",
            "name": "Test Scheme",
            "description": "A test scheme"
        }

        mock_response = Mock()
        mock_response.json.return_value = {"issueTypeSchemeId": "10000"}
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response

        # Mock get request for fetching the created scheme
        mock_get_response = Mock()
        mock_get_response.json.return_value = {"values": [scheme_data]}
        mock_get_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_get_response

        issue_types_manager = IssueTypes(mock_client)
        scheme = issue_types_manager.create_issue_type_scheme("Test Scheme", "A test scheme", ["10001"])

        assert isinstance(scheme, IssueTypeScheme)
        mock_client.post.assert_called_once()

    def test_get_all_issue_type_schemes(self, mock_client, paginated_response_factory):
        """Test fetching all issue type schemes."""
        schemes_data = [
            {"id": "10000", "name": "Scheme 1", "description": "First scheme"},
            {"id": "10001", "name": "Scheme 2", "description": "Second scheme"}
        ]

        mock_response = Mock()
        mock_response.json.return_value = paginated_response_factory(schemes_data, is_last=True)
        mock_client.get.return_value = mock_response

        issue_types_manager = IssueTypes(mock_client)
        schemes = issue_types_manager.get_all_issue_type_schemes()

        assert len(schemes) == 2
        assert all(isinstance(s, IssueTypeScheme) for s in schemes)

    def test_delete_issue_type_scheme(self, mock_client):
        """Test deleting an issue type scheme."""
        scheme_data = {
            "id": "10000",
            "name": "Test Scheme",
            "description": "A test scheme"
        }

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_client.delete.return_value = mock_response

        scheme = IssueTypeScheme(scheme_data, mock_client)
        issue_types_manager = IssueTypes(mock_client)

        issue_types_manager.delete_issue_type_scheme(scheme)

        mock_client.delete.assert_called_once()
