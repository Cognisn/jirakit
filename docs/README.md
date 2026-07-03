# jirakit Documentation

Welcome to the jirakit documentation! This guide will help you get started with template-based Jira project deployment, management, and automation.

## What is jirakit?

jirakit is a Python library that simplifies working with Atlassian Jira Cloud. It provides:

- **Template-Based Deployment**: Deploy complete Jira projects from YAML templates
- **Automatic Tracking**: Track all created resources for precise rollback
- **Rollback & Recovery**: Clean up test projects or recover from failed deployments
- **Simplified API**: Easier-to-use wrapper around Jira Cloud REST API v3
- **Full CRUD Operations**: Manage projects, issues, workflows, screens, and more

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

**Requirements:**
- Python 3.12+
- Jira Cloud instance
- API token for authentication

### 5-Minute Example

```python
from jirakit import JiraClient
import yaml

# Connect to Jira
client = JiraClient(
    url="https://your-instance.atlassian.net/",
    username="your-email@example.com",
    api_token="your-api-token"
)

# Load a template
with open('docs/examples/simple-task-tracker.yaml', 'r') as f:
    template = yaml.safe_load(f)

# Deploy the template
projects = client.projects()
project = projects.create(
    name="Task Tracker",
    key="TASKS",
    template=template
)

print(f"Project created: {project.key}")
print(f"URL: https://your-instance.atlassian.net/browse/{project.key}")
```

That's it! You now have a fully configured Jira project with custom issue types, screens, and workflows.

## Documentation Structure

### Getting Started

- **[Installation & Setup](#installation--setup)** - Get jirakit up and running
- **[Quick Start Guide](#quick-start)** - Deploy your first template in 5 minutes
- **[Authentication](#authentication)** - Connect to Jira Cloud

### User Guides

Comprehensive guides for common tasks:

- **[Release History](releases/README.md)** - Version history and release notes
- **[Template Deployment Guide](guides/template-deployment.md)** - Complete guide to deploying templates
  - Deployment process and workflow
  - Best practices and validation
  - Batch deployments
  - Troubleshooting common issues

- **[Rollback & Recovery Guide](guides/rollback-recovery.md)** - Managing deployments and cleanup
  - Tracking-based vs. fallback rollback
  - Recovery scenarios
  - Best practices for safe rollback
  - Verification and logging

- **[Template Structure Reference](guides/template-structure.md)** - YAML template format
  - Complete structure reference
  - Field definitions and types
  - Naming conventions
  - Validation and development tips

- **[Quick Reference Guide](guides/quick-reference.md)** - Cheat sheet for common operations
  - Installation and connection
  - Template deployment
  - Project management
  - Deployment tracking
  - Common patterns and snippets

### Examples

Ready-to-use templates and code examples:

- **[Example Templates](examples/)** - Pre-built templates
  - Simple Task Tracker (beginner)
  - IT Help Desk (intermediate)
  - Customisation examples

### API Reference

Detailed API documentation for all classes and methods:

- **[API Reference](api-reference/)** - Complete API documentation
  - JiraClient - Main connection class
  - Projects - Project management
  - DeploymentTracker - Deployment tracking (NEW in v0.1.6)
  - IssueTypes - Issue type management
  - And more...

## Installation & Setup

### Prerequisites

1. **Python 3.12 or higher**
   ```bash
   python --version
   ```

2. **Jira Cloud Instance**
   - You need access to a Jira Cloud instance
   - Administrator permissions for creating projects

3. **API Token**
   - Generate from: https://id.atlassian.com/manage-profile/security/api-tokens
   - Keep it secure - treat it like a password

### Installation Steps

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd jirakit
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**
   ```python
   from jirakit import JiraClient

   # Should import without errors
   print("jirakit installed successfully!")
   ```

### First Connection Test

```python
from jirakit import JiraClient

# Replace with your details
client = JiraClient(
    url="https://your-instance.atlassian.net/",
    username="your-email@example.com",
    api_token="your-api-token"
)

# Test connection
me = client.get_me()
print(f"Connected as: {me['displayName']}")
print(f"Email: {me['emailAddress']}")
```

If this runs without errors, you're ready to start deploying templates!

## Authentication

jirakit uses Jira Cloud's API token authentication.

### Creating an API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a meaningful label (e.g., "jirakit Development")
4. Copy the token immediately (you won't be able to see it again)

### Using the API Token

```python
from jirakit import JiraClient

client = JiraClient(
    url="https://your-instance.atlassian.net/",
    username="your-email@example.com",  # Your Atlassian account email
    api_token="your-api-token-here"     # The token you just created
)
```

### Security Best Practices

**DO:**
- Store tokens in environment variables
- Use different tokens for different environments
- Rotate tokens regularly
- Keep tokens out of version control

**DON'T:**
- Commit tokens to Git repositories
- Share tokens in chat or email
- Use the same token across multiple applications

**Example with environment variables:**

```python
import os
from jirakit import JiraClient

client = JiraClient(
    url=os.environ['JIRA_URL'],
    username=os.environ['JIRA_USERNAME'],
    api_token=os.environ['JIRA_API_TOKEN']
)
```

## Core Concepts

### Templates

Templates are YAML files that define complete Jira project configurations:

```yaml
name: "My Template"
description: "A simple template"

groups:
  - name: "project-users"

issue_types:
  - name: "Task"
    description: "A task to complete"
    subtask: false

screens:
  - name: "Task Screen"
    description: "Screen for tasks"

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

# ... and more
```

See [Template Structure Reference](guides/template-structure.md) for complete details.

### Deployment Tracking

Every template deployment creates a tracking file:

```
.jirakit_deployments/
└── PROJECTKEY.json
```

This file contains:
- All resources created (with IDs)
- Deployment metadata
- Timestamps and user information
- Status and any errors

This enables:
- **Precise rollback** - Delete only what was created
- **Partial deployment recovery** - Know exactly what succeeded
- **Audit trail** - Track who deployed what and when

### Rollback

Rollback allows you to completely remove a template-deployed project:

```python
summary = projects.rollback_template_deployment(
    project_key="MYPROJ",
    delete_project=True
)

if summary['tracking_file_used']:
    print("Used tracking file for precise rollback")

if summary['project_deleted']:
    print("Rollback successful!")
```

Two rollback modes:
1. **Tracking-based** (recommended) - Uses tracking file for precision
2. **Fallback** - Searches by project key prefix if no tracking file

## Common Tasks

### Deploy a Template

```python
import yaml
from jirakit import JiraClient

client = JiraClient(url, username, api_token)

with open('template.yaml', 'r') as f:
    template = yaml.safe_load(f)

project = client.projects().create(
    name="My Project",
    key="MYPROJ",
    template=template
)
```

### Check Deployment Status

```python
from jirakit.projects.tracking import DeploymentTracker

tracker = DeploymentTracker.load("MYPROJ")
summary = tracker.get_summary()

print(f"Status: {summary['status']}")
print(f"Issue types: {summary['issue_types_created']}")
print(f"Screens: {summary['screens_created']}")
```

### Rollback a Deployment

```python
summary = client.projects().rollback_template_deployment("MYPROJ")

print(f"Deleted {len(summary['issue_types_deleted'])} issue types")
print(f"Project deleted: {summary['project_deleted']}")
```

### Create a Custom Template

Start with an example and customise:

```python
import yaml

# Load example
with open('docs/examples/simple-task-tracker.yaml', 'r') as f:
    template = yaml.safe_load(f)

# Customise
template['name'] = "My Custom Template"
template['issue_types'].append({
    'name': 'Epic',
    'description': 'Large initiative',
    'subtask': False
})

# Save
with open('my-template.yaml', 'w') as f:
    yaml.dump(template, f)
```

## Project Modules

### JiraClient (`src/jirakit/__init__.py`)

Main client for Jira Cloud interaction.

```python
from jirakit import JiraClient

client = JiraClient(url, username, api_token)

# Get current user
me = client.get_me()

# HTTP methods
response = client.get('/rest/api/3/myself')
response = client.post('/rest/api/3/project', data={...})
```

### Projects (`src/jirakit/projects/`)

Project management and template deployment.

```python
projects = client.projects()

# Get project
project = projects.get_project("MYPROJ")

# Create with template
project = projects.create(name, key, template)

# Rollback
summary = projects.rollback_template_deployment(key)
```

### Issue Types (`src/jirakit/issues/types.py`)

Issue type and scheme management.

```python
issue_types = client.issue_types()

# Create issue type
issue_type = issue_types.create(name, description, is_subtask)

# Create issue type scheme
scheme = issue_types.create_issue_type_scheme(name, description, issue_type_ids)
```

### Screens (`src/jirakit/screens/`)

Screen and screen scheme management.

```python
screens = client.screens()

# Create screen
screen = screens.create(name, description)

# Create screen scheme
scheme = screens.create_screen_scheme(name, description, default_screen_id)
```

### Workflows (`src/jirakit/workflows/`)

Workflow management.

```python
workflows = client.workflows()

# Get all workflows
all_workflows = workflows.get_all(active=True)

# Create workflow (via template)
workflow = workflows.create(name, description, workflow_def, project)
```

### Fields (`src/jirakit/fields/`)

Custom field management.

```python
fields = client.fields()

# Get all fields
all_fields = fields.get_all()

# Get field by name
field = fields.get_field_by_name("Priority")
```

### Groups (`src/jirakit/groups/`)

User group management.

```python
groups = client.groups()

# Create groups
groups.create_groups(['group-1', 'group-2'])

# Get all groups
all_groups = groups.get_groups()
```

## Troubleshooting

### Common Issues

#### Authentication Failed
```
Error: 401 Unauthorized
```
**Solution:** Verify your API token and email address are correct.

#### Project Key Too Long
```
Error: The project key must not exceed 10 characters
```
**Solution:** Use a shorter project key (max 10 characters).

#### Field Not Found
```
Error: Field 'Custom Field' not found
```
**Solution:** Create the field in Jira first, or remove it from the template.

#### Template Deployment Failed
**Solution:** Check the tracking file in `.jirakit_deployments/` for details:
```python
import json

with open('.jirakit_deployments/MYPROJ.json', 'r') as f:
    tracking = json.load(f)

print(f"Status: {tracking['status']}")
print(f"Errors: {tracking['errors']}")
```

### Getting Help

1. **Check the guides** - Detailed information in [guides/](guides/)
2. **Review examples** - Working templates in [examples/](examples/)
3. **Check logs** - Enable Python logging for details:
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   ```
4. **Check tracking files** - Review `.jirakit_deployments/*.json` for deployment details

## Best Practices

### Template Development

1. **Start small** - Begin with simple templates
2. **Test first** - Deploy to test instance before production
3. **Version control** - Keep templates in Git
4. **Document** - Add comments explaining customisations
5. **Validate** - Test rollback before deploying to production

### Deployment

1. **Use descriptive keys** - Choose meaningful project keys
2. **Check tracking** - Verify tracking file after deployment
3. **Log operations** - Enable logging for audit trail
4. **Handle errors** - Check status and errors in tracking file
5. **Test rollback** - Verify rollback works in test environment

### Security

1. **Protect tokens** - Use environment variables
2. **Rotate regularly** - Change API tokens periodically
3. **Limit permissions** - Use dedicated service accounts
4. **Audit access** - Review who has access to tokens
5. **Secure tracking files** - Don't commit to public repositories

## Version Information

**Current Version:** 0.1.7

**Latest Release:** [v0.1.7](releases/v0.1.7.md) - 9 October 2025
- Fixed deprecated Jira API search endpoint (410 Gone error)
- Migrated to POST `/rest/api/3/search/jql` endpoint

**[View Complete Release History](releases/README.md)**

**API Compatibility:** Jira Cloud REST API v3

## Contributing

Contributions are welcome! Areas where help is needed:

- Additional example templates
- API reference documentation
- Unit test coverage
- Bug fixes and improvements

Please ensure:
- Australian English spelling in documentation
- Tests in `./tests/`
- Documentation updates for new features

## License

This project is licensed under the MIT License.

## Additional Resources

- [Jira Cloud REST API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
- [YAML Syntax Guide](https://yaml.org/spec/1.2/spec.html)

---

**Need help?** Check the [guides](guides/), review [examples](examples/), or open an issue in the repository.
