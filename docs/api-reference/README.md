# API Reference

Complete API documentation for jirakit modules and classes.

## Overview

This section provides detailed API documentation for all public classes and methods in jirakit.

## Core Classes

- **[JiraClient](#jiraclient)** - Main client for Jira Cloud connection
- **[Projects](#projects)** - Project management and template deployment
- **[DeploymentTracker](#deploymenttracker)** - Deployment tracking and rollback
- **[IssueTypes](#issuetypes)** - Issue type management
- **[Screens](#screens)** - Screen management
- **[Workflows](#workflows)** - Workflow management
- **[Fields](#fields)** - Field management
- **[Groups](#groups)** - Group management

---

## JiraClient

Main client for connecting to and interacting with Jira Cloud.

**Location:** `src/jirakit/__init__.py`

### Constructor

```python
JiraClient(url: str, username: str, password: str)
```

**Parameters:**
- `url` (str): Jira Cloud instance URL (e.g., "https://your-instance.atlassian.net/")
- `username` (str): Email address for authentication
- `password` (str): API token (not your Atlassian password)

**Example:**
```python
from jirakit import JiraClient

client = JiraClient(
    url="https://your-instance.atlassian.net/",
    username="your-email@example.com",
    api_token="your-api-token"
)
```

### Methods

#### get_me()

Get information about the current authenticated user.

```python
client.get_me() -> dict
```

**Returns:** Dictionary with user information (displayName, emailAddress, accountId, etc.)

**Example:**
```python
me = client.get_me()
print(f"Logged in as: {me['displayName']}")
```

#### projects()

Get the Projects manager instance.

```python
client.projects() -> Projects
```

**Returns:** Projects instance

#### issue_types()

Get the IssueTypes manager instance.

```python
client.issue_types() -> IssueTypes
```

**Returns:** IssueTypes instance

#### screens()

Get the Screens manager instance.

```python
client.screens() -> Screens
```

**Returns:** Screens instance

#### workflows()

Get the Workflows manager instance.

```python
client.workflows() -> Workflows
```

**Returns:** Workflows instance

#### fields()

Get the Fields manager instance.

```python
client.fields() -> Fields
```

**Returns:** Fields instance

#### groups()

Get the Groups manager instance.

```python
client.groups() -> Groups
```

**Returns:** Groups instance

#### HTTP Methods

Low-level HTTP methods for direct API access.

```python
client.get(path: str) -> requests.Response
client.post(path: str, data: dict) -> requests.Response
client.put(path: str, data: dict) -> requests.Response
client.delete(path: str) -> requests.Response
```

**Parameters:**
- `path` (str): API endpoint path (e.g., "/rest/api/3/project")
- `data` (dict): Request payload (for POST/PUT)

**Returns:** requests.Response object

**Example:**
```python
response = client.get('/rest/api/3/myself')
response.raise_for_status()
data = response.json()
```

---

## Projects

Project management including template deployment and rollback.

**Location:** `src/jirakit/projects/__init__.py`

### Methods

#### get_project()

Get a project by key.

```python
projects.get_project(project_key: str) -> Project
```

**Parameters:**
- `project_key` (str): The project key

**Returns:** Project instance

**Raises:** Exception if project not found

**Example:**
```python
project = client.projects().get_project("MYPROJ")
print(project.name)
```

#### get_all()

Get all projects.

```python
projects.get_all(status: str = 'live') -> list[Project]
```

**Parameters:**
- `status` (str, optional): Project status filter ('live', 'archived', etc.). Default: 'live'

**Returns:** List of Project instances

**Example:**
```python
all_projects = client.projects().get_all()
for project in all_projects:
    print(f"{project.key}: {project.name}")
```

#### create()

Create a new project from a template.

```python
projects.create(
    name: str,
    key: str,
    template: dict
) -> Project
```

**Parameters:**
- `name` (str): Project name
- `key` (str): Project key (max 10 characters, alphanumeric)
- `template` (dict): Template definition (loaded from YAML)

**Returns:** Created Project instance

**Raises:**
- Exception if project key already exists
- Exception if template is invalid
- Exception if deployment fails

**Side Effects:**
- Creates deployment tracking file in `.jirakit_deployments/{key}.json`
- Logs all operations

**Example:**
```python
import yaml

with open('template.yaml', 'r') as f:
    template = yaml.safe_load(f)

project = client.projects().create(
    name="My Project",
    key="MYPROJ",
    template=template
)
```

#### apply_template()

Apply a template to a project, creating only what is not already there.

```python
projects.apply_template(
    project: Project,
    template: dict,
    tracker: DeploymentTracker = None,
    dry_run: bool = False,
    reconcile_workflows: bool = False
) -> TemplateApplication
```

This is the single implementation behind both `create()` and
`reconcile_template()`. Every step is a get-or-create against the name the
deployment gives the resource (`<KEY>: <template name>`), so applying the same
template twice is a no-op.

**Parameters:**
- `project` (Project): The project to apply the template to
- `template` (dict): Template definition
- `tracker` (DeploymentTracker, optional): Records created resources for rollback. Resources that are adopted rather than created are deliberately not tracked, so a rollback never deletes what the deployment did not make
- `dry_run` (bool): Report the changes without making any of them
- `reconcile_workflows` (bool): Update a workflow that already exists. Off by default; see the note under `reconcile_template()`

**Returns:** `TemplateApplication` with `.project`, `.changes`, `.changed` and `.summary()`

#### reconcile_template()

Bring an already-deployed project up to a template that has changed.

```python
projects.reconcile_template(
    project: Project | str,
    template: dict,
    dry_run: bool = False,
    reconcile_workflows: bool = False
) -> TemplateApplication
```

**Example:**
```python
result = client.projects().reconcile_template("MYPROJ", template)

if result.changed:
    for line in result.summary():
        print(line)
```

**Workflows are not reconciled by default.** Jira Cloud's workflow update
endpoint replaces a whole workflow definition rather than merging into it, so
running it against a workflow carrying live issues is a materially different
risk from adding a field to a screen. An existing workflow is left alone and
reported as a `skip` change. Pass `reconcile_workflows=True` to update it.

Requires Jira administrator permission, as the screen and scheme endpoints do.

#### plan_template()

Report what `reconcile_template()` would change, without changing it.

```python
projects.plan_template(project: Project | str, template: dict) -> TemplateApplication
```

**Example:**
```python
plan = client.projects().plan_template("MYPROJ", template)

for line in plan.summary():
    print(f"would {line}")
```

#### missing_template_fields()

Report which template fields an issue type's create metadata is missing.

```python
projects.missing_template_fields(
    project: Project | str,
    template: dict
) -> dict[str, list[str]]
```

Answers the narrower question a least-privileged runtime has — can this project
accept the fields the template describes? — from issue create metadata alone.
Createmeta reads **without Jira administrator permission**, whereas the screen
endpoints `plan_template()` needs return 403, so this works where a full plan
cannot.

Because Jira derives create metadata from screen tab membership, a field
reported here is one that genuinely cannot be set on an issue of that type.

**Returns:** Missing field names keyed by issue type name, omitting issue types
that are missing nothing.

**Example:**
```python
missing = client.projects().missing_template_fields("MYPROJ", template)

for issue_type, fields in missing.items():
    print(f"{issue_type} is missing: {', '.join(fields)}")
```

#### rollback_template_deployment()

Rollback a template deployment, deleting all created resources.

```python
projects.rollback_template_deployment(
    project_key: str,
    delete_project: bool = True,
    enable_undo: bool = False,
    tracking_dir: str = ".jirakit_deployments",
    retry_seconds: float = 30.0
) -> dict
```

**Parameters:**
- `project_key` (str): The project key to rollback
- `delete_project` (bool, optional): Whether to delete the project. Default: True.
  When False nothing is deleted at all, because a scheme assigned to a live project
  cannot be deleted; the reason is recorded in `skipped`
- `enable_undo` (bool, optional): Enable project deletion undo. Default: False. When
  True the project goes to the recycle bin instead of being deleted, and a project
  in the recycle bin still holds its schemes, so nothing beyond the project itself
  can be deleted; the reason is recorded in `skipped`
- `tracking_dir` (str, optional): Tracking file directory. Default: ".jirakit_deployments"
- `retry_seconds` (float, optional): How long to keep retrying deletions Jira
  refuses. Default: 30.0. Pass 0 to attempt each deletion once

**Returns:** Summary dictionary with keys:
- `issue_types_deleted` (list[str]): Deleted issue type names
- `issue_type_schemes_deleted` (list[str]): Deleted scheme names
- `screens_deleted` (list[str]): Deleted screen names
- `screen_schemes_deleted` (list[str]): Deleted screen scheme names
- `issue_type_screen_schemes_deleted` (list[str]): Deleted ITSS names
- `workflows_deleted` (list[str]): Deleted workflow names
- `workflow_schemes_deleted` (list[str]): Deleted workflow scheme names
- `project_deleted` (bool): Whether project was deleted
- `tracking_file_used` (bool): Whether tracking file was found and used
- `resources_remaining` (list[dict]): Resources that could not be deleted, each
  with `type`, `id`, `name` and `reason`
- `shared_resources_left` (list[str]): Notes on resources deliberately not deleted
  because they may be shared, namely custom fields and statuses
- `skipped` (list[str]): Why whole groups of deletions were not attempted
- `errors` (list[str]): List of error messages

**Behaviour:**
- Deletes the project first. A scheme still assigned to a live project cannot be
  deleted, so everything else follows in dependency order: workflow schemes then
  their workflows; issue type screen schemes, then screen schemes, then screens;
  issue type schemes then issue types
- Also deletes the resources the project template makes Jira create alongside the
  project — its screens, screen schemes, issue type screen scheme, issue type
  scheme, workflow scheme and workflow — which nothing tracks and project deletion
  does not remove. They are found by the `<KEY>: ` prefix the deployment itself
  uses, so a resource merely mentioning the key elsewhere is left alone
- Attempts to load the tracking file for a precise rollback, and falls back to
  searching by naming convention if there is none
- Treats a project it cannot retrieve as already deleted and cleans up what it
  left behind, so a rollback kept for retry can finish the job later
- Retries a refused deletion until it succeeds or `retry_seconds` runs out. This
  is defensive; in practice the corrected ordering makes every deletion succeed
  first time
- Continues on errors, recording each in `errors` and `resources_remaining`
- Deletes the tracking file only after a completely clean rollback, so a partial
  rollback can be retried from the same record

**Example:**
```python
summary = client.projects().rollback_template_deployment(
    project_key="MYPROJ",
    delete_project=True
)

print(f"Tracking used: {summary['tracking_file_used']}")
print(f"Issue types deleted: {len(summary['issue_types_deleted'])}")
print(f"Project deleted: {summary['project_deleted']}")

for resource in summary['resources_remaining']:
    print(f"Left behind: {resource['type']} {resource['name']} - {resource['reason']}")

for note in summary['shared_resources_left']:
    print(note)
```

#### delete_project()

Delete a project.

```python
projects.delete_project(
    project: Project,
    enable_undo: bool = False
) -> None
```

**Parameters:**
- `project` (Project): The project to delete
- `enable_undo` (bool, optional): Enable deletion undo. Default: False

**Example:**
```python
project = client.projects().get_project("MYPROJ")
client.projects().delete_project(project, enable_undo=True)
```

---

## DeploymentTracker

**NEW in v0.1.6**

Tracks resources created during template deployment for precise rollback.

**Location:** `src/jirakit/projects/tracking.py`

### Constructor

```python
DeploymentTracker(
    project_key: str,
    project_id: str = None,
    project_name: str = None,
    template_name: str = None,
    tracking_dir: str = ".jirakit_deployments"
)
```

**Parameters:**
- `project_key` (str): The project key
- `project_id` (str, optional): The project ID
- `project_name` (str, optional): The project name
- `template_name` (str, optional): The template name
- `tracking_dir` (str, optional): Directory for tracking files

**Side Effects:**
- Creates tracking directory if it doesn't exist
- Creates tracking file with initial data
- Sets status to "in_progress"

**Example:**
```python
from jirakit.projects.tracking import DeploymentTracker

tracker = DeploymentTracker(
    project_key="MYPROJ",
    project_name="My Project",
    template_name="My Template"
)
```

### Methods

#### set_project_id()

Set the project ID after creation.

```python
tracker.set_project_id(project_id: str) -> None
```

**Parameters:**
- `project_id` (str): The created project ID

#### set_deployed_by()

Set the deploying user's email.

```python
tracker.set_deployed_by(user_email: str) -> None
```

**Parameters:**
- `user_email` (str): Email address of deploying user

#### track_issue_type()

Track a created issue type.

```python
tracker.track_issue_type(issue_type_id: str, name: str) -> None
```

**Parameters:**
- `issue_type_id` (str): The issue type ID
- `name` (str): The issue type name

#### track_screen()

Track a created screen.

```python
tracker.track_screen(screen_id: str, name: str) -> None
```

**Parameters:**
- `screen_id` (str): The screen ID
- `name` (str): The screen name

#### track_workflow()

Track a created workflow.

```python
tracker.track_workflow(entity_id: str, name: str) -> None
```

**Parameters:**
- `entity_id` (str): The workflow entity ID
- `name` (str): The workflow name

#### track_screen_scheme()

Track a created screen scheme.

```python
tracker.track_screen_scheme(scheme_id: str, name: str) -> None
```

#### track_issue_type_screen_scheme()

Track a created issue type screen scheme.

```python
tracker.track_issue_type_screen_scheme(scheme_id: str, name: str) -> None
```

#### track_issue_type_scheme()

Track a created issue type scheme.

```python
tracker.track_issue_type_scheme(scheme_id: str, name: str) -> None
```

#### track_workflow_scheme()

Track a created workflow scheme.

```python
tracker.track_workflow_scheme(scheme_id: str, name: str) -> None
```

#### track_error()

Track an error that occurred during deployment.

```python
tracker.track_error(error_message: str) -> None
```

**Parameters:**
- `error_message` (str): Error description

#### mark_completed()

Mark the deployment as successfully completed.

```python
tracker.mark_completed() -> None
```

**Side Effects:**
- Sets status to "completed"
- Records completion timestamp

#### mark_failed()

Mark the deployment as failed.

```python
tracker.mark_failed() -> None
```

**Side Effects:**
- Sets status to "failed"
- Records completion timestamp

#### mark_partial()

Mark the deployment as partially completed.

```python
tracker.mark_partial() -> None
```

**Side Effects:**
- Sets status to "partial"
- Records completion timestamp

#### load() (classmethod)

Load tracking data for a project.

```python
DeploymentTracker.load(
    project_key: str,
    tracking_dir: str = ".jirakit_deployments"
) -> Optional[DeploymentTracker]
```

**Parameters:**
- `project_key` (str): The project key
- `tracking_dir` (str, optional): Tracking directory

**Returns:** DeploymentTracker instance or None if not found

**Example:**
```python
tracker = DeploymentTracker.load("MYPROJ")

if tracker:
    print(f"Status: {tracker.data['status']}")
else:
    print("No tracking file found")
```

#### get_summary()

Get a summary of the deployment.

```python
tracker.get_summary() -> dict
```

**Returns:** Dictionary with keys:
- `project_key` (str)
- `status` (str)
- `started` (str): ISO timestamp
- `completed` (str): ISO timestamp or None
- `custom_fields_created` (int)
- `issue_types_created` (int)
- `screens_created` (int)
- `screen_schemes_created` (int)
- `workflows_created` (int)
- `errors` (int)

**Example:**
```python
summary = tracker.get_summary()
print(f"Status: {summary['status']}")
print(f"Issue types created: {summary['issue_types_created']}")
```

#### delete_tracking_file()

Delete the tracking file.

```python
tracker.delete_tracking_file() -> None
```

**Example:**
```python
tracker.delete_tracking_file()
```

### Data Structure

The `data` attribute contains the tracking information:

```python
{
    "project_key": str,
    "project_id": str,
    "project_name": str,
    "template_name": str,
    "deployment_started": str,  # ISO timestamp
    "deployment_completed": str,  # ISO timestamp or None
    "deployed_by": str,
    "status": str,  # "in_progress", "completed", "failed", "partial"
    "resources_created": {
        "custom_fields": [],
        "issue_types": [
            {
                "id": str,
                "name": str,
                "created_at": str  # ISO timestamp
            }
        ],
        "screens": [...],
        "screen_schemes": [...],
        "issue_type_screen_schemes": [...],
        "issue_type_schemes": [...],
        "workflows": [
            {
                "entity_id": str,
                "name": str,
                "created_at": str
            }
        ],
        "workflow_schemes": [...]
    },
    "errors": [
        {
            "message": str,
            "timestamp": str  # ISO timestamp
        }
    ]
}
```

---

## IssueTypes

Issue type and scheme management.

**Location:** `src/jirakit/issues/types.py`

### Methods

#### get_all_user_issue_types()

Get all user-created issue types.

```python
issue_types.get_all_user_issue_types() -> list[IssueType]
```

**Returns:** List of IssueType instances

#### create()

Create a new issue type.

```python
issue_types.create(
    name: str,
    description: str,
    is_subtask: bool
) -> IssueType
```

**Parameters:**
- `name` (str): Issue type name
- `description` (str): Issue type description
- `is_subtask` (bool): Whether this is a subtask type

**Returns:** Created IssueType instance

#### delete()

Delete an issue type.

```python
issue_types.delete(issue_type: IssueType) -> None
```

**Parameters:**
- `issue_type` (IssueType): The issue type to delete

---

## Additional Modules

Documentation for additional modules coming soon:

- Screens
- Workflows
- Fields
- Groups

## Related Documentation

- [Quick Reference](../guides/quick-reference.md) - Common operations
- [Template Deployment Guide](../guides/template-deployment.md) - Deployment guide
- [Rollback & Recovery](../guides/rollback-recovery.md) - Rollback guide
