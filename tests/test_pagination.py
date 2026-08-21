"""
Unit tests for the paginated list helpers shared across the package.

Every "get all" helper walks Jira's paginated endpoints with the same loop. Two
properties of that loop are the behaviour under test:

* the HTTP status is checked before the body is parsed, so an authentication,
  permission or rate-limit failure surfaces as an ``HTTPError`` naming the
  status and URL rather than a ``JSONDecodeError`` from deep inside the loop;
* the loop terminates on any response shape, including one that carries no
  ``isLast`` key, rather than advancing ``startAt`` indefinitely.

``Fields.get_all`` already had both properties and is included to keep it that
way.
"""

import json
from unittest.mock import Mock

import pytest
import requests

from jirakit.fields import Fields
from jirakit.groups import Groups
from jirakit.issues.types import IssueTypes
from jirakit.projects import Projects
from jirakit.screens import Screens
from jirakit.workflows import Workflows
from jirakit.workflows.statuses import Statuses

# A correct helper asks for exactly one page of a single-page body. Anything
# beyond this is the runaway loop, not slow progress.
PAGE_LIMIT = 5

UNAUTHENTICATED_BODY = "Client must be authenticated to access this resource."


class FakeResponse:
    """
    A response that behaves like Jira's, including its non-JSON error bodies.

    Jira Cloud answers 401 with ``Content-Type: application/json`` and a
    plain-text body, so ``json()`` raises where a caller might reasonably
    expect it to succeed.
    """

    def __init__(self, body, status_code=200, url="https://test.atlassian.net/rest/api/3/x"):
        self._body = body
        self.status_code = status_code
        self.url = url
        self.text = body if isinstance(body, str) else json.dumps(body)
        self.json_calls = 0

    def json(self):
        self.json_calls += 1
        if isinstance(self._body, str):
            raise requests.exceptions.JSONDecodeError("Expecting value", self._body, 0)
        return self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(
                f"{self.status_code} Client Error: for url: {self.url}", response=self
            )


class PagingClient:
    """
    A client that answers every GET identically and refuses to be asked forever.

    The refusal is what makes the unbounded loop observable: a helper that never
    terminates raises ``RuntimeError`` here instead of hanging the suite.
    """

    def __init__(self, response_factory, limit=PAGE_LIMIT):
        self.response_factory = response_factory
        self.limit = limit
        self.responses = []

    def get(self, path=None, *args, **kwargs):
        if len(self.responses) >= self.limit:
            raise RuntimeError(
                f"pagination did not terminate: {self.limit} pages requested"
            )
        response = self.response_factory()
        self.responses.append(response)
        return response


def project_stub():
    """The minimum a project needs to be for the helpers that take one."""
    project = Mock()
    project.id = "10000"
    project.key = "JK"
    return project


PAGINATED_HELPERS = [
    ("Fields.get_all", lambda c: Fields(c).get_all()),
    ("Groups.get_groups", lambda c: Groups(c).get_groups()),
    (
        "IssueTypes.get_all_issue_type_schemes",
        lambda c: IssueTypes(c).get_all_issue_type_schemes(),
    ),
    (
        "IssueTypes.get_all_issue_type_schemes_for_project",
        lambda c: IssueTypes(c).get_all_issue_type_schemes_for_project(project_stub()),
    ),
    (
        "IssueTypes.get_all_issue_type_screen_schemes",
        lambda c: IssueTypes(c).get_all_issue_type_screen_schemes(),
    ),
    ("Projects.get_all", lambda c: Projects(c).get_all()),
    ("Screens.get_all_screen_schemes", lambda c: Screens(c).get_all_screen_schemes()),
    ("Screens.get_all_screens", lambda c: Screens(c).get_all_screens()),
    ("Statuses.get_all", lambda c: Statuses(c).get_all()),
    ("Workflows.get_all", lambda c: Workflows(c).get_all()),
    (
        "Workflows.get_all_workflow_schemes",
        lambda c: Workflows(c).get_all_workflow_schemes(),
    ),
]

HELPER_IDS = [name for name, _ in PAGINATED_HELPERS]


@pytest.mark.parametrize("name,invoke", PAGINATED_HELPERS, ids=HELPER_IDS)
class TestPaginatedHelpers:
    """The properties every paginated helper is expected to share."""

    def test_an_authentication_failure_raises_http_error(self, name, invoke):
        """
        A 401 must name itself. Parsing the body first turns an authentication
        failure into a JSONDecodeError with nothing in the traceback pointing at
        the credentials.
        """
        client = PagingClient(
            lambda: FakeResponse(UNAUTHENTICATED_BODY, status_code=401)
        )

        with pytest.raises(requests.HTTPError):
            invoke(client)

    def test_a_permission_failure_raises_http_error(self, name, invoke):
        """
        403 is the likelier failure in practice: the admin-only endpoints refuse
        a service account that can otherwise use the site perfectly well.
        """
        client = PagingClient(
            lambda: FakeResponse({"errorMessages": ["Forbidden"]}, status_code=403)
        )

        with pytest.raises(requests.HTTPError):
            invoke(client)

    def test_a_rate_limit_raises_http_error(self, name, invoke):
        """429 must surface as itself so a caller can back off."""
        client = PagingClient(lambda: FakeResponse({}, status_code=429))

        with pytest.raises(requests.HTTPError):
            invoke(client)

    def test_a_response_without_is_last_terminates_the_loop(self, name, invoke):
        """
        An absent ``isLast`` must stop the walk. Treating it as falsy advances
        ``startAt`` forever, turning one call into an unbounded request flood
        against the Atlassian API.
        """
        client = PagingClient(lambda: FakeResponse({"values": []}))

        assert invoke(client) == []
        assert len(client.responses) == 1

    def test_each_page_is_parsed_once(self, name, invoke):
        """Parsing the same body twice per page doubles the work for nothing."""
        client = PagingClient(lambda: FakeResponse({"isLast": True, "values": []}))

        invoke(client)

        assert client.responses[0].json_calls == 1

    def test_a_successful_page_is_still_walked(self, name, invoke):
        """The guards must not stop a well-formed response being read."""
        client = PagingClient(lambda: FakeResponse({"isLast": True, "values": []}))

        assert invoke(client) == []
        assert len(client.responses) == 1
