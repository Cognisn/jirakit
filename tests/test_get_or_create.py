"""
Unit tests for the get-or-create helpers behind template reconciliation.

Applying a template to a project it has already been applied to must adopt the
resources that are there rather than creating a second one of each. Every
``ensure_*`` helper looks the resource up by the name the deployment gives it
(``<KEY>: <template name>``), creates it only if it is absent, and reports which
of the two happened so the caller can track and report the change.

A dry run answers the same question without writing anything. A resource that
would be created has no id yet, so it is reported with ``id`` of None.
"""

import pytest
import requests

from jirakit.issues.types import IssueTypes, IssueTypeScheme, IssueTypeScreenScheme
from jirakit.screens import Screens, ScreenScheme


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error")


class RecordingClient:
    """Answers the list endpoints from a fixed inventory and records writes."""

    def __init__(self, inventory=None):
        self.inventory = inventory or {}
        self.calls = []
        self._next_id = 500

    def _list(self, key):
        return self.inventory.get(key, [])

    def get(self, path=None, **kwargs):
        self.calls.append(f"GET {path}")
        if path.startswith("/rest/api/3/issuetype?") or path == "/rest/api/3/issuetype":
            return FakeResponse(self._list("issue_types"))
        for endpoint, key in (
            ("/rest/api/3/issuetypescreenscheme", "issue_type_screen_schemes"),
            ("/rest/api/3/issuetypescheme", "issue_type_schemes"),
            ("/rest/api/3/screenscheme", "screen_schemes"),
            ("/rest/api/3/screens", "screens"),
        ):
            if path.startswith(endpoint):
                return FakeResponse({"isLast": True, "values": self._list(key)})
        raise AssertionError(f"unexpected GET {path}")

    def post(self, path=None, data=None, **kwargs):
        self.calls.append(f"POST {path}")
        self._next_id += 1
        record = {"id": str(self._next_id), **(data or {})}
        # create_screen_scheme reads the scheme back by id after creating it,
        # so the inventory has to reflect the write.
        if path == "/rest/api/3/screenscheme":
            self.inventory.setdefault("screen_schemes", []).append(record)
        return FakeResponse(record, 201)

    def writes(self):
        return [c for c in self.calls if c.startswith("POST")]


NAME = "JK: Incident"


class TestIssueTypeGetOrCreate:
    def test_creates_the_issue_type_when_it_is_absent(self):
        client = RecordingClient()

        issue_type, created = IssueTypes(client).ensure(NAME, "An incident", False)

        assert created is True
        assert issue_type.name == NAME
        assert "POST /rest/api/3/issuetype" in client.writes()

    def test_adopts_an_existing_issue_type_of_the_same_name(self):
        """Creating a second issue type of the same name is what fails today."""
        client = RecordingClient(
            {"issue_types": [{"id": "10100", "name": NAME, "description": "x"}]}
        )

        issue_type, created = IssueTypes(client).ensure(NAME, "An incident", False)

        assert created is False
        assert issue_type.id == "10100"
        assert client.writes() == []

    def test_a_dry_run_creates_nothing(self):
        client = RecordingClient()

        issue_type, created = IssueTypes(client).ensure(
            NAME, "An incident", False, dry_run=True
        )

        assert created is True
        assert issue_type.id is None
        assert client.writes() == []

    def test_a_dry_run_reports_an_existing_issue_type_as_unchanged(self):
        client = RecordingClient(
            {"issue_types": [{"id": "10100", "name": NAME, "description": "x"}]}
        )

        issue_type, created = IssueTypes(client).ensure(
            NAME, "An incident", False, dry_run=True
        )

        assert created is False
        assert issue_type.id == "10100"


class TestScreenGetOrCreate:
    def test_creates_the_screen_when_it_is_absent(self):
        client = RecordingClient()

        screen, created = Screens(client).ensure("JK: Incident Screen", "")

        assert created is True
        assert "POST /rest/api/3/screens" in client.writes()

    def test_adopts_an_existing_screen_of_the_same_name(self):
        client = RecordingClient(
            {"screens": [{"id": "10300", "name": "JK: Incident Screen"}]}
        )

        screen, created = Screens(client).ensure("JK: Incident Screen", "")

        assert created is False
        assert screen.id == "10300"
        assert client.writes() == []

    def test_a_dry_run_creates_nothing(self):
        client = RecordingClient()

        screen, created = Screens(client).ensure(
            "JK: Incident Screen", "", dry_run=True
        )

        assert created is True
        assert screen.id is None
        assert client.writes() == []


class TestScreenSchemeGetOrCreate:
    def test_creates_the_screen_scheme_when_it_is_absent(self):
        client = RecordingClient()

        scheme, created = Screens(client).ensure_screen_scheme(
            "JK: Incident Screen Scheme", "", "10300", "10300", "10300"
        )

        assert created is True
        assert "POST /rest/api/3/screenscheme" in client.writes()

    def test_adopts_an_existing_screen_scheme_of_the_same_name(self):
        client = RecordingClient(
            {
                "screen_schemes": [
                    {"id": "10500", "name": "JK: Incident Screen Scheme"}
                ]
            }
        )

        scheme, created = Screens(client).ensure_screen_scheme(
            "JK: Incident Screen Scheme", "", "10300", "10300", "10300"
        )

        assert created is False
        assert scheme.id == "10500"
        assert client.writes() == []


class TestIssueTypeSchemeGetOrCreate:
    def test_creates_the_issue_type_scheme_when_it_is_absent(self):
        client = RecordingClient()

        scheme, created = IssueTypes(client).ensure_issue_type_scheme(
            "JK: Incident Issue Type Scheme", "", ["10100"]
        )

        assert created is True
        assert "POST /rest/api/3/issuetypescheme" in client.writes()

    def test_adopts_an_existing_issue_type_scheme_of_the_same_name(self):
        client = RecordingClient(
            {
                "issue_type_schemes": [
                    {"id": "10200", "name": "JK: Incident Issue Type Scheme"}
                ]
            }
        )

        scheme, created = IssueTypes(client).ensure_issue_type_scheme(
            "JK: Incident Issue Type Scheme", "", ["10100"]
        )

        assert created is False
        assert scheme.id == "10200"
        assert client.writes() == []


class TestIssueTypeScreenSchemeGetOrCreate:
    def test_creates_the_issue_type_screen_scheme_when_it_is_absent(self):
        client = RecordingClient()

        scheme, created = IssueTypes(client).ensure_issue_type_screen_scheme(
            "JK: Incident ITSS", "", [{"issueTypeId": "default", "screenSchemeId": "1"}]
        )

        assert created is True
        assert "POST /rest/api/3/issuetypescreenscheme" in client.writes()

    def test_adopts_an_existing_issue_type_screen_scheme_of_the_same_name(self):
        client = RecordingClient(
            {"issue_type_screen_schemes": [{"id": "10600", "name": "JK: Incident ITSS"}]}
        )

        scheme, created = IssueTypes(client).ensure_issue_type_screen_scheme(
            "JK: Incident ITSS", "", [{"issueTypeId": "default", "screenSchemeId": "1"}]
        )

        assert created is False
        assert scheme.id == "10600"
        assert client.writes() == []


class TestSchemeNames:
    """The lookups match on name, so the scheme classes have to expose one."""

    def test_issue_type_scheme_exposes_its_name(self):
        scheme = IssueTypeScheme({"id": "10200", "name": "JK: Scheme"}, None)

        assert scheme.name == "JK: Scheme"

    def test_issue_type_screen_scheme_exposes_its_name(self):
        scheme = IssueTypeScreenScheme({"id": "10600", "name": "JK: ITSS"}, None)

        assert scheme.name == "JK: ITSS"

    def test_issue_type_screen_scheme_name_handles_the_nested_shape(self):
        """
        The id property already copes with the nested 'issueTypeScreenScheme'
        envelope some responses use, and the name has to do the same.
        """
        scheme = IssueTypeScreenScheme(
            {"issueTypeScreenScheme": {"id": "10600", "name": "JK: ITSS"}}, None
        )

        assert scheme.name == "JK: ITSS"
