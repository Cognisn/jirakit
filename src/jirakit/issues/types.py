
class IssueType:
    """
    Represents an issue type with specific attributes and metadata.

    This class provides access to various properties of an issue type, such as
    its ID, name, description, and other related attributes. It interacts with a
    client to retrieve or manage issue type details.

    :ivar type_detail: Detailed information about the issue type, typically
        retrieved from a client or external source.
    :type type_detail: dict
    :ivar client: Reference to the client managing interactions with the source
        of the issue type data.
    :type client: Any
    """
    def __init__(self, type_detail, client):
        """
        Represents the initialization of an object with type details and a client.

        This constructor method initializes the object with the given type details
        and a client instance for further use or processing. The attributes are
        assigned based on the provided inputs.

        :param type_detail: The specific details or attributes representing the type.
        :type type_detail: Any
        :param client: The client instance interacting with the object.
        :type client: Any
        """
        self.type_detail = type_detail
        self.client = client

    @property
    def id(self):
        """
        Retrieves the unique identifier associated with the `type_detail` field.

        The `id` property accesses the `id` attribute within the `type_detail`
        dictionary of the class. It provides a read-only method to obtain the
        unique identifier, which is expected to be present within the
        `type_detail` attribute.

        :returns: The unique identifier extracted from the `type_detail` dictionary.
        :rtype: Any
        """
        return self.type_detail['id']

    @property
    def name(self):
        """
        Provides access to the `name` property, which retrieves the 'name' value
        from the `type_detail` dictionary. This property serves as a convenient
        way to access the 'name' key in objects that store their specific details
        in a `type_detail` structure.

        :return: The value associated with the 'name' key in the `type_detail`
            dictionary.
        :rtype: str
        """
        return self.type_detail['name']

    @property
    def description(self):
        """
        Provides a detailed explanation and access to the 'description' attribute of an
        object. The 'description' is derived dynamically from the 'type_detail' dictionary
        keyed by 'description'. This property is read-only and returns a string value.

        :rtype: str
        :return: The value of the 'description' key from the object's 'type_detail'
            dictionary.
        """
        return self.type_detail['description']

    @property
    def subtask(self):
        """
        Gets the subtask data from the type_detail dictionary.

        This property retrieves the 'subtask' value stored in the object’s
        `type_detail` dictionary. The `type_detail` dictionary is expected
        to contain relevant metadata, and the property specifically pulls
        the 'subtask' key’s value when accessed. This helps encapsulate
        and standardize access to this key.

        :return: The value corresponding to the 'subtask' key in the `type_detail` dictionary.
        :rtype: Any
        """
        return self.type_detail['subtask']

    @property
    def icon_url(self):
        """
        Provides a property that retrieves the URL of the icon from the `type_detail` attribute.

        :return: The URL of the icon as a string.
        :rtype: str
        """
        return self.type_detail['iconUrl']

    @property
    def avatar_id(self):
        """
        Retrieves the avatar ID from the `type_detail` dictionary.

        :return: The avatar ID stored in the `type_detail` dictionary.
        :rtype: Any
        """
        return self.type_detail['avatarId']

    @property
    def hierarchy_level(self):
        """
        Provides access to the hierarchy level information from the `type_detail`
        dictionary attribute. This property retrieves and returns the value
        associated with the `'hierarchyLevel'` key in the `type_detail` dictionary.

        :return: The hierarchy level as stored within the `type_detail` dictionary. It
            is directly accessed via the `'hierarchyLevel'` key.
        """
        return self.type_detail['hierarchyLevel']

class IssueTypeScheme:
    """
    Represents an issue type scheme in a project management or issue tracking
    system with capabilities for managing associated issue types.

    This class provides access to scheme details and performs operations such as
    associating additional issue types with the scheme. It retrieves scheme
    details through a client and enables users to handle issue type schemes
    programmatically.

    :ivar scheme_detail: Metadata and details about the issue type scheme.
    :type scheme_detail: dict
    :ivar client: Client instance used to interact with the backend or API.
    :type client: object
    """
    def __init__(self, scheme_detail, client):
        """
        Represents a base initialization for managing scheme and client information.

        This class provides core properties for scheme details and client
        interaction, which may be utilized throughout the application's context.

        :param scheme_detail: Details related to the scheme being managed,
                              stored as part of the object's state.
        :type scheme_detail: Any
        :param client: A client instance or information for interacting with
                       external systems or performing operations,
                       stored in the object state.
        :type client: Any
        """
        self.scheme_detail = scheme_detail
        self.client = client

    @property
    def id(self):
        """
        Returns the ID of the issue type scheme.

        The method accesses the `scheme_detail` dictionary to retrieve the identifier
        related to the issue type scheme. It looks for the 'issueTypeScheme' key
        first, then 'id', and finally 'issueTypeSchemeId' in the dictionary, returning
        the first value it successfully finds. This approach ensures compatibility
        with varied representations of the scheme detail.

        :raises KeyError: If none of the keys ('issueTypeScheme', 'id',
            'issueTypeSchemeId') is present in `scheme_detail`.
        :return: The ID associated with the issue type scheme, if available.
        :rtype: Any
        """
        return self.scheme_detail.get('issueTypeScheme', self.scheme_detail.get('id', self.scheme_detail.get('issueTypeSchemeId')))

    @property
    def is_default(self):
        """
        Indicates whether the current scheme is the default scheme. This property checks
        the 'isDefault' key in the `scheme_detail` dictionary and returns its value
        to signify if the scheme is marked as default.

        :return: The value of the 'isDefault' key from the `scheme_detail` dictionary,
            indicating if the scheme is the default one.
        :rtype: bool or None
        """
        return self.scheme_detail.get('isDefault')

    def add_issue_type(self, issue_type):
        """
        Adds one or more issue types to the issue type scheme identified by its ID.

        The method iterates over the provided list of issue types, extracts their IDs,
        and organizes them into a payload which is then sent via an HTTP PUT request
        to associate the issue types with the specified issue type scheme. The request
        is expected to succeed without returning a specific response body but raises
        an error if the operation fails.

        :param issue_type: List of issue type objects to be added to the issue type
                           scheme.
        :type issue_type: list
        :return: None
        """
        id_ = []
        for i in issue_type:
            id_.append(i.id)
        payload = {
            "issueTypeIds": id_
        }

        resp = self.client.put(f"/rest/api/3/issuetypescheme/{self.id}/issuetype", data=payload)
        resp.raise_for_status()

class IssueTypeScreenScheme:
    """
    Represents a Jira Issue Type Screen Scheme.

    This class provides methods and attributes to interact with and modify
    a Jira Issue Type Screen Scheme, which is used to map issue types to
    specific screen schemes in Jira.

    :ivar detail: The detailed information of the IssueTypeScreenScheme.
    :type detail: dict
    :ivar client: The client instance used for making API calls.
    :type client: object
    """
    def __init__(self, detail, client):
        """
        Represents an initialization method for a class that sets up the detail
        and client attributes. This constructor allows each created instance
        of the class to be initialized with the provided detail and client
        parameters.

        :param detail: Detail parameter specifying the data or information associated
            with the instance.
        :type detail: str
        :param client: Client parameter representing a client instance or identifier
            used within the class context.
        :type client: object
        """
        self.detail = detail
        self.client = client

    @property
    def id(self):
        """
        Retrieves the unique identifier (ID) of an issue type screen scheme or other detail stored
        within the object's detail attribute.

        :return: The ID value extracted from `self.detail`. If 'issueTypeScreenScheme' exists within
            the `self.detail` dictionary, its associated ID is returned. Otherwise, the ID is fetched
            from the top-level 'id' key of `self.detail`.
        :rtype: str
        """
        return self.detail.get('issueTypeScreenScheme', self.detail)['id']

    def add_mapping(self, issue_type, screen_scheme):
        """
        Add a mapping of an issue type to a screen scheme in the specified screen
        scheme mapping.

        This method sends a PUT request to associate a given issue type with a
        specific screen scheme by interacting with the issue type screen scheme
        API endpoint.

        :param issue_type: The issue type object containing its identifier.
        :type issue_type: IssueType
        :param screen_scheme: The screen scheme object containing its identifier.
        :type screen_scheme: ScreenScheme
        :return: None
        :rtype: None
        :raises requests.HTTPError: Raises an HTTP error if the request fails.
        """
        payload = {
            "issueTypeMappings": [
                {
                    "issueTypeId": issue_type.id,
                    "screenSchemeId": screen_scheme.id
                }
            ]
        }
        resp = self.client.put(f"/rest/api/3/issuetypescreenscheme/{self.id}/mapping", data=payload)
        resp.raise_for_status()

class IssueTypes:
    """Manages operations related to issue types in a project management system.

    This class provides a way to interact with different issue types, issue type schemes,
    and issue type screen schemes within a project management system. It includes methods
    for creating, deleting, and retrieving issue types and related schemes. The user can
    utilize these methods to manage configurations specific to their project environment.

    :ivar client: The client instance used for making HTTP requests to the API.
    :type client: Any
    """
    def __init__(self, client):
        """
        Represents a class for handling client-related operations and interactions.

        This class initializes and stores a client instance for further operations.
        The client instance is expected to be provided during the initialization of
        the class.

        :param client: The client instance to be associated with this class. The
            client is used for handling and managing external interactions.
        :type client: Any
        """
        self.client = client

    def create(self, name, description, subtask) -> IssueType:
        """
        Creates a new issue type within the system based on the provided parameters.

        This method interacts with the API endpoint to create an issue type. It assigns
        a hierarchy level depending on whether the issue type is identified as a subtask
        or a regular issue. Successful API interaction creates a new issue type and
        returns its corresponding object.

        :param name: The name of the issue type to be created.
        :type name: str
        :param description: A detailed description of the issue type.
        :type description: str
        :param subtask: A boolean flag indicating whether the issue type is a subtask.
        :type subtask: bool
        :return: An object representing the newly created issue type.
        :rtype: IssueType
        """
        hierarchy = -1 if subtask else 0
        payload = {
            "name": name,
            "description": description,
            "hierarchyLevel": hierarchy
        }

        resp = self.client.post("/rest/api/3/issuetype", data=payload)
        resp.raise_for_status()
        return IssueType(resp.json(), self.client)

    def delete(self, issue_type: IssueType):
        """
        Deletes an issue type from the system based on the provided issue type ID.

        This method interacts with the REST API to remove the specified issue type.
        It sends a DELETE request to the configured end-point using the ID of the
        issue type and raises an exception if the request fails.

        :param issue_type: The issue type instance containing the identifier of
            the issue type to be deleted.
        :type issue_type: IssueType
        :return: None
        """
        resp = self.client.delete(f"/rest/api/3/issuetype/{issue_type.id}")
        resp.raise_for_status()

    def get_all(self, project_id):
        """
        Retrieves all issue types associated with a specific project ID.

        This method sends an HTTP GET request to the Jira API to fetch issue
        types linked to the given project. The retrieved response, which is
        in JSON format, is processed and converted into a list of `IssueType`
        objects for easier handling in Python.

        :param project_id: The unique identifier of the project whose issue types
            are to be retrieved.
        :type project_id: str

        :return: A list of `IssueType` objects representing the issue types
            associated with the specified project.
        :rtype: list[IssueType]

        :raises requests.exceptions.RequestException: If the HTTP request fails,
            an exception will be raised.
        """
        resp = self.client.get(f"/rest/api/3/issuetype/project?projectId={project_id}")
        resp.raise_for_status()
        _l = []
        for _p in resp.json():
            _l.append(IssueType(_p, self.client))
        return _l

    def get_all_user_issue_types(self):
        """
        Fetches all issue types for the current user by making a request to the API.

        This method interacts with the `/rest/api/3/issuetype` endpoint to retrieve
        a list of issue types available to the user. It parses the API response and
        wraps the resulting data into `IssueType` objects before returning them.

        :raises HTTPError: If the HTTP request to the API fails or returns an error
                           status code.
        :raises Exception: For any issues encountered during the retrieval or
                           processing of the response data.

        :return: A list of `IssueType` objects based on the data retrieved from the
                 API.
        :rtype: list[IssueType]
        """
        resp = self.client.get(f"/rest/api/3/issuetype")
        resp.raise_for_status()
        _l = []
        for _p in resp.json():
            _l.append(IssueType(_p, self.client))
        return _l

    def create_issue_type_scheme(self, name, description, issue_types) -> IssueTypeScheme:
        """
        Create a new issue type scheme with the specified parameters.

        This method sends a POST request to create an issue type scheme in the system
        using the provided name, description, and a list of issue type IDs. The created
        issue type scheme will be returned as an instance of the IssueTypeScheme class
        on successful execution.

        :param name: The name of the issue type scheme to be created.
        :type name: str
        :param description: The description of the issue type scheme.
        :type description: str
        :param issue_types: A list of issue type IDs to be associated with the scheme.
        :type issue_types: list[str]
        :return: An instance of the IssueTypeScheme containing the details of the created
            issue type scheme.
        :rtype: IssueTypeScheme
        """
        payload = {
            "name": name,
            "description": description,
            "issueTypeIds": issue_types
        }

        resp = self.client.post(f"/rest/api/3/issuetypescheme", data=payload)
        resp.raise_for_status()
        return IssueTypeScheme(resp.json(), self.client)

    def create_issue_type_screen_scheme(self, name, description, mapping) -> IssueTypeScreenScheme:
        """
        Creates a new Issue Type Screen Scheme in the Jira instance. The Issue Type
        Screen Scheme defines a mapping between issue types and screen schemes, allowing
        Jira to configure different screens for different issue types. This method
        sends a POST request to the Jira REST API to create the scheme and returns
        the created `IssueTypeScreenScheme`.

        :param name: The name of the Issue Type Screen Scheme to create.
        :type name: str
        :param description: A description for the Issue Type Screen Scheme.
        :type description: str
        :param mapping: A dictionary defining the mapping between issue types
            and screen schemes. The keys are issue type IDs, and values are
            screen scheme IDs.
        :type mapping: dict
        :return: An instance of `IssueTypeScreenScheme` representing the created Issue
            Type Screen Scheme.
        :rtype: IssueTypeScreenScheme
        """
        payload = {
            "name": name,
            "description": description,
            "issueTypeMappings": mapping
        }
        resp = self.client.post(f"/rest/api/3/issuetypescreenscheme", data=payload)
        resp.raise_for_status()
        return IssueTypeScreenScheme(resp.json(), self.client)

    def delete_issue_type_screen_scheme(self, issue_type_screen_scheme: IssueTypeScreenScheme):
        """
        Deletes the specified issue type screen scheme in the system. This operation cannot
        be undone and ensures that the given issue type screen scheme is permanently removed
        from the system by its unique identifier.

        :param issue_type_screen_scheme: The issue type screen scheme to be deleted.
        :type issue_type_screen_scheme: IssueTypeScreenScheme
        :return: None
        """
        resp = self.client.delete(f"/rest/api/3/issuetypescreenscheme/{issue_type_screen_scheme.id}")
        resp.raise_for_status()

    def get_issue_type_screen_schemes(self, project) -> list:
        """
        Retrieves issue type screen schemes associated with the given project.

        This method interacts with the Jira REST API to fetch the issue type screen
        schemes linked to the specified project. It processes the response to
        generate a list of `IssueTypeScreenScheme` objects.

        :param project: The project object containing the ID for which issue type screen
                        schemes need to be fetched.
        :type project: Project
        :return: A list of `IssueTypeScreenScheme` objects derived from the API response.
        :rtype: list
        :raises HTTPError: If the API request fails or returns an error status code.
        """
        _l = []

        resp = self.client.get(f"/rest/api/3/issuetypescreenscheme/project?projectId={project.id}")
        resp.raise_for_status()
        for val in resp.json().get('values', []):
            _l.append(IssueTypeScreenScheme(val, self.client))

        return _l

    def delete_issue_screen_scheme(self, issue_type_screen_scheme: IssueTypeScreenScheme):
        """
        Deletes the specified issue type screen scheme in the Jira system. The operation
        requires the provided issue type screen scheme to have an existing valid ID.
        Upon successful deletion, the server responds with no content.

        :param issue_type_screen_scheme: The issue type screen scheme to be deleted.
                                         It should have a valid ID associated with it.
        :type issue_type_screen_scheme: IssueTypeScreenScheme
        :return: None
        :rtype: None
        """
        resp = self.client.delete(f"/rest/api/3/issuetypescreenscheme/{issue_type_screen_scheme.id}")
        resp.raise_for_status()

    def get_all_issue_type_screen_schemes(self) -> list:
        """
        Fetches all issue type screen schemes from the API in a paginated manner. This method sends
        requests to the specified REST endpoint, retrieves paginated results, and aggregates them
        into a complete list of `IssueTypeScreenScheme` objects.

        :param self:
            Instance of the class containing this method.
        :return:
            A list of `IssueTypeScreenScheme` objects representing all the retrieved issue type
            screen schemes.
        :rtype:
            list
        """
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(f"/rest/api/3/issuetypescreenscheme?startAt={start_at}&maxResults={max_results}")
            is_last = resp.json().get('isLast')
            start_at += max_results
            for val in resp.json().get('values', []):
                _l.append(IssueTypeScreenScheme(val, self.client))
        return _l

    def get_all_issue_type_schemes(self) -> list:
        """
        Retrieve all issue type schemes from the Jira server using paginated API requests.

        This method utilizes Jira's REST API to fetch all available issue type schemes.
        It performs multiple API calls as necessary to handle paginated responses, aggregating
        each page of results into a final list of `IssueTypeScheme` objects.

        :return: A list of all `IssueTypeScheme` retrieved from the Jira server.
        :rtype: list
        """
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(f"/rest/api/3/issuetypescheme?startAt={start_at}&maxResults={max_results}")
            is_last = resp.json().get('isLast')
            start_at += max_results
            for val in resp.json().get('values', []):
                _l.append(IssueTypeScheme(val, self.client))
        return _l

    def get_all_issue_type_schemes_for_project(self, project) -> list:
        """
        Retrieves all issue type schemes associated with a given project. The method paginates
        through the API results to collect all available issue type schemes for the specified project.

        :param project: The project for which the issue type schemes are to be retrieved.
                        The parameter must be an object with an `id` attribute that represents
                        the unique identifier of the project.

        :return: A list of `IssueTypeScheme` objects representing all issue type schemes
                 associated with the specified project.
        :rtype: list
        """
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(f"/rest/api/3/issuetypescheme?startAt={start_at}&maxResults={max_results}&projectId={project.id}")
            is_last = resp.json().get('isLast')
            start_at += max_results
            for val in resp.json().get('values', []):
                _l.append(IssueTypeScheme(val, self.client))
        return _l

    def delete_issue_type_scheme(self, issue_type_scheme: IssueTypeScheme):
        """
        Deletes an issue type scheme from the Jira instance using the provided
        issue type scheme's unique identifier. The API request ensures that the
        scheme is removed, and in case of failure, an exception is raised.

        :param issue_type_scheme: An object of IssueTypeScheme containing the
            identifier for the issue type scheme to be deleted.
        :type issue_type_scheme: IssueTypeScheme
        :return: None
        """
        resp = self.client.delete(f"/rest/api/3/issuetypescheme/{issue_type_scheme.id}")
        resp.raise_for_status()
