"""
Text area content handling for Jira fields.

This module provides functionality to convert markdown text to Atlassian Document
Format (ADF) and manage text area content for Jira issues. It uses Node.js with
the md-to-adf package to perform the conversion.
"""

import subprocess
import json
import base64
import logging


def convert_markdown_to_adf(markdown_text):
    """
    Converts Markdown to Jira Atlassian Document Format (ADF) using Node.js.

    This function takes markdown-formatted text and converts it to ADF using the
    md-to-adf Node.js package. The conversion is performed by executing a Node.js
    script that imports the translation function and processes the markdown text.

    The function uses base64 encoding to safely pass the markdown text to Node.js,
    avoiding issues with special characters and shell escaping.

    :param markdown_text: The markdown text to convert to ADF format.
    :type markdown_text: str
    :return: A dictionary representing the ADF document structure, or None if
        conversion fails.
    :rtype: dict or None
    :raises RuntimeError: If Node.js is not available on PATH.
    """
    try:
        # Encode markdown text to base64 to safely pass to Node.js
        base64_bytes = base64.b64encode(markdown_text.encode("utf-8"))
        base64_string = base64_bytes.decode("utf-8")

        # Construct JavaScript code to translate markdown to ADF
        js = f"""import fnTranslate from 'md-to-adf';const inputMarkdown = atob("{base64_string}");const translatedADF = fnTranslate( inputMarkdown );console.log(JSON.stringify(translatedADF, null, 2));"""

        # Execute Node.js script; the environment check happens here at first
        # use rather than at import, and nothing is ever installed on the
        # caller's behalf
        try:
            result = subprocess.run(
                ["node", "-e", js], capture_output=True, text=True, check=False
            )
        except FileNotFoundError:
            raise RuntimeError(
                "Node.js is required to convert Markdown to ADF. Install Node.js "
                "and the md-to-adf package (npm install -g md-to-adf) to use "
                "Markdown conversion."
            ) from None

        if result.returncode != 0:
            logging.error(f"Error running Node.js script: {result.returncode}")
            logging.error(f"stderr: {result.stderr}")
            logging.error(f"stdout: {result.stdout}")
            return None

        # Parse the JSON output from Node.js
        adf_output = json.loads(result.stdout)
        return adf_output

    except json.JSONDecodeError:
        logging.error("Error: Failed to parse JSON output from Node.js")
        return None


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
