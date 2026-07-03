# Rollback & Recovery Guide

This guide explains how to safely rollback and clean up Jira projects created from templates.

## Overview

The rollback system allows you to:

- Completely remove a template-deployed project
- Delete all associated resources (issue types, screens, workflows, etc.)
- Recover from failed or partial deployments
- Clean up test deployments

The system uses deployment tracking files to ensure precise deletion of only the resources that were created during deployment.

## Quick Start

### Basic Rollback

```python
from jirakit import JiraClient

# Connect to Jira
client = JiraClient(
    url="https://your-instance.atlassian.net/",
    username="your-email@example.com",
    api_token="your-api-token"
)

# Rollback the deployment
projects = client.projects()
summary = projects.rollback_template_deployment(
    project_key="MYPROJ",
    delete_project=True,
    enable_undo=False
)

# Check results
if summary['project_deleted']:
    print("Rollback successful!")
else:
    print(f"Rollback completed with {len(summary['errors'])} errors")
```

### With Detailed Reporting

```python
from jirakit import JiraClient
import logging

logging.basicConfig(level=logging.INFO)

def rollback_with_report(project_key):
    """
    Rollback a deployment and provide detailed report.

    :param project_key: The project key to rollback
    :return: Summary dictionary
    """
    client = JiraClient(
        url="https://your-instance.atlassian.net/",
        username="your-email@example.com",
        api_token="your-api-token"
    )

    projects = client.projects()

    print(f"Rolling back project: {project_key}")
    print("=" * 50)

    summary = projects.rollback_template_deployment(
        project_key=project_key,
        delete_project=True,
        enable_undo=False
    )

    # Print detailed summary
    print(f"\nTracking file used: {summary['tracking_file_used']}")
    print("\nResources Deleted:")
    print(f"  Issue Types: {len(summary['issue_types_deleted'])}")
    for item in summary['issue_types_deleted']:
        print(f"    - {item}")

    print(f"  Issue Type Schemes: {len(summary['issue_type_schemes_deleted'])}")
    print(f"  Screens: {len(summary['screens_deleted'])}")
    print(f"  Screen Schemes: {len(summary['screen_schemes_deleted'])}")
    print(f"  Issue Type Screen Schemes: {len(summary['issue_type_screen_schemes_deleted'])}")
    print(f"  Workflows: {len(summary['workflows_deleted'])}")
    print(f"  Workflow Schemes: {len(summary['workflow_schemes_deleted'])}")
    print(f"  Project: {summary['project_deleted']}")

    if summary['errors']:
        print(f"\nWarnings ({len(summary['errors'])}):")
        for error in summary['errors']:
            print(f"  - {error}")

    return summary

# Usage
summary = rollback_with_report("MYPROJ")
```

## Rollback Methods

### Tracking-Based Rollback (Recommended)

Uses the deployment tracking file for precise resource deletion.

**Advantages:**
- Precise - only deletes resources created during deployment
- Fast - no need to search through all Jira resources
- Safe - tracks exactly what was created
- Works for partial deployments

```python
# Requires tracking file: .jirakit_deployments/{PROJECT_KEY}.json
summary = projects.rollback_template_deployment(
    project_key="MYPROJ"
)
```

### Fallback Search-Based Rollback

If no tracking file exists, the system falls back to searching for resources by project key prefix.

**Characteristics:**
- Searches all Jira resources
- Deletes resources with matching project key prefix
- Slower than tracking-based rollback
- May miss resources or find unexpected ones

```python
# Works even without tracking file
# Searches for resources named: "MYPROJ: *"
summary = projects.rollback_template_deployment(
    project_key="MYPROJ"
)
```

## Rollback Options

### delete_project

Controls whether the project itself is deleted.

```python
# Delete everything including project (default)
summary = projects.rollback_template_deployment(
    project_key="MYPROJ",
    delete_project=True
)

# Delete only resources, keep project
summary = projects.rollback_template_deployment(
    project_key="MYPROJ",
    delete_project=False
)
```

**Use Cases for delete_project=False:**
- Remove template resources but keep project for redeployment
- Clean up before applying a different template
- Troubleshooting - inspect project after resource cleanup

### enable_undo

Controls whether project deletion can be undone in Jira.

```python
# Allow undo (available in Jira trash for 60 days)
summary = projects.rollback_template_deployment(
    project_key="MYPROJ",
    delete_project=True,
    enable_undo=True
)

# Permanent deletion (default)
summary = projects.rollback_template_deployment(
    project_key="MYPROJ",
    delete_project=True,
    enable_undo=False
)
```

**Note:** enable_undo only affects the project deletion, not the resource deletions.

### tracking_dir

Specifies custom location for tracking files.

```python
# Use custom tracking directory
summary = projects.rollback_template_deployment(
    project_key="MYPROJ",
    tracking_dir="./custom_tracking"
)

# Default is: .jirakit_deployments/
summary = projects.rollback_template_deployment(
    project_key="MYPROJ"
)
```

## Deletion Order

Resources are deleted in reverse order of creation to respect dependencies:

1. **Workflow Schemes** - Tracked (auto-deleted with project)
2. **Workflows** - Inactive workflows only (active deleted with project)
3. **Issue Type Screen Schemes** - Explicit deletion
4. **Screen Schemes** - Explicit deletion
5. **Screens** - Explicit deletion
6. **Issue Type Schemes** - Tracked (auto-deleted with project)
7. **Issue Types** - Explicit deletion
8. **Project** - If delete_project=True

**Note:** Some resources (like screens) may fail to delete explicitly because they're automatically cleaned up when the project is deleted. These failures are expected and non-critical.

## What Gets Deleted vs. Preserved

### Deleted Resources

Resources created specifically for the project:

- ✓ Custom issue types (prefixed with project key)
- ✓ Issue type schemes
- ✓ Screens (prefixed with project key)
- ✓ Screen schemes
- ✓ Issue type screen schemes
- ✓ Workflows (prefixed with project key)
- ✓ Workflow schemes
- ✓ The project itself (if delete_project=True)

### Preserved Resources

Shared resources that may be used by multiple projects:

- ✗ Groups (may be used by other projects)
- ✗ Custom fields (may be used by other projects)
- ✗ Global Jira settings

## Recovery Scenarios

### Scenario 1: Failed Deployment

Deployment fails partway through.

```python
from jirakit import JiraClient

# Deployment failed
try:
    project = projects.create(name="Test", key="TEST", template=template)
except Exception as e:
    print(f"Deployment failed: {e}")

    # Check tracking file
    from jirakit.projects.tracking import DeploymentTracker
    tracker = DeploymentTracker.load("TEST")

    if tracker:
        print(f"Status: {tracker.data['status']}")
        print(f"Errors: {len(tracker.data['errors'])}")

        # Rollback partial deployment
        summary = projects.rollback_template_deployment("TEST")

        if summary['project_deleted']:
            print("Partial deployment cleaned up successfully")
```

### Scenario 2: Clean Up Test Projects

Remove multiple test deployments.

```python
def cleanup_test_projects(test_keys):
    """
    Clean up multiple test projects.

    :param test_keys: List of project keys to remove
    :return: Results summary
    """
    client = JiraClient(url, username, api_token)
    projects = client.projects()

    results = {'successful': [], 'failed': []}

    for key in test_keys:
        try:
            summary = projects.rollback_template_deployment(key)

            if summary['project_deleted']:
                results['successful'].append(key)
            else:
                results['failed'].append({
                    'key': key,
                    'errors': summary['errors']
                })

        except Exception as e:
            results['failed'].append({
                'key': key,
                'errors': [str(e)]
            })

    return results

# Clean up test projects
test_projects = ["TEST1", "TEST2", "TEST3"]
results = cleanup_test_projects(test_projects)

print(f"Cleaned up: {len(results['successful'])}")
print(f"Failed: {len(results['failed'])}")
```

### Scenario 3: Reapply Template

Remove existing template deployment and redeploy with updated template.

```python
def redeploy_template(project_key, project_name, new_template):
    """
    Redeploy a template to an existing project.

    :param project_key: Existing project key
    :param project_name: Project name
    :param new_template: New template to apply
    :return: New project object
    """
    client = JiraClient(url, username, api_token)
    projects = client.projects()

    # Step 1: Rollback existing deployment
    print(f"Rolling back {project_key}...")
    summary = projects.rollback_template_deployment(
        project_key=project_key,
        delete_project=True  # Must delete to recreate
    )

    if not summary['project_deleted']:
        raise Exception(f"Failed to rollback {project_key}")

    # Step 2: Deploy new template
    print(f"Deploying new template...")
    project = projects.create(
        name=project_name,
        key=project_key,
        template=new_template
    )

    print(f"Redeployment successful: {project.key}")
    return project

# Usage
import yaml
with open('updated-template.yaml', 'r') as f:
    new_template = yaml.safe_load(f)

project = redeploy_template("MYPROJ", "My Project", new_template)
```

### Scenario 4: Migrate to Different Template

Preserve project but change template configuration.

```python
def migrate_template(project_key, new_template):
    """
    Migrate project to different template configuration.

    :param project_key: Existing project key
    :param new_template: New template to apply
    :return: Updated project object
    """
    client = JiraClient(url, username, api_token)
    projects = client.projects()

    # Step 1: Remove old template resources (keep project)
    print(f"Removing old template resources from {project_key}...")
    summary = projects.rollback_template_deployment(
        project_key=project_key,
        delete_project=False  # Keep the project
    )

    # Step 2: Get existing project
    project = projects.get_project(project_key)

    # Step 3: Apply new template configuration manually
    # Note: This requires manual implementation as create() expects
    # to create a new project. You would need to manually call
    # the individual resource creation methods.

    print(f"Migration completed for {project_key}")
    return project

# Usage - requires additional implementation
# project = migrate_template("MYPROJ", new_template)
```

## Best Practices

### Confirmation Before Rollback

```python
def confirm_rollback(project_key):
    """Request user confirmation before rollback."""
    from jirakit.projects.tracking import DeploymentTracker

    # Show what will be deleted
    tracker = DeploymentTracker.load(project_key)

    if tracker:
        summary = tracker.get_summary()
        print(f"\nRollback will delete:")
        print(f"  - {summary['issue_types_created']} issue types")
        print(f"  - {summary['screens_created']} screens")
        print(f"  - {summary['workflows_created']} workflows")
        print(f"  - The project itself")
    else:
        print(f"\nNo tracking file found.")
        print(f"Will search for resources with prefix: {project_key}:")

    response = input(f"\nDelete project {project_key}? (yes/no): ")
    return response.lower() == 'yes'

# Usage
if confirm_rollback("MYPROJ"):
    summary = projects.rollback_template_deployment("MYPROJ")
else:
    print("Rollback cancelled")
```

### Logging Rollback Actions

```python
import logging
from datetime import datetime

def logged_rollback(project_key, log_file="rollback.log"):
    """Rollback with detailed logging."""

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    logging.info(f"Starting rollback for {project_key}")

    try:
        client = JiraClient(url, username, api_token)
        projects = client.projects()

        summary = projects.rollback_template_deployment(project_key)

        # Log results
        logging.info(f"Tracking file used: {summary['tracking_file_used']}")
        logging.info(f"Issue types deleted: {len(summary['issue_types_deleted'])}")
        logging.info(f"Screens deleted: {len(summary['screens_deleted'])}")
        logging.info(f"Project deleted: {summary['project_deleted']}")

        if summary['errors']:
            logging.warning(f"Errors: {len(summary['errors'])}")
            for error in summary['errors']:
                logging.warning(f"  {error}")

        logging.info("Rollback completed")
        return summary

    except Exception as e:
        logging.error(f"Rollback failed: {e}")
        raise

# Usage
summary = logged_rollback("MYPROJ")
```

### Backup Before Rollback

```python
import json
import shutil
from datetime import datetime

def backup_and_rollback(project_key):
    """Create backup of tracking file before rollback."""

    tracking_file = f".jirakit_deployments/{project_key}.json"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f".jirakit_deployments/backups/{project_key}_{timestamp}.json"

    # Create backup directory
    os.makedirs(".jirakit_deployments/backups", exist_ok=True)

    # Backup tracking file
    if os.path.exists(tracking_file):
        shutil.copy2(tracking_file, backup_file)
        print(f"Tracking file backed up to: {backup_file}")

    # Perform rollback
    client = JiraClient(url, username, api_token)
    projects = client.projects()

    summary = projects.rollback_template_deployment(project_key)

    # Log backup location
    if summary['project_deleted']:
        print(f"Rollback successful. Backup: {backup_file}")

    return summary

# Usage
summary = backup_and_rollback("MYPROJ")
```

## Troubleshooting

### Common Issues

#### 1. Resource Still In Use
```
Error: 400 Bad Request - Screen is in use by active screens schemes
```
**Cause:** Resource is being used by other projects or schemes
**Solution:** This is expected for some resources - they'll be cleaned up when the project is deleted

#### 2. No Tracking File
```
WARNING: No tracking file found for MYPROJ. Using fallback search by naming convention.
```
**Cause:** Tracking file missing or deleted
**Solution:** Rollback will use search-based fallback. Verify resources manually after rollback.

#### 3. Partial Deletion
```
Project deleted: False
Errors: [...]
```
**Cause:** Some resources couldn't be deleted
**Solution:** Review errors, manually delete remaining resources, or retry rollback

### Verification After Rollback

```python
def verify_rollback(project_key):
    """Verify project and resources are deleted."""
    client = JiraClient(url, username, api_token)

    # Check project
    try:
        project = client.projects().get_project(project_key)
        print(f"WARNING: Project {project_key} still exists!")
        return False
    except:
        print(f"✓ Project {project_key} deleted")

    # Check tracking file
    tracking_file = f".jirakit_deployments/{project_key}.json"
    if os.path.exists(tracking_file):
        print(f"WARNING: Tracking file still exists: {tracking_file}")
        return False
    else:
        print(f"✓ Tracking file deleted")

    # Check issue types
    issue_types = client.issue_types().get_all_user_issue_types()
    remaining = [it for it in issue_types if it.name.startswith(f"{project_key}:")]

    if remaining:
        print(f"WARNING: {len(remaining)} issue types still exist:")
        for it in remaining:
            print(f"  - {it.name}")
        return False
    else:
        print(f"✓ No issue types remaining")

    print(f"\nRollback verification: PASSED")
    return True

# Usage
verify_rollback("MYPROJ")
```

## Summary Return Object

The `rollback_template_deployment()` method returns a dictionary:

```python
{
    'issue_types_deleted': ['MYPROJ: Task', ...],
    'issue_type_schemes_deleted': ['MYPROJ: Scheme', ...],
    'screens_deleted': ['MYPROJ: Screen', ...],
    'screen_schemes_deleted': ['MYPROJ: Screen Scheme', ...],
    'issue_type_screen_schemes_deleted': ['MYPROJ: ITSS', ...],
    'workflows_deleted': ['MYPROJ: Workflow', ...],
    'workflow_schemes_deleted': ['MYPROJ: Workflow Scheme', ...],
    'project_deleted': True,
    'tracking_file_used': True,
    'errors': []
}
```

## Related Documentation

- [Template Deployment Guide](template-deployment.md)
- [Tracking System Guide](tracking-system.md)
- [DeploymentTracker API Reference](../api-reference/deployment-tracker.md)
