import logging
import re

from jirakit.fields.text_area import TextAreaContent


class Issue:
    """
    Represents an issue with associated metadata and operations.

    This class is designed to encapsulate issue-related data and provide mechanisms
    for accessing and formatting the associated details. It supports operations such
    as retrieving field values, formatting nested data structures, and accessing
    key issue properties like summary, assignee, status, and more.

    :ivar detail: The dictionary containing the issue details, such as fields and metadata.
    :type detail: dict
    :ivar client: Reference to the client object associated with the issue.
    :type client: Any
    :ivar issue_type: The type of the issue, e.g., "bug" or "task".
    :type issue_type: str
    :ivar get_field: A callable function that retrieves field configuration for
        a given issue type and field name.
    :type get_field: Callable[[str, str], dict]
    """

    def __init__(self, detail, client, issue_type, get_field):
        """
        Initializes an instance of the class with the specified details, client, issue type,
        and field retrieval function.

        This initializer sets up the necessary attributes required for the instance to operate
        effectively and handle specific tasks based on the provided argument values.

        :param detail: Additional information pertinent to the operation of the instance.
        :param client: Represents the client or entity interacting with this instance.
        :param issue_type: Specifies the type of issue this instance is designed to manage or resolve.
        :param get_field: A callable used to retrieve specific fields or data pertaining to
                          the instance's usage context.
        """
        self.detail = detail
        self.client = client
        self.issue_type = issue_type
        self.get_field = get_field

    def _format_doc(self, doc):
        """
        Formats a given document containing a list of dictionaries that describe
        different types of content, such as text, paragraphs, headings, and code.
        The function parses the content based on its type and combines it into a
        single formatted string.

        This function is intended to handle documents with a nested structure while
        taking into account various content types and formatting accordingly.

        :param doc: A list of dictionaries where each dictionary represents a piece
            of content, with its type and corresponding data. Each dictionary may
            have the keys 'type', 'text', and 'content'. The 'type' specifies the kind
            of content (e.g., 'text', 'paragraph', 'heading', 'code'), 'text' contains
            the raw string content, and 'content' is a nested list of dictionaries in
            case the content type is a paragraph.
        :type doc: list[dict[str, Union[str, list[dict]]]]

        :return: A string that combines all pieces of content from the input list,
            formatted according to their types. Content of type 'paragraph' and nested
            elements are constructed recursively. Errors encountered during formatting
            are logged, and any problematic content is skipped.
        :rtype: str

        :raises LoggingError: This function logs errors that occur when there is an
            issue processing a dictionary in the `doc` list, such as missing keys
            or improper structure.
        """
        response = ""
        if doc:
            for c in doc:
                try:
                    node_type = c.get("type")
                    if node_type == "text":
                        response += c.get("text", "")
                    elif node_type == "paragraph":
                        # An empty paragraph has no "content" key; the recursive
                        # call renders None as "" via the `if doc:` guard.
                        response += f"\n{self._format_doc(c.get('content'))}\n"
                    elif node_type == "heading":
                        response += f"\n{c.get('text', '')}\n"
                    elif node_type == "code":
                        response += f"\n{c.get('text', '')}\n"
                    elif node_type in ("bulletList", "orderedList"):
                        response += self._format_list(
                            c, ordered=node_type == "orderedList"
                        )
                    elif node_type == "listItem":
                        # Reached only if a listItem appears outside a list; render
                        # its content rather than dropping it.
                        response += self._format_doc(c.get("content"))
                    else:
                        response += f"\n{c.get('text', '')}\n"
                except Exception as e:
                    # Recoverable: skip the node but keep its siblings. Log with
                    # context at WARNING so it does not masquerade as a failure.
                    logging.getLogger("jirakit.issues").warning(
                        "Skipping malformed ADF node %r: %s", c, e
                    )
                    continue
        return response

    def _format_list(self, node, ordered):
        """
        Renders an ADF ``bulletList`` or ``orderedList`` node to plain text.

        Each ``listItem`` child is rendered on its own line with a marker: a
        dash for bullet lists, or an incrementing number for ordered lists
        (honouring the node's ``attrs.order`` start value when present). The
        item's own content is rendered recursively, so nested lists and inline
        marks are preserved rather than dropped.

        :param node: The list node, with a ``content`` list of ``listItem`` nodes.
        :type node: dict
        :param ordered: Whether to render numbered (True) or bulleted (False) markers.
        :type ordered: bool
        :return: The rendered list text, or an empty string if the node has no items.
        :rtype: str
        """
        rendered = ""
        start = node.get("attrs", {}).get("order", 1) if ordered else 1
        for index, item in enumerate(node.get("content") or [], start=start):
            marker = f"{index}. " if ordered else "- "
            text = self._format_doc(item.get("content")).strip()
            rendered += f"\n{marker}{text}"
        if rendered:
            rendered += "\n"
        return rendered

    def _format_value(self, value):
        """
        Formats the given value based on its type. It handles lists, dictionaries, and other
        types of input, applying specific formatting rules to each. For lists, it extracts
        the 'value' fields from the contained dictionaries. For dictionaries, it recursively
        handles 'doc' content types or processes truthy/falsey 'value' fields. For other types,
        it returns the value as is.

        :param value: An input value that can be of type list, dict, or another type.
        :return: The formatted value based on its type and specific formatting rules.
        """
        if isinstance(value, list):
            values = []
            for v in value:
                values.append(v["value"])
            return values
        if isinstance(value, dict):
            if value.get("type", "") == "doc":
                return self._format_doc(value.get("content")).strip()
            if "value" in value:
                v = value["value"]
                if v in ["false", "true"]:
                    return v == "true"
                else:
                    return v
        else:
            return value

    def get_value(self, field_name):
        """
        Retrieve and format the value of a specified field.

        This method fetches a field based on the provided `field_name` by determining
        its corresponding field ID through `self.issue_type`. It then retrieves the
        value of that field from the `self.detail` dictionary and formats it for
        further use or output.

        :param field_name: The name of the field whose value needs to be retrieved
            and formatted.
        :type field_name: str

        :return: The formatted value of the specified field.
        :rtype: Any
        """
        field = self.get_field(self.issue_type, field_name)
        return self._format_value(self.detail["fields"][field["fieldId"]])

    @property
    def creator(self):
        """
        Provides access to the 'creator' field in the `detail` dictionary.

        The `creator` property retrieves the value associated with the 'creator'
        key from the 'fields' sub-dictionary in the `detail` attribute. This is
        typically used to access details about the creator of an entity.

        :return: The value of the 'creator' field in the `detail` dictionary
        :rtype: Any
        """
        return self.detail["fields"]["creator"]

    @property
    def description(self):
        """
        Provides access to the 'description' property of the object. This property
        retrieves the value of the 'description' field from the 'detail' dictionary
        and formats it.

        :raises KeyError: If the 'fields' or 'description' key does not exist in the
            'detail' dictionary.
        :raises TypeError: If 'self.detail['fields']' is not subscriptable or expected
            formatting cannot be applied.
        :raises AttributeError: If '_format_value' is not callable or 'detail' is not
            correctly initialized.

        :return: Formatted value of the 'description' field.
        :rtype: Any
        """
        return self._format_value(self.detail["fields"]["description"])

    @property
    def subtasks(self):
        """
        Returns the subtasks associated with a particular detail field.

        The property retrieves the subtasks stored in the 'fields' key of the
        detail dictionary. It provides access to the data structure representing
        these subtasks, without requiring direct dictionary access.

        :return: The subtasks associated with the 'fields' dictionary in
                 the 'detail' attribute.
        :rtype: Any
        """
        return self.detail["fields"]["subtasks"]

    @property
    def reporter(self):
        """
        Retrieves the 'reporter' information from the 'fields' within the 'detail' dictionary.

        The property serves as a convenient way to access the 'reporter' data associated
        with the instance without directly interacting with the underlying data structure.

        :return: Returns the value of the 'reporter' field from the 'detail' dictionary.
        :rtype: Any
        """
        return self.detail["fields"]["reporter"]

    def apply_transition(self, transition_name):
        """
        Applies a workflow transition to the issue.

        This method retrieves all available transitions for the issue, finds the
        transition with the specified name, and applies it. The transition moves
        the issue from its current status to a new status as defined by the
        workflow.

        :param transition_name: The name of the transition to apply (e.g., "Start
            Progress", "Resolve", "Close").
        :type transition_name: str
        :raises Exception: If no transition with the specified name exists for the
            current issue status.
        :raises HTTPError: If the API request fails.
        :return: None
        """
        transition_id = None
        response = self.client.get(f"/rest/api/3/issue/{self.key}/transitions")
        response.raise_for_status()
        transitions = response.json()["transitions"]
        for transition in transitions:
            if transition["name"] == transition_name:
                transition_id = transition["id"]

        if transition_id is None:
            raise Exception(f'No transition named "{transition_name}"')

        payload = {"transition": {"id": transition_id}}
        response = self.client.post(
            f"/rest/api/3/issue/{self.key}/transitions", data=payload
        )
        response.raise_for_status()

    @property
    def summary(self):
        """
        Retrieve the summary information from the detail dictionary.

        This property allows access to the 'summary' key within the nested
        'fields' dictionary of the `detail` attribute. It provides a convenient
        way to fetch summary-related information stored in the object's
        details.

        :return: The value of the 'summary' key from the 'fields' dictionary
            contained within the `detail` attribute.
        :rtype: str
        """
        return self.detail["fields"]["summary"]

    @property
    def assignee(self):
        """
        Provides a property to access the assignee information from the 'detail'
        dictionary. The 'assignee' represents the individual assigned to a task or
        ticket within the 'fields' subdictionary of the 'detail' attribute.

        :raises KeyError: If the 'assignee' key or the 'fields' key is not present
            in the 'detail' dictionary.

        :return: Returns the value associated with the 'assignee' key in the
            'fields' subdictionary of the 'detail' attribute.
        """
        return self.detail["fields"]["assignee"]

    @property
    def status(self):
        """
        Retrieves the status property from the detail dictionary.

        This property fetches the value associated with the 'status' key nested
        inside the 'fields' dictionary of the detail attribute. It provides a
        read-only interface to access this specific piece of data.

        :return: The name associated with the 'status' key in the detail attribute.
        :rtype: str
        """
        return self.detail["fields"]["status"]["name"]

    @property
    def key(self):
        """
        Provides access to the 'key' attribute of the 'detail' dictionary within the
        object in a read-only manner. This ensures encapsulation of 'key' while
        allowing external entities to retrieve its value.

        :return: The value associated with the 'key' in the 'detail' dictionary
        :rtype: Any
        """
        return self.detail["key"]

    @property
    def id(self):
        """
        Represents a property to retrieve the 'id' from the `detail` attribute of the class.

        This property provides a convenient access to the 'id' value contained within the
        `detail` dictionary attribute. The 'id' key is expected to exist in the `detail`
        dictionary for this property to function correctly.

        :raises KeyError: If the 'id' key is not present in the `detail` dictionary.
        :raises TypeError: If the `detail` attribute is not a dictionary or is improperly
            formatted.

        :rtype: Any
        :return: The value associated with the 'id' key in the `detail` dictionary.
        """
        return self.detail["id"]


class Issues:
    """
    Represents a collection of issue management operations within a given project.

    This class provides the capability to interact with issue-related endpoints
    of a project, enabling manipulation and retrieval of issue data such as
    issues' metadata, allowed field values, text formatting, and issue creation.
    It facilitates integration with Jira's REST API for managing issues and provides
    support for structured data formatting.

    :ivar project: The project related to issue management.
    :type project: Project
    :ivar client: The client used to interact with the Jira REST API.
    :type client: Client
    :ivar issue_types: Cached metadata of issue types retrievable from the API.
    :type issue_types: list
    :ivar issue_type_field_metadata: Metadata schema and allowed fields for different issue types.
    :type issue_type_field_metadata: dict
    """

    def __init__(self, project, client):
        """
        Represents a class responsible for interacting with a specific project and client,
        while retrieving metadata for issue types and related field configurations.

        :param project: The project associated with the instance.
        :type project: Any
        :param client: The client used to interact with external systems.
        :type client: Any
        """
        self.project = project
        self.client = client
        self.issue_types = self._get_create_meta()
        self.issue_type_field_metadata = self._get_create_meta_field_metadata()

    @staticmethod
    def strip_html_and_format(text):
        """
        Processes a string containing HTML tags, replacing specific HTML elements with
        newline characters and removing all remaining HTML tags.

        :param text: The HTML formatted string to be processed.
        :type text: str

        :return: A cleaned and formatted string with specific HTML tags replaced by
                 newline characters and all other HTML tags removed.
        :rtype: str
        """
        # Replace paragraph and <br> tags with a newline
        text = re.sub(r"<p.*?>", "\n", text)  # Open <p> tags replaced with \n
        text = text.replace("</p>", "\n")  # Closing </p> tags replaced with \n
        text = text.replace("<br>", "\n")  # Replace <br> with \n
        text = text.replace("<br />", "\n")  # Replace self-closed <br /> with \n

        # Remove all remaining HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        return text.strip()

    def _get_create_meta(self):
        """
        Fetches metadata for issue creation specific to the project's issue types.

        This method makes a GET request to the Jira REST API to retrieve metadata
        (details and information) for issue creation related to the issue types
        available in the specified project. It ensures the response is successful
        and extracts relevant data regarding issue types from the JSON response.

        :raises requests.exceptions.HTTPError: If the API request fails or returns
            an HTTP error.

        :return: A list containing details of the issue types associated with the
            project.
        :rtype: list
        """
        # Use project key instead of ID for better compatibility across Jira instances
        project_identifier = (
            self.project.key
            if hasattr(self.project, "key") and self.project.key
            else self.project.id
        )
        resp = self.client.get(
            path=f"/rest/api/3/issue/createmeta/{project_identifier}/issuetypes"
        )
        resp.raise_for_status()
        return resp.json()["issueTypes"]

    def _get_create_meta_field_metadata(self):
        """
        Fetches and returns metadata for creating fields for all configured issue types
        in the specified project by calling the Jira API. Each issue type's metadata
        is stored in a dictionary with the issue type ID as the key.

        :raises HTTPError: If the API request fails for any particular issue type.

        :return: A dictionary where keys are the issue type IDs and values are the
            corresponding field metadata for issue creation.
        :rtype: dict
        """
        meta = {}
        # Use project key instead of ID for better compatibility across Jira instances
        project_identifier = (
            self.project.key
            if hasattr(self.project, "key") and self.project.key
            else self.project.id
        )
        for issue_type in self.issue_types:
            resp = self.client.get(
                path=f"/rest/api/3/issue/createmeta/{project_identifier}/issuetypes/{issue_type['id']}?maxResults=200"
            )
            resp.raise_for_status()
            meta[issue_type["id"]] = resp.json()["fields"]
        return meta

    def get_allowed_value_id(self, allowed_values, my_value):
        """
        Retrieve the ID of an allowed value from a list of allowed values, based on a
        given input value. If the input value matches the 'value' field of an item in
        the allowed values list, the corresponding 'id' field is returned. The input
        value can also match boolean-like strings ('YES' or 'NO') mapped to 'true' or
        'false'.

        :param allowed_values: A list of dictionaries, each containing a 'value' and
            an 'id'.
        :param my_value: The input value to search for in the allowed values list.
        :return: The 'id' of the matching allowed value, or None if no match is found.

        """
        for allowed_value in allowed_values:
            if allowed_value["value"] == my_value:
                return allowed_value["id"]
            if str(my_value).upper() == "YES" and allowed_value["value"] == "true":
                return allowed_value["id"]
            if str(my_value).upper() == "NO" and allowed_value["value"] == "false":
                return allowed_value["id"]
        return None

    def format_textarea_resp(self, value):
        """
        Formats a given string into a structured response dictionary by processing
        the input with HTML stripping and formatting the text into paragraphs. This
        method prepares the text for use in environments that require specific
        document structures and formatting.

        :param value: The input string to be processed and formatted.
        :type value: str

        :return: A dictionary containing the processed text structured into
            paragraphs with a specific document format. Each line of the input string
            is transformed into a content element.
        :rtype: dict
        """
        value = self.strip_html_and_format(value)
        resp = {"content": [], "type": "doc", "version": 1}
        for val in value.split("\n"):
            resp["content"].append(
                {"content": [{"text": val, "type": "text"}], "type": "paragraph"}
            )

        return resp

    def format_field_data(self, issue_type, field_name, value):
        """
        Formats field data based on issue type, field name, and value, ensuring the data conforms to the
        expected schema type for the specific field. Supports formatting for string, array, and option value
        types, with special handling of allowed values based on the field schema.

        :param issue_type: The type of the issue for which the field data is being formatted
        :type issue_type: str
        :param field_name: The name of the field to access and format
        :type field_name: str
        :param value: The value to format according to the field schema
        :type value: str | dict | list
        :return: A tuple containing the field key and the corresponding formatted value. Returns None, None
                 in case of errors or if no translation is found for the given field schema
        :rtype: tuple
        """
        field = self.get_field(issue_type, field_name)
        if field is None:
            return None, None

        field_scheme = field.get("schema").get("type")
        custom = field.get("schema").get("custom")
        if field_scheme == "string":
            if custom.endswith("textfield"):
                if isinstance(value, TextAreaContent):
                    return field.get("key"), value.content
                return field.get("key"), value
            elif custom.endswith("textarea") or custom.endswith("readonlyfield"):
                if isinstance(value, TextAreaContent):
                    return field.get("key"), value.content
                return field.get("key"), self.format_textarea_resp(value)
            else:
                return field.get("key"), value
        elif field_scheme == "number":
            return field.get("key"), value
        elif field_scheme == "datetime":
            return field.get("key"), value
        elif field_scheme == "array":
            array_values = []
            if isinstance(value, dict):
                for key in value:
                    val_id = self.get_allowed_value_id(
                        field.get("allowedValues"), value[key]
                    )
                    if val_id:
                        array_values.append({"id": val_id})
            else:
                if custom.endswith("labels"):
                    return field.get("key"), value
                else:
                    for val in value:
                        if isinstance(val, str):
                            val_id = self.get_allowed_value_id(
                                field.get("allowedValues"), val
                            )
                        elif isinstance(val, dict):
                            for key in val:
                                val_id = self.get_allowed_value_id(
                                    field.get("allowedValues"), val[key]
                                )
                        else:
                            val_id = None
                            logging.error(
                                f"When processing ARRAY values.  The instance type was not fond for {str(val)}"
                            )

                        if val_id:
                            array_values.append({"id": val_id})

            return field.get("key"), array_values
        elif field_scheme == "option":
            val_id = self.get_allowed_value_id(field.get("allowedValues"), value)
            if val_id:
                return field.get("key"), {"id": val_id}
            else:
                logging.error(f'Could not find value id for "{value}"')
                return None, None
        else:
            logging.error(f'Could not find translation for "{field_scheme}/{custom}"')
            return None, None

    def get_field(self, issue_type, field_name):
        """
        Retrieves field metadata for a specific field name and issue type.

        This method searches the cached field metadata for the specified issue type
        and returns the field configuration matching the given field name.

        :param issue_type: The issue type to search fields for. Can be either a
            dictionary with an 'id' key or an object with an id attribute.
        :type issue_type: dict or IssueType
        :param field_name: The name of the field to retrieve metadata for.
        :type field_name: str
        :return: Field metadata dictionary if found, None otherwise.
        :rtype: dict or None
        """
        if isinstance(issue_type, dict):
            issue_type_id = issue_type["id"]
        else:
            issue_type_id = issue_type.id

        for field in self.issue_type_field_metadata[issue_type_id]:
            if field["name"] == field_name:
                return field
        return None

    def get_issues_updated_last_days(self, issue_type, days):
        """
        Fetches and returns a list of issues of a specified type that were updated within the
        last specified number of days in the current project.

        This method queries the issues from the project using JIRA API. It identifies the relevant
        issue type by matching the suffix with the given `issue_type`. If no matching issue type
        is found, an error is logged and an empty list is returned. Once the relevant issue type
        is identified, it constructs a JQL query to filter issues updated within the last `days`
        days and issues a request to the JIRA API.

        :param issue_type: The name suffix of the issue type to search for.
        :type issue_type: str
        :param days: The number of days to look back for updated issues.
        :type days: int

        :return: A list of `Issue` objects that match the given constraints or an empty list if no
                 issues or matching issue type is found.
        :rtype: list[Issue]
        """
        relevant_issue_type = None
        for it in self.issue_types:
            if it["name"].endswith(issue_type):
                relevant_issue_type = it

        if relevant_issue_type is None:
            logging.error(f'Could not find issue type "{issue_type}"')
            return []

        jql = f'project="{self.project.key}" AND issuetype="{relevant_issue_type["name"]}" AND updated >= "-{days}d"'

        # Use new /search/jql endpoint (POST method as per API v3 migration)
        payload = {"jql": jql, "maxResults": 100, "fields": ["*all"]}
        resp = self.client.post(path="/rest/api/3/search/jql", data=payload)
        resp.raise_for_status()
        results = []
        for issue in resp.json()["issues"]:
            results.append(
                Issue(issue, self.client, relevant_issue_type, self.get_field)
            )
        return results

    def get_issue(self, key):
        """
        Retrieves a specific issue by its key.

        Fetches full issue details from the Jira API using the issue key and
        returns an Issue object.

        :param key: The issue key (e.g., 'PROJ-123').
        :type key: str
        :return: An Issue object representing the retrieved issue.
        :rtype: Issue
        :raises HTTPError: If the API request fails or the issue doesn't exist.
        """
        resp = self.client.get(path=f"/rest/api/3/issue/{key}")
        resp.raise_for_status()
        data = resp.json()
        return Issue(data, self.client, data["fields"]["issuetype"], self.get_field)

    def update_issue(
        self, issue_key, issue_type, summary=None, description=None, fields={}
    ):
        """
        Updates an existing Jira issue with new field values.

        This method allows updating the summary, description, and custom fields of an
        existing issue. Only provided fields will be updated; others remain unchanged.

        :param issue_key: The key of the issue to update (e.g., 'PROJ-123').
        :type issue_key: str
        :param issue_type: The issue type dictionary or object containing the id.
        :type issue_type: dict or IssueType
        :param summary: New summary text for the issue. If None, summary is not updated.
        :type summary: str or None
        :param description: New description for the issue. Can be a string or
            TextAreaContent object. If None, description is not updated.
        :type description: str or TextAreaContent or None
        :param fields: Dictionary of custom field names and their values to update.
        :type fields: dict
        :raises HTTPError: If the API request fails.
        :return: None
        """
        payload = {"fields": {}}

        if summary is not None:
            payload["fields"]["summary"] = summary

        if description is not None:
            if isinstance(description, TextAreaContent):
                payload["fields"]["description"] = description.content
            else:
                payload["fields"]["description"] = self.format_textarea_resp(
                    description
                )

        for field in fields:
            try:
                if fields[field]:
                    field_key, val = self.format_field_data(
                        issue_type, field, fields[field]
                    )
                    if field_key:
                        payload["fields"][field_key] = val
                    else:
                        logging.error(f'Could not find field key for "{field}"')
            except Exception as e:
                logging.exception(f"Field {field}: {e}")
                continue

        resp = self.client.put(path=f"/rest/api/3/issue/{issue_key}", data=payload)
        resp.raise_for_status()

    def create_issue(
        self, issue_type, summary, description="", fields={}, parent_issue: Issue = None
    ):
        """
        Creates a new issue in the Jira system with the specified details. This function sends a POST request
        to the Jira API to create the issue and populates the required fields such as project ID, issue type,
        summary, and description. Optional fields and parent issue information can also be provided.

        :param issue_type: The type of the issue being created, specified as a dictionary containing its ID.
        :param summary: A brief summary or title for the issue.
        :param description: A detailed description of the issue. Defaults to an empty string if not provided.
        :param fields: Additional custom fields to include while creating the issue. Defaults to an empty dictionary.
        :param parent_issue: An optional parent issue object to establish parent-child relationship while creating
            a sub-task issue. Defaults to None.
        :return: An Issue object representing the created Jira issue.
        :rtype: Issue
        """
        if isinstance(issue_type, dict):
            issue_type_id = issue_type["id"]
        else:
            issue_type_id = issue_type.id

        payload = {
            "fields": {
                "project": {"id": self.project.id},
                "summary": summary,
                "issuetype": {"id": issue_type_id},
            }
        }

        if isinstance(description, TextAreaContent):
            payload["fields"]["description"] = description.content
        else:
            payload["fields"]["description"] = self.format_textarea_resp(description)

        if parent_issue:
            if isinstance(parent_issue, str):
                payload["fields"]["parent"] = {"key": parent_issue}
            else:
                payload["fields"]["parent"] = {"key": parent_issue.key}

        for field in fields:
            try:
                if fields[field]:
                    field_key, val = self.format_field_data(
                        issue_type, field, fields[field]
                    )
                    if field_key:
                        payload["fields"][field_key] = val
                    else:
                        logging.error(f'Could not find field key for "{field}"')
            except Exception as e:
                logging.exception(f"Field {field}: {e}")
                continue

        resp = self.client.post(path="/rest/api/3/issue", data=payload)
        resp.raise_for_status()
        resp = self.client.get(path=f"/rest/api/3/issue/{resp.json()['key']}")
        resp.raise_for_status()
        return Issue(resp.json(), self.client, issue_type, self.get_field)
