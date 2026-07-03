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

import pytest
from unittest.mock import Mock
from jirakit.workflows import Workflow, WorkflowScheme, Workflows
from jirakit.workflows.statuses import Status, Statuses


class TestWorkflowClass:
    """Tests for the Workflow class."""

    def test_workflow_initialisation(self, mock_client, sample_workflow_data):
        """Test Workflow class initialisation."""
        workflow = Workflow(sample_workflow_data, mock_client)

        assert workflow.details == sample_workflow_data
        assert workflow.client == mock_client

    def test_workflow_properties(self, mock_client, sample_workflow_data):
        """Test Workflow properties."""
        workflow = Workflow(sample_workflow_data, mock_client)

        assert workflow.name == sample_workflow_data["name"]
        assert workflow.description == sample_workflow_data["description"]


class TestWorkflowsGetAll:
    """Tests for Workflows.get_all() method."""

    def test_get_all_workflows(self, mock_client, sample_workflow_data, paginated_response_factory):
        """Test fetching all workflows."""
        workflows_data = [sample_workflow_data]

        mock_response = Mock()
        mock_response.json.return_value = paginated_response_factory(workflows_data, is_last=True)
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

    def test_get_all_statuses(self, mock_client, sample_status_data, paginated_response_factory):
        """Test fetching all statuses."""
        statuses_data = [sample_status_data]

        mock_response = Mock()
        mock_response.json.return_value = paginated_response_factory(statuses_data, is_last=True)
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
