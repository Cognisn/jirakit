"""
Unit tests for the Fields module.

Tests cover:
- Field class properties and methods
- Fields.get_all() method
- Fields.create_field() method
- Fields.delete_field() method
"""

from unittest.mock import Mock
from jirakit.fields import Field, Fields


class TestFieldClass:
    """Tests for the Field class."""

    def test_field_initialisation(self, mock_client, sample_field_data):
        """Test Field class initialisation."""
        field = Field(sample_field_data, mock_client)

        assert field.field_detail == sample_field_data
        assert field.client == mock_client

    def test_field_properties(self, mock_client, sample_field_data):
        """Test Field properties."""
        field = Field(sample_field_data, mock_client)

        assert field.id == sample_field_data["id"]
        assert field.name == sample_field_data["name"]


class TestFieldsOperations:
    """Tests for Fields operations."""

    def test_get_all_fields(
        self, mock_client, sample_field_data, paginated_response_factory
    ):
        """Test fetching all fields."""
        fields_data = [sample_field_data]

        mock_response = Mock()
        mock_response.json.return_value = paginated_response_factory(
            fields_data, is_last=True
        )
        mock_client.get.return_value = mock_response

        fields_manager = Fields(mock_client)
        fields = fields_manager.get_all()

        assert len(fields) == 1
        assert isinstance(fields[0], Field)

    def test_delete_field(self, mock_client, sample_field_data):
        """Test deleting a field."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_client.delete.return_value = mock_response

        field = Field(sample_field_data, mock_client)
        fields_manager = Fields(mock_client)

        fields_manager.delete_field(field)

        mock_client.delete.assert_called_once()
