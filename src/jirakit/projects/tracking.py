"""
Deployment tracking for template-based project creation.

This module provides functionality to track resources created during template
deployment, enabling precise rollback and cleanup operations.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional


class DeploymentTracker:
    """
    Tracks resources created during template deployment.

    This class maintains a record of all resources created when deploying
    a template to a Jira project. The tracking information is persisted to
    a JSON file, allowing for precise rollback even if deployment fails
    partway through.

    :ivar project_key: The project key being deployed.
    :type project_key: str
    :ivar tracking_dir: Directory where tracking files are stored.
    :type tracking_dir: str
    :ivar tracking_file: Path to the tracking file for this deployment.
    :type tracking_file: str
    :ivar data: The tracking data dictionary.
    :type data: dict
    """

    def __init__(self, project_key: str, project_id: str = None,
                 project_name: str = None, template_name: str = None,
                 tracking_dir: str = ".jirakit_deployments"):
        """
        Initialise a deployment tracker.

        :param project_key: The key of the project being deployed.
        :type project_key: str
        :param project_id: The ID of the project (optional, can be set later).
        :type project_id: str
        :param project_name: The name of the project (optional).
        :type project_name: str
        :param template_name: The name of the template being applied (optional).
        :type template_name: str
        :param tracking_dir: Directory to store tracking files. Defaults to
            '.jirakit_deployments'.
        :type tracking_dir: str
        """
        self.project_key = project_key
        self.tracking_dir = tracking_dir
        self.tracking_file = os.path.join(tracking_dir, f"{project_key}.json")

        # Initialise tracking data
        self.data = {
            "project_key": project_key,
            "project_id": project_id,
            "project_name": project_name,
            "template_name": template_name,
            "deployment_started": datetime.utcnow().isoformat(),
            "deployment_completed": None,
            "deployed_by": None,
            "status": "in_progress",
            "resources_created": {
                "custom_fields": [],
                "issue_types": [],
                "screens": [],
                "screen_schemes": [],
                "issue_type_screen_schemes": [],
                "issue_type_schemes": [],
                "workflows": [],
                "workflow_schemes": []
            },
            "errors": []
        }

        # Create tracking directory if it doesn't exist
        os.makedirs(tracking_dir, exist_ok=True)

        # Save initial state
        self.save()
        logging.info(f"Initialised deployment tracker for {project_key}")

    def set_project_id(self, project_id: str):
        """
        Set the project ID after project creation.

        :param project_id: The ID of the created project.
        :type project_id: str
        """
        self.data["project_id"] = project_id
        self.save()

    def set_deployed_by(self, user_email: str):
        """
        Set the user who performed the deployment.

        :param user_email: Email address of the deploying user.
        :type user_email: str
        """
        self.data["deployed_by"] = user_email
        self.save()

    def track_custom_field(self, field_id: str, name: str):
        """
        Track a custom field creation.

        :param field_id: The ID of the created field.
        :type field_id: str
        :param name: The name of the field.
        :type name: str
        """
        self.data["resources_created"]["custom_fields"].append({
            "id": field_id,
            "name": name,
            "created_at": datetime.utcnow().isoformat()
        })
        self.save()
        logging.debug(f"Tracked custom field: {name} ({field_id})")

    def track_issue_type(self, issue_type_id: str, name: str):
        """
        Track an issue type creation.

        :param issue_type_id: The ID of the created issue type.
        :type issue_type_id: str
        :param name: The name of the issue type.
        :type name: str
        """
        self.data["resources_created"]["issue_types"].append({
            "id": issue_type_id,
            "name": name,
            "created_at": datetime.utcnow().isoformat()
        })
        self.save()
        logging.debug(f"Tracked issue type: {name} ({issue_type_id})")

    def track_screen(self, screen_id: str, name: str):
        """
        Track a screen creation.

        :param screen_id: The ID of the created screen.
        :type screen_id: str
        :param name: The name of the screen.
        :type name: str
        """
        self.data["resources_created"]["screens"].append({
            "id": screen_id,
            "name": name,
            "created_at": datetime.utcnow().isoformat()
        })
        self.save()
        logging.debug(f"Tracked screen: {name} ({screen_id})")

    def track_screen_scheme(self, scheme_id: str, name: str):
        """
        Track a screen scheme creation.

        :param scheme_id: The ID of the created screen scheme.
        :type scheme_id: str
        :param name: The name of the screen scheme.
        :type name: str
        """
        self.data["resources_created"]["screen_schemes"].append({
            "id": scheme_id,
            "name": name,
            "created_at": datetime.utcnow().isoformat()
        })
        self.save()
        logging.debug(f"Tracked screen scheme: {name} ({scheme_id})")

    def track_issue_type_screen_scheme(self, scheme_id: str, name: str):
        """
        Track an issue type screen scheme creation.

        :param scheme_id: The ID of the created scheme.
        :type scheme_id: str
        :param name: The name of the scheme.
        :type name: str
        """
        self.data["resources_created"]["issue_type_screen_schemes"].append({
            "id": scheme_id,
            "name": name,
            "created_at": datetime.utcnow().isoformat()
        })
        self.save()
        logging.debug(f"Tracked issue type screen scheme: {name} ({scheme_id})")

    def track_issue_type_scheme(self, scheme_id: str, name: str):
        """
        Track an issue type scheme creation.

        :param scheme_id: The ID of the created scheme.
        :type scheme_id: str
        :param name: The name of the scheme.
        :type name: str
        """
        self.data["resources_created"]["issue_type_schemes"].append({
            "id": scheme_id,
            "name": name,
            "created_at": datetime.utcnow().isoformat()
        })
        self.save()
        logging.debug(f"Tracked issue type scheme: {name} ({scheme_id})")

    def track_workflow(self, entity_id: str, name: str):
        """
        Track a workflow creation.

        :param entity_id: The entity ID of the created workflow.
        :type entity_id: str
        :param name: The name of the workflow.
        :type name: str
        """
        self.data["resources_created"]["workflows"].append({
            "entity_id": entity_id,
            "name": name,
            "created_at": datetime.utcnow().isoformat()
        })
        self.save()
        logging.debug(f"Tracked workflow: {name} ({entity_id})")

    def track_workflow_scheme(self, scheme_id: str, name: str):
        """
        Track a workflow scheme creation.

        :param scheme_id: The ID of the created workflow scheme.
        :type scheme_id: str
        :param name: The name of the workflow scheme.
        :type name: str
        """
        self.data["resources_created"]["workflow_schemes"].append({
            "id": scheme_id,
            "name": name,
            "created_at": datetime.utcnow().isoformat()
        })
        self.save()
        logging.debug(f"Tracked workflow scheme: {name} ({scheme_id})")

    def track_error(self, error_message: str):
        """
        Track an error that occurred during deployment.

        :param error_message: Description of the error.
        :type error_message: str
        """
        self.data["errors"].append({
            "message": error_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.save()
        logging.warning(f"Tracked error: {error_message}")

    def mark_completed(self):
        """Mark the deployment as completed successfully."""
        self.data["status"] = "completed"
        self.data["deployment_completed"] = datetime.utcnow().isoformat()
        self.save()
        logging.info(f"Deployment marked as completed for {self.project_key}")

    def mark_failed(self):
        """Mark the deployment as failed."""
        self.data["status"] = "failed"
        self.data["deployment_completed"] = datetime.utcnow().isoformat()
        self.save()
        logging.error(f"Deployment marked as failed for {self.project_key}")

    def mark_partial(self):
        """Mark the deployment as partially completed."""
        self.data["status"] = "partial"
        self.data["deployment_completed"] = datetime.utcnow().isoformat()
        self.save()
        logging.warning(f"Deployment marked as partial for {self.project_key}")

    def save(self):
        """Save tracking data to file."""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save tracking file: {e}")

    @classmethod
    def load(cls, project_key: str, tracking_dir: str = ".jirakit_deployments") -> Optional['DeploymentTracker']:
        """
        Load tracking data for a project.

        :param project_key: The project key to load tracking for.
        :type project_key: str
        :param tracking_dir: Directory where tracking files are stored.
        :type tracking_dir: str
        :return: DeploymentTracker instance if tracking file exists, None otherwise.
        :rtype: Optional[DeploymentTracker]
        """
        tracking_file = os.path.join(tracking_dir, f"{project_key}.json")

        if not os.path.exists(tracking_file):
            logging.info(f"No tracking file found for {project_key}")
            return None

        try:
            with open(tracking_file, 'r') as f:
                data = json.load(f)

            # Create tracker instance and load data
            tracker = cls.__new__(cls)
            tracker.project_key = project_key
            tracker.tracking_dir = tracking_dir
            tracker.tracking_file = tracking_file
            tracker.data = data

            logging.info(f"Loaded tracking data for {project_key}")
            return tracker

        except Exception as e:
            logging.error(f"Failed to load tracking file for {project_key}: {e}")
            return None

    def get_summary(self) -> Dict:
        """
        Get a summary of the deployment.

        :return: Dictionary with deployment summary.
        :rtype: dict
        """
        return {
            "project_key": self.data["project_key"],
            "status": self.data["status"],
            "started": self.data["deployment_started"],
            "completed": self.data["deployment_completed"],
            "custom_fields_created": len(self.data["resources_created"]["custom_fields"]),
            "issue_types_created": len(self.data["resources_created"]["issue_types"]),
            "screens_created": len(self.data["resources_created"]["screens"]),
            "screen_schemes_created": len(self.data["resources_created"]["screen_schemes"]),
            "workflows_created": len(self.data["resources_created"]["workflows"]),
            "errors": len(self.data["errors"])
        }

    def delete_tracking_file(self):
        """Delete the tracking file after successful rollback."""
        try:
            if os.path.exists(self.tracking_file):
                os.remove(self.tracking_file)
                logging.info(f"Deleted tracking file for {self.project_key}")
        except Exception as e:
            logging.error(f"Failed to delete tracking file: {e}")
