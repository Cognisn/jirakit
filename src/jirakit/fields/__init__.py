
class Field:
    """
    Representation of a field object with its details and client interaction.

    This class encapsulates the attributes and behaviors of a field, including
    its metadata, schema, and associated operations. It provides methods to
    interact with the field's contexts and options within a specified client.

    :ivar field_detail: Dictionary holding the detailed properties of the field.
    :type field_detail: dict
    :ivar client: Client instance used for interacting with field-related APIs.
    :type client: object
    """
    def __init__(self, field_detail, client):
        """
        Initializes an instance of a class with necessary configuration and dependencies.

        This constructor is created to accept configuration details and a client instance, which can
        be used for further operations within the class. The `field_detail` parameter is provided
        to specify additional settings or configurations needed for the functionality, while the
        `client` parameter is the external dependency injected into this class.

        :param field_detail: Configuration or detailed setting required by the class.
        :param client: External dependency or client instance used within the class.
        """
        self.field_detail = field_detail
        self.client = client

    def __str__(self):
        """
        Provides a string representation of the object including its name and id.

        The string representation consists of the object's `name` followed by its
        `id`, with a separator `/` between them. This representation can be useful
        for logging, debugging, or displaying information about the object in a
        readable format.

        :returns: A string that combines the object's `name` and `id` with a `/` separator.
        :rtype: str
        """
        return f"{self.name} / {self.id}"

    @property
    def id(self):
        """
        Retrieves the 'id' field from the `field_detail` dictionary.

        This property is used to access the value associated with the 'id' key in
        the `field_detail` attribute. It provides a simple and intuitive way to
        fetch this specific piece of information encapsulated within the
        `field_detail` dictionary.

        :raises KeyError: If the 'id' key is not present in the `field_detail`
            dictionary.

        :return: The value associated with the 'id' key in the `field_detail`
            dictionary.
        :rtype: Any
        """
        return self.field_detail.get('id')

    @property
    def key(self):
        """
        Retrieves the 'key' value from the 'field_detail' dictionary.

        The property fetches the value associated with the 'key' in the
        'field_detail' attribute. If the key is missing, it returns None.

        :return: Value retrieved from the 'key' in the 'field_detail' dictionary, or None if not present.
        :rtype: Any
        """
        return self.field_detail.get('key')

    @property
    def name(self):
        """
        Retrieves the 'name' attribute value from field_detail.

        The `name` property returns the value associated with
        the key 'name' in the `field_detail` dictionary, which
        is a detail container representing an entity or object.

        :return: The value of the 'name' key from field_detail.
        :rtype: Any
        """
        return self.field_detail.get('name')

    @property
    def description(self):
        """
        Provides a property method to retrieve the value of 'description' from
        the instance's 'field_detail' dictionary attribute. This is commonly
        used to access and return the description information related to an
        object in a structured manner.

        :return: The value associated with the key 'description' in the
            'field_detail' dictionary.
        :rtype: str or None
        """
        return self.field_detail.get('description')

    @property
    def navigable(self):
        """
        Provides a property to determine whether the object is navigable based on
        its internal field detail configuration.

        :return: The value associated with the 'navigable' key in the field_detail
            dictionary. The type corresponds to the type of the returned value from
            the dictionary's 'get' method.
        """
        return self.field_detail.get('navigable')

    @property
    def orderable(self):
        """
        Indicates if the current field can be ordered or not based on the field detail.

        This property accesses the `field_detail` attribute, retrieves the value
        associated with the key `orderable`, and returns it, indicating whether
        or not the field is configured to support ordering.

        :raises KeyError: If the key `orderable` does not exist in `field_detail`.

        :return: A boolean indicating whether the field is orderable or not.
        :rtype: bool or None
        """
        return self.field_detail.get('orderable')

    @property
    def schema(self):
        """
        Provides an interface to access the schema property derived from the
        'field_detail' attribute. This property fetches and returns the 'schema'
        key's value if available within the 'field_detail' dictionary.

        :return: Returns the value associated with the 'schema' key in the
            'field_detail' dictionary.
        :rtype: Any
        """
        return self.field_detail.get('schema')

    @property
    def searchable(self):
        """
        Indicates whether the field is searchable based on its metadata.

        This property retrieves the value of the 'searchable' key from the
        field's metadata. The 'searchable' attribute determines if the field
        can be used as a searchable element.

        :return: A value indicating if the field is searchable.
        :rtype: bool or None
        """
        return self.field_detail.get('searchable')

    @property
    def untranslated_name(self):
        """
        Retrieves the untranslated name from the field details.

        This property accesses the `field_detail` attribute of the object and extracts
        the value associated with the key `untranslatedName`. It provides a way to
        retrieve the untranslated name of a specific field based on the provided
        details.

        :return: The untranslated name from the field detail dictionary,
            or None if the key `untranslatedName` does not exist.
        :rtype: Any
        """
        return self.field_detail.get('untranslatedName')

    @property
    def is_locked(self):
        """
        Checks if the field is locked.

        This property evaluates whether the field detail contains the `isLocked` key
        and returns its associated value. It is useful for determining the lock status
        based on the given field detail.

        :return: A boolean value indicating whether the field is locked or not.
        :rtype: bool
        """
        return 'isLocked' in self.field_detail and self.field_detail['isLocked']

    @property
    def is_custom(self):
        """
        Indicates whether the schema contains a custom attribute.

        This property evaluates if the `schema` attribute contains the word 'custom'.
        It is a dynamic property that checks the contents of the `schema` attribute
        and returns a boolean based on whether the string 'custom' is found within it.

        :rtype: bool
        :return: Returns True if 'custom' is found in the `schema` attribute, otherwise False.
        """
        return self.schema and 'custom' in self.schema

    def fetch_field_contexts(self):
        """
        Fetches field contexts related to the current field based on its ID.

        This method interacts with the Jira API to retrieve contexts related to
        a specific field. It sends an HTTP GET request to the API endpoint,
        fetches the response, and extracts the necessary information from the
        JSON response.

        :raises requests.exceptions.HTTPError: If the HTTP request fails or
            returns an unsuccessful status code.

        :return: A list of field context information associated with the field.
        :rtype: list
        """
        resp = self.client.get(f"/rest/api/3/field/{self.id}/context")
        resp.raise_for_status()
        return resp.json().get('values')

    def add_option(self, context, option, parent_option_id=None):
        """
        Adds an option to a specified context for a custom field in Jira. This method is responsible for
        posting the provided option details to the Jira REST API for the associated field and context. If
        a parent option ID is provided, the option will be added as a child of the specified parent.

        :param context: The context where the option is to be added. This is expected to be an object
                        containing at least an "id" key-value pair.
        :type context: dict
        :param option: The option details to be added. This parameter should include the necessary keys
                       and values as required by the Jira REST API.
        :type option: dict
        :param parent_option_id: The ID of the parent option to which the new option is to be added.
                                 If not provided, defaults to None.
        :type parent_option_id: str or None
        :return: The JSON response from the Jira REST API after successfully adding the option.
        :rtype: dict
        :raises HTTPError: If the HTTP request to Jira fails.
        """
        if 'sub_items' in option:
            option.pop('sub_items')

        payload = {
            "options": [
                option
            ]
        }
        if parent_option_id:
            payload['options'][0]["optionId"] = parent_option_id

        resp = self.client.post(f"/rest/api/3/field/{self.id}/context/{context.get("id")}/option", data=payload)
        resp.raise_for_status()
        return resp.json()

    def add_options(self, context, options):
        """
        Adds a list of options to a given context. Each option may have sub-items,
        which will also be added recursively. The method ensures that each main
        option and its respective sub-items are processed and added properly.
        The relationship between a parent option and its sub-items is maintained
        through the parent_id parameter.

        :param context: The target context where the options will be added.
        :type context: dict
        :param options: A list of option objects. Each option may have sub-items
            represented as nested dictionaries within the "sub_items" key.
        :type options: list
        :return: None
        """
        for option in options:
            sub_items = option.get('sub_items')
            option_resp = self.add_option(context, option)
            if sub_items:
                parent_id = option_resp['options'][0]['id']
                for sub_item in sub_items:
                    self.add_option(context, sub_item, parent_id)

class Fields:
    """
    Handles operations related to field management in a Jira system.

    This class provides methods to interact with Jira's custom fields, allowing for
    fetching, creation, and deletion of fields. It also offers functionality to define
    field types and manages field options.

    :ivar SEARCHER_TYPE_MAPPING: Maps field types to their corresponding searcher key
        within Jira.
    :type SEARCHER_TYPE_MAPPING: dict
    """
    SEARCHER_TYPE_MAPPING = {
        "cascadingselect": "cascadingselectsearcher",
        "datepicker": "daterange",
        "datetime": "datetimerange",
        "float": "exactnumber",
        "grouppicker": "grouppickersearcher",
        "importid": "exactnumber",
        "labels": "labelsearcher",
        "multicheckboxes": "multiselectsearcher",
        "multigrouppicker": "multiselectsearcher",
        "multiselect": "multiselectsearcher",
        "multiuserpicker": "userpickergroupsearcher",
        "multiversion": "versionsearcher",
        "project": "projectsearcher",
        "radiobuttons": "multiselectsearcher",
        "readonlyfield": "textsearcher",
        "select": "multiselectsearcher",
        "textarea": "textsearcher",
        "textfield": "textsearcher",
        "url": "exacttextsearcher",
        "userpicker": "userpickergroupsearcher",
        "version": "versionsearcher",
    }

    def __init__(self, client):
        """
        Represents a class that initializes with a given client, storing it as an
        instance attribute. The client can then be used for further interactions
        within the class methods to interact with the functionality provided by the
        client.

        :param client: The client to be associated with the instance for future use
        :type client: depends on input type provided
        """
        self.client = client

    def fetch_field_contexts(self, field_id):
        """
        Fetches the contexts associated with a specific field.

        This method sends a GET request to the Jira REST API endpoint for retrieving
        the contexts associated with the given field. It fetches the details of field
        contexts and returns the list of values from the API's response.

        :param field_id: The unique identifier of the field for which contexts are
            being fetched.
        :type field_id: str
        :return: A list containing the contexts associated with the specified field.
        :rtype: list
        :raises HTTPError: If the API request fails or returns an error response.
        """
        response = self.client.get(f"/rest/api/3/field/{field_id}/context")
        response.raise_for_status()
        return response.json().get("values", [])


    @staticmethod
    def get_searcher_type(field_type):
        """
        Retrieve the searcher type based on the specified field type.

        This method maps a given field type to its corresponding searcher type
        by using a predefined mapping. If the field type is not found in the
        mapping, the method will return None.

        :param field_type: The field type for which the searcher type is required.
        :return: The corresponding searcher type if found in the mapping; otherwise, None.
        """
        return Fields.SEARCHER_TYPE_MAPPING.get(field_type)

    def create_field(self, field_type, field_name, description, options = None) -> Field:
        """
        Creates a custom field in Jira with specified attributes and optional options.

        The method constructs a payload for the Jira REST API to create a custom field. It then
        sends a POST request to create the field. If the creation fails, an exception is raised.
        If options are provided, it fetches the field's context and adds the specified options to
        the field.

        :param field_type: The type of the custom field to be created.
        :type field_type: str
        :param field_name: The name of the custom field.
        :type field_name: str
        :param description: The description for the custom field.
        :type description: str
        :param options: A list of options to add to the custom field. Optional.
        :type options: list or None
        :return: An instance of the Field class representing the newly created custom field.
        :rtype: Field
        :raises Exception: If the custom field creation fails (status code is not 201).
        """
        payload = {
            "name": field_name,
            "description": description,
            "type": f"com.atlassian.jira.plugin.system.customfieldtypes:{field_type}",
            "searcherKey": f"com.atlassian.jira.plugin.system.customfieldtypes:{self.get_searcher_type(field_type)}"
        }

        response = self.client.post("/rest/api/3/field", data=payload)
        if response.status_code != 201:
            raise Exception(f"Failed to create custom field: {response.text}, field type: {field_type}, field name: {field_name}")

        field = Field(response.json(), self.client)
        if options:
            context = field.fetch_field_contexts()[0]
            field.add_options(context, options)

        return field

    def create_datepicker_field(self, field_name, description):
        """
        Creates a datepicker field with the specified name and description. The method utilizes the
        `create_field` function to generate a field of type "datepicker".

        :param field_name: The name of the datepicker field to be created.
        :type field_name: str
        :param description: A brief description or label for the datepicker field.
        :type description: str
        :return: Returns the created datepicker field object.
        :rtype: Field
        """
        return self.create_field("datepicker", field_name, description)

    def create_datetime_field(self, field_name, description):
        """
        Creates a new datetime field with the specified name and description.

        This method is designed to facilitate the creation of a field with a
        "datetime" type, using the provided field name and its description.

        :param field_name: The name to assign to the datetime field.
        :type field_name: str
        :param description: A brief description of the datetime field's purpose.
        :type description: str
        :return: The newly created datetime field object.
        :rtype: Any
        """
        return self.create_field("datetime", field_name, description)

    def create_float_field(self, field_name, description):
        """
        Creates a field with a specified type of "float" in the system. This
        method abstracts the field creation process, focusing on defining
        a float type for the field while assigning it the specified name and
        description. It delegates the actual field creation to another method,
        ensuring the encapsulation of logic.

        :param field_name: The name of the field to be created.
        :type field_name: str
        :param description: A description of the purpose or usage of the field.
        :type description: str
        :return: The created field as an object or representation suitable for
                 the system.
        :rtype: Any
        """
        return self.create_field("float", field_name, description)

    def create_grouppicker_field(self, field_name, description):
        """
        Creates and returns a new field of type 'grouppicker'.

        This method is used to create a custom field for selecting a group in a
        predefined set. It calls the `create_field` method with the appropriate
        type to generate a 'grouppicker' field.

        :param field_name: The name of the field to be created.
        :type field_name: str
        :param description: A text description of the field being created,
            explaining its purpose or usage.
        :type description: str

        :return: The created 'grouppicker' field.
        :rtype: Any
        """
        return self.create_field("grouppicker", field_name, description)

    def create_multiuserpicker_field(self, field_name, description):
        """
        Creates a new 'multiuserpicker' field in the system.

        This method is used to create a field of type 'multiuserpicker' with a given
        name and description. It internally calls another method to handle the
        creation process for such fields.

        :param field_name: The name of the field to be created.
        :type field_name: str
        :param description: A brief description of the field's purpose or context.
        :type description: str
        :return: The result of the internal field creation process, typically
                 representing the created field object or confirmation.
        :rtype: Any
        """
        return self.create_field("multiuserpicker", field_name, description)

    def create_multigrouppicker_field(self, field_name, description):
        """
        Creates a field of type "multigrouppicker" with the given field name and description.

        This method leverages the `create_field` method to generate a field
        specifically designed for scenarios requiring multi-group picking functionality.

        :param field_name: The name of the field to be created.
        :param description: A brief description of the field's purpose or usage.
        :return: A newly created "multigrouppicker" field.
        """
        return self.create_field("multigrouppicker", field_name, description)

    def create_labels_field(self, field_name, description):
        """
        Creates a field of type "labels".

        This method generates and returns a field of type "labels" by utilizing the
        `create_field` method. It requires a specified `field_name` and a
        corresponding `description` to properly define the field. The returned field
        is customized per the inputs passed to this function.

        :param field_name: The unique identifier for the labels field.
        :param description: A textual description providing details about this labels
            field.
        :return: An instance of the created labels field.
        """
        return self.create_field("labels", field_name, description)

    def create_textarea_field(self, field_name, description):
        """
        Creates a textarea field using the specified field name and description.

        This function generates a field of type 'textarea' with a given field name
        and description. It utilizes the `create_field` method to create the field
        internally.

        :param field_name: Name of the field to be created.
        :type field_name: str
        :param description: Description associated with the field.
        :type description: str
        :return: The new textarea field created.
        :rtype: Any
        """
        return self.create_field("textarea", field_name, description)

    def create_textfield_field(self, field_name, description):
        """
        Creates a textfield type field with a specified name and description.

        This method generates a field of type "textfield" with the provided field name
        and description, utilizing the `create_field` method.

        :param field_name: The name of the field to be created.
        :type field_name: str
        :param description: A brief description of the textfield field to provide
            additional context.
        :type description: str
        :return: Returns the result of the `create_field` method which creates a
            "textfield" field with the specified parameters.
        :rtype: Any
        """
        return self.create_field("textfield", field_name, description)

    def create_url_field(self, field_name, description):
        """
        Creates a URL field using the given field name and description.

        :param field_name: Name of the field to be created.
        :type field_name: str
        :param description: Description of the field to be created.
        :type description: str
        :return: A field object of type URL.
        :rtype: Any
        """
        return self.create_field("url", field_name, description)

    def create_userpicker_field(self, field_name, description):
        """
        Creates a user picker field in a system or application.

        This method is used to create a field type specifically designed for selecting
        users. It abstracts the process of field creation by specifying the type as
        "userpicker". The `field_name` and `description` provide the necessary details
        for defining and identifying the field.

        :param field_name: The name of the field to be created.
        :type field_name: str
        :param description: A brief description of the field, used for context or
            field metadata.
        :type description: str
        :return: The created user picker field object.
        :rtype: Any
        """
        return self.create_field("userpicker", field_name, description)

    def _create_multi_field(self, field_type, field_name, description):
        """
        Creates a multi-field object by delegating to the `create_field` method with the
        specified parameters. The multi-field allows for defining multiple subfields
        under a single base field, enabling the creation of complex, structured data
        representations.

        :param field_type: Defines the type of the field to be created.
        :type field_type: str
        :param field_name: Name of the field to be created.
        :type field_name: str
        :param description: Description or purpose of the field being created.
        :type description: str
        :return: The created multi-field object.
        :rtype: Any
        """
        return self.create_field(field_type, field_name, description)

    def create_selects_field(self, field_name, description, options):
        """
        Creates a multi-select field for a form with the specified options.

        This function generates a form field of type "select" that allows selecting
        one or more options from a predefined list. It leverages the private
        method `_create_multi_field` to construct the field based on the input
        parameters.

        :param field_name: The name assigned to the field.
        :type field_name: str
        :param description: Detailed information or label for the field.
        :type description: str
        :param options: A list of selectable options for the field.
        :type options: list
        :return: Returns the created multi-select field representation.
        :rtype: Any
        """
        return self._create_multi_field("select", field_name, description)

    def create_radiobuttons_field(self, field_name, description, options):
        """
        Creates a multi-field form element of type "radiobuttons".

        This method is used to dynamically generate radio button groups for forms.
        It assigns the provided field name and description, and processes the options
        for the radio button group. The method also utilizes a helper function to handle
        the creation of the field.

        :param field_name: Unique identifier for the radio button field.
        :type field_name: str
        :param description: A short text describing the purpose of the radio button group.
        :type description: str
        :param options: A collection of choices for the radio buttons. Each option
            corresponds to a possible selection in the group.
        :type options: list[str]
        :return: A dictionary representing the generated radio button field.
        :rtype: dict
        """
        return self._create_multi_field("radiobuttons", field_name, description)

    def create_multiselect_field(self, field_name, description, options):
        """
        Creates a multi-select field by calling an internal method to construct it.

        This function is used to create a multi-select field configuration in the
        form builder. The generated field allows users to select multiple values
        from a predefined list of options. The `field_name` acts as a unique
        identifier for the field, and the `description` is displayed to help users
        understand the purpose of the field. The `options` parameter represents the
        list of possible values available for selection.

        :param field_name: The unique identifier for the multi-select field being created.
        :type field_name: str

        :param description: A brief explanation of what the multi-select field is intended
            to represent.
        :type description: str

        :param options: A predefined list of choices that users can select from. Each
            selection option must be unique and meaningful.
        :type options: list

        :return: The configuration object for the multi-select field.
        :rtype: dict
        """
        return self._create_multi_field("multiselect", field_name, description)

    def create_multi_checkboxes_field(self, field_name, description, options):
        """
        Creates a multi-checkboxes field with the specified configurations.

        This method is used to generate a "multicheckboxes" type of multi-field by
        taking the necessary parameters such as the field name, its description,
        and the available options. The field creation relies on an internal
        method `_create_multi_field`.

        :param field_name:
            The name of the field being created.
        :param description:
            A textual description intended for the field, providing necessary
            context or information about its purpose.
        :param options:
            The collection of possible values the checkboxes can represent.
        :return:
            Returns the result of the `_create_multi_field` method configured with
            the type "multicheckboxes" and input parameters.
        """
        return self._create_multi_field("multicheckboxes", field_name, description)

    def create_cascading_select_field(self, field_name, description, options):
        """
        Creates a cascading select custom field.

        This method defines a custom field of the 'cascadingselect' type, allowing nested
        selection options to be presented to users. Typically used for scenarios requiring
        hierarchical data entry, such as category and subcategory pairings.

        :param field_name: Name of the custom field to be created.
        :type field_name: str
        :param description: Description of the custom field explaining its purpose.
        :type description: str
        :param options: A hierarchical list of possible options for the cascading select
            field. Each top-level option contains its subordinate selections.
        :type options: list
        :return: Returns the created field object.
        :rtype: dict
        """
        return self.create_field('cascadingselect', field_name, description)

    def delete_field(self, field: Field):
        """
        Deletes a custom field by its ID. This method interacts with the API to delete
        the specified field. Ensure that the provided field exists and has the necessary
        permissions before calling this method. The API operation requires authentication
        and proper user privileges.

        :param field: The field object that needs to be deleted. This should contain the
            ID of the field to be deleted.
        :type field: Field

        :return: None
        """
        resp = self.client.delete(f"/rest/api/3/field/{field.id}")
        resp.raise_for_status()

    def get_custom_field(self, name, description, field_type):
        """
        Retrieves a custom field based on its name, description, and field type.

        This function iterates through the available custom fields and matches them
        against the provided name, description, and field type parameters. If a field
        with the specified attributes is found, it is returned. If no such field exists,
        the function returns None.

        :param name: A string representing the name of the custom field to retrieve.
        :param description: A string describing the custom field to retrieve.
        :param field_type: A string indicating the field type, checked against the field's schema.
        :return: The matched field object, or None if no match is found.
        """
        for field in self.get_custom_fields():
            if field.name == name and field.description == description and field.schema['custom'].endswith(field_type):
                return field
        return None

    def get_non_custom_fields(self):
        """
        Retrieves all non-custom fields from a collection of fields.

        This method iterates through all the fields obtained from the `get_all`
        method, identifies those fields that are not marked as custom, and appends
        them to a list. The list of non-custom fields is then returned to the caller.

        :return: A list containing all the fields that are not custom.
        :rtype: list
        """
        non_custom_fields = []
        for field in self.get_all():
            if not field.is_custom:
                non_custom_fields.append(field)
        return non_custom_fields

    def get_all(self):
        """
        Fetches all available fields from an API endpoint in a paginated manner. This method
        utilizes pagination by sending repeated requests to the API until all records are
        retrieved. Each page of results is processed and appended to the final list.

        :raises requests.exceptions.HTTPError: If the HTTP request returns an unsuccessful
            status code, it raises an error.
        :raises KeyError: If the expected keys ('isLast', 'values') are missing in the API
            response.

        :return: A list of `Field` objects constructed from the API response.
        :rtype: list[Field]
        """
        start_at = 0
        max_results = 50
        _l = []
        is_last = False
        while not is_last:
            resp = self.client.get(f"/rest/api/3/field/search?startAt={start_at}&maxResults={max_results}&expand=isLocked")
            resp.raise_for_status()
            results = resp.json()
            is_last = results['isLast']
            start_at += max_results
            for value in results['values']:
                _l.append(Field(value, self.client))

        return _l

    def get_custom_fields(self):
        """
        Retrieves all fields marked as custom fields from the collection of fields.

        This method iterates through all available fields using the `get_all` method
        and selects only those that are flagged as custom fields. The resulting list
        contains all such fields which can then be accessed or manipulated according
        to further requirements.

        :return: A list containing all custom fields.
        :rtype: list
        """
        _l = []
        for field in self.get_all():
            if field.is_custom:
                _l.append(field)
        return _l
