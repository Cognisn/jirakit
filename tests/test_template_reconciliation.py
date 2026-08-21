"""
Unit tests for applying a template to a project it has already been deployed to.

``apply_template`` could previously only build a project from scratch: every
step created unconditionally, so running it twice duplicated issue types,
screens and tabs, and a template that gained a field had to be reproduced by
hand in the Jira UI. These tests run it against stateful in-memory Jira, so
"applying it twice is safe" is demonstrated rather than asserted.
"""

import pytest

from tests.fake_jira import FakeClient
from jirakit.projects import Projects

KEY = "JK"

TEMPLATE = {
    "name": "reconciliation test template",
    "description": "Screens, tabs, schemes and wiring",
    "groups": ["jk-users"],
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


def with_extra_field(template):
    """The template as it looks after gaining a field: the reported case."""
    changed = {k: (list(v) if isinstance(v, list) else v) for k, v in template.items()}
    changed["fields"] = template["fields"] + [
        {"name": "Impact", "type": "select", "description": ""}
    ]
    changed["screen_tabs"] = [
        {
            "screen": "Incident Screen",
            "name": "Details",
            "fields": ["Severity", "Impact"],
        }
    ]
    return changed


def with_extra_issue_type(template):
    changed = dict(template)
    changed["issue_types"] = template["issue_types"] + [
        {"name": "Problem", "description": "A problem", "subtask": False}
    ]
    return changed


@pytest.fixture
def deployed(tmp_path, monkeypatch):
    """A project deployed from TEMPLATE, and the site it was deployed onto."""
    monkeypatch.chdir(tmp_path)
    jira = FakeClient()
    project = Projects(jira).create("Reconciliation Test", KEY, TEMPLATE)
    jira.calls.clear()
    return jira, project


class TestApplyTemplateIsIdempotent:
    """Running the same template twice must be a no-op, not a duplication."""

    def test_the_second_run_creates_nothing(self, deployed):
        jira, project = deployed

        Projects(jira).apply_template(project, TEMPLATE)

        assert jira.creations() == []

    def test_the_second_run_leaves_one_screen_and_one_tab(self, deployed):
        jira, project = deployed

        Projects(jira).apply_template(project, TEMPLATE)

        assert len(jira.named(jira.all_screens, f"{KEY}: Incident Screen")) == 1
        tab = jira.tab_named(f"{KEY}: Incident Screen", "Details")
        assert len(tab["fields"]) == 1

    def test_the_second_run_leaves_one_issue_type(self, deployed):
        jira, project = deployed

        Projects(jira).apply_template(project, TEMPLATE)

        assert len(jira.named(jira.all_issue_types, f"{KEY}: Incident")) == 1

    def test_the_second_run_reports_no_changes(self, deployed):
        jira, project = deployed

        result = Projects(jira).apply_template(project, TEMPLATE)

        assert result.changes == []


class TestApplyTemplateReconciles:
    """A template that has moved on must be applied to the deployed project."""

    def test_a_field_added_to_the_template_reaches_the_tab(self, deployed):
        """
        The reported case: a bundled template gains a field, existing projects
        fail validation, and there is no code path to bring them up to date.
        """
        jira, project = deployed

        Projects(jira).apply_template(project, with_extra_field(TEMPLATE))

        tab = jira.tab_named(f"{KEY}: Incident Screen", "Details")
        names = [jira.all_fields[f]["name"] for f in tab["fields"]]
        assert names == ["Severity", "Impact"]

    def test_the_added_field_is_the_only_thing_created(self, deployed):
        jira, project = deployed

        Projects(jira).apply_template(project, with_extra_field(TEMPLATE))

        assert "POST /rest/api/3/screens" not in jira.creations()
        assert "POST /rest/api/3/issuetype" not in jira.creations()

    def test_an_issue_type_added_to_the_template_is_created(self, deployed):
        jira, project = deployed

        Projects(jira).apply_template(project, with_extra_issue_type(TEMPLATE))

        assert len(jira.named(jira.all_issue_types, f"{KEY}: Problem")) == 1
        assert len(jira.named(jira.all_issue_types, f"{KEY}: Incident")) == 1

    def test_the_changes_name_what_was_done(self, deployed):
        jira, project = deployed

        result = Projects(jira).apply_template(project, with_extra_field(TEMPLATE))

        assert any(
            c["type"] == "field" and c["name"] == "Impact" for c in result.changes
        )


class TestApplyTemplateDryRun:
    """A dry run reports what would change and changes nothing."""

    def test_it_writes_nothing(self, deployed):
        jira, project = deployed

        Projects(jira).apply_template(
            project, with_extra_field(TEMPLATE), dry_run=True
        )

        assert jira.writes() == []

    def test_it_reports_the_field_that_would_be_added(self, deployed):
        jira, project = deployed

        result = Projects(jira).apply_template(
            project, with_extra_field(TEMPLATE), dry_run=True
        )

        assert result.dry_run is True
        assert any(c["name"] == "Impact" for c in result.changes)

    def test_an_up_to_date_project_reports_no_changes(self, deployed):
        jira, project = deployed

        result = Projects(jira).apply_template(project, TEMPLATE, dry_run=True)

        assert result.changes == []
        assert result.changed is False


class TestCreateStillWorks:
    """create() now runs through apply_template, so its behaviour is retested."""

    def test_it_deploys_the_whole_template(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        jira = FakeClient()

        Projects(jira).create("Reconciliation Test", KEY, TEMPLATE)

        assert jira.project["key"] == KEY
        assert jira.named(jira.all_issue_types, f"{KEY}: Incident")
        assert jira.named(jira.all_screens, f"{KEY}: Incident Screen")
        assert jira.named(jira.screen_schemes, f"{KEY}: Incident Screen Scheme")
        assert jira.tab_named(f"{KEY}: Incident Screen", "Details")["fields"]

    def test_it_wires_the_project_before_populating_tabs(self, tmp_path, monkeypatch):
        """
        Jira registers a field with createmeta on the tab-membership change, but
        only for a screen already wired to a project (issue #5). The unification
        must not reintroduce the old ordering.
        """
        monkeypatch.chdir(tmp_path)
        jira = FakeClient()

        Projects(jira).create("Reconciliation Test", KEY, TEMPLATE)

        wiring = jira.calls.index("PUT /rest/api/3/issuetypescreenscheme/project")
        field_adds = [
            i
            for i, c in enumerate(jira.calls)
            if c.startswith("POST") and "/tabs/" in c and c.endswith("/fields")
        ]
        assert field_adds and min(field_adds) > wiring

    def test_it_tracks_what_it_created_for_rollback(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        jira = FakeClient()

        Projects(jira).create("Reconciliation Test", KEY, TEMPLATE)

        tracking = list((tmp_path / ".jirakit_deployments").glob("*.json"))
        assert len(tracking) == 1
        import json

        record = json.loads(tracking[0].read_text())
        resources = record["resources_created"]
        assert resources["issue_types"]
        assert resources["screens"]
        assert resources["screen_schemes"]
        assert resources["issue_type_screen_schemes"]
