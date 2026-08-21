"""
Unit tests for reconciling a screen's tabs against a template.

Screen tab membership is what determines whether a field is available on an
issue type: Jira registers a field with a project's issue create metadata when
the field is added to a tab of a screen already wired to that project. Applying
a changed template to a deployed project therefore comes down to making a named
tab exist and carry a given set of fields, without disturbing what is already
there.
"""

import pytest
import requests

from jirakit.screens import Screen


class ScreenApi:
    """
    A stand-in for the screen endpoints, holding tab and field state in memory.

    Requests are recorded so a test can assert that nothing was written, which
    is the whole point of an idempotent reconcile.
    """

    def __init__(self, tabs=None):
        # {tab_id: {"name": str, "fields": [field_id, ...]}}
        self.tabs = dict(tabs or {})
        self.calls = []
        self._next_id = 900

    def _response(self, payload, status_code=200):
        return FakeResponse(payload, status_code)

    def get(self, path=None, **kwargs):
        self.calls.append(f"GET {path}")
        if path.endswith("/tabs"):
            return self._response(
                [{"id": tid, "name": tab["name"]} for tid, tab in self.tabs.items()]
            )
        if path.endswith("/fields"):
            tab_id = path.split("/tabs/")[1].split("/fields")[0]
            return self._response(
                [{"id": f, "name": f} for f in self.tabs[tab_id]["fields"]]
            )
        raise AssertionError(f"unexpected GET {path}")

    def post(self, path=None, data=None, **kwargs):
        self.calls.append(f"POST {path}")
        if path.endswith("/tabs"):
            self._next_id += 1
            tab_id = str(self._next_id)
            self.tabs[tab_id] = {"name": data["name"], "fields": []}
            return self._response({"id": tab_id, "name": data["name"]})
        if path.endswith("/fields"):
            tab_id = path.split("/tabs/")[1].split("/fields")[0]
            self.tabs[tab_id]["fields"].append(data["fieldId"])
            return self._response({})
        raise AssertionError(f"unexpected POST {path}")

    def writes(self):
        return [c for c in self.calls if c.startswith("POST")]

    def fields_on(self, tab_name):
        for tab in self.tabs.values():
            if tab["name"] == tab_name:
                return tab["fields"]
        raise AssertionError(f"no tab named {tab_name}; have {self.tabs}")


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error")


@pytest.fixture
def screen_factory():
    def make(tabs=None):
        api = ScreenApi(tabs)
        screen = Screen({"id": "300", "name": "JK: Incident Screen"}, api)
        return screen, api

    return make


class TestEnsureTab:
    """``ensure_tab`` brings a named tab up to a template's field list."""

    def test_creates_the_tab_when_the_screen_has_none_of_that_name(
        self, screen_factory
    ):
        """A template that gained a tab must be able to add it."""
        screen, api = screen_factory()

        screen.ensure_tab("Details", ["customfield_1", "customfield_2"])

        assert api.fields_on("Details") == ["customfield_1", "customfield_2"]

    def test_reuses_an_existing_tab_of_the_same_name(self, screen_factory):
        """
        Creating a second tab of the same name is what makes apply_template
        unsafe to run twice, so the existing tab must be found and used.
        """
        screen, api = screen_factory({"400": {"name": "Details", "fields": []}})

        screen.ensure_tab("Details", ["customfield_1"])

        assert "POST /rest/api/3/screens/300/tabs" not in api.writes()
        assert len(api.tabs) == 1

    def test_adds_only_the_fields_the_tab_is_missing(self, screen_factory):
        """The common case: a template gained a field since it was deployed."""
        screen, api = screen_factory(
            {"400": {"name": "Details", "fields": ["customfield_1"]}}
        )

        screen.ensure_tab("Details", ["customfield_1", "customfield_2"])

        assert api.fields_on("Details") == ["customfield_1", "customfield_2"]
        assert api.writes() == [
            "POST /rest/api/3/screens/300/tabs/400/fields",
        ]

    def test_writes_nothing_when_the_tab_already_matches(self, screen_factory):
        """Reconciling an up-to-date project must be a no-op, not a rewrite."""
        screen, api = screen_factory(
            {"400": {"name": "Details", "fields": ["customfield_1"]}}
        )

        screen.ensure_tab("Details", ["customfield_1"])

        assert api.writes() == []

    def test_does_not_re_add_a_field_that_sits_on_another_tab(self, screen_factory):
        """
        A field may sit on only one tab per screen, so adding one that is
        already on a sibling tab is refused by Jira. The whole screen is
        checked, as Screen.add_field already does.
        """
        screen, api = screen_factory(
            {
                "400": {"name": "Details", "fields": []},
                "401": {"name": "Other", "fields": ["customfield_1"]},
            }
        )

        screen.ensure_tab("Details", ["customfield_1"])

        assert api.writes() == []
        assert api.fields_on("Other") == ["customfield_1"]

    def test_returns_the_tab(self, screen_factory):
        """Callers record the tab against the project, as create() does."""
        screen, api = screen_factory({"400": {"name": "Details", "fields": []}})

        tab = screen.ensure_tab("Details", [])

        assert tab["id"] == "400"
        assert tab["name"] == "Details"

    def test_reports_the_fields_it_added(self, screen_factory):
        """
        A reconcile has to be able to say what it changed, so the caller can
        report it and a dry run can predict it.
        """
        screen, api = screen_factory(
            {"400": {"name": "Details", "fields": ["customfield_1"]}}
        )

        tab = screen.ensure_tab("Details", ["customfield_1", "customfield_2"])

        assert tab["fields_added"] == ["customfield_2"]
        assert tab["created"] is False


class TestEnsureTabDryRun:
    """A dry run predicts the same changes without writing any of them."""

    def test_predicts_a_tab_creation_without_creating_it(self, screen_factory):
        screen, api = screen_factory()

        tab = screen.ensure_tab("Details", ["customfield_1"], dry_run=True)

        assert api.writes() == []
        assert tab["created"] is True
        assert tab["fields_added"] == ["customfield_1"]

    def test_predicts_the_missing_fields_without_adding_them(self, screen_factory):
        screen, api = screen_factory(
            {"400": {"name": "Details", "fields": ["customfield_1"]}}
        )

        tab = screen.ensure_tab(
            "Details", ["customfield_1", "customfield_2"], dry_run=True
        )

        assert api.writes() == []
        assert tab["fields_added"] == ["customfield_2"]

    def test_predicts_no_change_for_an_up_to_date_tab(self, screen_factory):
        screen, api = screen_factory(
            {"400": {"name": "Details", "fields": ["customfield_1"]}}
        )

        tab = screen.ensure_tab("Details", ["customfield_1"], dry_run=True)

        assert tab["fields_added"] == []
        assert tab["created"] is False
