import logging


class Screen:
    """
    Represents a Screen entity in a system managing screen configurations.

    This class provides access to various details of a screen along with the ability
    to perform operations such as fetching screen tabs and creating new tabs with
    specific fields. The class relies on an external client for making API requests.

    :ivar screen_detail: Contains the details of the screen such as its ID, name, and
        description.
    :type screen_detail: dict
    :ivar client: A client instance used to interact with the external API.
    :type client: Client
    """

    def __init__(self, screen_detail, client):
        """
        Represents the initialization of a class with screen details and client object.

        This constructor initializes the class with the provided screen_detail and
        client attributes, which are stored for later use. It serves as the entry
        point for creating an instance of this class.

        :param screen_detail: The details or specifications of the screen, required
            during initialization.
        :type screen_detail: Any

        :param client: The client object associated with this instance, required
            during initialization.
        :type client: Any
        """
        self.screen_detail = screen_detail
        self.client = client

    @property
    def id(self):
        """
        Provides access to the `id` property from the `screen_detail` dictionary. This property
        represents the identifier related to the screen details of the object.

        :return: The identifier value from the `screen_detail` dictionary.
        :rtype: str
        """
        return self.screen_detail["id"]

    @property
    def name(self):
        """
        Provides an interface to retrieve the name of the screen from the screen details.

        This property accesses the 'name' key within the `screen_detail` dictionary
        and returns its corresponding value. It is useful for fetching the name
        identifier associated with the screen without directly accessing the internal
        attribute dictionary.

        :rtype: str
        :return: The name of the screen as a string extracted from the 'name' key of
            `screen_detail`.
        """
        return self.screen_detail["name"]

    @property
    def description(self):
        """
        Provides a description of the screen detail.

        The `description` property retrieves the 'description' key from the
        `screen_detail` dictionary attribute of the object. This property allows
        read-only access to the specific piece of information related to the screen
        detail's description.

        :return: The value of the 'description' key from the `screen_detail` dictionary
        :rtype: str
        """
        return self.screen_detail["description"]

    def get_tabs(self, project):
        """
        Retrieves and returns the tabs associated with a specific screen and project.

        This method interacts with the Jira REST API to fetch the tabs linked to the
        screen identified by the current instance's `id`. Tabs represent logical
        groupings of fields on a Jira screen. The `project` parameter is utilized
        to specify the project context for which the tabs should be retrieved.

        :param project: The project object that contains the `id` key representing
            the target Jira project.
        :type project: Project
        :return: A JSON object representing the tabs associated with the given
            screen and project.
        :rtype: dict
        :raises HTTPError: If the HTTP request to fetch the tabs fails.
        """
        resp = self.client.get(
            path=f"/rest/api/3/screens/{self.id}/tabs?projectKey={project.key}"
        )
        resp.raise_for_status()
        return resp.json()

    def create_tab(self, name, fields):
        """
        Creates a new tab in the screen specified by its ID and populates it with the provided fields.

        This method initializes a new tab within the context of a specific screen by sending a request
        to the server with the provided tab name. It then iterates over the given fields, associating
        each field with the newly created tab by making further requests. If a request fails during
        this process, the method logs the exception and re-raises it to be handled by the caller.

        :param name: Name of the tab to be created.
        :type name: str
        :param fields: A list of field IDs to be added to the newly created tab.
        :type fields: list[str]
        :return: A dictionary containing the details of the newly created tab, as returned by the server.
        :rtype: dict
        """
        payload = {
            "name": name,
        }
        resp = self.client.post(
            path=f"/rest/api/3/screens/{self.id}/tabs", data=payload
        )
        resp.raise_for_status()
        tab_detail = resp.json()
        for field in fields:
            payload = {
                "fieldId": field,
            }
            try:
                resp = self.client.post(
                    path=f"/rest/api/3/screens/{self.id}/tabs/{tab_detail['id']}/fields",
                    data=payload,
                )
                resp.raise_for_status()
            except Exception as e:
                logging.exception(e)
                raise e
        return tab_detail

    def add_field(self, field_id):
        """
        Adds a field to this screen's default (first) tab, idempotently.

        Resolves the screen's tabs and adds the field to the first one, but only
        if the field is not already present on any tab of the screen (a field
        may sit on only one tab per screen, so the whole screen is checked
        before writing). Used to place a newly provisioned custom field onto an
        operator-chosen screen.

        :param field_id: The id of the field to add, for example 'customfield_10050'.
        :type field_id: str
        :return: None
        :raises ValueError: If the screen has no tabs to add the field to.
        :raises requests.HTTPError: If any request fails.
        """
        resp = self.client.get(path=f"/rest/api/3/screens/{self.id}/tabs")
        resp.raise_for_status()
        tabs = resp.json()
        if not tabs:
            raise ValueError(f"Screen {self.id} has no tabs to add a field to")

        # A field can only be on one tab per screen, so check every tab before
        # writing; if it is already present anywhere, there is nothing to do.
        for tab in tabs:
            existing = self.client.get(
                path=f"/rest/api/3/screens/{self.id}/tabs/{tab['id']}/fields"
            )
            existing.raise_for_status()
            if any(field.get("id") == field_id for field in existing.json()):
                return

        tab_id = tabs[0]["id"]
        resp = self.client.post(
            path=f"/rest/api/3/screens/{self.id}/tabs/{tab_id}/fields",
            data={"fieldId": field_id},
        )
        resp.raise_for_status()


class ScreenScheme:
    """
    Represents a screen scheme in a client interface.

    A screen scheme is used to manage and organize the relationship between
    screens and different operations in the system. It includes details such
    as its unique identifier, name, description, and associated screens. This
    class allows for retrieval of unique screen IDs and encapsulates the
    screen scheme properties for interaction with the client.

    :ivar detail: Contains all details of the screen scheme.
    :type detail: dict
    :ivar client: Represents the client that interacts with the screen scheme.
    :type client: object
    """

    def __init__(self, detail, client):
        """
        Represents an example class with attributes for detail and client.

        This class serves as a simple example for storing and managing a
        combination of a detail string and a client object. Instances of
        this class are typically initialized with these attributes.

        :param detail: A description or detail related to this example.
        :type detail: str
        :param client: The client object associated with this example.
        :type client: object
        """
        self.detail = detail
        self.client = client

    @property
    def id(self):
        """
        Provides access to the `id` attribute from the `detail` dictionary property.

        This property retrieves the value associated with the `id` key in the
        `detail` dictionary of the object.

        :raises KeyError: If the `id` key does not exist in the `detail` dictionary.
        :return: The value of the `id` key in the `detail` dictionary.
        :rtype: Any
        """
        return self.detail["id"]

    @property
    def name(self):
        """
        Provides access to the 'name' attribute from the 'detail' dictionary.

        This property is used to retrieve the value of the 'name' key in the
        'detail' dictionary associated with the instance. The property is
        read-only and allows external access to this specific data in a
        controlled manner.

        :return: The value associated with the 'name' key in the 'detail' dictionary
        :rtype: str
        """
        return self.detail["name"]

    @property
    def description(self):
        """
        Provides access to the 'description' detail within the object's 'detail' dictionary attribute.

        This read-only property retrieves the value of the key 'description', which is expected to
        exist in the 'detail' dictionary. It is primarily intended for fetching a descriptive text or
        message associated with the object.

        :raises KeyError: If the key 'description' is not found within the 'detail' dictionary.

        :return: The value corresponding to the 'description' key from the 'detail' dictionary.
        :rtype: str
        """
        return self.detail["description"]

    def get_screen_ids(self):
        """
        Extract unique screen IDs from the provided detail attribute of the instance.

        This method iterates through the 'screens' dictionary in `self.detail` and
        aggregates all unique values to return them as a list. It avoids duplicates
        by checking if a value already exists in the list before appending.

        :return: A list of unique screen IDs
        :rtype: list
        """
        _l = []
        for screen in self.detail["screens"]:
            if self.detail["screens"][screen] not in _l:
                _l.append(self.detail["screens"][screen])
        return _l


class Screens:
    """
    The Screens class provides functionalities to interact with screen and screen scheme
    configurations in a system via an API. It allows for creating, retrieving, deleting
    screens and screen schemes, as well as fetching all available screens or screen schemes.

    This class is primarily designed for managing screen layouts or configurations
    related to different use cases within an application.

    :ivar client: An instance of the client used for making API requests.
    :type client: any
    """

    def __init__(self, client):
        """
        Represents initialization for a client-based instance.

        This constructor initializes an instance of the class using the provided
        client object. This allows the object to interact or operate with the
        client instance passed during its creation. Initialization ensures that
        the instance is correctly set up with the required client.

        :param client: The client object used to set up the instance.
        :type client: Any
        """
        self.client = client

    def create(self, name, description):
        """
        Creates a new screen using the provided name and description. This method sends
        a POST request to the Jira API endpoint to create the screen and returns an
        instance of the newly created Screen object.

        :param name: The name of the screen to be created.
        :type name: str
        :param description: A brief description of the screen to be created.
        :type description: str
        :return: An instance of the newly created Screen object.
        :rtype: Screen
        :raises HTTPError: If the HTTP request fails or the response contains an error.
        """
        payload = {"name": name, "description": description}
        resp = self.client.post("/rest/api/3/screens", data=payload)
        resp.raise_for_status()
        return Screen(resp.json(), self.client)

    def create_screen_scheme(
        self, name, description, default, edit, view
    ) -> ScreenScheme:
        """
        Creates a new screen scheme in the system with the specified configurations. The screen
        scheme is defined by providing the name, description, and associated screens (default, view, edit).
        This function communicates with the API to create the screen scheme and retrieves the created
        screen scheme based on its assigned ID.

        :param name: The name of the screen scheme to be created.
        :type name: str
        :param description: A brief description of the screen scheme.
        :type description: str
        :param default: Identifier for the default screen to be associated with the screen scheme.
        :type default: str
        :param edit: Identifier for the edit screen to be associated with the screen scheme.
        :type edit: str
        :param view: Identifier for the view screen to be associated with the screen scheme.
        :type view: str
        :return: The created screen scheme object after successful creation and retrieval.
        :rtype: ScreenScheme
        """
        payload = {
            "name": name,
            "description": description,
            "screens": {"edit": edit, "view": view, "default": default},
        }
        resp = self.client.post("/rest/api/3/screenscheme", data=payload)
        resp.raise_for_status()
        return self.get_screen_scheme(resp.json()["id"])

    def get_screen_scheme(self, screen_scheme_id) -> ScreenScheme:
        """
        Retrieves a specific screen scheme by its ID. This function sends a GET request
        to the Jira API and fetches the information of the requested screen scheme.
        The returned data is used to create and return a `ScreenScheme` object.

        :param screen_scheme_id: The ID of the screen scheme to retrieve.
        :type screen_scheme_id: int
        :return: An instance of `ScreenScheme` representing the requested screen scheme.
        :rtype: ScreenScheme
        :raises HTTPError: If the HTTP request to the Jira API fails with an HTTP error.
        :raises KeyError: If the expected data structure is not found in the API response.
        """
        resp = self.client.get(f"/rest/api/3/screenscheme?id={screen_scheme_id}")
        resp.raise_for_status()
        return ScreenScheme(resp.json()["values"][0], self.client)

    def delete_screen_scheme(self, screen_scheme: ScreenScheme):
        """
        Deletes an existing screen scheme from the system. This operation is irreversible
        and removes the associated screen scheme by its unique identifier.

        :param screen_scheme: The screen scheme object to be deleted.
        :type screen_scheme: ScreenScheme
        :return: None
        """
        resp = self.client.delete(f"/rest/api/3/screenscheme/{screen_scheme.id}")
        resp.raise_for_status()

    def get_all_screen_schemes(self) -> list:
        """
        Retrieves all screen schemes in the system by iterating through paginated API responses.

        This method fetches all screen schemes by making multiple API calls to handle pagination. It starts from the first page,
        fetching a limited number of results at a time until the last page is reached. The results from all pages are aggregated
        and returned as a single list of `ScreenScheme` objects.

        :param self: Object of the calling class. Contains the client to make API calls.

        :rtype: list
        :return: A list of `ScreenScheme` objects representing the available screen schemes.
        """
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(
                f"/rest/api/3/screenscheme?startAt={start_at}&maxResults={max_results}"
            )
            is_last = resp.json().get("isLast")
            start_at += max_results
            for val in resp.json().get("values", []):
                _l.append(ScreenScheme(val, self.client))
        return _l

    def get_screen(self, _id) -> Screen:
        """
        Fetches the Screen object associated with the given screen ID.

        The method retrieves screen information from the specified API endpoint using
        the given screen ID and returns it encapsulated within a Screen object.

        :param _id: The unique identifier of the screen to retrieve.
        :type _id: int
        :return: An instance of Screen representing the retrieved screen details.
        :rtype: Screen
        :raises: HTTPError if the request to the API endpoint fails or the status code
                 indicates an error.
        """
        resp = self.client.get(f"/rest/api/3/screens?id={_id}")
        resp.raise_for_status()
        return Screen(resp.json()["values"][0], self.client)

    def get_all_screens(self) -> list:
        """
        Retrieves all screens by making paginated requests to the API endpoint. This method
        aggregates the list of screens returned by paginated API calls until all pages are
        retrieved.

        :raises Exception: if there is an issue with the API call or response parsing
        :returns: A list of `Screen` objects representing all retrieved screens
        :rtype: list
        """
        _l = []
        start_at = 0
        max_results = 50
        is_last = False
        while not is_last:
            resp = self.client.get(
                f"/rest/api/3/screens?startAt={start_at}&maxResults={max_results}"
            )
            is_last = resp.json().get("isLast")
            start_at += max_results
            for val in resp.json().get("values", []):
                _l.append(Screen(val, self.client))
        return _l

    def delete_screen(self, screen: Screen):
        """
        Deletes a screen by its unique identifier.

        This function sends a DELETE request to the appropriate endpoint to remove the given
        Jira screen. If the operation fails, the method throws an HTTPError after raising
        the status for the response. This method ensures proper error handling for failed
        delete operations.

        :param screen: The Screen object to be deleted.
                       It must include a valid `id` attribute.
        :type screen: Screen
        :return: None
        """
        resp = self.client.delete(f"/rest/api/3/screens/{screen.id}")
        resp.raise_for_status()
