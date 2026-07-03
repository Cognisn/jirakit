"""
Unit tests for package import behaviour.

Tests cover:
- Importing jirakit has no import-time side effects (no environment checks,
  no software installation), even when Node.js is absent from PATH.
"""

import subprocess
import sys


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
