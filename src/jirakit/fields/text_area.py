"""
Text area content handling for Jira fields.

This module provides functionality to convert Markdown text to Atlassian Document
Format (ADF) and manage text area content for Jira issues. Conversion is performed
in pure Python by the marklassian package.
"""

import json

from marklassian import markdown_to_adf


def convert_markdown_to_adf(markdown_text):
    """
    Converts Markdown to Jira Atlassian Document Format (ADF).

    This function takes Markdown-formatted text and converts it to an ADF
    version 1 document using the marklassian package, entirely in Python.

    :param markdown_text: The Markdown text to convert to ADF format.
    :type markdown_text: str
    :return: A dictionary representing the ADF document structure.
    :rtype: dict
    """
    return markdown_to_adf(markdown_text)


class TextAreaContent:
    """
    Represents text area content for Jira fields in Atlassian Document Format (ADF).

    This class handles the conversion of text content (markdown or plain text) into
    the ADF format required by Jira. It supports both standard markdown conversion
    and JSON code block formatting.

    The class can automatically format various content types:
    - Strings: Converted from markdown to ADF
    - Lists: Formatted as markdown lists before conversion
    - JSON content: Wrapped in code blocks with JSON syntax highlighting

    :ivar original_content: The original content provided during initialisation.
    :type original_content: str or list
    :ivar content: The ADF-formatted content dictionary.
    :type content: dict

    :example:
        >>> # Create from markdown
        >>> content = TextAreaContent("# Header\\n\\nSome text")
        >>> # Create from list
        >>> content = TextAreaContent(["Item 1", "Item 2", "Item 3"])
        >>> # Create with JSON code block
        >>> content = TextAreaContent("", json_content='{"key": "value"}')
    """

    def __init__(self, content="", json_content=None):
        """
        Initialise TextAreaContent with content or JSON code block.

        :param content: The content to format. Can be a string (markdown), a list of
            strings (converted to markdown list), or any other type (converted to string).
            Defaults to empty string.
        :type content: str or list or any
        :param json_content: Optional JSON content to wrap in a code block. If provided,
            this takes precedence over the content parameter.
        :type json_content: str or None
        """
        self.original_content = content

        # Format non-string content
        if not isinstance(content, str):
            content = self.format_content(content)

        # Ensure there's always content
        if len(content) == 0:
            content = "No Content"

        # Create ADF structure
        if json_content:
            self.content = {
                "content": [
                    {
                        "type": "codeBlock",
                        "attrs": {"language": "json"},
                        "content": [{"type": "text", "text": json_content}],
                    }
                ],
                "type": "doc",
                "version": 1,
            }
        else:
            self.content = convert_markdown_to_adf(content)

    def __str__(self):
        """
        Return a JSON string representation of the ADF content.

        :return: A formatted JSON string representing the ADF content.
        :rtype: str
        """
        return json.dumps(self.content, indent=2)

    @staticmethod
    def format_markdown_list(items):
        """
        Formats a list of strings into a markdown bulleted list.

        Each item in the input list is prefixed with a dash and newline to create
        a markdown-formatted bulleted list.

        :param items: List of strings to format as markdown list items.
        :type items: list[str]
        :return: Markdown-formatted bulleted list string.
        :rtype: str

        :example:
            >>> TextAreaContent.format_markdown_list(["First", "Second", "Third"])
            '- First\\n- Second\\n- Third'
        """
        return "\n".join(f"- {item}" for item in items)

    @staticmethod
    def format_content(content):
        """
        Formats content based on its type.

        Converts various content types into formatted strings appropriate for
        markdown conversion:
        - Lists are formatted as markdown bulleted lists
        - Other types are returned as-is

        :param content: Content to format. Currently handles list types specially.
        :type content: any
        :return: Formatted content string, or None if no formatting is applicable.
        :rtype: str or None
        """
        if isinstance(content, list):
            return TextAreaContent.format_markdown_list(content)
