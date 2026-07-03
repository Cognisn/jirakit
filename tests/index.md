# Tests

Index of the tests in this folder. Keep it current as tests are added, changed, or removed. See `README.md` in this folder for fuller coverage notes. The suite runs fully offline; all HTTP and `jira.JIRA` interactions are mocked.

| Test | Covers |
| --- | --- |
| `test_client.py` | The `JiraClient` class: authentication, request handling, and core API access. |
| `test_fields.py` | The Fields module: custom field creation and management, including text area / ADF handling. |
| `test_groups.py` | The Groups module: Jira group creation and membership management. |
| `test_issue_types.py` | The Issue Types module: custom issue type creation and scheme association. |
| `test_issues.py` | The Issues module: issue creation and manipulation over the REST API v3. |
| `test_projects.py` | The Projects module: template-based project deployment and configuration. |
| `test_screens.py` | The Screens module: screens, screen schemes, and field-to-screen mapping. |
| `test_tracking.py` | The `DeploymentTracker` class: deployment tracking and rollback support. |
| `test_workflows.py` | The Workflows module: workflow and workflow scheme creation and assignment. |

`conftest.py` provides the shared pytest fixtures for the suite.
