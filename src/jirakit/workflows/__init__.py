import json


class Workflow:
    """
    Represents a workflow entity in a client context.

    Provides access to workflow details and attributes such as name, ID,
    description, and other metadata. This class facilitates interaction with
    workflow particulars and operational data through its attributes.

    :ivar details: The dictionary containing workflow details.
    :type details: dict
    :ivar client: The client used to interact with the workflow.
    :type client: Any
    """
    def __init__(self, details, client):
        """
        Represents a class for handling and managing client details.

        Provides an interface to store, access, and potentially manipulate client
        details along with an associated client object. Instances of this class can
        store essential information about the client and its corresponding metadata.

        Attributes
        ----------
        details : Any
            A container or structure holding specific client-related details that may
            include information such as identity, preferences, or additional metadata.
        client : Any
            The client object or reference that may be used to interact with external
            systems or manage client-specific interactions and operations.

        Parameters
        ----------
        details : Any
            The parameter to provide client-specific details that must be stored
            within the instance.
        client : Any
            The parameter for supplying a corresponding client object or reference that
            helps to manage client operations or services.
        """
        self.details = details
        self.client = client

    @property
    def default(self):
        """
        This property represents the default configuration or value associated
        with the instance. It retrieves the 'default' key's value from the
        internal `details` dictionary.

        :return: The value of the 'default' key in the `details` dictionary.
        """
        return self.details['default']

    @property
    def id(self):
        """
        Provides access to the `id` attribute derived from the 'details' dictionary. This property retrieves the
        value associated with the 'id' key, allowing easy access to this specific detail.

        :returns: The value associated with the 'id' key from the `details` dictionary.
        :rtype: Any
        """
        return self.details['id']

    @property
    def description(self):
        """
        Provides access to the description attribute stored within the 'details' dictionary.
        This property allows retrieval of the 'description' field without directly accessing
        the 'details' dictionary, facilitating better encapsulation and abstraction of the
        underlying data structure.

        :return: The value of the 'description' field from the 'details' dictionary.
        :rtype: str
        """
        return self.details['description']

    @property
    def last_modified_date(self):
        """
        Provides the functionality to retrieve the last modified date of an object
        from its details attribute.

        This property accessor is used to fetch the value of the key
        'lastModifiedDate' from the 'details' dictionary attribute of the object.
        The returned value indicates the timestamp when the object was
        last modified.

        :return: The last modified date of the object stored in the
        details dictionary.
        :rtype: Any
        """
        return self.details['lastModifiedDate']

    @property
    def last_modified_user(self):
        """
        Provides access to the 'lastModifiedUser' information from the details attribute.

        This property retrieves the value associated with the key 'lastModifiedUser'
        from the details dictionary. The 'lastModifiedUser' indicates the identifier
        or name of the user who last modified the corresponding entity.

        :return: The user who last modified the associated object.
        :rtype: Any
        """
        return self.details['lastModifiedUser']

    @property
    def last_modified_user_account_id(self):
        """
        Retrieve the identifier of the last user account that modified the associated details.

        This property retrieves the value of the 'lastModifiedUserAccountId' key
        from the `details` dictionary, providing information about the user account
        responsible for the last modification of the related details.

        :rtype: Any
        :return: The identifier of the user account that last modified the details.
        """
        return self.details['lastModifiedUserAccountId']

    @property
    def name(self):
        """
        Retrieves the name property from the details dictionary.

        The name property dynamically accesses the 'name' value within the
        `details` dictionary attribute and returns it when accessed. This property
        provides a convenient way to retrieve the name without directly interacting
        with the internal dictionary.

        :rtype: str
        :return: The value of the 'name' key within the `details` dictionary.
        """
        return self.details['name']

    @property
    def entity_id(self):
        """
        Retrieves the `entity_id` from the object's `details` attribute.

        This property accesses the `details` dictionary to obtain the value of
        `entityId`. If `entityId` is not directly present, it will attempt to retrieve
        it from a nested dictionary under the key `id`.

        :raises KeyError: If neither `entityId` nor the nested `id` dictionary exists
            within `details`.

        :return: The value of the `entity_id` found in the `details` dictionary, or
            in the nested dictionary under the key `id`.
        :rtype: Any
        """
        return self.details.get('entityId', self.details.get('id', {}).get('entityId'))

    @property
    def steps(self):
        """
        Provides access to the 'steps' property from the 'details' dictionary, allowing for
        retrieval of the corresponding value. This property acts as a convenient
        read-only accessor.

        :return: The value of the 'steps' key from the 'details' dictionary.
        :rtype: Any
        """
        return self.details['steps']


class WorkflowScheme:
    """
    Represents a workflow scheme in a project management system.

    A workflow scheme defines how workflows are mapped to issue types in
    a project. Provides access to its properties and allows modifying the
    issue type to workflow mapping.

    :ivar details: Represents the raw details of the workflow scheme.
    :type details: dict
    :ivar client: Client instance used to interact with the remote API.
    :type client: object
    """
    def __init__(self, details, client):
        """
        Represents a generic initialization setup for an object with details and a client.

        This class is used to initialize an object with given details and a client
        instance. The `details` attribute generally refers to the configuration or
        description pertaining to the object, while the `client` attribute often
        refers to an external service or resource associated with the class.

        :param details: The configuration or description associated with the object.
        :type details: Any
        :param client: The client instance for external interactions or operations.
        :type client: Any
        """
        self.details = details
        self.client = client

    @property
    def name(self):
        """
        Retrieve the 'name' attribute from internal details.

        This property accesses the `details` dictionary attribute of the instance
        and retrieves the value associated with the 'name' key. It provides a
        read-only interface to fetch the `name` without direct manipulation of the
        underlying details dictionary.

        :return: The value of the 'name' key stored in the `details` dictionary.
        :rtype: str
        """
        return self.details['name']

    @property
    def description(self):
        """
        Provides a property for accessing the 'description' from the 'details' dictionary.

        The property retrieves a specific value from an instance's 'details' attribute, aimed to
        provide a straightforward and convenient way to access the 'description' field without
        manipulating the dictionary directly.

        :raises KeyError: If the 'description' key is not found in the 'details' dictionary
        :return: The value of the 'description' key from the 'details' dictionary
        :rtype: str
        """
        return self.details['description']

    @property
    def id(self):
        """
        A property to retrieve the unique identifier of an entity from its details.

        This property accesses the `id` value stored in the `details` dictionary of
        the object. It ensures the `id` is extracted whenever this property is called.

        :rtype: Any
        :return: The unique identifier of the entity contained in the `details`
            dictionary.
        """
        return self.details['id']

    @property
    def issue_type_mappings(self):
        """
        Provides access to the `issueTypeMappings` property from the `details` dictionary of the object.

        :return: The mappings of issue types extracted from the `details` dictionary.
        :rtype: Any
        """
        return self.details['issueTypeMappings']

    def add_workflow_issue_type(self, issue_type, workflow):
        """
        Associates a specific issue type with a workflow in a workflow scheme. The issue type
        is linked to the given workflow, updating the draft workflow scheme if necessary. This
        operation leverages the Jira REST API to modify the workflow scheme configuration.

        :param issue_type: The issue type to associate with the workflow
        :type issue_type: Any
        :param workflow: The workflow to be associated with the specified issue type
        :type workflow: Any
        :return: None
        """
        payload = {
            "issueType": issue_type.id,
            "updateDraftIfNeeded": True,
            "workflow": workflow
        }
        resp = self.client.put(f"/rest/api/3/workflowscheme/{self.id}/issuetype/{issue_type.id}", data=payload)
        resp.raise_for_status()


class Workflows:
    """
    Provides functionality for managing Jira workflows including creating, listing,
    and performing other operations related to workflows and workflow schemes.

    This class provides an interface for interacting with the Jira REST API. It is
    typically initialized with a client instance to facilitate direct communication
    with the API. Users can create new workflows, list all available workflows,
    manage workflow schemes, and perform actions such as deletion of inactive workflows.

    :ivar client: Client instance to communicate with the Jira API.
    :type client: Client
    """
    def __init__(self, client):
        """
        Represents a client handler that initializes and stores a given client instance.

        This class is designed to handle and manage a client object passed during
        initialization. It acts as a container for the client instance, enabling further
        operations or interactions through the stored client.

        :param client: Instance of the client to be managed by this handler.
        :type client: Any
        """
        self.client = client

    def get_all(self, active=True):
        """
        Retrieve all workflows from the API with pagination.

        This method fetches workflows from the API by iterating through paginated
        results. The process stops when the last page of results is reached. It allows
        retrieving either active workflows by default or all workflows depending on the
        parameter provided.

        :param active: A boolean flag to filter results based on the activity state
            of workflows. If True, only active workflows are retrieved. Defaults to
            True.
        :type active: bool
        :return: A list of Workflow objects retrieved from the API. Each Workflow
            object represents a single workflow.
        :rtype: list
        """
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(
                path=f'/rest/api/3/workflow/search?startAt={start_at}&maxResults={max_results}&isActive={active}')
            is_last = resp.json()['isLast']
            start_at += max_results
            for p in resp.json()['values']:
                _l.append(Workflow(p, self.client))
        return _l

    def create(self, name, description, workflow_definition, project):
        """
        Creates a workflow in the system using the provided details, including its
        name, description, statuses, transitions, and associated project. It ensures
        that all statuses exist or are created, and transitions are properly mapped
        and configured. The workflow is then sent to the relevant API for creation.

        :param name: Name of the workflow to be created.
        :type name: str
        :param description: Brief description of the workflow.
        :type description: str
        :param workflow_definition: The definition of the workflow, containing its
            statuses and transitions.
        :type workflow_definition: dict
        :param project: The project associated with the workflow, used for mapping
            configurations.
        :type project: str
        :return: A Workflow object representing the newly created workflow with all
            associated details from the API response.
        :rtype: Workflow
        """
        statuses = self.client.statuses().get_all()
        workflow_statuses = []
        transitions = []
        for status in workflow_definition.get('statuses', []):
            workflow_status = None
            for s in statuses:
                if s.name == status['name']:
                    workflow_status = s
                    break
            if workflow_status is None:
                workflow_status = self.client.statuses().create(status['name'], status['type'])

            if workflow_status.status_category != status['type']:
                raise Exception(f"A status of {status['name']} already exists but has a different status category")
            workflow_statuses.append(workflow_status)

        for transition in workflow_definition.get('transitions', []):
            t = {
                'name': transition['name'],
                'type': transition['type'],
                'to': self.get_status_id_from_name(transition['to']),
                'rules': {}
            }

            if 'from' in transition:
                t['from'] = []
                for trf in transition['from']:
                    t['from'].append(self.get_status_id_from_name(trf))

            if 'conditions' in transition:
                t['rules']['conditions'] = transition['conditions']
                for condition in t['rules']['conditions']['conditions']:
                    if 'configuration' in condition:
                        condition['configuration'] = self.map_replace_configurations(condition['configuration'],
                                                                                     project)

            if 'validators' in transition:
                t['rules']['validators'] = transition['validators']
                for condition in t['rules']['validators']:
                    if 'configuration' in condition:
                        condition['configuration'] = self.map_replace_configurations(condition['configuration'],
                                                                                     project)

            transitions.append(t)

        status_ids = []
        for status in workflow_statuses:
            status_ids.append({'id': status.id})
        payload = {
            'name': name,
            'description': description,
            'statuses': status_ids,
            'transitions': transitions,
        }

        resp = self.client.post('/rest/api/3/workflow', data=payload)
        resp.raise_for_status()
        return Workflow(resp.json(), self.client)

    def map_replace_configurations(self, configuration, project):
        """
        Maps and replaces specific configuration fields with corresponding IDs or lists of IDs
        based on the provided project context. This function modifies certain keys in the input
        configuration structure to ensure compatibility with the project configuration.

        :param configuration: A dictionary containing the current configuration mappings that
            may include statuses, field ID, or field IDs to be replaced with appropriate IDs.
        :type configuration: dict
        :param project: The project instance which contains the details and context for field
            ID resolution. This instance provides access to relevant project fields for mapping.
        :type project: Project
        :return: The updated configuration dictionary with mapped and replaced statuses or
            field IDs based on the input data and project details.
        :rtype: dict
        """
        if 'statuses' in configuration:
            statuses = []
            for status in configuration['statuses']:
                statuses.append({"id": self.get_status_id_from_name(status)})
            configuration['statuses'] = statuses

        if 'fieldId' in configuration:
            configuration['fieldId'] = self.get_field_id_from_name(configuration['fieldId'], project.project_fields)

        if 'fieldIds' in configuration:
            field_ids = []
            for field_id in configuration['fieldIds']:
                field_ids.append(self.get_field_id_from_name(field_id, project.project_fields))
            configuration['fieldIds'] = field_ids

        return configuration

    def get_field_id_from_name(self, name, project_fields):
        """
        Retrieve the unique identifier of a field based on its name from a list
        of project fields. This function iterates through the provided list of
        project fields and compares the name attribute of each field with the
        given name. If a match is found, the corresponding field's identifier is
        returned.

        :param name: The name of the field to search for.
        :type name: str
        :param project_fields: A list containing the fields of a project.
        :type project_fields: list
        :return: The unique identifier of the field that matches the given name.
        :rtype: Any
        """
        for field in project_fields:
            if field.name == name:
                return field.id

    def get_status_id_from_name(self, name):
        """
        Retrieves the unique identifier (ID) of a status based on its name.

        This method fetches all available statuses using the `statuses()` method of the
        `client` and searches for the status that matches the specified name. If a match
        is found, the method returns the corresponding status ID. If no match is found,
        no explicit return value is provided.

        :param name: The name of the status for which the ID is being retrieved.
        :type name: str
        :return: The ID of the status matching the specified name or None if no match
            is found.
        :rtype: int | None
        """
        statuses = self.client.statuses().get_all()
        for status in statuses:
            if status.name == name:
                return status.id

    def get_all_workflow_schemes(self) -> list:
        """
        Retrieve all workflow schemes using the Jira REST API by paginating through
        the results until all available schemes have been fetched.

        The method sends repeated GET requests to the endpoint
        "/rest/api/3/workflowscheme" using a maximum results pagination scheme. It
        collects all available workflow schemes and returns them as a list of
        WorkflowScheme objects.

        :param self: Instance of the client to make API calls.
        :return: List of WorkflowScheme objects representing all workflows fetched
            through the API.
        :rtype: list
        """
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(f"/rest/api/3/workflowscheme?startAt={start_at}&maxResults={max_results}")
            is_last = resp.json().get('isLast')
            start_at += max_results
            for val in resp.json().get('values', []):
                _l.append(WorkflowScheme(val, self.client))
        return _l

    def get_workflow_scheme_for_project(self, project) -> WorkflowScheme:
        """
        Retrieves the workflow scheme associated with the specified project.

        This function utilizes the provided project's ID to query the Jira REST API
        and fetch the workflow scheme linked to that project. If there are no available
        workflow schemes or an error occurs during the API call, the function will
        either return None or raise an appropriate exception.

        :param project: The project object whose workflow scheme is to be fetched
                        using its ID.
        :type project: Project
        :return: An instance of WorkflowScheme if a workflow scheme is associated
                 with the project, or None if no such scheme exists.
        :rtype: WorkflowScheme or None
        :raises HTTPError: If there is an issue with the API request/response.
        """
        resp = self.client.get(f"/rest/api/3/workflowscheme/project?projectId={project.id}")
        resp.raise_for_status()
        for v in resp.json()['values']:
            return WorkflowScheme(v.get('workflowScheme'), self.client)
        return None

    def delete_workflow_scheme(self, workflow: WorkflowScheme):
        """
        Deletes the specified workflow scheme by making an HTTP DELETE request to the
        corresponding API endpoint. This operation removes the workflow scheme from the
        system entirely.

        :param workflow: The workflow scheme to be deleted. It must be a valid instance
            of WorkflowScheme with a defined ID.
        :type workflow: WorkflowScheme
        :return: None
        :rtype: NoneType
        :raises requests.HTTPError: If the HTTP request fails or the server returns a
            status indicating an error.
        """
        resp = self.client.delete(f"/rest/api/3/workflowscheme/{workflow.id}")
        resp.raise_for_status()

    def delete_inactive_workflow(self, workflow: Workflow):
        """
        Deletes an inactive workflow by its entity ID.

        This method provides functionality to interact with a given API endpoint
        to delete a workflow specified by its entity ID. It checks and ensures
        the provided workflow is inactive before deletion, ensuring safe use of
        the API.

        :param workflow: Represents the workflow to be deleted. Must be inactive.
        :type workflow: Workflow
        :return: None
        """
        resp = self.client.delete(f"/rest/api/3/workflow/{workflow.entity_id}")
        resp.raise_for_status()