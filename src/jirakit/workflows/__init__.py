import json
import uuid

# Workflow creation moved off the legacy POST /rest/api/3/workflow, which Atlassian
# deprecated in 2024 and has since removed.
WORKFLOW_CREATE_PATH = "/rest/api/3/workflows/create"
WORKFLOW_CREATE_VALIDATION_PATH = "/rest/api/3/workflows/create/validation"

# The legacy AND/OR condition operators are expressed as ALL/ANY operations.
CONDITION_OPERATIONS = {
    "AND": "ALL",
    "OR": "ANY",
    "ALL": "ALL",
    "ANY": "ANY",
}

# Condition types a workflow definition may name, and the rule they map to. Any
# other rule the site supports can be used by giving its rule key directly.
CONDITION_RULE_KEYS = {
    "AllowOnlyAssignee": "system:restrict-issue-transition",
    "ValueFieldCondition": "system:check-field-value",
}


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
        return self.details["default"]

    @property
    def id(self):
        """
        Provides access to the `id` attribute derived from the 'details' dictionary. This property retrieves the
        value associated with the 'id' key, allowing easy access to this specific detail.

        :returns: The value associated with the 'id' key from the `details` dictionary.
        :rtype: Any
        """
        return self.details["id"]

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
        return self.details["description"]

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
        return self.details["lastModifiedDate"]

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
        return self.details["lastModifiedUser"]

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
        return self.details["lastModifiedUserAccountId"]

    @property
    def name(self):
        """
        Retrieves the name property from the details dictionary.

        As with `entity_id`, the shape depends on the endpoint the workflow came
        from. Workflow search nests the name under `id` and sends none at the top
        level, whereas workflow creation returns it at the top level.

        :rtype: str
        :return: The name of the workflow, or None when it carries no name.
        """
        if "name" in self.details:
            return self.details["name"]

        identifier = self.details.get("id")
        if isinstance(identifier, dict):
            return identifier.get("name")
        return None

    @property
    def entity_id(self):
        """
        Retrieves the `entity_id` from the object's `details` attribute.

        The shape depends on the endpoint the workflow came from. Workflow search
        nests the value under `id` as `{'entityId': ...}`, whereas workflow creation
        returns `id` as a plain string, so both forms are accepted.

        :return: The value of the `entity_id` found in the `details` dictionary, or
            None when the workflow carries no identifier.
        :rtype: Any
        """
        if "entityId" in self.details:
            return self.details["entityId"]

        identifier = self.details.get("id")
        if isinstance(identifier, dict):
            return identifier.get("entityId")
        return identifier

    @property
    def steps(self):
        """
        Provides access to the 'steps' property from the 'details' dictionary, allowing for
        retrieval of the corresponding value. This property acts as a convenient
        read-only accessor.

        :return: The value of the 'steps' key from the 'details' dictionary.
        :rtype: Any
        """
        return self.details["steps"]


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
        return self.details["name"]

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
        return self.details["description"]

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
        return self.details["id"]

    @property
    def issue_type_mappings(self):
        """
        Provides access to the `issueTypeMappings` property from the `details` dictionary of the object.

        :return: The mappings of issue types extracted from the `details` dictionary.
        :rtype: Any
        """
        return self.details["issueTypeMappings"]

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
            "workflow": workflow,
        }
        resp = self.client.put(
            f"/rest/api/3/workflowscheme/{self.id}/issuetype/{issue_type.id}",
            data=payload,
        )
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
                path=f"/rest/api/3/workflow/search?startAt={start_at}&maxResults={max_results}&isActive={active}"
            )
            is_last = resp.json()["isLast"]
            start_at += max_results
            for p in resp.json()["values"]:
                _l.append(Workflow(p, self.client))
        return _l

    def create(self, name, description, workflow_definition, project):
        """
        Creates a workflow in the system using the provided details, including its
        name, description, statuses, transitions, and associated project. It ensures
        that all statuses exist or are created, and transitions are properly mapped
        and configured. The workflow is then sent to the relevant API for creation.

        The payload is validated by Jira before it is created, so a definition Jira
        will not accept raises with the validation codes rather than a bare 400.

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
        :raises ValueError: If the definition cannot be translated, or if Jira reports
            errors when validating the resulting payload.
        :return: A Workflow object representing the newly created workflow with all
            associated details from the API response.
        :rtype: Workflow
        """
        workflow_statuses = self.resolve_statuses(
            workflow_definition.get("statuses", [])
        )

        # Statuses are referenced throughout the payload by a client-generated UUID.
        # Supplying the numeric status ID instead fails with STATUS_REFERENCE_NOT_UUID.
        references = {status.name: str(uuid.uuid4()) for status in workflow_statuses}

        payload = {
            "scope": {"type": "GLOBAL"},
            "statuses": [
                {
                    "id": status.id,
                    "statusReference": references[status.name],
                    "name": status.name,
                    "statusCategory": status.status_category,
                }
                for status in workflow_statuses
            ],
            "workflows": [
                {
                    "name": name,
                    "description": description,
                    "startPointLayout": {"x": -100.0, "y": 0.0},
                    "statuses": [
                        {
                            "statusReference": references[status.name],
                            "layout": {"x": float(position * 300), "y": 0.0},
                        }
                        for position, status in enumerate(workflow_statuses)
                    ],
                    "transitions": [
                        self.build_transition(position, transition, references, project)
                        for position, transition in enumerate(
                            workflow_definition.get("transitions", [])
                        )
                    ],
                }
            ],
        }

        self.validate_create_payload(payload)

        resp = self.client.post(WORKFLOW_CREATE_PATH, data=payload)
        resp.raise_for_status()
        return Workflow(resp.json()["workflows"][0], self.client)

    def resolve_statuses(self, status_definitions):
        """
        Resolves the statuses a workflow definition names, creating any the site
        does not already have.

        :param status_definitions: Status entries from the workflow definition, each
            carrying a ``name`` and a ``type`` (the status category).
        :type status_definitions: list
        :raises Exception: If a status of that name exists under a different category.
        :return: The resolved Status objects, in definition order.
        :rtype: list
        """
        site_statuses = self.client.statuses().get_all()
        resolved = []

        for definition in status_definitions:
            status = None
            for candidate in site_statuses:
                if candidate.name == definition["name"]:
                    status = candidate
                    break

            if status is None:
                status = self.client.statuses().create(
                    definition["name"], definition["type"]
                )

            if status.status_category != definition["type"]:
                raise Exception(
                    f"A status of {definition['name']} already exists but has a different status category"
                )
            resolved.append(status)

        return resolved

    def build_transition(self, position, transition, references, project):
        """
        Translates a workflow definition transition into the shape the workflow
        creation API expects.

        :param position: Index of the transition within the workflow, used to derive
            a unique transition ID.
        :type position: int
        :param transition: The transition entry from the workflow definition.
        :type transition: dict
        :param references: Map of status name to the UUID reference assigned to it.
        :type references: dict
        :param project: The project the workflow is being deployed to, used to
            resolve field names to field IDs.
        :type project: Project
        :raises ValueError: If the transition names a status the workflow does not define.
        :return: The translated transition.
        :rtype: dict
        """
        translated = {
            "id": str(position + 1),
            "name": transition["name"],
            "type": transition["type"].upper(),
            "toStatusReference": self.status_reference(transition["to"], references),
            # The legacy list of originating status IDs becomes a list of links.
            "links": [
                {"fromStatusReference": self.status_reference(source, references)}
                for source in transition.get("from", [])
            ],
        }

        if "description" in transition:
            translated["description"] = transition["description"]

        if "conditions" in transition:
            translated["conditions"] = self.build_condition_group(
                transition["conditions"], project
            )

        if "validators" in transition:
            translated["validators"] = [
                self.build_rule(validator, project)
                for validator in transition["validators"]
            ]

        return translated

    def status_reference(self, status_name, references):
        """
        Looks up the UUID reference assigned to a status.

        :param status_name: Name of the status as written in the workflow definition.
        :type status_name: str
        :param references: Map of status name to the UUID reference assigned to it.
        :type references: dict
        :raises ValueError: If the workflow does not define a status of that name.
        :return: The UUID reference for the status.
        :rtype: str
        """
        if status_name not in references:
            raise ValueError(
                f'Transition references status "{status_name}", which the workflow '
                f"does not define; defined statuses are {sorted(references)}"
            )
        return references[status_name]

    def build_condition_group(self, conditions, project):
        """
        Translates a transition's conditions into a condition group.

        :param conditions: The ``conditions`` entry from a transition definition,
            carrying an ``operator`` and a list of conditions.
        :type conditions: dict
        :param project: The project the workflow is being deployed to.
        :type project: Project
        :raises ValueError: If the operator is not one of AND, OR, ALL or ANY.
        :return: The condition group.
        :rtype: dict
        """
        operator = conditions.get("operator", "ALL").upper()
        if operator not in CONDITION_OPERATIONS:
            raise ValueError(
                f'Workflow condition operator "{operator}" is not supported; '
                f"use one of {sorted(CONDITION_OPERATIONS)}"
            )

        return {
            "operation": CONDITION_OPERATIONS[operator],
            "conditionGroups": [],
            "conditions": [
                self.build_rule(condition, project)
                for condition in conditions.get("conditions", [])
            ],
        }

    def build_rule(self, rule, project):
        """
        Translates a condition or validator into a workflow rule configuration.

        A rule that already carries a ``ruleKey`` is passed through with its
        parameters mapped, which lets a template use any rule key the site supports
        without jirakit needing a mapping for it.

        :param rule: The condition or validator entry from a transition definition.
        :type rule: dict
        :param project: The project the workflow is being deployed to.
        :type project: Project
        :raises ValueError: If the rule has no ``ruleKey`` and its ``type`` has no mapping.
        :return: The rule configuration.
        :rtype: dict
        """
        if "ruleKey" in rule:
            return {
                "ruleKey": rule["ruleKey"],
                "parameters": self.map_replace_parameters(
                    rule.get("parameters", {}), project
                ),
            }

        rule_type = rule.get("type")

        if rule_type == "AllowOnlyAssignee":
            return {
                "ruleKey": CONDITION_RULE_KEYS[rule_type],
                "parameters": {"allowUserCustomFields": "assignee"},
            }

        if rule_type == "ValueFieldCondition":
            configuration = rule.get("configuration", {})
            return {
                "ruleKey": CONDITION_RULE_KEYS[rule_type],
                "parameters": self.map_replace_parameters(
                    {
                        "fieldId": configuration["fieldId"],
                        # The API takes the value as a JSON-encoded array of strings.
                        "fieldValue": json.dumps([configuration["fieldValue"]]),
                        "comparator": configuration.get("comparator", "="),
                        "comparisonType": configuration.get("comparisonType", "STRING"),
                    },
                    project,
                ),
            }

        raise ValueError(
            f'Workflow rule type "{rule_type}" has no mapping to a Jira workflow '
            f"rule key; supported types are {sorted(CONDITION_RULE_KEYS)}, "
            f'or supply an explicit "ruleKey"'
        )

    def map_replace_parameters(self, parameters, project):
        """
        Replaces field names in a rule's parameters with their field IDs.

        Parameters that already hold a field ID, or name a field the project does
        not carry, are left as they are.

        :param parameters: The rule parameters.
        :type parameters: dict
        :param project: The project the workflow is being deployed to.
        :type project: Project
        :return: The parameters with field names resolved to field IDs.
        :rtype: dict
        """
        mapped = dict(parameters)

        if "fieldId" in mapped:
            field_id = self.get_field_id_from_name(
                mapped["fieldId"], project.project_fields
            )
            if field_id is not None:
                mapped["fieldId"] = field_id

        return mapped

    def validate_create_payload(self, payload):
        """
        Asks Jira to validate a workflow creation payload before it is sent to be
        created, so that a rejected definition reports why rather than returning a
        bare 400 from the create endpoint.

        :param payload: The workflow creation payload.
        :type payload: dict
        :raises ValueError: If Jira reports any error-level validation findings.
        :return: None
        """
        resp = self.client.post(
            WORKFLOW_CREATE_VALIDATION_PATH,
            data={"payload": payload, "validationOptions": {"levels": ["ERROR"]}},
        )
        resp.raise_for_status()

        errors = [
            error
            for error in resp.json().get("errors", [])
            if error.get("level", "ERROR") == "ERROR"
        ]

        if errors:
            detail = "; ".join(
                f"{error.get('code')}: {error.get('message')}" for error in errors
            )
            raise ValueError(f"Jira rejected the workflow payload: {detail}")

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
        if "statuses" in configuration:
            statuses = []
            for status in configuration["statuses"]:
                statuses.append({"id": self.get_status_id_from_name(status)})
            configuration["statuses"] = statuses

        if "fieldId" in configuration:
            configuration["fieldId"] = self.get_field_id_from_name(
                configuration["fieldId"], project.project_fields
            )

        if "fieldIds" in configuration:
            field_ids = []
            for field_id in configuration["fieldIds"]:
                field_ids.append(
                    self.get_field_id_from_name(field_id, project.project_fields)
                )
            configuration["fieldIds"] = field_ids

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
            resp = self.client.get(
                f"/rest/api/3/workflowscheme?startAt={start_at}&maxResults={max_results}"
            )
            is_last = resp.json().get("isLast")
            start_at += max_results
            for val in resp.json().get("values", []):
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
        resp = self.client.get(
            f"/rest/api/3/workflowscheme/project?projectId={project.id}"
        )
        resp.raise_for_status()
        for v in resp.json()["values"]:
            return WorkflowScheme(v.get("workflowScheme"), self.client)
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
