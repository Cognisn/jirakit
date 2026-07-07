"""
Unit tests for the Issues module.

Tests cover:
- Issue class properties
- Issue._format_doc() defensive ADF rendering
- Issues.get_issue() method
- Issues.get_issues_updated_last_days() method
"""

import logging
from unittest.mock import MagicMock, Mock

from jirakit.issues import Issue, Issues
from jirakit.projects import Project


def _mock_response(payload):
    """Build a mock HTTP response returning the given JSON payload."""
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status = Mock()
    return response


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


class TestFormatDoc:
    """Tests for Issue._format_doc ADF rendering."""

    def _make_issue(self, mock_client):
        """Build a minimal Issue; _format_doc only uses self for recursion."""
        return Issue({}, mock_client, "Bug", Mock())

    def test_empty_paragraph_is_rendered_without_error(self, mock_client, caplog):
        """An empty ADF paragraph must not log an error, and sibling text survives."""
        issue = self._make_issue(mock_client)
        doc = [
            {"type": "paragraph", "content": [{"type": "text", "text": "Hello"}]},
            {"type": "paragraph"},  # empty: no 'content' key
            {"type": "paragraph", "content": [{"type": "text", "text": "World"}]},
        ]

        with caplog.at_level(logging.ERROR):
            result = issue._format_doc(doc)

        assert "Hello" in result
        assert "World" in result
        assert [r for r in caplog.records if r.levelno >= logging.ERROR] == []

    def test_node_missing_text_is_rendered_without_error(self, mock_client, caplog):
        """A heading node with no 'text' key must not log an error; siblings survive."""
        issue = self._make_issue(mock_client)
        doc = [
            {"type": "heading"},  # no 'text' key
            {"type": "text", "text": "kept"},
        ]

        with caplog.at_level(logging.ERROR):
            result = issue._format_doc(doc)

        assert "kept" in result
        assert [r for r in caplog.records if r.levelno >= logging.ERROR] == []

    def test_node_missing_type_is_rendered_without_error(self, mock_client, caplog):
        """A node with no 'type' key must not log an error; siblings survive."""
        issue = self._make_issue(mock_client)
        doc = [
            {"text": "orphan"},  # no 'type' key
            {"type": "text", "text": "kept"},
        ]

        with caplog.at_level(logging.ERROR):
            result = issue._format_doc(doc)

        assert "kept" in result
        assert [r for r in caplog.records if r.levelno >= logging.ERROR] == []


class TestIssuesOperations:
    """Tests for Issues operations."""

    def test_get_issue(self, mock_client, sample_issue_data):
        """Test fetching an issue by key."""
        mock_project = MagicMock(spec=Project)
        mock_project.id = "10000"
        mock_project.key = "TEST"

        # Issues.__init__ fetches create metadata, then get_issue fetches the issue
        mock_client.get.side_effect = [
            _mock_response({"issueTypes": []}),
            _mock_response(sample_issue_data),
        ]

        issues_manager = Issues(mock_project, mock_client)
        issue = issues_manager.get_issue("TEST-1")

        assert isinstance(issue, Issue)
        assert issue.key == sample_issue_data["key"]
        call_args = mock_client.get.call_args
        assert call_args.kwargs["path"] == "/rest/api/3/issue/TEST-1"

    def test_get_issues_updated_last_days(self, mock_client, sample_issue_data):
        """Test searching for recently updated issues of a given type."""
        mock_project = MagicMock(spec=Project)
        mock_project.id = "10000"
        mock_project.key = "TEST"

        # Issues.__init__ fetches create metadata, then field metadata per type
        mock_client.get.side_effect = [
            _mock_response({"issueTypes": [{"id": "10001", "name": "Bug"}]}),
            _mock_response({"fields": {}}),
        ]
        mock_client.post.return_value = _mock_response({"issues": [sample_issue_data]})

        issues_manager = Issues(mock_project, mock_client)
        results = issues_manager.get_issues_updated_last_days("Bug", 7)

        assert len(results) == 1
        assert isinstance(results[0], Issue)
        assert results[0].key == sample_issue_data["key"]

        # Verify the new v3 search endpoint and the JQL constraints
        call_args = mock_client.post.call_args
        assert call_args.kwargs["path"] == "/rest/api/3/search/jql"
        jql = call_args.kwargs["data"]["jql"]
        assert 'project="TEST"' in jql
        assert 'updated >= "-7d"' in jql
