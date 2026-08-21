import logging
import time

from jirakit.fields import Field
from jirakit.issues import Issues
from jirakit.projects.tracking import DeploymentTracker

# Deleting a project does not immediately release the schemes assigned to it, so
# a dependent deletion can be refused for a while after the project has gone.
DEFAULT_ROLLBACK_RETRY_SECONDS = 30.0
ROLLBACK_RETRY_INTERVAL = 5.0

# Resources a deployment creates but deliberately does not delete, because they
# are global and may be shared with projects this rollback knows nothing about.
SHARED_RESOURCES_LEFT = [
    "Custom fields created by this deployment were not deleted, as a field may be "
    "shared with other projects.",
    "Statuses created by this deployment were not deleted, as a status is global "
    "and may be shared with other workflows.",
]


class Project:
    """
    Represents a Project and provides functionalities for managing its settings,
    fields, issue types, screen schemes, workflows, and various related entities.

    This class interacts with a project's related configurations through a client
    interface. It can load project settings, manage screen schemes, issue type
    schemes, and workflow schemes, among others. It is designed for use in systems
    where project configurations need to be programmatically accessed or modified.

    :ivar project_detail: Dictionary containing raw details about the project.
    :type project_detail: dict
    :ivar client: Client interface for making API calls.
    :type client: object
    :ivar project_fields: List of fields associated with the project.
    :type project_fields: list
    :ivar issue_types: List of issue types defined for the project.
    :type issue_types: list
    :ivar issue_type_schemes: List of issue type schemes applied to the project.
    :type issue_type_schemes: list
    :ivar issue_type_scheme_mappings: Dictionary mapping issue type schemes to their
        respective settings.
    :type issue_type_scheme_mappings: dict
    :ivar screens: List of screens associated with the project.
    :type screens: list
    :ivar screen_tabs: Dictionary mapping screen IDs to their respective tabs.
    :type screen_tabs: dict
    :ivar screen_schemes: List of screen schemes configured for the project.
    :type screen_schemes: list
    :ivar issue_type_screen_schemes: List of issue type screen schemes assigned to
        the project.
    :type issue_type_screen_schemes: list
    :ivar workflows: List of workflows associated with the project.
    :type workflows: list
    """

    def __init__(self, project_detail, client, skip_load=False):
        """
        Initializes a new instance of the class that manages project settings and
        metadata. It sets up various project-related attributes and optionally
        loads project configuration settings.

        :param project_detail: Contains detailed project information used for
            initializing the project settings.
        :type project_detail: Any
        :param client: The client interface or API client used for interacting
            with project-related data.
        :type client: Any
        :param skip_load: Flag that determines whether to skip loading project
            configuration settings during initialization. Default is False.
        :type skip_load: bool
        """
        self.project_detail = project_detail
        self.client = client
        self.project_fields = []
        self.issue_types = []
        self.issue_type_schemes = []
        self.issue_type_scheme_mappings = {}
        self.screens = []
        self.screen_tabs = {}
        self.screen_schemes = []
        self.issue_type_screen_schemes = []
        self.workflows = []

        if not skip_load:
            self._load_project_settings()

    def issues(self) -> Issues:
        """
        Returns an instance of the Issues class, which provides methods for interacting
        with issue-related data. This method initializes the Issues class with the
        current instance and client.

        :return: An instance of the Issues class.
        :rtype: Issues
        """
        return Issues(self, self.client)

    def _load_project_settings(self):
        """
        Loads the project settings and initializes various attributes with project-related
        information retrieved using API calls. This function prepares the project by
        fetching issue type schemes, screen schemes, screen tabs, fields, and screen
        mappings, and organizes them into the respective data structures.

        The process includes:
        - Retrieving and associating issue type schemes and issue type screen schemes.
        - Mapping the screen schemes to the corresponding screen data.
        - Populating the list of issue types and screen schemes for the project.
        - Gathering screen tab information and associated fields for each screen.
        - Aggregating and storing all relevant field data in the project fields.

        This ensures that the project attributes contain the most up-to-date and detailed
        information about the project's issue and screen configurations.

        :param self: Reference to the current instance of the class.
        """
        self.issue_type_schemes = (
            self.client.issue_types().get_all_issue_type_schemes_for_project(self)
        )
        self.issue_type_screen_schemes = (
            self.client.issue_types().get_issue_type_screen_schemes(self)
        )
        for i in self.issue_type_screen_schemes:
            resp = self.client.get(
                path=f"/rest/api/3/issuetypescreenscheme/mapping?issueTypeScreenSchemeId={i.id}"
            )
            resp.raise_for_status()
            self.issue_type_scheme_mappings[i.id] = resp.json()["values"]

        processed_screen_scheme_ids = []
        for i in self.issue_type_scheme_mappings:
            for v in self.issue_type_scheme_mappings[i]:
                screen_scheme_id = v["screenSchemeId"]
                if screen_scheme_id not in processed_screen_scheme_ids:
                    self.screen_schemes.append(
                        self.client.screens().get_screen_scheme(screen_scheme_id)
                    )
                    processed_screen_scheme_ids.append(screen_scheme_id)

        self.issue_types.extend(self.client.issue_types().get_all(self.id))

        processed_screen_ids = []
        for ss in self.screen_schemes:
            for screen_id in ss.get_screen_ids():
                if screen_id not in processed_screen_ids:
                    self.screens.append(self.client.screens().get_screen(screen_id))
                    processed_screen_ids.append(screen_id)

        for screen in self.screens:
            self.screen_tabs[screen.id] = screen.get_tabs(self)

        field_ids = []
        for screen_id, tabs in self.screen_tabs.items():
            for tab in tabs:
                resp = self.client.get(
                    path=f"/rest/api/3/screens/{screen_id}/tabs/{tab['id']}/fields"
                )
                resp.raise_for_status()
                for field in resp.json():
                    if field["id"] not in field_ids:
                        field_ids.append(field["id"])

        all_fields = self.client.fields().get_all()
        for i in field_ids:
            for f in all_fields:
                if f.id == i:
                    self.project_fields.append(f)

    @property
    def id(self):
        """
        Retrieves the unique identifier for a project.

        This property fetches the 'id' value from the project detail dictionary.
        It provides a read-only way to access the project's identifier in the
        internal data structure.

        :rtype:
            Any
        :returns:
            The unique identifier of the project obtained from the
            `project_detail` dictionary.
        """
        return self.project_detail["id"]

    @property
    def key(self):
        """
        Represents a property to retrieve the 'key' from the project details.

        The 'key' is obtained dynamically from the project's details dictionary,
        where it is identified under the 'key' field. This property allows
        access to the value without exposing raw dictionary access, ensuring
        encapsulation.

        :rtype: str
        :return: The value of the 'key' field from the project details.
        """
        return self.project_detail["key"]

    @property
    def name(self):
        """
        This property retrieves the 'name' field from the 'project_detail' dictionary.
        It is used to access the project name information stored in the data structure.

        :return: The value associated with the 'name' key in the 'project_detail' dictionary
        :rtype: str
        """
        return self.project_detail["name"]

    @property
    def project_type_key(self):
        """
        Retrieves the project type key from the project details.

        The project type key provides essential categorization or type
        information about the project, which is extracted from the
        'project_detail' dictionary.

        :return: The project type key as a string.
        :rtype: str
        """
        return self.project_detail["projectTypeKey"]

    @property
    def simplified(self):
        """
        A property that provides the 'simplified' value from the `project_detail` dictionary.

        :return: The value associated with the key 'simplified'
                 in the `project_detail` dictionary.
        :rtype: Any
        """
        return self.project_detail["simplified"]

    @property
    def style(self):
        """
        Provides a property to access the style attribute of `project_detail`.

        This property retrieves the value of the 'style' key from the
        `project_detail` dictionary.

        :return: The value corresponding to the 'style' key in `project_detail`.
        :rtype: Any
        """
        return self.project_detail["style"]

    @property
    def is_private(self):
        """
        Checks whether the project is private or not.

        This property retrieves the value of `isPrivate` from the
        `project_detail` dictionary to determine the privacy status
        of the project. If the `isPrivate` key in the dictionary is
        set to `True`, the project is considered private.

        :raises KeyError: If the `isPrivate` key is not present in the
          `project_detail` dictionary.
        :return: Returns ``True`` if the project is private, otherwise
          ``False``.
        :rtype: bool
        """
        return self.project_detail["isPrivate"]

    @property
    def properties(self):
        """
        Provides access to the 'properties' attribute of the 'project_detail' dictionary
        contained within the class. This retrieves the value associated with the
        'properties' key.

        :return: The value of the 'properties' key in the 'project_detail' dictionary.
        :rtype: Any
        """
        return self.project_detail["properties"]

    @property
    def entity_id(self):
        """
        Provides a read-only property to access the 'entityId' of the object.

        This property retrieves the 'entityId' value from the 'project_detail'
        attribute. It is useful for cases where the entity's unique identifier
        is required without directly accessing the underlying data structure.

        :return: The 'entityId' value from the 'project_detail' dictionary.
        :rtype: Any
        """
        return self.project_detail["entityId"]

    @property
    def uuid(self):
        """
        Provides access to the unique identifier of the project in the form of a property. The `uuid`
        property retrieves the 'isPrivate' value from the project's details dictionary.

        :return: Returns the value of the 'isPrivate' key from the `project_detail` attribute.
        :rtype: bool
        """
        return self.project_detail["isPrivate"]

    def assign_fields(self, field_defs: list, auto_create: bool = True, dry_run: bool = False):
        """
        Assign custom fields to the current project based on provided definitions. If a custom field
        does not exist and the ``auto_create`` parameter is ``True``, the method attempts to create
        the missing field automatically. Successfully fetched or created fields are stored in the
        ``project_fields`` attribute.

        :param field_defs: A list of dictionaries, where each dictionary contains the specifications
            of a custom field, including its ``name``, ``type``, ``description``, and optional
            ``options``.
        :type field_defs: list
        :param auto_create: A boolean indicating whether missing fields should be created
            automatically if they do not exist within the client repository. Defaults to ``True``.
        :type auto_create: bool
        :param dry_run: When True, no field is created. A field that would have been
            created is still added to ``project_fields``, with an id of None, so the
            caller can go on to report what depends on it.
        :type dry_run: bool
        :return: The names of the fields that were created, or that would have been
            created under a dry run.
        :rtype: list[str]
        """
        created = []
        for field_def in field_defs:
            field = self.client.fields().get_custom_field(
                field_def.get("name"),
                field_def.get("description", ""),
                field_def.get("type"),
            )
            if field is None and auto_create:
                created.append(field_def.get("name"))
                if dry_run:
                    field = Field(
                        {"id": None, "name": field_def.get("name")}, self.client
                    )
                else:
                    field = self.client.fields().create_field(
                        field_def.get("type"),
                        field_def.get("name"),
                        field_def.get("description", ""),
                        field_def.get("options"),
                    )

            if field is not None:
                self.project_fields.append(field)
        return created

    def assign_issue_type_screen_scheme(self, issue_type_screen_scheme):
        """
        Assigns an issue type screen scheme to the current project. This operation connects
        an issue type screen scheme, which defines the association between issue types
        and screen schemes, to the project. The `issue_type_screen_scheme` parameter
        is required to configure the appropriate scheme for the project. Upon successful
        assignment, the issue type screen scheme is added to the list of screen schemes
        associated with the project.

        :param issue_type_screen_scheme: The issue type screen scheme to assign. Must be
            provided as an object with an `id` attribute.
        :type issue_type_screen_scheme: Any
        :return: None
        """
        payload = {
            "issueTypeScreenSchemeId": issue_type_screen_scheme.id,
            "projectId": self.id,
        }
        resp = self.client.put(
            "/rest/api/3/issuetypescreenscheme/project", data=payload
        )
        resp.raise_for_status()
        self.issue_type_screen_schemes.append(issue_type_screen_scheme)

    def assign_issue_type_scheme(self, issue_type_scheme):
        """
        Assigns an issue type scheme to the current project.

        This method associates the specified issue type scheme with the project using
        the assigned project ID and issue type scheme ID. The association is made by
        sending a PUT request to the corresponding API endpoint. If the operation is
        successful, the issue type scheme is appended to the local list of associated
        schemes.

        :param issue_type_scheme: The issue type scheme to be assigned to the project.
        :type issue_type_scheme: IssueTypeScheme
        :return: None
        """
        payload = {"issueTypeSchemeId": issue_type_scheme.id, "projectId": self.id}
        resp = self.client.put("/rest/api/3/issuetypescheme/project", data=payload)
        resp.raise_for_status()
        self.issue_type_schemes.append(issue_type_scheme)

    def assign_workflow_scheme(self, workflow_scheme):
        """
        Assigns a workflow scheme to a project by making a PUT request to the
        Jira REST API endpoint for workflow scheme assignment. This method updates
        the association of the specified workflow scheme with the corresponding
        project represented by the current object.

        :param workflow_scheme: The workflow scheme to be assigned to the project.
            Must be an object that contains an `id` attribute representing the ID
            of the workflow scheme in Jira.
        :type workflow_scheme: object
        :return: None. This method does not return any value.
        :rtype: NoneType
        :raises HTTPError: If the API call fails, this method raises an HTTPError
            exception for failed HTTP requests or unexpected responses.
        """
        payload = {"workflowSchemeId": workflow_scheme.id, "projectId": self.id}

        resp = self.client.put("/rest/api/3/workflowscheme/project", data=payload)
        resp.raise_for_status()

    def get_screen(self, name):
        """
        Retrieves a screen object by its name from the list of available screens.
        If no screen is found with the specified name, returns None.

        :param name: The name of the screen to search for.
        :type name: str
        :return: The screen object with the specified name, or None if not found.
        :rtype: Optional[Screen]
        """
        for screen in self.screens:
            if screen.name == name:
                return screen
        return None

    def get_issue_type(self, name):
        """
        Retrieves an issue type by its name from the list of issue types.

        This function iterates through a list of issue types and attempts to find one
        that matches the specified name. If a match is found, the corresponding issue
        type is returned. If no match is found, None is returned.

        :param name: The name of the issue type to search for.
        :type name: str
        :return: An issue type object that matches the specified name, or None if no
            match is found.
        :rtype: Optional[IssueType]
        """
        for issue_type in self.issue_types:
            if issue_type.name == name:
                return issue_type
        return None

    def get_screen_scheme(self, name):
        """
        Searches for a screen scheme by its name in the list of available screen schemes.

        :param name: The name of the screen scheme to search for.
        :type name: str
        :return: The screen scheme object with the specified name if found,
            otherwise None.
        :rtype: Optional[ScreenScheme]
        """
        for screen_scheme in self.screen_schemes:
            if screen_scheme.name == name:
                return screen_scheme
        return None


class TemplateApplication:
    """
    The outcome of applying a template: the project, and what changed.

    A dry run produces one of these without making any of the changes, which is
    how an operator can be told precisely what a deployed project is missing
    rather than being handed a bare list of field names.
    """

    def __init__(self, project, changes, dry_run=False):
        """
        :param project: The project the template was applied to.
        :type project: Project
        :param changes: The changes made, or that would be made under a dry run.
            Each is a dict with 'action', 'type' and 'name', plus whatever else
            that kind of change carries.
        :type changes: list[dict]
        :param dry_run: Whether the changes were reported rather than made.
        :type dry_run: bool
        """
        self.project = project
        self.changes = changes
        self.dry_run = dry_run

    @property
    def changed(self):
        """
        Whether anything was, or would be, changed.

        :rtype: bool
        """
        return bool(self.changes)

    def summary(self):
        """
        The changes as lines of text, for reporting to an operator.

        :return: One line per change.
        :rtype: list[str]
        """
        lines = []
        for change in self.changes:
            resource = change["type"].replace("_", " ")
            if change["action"] == "add_fields":
                fields = ", ".join(change.get("fields", []))
                lines.append(
                    f"add {fields} to {resource} '{change['name']}'"
                    f" on screen '{change.get('screen')}'"
                )
            else:
                lines.append(f"{change['action']} {resource} '{change['name']}'")
        return lines

    def __repr__(self):
        state = "would change" if self.dry_run else "changed"
        return f"<TemplateApplication {state} {len(self.changes)} resource(s)>"


class Projects:
    """
    This class provides methods for managing and interacting with projects, including listing,
    creating, deleting, and applying templates for project configurations within a client system.
    It allows users to perform various project-related operations with specific configurations,
    workflows, screen schemes, and issue types.

    :ivar client: Reference to the client instance used for handling API operations.
    :type client: Client
    """

    def __init__(self, client):
        """
        Represents the initialization of an object with a specified client.

        This constructor is responsible for initializing an instance with the given
        client object. The client is expected to provide the necessary interface or
        connection details required by the class for its functionality.

        :param client: The client object required for the initialization.
        :type client: Any
        """
        self.client = client

    def delete_project(self, project, enable_undo=False):
        """
        Deletes a project in the system.

        This method will permanently delete the specified project unless the
        `enable_undo` parameter is set to True. The deletion operation is
        performed using the client API endpoint. The system will raise an
        exception if the request fails.

        :param project: The project object to be deleted. This should include the
            project ID that uniquely identifies the project.
        :type project: Project
        :param enable_undo: A boolean flag indicating whether undo capabilities
            should be enabled during the deletion process. Defaults to False.
        :type enable_undo: bool
        :return: None
        """
        resp = self.client.delete(
            f"/rest/api/3/project/{project.id}?enableUndo={enable_undo}"
        )
        resp.raise_for_status()

    def rollback_template_deployment(
        self,
        project_key,
        delete_project=True,
        enable_undo=False,
        tracking_dir=".jirakit_deployments",
        retry_seconds=DEFAULT_ROLLBACK_RETRY_SECONDS,
    ):
        """
        Rolls back a template deployment by deleting project-specific resources.

        This method uses the deployment tracking file to precisely delete resources created
        during template deployment. If no tracking file exists, it falls back to searching
        for resources by project key prefix.

        The project is deleted first, because a scheme still assigned to a live
        project cannot be deleted. Everything else follows in dependency order:

        1. Project
        2. Workflow schemes, then the workflows they referenced
        3. Issue type screen schemes, then screen schemes, then screens
        4. Issue type schemes, then issue types

        Deleting a project does not release its schemes immediately, so a deletion
        Jira refuses is retried for up to ``retry_seconds``. Anything still
        undeletable when that budget runs out is reported in ``resources_remaining``
        and ``errors``, and the tracking file is kept so the rollback can be
        retried later.

        Note: groups, custom fields and statuses are NOT deleted, as they may be
        shared across projects. They are described in ``shared_resources_left``.

        :param project_key: The key of the project to roll back.
        :type project_key: str
        :param delete_project: Whether to delete the project. Defaults to True.
            When False, no scheme is deleted either, as every scheme deletion is
            refused while the project it is assigned to is live; the reason is
            recorded in ``skipped``.
        :type delete_project: bool
        :param enable_undo: Whether to enable undo for project deletion. Only applies
            if delete_project is True. Defaults to False.
        :type enable_undo: bool
        :param tracking_dir: Directory where tracking files are stored. Defaults to
            '.jirakit_deployments'.
        :type tracking_dir: str
        :param retry_seconds: How long to keep retrying deletions Jira refuses.
            Defaults to DEFAULT_ROLLBACK_RETRY_SECONDS. Pass 0 to attempt each
            deletion once.
        :type retry_seconds: float
        :return: Dictionary containing summary of deleted resources, resources that
            could not be deleted, resources deliberately left, and any errors.
        :rtype: dict
        """
        summary = {
            "issue_types_deleted": [],
            "issue_type_schemes_deleted": [],
            "screens_deleted": [],
            "screen_schemes_deleted": [],
            "issue_type_screen_schemes_deleted": [],
            "workflows_deleted": [],
            "workflow_schemes_deleted": [],
            "project_deleted": False,
            "tracking_file_used": False,
            "resources_remaining": [],
            "shared_resources_left": list(SHARED_RESOURCES_LEFT),
            "skipped": [],
            "errors": [],
        }

        logging.info(f"Starting rollback for project: {project_key}")

        tracker = DeploymentTracker.load(project_key, tracking_dir)
        summary["tracking_file_used"] = tracker is not None

        if not delete_project:
            summary["skipped"].append(
                "No resource was deleted because delete_project is False. A scheme "
                "assigned to a live project cannot be deleted, so the project must "
                "be removed, or its schemes reassigned, before a rollback can "
                "remove them."
            )
            logging.warning(
                f"Rollback for {project_key} deleted nothing: delete_project is False"
            )
            return summary

        try:
            # Only the project ID is needed to delete it, and loading a
            # half-deployed project's configuration can fail outright.
            project = self.get_project_reference(project_key)
        except Exception as e:
            # A rollback that left resources behind keeps its tracking file so it
            # can be retried, and by then the project itself is already gone.
            project = None
            logging.info(
                f"Project {project_key} could not be retrieved, treating it as "
                f"already deleted and cleaning up what it left behind: {e}"
            )
            summary["skipped"].append(
                f"The project was not deleted because it could not be retrieved, "
                f"which is expected when it has already been deleted: {e}"
            )

        if project is not None:
            try:
                logging.info(f"Deleting project: {project_key}")
                self.delete_project(project, enable_undo=enable_undo)
                summary["project_deleted"] = True
                logging.info(f"Successfully deleted project: {project_key}")
            except Exception as e:
                summary["errors"].append(f"Failed to delete project: {e}")
                logging.error(f"Failed to delete project {project_key}: {e}")
                # Every dependent deletion is refused while the project is live,
                # so attempting them would only fill the result with 400s.
                summary["skipped"].append(
                    "Dependent resources were not deleted because the project "
                    "could not be deleted."
                )
                return summary

        if enable_undo and summary["project_deleted"]:
            # The project is in the recycle bin rather than gone, and it goes on
            # holding the schemes assigned to it while it sits there.
            summary["skipped"].append(
                "Dependent resources were not deleted because enable_undo leaves "
                "the project in the recycle bin, where it still holds the schemes "
                "assigned to it. Jira refuses to delete them until the project is "
                "permanently deleted."
            )
            logging.warning(
                f"Rollback for {project_key} deleted only the project: enable_undo "
                f"leaves it in the recycle bin, still holding its schemes"
            )
            return summary

        if tracker:
            logging.info(f"Using tracking file for precise rollback of {project_key}")
            deletions = self.tracked_deletions(tracker)
        else:
            logging.warning(
                f"No tracking file found for {project_key}. Using fallback search by "
                f"naming convention."
            )
            deletions = []

        already = {(d["type"], str(d["id"])) for d in deletions}
        deletions.extend(self.untracked_deletions(project_key, summary, already))

        self.run_deletions(deletions, retry_seconds, summary)

        if tracker and not summary["errors"]:
            tracker.delete_tracking_file()
        elif tracker:
            logging.warning(
                f"Keeping the tracking file for {project_key}: "
                f"{len(summary['resources_remaining'])} resource(s) were not deleted"
            )

        logging.info(f"Rollback complete for {project_key}")
        return summary

    def tracked_deletions(self, tracker):
        """
        Builds the deletions a tracking file describes, in dependency order.

        :param tracker: The loaded deployment tracker.
        :type tracker: DeploymentTracker
        :return: Deletions to run, in the order they must be attempted.
        :rtype: list
        """
        from jirakit.issues.types import (
            IssueType,
            IssueTypeScheme,
            IssueTypeScreenScheme,
        )
        from jirakit.screens import Screen, ScreenScheme
        from jirakit.workflows import Workflow, WorkflowScheme

        created = tracker.data["resources_created"]
        deletions = []

        for scheme in created["workflow_schemes"]:
            deletions.append(
                self.deletion(
                    "workflow scheme",
                    "workflow_schemes_deleted",
                    scheme["id"],
                    scheme["name"],
                    lambda scheme=scheme: (
                        self.client.workflows().delete_workflow_scheme(
                            WorkflowScheme(
                                {"id": scheme["id"], "name": scheme["name"]},
                                self.client,
                            )
                        )
                    ),
                )
            )

        for scheme in created["issue_type_screen_schemes"]:
            deletions.append(
                self.deletion(
                    "issue type screen scheme",
                    "issue_type_screen_schemes_deleted",
                    scheme["id"],
                    scheme["name"],
                    lambda scheme=scheme: (
                        self.client.issue_types().delete_issue_type_screen_scheme(
                            IssueTypeScreenScheme(
                                {"id": scheme["id"], "name": scheme["name"]},
                                self.client,
                            )
                        )
                    ),
                )
            )

        for scheme in created["screen_schemes"]:
            deletions.append(
                self.deletion(
                    "screen scheme",
                    "screen_schemes_deleted",
                    scheme["id"],
                    scheme["name"],
                    lambda scheme=scheme: self.client.screens().delete_screen_scheme(
                        ScreenScheme(
                            {"id": scheme["id"], "name": scheme["name"]}, self.client
                        )
                    ),
                )
            )

        for screen in created["screens"]:
            deletions.append(
                self.deletion(
                    "screen",
                    "screens_deleted",
                    screen["id"],
                    screen["name"],
                    lambda screen=screen: self.client.screens().delete_screen(
                        Screen(
                            {"id": screen["id"], "name": screen["name"]}, self.client
                        )
                    ),
                )
            )

        for scheme in created["issue_type_schemes"]:
            deletions.append(
                self.deletion(
                    "issue type scheme",
                    "issue_type_schemes_deleted",
                    scheme["id"],
                    scheme["name"],
                    lambda scheme=scheme: (
                        self.client.issue_types().delete_issue_type_scheme(
                            IssueTypeScheme(
                                {"id": scheme["id"], "name": scheme["name"]},
                                self.client,
                            )
                        )
                    ),
                )
            )

        for issue_type in created["issue_types"]:
            deletions.append(
                self.deletion(
                    "issue type",
                    "issue_types_deleted",
                    issue_type["id"],
                    issue_type["name"],
                    lambda issue_type=issue_type: self.client.issue_types().delete(
                        IssueType(
                            {"id": issue_type["id"], "name": issue_type["name"]},
                            self.client,
                        )
                    ),
                )
            )

        for workflow in created["workflows"]:
            deletions.append(
                self.deletion(
                    "workflow",
                    "workflows_deleted",
                    workflow["entity_id"],
                    workflow["name"],
                    lambda workflow=workflow: (
                        self.client.workflows().delete_inactive_workflow(
                            Workflow(
                                {
                                    "id": workflow["entity_id"],
                                    "name": workflow["name"],
                                },
                                self.client,
                            )
                        )
                    ),
                )
            )

        return deletions

    def untracked_deletions(self, project_key, summary, already_covered=()):
        """
        Finds resources named for the project that no tracking file covers, in
        dependency order.

        Deploying a template makes Jira create resources of its own alongside the
        project, such as the screens, screen schemes and workflow the project
        template provides. Nothing tracks them, and deleting the project does not
        remove them. They follow the same naming convention the deployment uses,
        so they are found by their project-key prefix.

        :param project_key: The key of the project being rolled back.
        :type project_key: str
        :param summary: The rollback summary, for recording lookup failures.
        :type summary: dict
        :param already_covered: (type, id) pairs already scheduled for deletion.
        :type already_covered: iterable
        :return: Deletions to run, in the order they must be attempted.
        :rtype: list
        """
        prefix = f"{project_key}: "
        # The one project-scoped resource Jira does not name with the prefix.
        auto_workflow = f"Software Simplified Workflow for Project {project_key}"
        covered = set(already_covered)
        deletions = []

        def sweep(
            description,
            lookup,
            resource_type,
            summary_key,
            delete,
            name_of,
            id_of=lambda resource: resource.id,
        ):
            try:
                found = lookup()
            except Exception as e:
                summary["errors"].append(f"Failed to retrieve {description}: {e}")
                logging.error(f"Failed to retrieve {description}: {e}")
                return

            for resource in found:
                try:
                    name = name_of(resource) or ""
                    if not (name.startswith(prefix) or name == auto_workflow):
                        continue
                    resource_id = id_of(resource)
                except (KeyError, AttributeError, TypeError):
                    continue

                if (resource_type, str(resource_id)) in covered:
                    continue
                covered.add((resource_type, str(resource_id)))

                deletions.append(
                    self.deletion(
                        resource_type,
                        summary_key,
                        resource_id,
                        name,
                        lambda resource=resource: delete(resource),
                    )
                )

        issue_types = self.client.issue_types()
        screens = self.client.screens()
        workflows = self.client.workflows()

        sweep(
            "workflow schemes",
            workflows.get_all_workflow_schemes,
            "workflow scheme",
            "workflow_schemes_deleted",
            workflows.delete_workflow_scheme,
            lambda resource: resource.name,
        )
        sweep(
            "issue type screen schemes",
            issue_types.get_all_issue_type_screen_schemes,
            "issue type screen scheme",
            "issue_type_screen_schemes_deleted",
            issue_types.delete_issue_type_screen_scheme,
            lambda resource: resource.detail.get("name", ""),
        )
        sweep(
            "screen schemes",
            screens.get_all_screen_schemes,
            "screen scheme",
            "screen_schemes_deleted",
            screens.delete_screen_scheme,
            lambda resource: resource.name,
        )
        sweep(
            "screens",
            screens.get_all_screens,
            "screen",
            "screens_deleted",
            screens.delete_screen,
            lambda resource: resource.name,
        )
        sweep(
            "issue type schemes",
            issue_types.get_all_issue_type_schemes,
            "issue type scheme",
            "issue_type_schemes_deleted",
            issue_types.delete_issue_type_scheme,
            lambda resource: resource.scheme_detail.get("name", ""),
        )
        sweep(
            "issue types",
            issue_types.get_all_user_issue_types,
            "issue type",
            "issue_types_deleted",
            issue_types.delete,
            lambda resource: resource.name,
        )
        sweep(
            "workflows",
            lambda: workflows.get_all(active=False),
            "workflow",
            "workflows_deleted",
            workflows.delete_inactive_workflow,
            lambda resource: resource.name,
            lambda resource: resource.entity_id,
        )

        return deletions

    @staticmethod
    def deletion(resource_type, summary_key, resource_id, name, delete):
        """
        Describes one deletion the rollback should attempt.

        :param resource_type: Human-readable type, used when reporting.
        :type resource_type: str
        :param summary_key: Key in the rollback summary to record success under.
        :type summary_key: str
        :param resource_id: Identifier of the resource, used when reporting.
        :type resource_id: str
        :param name: Name of the resource.
        :type name: str
        :param delete: Callable performing the deletion.
        :type delete: callable
        :return: The deletion description.
        :rtype: dict
        """
        return {
            "type": resource_type,
            "summary_key": summary_key,
            "id": resource_id,
            "name": name,
            "delete": delete,
        }

    @staticmethod
    def run_deletions(deletions, retry_seconds, summary):
        """
        Runs deletions in order, retrying the ones Jira refuses until they
        succeed or the retry budget runs out, then records what survived.

        :param deletions: Deletions to attempt, in dependency order.
        :type deletions: list
        :param retry_seconds: How long to keep retrying refused deletions.
        :type retry_seconds: float
        :param summary: The rollback summary to record outcomes in.
        :type summary: dict
        :return: None
        """
        deadline = time.monotonic() + retry_seconds
        pending = list(deletions)
        reasons = {}

        while pending:
            still_pending = []
            for deletion in pending:
                try:
                    deletion["delete"]()
                except Exception as e:
                    reasons[id(deletion)] = str(e)
                    still_pending.append(deletion)
                    continue
                summary[deletion["summary_key"]].append(deletion["name"])
                logging.info(f"Deleted {deletion['type']}: {deletion['name']}")

            pending = still_pending
            if not pending:
                break

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            logging.info(
                f"{len(pending)} deletion(s) refused; retrying for another "
                f"{remaining:.0f}s"
            )
            time.sleep(min(ROLLBACK_RETRY_INTERVAL, remaining))

        for deletion in pending:
            reason = reasons[id(deletion)]
            summary["errors"].append(
                f"Failed to delete {deletion['type']} {deletion['name']}: {reason}"
            )
            summary["resources_remaining"].append(
                {
                    "type": deletion["type"],
                    "id": deletion["id"],
                    "name": deletion["name"],
                    "reason": reason,
                }
            )
            logging.warning(
                f"Failed to delete {deletion['type']} {deletion['name']}: {reason}"
            )

    def get_all(self, status="live"):
        """
        Fetches all projects from the API based on the specified status. This method paginates
        the results and accumulates all projects into a list until all pages are processed.
        The `status` parameter determines the type of projects to retrieve.

        :param status: Project status to filter by (default is 'live').
            Acceptable values are 'live', 'deleted', or similar recognized statuses.
        :type status: str
        :return: A list of Project objects corresponding to the specified status.
        :rtype: list[Project]
        """
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(
                path=f"/rest/api/3/project/search?startAt={start_at}&maxResults={max_results}&status={status}"
            )
            resp.raise_for_status()
            page = resp.json()
            is_last = page.get("isLast", True)
            start_at += max_results
            for p in page.get("values", []):
                _l.append(Project(p, self.client, skip_load=status == "deleted"))
        return _l

    def get_project(self, project_key):
        """
        Retrieve a project by its project key.

        This function fetches the project details for the given project key using the
        REST API. It raises an exception if the request fails. The project data is
        wrapped into a `Project` object upon successful retrieval.

        :param project_key: The unique key of the project to be retrieved.
        :type project_key: str
        :return: An instance of the `Project` class that encapsulates the project details.
        :rtype: Project
        :raises HTTPError: If the request to fetch the project data fails.
        """
        _l = []
        resp = self.client.get(path=f"/rest/api/3/project/{project_key}")
        resp.raise_for_status()
        return Project(resp.json(), self.client)

    def get_project_reference(self, project_key):
        """
        Retrieve a project without loading its configuration.

        Loading a project reads its screens, schemes and mappings, which is both
        unnecessary when the project is about to be deleted and liable to fail on
        a partially deployed project.

        :param project_key: The unique key of the project to be retrieved.
        :type project_key: str
        :return: An instance of the `Project` class carrying only the project's
            own details.
        :rtype: Project
        :raises HTTPError: If the request to fetch the project data fails.
        """
        resp = self.client.get(path=f"/rest/api/3/project/{project_key}")
        resp.raise_for_status()
        return Project(resp.json(), self.client, skip_load=True)

    def apply_template(
        self,
        project: Project,
        template: dict,
        tracker=None,
        dry_run: bool = False,
    ):
        """
        Apply a template to a project, creating only what is not already there.

        This is the single implementation behind both deploying a new project
        and bringing an existing one up to a changed template. Every step is a
        get-or-create against the name the deployment gives the resource
        (``<KEY>: <template name>``), so on a project the template has never
        been applied to everything is created, and on one it has been applied to
        before only the difference is. Applying the same template twice is a
        no-op.

        Screen tabs are populated only after the screens have been wired to the
        project, because Jira registers a field with the project's issue create
        metadata when the field is added to a tab of an already-wired screen.

        Workflows are still created unconditionally; see ``reconcile_workflows``
        on :meth:`reconcile_template` for updating one that already exists.

        :param project: The project to apply the template to.
        :type project: Project
        :param template: The template definition.
        :type template: dict
        :param tracker: A DeploymentTracker to record created resources against,
            so they can be rolled back. Resources that were adopted rather than
            created are deliberately not tracked: a rollback must not delete
            something this deployment did not make.
        :type tracker: DeploymentTracker or None
        :param dry_run: When True, report the changes that would be made and
            make none of them. No request that writes is issued.
        :type dry_run: bool
        :return: The project and the changes applied, or that would be applied.
        :rtype: TemplateApplication
        """
        changes = []

        def record(action, resource_type, name, **extra):
            change = {"action": action, "type": resource_type, "name": name}
            change.update(extra)
            changes.append(change)
            return change

        def track(method_name, *args):
            if tracker is not None and not dry_run:
                getattr(tracker, method_name)(*args)

        def qualified(name):
            return f"{project.key}: {name}"

        logging.info(f'Applying Template "{template.get("name")}" to {project.key}')

        # Groups are shared, so they are neither tracked nor rolled back.
        # create_groups already skips the ones that exist.
        if not dry_run:
            self.client.groups().create_groups(template.get("groups", []) or [])

        # Fields are shared too, and assign_fields only creates the missing ones.
        for field_name in project.assign_fields(
            template.get("fields") or [], dry_run=dry_run
        ):
            record("create", "field", field_name)

        new_issue_types = []
        for issue_type_def in template.get("issue_types") or []:
            name = qualified(issue_type_def["name"])
            issue_type, created = self.client.issue_types().ensure(
                name,
                issue_type_def["description"],
                issue_type_def["subtask"],
                dry_run=dry_run,
            )
            project.issue_types.append(issue_type)
            if created:
                new_issue_types.append(issue_type)
                record("create", "issue_type", name, id=issue_type.id)
                track("track_issue_type", issue_type.id, name)

        for issue_type_scheme_def in template.get("issue_type_schemes") or []:
            name = qualified(issue_type_scheme_def["name"])
            wanted = {
                qualified(n) for n in issue_type_scheme_def.get("issue_types") or []
            }
            issue_type_ids = [
                issue_type.id
                for issue_type in project.issue_types
                if issue_type.name in wanted
            ]
            scheme, created = self.client.issue_types().ensure_issue_type_scheme(
                name,
                issue_type_scheme_def["description"],
                issue_type_ids,
                dry_run=dry_run,
            )
            if created:
                record("create", "issue_type_scheme", name, id=scheme.id)
                track("track_issue_type_scheme", scheme.id, name)
            elif new_issue_types and not dry_run:
                # The scheme was already there, so only the issue types created
                # on this run can be missing from it.
                scheme.add_issue_type(
                    [it for it in new_issue_types if it.name in wanted]
                )
            self.assign_issue_type_scheme_if_needed(project, scheme, dry_run)

        for screen_def in template.get("screens") or []:
            name = qualified(screen_def["name"])
            screen, created = self.client.screens().ensure(
                name, screen_def["description"], dry_run=dry_run
            )
            project.screens.append(screen)
            if created:
                record("create", "screen", name, id=screen.id)
                track("track_screen", screen.id, name)

        for screen_scheme_def in template.get("screen_schemes") or []:
            name = qualified(screen_scheme_def["name"])
            default_screen = project.get_screen(
                qualified(screen_scheme_def["screens"]["default"])
            )
            scheme, created = self.client.screens().ensure_screen_scheme(
                name,
                screen_scheme_def["description"],
                default=default_screen.id,
                edit=default_screen.id,
                view=default_screen.id,
                dry_run=dry_run,
            )
            project.screen_schemes.append(scheme)
            if created:
                record("create", "screen_scheme", name, id=scheme.id)
                track("track_screen_scheme", scheme.id, name)

        for itss_def in template.get("issue_type_screen_schemes") or []:
            name = qualified(itss_def["name"])
            mappings = [
                {
                    "issueTypeId": project.get_issue_type(
                        qualified(mapping_def["issue_type"])
                    ).id,
                    "screenSchemeId": project.get_screen_scheme(
                        qualified(mapping_def["screen_scheme"])
                    ).id,
                }
                for mapping_def in itss_def["mappings"]
            ]
            mappings.append(
                {
                    "issueTypeId": "default",
                    "screenSchemeId": project.get_screen_scheme(
                        qualified(itss_def["default_screen_scheme"])
                    ).id,
                }
            )
            scheme, created = self.client.issue_types().ensure_issue_type_screen_scheme(
                name, itss_def["description"], mappings, dry_run=dry_run
            )
            if created:
                record("create", "issue_type_screen_scheme", name, id=scheme.id)
                track("track_issue_type_screen_scheme", scheme.id, name)
            elif new_issue_types and not dry_run:
                for mapping_def in itss_def["mappings"]:
                    issue_type_name = qualified(mapping_def["issue_type"])
                    if any(it.name == issue_type_name for it in new_issue_types):
                        scheme.add_mapping(
                            project.get_issue_type(issue_type_name),
                            project.get_screen_scheme(
                                qualified(mapping_def["screen_scheme"])
                            ),
                        )
            self.assign_issue_type_screen_scheme_if_needed(project, scheme, dry_run)

        # Screen tabs are populated last, after the wiring above. Jira registers
        # a field with the project's issue create metadata when the field is
        # added to a tab of a screen that is already wired to a project;
        # populating the tabs first leaves every field permanently invisible to
        # createmeta, so none of them can be set when creating an issue.
        logging.info(f"Applying Screen Tabs to {project.key}")
        for screen_tab_def in template.get("screen_tabs") or []:
            screen_name = qualified(screen_tab_def["screen"])
            for screen in project.screens:
                if screen.name != screen_name:
                    continue
                field_ids = []
                for field in project.project_fields:
                    if (
                        field.name in screen_tab_def["fields"]
                        and field.id not in field_ids
                    ):
                        field_ids.append(field.id)

                tab = screen.ensure_tab(
                    screen_tab_def["name"], field_ids, dry_run=dry_run
                )
                if tab["created"]:
                    record(
                        "create", "screen_tab", tab["name"], screen=screen_name
                    )
                if tab["fields_added"]:
                    record(
                        "add_fields",
                        "screen_tab",
                        tab["name"],
                        screen=screen_name,
                        fields=tab["fields_added"],
                    )
                if not dry_run:
                    project.screen_tabs.setdefault(screen.id, []).append(tab)

        for workflow_def in template.get("workflows") or []:
            name = qualified(workflow_def["name"])
            if dry_run:
                record("create", "workflow", name)
                continue
            logging.info(f'Applying Workflow "{workflow_def["name"]}" to {project.key}')
            workflow = self.client.workflows().create(
                name, workflow_def["description"], workflow_def, project
            )
            project.workflows.append(workflow)
            record("create", "workflow", name, id=workflow.entity_id)
            track("track_workflow", workflow.entity_id, name)

        for workflow_scheme_def in template.get("workflow_schemes") or []:
            name = qualified(workflow_scheme_def["name"])
            if dry_run:
                record("create", "workflow_scheme", name)
                continue
            logging.info(f"Applying Workflow Scheme to {project.key}")
            issue_type_mappings = {}
            for mapping in workflow_scheme_def["issueTypeMappings"]:
                issue_type_id = project.get_issue_type(
                    qualified(mapping["issue_type"])
                ).id
                issue_type_mappings[f"{issue_type_id}"] = qualified(
                    mapping["workflow"]
                )

            payload = {
                "name": name,
                "description": workflow_scheme_def["description"],
                "defaultWorkflow": workflow_scheme_def["defaultWorkflow"],
                "issueTypeMappings": issue_type_mappings,
            }
            resp = self.client.post(path="/rest/api/3/workflowscheme", data=payload)
            resp.raise_for_status()
            workflow_scheme_id = resp.json()["id"]
            record("create", "workflow_scheme", name, id=workflow_scheme_id)
            track("track_workflow_scheme", workflow_scheme_id, name)

            resp = self.client.put(
                path="/rest/api/3/workflowscheme/project",
                data={
                    "projectId": project.id,
                    "workflowSchemeId": workflow_scheme_id,
                },
            )
            resp.raise_for_status()

        return TemplateApplication(project, changes, dry_run=dry_run)

    def assign_issue_type_scheme_if_needed(self, project, scheme, dry_run=False):
        """
        Assign an issue type scheme to a project unless it is already assigned.

        Re-assigning is harmless but is still a write, and a reconcile that finds
        nothing to do should issue none.

        :param project: The project to assign the scheme to.
        :type project: Project
        :param scheme: The issue type scheme.
        :type scheme: IssueTypeScheme
        :param dry_run: When True, nothing is assigned.
        :type dry_run: bool
        :return: Whether the scheme needed assigning.
        :rtype: bool
        """
        if dry_run:
            return True
        if any(
            assigned.id == scheme.id for assigned in project.issue_type_schemes
        ):
            return False
        project.assign_issue_type_scheme(scheme)
        return True

    def assign_issue_type_screen_scheme_if_needed(self, project, scheme, dry_run=False):
        """
        Assign an issue type screen scheme to a project unless already assigned.

        :param project: The project to assign the scheme to.
        :type project: Project
        :param scheme: The issue type screen scheme.
        :type scheme: IssueTypeScreenScheme
        :param dry_run: When True, nothing is assigned.
        :type dry_run: bool
        :return: Whether the scheme needed assigning.
        :rtype: bool
        """
        if dry_run:
            return True
        if any(
            assigned.id == scheme.id
            for assigned in project.issue_type_screen_schemes
        ):
            return False
        project.assign_issue_type_screen_scheme(scheme)
        return True


    def create(self, name: str, key: str, template: dict):
        """
        Create a project and apply a template to it.

        The project itself is created here; everything the template describes is
        applied by :meth:`apply_template`, which is the single implementation
        shared with reconciling an existing project. Every resource it creates
        is recorded against a DeploymentTracker so the deployment can be rolled
        back.

        :param name: The name of the project to create.
        :type name: str
        :param key: The unique key for the project.
        :type key: str
        :param template: The template that contains the project configuration.
        :type template: dict
        :return: The created project instance with all configurations applied.
        :rtype: Project
        """
        tracker = DeploymentTracker(
            project_key=key, project_name=name, template_name=template.get("name")
        )

        try:
            try:
                me = self.client.get_me()
                tracker.set_deployed_by(me.get("emailAddress", "unknown"))
            except Exception:
                pass  # Non-critical, continue without user email

            payload = {
                "key": key,
                "name": name,
                "projectTemplateKey": "com.pyxis.greenhopper.jira:gh-simplified-kanban-classic",
                "projectTypeKey": "software",
                "assigneeType": "UNASSIGNED",
                "leadAccountId": self.client.get_me()["accountId"],
            }
            resp = self.client.post(path="/rest/api/3/project", data=payload)
            if resp.status_code != 200 and resp.status_code != 201:
                logging.error(
                    f"Project creation failed. Status: {resp.status_code}, Response: {resp.text}"
                )
            resp.raise_for_status()
            project = Project(resp.json(), self.client)

            tracker.set_project_id(project.id)

            self.apply_template(project, template, tracker=tracker)

            tracker.mark_completed()
            logging.info(
                f"Template deployment completed successfully for {project.key}"
            )

            return project

        except Exception as e:
            error_msg = f"Deployment failed: {str(e)}"
            tracker.track_error(error_msg)
            tracker.mark_failed()

            logging.error(error_msg)
            raise
