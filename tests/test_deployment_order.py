"""
Unit tests for the order in which Projects.create wires a deployment together.

Jira registers a screen's fields with its issue create metadata when the field
is added to a tab of a screen that is already wired to a project. Adding fields
first and wiring afterwards leaves them permanently invisible to createmeta, so
the order these requests are issued in is the behaviour under test.
"""

import pytest
from unittest.mock import Mock

from jirakit.fields import Field
from jirakit.issues.types import IssueTypes
from jirakit.projects import Projects
from jirakit.screens import Screens

KEY = "JK"

WIRE_PROJECT = "PUT /rest/api/3/issuetypescreenscheme/project"

TEMPLATE = {
    "name": "ordering test template",
    "description": "Minimal template covering screens, tabs and wiring",
    "groups": [],
    "fields": [{"name": "Severity", "type": "select", "description": ""}],
    "issue_types": [
        {"name": "Incident", "description": "An incident", "subtask": False}
    ],
    "issue_type_schemes": [
        {
            "name": "Incident Issue Type Scheme",
            "description": "",
            "issue_types": ["Incident"],
        }
    ],
    "screens": [{"name": "Incident Screen", "description": ""}],
    "screen_tabs": [
        {"screen": "Incident Screen", "name": "Details", "fields": ["Severity"]}
    ],
    "screen_schemes": [
        {
            "name": "Incident Screen Scheme",
            "description": "",
            "screens": {"default": "Incident Screen"},
        }
    ],
    "issue_type_screen_schemes": [
        {
            "name": "Incident Issue Type Screen Scheme",
            "description": "",
            "default_screen_scheme": "Incident Screen Scheme",
            "mappings": [
                {"issue_type": "Incident", "screen_scheme": "Incident Screen Scheme"}
            ],
        }
    ],
}


class CallRecorder:
    """Records every request jirakit makes, in order, and answers them."""

    def __init__(self):
        self.calls = []

    def _record(self, method, path):
        self.calls.append(f"{method} {path}")

    def _response(self, payload):
        response = Mock()
        response.status_code = 201
        response.raise_for_status = Mock()
        response.json.return_value = payload
        return response

    def post(self, path=None, data=None, **kwargs):
        self._record("POST", path)

        if path == "/rest/api/3/project":
            return self._response({"id": "10000", "key": KEY, "name": "Ordering Test"})
        if path == "/rest/api/3/issuetype":
            return self._response({"id": "10100", "name": data["name"]})
        if path == "/rest/api/3/issuetypescheme":
            return self._response({"issueTypeSchemeId": "10200"})
        if path == "/rest/api/3/screens":
            return self._response({"id": "10300", "name": data["name"]})
        if path.endswith("/tabs"):
            return self._response({"id": "10400", "name": data["name"]})
        if path.endswith("/fields"):
            return self._response({})
        if path == "/rest/api/3/screenscheme":
            return self._response({"id": "10500", "name": data["name"]})
        if path == "/rest/api/3/issuetypescreenscheme":
            return self._response({"id": "10600", "name": data["name"]})

        return self._response({})

    def put(self, path=None, data=None, **kwargs):
        self._record("PUT", path)
        return self._response({})

    def get(self, path=None, **kwargs):
        self._record("GET", path)

        # Endpoints that return a bare array rather than a paginated envelope.
        if path.startswith("/rest/api/3/issuetype/project") or path.endswith("/fields"):
            return self._response([])

        # Reading back a resource that has just been created, by id.
        if path.startswith("/rest/api/3/screenscheme?id="):
            return self._response(
                {
                    "isLast": True,
                    "values": [
                        {"id": "10500", "name": f"{KEY}: Incident Screen Scheme"}
                    ],
                }
            )
        if path.startswith("/rest/api/3/screens?id="):
            return self._response(
                {
                    "isLast": True,
                    "values": [{"id": "10300", "name": f"{KEY}: Incident Screen"}],
                }
            )

        return self._response({"isLast": True, "values": [], "total": 0})

    def delete(self, path=None, **kwargs):
        self._record("DELETE", path)
        return self._response({})

    def index(self, call):
        assert call in self.calls, f"{call} never happened; calls were {self.calls}"
        return self.calls.index(call)

    def indices(self, predicate):
        return [i for i, call in enumerate(self.calls) if predicate(call)]


def adds_a_field_to_a_tab(call):
    """A POST that puts a field onto a screen tab."""
    return call.startswith("POST") and "/tabs/" in call and call.endswith("/fields")


@pytest.fixture
def recorder(mock_client):
    """Wire mock_client with real managers over a recording HTTP layer."""
    calls = CallRecorder()

    mock_client.post.side_effect = calls.post
    mock_client.put.side_effect = calls.put
    mock_client.get.side_effect = calls.get
    mock_client.delete.side_effect = calls.delete

    mock_client.get_me.return_value = {
        "accountId": "account-1",
        "emailAddress": "test@example.com",
    }
    mock_client.issue_types.return_value = IssueTypes(mock_client)
    mock_client.screens.return_value = Screens(mock_client)

    groups = Mock()
    groups.create_groups = Mock()
    mock_client.groups.return_value = groups

    fields = Mock()
    fields.get_custom_field.return_value = Field(
        {"id": "customfield_10050", "name": "Severity"}, mock_client
    )
    mock_client.fields.return_value = fields

    return calls


@pytest.fixture
def projects(mock_client, recorder, tmp_path, monkeypatch):
    """Projects with the deployment tracker writing into a temporary directory."""
    monkeypatch.chdir(tmp_path)
    return Projects(mock_client)


MAP_SCREEN_SCHEME = "PUT /rest/api/3/issuetypescreenscheme/10600/mapping"


@pytest.fixture
def existing_project(mock_client):
    """
    A project that already exists, as apply_template expects: it carries the
    issue type scheme and issue type screen scheme the template is applied into.
    """
    from jirakit.issues.types import IssueTypeScheme, IssueTypeScreenScheme
    from jirakit.projects import Project

    project = Project({"id": "10000", "key": KEY, "name": "Existing"}, mock_client, skip_load=True)
    project.project_fields = [
        Field({"id": "customfield_10050", "name": "Severity"}, mock_client)
    ]
    project.issue_type_schemes = [
        IssueTypeScheme({"id": "10200", "name": "Scheme", "isDefault": False}, mock_client)
    ]
    project.issue_type_screen_schemes = [
        IssueTypeScreenScheme({"id": "10600", "name": "ITSS"}, mock_client)
    ]
    return project


class TestApplyTemplateOrder:
    """apply_template wires an existing project and has the same constraint."""

    def test_fields_are_added_to_tabs_after_the_screen_scheme_is_mapped(
        self, mock_client, recorder, existing_project
    ):
        """
        The new screen only becomes part of the project when its screen scheme is
        mapped into the project's issue type screen scheme. Adding fields to the
        tabs before that leaves them invisible to createmeta, exactly as in
        Projects.create.
        """
        Projects(mock_client).apply_template(existing_project, TEMPLATE)

        field_adds = recorder.indices(adds_a_field_to_a_tab)

        assert field_adds, "no field was added to a tab"
        assert min(field_adds) > recorder.index(MAP_SCREEN_SCHEME)


class TestDeploymentOrder:
    """Ordering decides whether Jira ever learns about the deployed fields."""

    def test_fields_are_added_to_tabs_after_the_project_is_wired(
        self, projects, recorder
    ):
        """
        Jira registers a field with createmeta on the tab-membership change, but
        only for a screen already wired to a project. Adding fields before the
        issue type screen scheme is assigned leaves them invisible to createmeta
        for good, so no deployed custom field can be set on an issue.
        """
        projects.create("Ordering Test", KEY, TEMPLATE)

        field_adds = recorder.indices(adds_a_field_to_a_tab)

        assert field_adds, "no field was added to a tab"
        assert min(field_adds) > recorder.index(WIRE_PROJECT)

    def test_the_deployed_field_still_reaches_its_tab(self, projects, recorder):
        """Reordering must not drop the field placement it is reordering."""
        projects.create("Ordering Test", KEY, TEMPLATE)

        assert "POST /rest/api/3/screens/10300/tabs/10400/fields" in recorder.calls

    def test_screens_and_schemes_are_still_created_before_the_wiring(
        self, projects, recorder
    ):
        """The wiring depends on them, so they cannot move after it."""
        projects.create("Ordering Test", KEY, TEMPLATE)

        wiring = recorder.index(WIRE_PROJECT)

        assert recorder.index("POST /rest/api/3/screens") < wiring
        assert recorder.index("POST /rest/api/3/screenscheme") < wiring
        assert recorder.index("POST /rest/api/3/issuetypescreenscheme") < wiring
