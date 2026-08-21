"""
Unit tests for reporting what a deployed project is missing from a template.

A service that ships a bundled template and validates it at start-up needs to
say precisely what an administrator must change, rather than failing with a bare
list of field names. Two entry points serve that: ``plan_template``, which is a
full dry run and needs Jira administrator permission to read the screens, and
``missing_template_fields``, which answers the narrower question from issue
create metadata alone and so works for a least-privileged runtime.
"""

from unittest.mock import Mock

import pytest

from tests.fake_jira import FakeClient
from tests.test_template_reconciliation import (
    KEY,
    TEMPLATE,
    with_extra_field,
    with_extra_issue_type,
)
from jirakit.projects import Projects, read_all_pages


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


def wide_template(field_count):
    """
    A template whose issue type carries more fields than one page holds.

    Both create metadata endpoints default to 50 per page, and a deployment
    from a substantial template routinely exceeds that, so this is the ordinary
    case rather than an edge one.
    """
    names = [f"Field {n:03d}" for n in range(field_count)]
    return {
        "name": "wide template",
        "description": "",
        "groups": [],
        "fields": [
            {"name": name, "type": "select", "description": ""} for name in names
        ],
        "issue_types": [
            {"name": "Incident", "description": "An incident", "subtask": False}
        ],
        "issue_type_schemes": [
            {"name": "Scheme", "description": "", "issue_types": ["Incident"]}
        ],
        "screens": [{"name": "Screen", "description": ""}],
        "screen_tabs": [{"screen": "Screen", "name": "Details", "fields": names}],
        "screen_schemes": [
            {"name": "Screen Scheme", "description": "", "screens": {"default": "Screen"}}
        ],
        "issue_type_screen_schemes": [
            {
                "name": "ITSS",
                "description": "",
                "default_screen_scheme": "Screen Scheme",
                "mappings": [
                    {"issue_type": "Incident", "screen_scheme": "Screen Scheme"}
                ],
            }
        ],
    }


class TestMissingTemplateFieldsPagination:
    """
    Both create metadata endpoints page and default to 50 per page. Reading a
    single page reports every field beyond it as missing, which is the worst
    possible direction for this function to be wrong in: it is what a
    least-privileged runtime calls to tell an administrator what to fix, so a
    false positive means adding fields that are already there.
    """

    def test_a_project_matching_its_template_is_missing_nothing_beyond_one_page(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        jira = FakeClient()
        template = wide_template(86)
        project = Projects(jira).create("Wide", KEY, template)

        missing = Projects(jira).missing_template_fields(project, template)

        assert missing == {}

    def test_it_still_finds_a_field_that_is_genuinely_absent(
        self, tmp_path, monkeypatch
    ):
        """Paging must not be achieved by simply reporting nothing."""
        monkeypatch.chdir(tmp_path)
        jira = FakeClient()
        deployed = wide_template(86)
        project = Projects(jira).create("Wide", KEY, deployed)

        grown = wide_template(86)
        grown["fields"] = deployed["fields"] + [
            {"name": "Latecomer", "type": "select", "description": ""}
        ]
        grown["screen_tabs"] = [
            {
                "screen": "Screen",
                "name": "Details",
                "fields": [f["name"] for f in grown["fields"]],
            }
        ]

        missing = Projects(jira).missing_template_fields(project, grown)

        assert missing == {f"{KEY}: Incident": ["Latecomer"]}

    def test_the_field_lookup_is_read_to_exhaustion(self, tmp_path, monkeypatch):
        """Across several pages, not just the first two."""
        monkeypatch.chdir(tmp_path)
        jira = FakeClient()
        jira.createmeta_page_size = 7
        template = wide_template(40)
        project = Projects(jira).create("Wide", KEY, template)

        assert Projects(jira).missing_template_fields(project, template) == {}

    def test_the_issue_type_lookup_is_read_to_exhaustion(
        self, tmp_path, monkeypatch
    ):
        """
        The issue type listing pages too, so a project with more issue types
        than one page holds would silently skip the ones beyond it.
        """
        monkeypatch.chdir(tmp_path)
        jira = FakeClient()
        jira.createmeta_page_size = 2
        template = wide_template(3)
        template["issue_types"] = [
            {"name": f"Type {n}", "description": "", "subtask": False}
            for n in range(5)
        ]
        template["issue_type_schemes"][0]["issue_types"] = [
            f"Type {n}" for n in range(5)
        ]
        template["issue_type_screen_schemes"][0]["mappings"] = [
            {"issue_type": f"Type {n}", "screen_scheme": "Screen Scheme"}
            for n in range(5)
        ]
        project = Projects(jira).create("Wide", KEY, template)

        # Every issue type maps to the same screen, so all five must report the
        # same absent field rather than only those on the first page.
        grown = {**template, "fields": template["fields"] + [
            {"name": "Latecomer", "type": "select", "description": ""}
        ]}
        grown["screen_tabs"] = [
            {
                "screen": "Screen",
                "name": "Details",
                "fields": [f["name"] for f in grown["fields"]],
            }
        ]

        missing = Projects(jira).missing_template_fields(project, grown)

        assert sorted(missing) == [f"{KEY}: Type {n}" for n in range(5)]


class PagingStub:
    """
    Serves create metadata pages that deliberately omit ``total``.

    Not every response carries it, and a walk that depends on it alone would
    not terminate without one -- the defect fixed across the library in 0.7.0.
    """

    def __init__(self, items, page_size, include_total=False):
        self.items = items
        self.page_size = page_size
        self.include_total = include_total
        self.calls = 0

    def get(self, path=None, **kwargs):
        self.calls += 1
        start_at = int(path.split("startAt=")[1].split("&")[0])
        max_results = int(path.split("maxResults=")[1].split("&")[0])
        page_size = min(max_results, self.page_size)
        window = self.items[start_at : start_at + page_size]

        payload = {"startAt": start_at, "maxResults": page_size, "fields": window}
        if self.include_total:
            payload["total"] = len(self.items)

        response = Mock()
        response.status_code = 200
        response.raise_for_status = Mock()
        response.json.return_value = payload
        return response


class TestReadCreatemetaTerminates:
    """Every terminator of the paging walk, independently."""

    def test_a_short_page_ends_the_walk_when_total_is_absent(self):
        items = [{"name": f"F{n}"} for n in range(205)]
        stub = PagingStub(items, page_size=200)

        read = Projects(stub).read_createmeta("/createmeta", "fields")

        assert len(read) == 205
        assert stub.calls == 2

    def test_an_empty_page_ends_the_walk_when_the_total_divides_exactly(self):
        """
        With an exact multiple there is no short page, so the walk ends on the
        empty one that follows.
        """
        items = [{"name": f"F{n}"} for n in range(400)]
        stub = PagingStub(items, page_size=200)

        read = Projects(stub).read_createmeta("/createmeta", "fields")

        assert len(read) == 400
        assert stub.calls == 3

    def test_the_reported_total_ends_the_walk(self):
        items = [{"name": f"F{n}"} for n in range(400)]
        stub = PagingStub(items, page_size=200, include_total=True)

        read = Projects(stub).read_createmeta("/createmeta", "fields")

        assert len(read) == 400
        assert stub.calls == 2

    def test_a_page_reporting_no_capacity_ends_the_walk(self):
        """
        A response echoing maxResults of 0 makes the short-page comparison
        false however few items came back, so an empty page has to end the walk
        in its own right. No response shape should be able to keep this looping
        -- the same principle as the paginated helpers fixed in 0.7.0.
        """
        response = Mock()
        response.status_code = 200
        response.raise_for_status = Mock()
        response.json.return_value = {"startAt": 0, "maxResults": 0, "fields": []}
        client = Mock()
        client.get.return_value = response

        assert Projects(client).read_createmeta("/createmeta", "fields") == []
        assert client.get.call_count == 1

    def test_it_appends_to_a_path_that_already_has_a_query_string(self):
        """
        The issue type screen scheme mapping endpoint is read with its scheme id
        already in the query string. Starting a second one with '?' would make
        the URL malformed.
        """
        response = Mock()
        response.status_code = 200
        response.raise_for_status = Mock()
        response.json.return_value = {"maxResults": 200, "total": 0, "values": []}
        client = Mock()
        client.get.return_value = response

        read_all_pages(client, "/rest/api/3/thing?id=7", "values")

        requested = client.get.call_args.kwargs["path"]
        assert requested.count("?") == 1
        assert requested == "/rest/api/3/thing?id=7&startAt=0&maxResults=200"

    def test_a_single_short_page_is_one_request(self):
        stub = PagingStub([{"name": "F0"}], page_size=200)

        assert Projects(stub).read_createmeta("/createmeta", "fields") == [
            {"name": "F0"}
        ]
        assert stub.calls == 1
