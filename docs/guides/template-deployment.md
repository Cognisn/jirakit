# Template Deployment Guide

This guide explains how to deploy Jira project templates using jirakit's template deployment system.

## Overview

The template deployment feature allows you to create fully-configured Jira projects from YAML template files. This includes:

- Custom project configuration
- Issue types with custom fields
- Screens and screen schemes
- Workflows and workflow schemes
- Issue type mappings
- Groups and permissions

All deployments are automatically tracked, enabling precise rollback if needed.

## Quick Start

### Basic Deployment

```python
from jirakit import JiraClient

# Connect to Jira
client = JiraClient(
    url="https://your-instance.atlassian.net/",
    username="your-email@example.com",
    api_token="your-api-token"
)

# Load template
import yaml
with open('my-template.yaml', 'r') as f:
    template = yaml.safe_load(f)

# Deploy template
projects = client.projects()
project = projects.create(
    name="My New Project",
    key="MNP",  # Must be unique and max 10 characters
    template=template
)

print(f"Project created: {project.key}")
print(f"Project ID: {project.id}")
```

### With Error Handling

```python
from jirakit import JiraClient
import yaml
import logging

# Enable logging to see deployment progress
logging.basicConfig(level=logging.INFO)

def deploy_template(template_path, project_name, project_key):
    """
    Deploy a template to a new Jira project with proper error handling.

    :param template_path: Path to the YAML template file
    :param project_name: Name for the new project
    :param project_key: Unique key for the project (max 10 chars)
    :return: Created project object or None on failure
    """
    try:
        # Connect to Jira
        client = JiraClient(
            url="https://your-instance.atlassian.net/",
            username="your-email@example.com",
            api_token="your-api-token"
        )

        # Load template
        with open(template_path, 'r') as f:
            template = yaml.safe_load(f)

        # Deploy
        logging.info(f"Deploying template '{template.get('name')}' to {project_key}")
        projects = client.projects()
        project = projects.create(
            name=project_name,
            key=project_key,
            template=template
        )

        logging.info(f"Successfully created project: {project.key} (ID: {project.id})")
        return project

    except FileNotFoundError as e:
        logging.error(f"Template file not found: {template_path}")
        return None
    except Exception as e:
        logging.error(f"Deployment failed: {e}")
        # Check tracking file for partial deployment info
        tracking_file = f".jirakit_deployments/{project_key}.json"
        if os.path.exists(tracking_file):
            logging.info(f"Tracking file available for rollback: {tracking_file}")
        return None

# Example usage
project = deploy_template(
    template_path="templates/service-desk.yaml",
    project_name="IT Service Desk",
    project_key="ITSD"
)

if project:
    print(f"Deployment successful! URL: https://your-instance.atlassian.net/browse/{project.key}")
else:
    print("Deployment failed. Check logs for details.")
```

## Deployment Process

When you deploy a template, jirakit performs the following steps in order:

### 1. Initialisation
- Creates a deployment tracker
- Records project metadata (key, name, template name)
- Creates tracking file in `.jirakit_deployments/`
- Records deploying user's email

### 2. Project Creation
- Creates the base Jira project
- Records project ID in tracking file

### 3. Groups Creation
- Creates all groups defined in template
- Groups are **not tracked** (shared resource)

### 4. Field Assignment
- Assigns custom fields to the project
- Fields are **not tracked** (shared resource)

### 5. Issue Types Creation
- Creates custom issue types with project key prefix
- Each issue type is tracked with ID
- Format: `{PROJECT_KEY}: {Issue Type Name}`

### 6. Issue Type Schemes
- Creates issue type schemes
- Associates issue types with the scheme
- Tracked with scheme ID

### 7. Screens Creation
- Creates custom screens
- Each screen is tracked with ID
- Tabs are **not** populated here; see step 10

### 8. Screen Schemes Creation
- Creates screen schemes
- Maps operations (create/edit/view) to screens
- Tracked with scheme ID

### 9. Issue Type Screen Schemes
- Creates mappings between issue types and screen schemes
- Includes default screen scheme mapping
- Assigns the scheme to the project, which is what wires the screens to it
- Tracked with scheme ID

### 10. Screen Tabs
- Creates each tab and adds the template's fields to it
- Runs **after** step 9, and the order matters: Jira registers a field with the
  project's issue create metadata when the field is added to a tab of a screen
  that is already wired to a project. Populating the tabs earlier leaves every
  field permanently invisible to create metadata, so none of them can be set
  when creating an issue

### 11. Workflows Creation
- Creates custom workflows
- Defines statuses and transitions
- Tracked with workflow entity ID

### 12. Workflow Schemes Creation
- Creates workflow schemes
- Maps issue types to workflows
- Associates scheme with project
- Tracked with scheme ID

### 13. Completion
- Marks deployment as completed in tracking file
- Records completion timestamp

## Applying a Changed Template

Every step above is a get-or-create against the name the deployment gives the
resource (`{PROJECT_KEY}: {Template Name}`), so a template can be applied to a
project it has already been deployed to. Only the difference is applied, and
applying an unchanged template is a no-op.

```python
result = client.projects().reconcile_template("MYPROJ", template)

if result.changed:
    for line in result.summary():
        print(line)
```

Resources that are **adopted** rather than created are deliberately not
tracked, so a later rollback never deletes something the deployment did not
make.

### Seeing what would change first

```python
plan = client.projects().plan_template("MYPROJ", template)

for line in plan.summary():
    print(f"would {line}")
```

A plan makes no requests that write, and reports exactly what the reconcile
that follows it would do.

### Workflows are not reconciled by default

Jira Cloud's workflow update endpoint replaces a whole workflow definition
rather than merging into it, so running it against a workflow carrying live
issues is a materially different risk from adding a field to a screen. A
workflow that already exists is therefore left alone and reported as a `skip`
change, rather than silently ignored:

```python
for change in result.changes:
    if change["action"] == "skip":
        print(f"{change['name']}: {change['reason']}")
```

Pass `reconcile_workflows=True` to update it instead.

### Repairing a workflow deployed by 0.6.x

jirakit 0.6.0 and 0.6.1 emitted the `AllowOnlyAssignee` condition in a form Jira
cannot resolve, which denies the transition to everyone rather than restricting
it to the assignee. Any project provisioned by those versions has a workflow
nobody can drive, and nothing reports it at deployment time.

Since 0.7.1 the condition is emitted correctly, so reconciling the workflow
repairs it:

```python
result = client.projects().reconcile_template(
    "MYPROJ", template, reconcile_workflows=True
)
```

This is the one case where `reconcile_workflows=True` is the remedy rather than
the risk. It still replaces the whole workflow definition, so the template must
be the one the project was deployed from, and check the plan first:

```python
plan = client.projects().plan_template("MYPROJ", template)
```

### Without administrator permission

`reconcile_template()` and `plan_template()` read the screen and scheme
endpoints, which require Jira administrator. A service account that can create
and transition issues perfectly well gets 403 on those.

`missing_template_fields()` answers the narrower question from issue create
metadata alone, which reads without administrator permission:

```python
missing = client.projects().missing_template_fields("MYPROJ", template)

for issue_type, fields in missing.items():
    print(f"{issue_type} cannot accept: {', '.join(fields)}")
```

Because Jira derives create metadata from screen tab membership, a field
reported here is one that genuinely cannot be set on an issue of that type.
This lets a least-privileged runtime report precisely what an administrator
must change, and leaves the apply to a separate, deliberately elevated
invocation.

## Tracking System

Every deployment creates a tracking file in `.jirakit_deployments/{PROJECT_KEY}.json` containing:

### Tracking File Structure

```json
{
  "project_key": "MYPROJ",
  "project_id": "10188",
  "project_name": "My Project",
  "template_name": "My Template",
  "deployment_started": "2025-10-08T12:07:17.117803",
  "deployment_completed": "2025-10-08T12:08:35.810145",
  "deployed_by": "user@example.com",
  "status": "completed",
  "resources_created": {
    "custom_fields": [],
    "issue_types": [
      {
        "id": "10404",
        "name": "MYPROJ: Task",
        "created_at": "2025-10-08T12:07:20.123456"
      }
    ],
    "screens": [
      {
        "id": "10403",
        "name": "MYPROJ: Task Screen",
        "created_at": "2025-10-08T12:07:25.654321"
      }
    ],
    "screen_schemes": [...],
    "issue_type_screen_schemes": [...],
    "issue_type_schemes": [...],
    "workflows": [...],
    "workflow_schemes": [...]
  },
  "errors": []
}
```

### Status Values

- **in_progress** - Deployment currently running
- **completed** - Deployment finished successfully
- **failed** - Deployment failed (see errors array)
- **partial** - Deployment partially completed

### Using Tracking Information

```python
from jirakit.projects.tracking import DeploymentTracker

# Load tracking data
tracker = DeploymentTracker.load("MYPROJ")

if tracker:
    # Get summary
    summary = tracker.get_summary()
    print(f"Status: {summary['status']}")
    print(f"Issue types created: {summary['issue_types_created']}")
    print(f"Screens created: {summary['screens_created']}")
    print(f"Errors: {summary['errors']}")

    # Access full data
    for issue_type in tracker.data['resources_created']['issue_types']:
        print(f"  - {issue_type['name']} (ID: {issue_type['id']})")
else:
    print("No tracking data found")
```

## Best Practices

### Project Key Naming

```python
# Good: Short, descriptive, unique
project_key = "ITSD"      # IT Service Desk
project_key = "ITSEC"     # IT Security
project_key = "HRPROC"    # HR Processes

# Bad: Too long (max 10 chars)
project_key = "ITSERVICEDESK"  # 13 chars - will fail

# Bad: Not unique
project_key = "TEMP"      # Generic, likely conflicts
```

### Template Organisation

```python
# Organise templates by type/purpose
templates/
├── service-desk/
│   ├── basic-service-desk.yaml
│   └── advanced-service-desk.yaml
├── software/
│   ├── agile-scrum.yaml
│   └── kanban.yaml
└── hr/
    └── recruitment.yaml

# Load with consistent pattern
def load_template(category, name):
    path = f"templates/{category}/{name}.yaml"
    with open(path, 'r') as f:
        return yaml.safe_load(f)

template = load_template("service-desk", "basic-service-desk")
```

### Deployment Validation

```python
def validate_deployment(project_key):
    """
    Validate a deployment was successful.

    :param project_key: The project key to validate
    :return: True if successful, False otherwise
    """
    from jirakit.projects.tracking import DeploymentTracker

    tracker = DeploymentTracker.load(project_key)

    if not tracker:
        print(f"No tracking data for {project_key}")
        return False

    if tracker.data['status'] != 'completed':
        print(f"Deployment status: {tracker.data['status']}")
        return False

    if tracker.data['errors']:
        print(f"Deployment had {len(tracker.data['errors'])} errors:")
        for error in tracker.data['errors']:
            print(f"  - {error['message']}")
        return False

    print(f"Deployment of {project_key} validated successfully")
    return True

# Use after deployment
if validate_deployment("MYPROJ"):
    print("Ready to use!")
else:
    print("Check logs and consider rollback")
```

### Batch Deployments

```python
def batch_deploy(deployments):
    """
    Deploy multiple projects from templates.

    :param deployments: List of (name, key, template_path) tuples
    :return: Dictionary of results
    """
    results = {
        'successful': [],
        'failed': []
    }

    client = JiraClient(url, username, api_token)
    projects = client.projects()

    for name, key, template_path in deployments:
        try:
            with open(template_path, 'r') as f:
                template = yaml.safe_load(f)

            project = projects.create(name=name, key=key, template=template)
            results['successful'].append({
                'key': key,
                'id': project.id,
                'name': name
            })

        except Exception as e:
            results['failed'].append({
                'key': key,
                'name': name,
                'error': str(e)
            })

    return results

# Example usage
deployments = [
    ("IT Service Desk", "ITSD", "templates/service-desk.yaml"),
    ("HR Recruitment", "HRREC", "templates/hr-recruitment.yaml"),
    ("Sales Pipeline", "SALES", "templates/sales.yaml")
]

results = batch_deploy(deployments)

print(f"Successful: {len(results['successful'])}")
print(f"Failed: {len(results['failed'])}")

# Rollback failed deployments
for failed in results['failed']:
    print(f"Rolling back {failed['key']}...")
    projects.rollback_template_deployment(failed['key'])
```

## Troubleshooting

### Common Issues

#### 1. Project Key Too Long
```
Error: The project key must not exceed 10 characters in length.
```
**Solution:** Use a shorter project key (max 10 characters)

#### 2. Duplicate Project Key
```
Error: A project with that project key already exists.
```
**Solution:** Choose a unique project key or delete the existing project

#### 3. Template File Not Found
```
FileNotFoundError: [Errno 2] No such file or directory: 'template.yaml'
```
**Solution:** Verify the template file path is correct

#### 4. Partial Deployment
```
Status: failed
Errors: [...]
```
**Solution:** Check tracking file for details, then rollback:
```python
summary = projects.rollback_template_deployment("PROJECT_KEY")

for resource in summary["resources_remaining"]:
    print(f"Left behind: {resource['type']} {resource['name']} - {resource['reason']}")
```

Rollback deletes the project first, then everything that depended on it. Jira does
not release a deleted project's schemes straight away, so refused deletions are
retried for `retry_seconds` (30 by default). Anything still refused is reported in
`resources_remaining`, and the tracking file is kept so the rollback can be run
again later. Custom fields and statuses are never deleted, as they may be shared;
`shared_resources_left` says so explicitly.

### Checking Deployment Status

```python
import os
import json

def check_deployment_status(project_key):
    """Print detailed deployment status."""
    tracking_file = f".jirakit_deployments/{project_key}.json"

    if not os.path.exists(tracking_file):
        print(f"No deployment found for {project_key}")
        return

    with open(tracking_file, 'r') as f:
        data = json.load(f)

    print(f"\nDeployment Status: {project_key}")
    print("=" * 50)
    print(f"Status: {data['status']}")
    print(f"Started: {data['deployment_started']}")
    print(f"Completed: {data['deployment_completed']}")
    print(f"Deployed by: {data['deployed_by']}")
    print(f"\nResources Created:")

    for resource_type, resources in data['resources_created'].items():
        if resources:
            print(f"  {resource_type}: {len(resources)}")

    if data['errors']:
        print(f"\nErrors ({len(data['errors'])}):")
        for error in data['errors']:
            print(f"  - {error['message']}")
            print(f"    at {error['timestamp']}")

# Usage
check_deployment_status("MYPROJ")
```

## Next Steps

- **[Rollback & Recovery Guide](rollback-recovery.md)** - Learn how to rollback deployments
- **[Template Structure Reference](template-structure.md)** - Understand template file format
- **[Tracking System Guide](tracking-system.md)** - Deep dive into deployment tracking
- **[Example Templates](../examples/)** - Ready-to-use template examples

## Related Documentation

- [DeploymentTracker API Reference](../api-reference/deployment-tracker.md)
- [Projects API Reference](../api-reference/projects.md)
