# jirakit

**Template-based Jira Cloud project deployment and management**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Jira Cloud API v3](https://img.shields.io/badge/Jira%20API-v3-blue.svg)](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

jirakit is a Python library that simplifies Jira Cloud automation by providing template-based project deployment with automatic tracking and rollback capabilities. Deploy complete Jira projects from YAML templates, including custom issue types, workflows, screens, and configurations.

jirakit is pure Python with no external runtime dependencies beyond its listed packages. See [CHANGELOG.md](CHANGELOG.md) for version history.

## Key Features

✨ **Template-Based Deployment** - Deploy complete Jira projects from YAML configuration files
📊 **Automatic Tracking** - Track all created resources with deployment metadata
🔄 **Precision Rollback** - Clean up test projects or recover from failed deployments
🛡️ **Safe & Reliable** - Fallback mechanisms and comprehensive error handling
🚀 **Simple API** - Intuitive wrapper around Jira Cloud REST API v3
📝 **Comprehensive Docs** - Detailed guides, examples, and API reference

## Quick Start

### Installation

```bash
pip install git+https://github.com/Cognisn/jirakit.git
```

Publication to PyPI is planned, after which this becomes `pip install jirakit`.

For development:

```bash
git clone https://github.com/Cognisn/jirakit.git
cd jirakit
pip install -e .
```

**Requirements:** Python 3.12+

### 5-Minute Example

```python
from jirakit import JiraClient
import yaml

# Connect to Jira Cloud (the API token is used as the basic auth password)
client = JiraClient(
    url="https://your-instance.atlassian.net/",
    username="your-email@example.com",
    password="your-api-token"
)

# Load a template
with open('docs/examples/simple-task-tracker.yaml', 'r') as f:
    template = yaml.safe_load(f)

# Deploy the template
project = client.projects().create(
    name="Task Tracker",
    key="TASKS",
    template=template
)

print(f"✓ Project created: {project.key}")
```

**That's it!** You now have a fully configured Jira project with:
- Custom issue types
- Configured screens and fields
- Custom workflows
- Screen schemes and mappings

### Rollback When Needed

```python
# Clean up test projects or recover from failed deployments
summary = client.projects().rollback_template_deployment(
    project_key="TASKS",
    delete_project=True
)

print(f"✓ Rolled back {len(summary['issue_types_deleted'])} issue types")
print(f"✓ Project deleted: {summary['project_deleted']}")
```

## What Makes jirakit Different?

### Deployment Tracking

Every deployment automatically creates a tracking file capturing:
- All resources created (with IDs)
- Deployment metadata (who, when, what template)
- Status tracking (in_progress, completed, failed)
- Error logging

This enables precise rollback even for partial deployments.

### Two Rollback Modes

1. **Tracking-based** (recommended) - Uses tracking file for exact resource deletion
2. **Fallback mode** - Searches by project key prefix if no tracking file exists

### Template-Driven Configuration

Define your entire Jira project in YAML:

```yaml
name: "IT Help Desk"

issue_types:
  - name: "Incident"
    description: "Service interruption"
    subtask: false

workflows:
  - name: "Incident Workflow"
    statuses:
      - name: "New"
      - name: "Investigating"
      - name: "Resolved"
    transitions:
      - name: "Start Investigation"
        from: ["New"]
        to: "Investigating"
```

See [template examples](docs/examples/) for complete templates.

## Documentation

**📚 [Complete Documentation](docs/README.md)** - Start here for detailed guides

### Quick Links

- **[Installation & Setup](docs/README.md#installation--setup)** - Get up and running
- **[Release History](docs/releases/README.md)** - Version history and release notes
- **[Quick Reference](docs/guides/quick-reference.md)** - Cheat sheet for common operations
- **[Template Deployment Guide](docs/guides/template-deployment.md)** - Deploy templates with confidence
- **[Rollback & Recovery Guide](docs/guides/rollback-recovery.md)** - Manage deployments safely
- **[Template Structure Reference](docs/guides/template-structure.md)** - YAML format documentation
- **[API Reference](docs/api-reference/)** - Complete API documentation
- **[Example Templates](docs/examples/)** - Ready-to-use templates

## Use Cases

### Development & Testing
- Quickly spin up test projects
- Clean up after integration tests
- Test configuration changes safely

### Project Standardisation
- Deploy consistent project configurations
- Enforce organisational standards
- Replicate successful project setups

### Migration & Cloning
- Migrate project configurations
- Clone project structures
- Template existing projects for reuse

### Disaster Recovery
- Rollback failed deployments
- Recover from partial deployments
- Audit deployment history

## Example Templates

### Simple Task Tracker
Perfect for small teams or personal projects.
```yaml
# 2 issue types (Task, Bug)
# Simple 3-state workflow
# Basic fields and screens
```
[View Template](docs/examples/simple-task-tracker.yaml)

### IT Help Desk
Comprehensive help desk with ITIL-based workflows.
```yaml
# 4 issue types (Service Request, Incident, Problem, Change)
# Custom workflows for each type
# Help desk specific fields
```
[View Template](docs/examples/help-desk-template.yaml)

## Core Modules

| Module | Purpose |
|--------|---------|
| **JiraClient** | Main client for Jira Cloud connection |
| **Projects** | Project CRUD and template deployment |
| **DeploymentTracker** | Deployment tracking and rollback |
| **IssueTypes** | Issue type and scheme management |
| **Screens** | Screen and screen scheme management |
| **Workflows** | Workflow creation and management |
| **Fields** | Custom field management |
| **Groups** | User group management |

## Requirements

### Python Packages
- `requests` - HTTP client
- `pyyaml` - YAML parsing
- `jira` - Atlassian Jira client
- `marklassian` - Markdown to ADF conversion (pure Python)

### Jira Requirements
- Jira Cloud instance
- Administrator permissions
- API token for authentication

## API Compatibility

**Jira Cloud REST API v3** - Exclusively uses the latest API version

All endpoints have been verified against the v3 specification:
- ✓ Project management
- ✓ Issue types and schemes
- ✓ Screen and screen schemes
- ✓ Workflow management
- ✓ Field operations
- ✓ User and group management

## Testing

Comprehensive test suite: 132 tests, all passing, fully offline (every HTTP interaction is mocked).

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/jirakit

# Run specific test file
pytest tests/test_projects.py
```

See [tests/README.md](tests/README.md) for detailed test documentation.

## Project Structure

```
jirakit/
├── src/jirakit/              # Source code
│   ├── __init__.py          # JiraClient
│   ├── projects/            # Project operations
│   │   ├── __init__.py      # Template deployment
│   │   └── tracking.py      # Deployment tracking
│   ├── issues/              # Issue management
│   ├── screens/             # Screen management
│   ├── workflows/           # Workflow management
│   ├── fields/              # Field management
│   └── groups/              # Group management
├── docs/                    # Documentation
│   ├── README.md            # Documentation index
│   ├── guides/              # User guides
│   └── examples/            # Example templates
├── tests/                   # Test suite
│   ├── test_*.py            # Unit tests
│   ├── index.md             # Test index
│   └── README.md            # Test documentation
├── samples/                 # Examples
├── scripts/                 # Project scripts (version management)
└── CHANGELOG.md             # Version history
```

## Contributing

Contributions are welcome! Please ensure:

- Australian English spelling in all documentation
- Tests added to `./tests/` for new features
- Documentation updated in `./docs/`
- Code follows existing patterns

## Recent Updates

**v0.2.0** (3 July 2026)
- Renamed from `dtJira` to `jirakit` and migrated into a clean Cognisn-owned project
- Relicensed under MIT (Copyright Cognisn)

Since 0.2.0, on `main`: import-time side effects removed (no more Node.js checks or installs at import), Markdown to ADF conversion moved to pure Python via `marklassian` (Node.js requirement dropped entirely), and configurable request timeouts added to `JiraClient`.

**[View Complete Release History](CHANGELOG.md)** (pre-rename dtJira history: [docs/releases](docs/releases/README.md))

## License

This project is licensed under the MIT License. See [LICENCE.txt](LICENCE.txt) for details.

## Trademark Notice

jirakit is an independent open-source project. It is not affiliated with, endorsed by, or sponsored by Atlassian. Jira is a registered trademark of Atlassian Corporation Pty Ltd.

## Support

- **📖 Documentation:** [docs/README.md](docs/README.md)
- **💡 Examples:** [docs/examples/](docs/examples/)
- **🐛 Issues:** Open an issue in the repository
- **📧 Questions:** Check the guides or open a discussion

## Authentication

jirakit uses API token authentication with Jira Cloud.

### Generate an API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a label (e.g., "jirakit Development")
4. Copy and securely store the token

### Security Best Practices

```python
import os
from jirakit import JiraClient

# Use environment variables
client = JiraClient(
    url=os.environ['JIRA_URL'],
    username=os.environ['JIRA_USERNAME'],
    password=os.environ['JIRA_API_TOKEN']
)

# Optionally tune request timeouts (defaults to 10 s connect, 60 s read)
client = JiraClient(
    url=os.environ['JIRA_URL'],
    username=os.environ['JIRA_USERNAME'],
    password=os.environ['JIRA_API_TOKEN'],
    timeout=(5.0, 30.0)
)
```

**Never** commit API tokens to version control!

## Links

- [Complete Documentation](docs/README.md)
- [Release History](docs/releases/README.md)
- [Quick Reference](docs/guides/quick-reference.md)
- [Template Deployment Guide](docs/guides/template-deployment.md)
- [Rollback & Recovery Guide](docs/guides/rollback-recovery.md)
- [Template Structure Reference](docs/guides/template-structure.md)
- [API Reference](docs/api-reference/)
- [Example Templates](docs/examples/)
- [Jira Cloud API Documentation](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)

---

**Ready to get started?** Check out the [documentation](docs/README.md) or try an [example template](docs/examples/)!
