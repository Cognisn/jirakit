"""
Unit tests for the Groups module.

Tests cover:
- Group class properties
- Groups.get_groups() method
- Groups.create_group() method
- Groups.create_groups() batch creation
"""

import pytest
from unittest.mock import Mock
from jirakit.groups import Group, Groups


class TestGroupClass:
    """Tests for the Group class."""

    def test_group_initialisation(self, mock_client, sample_group_data):
        """Test Group class initialisation."""
        group = Group(sample_group_data, mock_client)

        assert group.detail == sample_group_data
        assert group.client == mock_client

    def test_group_name_property(self, mock_client, sample_group_data):
        """Test Group.name property."""
        group = Group(sample_group_data, mock_client)

        assert group.name == sample_group_data["name"]

    def test_group_id_property(self, mock_client, sample_group_data):
        """Test Group.id property."""
        group = Group(sample_group_data, mock_client)

        assert group.id == sample_group_data["groupId"]


class TestGroupsGetGroups:
    """Tests for Groups.get_groups() method."""

    def test_get_groups_single_page(self, mock_client, sample_group_data, paginated_response_factory):
        """Test fetching groups from a single page."""
        mock_response = Mock()
        paginated_data = paginated_response_factory(
            [sample_group_data, {**sample_group_data, "name": "group-2", "groupId": "group-456"}],
            is_last=True
        )
        mock_response.json.return_value = paginated_data
        mock_client.get.return_value = mock_response

        groups_manager = Groups(mock_client)
        groups = groups_manager.get_groups()

        assert len(groups) == 2
        assert all(isinstance(g, Group) for g in groups)
        assert groups[0].name == "test-group"
        assert groups[1].name == "group-2"

    def test_get_groups_multiple_pages(self, mock_client, sample_group_data, paginated_response_factory):
        """Test fetching groups across multiple pages."""
        # First page
        mock_response_1 = Mock()
        paginated_data_1 = paginated_response_factory(
            [sample_group_data],
            start_at=0,
            max_results=50,
            is_last=False
        )
        mock_response_1.json.return_value = paginated_data_1

        # Second page
        mock_response_2 = Mock()
        paginated_data_2 = paginated_response_factory(
            [{**sample_group_data, "name": "group-2", "groupId": "group-456"}],
            start_at=50,
            max_results=50,
            is_last=True
        )
        mock_response_2.json.return_value = paginated_data_2

        mock_client.get.side_effect = [mock_response_1, mock_response_2]

        groups_manager = Groups(mock_client)
        groups = groups_manager.get_groups()

        assert len(groups) == 2
        assert mock_client.get.call_count == 2

    def test_get_groups_empty_result(self, mock_client, paginated_response_factory):
        """Test fetching groups when no groups exist."""
        mock_response = Mock()
        paginated_data = paginated_response_factory([], is_last=True)
        mock_response.json.return_value = paginated_data
        mock_client.get.return_value = mock_response

        groups_manager = Groups(mock_client)
        groups = groups_manager.get_groups()

        assert len(groups) == 0


class TestGroupsCreateGroup:
    """Tests for Groups.create_group() method."""

    def test_create_group_success(self, mock_client, sample_group_data):
        """Test successful group creation."""
        mock_response = Mock()
        mock_response.json.return_value = sample_group_data
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response

        groups_manager = Groups(mock_client)
        group = groups_manager.create_group("test-group")

        assert isinstance(group, Group)
        assert group.name == "test-group"
        mock_client.post.assert_called_once()

        # Verify correct API endpoint
        call_args = mock_client.post.call_args
        assert "/rest/api/3/group" in call_args[0][0]

    def test_create_group_with_special_characters(self, mock_client, sample_group_data):
        """Test creating a group with special characters in name."""
        special_name = "test-group-2024@domain"
        special_group_data = {**sample_group_data, "name": special_name}

        mock_response = Mock()
        mock_response.json.return_value = special_group_data
        mock_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_response

        groups_manager = Groups(mock_client)
        group = groups_manager.create_group(special_name)

        assert group.name == special_name


class TestGroupsCreateGroups:
    """Tests for Groups.create_groups() batch creation method."""

    def test_create_groups_all_new(self, mock_client, sample_group_data, paginated_response_factory):
        """Test creating multiple groups when none exist."""
        # Mock get_groups to return empty list
        mock_get_response = Mock()
        mock_get_response.json.return_value = paginated_response_factory([], is_last=True)

        # Mock create_group responses
        mock_create_response = Mock()
        mock_create_response.json.return_value = sample_group_data
        mock_create_response.raise_for_status = Mock()

        mock_client.get.return_value = mock_get_response
        mock_client.post.return_value = mock_create_response

        groups_manager = Groups(mock_client)
        groups = groups_manager.create_groups(["group-1", "group-2"])

        assert len(groups) == 2
        assert mock_client.post.call_count == 2

    def test_create_groups_some_exist(self, mock_client, sample_group_data, paginated_response_factory):
        """Test creating groups when some already exist."""
        existing_group = sample_group_data
        existing_group["name"] = "existing-group"

        # Mock get_groups to return existing group
        mock_get_response = Mock()
        mock_get_response.json.return_value = paginated_response_factory([existing_group], is_last=True)

        # Mock create_group for new group
        new_group_data = {**sample_group_data, "name": "new-group", "groupId": "group-789"}
        mock_create_response = Mock()
        mock_create_response.json.return_value = new_group_data
        mock_create_response.raise_for_status = Mock()

        mock_client.get.return_value = mock_get_response
        mock_client.post.return_value = mock_create_response

        groups_manager = Groups(mock_client)
        groups = groups_manager.create_groups(["existing-group", "new-group"])

        # Should only create the new group, not the existing one
        assert len(groups) == 1
        assert groups[0].name == "new-group"
        assert mock_client.post.call_count == 1

    def test_create_groups_all_exist(self, mock_client, sample_group_data, paginated_response_factory):
        """Test creating groups when all already exist."""
        # Mock get_groups to return all groups
        mock_get_response = Mock()
        mock_get_response.json.return_value = paginated_response_factory([sample_group_data], is_last=True)

        mock_client.get.return_value = mock_get_response

        groups_manager = Groups(mock_client)
        groups = groups_manager.create_groups(["test-group"])

        # Should not create any groups
        assert len(groups) == 0
        assert mock_client.post.call_count == 0

    def test_create_groups_empty_list(self, mock_client):
        """Test creating groups with empty list."""
        groups_manager = Groups(mock_client)
        groups = groups_manager.create_groups([])

        assert len(groups) == 0
        assert mock_client.post.call_count == 0
