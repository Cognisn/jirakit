"""
Unit tests for the text area module (Markdown to ADF conversion).

Tests cover:
- convert_markdown_to_adf() producing valid ADF v1 documents in pure Python
- Conversion working without Node.js and without spawning subprocesses
- TextAreaContent formatting of strings, lists, and JSON code blocks
"""

import subprocess

from jirakit.fields.text_area import TextAreaContent, convert_markdown_to_adf


class TestConvertMarkdownToAdf:
    """Tests for the pure Python Markdown to ADF conversion."""

    def test_returns_valid_adf_document(self):
        """Conversion produces a doc/version 1 ADF document."""
        adf = convert_markdown_to_adf("# Heading\n\nBody text.")

        assert adf["type"] == "doc"
        assert adf["version"] == 1
        assert adf["content"][0]["type"] == "heading"
        assert adf["content"][0]["attrs"]["level"] == 1
        assert adf["content"][1]["type"] == "paragraph"

    def test_converts_inline_marks_and_links(self):
        """Bold, italic, code, and link marks are converted."""
        adf = convert_markdown_to_adf(
            "**bold** *italic* `code` [link](https://example.com)"
        )

        marks = {
            mark["type"]
            for node in adf["content"][0]["content"]
            for mark in node.get("marks", [])
        }
        assert {"strong", "em", "code", "link"} <= marks

    def test_converts_lists(self):
        """Bullet and ordered lists become ADF list nodes."""
        adf = convert_markdown_to_adf("- one\n- two\n\n1. first\n2. second")

        types = [node["type"] for node in adf["content"]]
        assert "bulletList" in types
        assert "orderedList" in types

    def test_converts_tables(self):
        """Markdown tables become ADF table nodes (md-to-adf could not do this)."""
        adf = convert_markdown_to_adf("| A | B |\n| --- | --- |\n| 1 | 2 |")

        assert adf["content"][0]["type"] == "table"

    def test_conversion_needs_no_node_or_subprocess(self, monkeypatch):
        """Conversion is pure Python: no subprocess, no Node.js."""

        def fail(*args, **kwargs):
            raise AssertionError("conversion must not spawn a subprocess")

        monkeypatch.setattr(subprocess, "run", fail)
        monkeypatch.setattr(subprocess, "Popen", fail)
        monkeypatch.setenv("PATH", "")

        adf = convert_markdown_to_adf("# Works offline")

        assert adf["type"] == "doc"


class TestTextAreaContent:
    """Tests for the TextAreaContent class."""

    def test_string_content_converted_to_adf(self):
        """String content is converted from Markdown to ADF."""
        content = TextAreaContent("# Title\n\n- item")

        assert content.content["type"] == "doc"
        assert content.content["version"] == 1

    def test_list_content_formatted_as_markdown_list(self):
        """List content becomes an ADF bulletList."""
        content = TextAreaContent(["Item 1", "Item 2", "Item 3"])

        types = [node["type"] for node in content.content["content"]]
        assert types == ["bulletList"]
        assert len(content.content["content"][0]["content"]) == 3

    def test_empty_content_becomes_no_content(self):
        """Empty content is replaced with the 'No Content' placeholder."""
        content = TextAreaContent("")

        text_node = content.content["content"][0]["content"][0]
        assert text_node["text"] == "No Content"

    def test_json_content_wrapped_in_code_block(self):
        """JSON content takes precedence and is wrapped in a code block."""
        content = TextAreaContent("", json_content='{"key": "value"}')

        block = content.content["content"][0]
        assert block["type"] == "codeBlock"
        assert block["attrs"]["language"] == "json"
        assert block["content"][0]["text"] == '{"key": "value"}'
