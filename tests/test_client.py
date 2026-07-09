"""
Unit tests for the JiraClient class.

Tests cover:
- Client initialisation
- HTTP methods (GET, POST, PUT, DELETE)
- Authentication
- get_me() method
- Factory methods for sub-modules
"""

import pytest
from unittest.mock import Mock, patch
from jirakit import JiraClient


@pytest.fixture(autouse=True)
def mock_jira_library():
    """
    Mock the underlying jira.JIRA client for every test in this module.

    JiraClient.__init__ constructs a jira.JIRA instance, which performs a
    server-info request on creation. Mocking it keeps these tests offline.
    """
    with patch("jirakit.JIRA") as mock_jira:
        yield mock_jira


class TestJiraClientInitialisation:
    """Tests for JiraClient initialisation."""

    def test_client_initialisation(self):
        """Test that JiraClient initialises correctly."""
        url = "https://test.atlassian.net"
        username = "test@example.com"
        password = "test_token"

        client = JiraClient(url, username, password)

        assert client.url == url
        assert client.username == username
        assert client.password == password
        assert client.session is not None

    def test_client_session_auth(self):
        """Test that the session has correct authentication."""
        url = "https://test.atlassian.net"
        username = "test@example.com"
        password = "test_token"

        client = JiraClient(url, username, password)

        assert client.session.auth.username == username
        assert client.session.auth.password == password


class TestJiraClientTimeouts:
    """Tests for request timeout configuration."""

    def test_default_timeout(self):
        """The client applies the default (connect, read) timeout."""
        client = JiraClient("https://test.atlassian.net", "user", "pass")

        assert client.timeout == JiraClient.DEFAULT_TIMEOUT
        assert client.timeout == (10.0, 60.0)

    def test_custom_timeout(self):
        """A caller-supplied timeout is stored on the client."""
        client = JiraClient("https://test.atlassian.net", "user", "pass", timeout=5.0)

        assert client.timeout == 5.0

    def test_timeout_passed_to_jira_library(self, mock_jira_library):
        """The timeout is passed through to the underlying jira.JIRA client."""
        JiraClient("https://test.atlassian.net", "user", "pass", timeout=(3.0, 7.0))

        assert mock_jira_library.call_args.kwargs["timeout"] == (3.0, 7.0)

    @pytest.mark.parametrize("verb", ["get", "post", "put", "delete"])
    def test_http_methods_apply_timeout(self, verb):
        """Every HTTP verb passes the configured timeout to the session."""
        client = JiraClient(
            "https://test.atlassian.net", "user", "pass", timeout=(2.0, 4.0)
        )

        with patch(f"requests.Session.{verb}") as mock_verb:
            mock_verb.return_value = Mock(status_code=200)
            if verb in ("post", "put"):
                getattr(client, verb)("/rest/api/3/test", data={"a": 1})
            else:
                getattr(client, verb)("/rest/api/3/test")

        assert mock_verb.call_args.kwargs["timeout"] == (2.0, 4.0)


class TestJiraClientHTTPMethods:
    """Tests for JiraClient HTTP methods."""

    @patch("requests.Session.get")
    def test_get_method(self, mock_get):
        """Test GET method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value = mock_response

        client = JiraClient("https://test.atlassian.net", "user", "pass")
        response = client.get("/rest/api/3/test")

        assert response.status_code == 200
        assert response.json() == {"test": "data"}
        mock_get.assert_called_once()

    @patch("requests.Session.post")
    def test_post_method(self, mock_post):
        """Test POST method."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "123"}
        mock_post.return_value = mock_response

        client = JiraClient("https://test.atlassian.net", "user", "pass")
        response = client.post("/rest/api/3/test", data={"name": "test"})

        assert response.status_code == 201
        assert response.json() == {"id": "123"}
        mock_post.assert_called_once()

    @patch("requests.Session.put")
    def test_put_method(self, mock_put):
        """Test PUT method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        client = JiraClient("https://test.atlassian.net", "user", "pass")
        response = client.put("/rest/api/3/test/123", data={"name": "updated"})

        assert response.status_code == 200
        mock_put.assert_called_once()

    @patch("requests.Session.delete")
    def test_delete_method(self, mock_delete):
        """Test DELETE method."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        client = JiraClient("https://test.atlassian.net", "user", "pass")
        response = client.delete("/rest/api/3/test/123")

        assert response.status_code == 204
        mock_delete.assert_called_once()


class TestJiraClientGetMe:
    """Tests for get_me() method."""

    @patch("requests.Session.get")
    def test_get_me_success(self, mock_get, sample_user_data):
        """Test successful get_me() call."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_user_data
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = JiraClient("https://test.atlassian.net", "user", "pass")
        user_data = client.get_me()

        assert user_data["accountId"] == sample_user_data["accountId"]
        assert user_data["displayName"] == sample_user_data["displayName"]
        assert user_data["emailAddress"] == sample_user_data["emailAddress"]

        # Verify it called the v3 API endpoint
        args, kwargs = mock_get.call_args
        assert "/rest/api/3/myself" in args[0]

    @patch("requests.Session.get")
    def test_get_me_handles_error(self, mock_get):
        """Test get_me() handles errors correctly."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = Exception("Unauthorised")
        mock_get.return_value = mock_response

        client = JiraClient("https://test.atlassian.net", "user", "pass")

        with pytest.raises(Exception):
            client.get_me()


class TestJiraClientFactoryMethods:
    """Tests for factory methods that create sub-module instances."""

    def test_fields_factory(self):
        """Test fields() factory method."""
        client = JiraClient("https://test.atlassian.net", "user", "pass")
        fields = client.fields()

        from jirakit.fields import Fields

        assert isinstance(fields, Fields)
        assert fields.client == client

    def test_issue_types_factory(self):
        """Test issue_types() factory method."""
        client = JiraClient("https://test.atlassian.net", "user", "pass")
        issue_types = client.issue_types()

        from jirakit.issues.types import IssueTypes

        assert isinstance(issue_types, IssueTypes)
        assert issue_types.client == client

    def test_projects_factory(self):
        """Test projects() factory method."""
        client = JiraClient("https://test.atlassian.net", "user", "pass")
        projects = client.projects()

        from jirakit.projects import Projects

        assert isinstance(projects, Projects)
        assert projects.client == client

    def test_screens_factory(self):
        """Test screens() factory method."""
        client = JiraClient("https://test.atlassian.net", "user", "pass")
        screens = client.screens()

        from jirakit.screens import Screens

        assert isinstance(screens, Screens)
        assert screens.client == client

    def test_workflows_factory(self):
        """Test workflows() factory method."""
        client = JiraClient("https://test.atlassian.net", "user", "pass")
        workflows = client.workflows()

        from jirakit.workflows import Workflows

        assert isinstance(workflows, Workflows)
        assert workflows.client == client

    def test_statuses_factory(self):
        """Test statuses() factory method."""
        client = JiraClient("https://test.atlassian.net", "user", "pass")
        statuses = client.statuses()

        from jirakit.workflows.statuses import Statuses

        assert isinstance(statuses, Statuses)
        assert statuses.client == client

    def test_groups_factory(self):
        """Test groups() factory method."""
        client = JiraClient("https://test.atlassian.net", "user", "pass")
        groups = client.groups()

        from jirakit.groups import Groups

        assert isinstance(groups, Groups)
        assert groups.client == client


class TestJiraClientPermissions:
    """Tests for the can_administer() admin-capability probe."""

    @patch("requests.Session.get")
    def test_can_administer_true_when_permission_held(self, mock_get):
        """can_administer returns True when the ADMINISTER flag is set."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "permissions": {"ADMINISTER": {"havePermission": True}}
        }
        mock_get.return_value = mock_response

        client = JiraClient("https://test.atlassian.net", "user", "pass")

        assert client.can_administer() is True
        args, _ = mock_get.call_args
        assert "/rest/api/3/mypermissions" in args[0]
        assert "permissions=ADMINISTER" in args[0]

    @patch("requests.Session.get")
    def test_can_administer_false_when_not_held(self, mock_get):
        """can_administer returns False when the ADMINISTER flag is unset."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "permissions": {"ADMINISTER": {"havePermission": False}}
        }
        mock_get.return_value = mock_response

        client = JiraClient("https://test.atlassian.net", "user", "pass")

        assert client.can_administer() is False
