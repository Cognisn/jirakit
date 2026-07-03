
class Status:
    """
    Represents the status of an entity, encapsulating various details about
    its attributes, state, and usage scope.

    This class is designed to provide a structured way to access status-related
    information derived from a given detail dictionary and a client context.
    It includes properties that allow retrieval of specific attributes of the
    status, such as its ID, description, or usage.

    :ivar detail: A dictionary containing detailed status information.
    :type detail: dict
    :ivar client: An instance representing the client associated with the status.
    :type client: Any
    """
    def __init__(self, detail, client):
        """
        Represents an object that encapsulates detail and client information.

        This class provides a simple representation to store and manage the
        attributes `detail` and `client`. The attributes are managed during
        object instantiation, and no additional functionality is tied to them
        within this class.

        :param detail: The specific detail data related to the object.
        :type detail: Any
        :param client: The client data associated with the object.
        :type client: Any
        """
        self.detail = detail
        self.client = client

    @property
    def id(self):
        """
        Represents a property method to retrieve the `id` attribute from a dictionary
        stored in the `detail` attribute.

        This property provides access to the `id` value stored within the internal
        `detail` dictionary of the object.

        :return: The `id` value retrieved from the `detail` dictionary.
        :rtype: Any
        """
        return self.detail['id']

    @property
    def description(self):
        """
        Provides the description of an instance based on the 'description' key
        of the `detail` property, typically representing metadata or specific
        information about the instance.

        :return: A string containing the description information.
        :rtype: str
        """
        return self.detail['description']

    @property
    def name(self):
        """
        Represents a property accessor for the `name` detail of an object.

        The `name` property retrieves the value associated with the `name` key
        from the `detail` dictionary attribute of the containing object. This
        property provides read-only access to the `name` detail.

        :rtype: str
        :return: The value of the `name` key from the `detail` attribute.
        """
        return self.detail['name']

    @property
    def scope(self):
        """
        Represents a property that retrieves the 'scope' key's value from the
        'detail' dictionary. This function acts as a getter for accessing the
        'scope' component of the 'detail' attribute.

        :raises KeyError: If the 'scope' key is not present in the 'detail'
            dictionary.
        :raises TypeError: If 'detail' is not a dictionary with string keys
            and corresponding values.
        :return: The value associated with the 'scope' key in the 'detail'
            dictionary.
        :rtype: Any
        """
        return self.detail['scope']

    @property
    def status_category(self):
        """
        Fetches and returns the status category of the detail attribute.

        This property retrieves the 'statusCategory' key from the 'detail' dictionary
        and provides its value, which represents the category of the status within the
        context of the object's detail.

        :rtype: Any
        :return: The value associated with the 'statusCategory' key in the `detail`
            dictionary.
        """
        return self.detail['statusCategory']

    @property
    def usages(self):
        """
        Provides access to the 'usages' information stored in the 'detail' dictionary
        attribute of the class. This property retrieves the specific value associated
        with the 'usages' key in the 'detail' dictionary.

        :return: The value corresponding to the 'usages' key within the 'detail'
            dictionary. This provides details regarding the 'usages' attribute
            that may be defined in the class.
        :rtype: Any
        """
        return self.detail['usages']

    @property
    def workflow_usages(self):
        """
        Retrieves the workflow usages associated with the given object.

        This property accesses the `workflowUsages` data from the `detail` dictionary
        attribute of the object. It provides information regarding the usages of
        workflows associated with the specific object.

        :rtype: dict
        :return: A dictionary containing the workflow usages data retrieved from
                 the `detail` attribute.
        """
        return self.detail['workflowUsages']

class Statuses:
    """
    The Statuses class provides functionality to manage statuses in a system by interacting
    with a REST API. This includes creating, retrieving, and deleting statuses, as well as
    handling their associated details.

    It is designed to interface with a pre-configured client object that enables communication
    with the API endpoints.

    :ivar client: The client object used to make API requests.
    :type client: Any
    """
    def __init__(self, client):
        """
        Represents a generic class for initializing an object with a client.

        This class serves as a wrapper that requires a client object. It provides a
        container for the client that can be used across other instances or
        functionalities where this object is initialized.

        :param client: The client object required for initializing the class.

        :ivar client: This attribute holds the reference to the client object passed
            during initialization. It is accessible for further usage within the
            class or external calls.
        """
        self.client = client

    def get_all(self):
        """
        Fetches all statuses with their usage and workflow usage details from the API.

        This method sends a GET request to the specified API endpoint to retrieve
        all statuses in the system. It automatically raises exceptions for HTTP
        errors and processes the response to create a list of `Status` objects
        with the data returned by the API.

        :raises Exception: If the GET request fails for any HTTP-related reasons.
        :return: A list of `Status` objects representing the statuses retrieved
                 from the API with their usage and workflow usage details.
        :rtype: list[Status]
        """

        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(f"/rest/api/3/statuses/search?expand=usages,workflowUsages&startAt={start_at}&maxResults={max_results}")
            is_last = resp.json().get('isLast')
            start_at += max_results
            for status_data in resp.json().get('values', []):
                _l.append(Status(status_data, self.client))
        return _l

    def delete(self, status: Status):
        """
        Deletes a specific status by its unique identifier. This method sends a DELETE
        request to the Jira API to remove the status associated with the given ID.

        The operation ensures the deletion is processed successfully by raising an
        exception for any HTTP errors encountered.

        :param status: The Status object containing the ID of the status to be deleted.
        :type status: Status
        :return: None
        """
        resp = self.client.delete(path=f'/rest/api/3/statuses?id={status.id}')
        resp.raise_for_status()

    def create(self, name, status_category, description=''):
        """
        Creates a new status in the system with the specified name, status category,
        and an optional description. This method sends a POST request to the API to
        create the status and returns the created status object upon success.

        :param name: The name of the status to be created.
        :type name: str
        :param status_category: The category of the status, such as "To Do",
            "In Progress", or "Done".
        :type status_category: str
        :param description: (Optional) A detailed description of the status.
            Defaults to an empty string when not provided.
        :type description: str, optional
        :return: A status object representing the newly created status.
        :rtype: Status
        """
        payload = {
            "scope": {
                "type": "GLOBAL"
            },
            "statuses": [
                {
                    "description": description,
                    "name": name,
                    "statusCategory": status_category
                }
            ]

        }
        resp = self.client.post(path='/rest/api/3/statuses', data=payload)
        resp.raise_for_status()
        return Status(resp.json()[0], self.client)