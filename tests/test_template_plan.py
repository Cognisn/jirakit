"""
Unit tests for reporting what a deployed project is missing from a template.

A service that ships a bundled template and validates it at start-up needs to
say precisely what an administrator must change, rather than failing with a bare
list of field names. Two entry points serve that: ``plan_template``, which is a
full dry run and needs Jira administrator permission to read the screens, and
``missing_template_fields``, which answers the narrower question from issue
create metadata alone and so works for a least-privileged runtime.
"""

import pytest

from tests.fake_jira import FakeClient
from tests.test_template_reconciliation import (
    KEY,
    TEMPLATE,
    with_extra_field,
    with_extra_issue_type,
)
from jirakit.projects import Projects


@pytest.fixture
def deployed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    jira = FakeClient()
    project = Projects(jira).create("Plan Test", KEY, TEMPLATE)
    jira.calls.clear()
    return jira, project


class TestReconcileTemplate:
    """The named entry point for applying a template to an existing project."""

    def test_it_applies_the_difference(self, deployed):
        jira, project = deployed

        Projects(jira).reconcile_template(project, with_extra_field(TEMPLATE))

        tab = jira.tab_named(f"{KEY}: Incident Screen", "Details")
        names = [jira.all_fields[f]["name"] for f in tab["fields"]]
        assert names == ["Severity", "Impact"]

    def test_it_reports_what_it_changed(self, deployed):
        jira, project = deployed

        result = Projects(jira).reconcile_template(
            project, with_extra_field(TEMPLATE)
        )

        assert result.changed is True
        assert any("Impact" in line for line in result.summary())

    def test_it_changes_nothing_on_an_up_to_date_project(self, deployed):
        jira, project = deployed

        result = Projects(jira).reconcile_template(project, TEMPLATE)

        assert result.changed is False
        assert jira.creations() == []


class TestPlanTemplate:
    """A plan is a dry run: it reports the changes and makes none of them."""

    def test_it_writes_nothing(self, deployed):
        jira, project = deployed

        Projects(jira).plan_template(project, with_extra_field(TEMPLATE))

        assert jira.writes() == []

    def test_it_reports_the_change_that_would_be_made(self, deployed):
        jira, project = deployed

        plan = Projects(jira).plan_template(project, with_extra_field(TEMPLATE))

        assert plan.dry_run is True
        assert any("Impact" in line for line in plan.summary())

    def test_two_new_fields_are_both_reported(self, deployed):
        """
        A planned field has no id yet. If they all shared one placeholder they
        would collide when the tab's field list is deduplicated, and the plan
        would under-report what an administrator has to add.
        """
        jira, project = deployed
        changed = dict(TEMPLATE)
        changed["fields"] = TEMPLATE["fields"] + [
            {"name": "Impact", "type": "select", "description": ""},
            {"name": "Urgency", "type": "select", "description": ""},
        ]
        changed["screen_tabs"] = [
            {
                "screen": "Incident Screen",
                "name": "Details",
                "fields": ["Severity", "Impact", "Urgency"],
            }
        ]

        plan = Projects(jira).plan_template(project, changed)

        added = [c for c in plan.changes if c["action"] == "add_fields"]
        assert added and added[0]["fields"] == ["Impact", "Urgency"]

    def test_an_up_to_date_project_plans_no_change(self, deployed):
        jira, project = deployed

        plan = Projects(jira).plan_template(project, TEMPLATE)

        assert plan.changed is False
        assert plan.summary() == []

    def test_the_plan_predicts_what_reconcile_then_does(self, deployed):
        """A plan an operator acts on has to match the apply that follows it."""
        jira, project = deployed
        changed_template = with_extra_issue_type(TEMPLATE)

        planned = Projects(jira).plan_template(project, changed_template).summary()

        jira_two = FakeClient()
        # Re-deploy onto a second site so the apply starts from the same state.
        applied_project = Projects(jira_two).create("Plan Test", KEY, TEMPLATE)
        applied = (
            Projects(jira_two)
            .reconcile_template(applied_project, changed_template)
            .summary()
        )

        assert planned == applied


class TestMissingTemplateFields:
    """
    The least-privileged report: which template fields an issue type's create
    metadata does not carry. Createmeta reads fine without administrator
    permission, while the screen endpoints do not.
    """

    def test_a_correctly_deployed_project_is_missing_nothing(self, deployed):
        jira, project = deployed

        missing = Projects(jira).missing_template_fields(project, TEMPLATE)

        assert missing == {}

    def test_it_names_the_field_and_the_issue_type_missing_it(self, deployed):
        jira, project = deployed

        missing = Projects(jira).missing_template_fields(
            project, with_extra_field(TEMPLATE)
        )

        assert missing == {f"{KEY}: Incident": ["Impact"]}

    def test_it_reads_only_create_metadata(self, deployed):
        """
        The point of this report is that it works for a caller who gets 403 on
        the screen and workflow endpoints, so it must not touch them.
        """
        jira, project = deployed

        Projects(jira).missing_template_fields(project, with_extra_field(TEMPLATE))

        assert jira.writes() == []
        assert all("/issue/createmeta/" in call for call in jira.calls), jira.calls

    def test_reconciling_makes_the_report_come_back_clean(self, deployed):
        """
        The report is derived from screen tab membership, as Jira derives
        createmeta, so a reconcile that fixes the tabs must clear it.
        """
        jira, project = deployed
        changed = with_extra_field(TEMPLATE)

        assert Projects(jira).missing_template_fields(project, changed)

        Projects(jira).reconcile_template(project, changed)

        assert Projects(jira).missing_template_fields(project, changed) == {}
