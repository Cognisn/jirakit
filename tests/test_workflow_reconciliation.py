"""
Unit tests for reconciling a workflow on an already-deployed project.

Workflow reconciliation is deliberately opt-in. Jira Cloud's workflow update
endpoint replaces a whole workflow definition, so applying it to a workflow
carrying live issues is a materially different risk from adding a field to a
screen. Reconciling a template therefore leaves an existing workflow alone and
says so, unless the caller asks for it.
"""

import pytest

from tests.fake_jira import FakeClient
from tests.test_template_reconciliation import KEY, TEMPLATE
from jirakit.projects import Projects

WORKFLOW_TEMPLATE = dict(TEMPLATE)
WORKFLOW_TEMPLATE["workflows"] = [
    {
        "name": "Incident Workflow",
        "description": "Incident handling",
        "statuses": [
            {"name": "Open", "type": "TODO"},
            {"name": "Resolved", "type": "DONE"},
        ],
        "transitions": [
            {"name": "Start", "type": "INITIAL", "to": "Open"},
            {"name": "Resolve", "type": "DIRECTED", "from": ["Open"], "to": "Resolved"},
        ],
    }
]
WORKFLOW_TEMPLATE["workflow_schemes"] = [
    {
        "name": "Incident Workflow Scheme",
        "description": "",
        "defaultWorkflow": "jira",
        "issueTypeMappings": [
            {"issue_type": "Incident", "workflow": "Incident Workflow"}
        ],
    }
]


def with_extra_transition(template):
    changed = dict(template)
    workflow = dict(template["workflows"][0])
    workflow["statuses"] = template["workflows"][0]["statuses"] + [
        {"name": "Closed", "type": "DONE"}
    ]
    workflow["transitions"] = template["workflows"][0]["transitions"] + [
        {"name": "Close", "type": "DIRECTED", "from": ["Resolved"], "to": "Closed"}
    ]
    changed["workflows"] = [workflow]
    return changed


@pytest.fixture
def deployed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    jira = FakeClient()
    project = Projects(jira).create("Workflow Test", KEY, WORKFLOW_TEMPLATE)
    jira.calls.clear()
    return jira, project


class TestWorkflowsAreLeftAloneByDefault:
    """The safe default: an existing workflow is not touched."""

    def test_a_second_run_does_not_create_a_second_workflow(self, deployed):
        jira, project = deployed

        Projects(jira).reconcile_template(project, WORKFLOW_TEMPLATE)

        assert len(jira.named(jira.all_workflows, f"{KEY}: Incident Workflow")) == 1

    def test_a_changed_workflow_is_not_updated(self, deployed):
        jira, project = deployed

        Projects(jira).reconcile_template(project, with_extra_transition(WORKFLOW_TEMPLATE))

        assert "POST /rest/api/3/workflows/update" not in jira.calls

    def test_it_reports_the_workflow_it_skipped_and_why(self, deployed):
        """
        Silence would be wrong here: the operator has to know the workflow was
        left behind, or they will believe the project matches the template.
        """
        jira, project = deployed

        result = Projects(jira).reconcile_template(
            project, with_extra_transition(WORKFLOW_TEMPLATE)
        )

        skipped = [c for c in result.changes if c["action"] == "skip"]
        assert skipped and skipped[0]["type"] == "workflow"
        assert skipped[0]["name"] == f"{KEY}: Incident Workflow"
        assert "reconcile_workflows" in skipped[0]["reason"]


class TestWorkflowsAreReconciledOnRequest:
    """With the flag, an existing workflow is brought up to the definition."""

    def test_it_updates_the_existing_workflow(self, deployed):
        jira, project = deployed

        Projects(jira).reconcile_template(
            project, with_extra_transition(WORKFLOW_TEMPLATE), reconcile_workflows=True
        )

        assert "POST /rest/api/3/workflows/update" in jira.calls
        assert len(jira.named(jira.all_workflows, f"{KEY}: Incident Workflow")) == 1

    def test_the_update_carries_the_workflows_current_version(self, deployed):
        """
        The update endpoint takes a version for optimistic locking; without it
        the request is rejected, and with a stale one it would clobber a
        concurrent edit.
        """
        jira, project = deployed
        before = dict(next(iter(jira.workflow_versions.values())))

        Projects(jira).reconcile_template(
            project, with_extra_transition(WORKFLOW_TEMPLATE), reconcile_workflows=True
        )

        # The fake rejects an update carrying no version or a stale one, as the
        # real endpoint does, so reaching a new version number proves the
        # payload carried the current one.
        after = next(iter(jira.workflow_versions.values()))
        assert after["versionNumber"] == before["versionNumber"] + 1
        assert "POST /rest/api/3/workflows" in jira.calls, "version was never read"

    def test_the_update_is_validated_first(self, deployed):
        """As creation is, so a bad definition raises rather than 400ing."""
        jira, project = deployed

        Projects(jira).reconcile_template(
            project, with_extra_transition(WORKFLOW_TEMPLATE), reconcile_workflows=True
        )

        assert jira.calls.index(
            "POST /rest/api/3/workflows/update/validation"
        ) < jira.calls.index("POST /rest/api/3/workflows/update")

    def test_it_reports_the_update(self, deployed):
        jira, project = deployed

        result = Projects(jira).reconcile_template(
            project, with_extra_transition(WORKFLOW_TEMPLATE), reconcile_workflows=True
        )

        updates = [
            c
            for c in result.changes
            if c["type"] == "workflow" and c["action"] == "update"
        ]
        assert updates and updates[0]["name"] == f"{KEY}: Incident Workflow"

    def test_the_new_transition_reaches_the_workflow(self, deployed):
        jira, project = deployed

        Projects(jira).reconcile_template(
            project, with_extra_transition(WORKFLOW_TEMPLATE), reconcile_workflows=True
        )

        workflow = jira.named(jira.all_workflows, f"{KEY}: Incident Workflow")[0]
        names = [t["name"] for t in workflow["transitions"]]
        assert "Close" in names


class TestWorkflowsStillGetCreated:
    """A workflow the project does not have is created either way."""

    def test_an_absent_workflow_is_created_without_the_flag(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        jira = FakeClient()

        Projects(jira).create("Workflow Test", KEY, WORKFLOW_TEMPLATE)

        assert jira.named(jira.all_workflows, f"{KEY}: Incident Workflow")


class TestWorkflowDryRun:
    """A dry run reports the workflow decision without acting on it."""

    def test_it_reports_the_update_without_making_it(self, deployed):
        jira, project = deployed

        result = Projects(jira).plan_template(
            project, with_extra_transition(WORKFLOW_TEMPLATE)
        )

        assert jira.writes() == []
        assert any(c["type"] == "workflow" for c in result.changes)
