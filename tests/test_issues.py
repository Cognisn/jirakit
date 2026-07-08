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

    @staticmethod
    def _list_item(text):
        """Build an ADF listItem wrapping a paragraph of the given text."""
        return {
            "type": "listItem",
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": text}]}
            ],
        }

    def test_bullet_list_items_are_rendered(self, mock_client):
        """A bulletList renders each item's text with a bullet marker."""
        issue = self._make_issue(mock_client)
        doc = [
            {
                "type": "bulletList",
                "content": [self._list_item("First"), self._list_item("Second")],
            }
        ]

        result = issue._format_doc(doc)

        assert "First" in result
        assert "Second" in result
        assert "- First" in result
        assert "- Second" in result

    def test_ordered_list_items_are_numbered(self, mock_client):
        """An orderedList renders each item's text with an incrementing number."""
        issue = self._make_issue(mock_client)
        doc = [
            {
                "type": "orderedList",
                "content": [self._list_item("Alpha"), self._list_item("Beta")],
            }
        ]

        result = issue._format_doc(doc)

        assert "1. Alpha" in result
        assert "2. Beta" in result

    def test_nested_list_text_is_preserved(self, mock_client):
        """A list nested inside a list item still contributes its text."""
        issue = self._make_issue(mock_client)
        doc = [
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [{"type": "text", "text": "Parent"}],
                            },
                            {
                                "type": "bulletList",
                                "content": [self._list_item("Child")],
                            },
                        ],
                    }
                ],
            }
        ]

        result = issue._format_doc(doc)

        assert "Parent" in result
        assert "Child" in result

    def test_list_alongside_paragraph_keeps_both(self, mock_client):
        """A list between paragraphs does not drop the surrounding prose."""
        issue = self._make_issue(mock_client)
        doc = [
            {"type": "paragraph", "content": [{"type": "text", "text": "Before"}]},
            {"type": "bulletList", "content": [self._list_item("Item")]},
            {"type": "paragraph", "content": [{"type": "text", "text": "After"}]},
        ]

        result = issue._format_doc(doc)

        assert "Before" in result
        assert "Item" in result
        assert "After" in result


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


class TestAddAttachment:
    """Tests for Issues.add_attachment."""

    def _issues(self, mock_client):
        mock_project = MagicMock(spec=Project)
        mock_project.id = "10000"
        mock_project.key = "TEST"
        # Issues.__init__ fetches create metadata; no issue types => no field calls.
        mock_client.get.side_effect = [_mock_response({"issueTypes": []})]
        mock_client.jira = Mock()
        return Issues(mock_project, mock_client)

    def test_add_attachment_delegates_to_jira_client(self, mock_client):
        """add_attachment passes the key, a BytesIO of the content, and the filename."""
        issues = self._issues(mock_client)

        result = issues.add_attachment("TEST-1", "terms.pdf", b"PDF-BYTES")

        mock_client.jira.add_attachment.assert_called_once()
        kwargs = mock_client.jira.add_attachment.call_args.kwargs
        assert kwargs["issue"] == "TEST-1"
        assert kwargs["filename"] == "terms.pdf"
        assert kwargs["attachment"].read() == b"PDF-BYTES"
        assert result is mock_client.jira.add_attachment.return_value


class TestFieldMapping:
    """Tests for Issues.available_fields and Issues.unmapped_fields."""

    FIELD_META = [
        {"name": "Summary", "key": "summary", "schema": {"type": "string"}},
        {
            "name": "Severity",
            "key": "customfield_10001",
            "schema": {"type": "option"},
            "allowedValues": [
                {"value": "High", "id": "1"},
                {"value": "Low", "id": "2"},
            ],
        },
    ]

    def _issues(self, mock_client):
        mock_project = MagicMock(spec=Project)
        mock_project.id = "10000"
        mock_project.key = "TEST"
        mock_client.get.side_effect = [
            _mock_response({"issueTypes": [{"id": "10001", "name": "Bug"}]}),
            _mock_response({"fields": self.FIELD_META}),
        ]
        return Issues(mock_project, mock_client)

    def test_available_fields_enumerates_create_screen_fields(self, mock_client):
        """available_fields returns name, key, schema type and allowed values."""
        issues = self._issues(mock_client)

        by_name = {f["name"]: f for f in issues.available_fields({"id": "10001"})}

        assert set(by_name) == {"Summary", "Severity"}
        assert by_name["Summary"]["key"] == "summary"
        assert by_name["Summary"]["schema_type"] == "string"
        assert by_name["Summary"]["allowed_values"] == []
        assert by_name["Severity"]["schema_type"] == "option"
        assert by_name["Severity"]["allowed_values"] == ["High", "Low"]

    def test_unmapped_fields_reports_fields_absent_from_create_screen(self, mock_client):
        """unmapped_fields flags supplied fields with a value but no matching field."""
        issues = self._issues(mock_client)
        supplied = {
            "Summary": "hi",
            "Severity": "High",
            "Nonexistent Question": "some value",
            "Empty": "",  # falsy, not sent, so not reported
        }

        assert issues.unmapped_fields({"id": "10001"}, supplied) == [
            "Nonexistent Question"
        ]

    def test_unmapped_fields_empty_when_all_map(self, mock_client):
        """unmapped_fields returns an empty list when every field resolves."""
        issues = self._issues(mock_client)

        assert issues.unmapped_fields({"id": "10001"}, {"Summary": "hi"}) == []
