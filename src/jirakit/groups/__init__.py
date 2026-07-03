
class Group:
    """
    Representation of a group within a system.

    This class provides an abstraction for a group, encapsulating its details
    and associated client instance. It includes properties to access
    the group name and ID, which are retrieved from the group details.

    :ivar detail: Dictionary containing details of the group.
    :type detail: dict
    :ivar client: Client instance associated with the group.
    :type client: Any
    """
    def __init__(self, detail, client):
        """
        Represents a class responsible for managing client details and associated
        information. This class initializes its state with the provided details and
        client instance, allowing further operations or manipulations based on
        these attributes.

        :param detail: Contains the details or information related to the specific
                       client. The exact structure or format should be determined
                       by its usage.
        :type detail: Any
        :param client: Represents the client entity or object associated with the
                       current instance. This might be a string, an object, or
                       another data type as required by the application logic.
        :type client: Any
        """
        self.detail = detail
        self.client = client

    @property
    def name(self):
        """
        Represents a property of the object that retrieves the 'name' value from
        the `detail` attribute.

        This property provides access to the 'name' field stored in the
        `detail` dictionary of the instance.

        :return: The value associated with the 'name' key in the `detail`
            attribute.
        :rtype: Any
        """
        return self.detail['name']

    @property
    def id(self):
        """
        This property retrieves the 'groupId' value from the 'detail' attribute.
        The value returned corresponds to the unique identifier for a specific group
        within the current context.

        :rtype: str
        :return: The unique identifier of the group as stored in the 'groupId' key
            of the 'detail' dictionary.
        """
        return self.detail['groupId']

class Groups:
    """
    Represents a collection of groups and provides functionality to manage them.

    The Groups class is used to interact with a group management API. It allows
    fetching a list of groups, creating individual groups, and batch-creating
    multiple groups while avoiding duplication. This class requires a client
    object to perform API operations and expects the responses to conform to a
    specific schema.

    :param client: The client instance to interact with the API.
    :type client: object

    :ivar client: The API client used for making requests to the group resource.
    :type client: object
    """
    def __init__(self, client):
        """
        Represents a class that interacts with a client object to handle
        specific operations or functionality.

        Attributes
        ----------
        client : object
            An instance of the client object passed at initialization, which
            will be used for further operations or interactions.

        Methods
        -------
        This class may contain various methods designed to use the client
        object for specific tasks or processes.

        :param client: The client object required for initialization of the class.
        :type client: Any
        """
        self.client = client

    def get_groups(self):
        """
        Retrieves a list of groups by paginating through results obtained from the
        API endpoint. The method continues fetching until all pages are exhausted.

        :raises KeyError: If the response from the API does not contain the expected 'isLast'
            or 'values' keys.
        :raises ValueError: If the API response is invalid or not as expected.
        :raises AttributeError: If the `client` attribute is not properly initialized or
            does not have a `get` method.
        :raises TypeError: If any unexpected type is encountered during processing.

        :return: A list of `Group` objects obtained from the API endpoint.
        :rtype: list[Group]
        """
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(f"/rest/api/3/group/bulk?startAt={start_at}&maxResults={max_results}")
            is_last = resp.json().get('isLast')
            start_at += max_results
            for val in resp.json().get('values', []):
                _l.append(Group(val, self.client))
        return _l

    def create_group(self, name):
        """
        Creates a new group with the specified name.

        This function sends a POST request to create a new group using the provided name.
        The function wraps the response into a `Group` object upon success. Ensure that
        the name provided is valid and adheres to any constraints or requirements set by
        the API. The client used for the request is an instance variable of the containing class.

        :param name: The name of the group to create.
        :type name: str
        :return: A `Group` object representing the newly created group.
        :rtype: Group
        :raises HTTPError: If the API request fails or the response indicates an error.
        """
        payload = {
            "name": name
        }
        resp = self.client.post("/rest/api/3/group", data=payload)
        resp.raise_for_status()
        return Group(resp.json(), self.client)

    def create_groups(self, group_names: list):
        """
        Creates new groups from the provided list of group names. The method checks if a group
        with the given name already exists among the existing groups, and only creates groups
        for names that do not already exist. The newly created groups are then returned as a list.

        :param group_names: A list of group names as strings for the desired groups to create.
        :return: A list containing the newly created group objects.
        """
        _l = []
        for name in group_names:
            found = False
            for group in self.get_groups():
                if name == group.name:
                    found = True
                    break
            if not found:
                _l.append(self.create_group(name))

        return _l