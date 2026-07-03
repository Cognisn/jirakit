import logging

from jirakit.issues import Issues
from jirakit.projects.tracking import DeploymentTracker


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
        self.issue_type_schemes = self.client.issue_types().get_all_issue_type_schemes_for_project(self)
        self.issue_type_screen_schemes = self.client.issue_types().get_issue_type_screen_schemes(self)
        for i in self.issue_type_screen_schemes:
            resp = self.client.get(
                path=f'/rest/api/3/issuetypescreenscheme/mapping?issueTypeScreenSchemeId={i.id}')
            resp.raise_for_status()
            self.issue_type_scheme_mappings[i.id] = resp.json()['values']

        processed_screen_scheme_ids = []
        for i in self.issue_type_scheme_mappings:
            for v in self.issue_type_scheme_mappings[i]:
                screen_scheme_id = v['screenSchemeId']
                if screen_scheme_id not in processed_screen_scheme_ids:
                    self.screen_schemes.append(self.client.screens().get_screen_scheme(screen_scheme_id))
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
                resp = self.client.get(path=f"/rest/api/3/screens/{screen_id}/tabs/{tab['id']}/fields")
                resp.raise_for_status()
                for field in resp.json():
                    if field['id'] not in field_ids:
                        field_ids.append(field['id'])

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
        return self.project_detail['id']

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
        return self.project_detail['key']

    @property
    def name(self):
        """
        This property retrieves the 'name' field from the 'project_detail' dictionary.
        It is used to access the project name information stored in the data structure.

        :return: The value associated with the 'name' key in the 'project_detail' dictionary
        :rtype: str
        """
        return self.project_detail['name']

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
        return self.project_detail['projectTypeKey']

    @property
    def simplified(self):
        """
        A property that provides the 'simplified' value from the `project_detail` dictionary.

        :return: The value associated with the key 'simplified'
                 in the `project_detail` dictionary.
        :rtype: Any
        """
        return self.project_detail['simplified']

    @property
    def style(self):
        """
        Provides a property to access the style attribute of `project_detail`.

        This property retrieves the value of the 'style' key from the
        `project_detail` dictionary.

        :return: The value corresponding to the 'style' key in `project_detail`.
        :rtype: Any
        """
        return self.project_detail['style']

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
        return self.project_detail['isPrivate']

    @property
    def properties(self):
        """
        Provides access to the 'properties' attribute of the 'project_detail' dictionary
        contained within the class. This retrieves the value associated with the
        'properties' key.

        :return: The value of the 'properties' key in the 'project_detail' dictionary.
        :rtype: Any
        """
        return self.project_detail['properties']

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
        return self.project_detail['entityId']

    @property
    def uuid(self):
        """
        Provides access to the unique identifier of the project in the form of a property. The `uuid`
        property retrieves the 'isPrivate' value from the project's details dictionary.

        :return: Returns the value of the 'isPrivate' key from the `project_detail` attribute.
        :rtype: bool
        """
        return self.project_detail['isPrivate']

    def assign_fields(self, field_defs: list, auto_create: bool = True):
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
        :return: None
        """
        for field_def in field_defs:
            field = self.client.fields().get_custom_field(field_def.get('name'), field_def.get('description', ''),
                                                          field_def.get('type'))
            if field is None and auto_create:
                field = self.client.fields().create_field(field_def.get('type'), field_def.get('name'),
                                                  field_def.get('description', ''), field_def.get('options'))

            if field is not None:
                self.project_fields.append(field)


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
            "projectId": self.id
        }
        resp = self.client.put(f"/rest/api/3/issuetypescreenscheme/project", data=payload)
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
        payload = {
            "issueTypeSchemeId": issue_type_scheme.id,
            "projectId": self.id
        }
        resp = self.client.put(f"/rest/api/3/issuetypescheme/project", data=payload)
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
        payload = {
            "workflowSchemeId": workflow_scheme.id,
            "projectId": self.id
        }

        resp = self.client.put(f"/rest/api/3/workflowscheme/project", data=payload)
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
        resp = self.client.delete(f"/rest/api/3/project/{project.id}?enableUndo={enable_undo}")
        resp.raise_for_status()

    def rollback_template_deployment(self, project_key, delete_project=True, enable_undo=False, tracking_dir=".jirakit_deployments"):
        """
        Rolls back a template deployment by deleting project-specific resources.

        This method uses the deployment tracking file to precisely delete resources created
        during template deployment. If no tracking file exists, it falls back to searching
        for resources by project key prefix.

        Resources are deleted in reverse order of creation:
        1. Workflow schemes
        2. Workflows (inactive only)
        3. Issue type screen schemes
        4. Screen schemes
        5. Screens
        6. Issue type schemes
        7. Issue types
        8. Project (if delete_project is True)

        Note: Groups and custom fields are NOT deleted as they may be shared across projects.

        :param project_key: The key of the project to roll back.
        :type project_key: str
        :param delete_project: Whether to delete the project itself after cleaning up
            resources. Defaults to True.
        :type delete_project: bool
        :param enable_undo: Whether to enable undo for project deletion. Only applies
            if delete_project is True. Defaults to False.
        :type enable_undo: bool
        :param tracking_dir: Directory where tracking files are stored. Defaults to
            '.jirakit_deployments'.
        :type tracking_dir: str
        :return: Dictionary containing summary of deleted resources and any errors encountered.
        :rtype: dict
        """
        summary = {
            'issue_types_deleted': [],
            'issue_type_schemes_deleted': [],
            'screens_deleted': [],
            'screen_schemes_deleted': [],
            'issue_type_screen_schemes_deleted': [],
            'workflows_deleted': [],
            'workflow_schemes_deleted': [],
            'project_deleted': False,
            'tracking_file_used': False,
            'errors': []
        }

        logging.info(f"Starting rollback for project: {project_key}")

        # Try to load tracking file
        tracker = DeploymentTracker.load(project_key, tracking_dir)

        if tracker:
            logging.info(f"Using tracking file for precise rollback of {project_key}")
            summary['tracking_file_used'] = True

            # Delete workflow schemes
            for workflow_scheme in tracker.data['resources_created']['workflow_schemes']:
                try:
                    # Workflow schemes are automatically cleaned when project is deleted
                    # Just track them in summary
                    summary['workflow_schemes_deleted'].append(workflow_scheme['name'])
                    logging.info(f"Tracked workflow scheme for deletion: {workflow_scheme['name']}")
                except Exception as e:
                    summary['errors'].append(f"Error tracking workflow scheme {workflow_scheme.get('name')}: {e}")
                    logging.warning(f"Error tracking workflow scheme: {e}")

            # Delete workflows (inactive only via API)
            for workflow in tracker.data['resources_created']['workflows']:
                try:
                    # Try to delete inactive workflow
                    # Active workflows will be handled when project is deleted
                    try:
                        from jirakit.workflows import Workflow
                        workflow_obj = Workflow({'id': {'entityId': workflow['entity_id']}, 'name': workflow['name']}, self.client)
                        self.client.workflows().delete_inactive_workflow(workflow_obj)
                        summary['workflows_deleted'].append(workflow['name'])
                        logging.info(f"Deleted workflow: {workflow['name']}")
                    except Exception as e:
                        # Likely active - will be deleted with project
                        logging.info(f"Workflow {workflow['name']} likely active - will be deleted with project: {e}")
                except Exception as e:
                    summary['errors'].append(f"Error processing workflow {workflow.get('name')}: {e}")
                    logging.warning(f"Error processing workflow: {e}")

            # Delete issue type screen schemes
            for itss in tracker.data['resources_created']['issue_type_screen_schemes']:
                try:
                    from jirakit.issues.types import IssueTypeScreenScheme
                    scheme_obj = IssueTypeScreenScheme({'id': itss['id'], 'name': itss['name']}, self.client)
                    self.client.issue_types().delete_issue_type_screen_scheme(scheme_obj)
                    summary['issue_type_screen_schemes_deleted'].append(itss['name'])
                    logging.info(f"Deleted issue type screen scheme: {itss['name']}")
                except Exception as e:
                    summary['errors'].append(f"Failed to delete issue type screen scheme {itss['name']}: {e}")
                    logging.warning(f"Failed to delete issue type screen scheme {itss['name']}: {e}")

            # Delete screen schemes
            for screen_scheme in tracker.data['resources_created']['screen_schemes']:
                try:
                    from jirakit.screens import ScreenScheme
                    scheme_obj = ScreenScheme({'id': screen_scheme['id'], 'name': screen_scheme['name']}, self.client)
                    self.client.screens().delete_screen_scheme(scheme_obj)
                    summary['screen_schemes_deleted'].append(screen_scheme['name'])
                    logging.info(f"Deleted screen scheme: {screen_scheme['name']}")
                except Exception as e:
                    summary['errors'].append(f"Failed to delete screen scheme {screen_scheme['name']}: {e}")
                    logging.warning(f"Failed to delete screen scheme {screen_scheme['name']}: {e}")

            # Delete screens
            for screen in tracker.data['resources_created']['screens']:
                try:
                    from jirakit.screens import Screen
                    screen_obj = Screen({'id': screen['id'], 'name': screen['name']}, self.client)
                    self.client.screens().delete_screen(screen_obj)
                    summary['screens_deleted'].append(screen['name'])
                    logging.info(f"Deleted screen: {screen['name']}")
                except Exception as e:
                    summary['errors'].append(f"Failed to delete screen {screen['name']}: {e}")
                    logging.warning(f"Failed to delete screen {screen['name']}: {e}")

            # Delete issue type schemes
            for its in tracker.data['resources_created']['issue_type_schemes']:
                try:
                    # Issue type schemes are automatically cleaned when project is deleted
                    summary['issue_type_schemes_deleted'].append(its['name'])
                    logging.info(f"Tracked issue type scheme for deletion: {its['name']}")
                except Exception as e:
                    summary['errors'].append(f"Error tracking issue type scheme {its.get('name')}: {e}")
                    logging.warning(f"Error tracking issue type scheme: {e}")

            # Delete issue types
            for issue_type in tracker.data['resources_created']['issue_types']:
                try:
                    from jirakit.issues.types import IssueType
                    issue_type_obj = IssueType({'id': issue_type['id'], 'name': issue_type['name']}, self.client)
                    self.client.issue_types().delete(issue_type_obj)
                    summary['issue_types_deleted'].append(issue_type['name'])
                    logging.info(f"Deleted issue type: {issue_type['name']}")
                except Exception as e:
                    summary['errors'].append(f"Failed to delete issue type {issue_type['name']}: {e}")
                    logging.warning(f"Failed to delete issue type {issue_type['name']}: {e}")

            # Delete the project
            if delete_project:
                try:
                    project = self.get_project(project_key)
                    logging.info(f"Deleting project: {project_key}")
                    self.delete_project(project, enable_undo=enable_undo)
                    summary['project_deleted'] = True
                    logging.info(f"Successfully deleted project: {project_key}")
                except Exception as e:
                    summary['errors'].append(f"Failed to delete project: {e}")
                    logging.error(f"Failed to delete project {project_key}: {e}")

            # Delete tracking file
            if summary['project_deleted']:
                tracker.delete_tracking_file()

        else:
            # Fallback: No tracking file - search by naming convention
            logging.warning(f"No tracking file found for {project_key}. Using fallback search by naming convention.")
            summary['tracking_file_used'] = False

            try:
                # Get project
                project = self.get_project(project_key)
            except Exception as e:
                summary['errors'].append(f"Failed to retrieve project: {e}")
                logging.error(f"Failed to retrieve project {project_key}: {e}")
                return summary

            # Delete issue types with project key prefix
            try:
                logging.info(f"Deleting issue types for {project_key}...")
                all_issue_types = self.client.issue_types().get_all_user_issue_types()
                for issue_type in all_issue_types:
                    if issue_type.name.startswith(f"{project_key}:"):
                        try:
                            self.client.issue_types().delete(issue_type)
                            summary['issue_types_deleted'].append(issue_type.name)
                            logging.info(f"Deleted issue type: {issue_type.name}")
                        except Exception as e:
                            summary['errors'].append(f"Failed to delete issue type {issue_type.name}: {e}")
                            logging.warning(f"Failed to delete issue type {issue_type.name}: {e}")
            except Exception as e:
                summary['errors'].append(f"Failed to retrieve issue types: {e}")
                logging.error(f"Failed to retrieve issue types: {e}")

            # Delete screens with project key prefix
            try:
                logging.info(f"Deleting screens for {project_key}...")
                all_screens = self.client.screens().get_all_screens()
                for screen in all_screens:
                    if project_key in screen.name:
                        try:
                            self.client.screens().delete_screen(screen)
                            summary['screens_deleted'].append(screen.name)
                            logging.info(f"Deleted screen: {screen.name}")
                        except Exception as e:
                            summary['errors'].append(f"Failed to delete screen {screen.name}: {e}")
                            logging.warning(f"Failed to delete screen {screen.name}: {e}")
            except Exception as e:
                summary['errors'].append(f"Failed to retrieve screens: {e}")
                logging.error(f"Failed to retrieve screens: {e}")

            # Delete screen schemes with project key prefix
            try:
                logging.info(f"Deleting screen schemes for {project_key}...")
                all_screen_schemes = self.client.screens().get_all_screen_schemes()
                for scheme in all_screen_schemes:
                    if project_key in scheme.name:
                        try:
                            self.client.screens().delete_screen_scheme(scheme)
                            summary['screen_schemes_deleted'].append(scheme.name)
                            logging.info(f"Deleted screen scheme: {scheme.name}")
                        except Exception as e:
                            summary['errors'].append(f"Failed to delete screen scheme {scheme.name}: {e}")
                            logging.warning(f"Failed to delete screen scheme {scheme.name}: {e}")
            except Exception as e:
                summary['errors'].append(f"Failed to retrieve screen schemes: {e}")
                logging.error(f"Failed to retrieve screen schemes: {e}")

            # Delete issue type screen schemes with project key prefix
            try:
                logging.info(f"Deleting issue type screen schemes for {project_key}...")
                all_itss = self.client.issue_types().get_all_issue_type_screen_schemes()
                for scheme in all_itss:
                    # Access name from detail dictionary since it's not a property
                    scheme_name = scheme.detail.get('name', '')
                    if project_key in scheme_name:
                        try:
                            self.client.issue_types().delete_issue_type_screen_scheme(scheme)
                            summary['issue_type_screen_schemes_deleted'].append(scheme_name)
                            logging.info(f"Deleted issue type screen scheme: {scheme_name}")
                        except Exception as e:
                            summary['errors'].append(f"Failed to delete issue type screen scheme {scheme_name}: {e}")
                            logging.warning(f"Failed to delete issue type screen scheme {scheme_name}: {e}")
            except Exception as e:
                summary['errors'].append(f"Failed to retrieve issue type screen schemes: {e}")
                logging.error(f"Failed to retrieve issue type screen schemes: {e}")

            # Delete workflows with project key prefix
            try:
                logging.info(f"Deleting inactive workflows for {project_key}...")
                all_workflows = self.client.workflows().get_all(active=False)
                for workflow in all_workflows:
                    try:
                        if hasattr(workflow, 'name') and project_key in workflow.name:
                            try:
                                self.client.workflows().delete_inactive_workflow(workflow)
                                summary['workflows_deleted'].append(workflow.name)
                                logging.info(f"Deleted workflow: {workflow.name}")
                            except Exception as e:
                                summary['errors'].append(f"Failed to delete workflow {workflow.name}: {e}")
                                logging.warning(f"Failed to delete workflow {workflow.name}: {e}")
                    except (KeyError, AttributeError):
                        # Skip workflows without name attribute
                        pass
            except Exception as e:
                summary['errors'].append(f"Failed to retrieve workflows: {e}")
                logging.error(f"Failed to retrieve workflows: {e}")

            # Delete the project itself
            if delete_project:
                try:
                    logging.info(f"Deleting project: {project_key}")
                    self.delete_project(project, enable_undo=enable_undo)
                    summary['project_deleted'] = True
                    logging.info(f"Successfully deleted project: {project_key}")
                except Exception as e:
                    summary['errors'].append(f"Failed to delete project: {e}")
                    logging.error(f"Failed to delete project {project_key}: {e}")

        logging.info(f"Rollback complete for {project_key}")
        return summary

    def get_all(self, status='live'):
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
            resp = self.client.get(path=f'/rest/api/3/project/search?startAt={start_at}&maxResults={max_results}&status={status}')
            is_last = resp.json()['isLast']
            start_at += max_results
            for p in resp.json()['values']:
                _l.append(Project(p, self.client, skip_load=status=='deleted'))
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
        resp = self.client.get(path=f'/rest/api/3/project/{project_key}')
        resp.raise_for_status()
        return Project(resp.json(), self.client)

    def apply_template(self, project: Project, template: dict):
        """
        Applies a given template configuration to a specified project, including setting up fields,
        workflows, screens, issue types, screen schemes, and various mappings. The method utilizes
        the provided template to make updates and additions to the project structure and metadata
        by interacting with a client API.

        :param project: The project to which the template will be applied.
        :type project: Project
        :param template: The template definition including fields, workflows, screens, issue types,
            and other configurations to apply to the project.
        :type template: dict
        :return: The updated project instance after applying the template.
        :rtype: Project
        """
        logging.info(f'Applying Template "{template.get('name')}" to {project.key}')
        project.assign_fields(template.get('fields'))
        workflow_scheme = self.client.workflows().get_workflow_scheme_for_project(project)

        self.client.groups().create_groups(template.get('groups', []))

        target_issue_type_scheme = None
        for issue_type_scheme in project.issue_type_schemes:
            if not issue_type_scheme.is_default:
                target_issue_type_scheme = issue_type_scheme
                break

        for issue_type_def in template.get('issue_types'):
            logging.info(f'Applying Issue Type "{issue_type_def.get("name")}" to {project.key}')
            issue_type = self.client.issue_types().create(f"{project.key}: {issue_type_def['name']}", issue_type_def['description'],
                                                              issue_type_def['subtask'])
            project.issue_types.append(issue_type)
            target_issue_type_scheme.add_issue_type([issue_type])

        for screen_def in template.get('screens', []):
            logging.info(f'Applying Screen Def "{screen_def.get("name")}" to {project.key}')
            screen = self.client.screens().create(f"{project.key}: {screen_def['name']}", screen_def['description'])
            project.screens.append(screen)

        logging.info(f'Applying Screen Tabs to {project.key}')
        for screen_tab_def in template.get('screen_tabs', []):
            for screen in project.screens:
                if screen.name == f"{project.key}: {screen_tab_def['screen']}":
                    field_ids = []
                    for field in project.project_fields:
                        for field_name in screen_tab_def['fields']:
                            if field.name == field_name:
                                if field.id not in field_ids:
                                    field_ids.append(field.id)
                                break

                    tab = screen.create_tab(screen_tab_def['name'], field_ids)
                    if screen.id not in project.screen_tabs:
                        project.screen_tabs[screen.id] = []
                    project.screen_tabs[screen.id].append(tab)

        for screen_schemes_def in template.get('screen_schemes', []):
            logging.info(f'Applying Screen Scheme Def "{screen_schemes_def['name']}" to {project.key}')
            name = f"{project.key}: {screen_schemes_def['name']}"
            resp = self.client.screens().create_screen_scheme(name, screen_schemes_def['description'],
                                                              default=project.get_screen(f"{project.key}: {screen_schemes_def['screens']['default']}").id,
                                                              edit=project.get_screen(f"{project.key}: {screen_schemes_def['screens']['default']}").id,
                                                              view=project.get_screen(f"{project.key}: {screen_schemes_def['screens']['default']}").id)

            project.screen_schemes.append(resp)

        for issue_type_screen_scheme_def in template.get('issue_type_screen_schemes', []):
            logging.info(f'Applying Screen/Issue Scheme to {project.key}')
            issue_type_screen_scheme = project.issue_type_screen_schemes[0]
            for mapping_def in issue_type_screen_scheme_def['mappings']:
                issue_type_screen_scheme.add_mapping(project.get_issue_type(f"{project.key}: {mapping_def['issue_type']}"),
                                                     project.get_screen_scheme(f"{project.key}: {mapping_def['screen_scheme']}"))

        for workflow_def in template.get('workflows', []):
            logging.info(f'Applying Workflow "{workflow_def['name']}" to {project.key}')
            workflow_name = f"{project.key}: {workflow_def['name']}"
            workflow = self.client.workflows().create(workflow_name, workflow_def['description'], workflow_def, project)
            project.workflows.append(workflow)

        logging.info(f'Applying Workflow Scheme to {project.key}')
        for workflow_scheme_def in template.get('workflow_schemes', []):
            for mapping in workflow_scheme_def['issueTypeMappings']:
                workflow_scheme.add_workflow_issue_type(project.get_issue_type(f"{project.key}: {mapping['issue_type']}"),
                                                        f"{project.key}: {mapping['workflow']}")



        return project


    def create(self, name: str, key: str, template: dict):
        """
        Creates a new project using the specified name, key, and template, and applies the template's
        configuration to the project.

        The method performs the following tasks:
        1. Creates the project using the provided name and key.
        2. Applies groups, fields, issue types, issue type schemes, screens, screen tabs, screen schemes,
           issue type screen schemes, workflows, and workflow schemes, derived from the template.
        3. Links the created elements to the project for proper configuration inheritance.
        4. Tracks all created resources for potential rollback.

        :param name: The name of the project to create.
        :type name: str
        :param key: The unique key for the project.
        :type key: str
        :param template: The template that contains the project configuration, including groups,
                         issue types, fields, screens, workflows, etc.
        :type template: dict
        :return: The created project instance with all configurations applied.
        :rtype: Project
        """
        # Initialise deployment tracker
        tracker = DeploymentTracker(
            project_key=key,
            project_name=name,
            template_name=template.get('name')
        )

        try:
            # Get deploying user email
            try:
                me = self.client.get_me()
                tracker.set_deployed_by(me.get('emailAddress', 'unknown'))
            except Exception:
                pass  # Non-critical, continue without user email

            # Create groups (not tracked as they may be shared)
            self.client.groups().create_groups(template.get('groups', []))

            # Create project
            payload = {
                "key": key,
                "name": name,
                "projectTemplateKey": "com.pyxis.greenhopper.jira:gh-simplified-kanban-classic",
                "projectTypeKey": "software",
                "assigneeType": "UNASSIGNED",
                "leadAccountId": self.client.get_me()['accountId']
            }
            resp = self.client.post(path='/rest/api/3/project', data=payload)
            if resp.status_code != 200 and resp.status_code != 201:
                logging.error(f"Project creation failed. Status: {resp.status_code}, Response: {resp.text}")
            resp.raise_for_status()
            project = Project(resp.json(), self.client)

            # Track project creation
            tracker.set_project_id(project.id)

            logging.info(f'Applying Template "{template.get('name')}" to {project.key}')

            # Assign fields (not tracked individually as fields may be shared)
            project.assign_fields(template.get('fields'))

            # Create and track issue types
            for issue_type_def in template.get('issue_types'):
                logging.info(f'Applying Issue Type "{issue_type_def.get("name")}" to {project.key}')
                issue_type = self.client.issue_types().create(
                    f"{project.key}: {issue_type_def['name']}",
                    issue_type_def['description'],
                    issue_type_def['subtask']
                )
                project.issue_types.append(issue_type)
                tracker.track_issue_type(issue_type.id, f"{project.key}: {issue_type_def['name']}")

            # Create and track issue type schemes
            for issue_type_scheme_def in template.get('issue_type_schemes'):
                target_issue_type_ids = []
                for target_issue_type in issue_type_scheme_def.get('issue_types'):
                    for issue_type in project.issue_types:
                        if issue_type.name == f"{project.key}: {target_issue_type}":
                            target_issue_type_ids.append(issue_type.id)

                issue_type_scheme = self.client.issue_types().create_issue_type_scheme(
                    f"{project.key}: {issue_type_scheme_def['name']}",
                    issue_type_scheme_def['description'],
                    target_issue_type_ids
                )
                project.assign_issue_type_scheme(issue_type_scheme)
                tracker.track_issue_type_scheme(
                    issue_type_scheme.id,
                    f"{project.key}: {issue_type_scheme_def['name']}"
                )

            # Create and track screens
            for screen_def in template.get('screens', []):
                logging.info(f'Applying Screen Def "{screen_def.get("name")}" to {project.key}')
                screen = self.client.screens().create(
                    f"{project.key}: {screen_def['name']}",
                    screen_def['description']
                )
                project.screens.append(screen)
                tracker.track_screen(screen.id, f"{project.key}: {screen_def['name']}")

            # Apply screen tabs
            logging.info(f'Applying Screen Tabs to {project.key}')
            for screen_tab_def in template.get('screen_tabs', []):
                for screen in project.screens:
                    if screen.name == f"{project.key}: {screen_tab_def['screen']}":
                        field_ids = []
                        for field in project.project_fields:
                            for field_name in screen_tab_def['fields']:
                                if field.name == field_name:
                                    if field.id not in field_ids:
                                        field_ids.append(field.id)
                                    break

                        tab = screen.create_tab(screen_tab_def['name'], field_ids)
                        if screen.id not in project.screen_tabs:
                            project.screen_tabs[screen.id] = []
                        project.screen_tabs[screen.id].append(tab)

            # Create and track screen schemes
            for screen_schemes_def in template.get('screen_schemes', []):
                logging.info(f'Applying Screen Scheme Def "{screen_schemes_def['name']}" to {project.key}')
                name = f"{project.key}: {screen_schemes_def['name']}"
                resp = self.client.screens().create_screen_scheme(
                    name,
                    screen_schemes_def['description'],
                    default=project.get_screen(f"{project.key}: {screen_schemes_def['screens']['default']}").id,
                    edit=project.get_screen(f"{project.key}: {screen_schemes_def['screens']['default']}").id,
                    view=project.get_screen(f"{project.key}: {screen_schemes_def['screens']['default']}").id
                )
                project.screen_schemes.append(resp)
                tracker.track_screen_scheme(resp.id, name)

            # Create and track issue type screen schemes
            for issue_type_screen_scheme_def in template.get('issue_type_screen_schemes', []):
                logging.info(f'Applying Screen/Issue Scheme to {project.key}')
                issue_type_screen_scheme_name = f"{project.key}: {issue_type_screen_scheme_def['name']}"
                mappings = []
                for mapping_def in issue_type_screen_scheme_def['mappings']:
                    mappings.append({
                        'issueTypeId': project.get_issue_type(f"{project.key}: {mapping_def['issue_type']}").id,
                        'screenSchemeId': project.get_screen_scheme(f"{project.key}: {mapping_def['screen_scheme']}").id
                    })
                mappings.append({
                    'issueTypeId': 'default',
                    'screenSchemeId': project.get_screen_scheme(f"{project.key}: {issue_type_screen_scheme_def['default_screen_scheme']}").id
                })

                i = self.client.issue_types().create_issue_type_screen_scheme(
                    issue_type_screen_scheme_name,
                    issue_type_screen_scheme_def['description'],
                    mappings
                )
                project.assign_issue_type_screen_scheme(i)
                tracker.track_issue_type_screen_scheme(i.id, issue_type_screen_scheme_name)

            # Create and track workflows
            for workflow_def in template.get('workflows', []):
                logging.info(f'Applying Workflow "{workflow_def['name']}" to {project.key}')
                workflow_name = f"{project.key}: {workflow_def['name']}"
                workflow = self.client.workflows().create(workflow_name, workflow_def['description'], workflow_def, project)
                project.workflows.append(workflow)
                tracker.track_workflow(workflow.entity_id, workflow_name)

            # Create and track workflow schemes
            logging.info(f'Applying Workflow Scheme to {project.key}')
            for workflow_scheme_def in template.get('workflow_schemes', []):
                payload = {
                    "name": f"{project.key}: {workflow_scheme_def['name']}",
                    "description": workflow_scheme_def['description'],
                    "defaultWorkflow": workflow_scheme_def['defaultWorkflow'],
                    "issueTypeMappings": {}
                }

                for mapping in workflow_scheme_def['issueTypeMappings']:
                    issue_type_id = project.get_issue_type(f"{project.key}: {mapping['issue_type']}").id
                    workflow_name = f"{project.key}: {mapping['workflow']}"
                    payload["issueTypeMappings"][f"{issue_type_id}"] = workflow_name

                resp = self.client.post(path='/rest/api/3/workflowscheme', data=payload)
                resp.raise_for_status()
                workflow_scheme_id = resp.json()['id']

                tracker.track_workflow_scheme(
                    workflow_scheme_id,
                    f"{project.key}: {workflow_scheme_def['name']}"
                )

                payload = {
                    "projectId": project.id,
                    "workflowSchemeId": workflow_scheme_id
                }

                resp = self.client.put(path='/rest/api/3/workflowscheme/project', data=payload)
                resp.raise_for_status()

            # Mark deployment as completed
            tracker.mark_completed()
            logging.info(f'Template deployment completed successfully for {project.key}')

            return project

        except Exception as e:
            # Track error and mark deployment as failed
            error_msg = f"Deployment failed: {str(e)}"
            tracker.track_error(error_msg)
            tracker.mark_failed()
            logging.error(error_msg)
            raise