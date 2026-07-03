# Quick Reference Guide

A quick reference for common jirakit operations.

## Installation

```bash
pip install -r requirements.txt
```

## Connection

```python
from jirakit import JiraClient

client = JiraClient(
    url="https://your-instance.atlassian.net/",
    username="your-email@example.com",
    api_token="your-api-token"
)
```

## Template Deployment

### Deploy Template

```python
import yaml

with open('template.yaml', 'r') as f:
    template = yaml.safe_load(f)

project = client.projects().create(
    name="Project Name",
    key="PROJKEY",  # Max 10 chars
    template=template
)
```

### Check Deployment Status

```python
from jirakit.projects.tracking import DeploymentTracker

tracker = DeploymentTracker.load("PROJKEY")
if tracker:
    summary = tracker.get_summary()
    print(f"Status: {summary['status']}")
    print(f"Issue types: {summary['issue_types_created']}")
```

### Rollback Deployment

```python
summary = client.projects().rollback_template_deployment(
    project_key="PROJKEY",
    delete_project=True,
    enable_undo=False
)

print(f"Tracking used: {summary['tracking_file_used']}")
print(f"Project deleted: {summary['project_deleted']}")
```

## Projects

### Get Project

```python
projects = client.projects()
project = projects.get_project("PROJKEY")

print(project.key)
print(project.id)
print(project.name)
```

### Get All Projects

```python
all_projects = projects.get_all(status='live')

for project in all_projects:
    print(f"{project.key}: {project.name}")
```

### Delete Project

```python
projects.delete_project(project, enable_undo=False)
```

## Issue Types

### Get All Issue Types

```python
issue_types = client.issue_types()
all_types = issue_types.get_all_user_issue_types()

for it in all_types:
    print(f"{it.name} (ID: {it.id})")
```

### Create Issue Type

```python
issue_type = issue_types.create(
    name="PROJKEY: Task",
    description="A task to complete",
    is_subtask=False
)
```

### Delete Issue Type

```python
issue_types.delete(issue_type)
```

### Create Issue Type Scheme

```python
scheme = issue_types.create_issue_type_scheme(
    name="PROJKEY: Scheme",
    description="Issue type scheme",
    issue_type_ids=["10001", "10002"]
)
```

## Screens

### Get All Screens

```python
screens = client.screens()
all_screens = screens.get_all_screens()

for screen in all_screens:
    print(f"{screen.name} (ID: {screen.id})")
```

### Create Screen

```python
screen = screens.create(
    name="PROJKEY: Task Screen",
    description="Screen for tasks"
)
```

### Add Tab to Screen

```python
tab = screen.create_tab(
    name="Details",
    field_ids=["summary", "description", "assignee"]
)
```

### Delete Screen

```python
screens.delete_screen(screen)
```

### Create Screen Scheme

```python
scheme = screens.create_screen_scheme(
    name="PROJKEY: Screen Scheme",
    description="Screen scheme",
    default=screen.id,
    edit=screen.id,
    view=screen.id
)
```

## Workflows

### Get All Workflows

```python
workflows = client.workflows()

# Active workflows
active = workflows.get_all(active=True)

# Inactive workflows
inactive = workflows.get_all(active=False)
```

### Create Workflow (via template)

```python
workflow_def = {
    'name': 'Simple Workflow',
    'statuses': [
        {'name': 'To Do', 'category': 'To Do'},
        {'name': 'Done', 'category': 'Done'}
    ],
    'transitions': [
        {
            'name': 'Complete',
            'from': ['To Do'],
            'to': 'Done'
        }
    ]
}

workflow = workflows.create(
    name="PROJKEY: Simple Workflow",
    description="Basic workflow",
    workflow_def=workflow_def,
    project=project
)
```

### Delete Inactive Workflow

```python
workflows.delete_inactive_workflow(workflow)
```

## Fields

### Get All Fields

```python
fields = client.fields()
all_fields = fields.get_all()

for field in all_fields:
    print(f"{field.name} (ID: {field.id})")
```

### Get Field by Name

```python
field = fields.get_field_by_name("Priority")
```

### Get Project Fields

```python
project_fields = project.project_fields

for field in project_fields:
    print(field.name)
```

## Groups

### Create Groups

```python
groups = client.groups()
groups.create_groups(['group-1', 'group-2'])
```

### Get All Groups

```python
all_groups = groups.get_groups()

for group in all_groups:
    print(group.name)
```

## Deployment Tracking

### Create Tracker

```python
from jirakit.projects.tracking import DeploymentTracker

tracker = DeploymentTracker(
    project_key="PROJKEY",
    project_id="10001",
    project_name="My Project",
    template_name="My Template"
)
```

### Track Resources

```python
# Track issue type
tracker.track_issue_type(
    issue_type_id="10001",
    name="PROJKEY: Task"
)

# Track screen
tracker.track_screen(
    screen_id="10001",
    name="PROJKEY: Task Screen"
)

# Track workflow
tracker.track_workflow(
    entity_id="uuid-here",
    name="PROJKEY: Simple Workflow"
)
```

### Mark Status

```python
# Mark completed
tracker.mark_completed()

# Mark failed
tracker.mark_failed()

# Mark partial
tracker.mark_partial()
```

### Track Errors

```python
tracker.track_error("Deployment failed: Connection timeout")
```

### Load Tracker

```python
tracker = DeploymentTracker.load("PROJKEY")

if tracker:
    print(f"Status: {tracker.data['status']}")
    print(f"Resources: {tracker.data['resources_created']}")
else:
    print("No tracking file found")
```

### Get Summary

```python
summary = tracker.get_summary()

# Returns:
{
    'project_key': 'PROJKEY',
    'status': 'completed',
    'started': '2025-10-08T12:00:00',
    'completed': '2025-10-08T12:05:00',
    'custom_fields_created': 0,
    'issue_types_created': 4,
    'screens_created': 2,
    'screen_schemes_created': 2,
    'workflows_created': 2,
    'errors': 0
}
```

### Delete Tracking File

```python
tracker.delete_tracking_file()
```

## Template Structure

### Minimal Template

```yaml
name: "My Template"

groups:
  - name: "project-users"

fields:
  - name: "Summary"

issue_types:
  - name: "Task"
    description: "A task"
    subtask: false

issue_type_schemes:
  - name: "Scheme"
    description: "Issue type scheme"
    issue_types:
      - "Task"

screens:
  - name: "Task Screen"
    description: "Screen for tasks"

screen_tabs:
  - screen: "Task Screen"
    name: "Details"
    fields:
      - "Summary"

screen_schemes:
  - name: "Task Screen Scheme"
    description: "Screen scheme"
    screens:
      default: "Task Screen"

issue_type_screen_schemes:
  - name: "ITSS"
    description: "Issue type screen scheme"
    default_screen_scheme: "Task Screen Scheme"
    mappings:
      - issue_type: "Task"
        screen_scheme: "Task Screen Scheme"

workflows:
  - name: "Simple Workflow"
    description: "Basic workflow"
    statuses:
      - name: "To Do"
        category: "To Do"
      - name: "Done"
        category: "Done"
    transitions:
      - name: "Complete"
        from: ["To Do"]
        to: "Done"

workflow_schemes:
  - name: "Workflow Scheme"
    description: "Workflow scheme"
    defaultWorkflow: "jira"
    issueTypeMappings:
      - issue_type: "Task"
        workflow: "Simple Workflow"
```

## Error Handling

### Basic Error Handling

```python
try:
    project = client.projects().create(
        name="Test",
        key="TEST",
        template=template
    )
except Exception as e:
    print(f"Deployment failed: {e}")

    # Check tracking file
    tracker = DeploymentTracker.load("TEST")
    if tracker:
        for error in tracker.data['errors']:
            print(f"  - {error['message']}")
```

### Rollback After Failure

```python
try:
    project = client.projects().create(
        name="Test",
        key="TEST",
        template=template
    )
except Exception as e:
    print(f"Deployment failed: {e}")

    # Rollback partial deployment
    summary = client.projects().rollback_template_deployment("TEST")

    if summary['project_deleted']:
        print("Cleanup successful")
```

## Logging

### Enable Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

### Log Levels

```python
# DEBUG - Detailed information
logging.basicConfig(level=logging.DEBUG)

# INFO - General information
logging.basicConfig(level=logging.INFO)

# WARNING - Warning messages
logging.basicConfig(level=logging.WARNING)

# ERROR - Errors only
logging.basicConfig(level=logging.ERROR)
```

## Environment Variables

### Secure Configuration

```python
import os
from jirakit import JiraClient

# Set environment variables
os.environ['JIRA_URL'] = "https://your-instance.atlassian.net/"
os.environ['JIRA_USERNAME'] = "your-email@example.com"
os.environ['JIRA_API_TOKEN'] = "your-api-token"

# Use in code
client = JiraClient(
    url=os.environ['JIRA_URL'],
    username=os.environ['JIRA_USERNAME'],
    api_token=os.environ['JIRA_API_TOKEN']
)
```

### .env File

Create `.env` file:
```
JIRA_URL=https://your-instance.atlassian.net/
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-api-token
```

Load with python-dotenv:
```python
from dotenv import load_dotenv
import os

load_dotenv()

client = JiraClient(
    url=os.getenv('JIRA_URL'),
    username=os.getenv('JIRA_USERNAME'),
    api_token=os.getenv('JIRA_API_TOKEN')
)
```

## Common Patterns

### Batch Deploy Multiple Projects

```python
deployments = [
    ("Project 1", "PROJ1", "template1.yaml"),
    ("Project 2", "PROJ2", "template2.yaml"),
    ("Project 3", "PROJ3", "template3.yaml"),
]

results = {'success': [], 'failed': []}

for name, key, template_file in deployments:
    try:
        with open(template_file, 'r') as f:
            template = yaml.safe_load(f)

        project = client.projects().create(name, key, template)
        results['success'].append(key)
    except Exception as e:
        results['failed'].append({'key': key, 'error': str(e)})

print(f"Success: {len(results['success'])}")
print(f"Failed: {len(results['failed'])}")
```

### Cleanup All Test Projects

```python
test_projects = ["TEST1", "TEST2", "TEST3"]

for project_key in test_projects:
    try:
        summary = client.projects().rollback_template_deployment(project_key)
        if summary['project_deleted']:
            print(f"✓ Deleted {project_key}")
        else:
            print(f"✗ Failed to delete {project_key}")
    except Exception as e:
        print(f"✗ Error deleting {project_key}: {e}")
```

### Verify Deployment

```python
def verify_deployment(project_key):
    tracker = DeploymentTracker.load(project_key)

    if not tracker:
        return False, "No tracking file found"

    if tracker.data['status'] != 'completed':
        return False, f"Status: {tracker.data['status']}"

    if tracker.data['errors']:
        return False, f"{len(tracker.data['errors'])} errors occurred"

    return True, "Deployment successful"

# Usage
success, message = verify_deployment("PROJKEY")
if success:
    print(f"✓ {message}")
else:
    print(f"✗ {message}")
```

## Related Documentation

- [Template Deployment Guide](template-deployment.md)
- [Rollback & Recovery Guide](rollback-recovery.md)
- [Template Structure Reference](template-structure.md)
- [Example Templates](../examples/)
