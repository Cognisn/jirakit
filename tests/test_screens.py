"""
Unit tests for the Screens module.

Tests cover:
- Screen class properties and methods
- ScreenScheme class properties
- Screens.create() method
- Screens.create_screen_scheme() method
- Screens.get_screen() and get_all_screens() methods
- Screen.get_tabs() and create_tab() methods
- Bug fix verification: double slash in delete URL
- Bug fix verification: projectKey parameter
"""

import pytest
from unittest.mock import Mock
from jirakit.screens import Screen, ScreenScheme, Screens


class TestScreenClass:
    """Tests for the Screen class."""

    def test_screen_initialisation(self, mock_client, sample_screen_data):
        """Test Screen class initialisation."""
        screen = Screen(sample_screen_data, mock_client)

        assert screen.screen_detail == sample_screen_data
        assert screen.client == mock_client

    def test_screen_properties(self, mock_client, sample_screen_data):
        """Test Screen properties."""
        screen = Screen(sample_screen_data, mock_client)

        assert screen.id == sample_screen_data["id"]
        assert screen.name == sample_screen_data["name"]
        assert screen.description == sample_screen_data["description"]

    def test_get_tabs(self, mock_client, sample_screen_data, sample_project_data):
        """Test Screen.get_tabs() method."""
        from jirakit.projects import Project
        from unittest.mock import MagicMock

        tabs_data = [{"id": "10000", "name": "Tab 1"}, {"id": "10001", "name": "Tab 2"}]

        mock_response = Mock()
        mock_response.json.return_value = tabs_data
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response

        screen = Screen(sample_screen_data, mock_client)

        # Create a mock project with only the needed properties
        mock_project = MagicMock(spec=Project)
        mock_project.id = "10000"
        mock_project.key = "TEST"

        tabs = screen.get_tabs(mock_project)

        assert len(tabs) == 2
        mock_client.get.assert_called_once()

        # Verify correct API endpoint with projectKey (not projectId)
        call_args = mock_client.get.call_args
        assert f"projectKey={mock_project.key}" in call_args[1]["path"]

    def test_create_tab(self, mock_client, sample_screen_data):
        """Test Screen.create_tab() method."""
        tab_data = {"id": "10000", "name": "New Tab"}

        mock_response = Mock()
        mock_response.json.return_value = tab_data
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response

        screen = Screen(sample_screen_data, mock_client)
        result = screen.create_tab(
            "New Tab", ["customfield_10001", "customfield_10002"]
        )

        assert result["id"] == "10000"
        assert result["name"] == "New Tab"

        # Should be called 3 times: once for tab, twice for fields
        assert mock_client.post.call_count == 3


class TestScreenSchemeClass:
    """Tests for the ScreenScheme class."""

    def test_screen_scheme_initialisation(self, mock_client):
        """Test ScreenScheme class initialisation."""
        scheme_data = {
            "id": "10000",
            "name": "Test Screen Scheme",
            "description": "A test screen scheme",
            "screens": {"default": "10001", "edit": "10002", "view": "10003"},
        }

        scheme = ScreenScheme(scheme_data, mock_client)

        assert scheme.detail == scheme_data
        assert scheme.client == mock_client

    def test_screen_scheme_properties(self, mock_client):
        """Test ScreenScheme properties."""
        scheme_data = {
            "id": "10000",
            "name": "Test Screen Scheme",
            "description": "A test screen scheme",
            "screens": {},
        }

        scheme = ScreenScheme(scheme_data, mock_client)

        assert scheme.id == "10000"
        assert scheme.name == "Test Screen Scheme"
        assert scheme.description == "A test screen scheme"

    def test_get_screen_ids(self, mock_client):
        """Test ScreenScheme.get_screen_ids() method."""
        scheme_data = {
            "id": "10000",
            "name": "Test Screen Scheme",
            "description": "A test screen scheme",
            "screens": {
                "default": "10001",
                "edit": "10002",
                "view": "10001",  # Duplicate to test uniqueness
            },
        }

        scheme = ScreenScheme(scheme_data, mock_client)
        screen_ids = scheme.get_screen_ids()

        assert len(screen_ids) == 2  # Should be unique
        assert "10001" in screen_ids
        assert "10002" in screen_ids


class TestScreensCreate:
    """Tests for Screens.create() method."""

    def test_create_screen_success(self, mock_client, sample_screen_data):
        """Test successful screen creation."""
        mock_response = Mock()
        mock_response.json.return_value = sample_screen_data
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response

        screens_manager = Screens(mock_client)
        screen = screens_manager.create("Test Screen", "A test screen")

        assert isinstance(screen, Screen)
        assert screen.name == "Test Screen"
        mock_client.post.assert_called_once()

        # Verify correct API endpoint (v3, not v2)
        call_args = mock_client.post.call_args
        assert "/rest/api/3/screens" in call_args[0][0]

    def test_create_screen_with_empty_description(
        self, mock_client, sample_screen_data
    ):
        """Test creating a screen with empty description."""
        screen_data = {**sample_screen_data, "description": ""}

        mock_response = Mock()
        mock_response.json.return_value = screen_data
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response

        screens_manager = Screens(mock_client)
        screen = screens_manager.create("Test Screen", "")

        assert screen.description == ""


class TestScreensCreateScreenScheme:
    """Tests for Screens.create_screen_scheme() method."""

    def test_create_screen_scheme_success(self, mock_client):
        """Test successful screen scheme creation."""
        scheme_data = {
            "id": "10000",
            "name": "Test Scheme",
            "description": "A test scheme",
            "screens": {"default": "10001", "edit": "10002", "view": "10003"},
        }

        mock_post_response = Mock()
        mock_post_response.json.return_value = {"id": "10000"}
        mock_post_response.raise_for_status = Mock()

        mock_get_response = Mock()
        mock_get_response.json.return_value = {"values": [scheme_data]}
        mock_get_response.raise_for_status = Mock()

        mock_client.post.return_value = mock_post_response
        mock_client.get.return_value = mock_get_response

        screens_manager = Screens(mock_client)
        scheme = screens_manager.create_screen_scheme(
            "Test Scheme", "A test scheme", default="10001", edit="10002", view="10003"
        )

        assert isinstance(scheme, ScreenScheme)
        assert scheme.id == "10000"
        mock_client.post.assert_called_once()
        mock_client.get.assert_called_once()


class TestScreensGetOperations:
    """Tests for Screens get operations."""

    def test_get_screen(self, mock_client, sample_screen_data):
        """Test Screens.get_screen() method."""
        mock_response = Mock()
        mock_response.json.return_value = {"values": [sample_screen_data]}
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response

        screens_manager = Screens(mock_client)
        screen = screens_manager.get_screen("10000")

        assert isinstance(screen, Screen)
        assert screen.id == sample_screen_data["id"]

    def test_get_all_screens(
        self, mock_client, sample_screen_data, paginated_response_factory
    ):
        """Test Screens.get_all_screens() method."""
        screens_data = [
            sample_screen_data,
            {**sample_screen_data, "id": "10001", "name": "Screen 2"},
        ]

        mock_response = Mock()
        mock_response.json.return_value = paginated_response_factory(
            screens_data, is_last=True
        )
        mock_client.get.return_value = mock_response

        screens_manager = Screens(mock_client)
        screens = screens_manager.get_all_screens()

        assert len(screens) == 2
        assert all(isinstance(s, Screen) for s in screens)


class TestScreensDeleteOperations:
    """Tests for Screens delete operations."""

    def test_delete_screen(self, mock_client, sample_screen_data):
        """Test Screens.delete_screen() method - verifies no double slash bug."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_client.delete.return_value = mock_response

        screen = Screen(sample_screen_data, mock_client)
        screens_manager = Screens(mock_client)

        screens_manager.delete_screen(screen)

        mock_client.delete.assert_called_once()

        # Verify no double slash in URL (bug fix verification)
        call_args = mock_client.delete.call_args
        url = call_args[0][0]
        assert "/rest/api/3/screens//" not in url
        assert f"/rest/api/3/screens/{screen.id}" in url

    def test_delete_screen_scheme(self, mock_client):
        """Test Screens.delete_screen_scheme() method."""
        scheme_data = {
            "id": "10000",
            "name": "Test Scheme",
            "description": "A test scheme",
        }

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_client.delete.return_value = mock_response

        scheme = ScreenScheme(scheme_data, mock_client)
        screens_manager = Screens(mock_client)

        screens_manager.delete_screen_scheme(scheme)

        mock_client.delete.assert_called_once()

        # Verify correct API endpoint
        call_args = mock_client.delete.call_args
        assert f"/rest/api/3/screenscheme/{scheme.id}" in call_args[0][0]
