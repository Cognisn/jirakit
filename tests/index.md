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
| `test_pagination.py` | The paginated list helpers shared across the package: the HTTP status is checked before the body is parsed, so a 401, 403 or 429 raises `HTTPError` rather than `JSONDecodeError`; a response carrying no `isLast` ends the walk instead of looping indefinitely; and each page is parsed once. |
| `test_get_or_create.py` | The `ensure_*` get-or-create helpers for issue types, screens, screen schemes and issue type screen schemes: adopting an existing resource by name, creating an absent one, and reporting which happened without writing under a dry run. |
| `test_screen_reconciliation.py` | `Screen.ensure_tab`: finding a tab by name, adding only the fields it lacks, leaving a field already on a sibling tab alone, and predicting the same changes under a dry run. |
| `test_template_reconciliation.py` | Applying a template to a project it has already been deployed to, against stateful in-memory Jira: applying it twice creates nothing, a template that gained a field or issue type is applied, and `create` still deploys and tracks the whole template through the same code path. |
| `test_template_plan.py` | `reconcile_template`, `plan_template` and `missing_template_fields`: that a plan predicts what the apply then does, that the field report reads only create metadata so it works without Jira administrator permission, and that both create metadata endpoints are read to exhaustion rather than a single 50-item page. Also the terminators of the shared `read_all_pages` helper, each covered independently. |
| `test_workflow_reconciliation.py` | Opt-in workflow reconciliation: an existing workflow is skipped and reported by default, updated on request, and the update carries the workflow's current version and is validated first. |
| `test_projects.py` | The Projects module: template-based project deployment and configuration. |
| `test_deployment_order.py` | The order `Projects.create` and `Projects.apply_template` issue their requests in: screen tabs must be populated only after the screens are wired to the project, or the deployed fields never register with Jira's issue create metadata. |
| `test_rollback.py` | `Projects.rollback_template_deployment`: the order deletions are issued in, coverage of tracked and auto-created resources, retries for deletions Jira refuses, and what a partial rollback reports and keeps. |
| `test_screens.py` | The Screens module: screens, screen schemes, field-to-screen mapping, and adding a field to an existing screen (`Screen.add_field`). |
| `test_text_area.py` | Markdown to ADF conversion (pure Python via marklassian) and `TextAreaContent` formatting of strings, lists, and JSON code blocks. |
| `test_tracking.py` | The `DeploymentTracker` class: deployment tracking and rollback support. |
| `test_workflows.py` | The Workflows module: statuses, workflow and workflow scheme assignment, and workflow creation through `POST /rest/api/3/workflows/create` — status UUID references, transition links and types, condition and validator rule mapping, pre-flight validation, and the identifier rollback deletes by. |

`conftest.py` provides the shared pytest fixtures for the suite. `fake_jira.py` is a stateful in-memory stand-in for the Jira endpoints a template deployment uses, for the tests where what happens on a second run depends on what the first one left behind; it derives issue create metadata from screen tab membership, as Jira does, and pages the create metadata endpoints at 50 as they do, so a truncated read is something a test can actually observe.
