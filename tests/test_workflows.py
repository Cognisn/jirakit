"""
Unit tests for the Workflows module.

Tests cover:
- Workflow class properties
- Status class properties
- Workflows.get_all() method
- Workflows.create() method
- Statuses.get_all() method
- Statuses.create() and delete() methods
"""

import uuid
from unittest.mock import Mock

import pytest

from jirakit.fields import Field
from jirakit.workflows import Workflow, Workflows
from jirakit.workflows.statuses import Status, Statuses


class TestWorkflowClass:
    """Tests for the Workflow class."""

    def test_workflow_initialisation(self, mock_client, sample_workflow_data):
        """Test Workflow class initialisation."""
        workflow = Workflow(sample_workflow_data, mock_client)

        assert workflow.details == sample_workflow_data
        assert workflow.client == mock_client

    def test_name_and_description_from_search_shape(
        self, mock_client, sample_workflow_data
    ):
        """
        Workflow search nests the name under 'id' and sends none at the top level,
        so reading it must not assume the top-level key exists.
        """
        workflow = Workflow(sample_workflow_data, mock_client)

        assert workflow.name == "Test Workflow"
        assert workflow.description == "A test workflow"

    def test_name_from_a_top_level_key(self, mock_client):
        """Workflow creation returns the name at the top level."""
        workflow = Workflow(
            {"id": "6d0b3e12-9f6a-4c1e-8b4f-6a2f0c1d5e77", "name": "Created Workflow"},
            mock_client,
        )

        assert workflow.name == "Created Workflow"

    def test_entity_id_from_legacy_nested_id(self, mock_client, sample_workflow_data):
        """The legacy /workflow/search response nests the entity ID under 'id'."""
        workflow = Workflow(sample_workflow_data, mock_client)

        assert workflow.entity_id == "workflow-123"

    def test_entity_id_from_string_id(self, mock_client):
        """
        The /workflows/create response returns 'id' as a plain string UUID.

        Rollback tracks this value and deletes with it, so reading it must not
        assume the legacy nested shape.
        """
        workflow = Workflow(
            {"id": "6d0b3e12-9f6a-4c1e-8b4f-6a2f0c1d5e77", "name": "Test Workflow"},
            mock_client,
        )

        assert workflow.entity_id == "6d0b3e12-9f6a-4c1e-8b4f-6a2f0c1d5e77"


class TestWorkflowsGetAll:
    """Tests for Workflows.get_all() method."""

    def test_get_all_workflows(
        self, mock_client, sample_workflow_data, paginated_response_factory
    ):
        """Test fetching all workflows."""
        workflows_data = [sample_workflow_data]

        mock_response = Mock()
        mock_response.json.return_value = paginated_response_factory(
            workflows_data, is_last=True
        )
        mock_client.get.return_value = mock_response

        workflows_manager = Workflows(mock_client)
        workflows = workflows_manager.get_all(active=True)

        assert len(workflows) == 1
        assert isinstance(workflows[0], Workflow)


class TestStatusClass:
    """Tests for the Status class."""

    def test_status_initialisation(self, mock_client, sample_status_data):
        """Test Status class initialisation."""
        status = Status(sample_status_data, mock_client)

        assert status.detail == sample_status_data
        assert status.client == mock_client

    def test_status_properties(self, mock_client, sample_status_data):
        """Test Status properties."""
        status = Status(sample_status_data, mock_client)

        assert status.id == sample_status_data["id"]
        assert status.name == sample_status_data["name"]
        assert status.description == sample_status_data["description"]
        assert status.status_category == sample_status_data["statusCategory"]


class TestStatusesOperations:
    """Tests for Statuses operations."""

    def test_get_all_statuses(
        self, mock_client, sample_status_data, paginated_response_factory
    ):
        """Test fetching all statuses."""
        statuses_data = [sample_status_data]

        mock_response = Mock()
        mock_response.json.return_value = paginated_response_factory(
            statuses_data, is_last=True
        )
        mock_client.get.return_value = mock_response

        statuses_manager = Statuses(mock_client)
        statuses = statuses_manager.get_all()

        assert len(statuses) == 1
        assert isinstance(statuses[0], Status)

    def test_create_status(self, mock_client, sample_status_data):
        """Test creating a status."""
        mock_response = Mock()
        mock_response.json.return_value = [sample_status_data]
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response

        statuses_manager = Statuses(mock_client)
        status = statuses_manager.create("Open", "TODO", "The issue is open")

        assert isinstance(status, Status)
        assert status.name == "Open"

    def test_delete_status(self, mock_client, sample_status_data):
        """Test deleting a status."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_client.delete.return_value = mock_response

        status = Status(sample_status_data, mock_client)
        statuses_manager = Statuses(mock_client)

        statuses_manager.delete(status)

        mock_client.delete.assert_called_once()


CREATE_PATH = "/rest/api/3/workflows/create"
VALIDATE_PATH = "/rest/api/3/workflows/create/validation"
LEGACY_CREATE_PATH = "/rest/api/3/workflow"
STATUSES_PATH = "/rest/api/3/statuses"

CREATED_WORKFLOW_ID = "9f4c8a41-2d3b-4a55-8f0c-1e2d3c4b5a69"

NEW_STATUS = {
    "id": "10007",
    "name": "New",
    "description": "",
    "statusCategory": "TODO",
    "scope": {"type": "GLOBAL"},
    "usages": [],
    "workflowUsages": [],
}

CLOSED_STATUS = {
    "id": "6",
    "name": "Closed",
    "description": "",
    "statusCategory": "DONE",
    "scope": {"type": "GLOBAL"},
    "usages": [],
    "workflowUsages": [],
}


class JiraDouble:
    """
    Stands in for JiraClient.post, recording every call and serving the
    responses the real Jira Cloud endpoints return.
    """

    def __init__(self):
        self.posts = []
        self.validation_errors = []
        self.created_statuses = []

    def __call__(self, path, data=None, **kwargs):
        self.posts.append((path, data))
        response = Mock()
        response.raise_for_status = Mock()

        if path == VALIDATE_PATH:
            response.json.return_value = {"errors": self.validation_errors}
        elif path == CREATE_PATH:
            response.json.return_value = {
                "workflows": [
                    {
                        "id": CREATED_WORKFLOW_ID,
                        "name": data["workflows"][0]["name"],
                        "description": data["workflows"][0].get("description", ""),
                        "version": {"versionNumber": 1, "id": "version-1"},
                        "scope": {"type": "GLOBAL"},
                        "isEditable": True,
                        "statuses": [],
                        "transitions": [],
                    }
                ],
                "statuses": [],
            }
        elif path == STATUSES_PATH:
            created = {
                "id": "20001",
                "name": data["statuses"][0]["name"],
                "description": data["statuses"][0].get("description", ""),
                "statusCategory": data["statuses"][0]["statusCategory"],
                "scope": {"type": "GLOBAL"},
                "usages": [],
                "workflowUsages": [],
            }
            self.created_statuses.append(created)
            response.json.return_value = [created]
        else:
            response.json.return_value = {}

        return response

    @property
    def paths(self):
        """Paths POSTed to, in call order."""
        return [path for path, _ in self.posts]

    def payload(self, path):
        """The body sent to ``path``."""
        for posted_path, data in self.posts:
            if posted_path == path:
                return data
        raise AssertionError(f"No POST was made to {path}; posted to {self.paths}")


@pytest.fixture
def jira(mock_client, paginated_response_factory):
    """
    Wire ``mock_client`` for workflow creation.

    Status resolution runs through the real Statuses class against a mocked
    status search; POSTs are recorded by the returned double.
    """
    double = JiraDouble()

    mock_client.statuses.return_value = Statuses(mock_client)

    get_response = Mock()
    get_response.json.return_value = paginated_response_factory(
        [NEW_STATUS, CLOSED_STATUS], is_last=True
    )
    get_response.raise_for_status = Mock()
    mock_client.get.return_value = get_response
    mock_client.post.side_effect = double

    return double


@pytest.fixture
def project():
    """A project double exposing the fields conditions are mapped against."""
    project = Mock()
    project.key = "SENTEST"
    project.project_fields = [
        Field({"id": "customfield_10050", "name": "Severity"}, None)
    ]
    return project


@pytest.fixture
def workflow_definition():
    """A template workflow definition using both supported condition types."""
    return {
        "statuses": [
            {"name": "New", "type": "TODO"},
            {"name": "Closed", "type": "DONE"},
        ],
        "transitions": [
            {"name": "Created", "type": "INITIAL", "to": "New"},
            {
                "name": "Incident Completed",
                "type": "DIRECTED",
                "to": "Closed",
                "from": ["New"],
                "conditions": {
                    "operator": "AND",
                    "conditions": [
                        {"type": "AllowOnlyAssignee"},
                        {
                            "type": "ValueFieldCondition",
                            "configuration": {
                                "fieldId": "Severity",
                                "fieldValue": "Critical",
                                "comparisonType": "STRING",
                                "comparator": "=",
                            },
                        },
                    ],
                },
            },
        ],
    }


def status_references(payload):
    """Map status name to the UUID reference the payload assigned it."""
    return {status["name"]: status["statusReference"] for status in payload["statuses"]}


def transition_named(payload, name):
    """The transition called ``name`` in the payload's single workflow."""
    for transition in payload["workflows"][0]["transitions"]:
        if transition["name"] == name:
            return transition
    raise AssertionError(f"No transition named {name}")


class TestWorkflowsCreate:
    """Tests for Workflows.create() against the current workflow creation API."""

    def test_creates_through_the_current_endpoint(
        self, mock_client, jira, project, workflow_definition
    ):
        """
        The legacy POST /rest/api/3/workflow was removed by Atlassian and now
        returns 405, breaking every template deployment.
        """
        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        assert CREATE_PATH in jira.paths
        assert LEGACY_CREATE_PATH not in jira.paths

    def test_payload_scope_is_global(
        self, mock_client, jira, project, workflow_definition
    ):
        """Template workflows are shared across issue types, so scope is global."""
        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        assert jira.payload(CREATE_PATH)["scope"] == {"type": "GLOBAL"}

    def test_existing_statuses_pair_their_id_with_a_uuid_reference(
        self, mock_client, jira, project, workflow_definition
    ):
        """
        A numeric status ID as the reference fails with STATUS_REFERENCE_NOT_UUID,
        and a name with no ID fails with NON_UNIQUE_STATUS_NAME.
        """
        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        statuses = {s["name"]: s for s in jira.payload(CREATE_PATH)["statuses"]}

        assert statuses["New"]["id"] == "10007"
        assert statuses["New"]["statusCategory"] == "TODO"
        assert statuses["Closed"]["id"] == "6"
        assert statuses["Closed"]["statusCategory"] == "DONE"
        assert uuid.UUID(statuses["New"]["statusReference"])
        assert uuid.UUID(statuses["Closed"]["statusReference"])
        assert (
            statuses["New"]["statusReference"] != statuses["Closed"]["statusReference"]
        )

    def test_missing_status_is_created_and_referenced(
        self, mock_client, jira, project, workflow_definition
    ):
        """A status the site does not have yet must still be created first."""
        workflow_definition["statuses"].append(
            {"name": "Triaged", "type": "IN_PROGRESS"}
        )
        workflow_definition["transitions"].append(
            {"name": "Triage", "type": "DIRECTED", "to": "Triaged", "from": ["New"]}
        )

        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        assert jira.payload(STATUSES_PATH)["statuses"][0]["name"] == "Triaged"

        payload = jira.payload(CREATE_PATH)
        triaged = next(s for s in payload["statuses"] if s["name"] == "Triaged")
        assert triaged["id"] == "20001"
        assert triaged["statusCategory"] == "IN_PROGRESS"
        assert (
            transition_named(payload, "Triage")["toStatusReference"]
            == (triaged["statusReference"])
        )

    def test_existing_status_in_a_different_category_is_rejected(
        self, mock_client, jira, project, workflow_definition
    ):
        """Reusing a status name under a different category silently breaks the board."""
        workflow_definition["statuses"][0]["type"] = "DONE"

        with pytest.raises(Exception, match="different status category"):
            Workflows(mock_client).create(
                "SENTEST: Incident", "Incident workflow", workflow_definition, project
            )

    def test_workflow_carries_its_name_description_and_layout(
        self, mock_client, jira, project, workflow_definition
    ):
        """Workflow schemes map issue types by workflow name, so it must survive."""
        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        payload = jira.payload(CREATE_PATH)
        references = status_references(payload)
        workflow = payload["workflows"][0]

        assert workflow["name"] == "SENTEST: Incident"
        assert workflow["description"] == "Incident workflow"
        assert [s["statusReference"] for s in workflow["statuses"]] == [
            references["New"],
            references["Closed"],
        ]
        assert workflow["startPointLayout"] == {"x": -100.0, "y": 0.0}

        positions = [s["layout"]["x"] for s in workflow["statuses"]]
        assert len(set(positions)) == len(positions)

    def test_initial_transition_has_no_links(
        self, mock_client, jira, project, workflow_definition
    ):
        """An INITIAL transition with a populated links array is rejected."""
        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        payload = jira.payload(CREATE_PATH)
        created = transition_named(payload, "Created")

        assert created["type"] == "INITIAL"
        assert created["links"] == []
        assert created["toStatusReference"] == status_references(payload)["New"]

    def test_directed_transition_links_its_from_statuses(
        self, mock_client, jira, project, workflow_definition
    ):
        """The legacy 'from' list of status IDs becomes a list of link objects."""
        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        payload = jira.payload(CREATE_PATH)
        references = status_references(payload)
        completed = transition_named(payload, "Incident Completed")

        assert completed["type"] == "DIRECTED"
        assert completed["toStatusReference"] == references["Closed"]
        assert completed["links"] == [{"fromStatusReference": references["New"]}]

    def test_transition_to_an_undeclared_status_is_rejected(
        self, mock_client, jira, project, workflow_definition
    ):
        """
        Every status a transition touches needs a reference in the payload, so a
        typo in the template must be named rather than sent as a null reference.
        """
        workflow_definition["transitions"].append(
            {"name": "Escalate", "type": "DIRECTED", "to": "Esclated", "from": ["New"]}
        )

        with pytest.raises(ValueError, match="Esclated"):
            Workflows(mock_client).create(
                "SENTEST: Incident", "Incident workflow", workflow_definition, project
            )

        assert CREATE_PATH not in jira.paths

    def test_transition_ids_are_unique_strings(
        self, mock_client, jira, project, workflow_definition
    ):
        """Duplicate transition IDs are rejected by the create endpoint."""
        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        ids = [
            t["id"] for t in jira.payload(CREATE_PATH)["workflows"][0]["transitions"]
        ]

        assert all(isinstance(i, str) for i in ids)
        assert len(set(ids)) == len(ids)

    def test_lowercase_transition_types_are_normalised(
        self, mock_client, jira, project, workflow_definition
    ):
        """The legacy API took lowercase types; the current one only accepts uppercase."""
        for transition in workflow_definition["transitions"]:
            transition["type"] = transition["type"].lower()

        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        payload = jira.payload(CREATE_PATH)

        assert transition_named(payload, "Created")["type"] == "INITIAL"
        assert transition_named(payload, "Incident Completed")["type"] == "DIRECTED"

    def test_transition_without_conditions_omits_the_condition_group(
        self, mock_client, jira, project, workflow_definition
    ):
        """An empty condition group is not the same as no conditions."""
        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        assert "conditions" not in transition_named(
            jira.payload(CREATE_PATH), "Created"
        )

    def test_allow_only_assignee_maps_to_its_rule_key(
        self, mock_client, jira, project, workflow_definition
    ):
        """system:only-assignee-condition is rejected as UNSUPPORTED_RULE."""
        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        conditions = transition_named(jira.payload(CREATE_PATH), "Incident Completed")[
            "conditions"
        ]

        assert conditions["conditions"][0] == {
            "ruleKey": "system:restrict-issue-transition",
            "parameters": {"allowUserCustomFields": "assignee"},
        }

    def test_value_field_condition_maps_its_field_and_encodes_the_value(
        self, mock_client, jira, project, workflow_definition
    ):
        """
        The field name resolves to a custom field ID, and fieldValue is a
        JSON-array-encoded string rather than the bare value.
        """
        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        conditions = transition_named(jira.payload(CREATE_PATH), "Incident Completed")[
            "conditions"
        ]

        assert conditions["conditions"][1] == {
            "ruleKey": "system:check-field-value",
            "parameters": {
                "fieldId": "customfield_10050",
                "fieldValue": '["Critical"]',
                "comparator": "=",
                "comparisonType": "STRING",
            },
        }

    def test_condition_operator_and_becomes_all(
        self, mock_client, jira, project, workflow_definition
    ):
        """The legacy AND/OR operator vocabulary is not accepted as an operation."""
        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        conditions = transition_named(jira.payload(CREATE_PATH), "Incident Completed")[
            "conditions"
        ]

        assert conditions["operation"] == "ALL"
        assert conditions["conditionGroups"] == []

    def test_condition_operator_or_becomes_any(
        self, mock_client, jira, project, workflow_definition
    ):
        """OR must not silently degrade to ALL, which would block transitions."""
        workflow_definition["transitions"][1]["conditions"]["operator"] = "OR"

        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        conditions = transition_named(jira.payload(CREATE_PATH), "Incident Completed")[
            "conditions"
        ]

        assert conditions["operation"] == "ANY"

    def test_unmapped_condition_type_is_rejected_before_the_request(
        self, mock_client, jira, project, workflow_definition
    ):
        """An unmapped type would otherwise reach Jira as a rule key of None."""
        workflow_definition["transitions"][1]["conditions"]["conditions"] = [
            {
                "type": "PermissionCondition",
                "configuration": {"permissionKey": "WORK_ON_ISSUES"},
            }
        ]

        with pytest.raises(ValueError, match="PermissionCondition"):
            Workflows(mock_client).create(
                "SENTEST: Incident", "Incident workflow", workflow_definition, project
            )

        assert CREATE_PATH not in jira.paths

    def test_explicit_rule_key_is_passed_through(
        self, mock_client, jira, project, workflow_definition
    ):
        """Templates can reach any rule key the site supports without a mapping."""
        workflow_definition["transitions"][1]["conditions"]["conditions"] = [
            {
                "ruleKey": "system:parent-or-child-blocking-condition",
                "parameters": {"statusIds": "1,2"},
            }
        ]

        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        conditions = transition_named(jira.payload(CREATE_PATH), "Incident Completed")[
            "conditions"
        ]

        assert conditions["conditions"] == [
            {
                "ruleKey": "system:parent-or-child-blocking-condition",
                "parameters": {"statusIds": "1,2"},
            }
        ]

    def test_validators_are_sent_alongside_conditions(
        self, mock_client, jira, project, workflow_definition
    ):
        """Validators live in their own array on the transition, not in conditions."""
        workflow_definition["transitions"][1]["validators"] = [
            {
                "ruleKey": "system:field-required-validator",
                "parameters": {"fieldId": "Severity"},
            }
        ]

        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        completed = transition_named(jira.payload(CREATE_PATH), "Incident Completed")

        assert completed["validators"] == [
            {
                "ruleKey": "system:field-required-validator",
                "parameters": {"fieldId": "customfield_10050"},
            }
        ]

    def test_payload_is_validated_before_it_is_created(
        self, mock_client, jira, project, workflow_definition
    ):
        """The validation endpoint reports why a payload is bad; create returns a bare 400."""
        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        assert jira.paths.index(VALIDATE_PATH) < jira.paths.index(CREATE_PATH)
        assert jira.payload(VALIDATE_PATH) == {
            "payload": jira.payload(CREATE_PATH),
            "validationOptions": {"levels": ["ERROR"]},
        }

    def test_validation_errors_are_raised_and_stop_creation(
        self, mock_client, jira, project, workflow_definition
    ):
        """Creating a payload Jira already rejected leaves a half-built project."""
        jira.validation_errors = [
            {
                "code": "NON_UNIQUE_STATUS_NAME",
                "message": "Status name must be unique.",
                "level": "ERROR",
                "type": "STATUS",
            }
        ]

        with pytest.raises(ValueError) as raised:
            Workflows(mock_client).create(
                "SENTEST: Incident", "Incident workflow", workflow_definition, project
            )

        assert "NON_UNIQUE_STATUS_NAME" in str(raised.value)
        assert "Status name must be unique." in str(raised.value)
        assert CREATE_PATH not in jira.paths

    def test_warning_level_validation_does_not_stop_creation(
        self, mock_client, jira, project, workflow_definition
    ):
        """Only ERROR-level findings are fatal."""
        jira.validation_errors = [
            {"code": "SOME_ADVICE", "message": "Consider a loop.", "level": "WARNING"}
        ]

        Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        assert CREATE_PATH in jira.paths

    def test_returns_a_workflow_carrying_the_id_rollback_deletes_by(
        self, mock_client, jira, project, workflow_definition
    ):
        """Deployment tracking stores entity_id; rollback deletes with it."""
        workflow = Workflows(mock_client).create(
            "SENTEST: Incident", "Incident workflow", workflow_definition, project
        )

        assert isinstance(workflow, Workflow)
        assert workflow.name == "SENTEST: Incident"
        assert workflow.entity_id == CREATED_WORKFLOW_ID
