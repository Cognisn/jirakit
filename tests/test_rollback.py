"""
Unit tests for Projects.rollback_template_deployment.

Rollback drives real manager classes over a mocked HTTP layer, so these tests
assert the DELETE paths jirakit issues and the order it issues them in, which is
what determines whether Jira accepts the deletions.
"""

import os

import pytest
from unittest.mock import Mock

from jirakit.issues.types import IssueTypes
from jirakit.projects import Projects
from jirakit.projects.tracking import DeploymentTracker
from jirakit.screens import Screens
from jirakit.workflows import Workflows

KEY = "JKTEST"

PROJECT_PATH = "/rest/api/3/project/10002?enableUndo=False"
WORKFLOW_SCHEME_PATH = "/rest/api/3/workflowscheme/10004"
ITSS_PATH = "/rest/api/3/issuetypescreenscheme/10004"
SCREEN_SCHEME_PATH = "/rest/api/3/screenscheme/10013"
SCREEN_PATH = "/rest/api/3/screens/10013"
ISSUE_TYPE_SCHEME_PATH = "/rest/api/3/issuetypescheme/10229"
ISSUE_TYPE_PATH = "/rest/api/3/issuetype/10011"
WORKFLOW_PATH = "/rest/api/3/workflow/ed5b3859-bf7b-46d3-be24-baefc260cb75"

PROJECT_DATA = {
    "id": "10002",
    "key": KEY,
    "name": "jirakit workflow API test",
    "description": "",
    "projectTypeKey": "software",
}


class DeleteRecorder:
    """
    Stands in for JiraClient.delete, recording paths in call order and failing
    the paths it has been told to block.
    """

    def __init__(self):
        self.paths = []
        self.blocked = {}

    def block(self, path, message, times=None):
        """Fail `path` with `message`, for `times` calls or indefinitely."""
        self.blocked[path] = {"message": message, "remaining": times}

    def __call__(self, path, *args, **kwargs):
        self.paths.append(path)

        rule = self.blocked.get(path)
        if rule and (rule["remaining"] is None or rule["remaining"] > 0):
            if rule["remaining"] is not None:
                rule["remaining"] -= 1
            raise Exception(f"400 Client Error: {rule['message']} for url: {path}")

        response = Mock()
        response.status_code = 204
        response.raise_for_status = Mock()
        return response

    def index(self, path):
        """Position of the first DELETE of `path`."""
        assert path in self.paths, f"{path} was never deleted; deleted {self.paths}"
        return self.paths.index(path)


@pytest.fixture
def tracking_dir(tmp_path):
    """A tracking directory holding a completed deployment for JKTEST."""
    directory = tmp_path / ".jirakit_deployments"
    directory.mkdir()

    tracker = DeploymentTracker(
        project_key=KEY,
        project_id="10002",
        project_name="jirakit workflow API test",
        template_name="test template",
        tracking_dir=str(directory),
    )
    tracker.track_issue_type("10011", f"{KEY}: Test Item")
    tracker.track_issue_type_scheme("10229", f"{KEY}: Test Issue Type Scheme")
    tracker.track_screen("10013", f"{KEY}: Test Screen")
    tracker.track_screen_scheme("10013", f"{KEY}: Test Screen Scheme")
    tracker.track_issue_type_screen_scheme(
        "10004", f"{KEY}: Test Issue Type Screen Scheme"
    )
    tracker.track_workflow(
        "ed5b3859-bf7b-46d3-be24-baefc260cb75", f"{KEY}: Test Workflow"
    )
    tracker.track_workflow_scheme("10004", f"{KEY}: Test Workflow Scheme")
    tracker.mark_completed()

    return str(directory)


@pytest.fixture
def deleter(mock_client):
    """Wire mock_client with real managers and a recording delete."""
    recorder = DeleteRecorder()
    mock_client.delete.side_effect = recorder

    mock_client.issue_types.return_value = IssueTypes(mock_client)
    mock_client.screens.return_value = Screens(mock_client)
    mock_client.workflows.return_value = Workflows(mock_client)

    mock_client.get.side_effect = reader()
    return recorder


def reader(
    workflow_schemes=(),
    workflows=(),
    issue_type_screen_schemes=(),
    screen_schemes=(),
    screens=(),
    issue_type_schemes=(),
    issue_types=(),
):
    """
    A GET side effect serving only the reads a rollback legitimately makes: the
    project itself, and the sweeps that find resources named for it. Any other
    read raises, so loading the project's configuration cannot pass unnoticed.
    """

    listings = {
        "/rest/api/3/workflowscheme?": workflow_schemes,
        "/rest/api/3/workflow/search": workflows,
        "/rest/api/3/issuetypescreenscheme?": issue_type_screen_schemes,
        "/rest/api/3/screenscheme?": screen_schemes,
        "/rest/api/3/screens?": screens,
        "/rest/api/3/issuetypescheme?": issue_type_schemes,
    }

    def get(path, *args, **kwargs):
        response = Mock()
        response.raise_for_status = Mock()

        if path == f"/rest/api/3/project/{KEY}":
            response.json.return_value = PROJECT_DATA
            return response

        if path.startswith("/rest/api/3/issuetype?") or path == "/rest/api/3/issuetype":
            response.json.return_value = list(issue_types)
            return response

        for prefix, values in listings.items():
            if path.startswith(prefix):
                response.json.return_value = {"isLast": True, "values": list(values)}
                return response

        raise AssertionError(f"unexpected read during rollback: {path}")

    return get


@pytest.fixture
def projects(mock_client, deleter):
    return Projects(mock_client)


def tracking_file(tracking_dir):
    return os.path.join(tracking_dir, f"{KEY}.json")


class TestRollbackOrder:
    """The order deletions are issued in decides whether Jira accepts them."""

    def test_project_is_deleted_before_the_schemes_that_depend_on_it(
        self, projects, deleter, tracking_dir
    ):
        """
        A scheme still assigned to a live project cannot be deleted, so deleting
        the project last makes every dependent deletion fail with a 400.
        """
        projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        project_at = deleter.index(PROJECT_PATH)
        assert project_at < deleter.index(ITSS_PATH)
        assert project_at < deleter.index(SCREEN_SCHEME_PATH)
        assert project_at < deleter.index(SCREEN_PATH)
        assert project_at < deleter.index(ISSUE_TYPE_SCHEME_PATH)
        assert project_at < deleter.index(ISSUE_TYPE_PATH)

    def test_screens_are_deleted_after_the_schemes_that_use_them(
        self, projects, deleter, tracking_dir
    ):
        """A screen in use by a screen scheme, itself in use by an issue type
        screen scheme, can only be deleted from the outside in."""
        projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert deleter.index(ITSS_PATH) < deleter.index(SCREEN_SCHEME_PATH)
        assert deleter.index(SCREEN_SCHEME_PATH) < deleter.index(SCREEN_PATH)

    def test_workflow_scheme_is_deleted_before_its_workflow(
        self, projects, deleter, tracking_dir
    ):
        """A workflow still referenced by a scheme cannot be deleted."""
        projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert deleter.index(WORKFLOW_SCHEME_PATH) < deleter.index(WORKFLOW_PATH)


class TestRollbackCoverage:
    """Every tracked resource must actually be deleted."""

    def test_all_tracked_resources_are_deleted(self, projects, deleter, tracking_dir):
        """
        Issue type schemes and workflow schemes were only recorded as deleted,
        never actually deleted, on the assumption the project removed them.
        """
        summary = projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        for path in (
            PROJECT_PATH,
            WORKFLOW_SCHEME_PATH,
            ITSS_PATH,
            SCREEN_SCHEME_PATH,
            SCREEN_PATH,
            ISSUE_TYPE_SCHEME_PATH,
            ISSUE_TYPE_PATH,
            WORKFLOW_PATH,
        ):
            assert path in deleter.paths

        assert summary["errors"] == []
        assert summary["project_deleted"] is True
        assert summary["workflow_schemes_deleted"] == [f"{KEY}: Test Workflow Scheme"]
        assert summary["issue_type_schemes_deleted"] == [
            f"{KEY}: Test Issue Type Scheme"
        ]

    def test_the_project_configuration_is_not_loaded_before_deleting_it(
        self, projects, deleter, tracking_dir
    ):
        """
        Rollback runs on half-deployed projects, where loading the project's
        configuration can fail and abort the rollback before anything has been
        deleted. Only the project ID is needed.
        """
        summary = projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert summary["project_deleted"] is True
        assert summary["errors"] == []

    def test_auto_created_project_workflow_and_scheme_are_deleted(
        self, projects, deleter, tracking_dir, mock_client
    ):
        """
        Creating the project makes Jira auto-create a workflow scheme and
        workflow that nothing tracks and deleting the project does not remove.
        """
        auto_scheme = {
            "id": "10005",
            "name": f"{KEY}: Software Simplified Workflow Scheme",
        }
        auto_workflow = {
            "id": {
                "name": f"Software Simplified Workflow for Project {KEY}",
                "entityId": "auto-workflow-uuid",
            },
            "description": "",
        }

        mock_client.get.side_effect = reader(
            workflow_schemes=[auto_scheme], workflows=[auto_workflow]
        )

        projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert "/rest/api/3/workflowscheme/10005" in deleter.paths
        assert "/rest/api/3/workflow/auto-workflow-uuid" in deleter.paths
        assert deleter.index("/rest/api/3/workflowscheme/10005") < deleter.index(
            "/rest/api/3/workflow/auto-workflow-uuid"
        )

    def test_untracked_resources_named_for_the_project_are_deleted(
        self, projects, deleter, tracking_dir, mock_client
    ):
        """
        The project template makes Jira auto-create its own screens and schemes,
        named for the project. Nothing tracks them, and deleting the project
        does not remove them.
        """
        mock_client.get.side_effect = reader(
            issue_type_screen_schemes=[
                {"id": "10005", "name": f"{KEY}: Kanban Issue Type Screen Scheme"}
            ],
            screen_schemes=[
                {"id": "10014", "name": f"{KEY}: Kanban Default Screen Scheme"}
            ],
            screens=[{"id": "10010", "name": f"{KEY}: Kanban Default Issue Screen"}],
            issue_type_schemes=[
                {"id": "10230", "name": f"{KEY}: Kanban Issue Type Scheme"}
            ],
        )

        projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        kanban_itss = "/rest/api/3/issuetypescreenscheme/10005"
        kanban_screen_scheme = "/rest/api/3/screenscheme/10014"
        kanban_screen = "/rest/api/3/screens/10010"

        assert kanban_itss in deleter.paths
        assert kanban_screen_scheme in deleter.paths
        assert kanban_screen in deleter.paths
        assert "/rest/api/3/issuetypescheme/10230" in deleter.paths

        assert deleter.index(kanban_itss) < deleter.index(kanban_screen_scheme)
        assert deleter.index(kanban_screen_scheme) < deleter.index(kanban_screen)

    def test_a_tracked_resource_is_not_deleted_twice(
        self, projects, deleter, tracking_dir, mock_client
    ):
        """
        The sweep for untracked resources sees the tracked ones too, and a second
        delete of the same resource reports a spurious failure.
        """
        mock_client.get.side_effect = reader(
            screens=[{"id": "10013", "name": f"{KEY}: Test Screen"}]
        )

        summary = projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert deleter.paths.count(SCREEN_PATH) == 1
        assert summary["screens_deleted"] == [f"{KEY}: Test Screen"]
        assert summary["errors"] == []

    def test_unrelated_resources_are_left_alone(
        self, projects, deleter, tracking_dir, mock_client
    ):
        """
        The sweep matches on the project-key prefix the deployment uses, so a
        resource merely mentioning the key elsewhere must not be deleted.
        """
        mock_client.get.side_effect = reader(
            screens=[
                {"id": "99999", "name": f"Shared screen for {KEY} and others"},
                {"id": "99998", "name": f"{KEY}2: Test Screen"},
            ]
        )

        projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert "/rest/api/3/screens/99999" not in deleter.paths
        assert "/rest/api/3/screens/99998" not in deleter.paths

    def test_result_notes_the_shared_resources_left_behind(
        self, projects, deleter, tracking_dir
    ):
        """
        Custom fields and statuses are deliberately not deleted because they may
        be shared, which surprises operators who find them afterwards.
        """
        summary = projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        note = " ".join(summary["shared_resources_left"]).lower()
        assert "field" in note
        assert "status" in note


class TestRollbackFailureReporting:
    """A rollback that could not finish must say so, and keep the evidence."""

    def test_tracking_file_is_removed_after_a_clean_rollback(
        self, projects, deleter, tracking_dir
    ):
        """Nothing was left behind, so the record has nothing left to describe."""
        summary = projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert summary["errors"] == []
        assert not os.path.exists(tracking_file(tracking_dir))

    def test_tracking_file_is_kept_when_a_deletion_fails(
        self, projects, deleter, tracking_dir
    ):
        """
        Deleting the record after a partial rollback strands the survivors with
        nothing left to retry from.
        """
        deleter.block(SCREEN_PATH, "The screen is used in a screen scheme.")

        summary = projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert summary["errors"] != []
        assert os.path.exists(tracking_file(tracking_dir))

    def test_resources_that_could_not_be_deleted_are_listed(
        self, projects, deleter, tracking_dir
    ):
        """The operator needs to know exactly what is still on the site."""
        deleter.block(SCREEN_PATH, "The screen is used in a screen scheme.")

        summary = projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        remaining = summary["resources_remaining"]
        assert [r["name"] for r in remaining] == [f"{KEY}: Test Screen"]
        assert remaining[0]["id"] == "10013"
        assert remaining[0]["type"] == "screen"
        assert "used in a screen scheme" in remaining[0]["reason"]

    def test_failed_workflow_deletion_is_reported(
        self, projects, deleter, tracking_dir
    ):
        """
        A failed workflow deletion was logged as 'likely active' and swallowed,
        so an orphaned workflow never reached the errors list.
        """
        deleter.block(WORKFLOW_PATH, "Not allowed to delete active workflow.")

        summary = projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert any("Test Workflow" in error for error in summary["errors"])
        assert [r["type"] for r in summary["resources_remaining"]] == ["workflow"]

    def test_a_missing_project_is_treated_as_already_deleted(
        self, projects, deleter, tracking_dir, mock_client
    ):
        """
        A partial rollback keeps its tracking file so it can be retried, but by
        then the project is already gone. Retrying must clean up the survivors
        rather than stopping at the missing project.
        """
        inner = reader()

        def get(path, *args, **kwargs):
            if path == f"/rest/api/3/project/{KEY}":
                raise Exception("404 Client Error: Not Found for url: " + path)
            return inner(path)

        mock_client.get.side_effect = get

        summary = projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert PROJECT_PATH not in deleter.paths
        assert SCREEN_PATH in deleter.paths
        assert ITSS_PATH in deleter.paths
        assert summary["errors"] == []
        assert not os.path.exists(tracking_file(tracking_dir))

    def test_failed_project_deletion_stops_the_dependent_deletions(
        self, projects, deleter, tracking_dir
    ):
        """
        With the project still live every scheme deletion fails, so attempting
        them only fills the result with noise.
        """
        deleter.block(PROJECT_PATH, "Project cannot be deleted.")

        summary = projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert summary["project_deleted"] is False
        assert ITSS_PATH not in deleter.paths
        assert SCREEN_PATH not in deleter.paths
        assert any("project" in error.lower() for error in summary["errors"])


class TestRollbackRetries:
    """Jira does not release a deleted project's schemes synchronously."""

    def test_a_blocked_deletion_is_retried_until_it_succeeds(
        self, projects, deleter, tracking_dir, monkeypatch
    ):
        """
        The schemes of a deleted project stay un-deletable for a while, so a
        single attempt reports failures that a retry would have cleared.
        """
        slept = []
        monkeypatch.setattr("jirakit.projects.time.sleep", slept.append)

        deleter.block(
            ITSS_PATH,
            "The issue type screen scheme is assigned to one or more projects.",
            times=2,
        )

        summary = projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=30
        )

        assert deleter.paths.count(ITSS_PATH) == 3
        assert summary["errors"] == []
        assert summary["issue_type_screen_schemes_deleted"] == [
            f"{KEY}: Test Issue Type Screen Scheme"
        ]
        assert slept

    def test_retries_stop_at_the_configured_budget(
        self, projects, deleter, tracking_dir, monkeypatch
    ):
        """A rollback must not block its caller indefinitely."""
        elapsed = iter([0, 10, 20, 30, 40, 50, 60, 70])
        monkeypatch.setattr("jirakit.projects.time.sleep", lambda _: None)
        monkeypatch.setattr("jirakit.projects.time.monotonic", lambda: next(elapsed))

        deleter.block(ITSS_PATH, "The issue type screen scheme is assigned.")

        summary = projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=30
        )

        assert 1 < deleter.paths.count(ITSS_PATH) <= 4
        assert [r["type"] for r in summary["resources_remaining"]] == [
            "issue type screen scheme"
        ]

    def test_no_retry_is_attempted_when_the_budget_is_zero(
        self, projects, deleter, tracking_dir
    ):
        """Retries are opt-out for callers that cannot afford to wait."""
        deleter.block(ITSS_PATH, "The issue type screen scheme is assigned.")

        projects.rollback_template_deployment(
            KEY, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert deleter.paths.count(ITSS_PATH) == 1


class TestRollbackWithoutDeletingTheProject:
    """Scheme deletion needs the project gone."""

    def test_scheme_deletions_are_skipped_and_explained(
        self, projects, deleter, tracking_dir
    ):
        """
        Every scheme deletion fails while the project is live, so attempting
        them produces nothing but 400s.
        """
        summary = projects.rollback_template_deployment(
            KEY, delete_project=False, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert PROJECT_PATH not in deleter.paths
        assert ITSS_PATH not in deleter.paths
        assert SCREEN_SCHEME_PATH not in deleter.paths
        assert ISSUE_TYPE_SCHEME_PATH not in deleter.paths

        note = " ".join(summary["skipped"]).lower()
        assert "project" in note

    def test_the_tracking_file_is_kept(self, projects, deleter, tracking_dir):
        """Resources were deliberately left, so the record must survive."""
        projects.rollback_template_deployment(
            KEY, delete_project=False, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert os.path.exists(tracking_file(tracking_dir))


class TestRollbackWithUndoEnabled:
    """A project in the recycle bin still holds the schemes assigned to it."""

    def test_dependent_deletions_are_skipped_and_explained(
        self, projects, deleter, tracking_dir
    ):
        """
        enable_undo puts the project in the recycle bin rather than deleting it,
        and Jira goes on refusing to delete its schemes as "assigned to one or
        more projects" for as long as it sits there.
        """
        summary = projects.rollback_template_deployment(
            KEY, enable_undo=True, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert "/rest/api/3/project/10002?enableUndo=True" in deleter.paths
        assert summary["project_deleted"] is True
        assert ITSS_PATH not in deleter.paths
        assert SCREEN_PATH not in deleter.paths

        note = " ".join(summary["skipped"]).lower()
        assert "recycle bin" in note

    def test_the_tracking_file_is_kept(self, projects, deleter, tracking_dir):
        """Resources were deliberately left, so the record must survive."""
        projects.rollback_template_deployment(
            KEY, enable_undo=True, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert os.path.exists(tracking_file(tracking_dir))

    def test_an_already_deleted_project_is_still_cleaned_up(
        self, projects, deleter, tracking_dir, mock_client
    ):
        """
        Nothing goes to the recycle bin when there is no project left to put
        there, so enable_undo must not hold up the cleanup.
        """
        inner = reader()

        def get(path, *args, **kwargs):
            if path == f"/rest/api/3/project/{KEY}":
                raise Exception("404 Client Error: Not Found for url: " + path)
            return inner(path)

        mock_client.get.side_effect = get

        projects.rollback_template_deployment(
            KEY, enable_undo=True, tracking_dir=tracking_dir, retry_seconds=0
        )

        assert SCREEN_PATH in deleter.paths


class TestRollbackWithoutATrackingFile:
    """The fallback path searches by naming convention."""

    def test_project_is_deleted_before_the_resources_that_depend_on_it(
        self, projects, deleter, mock_client, tmp_path
    ):
        """The fallback path deleted the project last, exactly as the tracked one did."""
        screen = {"id": "10013", "name": f"{KEY}: Test Screen"}
        issue_type = {"id": "10011", "name": f"{KEY}: Test Item", "subtask": False}

        def get(path, *args, **kwargs):
            response = Mock()
            response.raise_for_status = Mock()
            if path == f"/rest/api/3/project/{KEY}":
                response.json.return_value = PROJECT_DATA
            elif path.startswith("/rest/api/3/screens?"):
                response.json.return_value = {"isLast": True, "values": [screen]}
            elif path.startswith("/rest/api/3/issuetype"):
                response.json.return_value = [issue_type]
            else:
                response.json.return_value = {"isLast": True, "values": []}
            return response

        mock_client.get.side_effect = get

        projects.rollback_template_deployment(
            KEY, tracking_dir=str(tmp_path / "empty"), retry_seconds=0
        )

        assert deleter.index(PROJECT_PATH) < deleter.index(SCREEN_PATH)
