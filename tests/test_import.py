"""
Unit tests for package import behaviour.

Tests cover:
- Importing jirakit has no import-time side effects (no environment checks,
  no software installation), even when Node.js is absent from PATH.
- convert_markdown_to_adf() raises a clear error at first use when Node.js
  is not available.
"""

import subprocess
import sys

import pytest


class TestImportSideEffects:
    """Tests that importing jirakit is side-effect free."""

    def test_import_succeeds_without_node_on_path(self, tmp_path):
        """Importing jirakit must succeed even when Node.js is unavailable."""
        result = subprocess.run(
            [sys.executable, "-c", "import jirakit"],
            capture_output=True,
            text=True,
            env={"PATH": str(tmp_path)},
            timeout=60,
        )

        assert result.returncode == 0, (
            f"import jirakit failed without Node.js on PATH:\n{result.stderr}"
        )

    def test_import_runs_no_subprocesses(self, tmp_path):
        """Importing jirakit must not spawn any subprocess (npm, node, installers)."""
        probe = (
            "import subprocess, sys\n"
            "calls = []\n"
            "subprocess.run = lambda *a, **k: calls.append(a) or sys.exit(2)\n"
            "subprocess.Popen = lambda *a, **k: calls.append(a) or sys.exit(2)\n"
            "import jirakit\n"
            "sys.exit(0)\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", probe],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, (
            f"import jirakit spawned a subprocess:\n{result.stderr}"
        )


class TestMarkdownConversionEnvironmentCheck:
    """Tests the first-use environment check for Markdown to ADF conversion."""

    def test_convert_markdown_raises_clear_error_without_node(self, monkeypatch):
        """convert_markdown_to_adf raises an actionable error when node is missing."""
        from jirakit.fields import text_area

        def raise_file_not_found(*args, **kwargs):
            raise FileNotFoundError("node")

        monkeypatch.setattr(text_area.subprocess, "run", raise_file_not_found)

        with pytest.raises(RuntimeError, match="Node.js"):
            text_area.convert_markdown_to_adf("# Heading")
