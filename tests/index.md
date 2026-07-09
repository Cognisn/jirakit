# Tests

Index of the tests in this folder. Keep it current as tests are added, changed, or removed. See `README.md` in this folder for fuller coverage notes. The suite runs fully offline; all HTTP and `jira.JIRA` interactions are mocked.

| Test | Covers |
| --- | --- |
| `test_client.py` | The `JiraClient` class: authentication, request handling, timeouts, the `can_administer` permission probe, and core API access. |
| `test_fields.py` | The Fields module: custom field creation and management, including text area / ADF handling. |
| `test_groups.py` | The Groups module: Jira group creation and membership management. |
| `test_import.py` | Package import behaviour: no import-time side effects (no environment checks, no subprocesses, no installs). |
| `test_issue_types.py` | The Issue Types module: custom issue type creation and scheme association. |
| `test_issues.py` | The Issues module: issue creation and manipulation over the REST API v3, `Issue._format_doc` ADF rendering (defensive key access plus bullet/ordered/nested list nodes), attachment upload, and field-mapping metadata / preflight. |
| `test_projects.py` | The Projects module: template-based project deployment and configuration. |
| `test_screens.py` | The Screens module: screens, screen schemes, field-to-screen mapping, and adding a field to an existing screen (`Screen.add_field`). |
| `test_text_area.py` | Markdown to ADF conversion (pure Python via marklassian) and `TextAreaContent` formatting of strings, lists, and JSON code blocks. |
| `test_tracking.py` | The `DeploymentTracker` class: deployment tracking and rollback support. |
| `test_workflows.py` | The Workflows module: workflow and workflow scheme creation and assignment. |

`conftest.py` provides the shared pytest fixtures for the suite.
