"""
Unit tests for the Projects module.

Tests cover:
- Project class properties (basic)
- Projects.get_all() method
- Projects.delete_project() method

Note: Project class has complex initialization that loads settings,
so we test with skip_load=True to avoid dependencies on other modules.
"""

from unittest.mock import Mock
from jirakit.projects import Project, Projects


class TestProjectClass:
    """Tests for the Project class."""

    def test_project_initialisation_skip_load(self, mock_client, sample_project_data):
        """Test Project class initialisation with skip_load."""
        project = Project(sample_project_data, mock_client, skip_load=True)

        assert project.project_detail == sample_project_data
        assert project.client == mock_client

    def test_project_properties_skip_load(self, mock_client, sample_project_data):
        """Test Project properties with skip_load."""
        project = Project(sample_project_data, mock_client, skip_load=True)

        assert project.id == sample_project_data["id"]
        assert project.key == sample_project_data["key"]
        assert project.name == sample_project_data["name"]


class TestProjectsOperations:
    """Tests for Projects operations."""

    def test_get_all_projects_deleted_status(
        self, mock_client, sample_project_data, paginated_response_factory
    ):
        """Test fetching all projects with deleted status (uses skip_load)."""
        projects_data = [sample_project_data]

        mock_response = Mock()
        mock_response.json.return_value = paginated_response_factory(
            projects_data, is_last=True
        )
        mock_client.get.return_value = mock_response

        projects_manager = Projects(mock_client)
        # Use status='deleted' which will use skip_load=True
        projects = projects_manager.get_all(status="deleted")

        assert len(projects) == 1
        assert isinstance(projects[0], Project)

    def test_delete_project(self, mock_client, sample_project_data):
        """Test deleting a project."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_client.delete.return_value = mock_response

        project = Project(sample_project_data, mock_client, skip_load=True)
        projects_manager = Projects(mock_client)

        projects_manager.delete_project(project)

        mock_client.delete.assert_called_once()
        call_args = mock_client.delete.call_args
        assert f"/rest/api/3/project/{sample_project_data['id']}" in call_args[0][0]
