"""
Unit tests for the Issues module.

Tests cover:
- Issue class properties
- Issues.get_by_key() method
- Issues.search() method
"""

import pytest
from unittest.mock import Mock
from jirakit.issues import Issue, Issues


class TestIssueClass:
    """Tests for the Issue class."""

    def test_issue_initialisation(self, mock_client, sample_issue_data):
        """Test Issue class initialisation."""
        get_field = Mock()
        issue = Issue(sample_issue_data, mock_client, "Bug", get_field)

        assert issue.detail == sample_issue_data
        assert issue.client == mock_client
        assert issue.issue_type == "Bug"

    def test_issue_key_property(self, mock_client, sample_issue_data):
        """Test Issue.key property."""
        get_field = Mock()
        issue = Issue(sample_issue_data, mock_client, "Bug", get_field)

        assert issue.key == sample_issue_data["key"]


class TestIssuesOperations:
    """Tests for Issues operations."""

    def test_get_by_key(self, mock_client, sample_issue_data):
        """Test fetching issue by key."""
        mock_response = Mock()
        mock_response.json.return_value = sample_issue_data
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response

        from jirakit.projects import Project
        from unittest.mock import MagicMock

        # Create a mock project with skip_load to avoid initialization issues
        mock_project = MagicMock(spec=Project)
        mock_project.id = "10000"
        mock_project.key = "TEST"

        issues_manager = Issues(mock_client, mock_project)
        issue_data = issues_manager.get_by_key("TEST-1")

        assert issue_data["key"] == "TEST-1"
        mock_client.get.assert_called_once()

    def test_search(self, mock_client, sample_issue_data):
        """Test searching issues with JQL."""
        mock_response = Mock()
        mock_response.json.return_value = {"issues": [sample_issue_data]}
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response

        from jirakit.projects import Project
        from unittest.mock import MagicMock

        # Create a mock project
        mock_project = MagicMock(spec=Project)

        issues_manager = Issues(mock_client, mock_project)
        results = issues_manager.search("project = TEST")

        assert "issues" in results
        assert len(results["issues"]) == 1
