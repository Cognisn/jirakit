#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the DeploymentTracker class.

Tests cover:
- Tracker initialisation
- Resource tracking
- Status management
- Loading and saving
- Summary generation
- File operations
"""

import pytest
import json
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, mock_open

from jirakit.projects.tracking import DeploymentTracker


class TestDeploymentTrackerInitialisation:
    """Test DeploymentTracker initialisation."""

    def test_tracker_initialisation_minimal(self, tmp_path):
        """Test tracker initialises with minimal parameters."""
        tracking_dir = str(tmp_path / "tracking")

        tracker = DeploymentTracker(project_key="TEST", tracking_dir=tracking_dir)

        assert tracker.project_key == "TEST"
        assert tracker.tracking_dir == tracking_dir
        assert tracker.data["project_key"] == "TEST"
        assert tracker.data["status"] == "in_progress"
        assert tracker.data["project_id"] is None
        assert tracker.data["project_name"] is None
        assert tracker.data["template_name"] is None

    def test_tracker_initialisation_full(self, tmp_path):
        """Test tracker initialises with all parameters."""
        tracking_dir = str(tmp_path / "tracking")

        tracker = DeploymentTracker(
            project_key="TEST",
            project_id="10001",
            project_name="Test Project",
            template_name="Test Template",
            tracking_dir=tracking_dir,
        )

        assert tracker.project_key == "TEST"
        assert tracker.data["project_id"] == "10001"
        assert tracker.data["project_name"] == "Test Project"
        assert tracker.data["template_name"] == "Test Template"

    def test_tracker_creates_directory(self, tmp_path):
        """Test tracker creates tracking directory if it doesn't exist."""
        tracking_dir = str(tmp_path / "tracking")

        assert not os.path.exists(tracking_dir)

        tracker = DeploymentTracker(project_key="TEST", tracking_dir=tracking_dir)

        assert os.path.exists(tracking_dir)

    def test_tracker_creates_tracking_file(self, tmp_path):
        """Test tracker creates tracking file on initialisation."""
        tracking_dir = str(tmp_path / "tracking")

        tracker = DeploymentTracker(project_key="TEST", tracking_dir=tracking_dir)

        tracking_file = os.path.join(tracking_dir, "TEST.json")
        assert os.path.exists(tracking_file)

    def test_tracker_data_structure(self, tmp_path):
        """Test tracker initialises with correct data structure."""
        tracking_dir = str(tmp_path / "tracking")

        tracker = DeploymentTracker(project_key="TEST", tracking_dir=tracking_dir)

        # Check top-level keys
        assert "project_key" in tracker.data
        assert "project_id" in tracker.data
        assert "deployment_started" in tracker.data
        assert "deployment_completed" in tracker.data
        assert "status" in tracker.data
        assert "resources_created" in tracker.data
        assert "errors" in tracker.data

        # Check resources structure
        resources = tracker.data["resources_created"]
        assert "custom_fields" in resources
        assert "issue_types" in resources
        assert "screens" in resources
        assert "screen_schemes" in resources
        assert "issue_type_screen_schemes" in resources
        assert "issue_type_schemes" in resources
        assert "workflows" in resources
        assert "workflow_schemes" in resources

        # All should be empty lists
        for resource_list in resources.values():
            assert isinstance(resource_list, list)
            assert len(resource_list) == 0


class TestDeploymentTrackerSetters:
    """Test DeploymentTracker setter methods."""

    def test_set_project_id(self, tmp_path):
        """Test setting project ID."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracker.set_project_id("10001")

        assert tracker.data["project_id"] == "10001"

    def test_set_deployed_by(self, tmp_path):
        """Test setting deployed by user."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracker.set_deployed_by("user@example.com")

        assert tracker.data["deployed_by"] == "user@example.com"


class TestDeploymentTrackerResourceTracking:
    """Test resource tracking methods."""

    def test_track_custom_field(self, tmp_path):
        """Test tracking custom field creation."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracker.track_custom_field("10001", "Custom Field")

        fields = tracker.data["resources_created"]["custom_fields"]
        assert len(fields) == 1
        assert fields[0]["id"] == "10001"
        assert fields[0]["name"] == "Custom Field"
        assert "created_at" in fields[0]

    def test_track_issue_type(self, tmp_path):
        """Test tracking issue type creation."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracker.track_issue_type("10001", "TEST: Task")

        issue_types = tracker.data["resources_created"]["issue_types"]
        assert len(issue_types) == 1
        assert issue_types[0]["id"] == "10001"
        assert issue_types[0]["name"] == "TEST: Task"
        assert "created_at" in issue_types[0]

    def test_track_screen(self, tmp_path):
        """Test tracking screen creation."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracker.track_screen("10001", "TEST: Task Screen")

        screens = tracker.data["resources_created"]["screens"]
        assert len(screens) == 1
        assert screens[0]["id"] == "10001"
        assert screens[0]["name"] == "TEST: Task Screen"

    def test_track_screen_scheme(self, tmp_path):
        """Test tracking screen scheme creation."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracker.track_screen_scheme("10001", "TEST: Screen Scheme")

        schemes = tracker.data["resources_created"]["screen_schemes"]
        assert len(schemes) == 1
        assert schemes[0]["id"] == "10001"
        assert schemes[0]["name"] == "TEST: Screen Scheme"

    def test_track_issue_type_screen_scheme(self, tmp_path):
        """Test tracking issue type screen scheme creation."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracker.track_issue_type_screen_scheme("10001", "TEST: ITSS")

        schemes = tracker.data["resources_created"]["issue_type_screen_schemes"]
        assert len(schemes) == 1
        assert schemes[0]["id"] == "10001"
        assert schemes[0]["name"] == "TEST: ITSS"

    def test_track_issue_type_scheme(self, tmp_path):
        """Test tracking issue type scheme creation."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracker.track_issue_type_scheme("10001", "TEST: Issue Type Scheme")

        schemes = tracker.data["resources_created"]["issue_type_schemes"]
        assert len(schemes) == 1
        assert schemes[0]["id"] == "10001"
        assert schemes[0]["name"] == "TEST: Issue Type Scheme"

    def test_track_workflow(self, tmp_path):
        """Test tracking workflow creation."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracker.track_workflow("uuid-123", "TEST: Workflow")

        workflows = tracker.data["resources_created"]["workflows"]
        assert len(workflows) == 1
        assert workflows[0]["entity_id"] == "uuid-123"
        assert workflows[0]["name"] == "TEST: Workflow"

    def test_track_workflow_scheme(self, tmp_path):
        """Test tracking workflow scheme creation."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracker.track_workflow_scheme("10001", "TEST: Workflow Scheme")

        schemes = tracker.data["resources_created"]["workflow_schemes"]
        assert len(schemes) == 1
        assert schemes[0]["id"] == "10001"
        assert schemes[0]["name"] == "TEST: Workflow Scheme"

    def test_track_multiple_resources(self, tmp_path):
        """Test tracking multiple resources."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        # Track multiple issue types
        tracker.track_issue_type("10001", "TEST: Task")
        tracker.track_issue_type("10002", "TEST: Bug")
        tracker.track_issue_type("10003", "TEST: Story")

        # Track multiple screens
        tracker.track_screen("10001", "TEST: Task Screen")
        tracker.track_screen("10002", "TEST: Bug Screen")

        issue_types = tracker.data["resources_created"]["issue_types"]
        screens = tracker.data["resources_created"]["screens"]

        assert len(issue_types) == 3
        assert len(screens) == 2


class TestDeploymentTrackerErrorTracking:
    """Test error tracking functionality."""

    def test_track_error(self, tmp_path):
        """Test tracking an error."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracker.track_error("Test error message")

        errors = tracker.data["errors"]
        assert len(errors) == 1
        assert errors[0]["message"] == "Test error message"
        assert "timestamp" in errors[0]

    def test_track_multiple_errors(self, tmp_path):
        """Test tracking multiple errors."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracker.track_error("Error 1")
        tracker.track_error("Error 2")
        tracker.track_error("Error 3")

        errors = tracker.data["errors"]
        assert len(errors) == 3
        assert errors[0]["message"] == "Error 1"
        assert errors[1]["message"] == "Error 2"
        assert errors[2]["message"] == "Error 3"


class TestDeploymentTrackerStatus:
    """Test status management methods."""

    def test_mark_completed(self, tmp_path):
        """Test marking deployment as completed."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        assert tracker.data["status"] == "in_progress"
        assert tracker.data["deployment_completed"] is None

        tracker.mark_completed()

        assert tracker.data["status"] == "completed"
        assert tracker.data["deployment_completed"] is not None

    def test_mark_failed(self, tmp_path):
        """Test marking deployment as failed."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracker.mark_failed()

        assert tracker.data["status"] == "failed"
        assert tracker.data["deployment_completed"] is not None

    def test_mark_partial(self, tmp_path):
        """Test marking deployment as partial."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracker.mark_partial()

        assert tracker.data["status"] == "partial"
        assert tracker.data["deployment_completed"] is not None


class TestDeploymentTrackerLoad:
    """Test loading tracking data."""

    def test_load_existing_tracker(self, tmp_path):
        """Test loading existing tracker."""
        tracking_dir = str(tmp_path / "tracking")

        # Create tracker
        tracker1 = DeploymentTracker("TEST", tracking_dir=tracking_dir)
        tracker1.track_issue_type("10001", "TEST: Task")
        tracker1.mark_completed()

        # Load tracker
        tracker2 = DeploymentTracker.load("TEST", tracking_dir)

        assert tracker2 is not None
        assert tracker2.project_key == "TEST"
        assert tracker2.data["status"] == "completed"
        assert len(tracker2.data["resources_created"]["issue_types"]) == 1

    def test_load_nonexistent_tracker(self, tmp_path):
        """Test loading non-existent tracker returns None."""
        tracking_dir = str(tmp_path / "tracking")
        os.makedirs(tracking_dir, exist_ok=True)

        tracker = DeploymentTracker.load("NOTEXIST", tracking_dir)

        assert tracker is None

    def test_load_from_nonexistent_directory(self, tmp_path):
        """Test loading from non-existent directory returns None."""
        tracking_dir = str(tmp_path / "nonexistent")

        tracker = DeploymentTracker.load("TEST", tracking_dir)

        assert tracker is None


class TestDeploymentTrackerSummary:
    """Test summary generation."""

    def test_get_summary_empty(self, tmp_path):
        """Test getting summary with no resources."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        summary = tracker.get_summary()

        assert summary["project_key"] == "TEST"
        assert summary["status"] == "in_progress"
        assert summary["custom_fields_created"] == 0
        assert summary["issue_types_created"] == 0
        assert summary["screens_created"] == 0
        assert summary["screen_schemes_created"] == 0
        assert summary["workflows_created"] == 0
        assert summary["errors"] == 0

    def test_get_summary_with_resources(self, tmp_path):
        """Test getting summary with resources."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        # Add resources
        tracker.track_issue_type("10001", "TEST: Task")
        tracker.track_issue_type("10002", "TEST: Bug")
        tracker.track_screen("10001", "TEST: Screen")
        tracker.track_workflow("uuid", "TEST: Workflow")
        tracker.track_error("Test error")

        summary = tracker.get_summary()

        assert summary["issue_types_created"] == 2
        assert summary["screens_created"] == 1
        assert summary["workflows_created"] == 1
        assert summary["errors"] == 1

    def test_get_summary_after_completion(self, tmp_path):
        """Test getting summary after marking completed."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracker.mark_completed()
        summary = tracker.get_summary()

        assert summary["status"] == "completed"
        assert summary["completed"] is not None


class TestDeploymentTrackerFileOperations:
    """Test file operations."""

    def test_save_creates_file(self, tmp_path):
        """Test save creates tracking file."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracking_file = os.path.join(tracking_dir, "TEST.json")
        assert os.path.exists(tracking_file)

        # Verify file contents
        with open(tracking_file, "r") as f:
            data = json.load(f)

        assert data["project_key"] == "TEST"
        assert data["status"] == "in_progress"

    def test_save_updates_file(self, tmp_path):
        """Test save updates tracking file."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        # Modify tracker
        tracker.track_issue_type("10001", "TEST: Task")
        tracker.save()

        # Load file directly
        tracking_file = os.path.join(tracking_dir, "TEST.json")
        with open(tracking_file, "r") as f:
            data = json.load(f)

        assert len(data["resources_created"]["issue_types"]) == 1

    def test_delete_tracking_file(self, tmp_path):
        """Test deleting tracking file."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracking_file = os.path.join(tracking_dir, "TEST.json")
        assert os.path.exists(tracking_file)

        tracker.delete_tracking_file()

        assert not os.path.exists(tracking_file)

    def test_delete_nonexistent_file(self, tmp_path):
        """Test deleting non-existent file doesn't raise error."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        # Delete file manually
        os.remove(tracker.tracking_file)

        # Should not raise error
        tracker.delete_tracking_file()


class TestDeploymentTrackerPersistence:
    """Test data persistence across save/load cycles."""

    def test_persistence_across_saves(self, tmp_path):
        """Test data persists across multiple saves."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        # Add data and save
        tracker.track_issue_type("10001", "TEST: Task")
        tracker.save()

        # Add more data and save
        tracker.track_screen("10001", "TEST: Screen")
        tracker.save()

        # Load fresh copy
        tracker2 = DeploymentTracker.load("TEST", tracking_dir)

        assert len(tracker2.data["resources_created"]["issue_types"]) == 1
        assert len(tracker2.data["resources_created"]["screens"]) == 1

    def test_complete_lifecycle(self, tmp_path):
        """Test complete deployment lifecycle."""
        tracking_dir = str(tmp_path / "tracking")

        # Create and populate tracker
        tracker = DeploymentTracker(
            project_key="TEST",
            project_id="10001",
            project_name="Test Project",
            template_name="Test Template",
            tracking_dir=tracking_dir,
        )

        tracker.set_deployed_by("user@example.com")
        tracker.track_issue_type("10001", "TEST: Task")
        tracker.track_issue_type("10002", "TEST: Bug")
        tracker.track_screen("10001", "TEST: Screen")
        tracker.track_workflow("uuid", "TEST: Workflow")
        tracker.mark_completed()

        # Load and verify
        loaded = DeploymentTracker.load("TEST", tracking_dir)

        assert loaded.data["project_id"] == "10001"
        assert loaded.data["project_name"] == "Test Project"
        assert loaded.data["template_name"] == "Test Template"
        assert loaded.data["deployed_by"] == "user@example.com"
        assert loaded.data["status"] == "completed"
        assert len(loaded.data["resources_created"]["issue_types"]) == 2
        assert len(loaded.data["resources_created"]["screens"]) == 1
        assert len(loaded.data["resources_created"]["workflows"]) == 1


class TestDeploymentTrackerEdgeCases:
    """Test edge cases and error conditions."""

    def test_tracking_with_special_characters(self, tmp_path):
        """Test tracking resources with special characters in names."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        tracker.track_issue_type(
            "10001", "TEST: Task with 'quotes' and \"double quotes\""
        )
        tracker.track_screen("10001", "TEST: Screen with émoji 🎉")

        issue_types = tracker.data["resources_created"]["issue_types"]
        screens = tracker.data["resources_created"]["screens"]

        assert "quotes" in issue_types[0]["name"]
        assert "émoji" in screens[0]["name"]

    def test_project_key_with_numbers(self, tmp_path):
        """Test project key with numbers."""
        tracking_dir = str(tmp_path / "tracking")

        tracker = DeploymentTracker("TEST123", tracking_dir=tracking_dir)

        assert tracker.project_key == "TEST123"
        assert tracker.data["project_key"] == "TEST123"

    def test_long_error_messages(self, tmp_path):
        """Test tracking long error messages."""
        tracking_dir = str(tmp_path / "tracking")
        tracker = DeploymentTracker("TEST", tracking_dir=tracking_dir)

        long_message = "Error: " + "x" * 1000

        tracker.track_error(long_message)

        errors = tracker.data["errors"]
        assert len(errors[0]["message"]) > 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
