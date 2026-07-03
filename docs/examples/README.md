# Template Examples

This directory contains example templates demonstrating various use cases and complexity levels.

## Available Templates

### [simple-task-tracker.yaml](simple-task-tracker.yaml)

**Complexity:** Beginner

A minimal template for basic task and bug tracking.

**Features:**
- 2 issue types (Task, Bug)
- Single screen for all issue types
- Simple 3-state workflow (To Do → In Progress → Done)
- Basic fields (Summary, Description, Assignee, Priority)

**Best for:**
- Learning template structure
- Small teams
- Simple project tracking
- Rapid prototyping

**Deploy:**
```python
from jirakit import JiraClient
import yaml

client = JiraClient(url, username, api_token)

with open('docs/examples/simple-task-tracker.yaml', 'r') as f:
    template = yaml.safe_load(f)

project = client.projects().create(
    name="Task Tracker",
    key="TASKS",
    template=template
)
```

### [help-desk-template.yaml](help-desk-template.yaml)

**Complexity:** Intermediate

A comprehensive IT help desk template with multiple issue types and workflows.

**Features:**
- 4 issue types (Service Request, Incident, Problem, Change Request)
- Dedicated screens for each issue type
- Custom workflows for each type
- Help desk specific fields (Affected Services, Time to Resolution, etc.)
- Different status flows for different request types

**Best for:**
- IT service desks
- Support teams
- ITIL-based processes
- Multi-tier support structures

**Deploy:**
```python
from jirakit import JiraClient
import yaml

client = JiraClient(url, username, api_token)

with open('docs/examples/help-desk-template.yaml', 'r') as f:
    template = yaml.safe_load(f)

project = client.projects().create(
    name="IT Help Desk",
    key="HELPDESK",
    template=template
)
```

## Usage Examples

### Deploy and Verify

```python
from jirakit import JiraClient
from jirakit.projects.tracking import DeploymentTracker
import yaml

# Connect
client = JiraClient(
    url="https://your-instance.atlassian.net/",
    username="your-email@example.com",
    api_token="your-api-token"
)

# Load template
with open('docs/examples/simple-task-tracker.yaml', 'r') as f:
    template = yaml.safe_load(f)

# Deploy
project_key = "TASKS"
project = client.projects().create(
    name="Task Tracker",
    key=project_key,
    template=template
)

print(f"Project created: {project.key} (ID: {project.id})")

# Verify deployment
tracker = DeploymentTracker.load(project_key)
summary = tracker.get_summary()

print(f"\nDeployment Summary:")
print(f"  Status: {summary['status']}")
print(f"  Issue types: {summary['issue_types_created']}")
print(f"  Screens: {summary['screens_created']}")
print(f"  Workflows: {summary['workflows_created']}")
```

### Compare Templates

```python
import yaml

def compare_templates(template1_path, template2_path):
    """Compare complexity of two templates."""
    with open(template1_path, 'r') as f:
        t1 = yaml.safe_load(f)
    with open(template2_path, 'r') as f:
        t2 = yaml.safe_load(f)

    print(f"Template Comparison:")
    print(f"\n{t1['name']}:")
    print(f"  Issue Types: {len(t1.get('issue_types', []))}")
    print(f"  Screens: {len(t1.get('screens', []))}")
    print(f"  Workflows: {len(t1.get('workflows', []))}")

    print(f"\n{t2['name']}:")
    print(f"  Issue Types: {len(t2.get('issue_types', []))}")
    print(f"  Screens: {len(t2.get('screens', []))}")
    print(f"  Workflows: {len(t2.get('workflows', []))}")

compare_templates(
    'docs/examples/simple-task-tracker.yaml',
    'docs/examples/help-desk-template.yaml'
)
```

### Customize a Template

```python
import yaml

# Load base template
with open('docs/examples/simple-task-tracker.yaml', 'r') as f:
    template = yaml.safe_load(f)

# Customize
template['name'] = "Custom Task Tracker"

# Add new issue type
template['issue_types'].append({
    'name': 'Epic',
    'description': 'Large feature or initiative',
    'subtask': False
})

# Add to scheme
template['issue_type_schemes'][0]['issue_types'].append('Epic')

# Add to screen mapping
template['issue_type_screen_schemes'][0]['mappings'].append({
    'issue_type': 'Epic',
    'screen_scheme': 'Task Screen Scheme'
})

# Add to workflow mapping
template['workflow_schemes'][0]['issueTypeMappings'].append({
    'issue_type': 'Epic',
    'workflow': 'Simple Task Workflow'
})

# Save customised template
with open('my-custom-template.yaml', 'w') as f:
    yaml.dump(template, f, default_flow_style=False, sort_keys=False)

print("Customised template saved to: my-custom-template.yaml")
```

### Test Deployment and Rollback

```python
from jirakit import JiraClient
import yaml

client = JiraClient(url, username, api_token)
projects = client.projects()

# Load template
with open('docs/examples/simple-task-tracker.yaml', 'r') as f:
    template = yaml.safe_load(f)

# Deploy test project
test_key = "TEST123"

try:
    print("Deploying test project...")
    project = projects.create(
        name="Test Project",
        key=test_key,
        template=template
    )
    print(f"Deployed: {project.key}")

    # Test the project (manual verification)
    input("Press Enter to rollback...")

except Exception as e:
    print(f"Deployment failed: {e}")

finally:
    # Rollback
    print("Rolling back...")
    summary = projects.rollback_template_deployment(test_key)

    if summary['project_deleted']:
        print("Rollback successful!")
    else:
        print(f"Rollback had {len(summary['errors'])} errors")
```

## Creating Your Own Template

### Start from an Example

1. Copy an example template:
   ```bash
   cp docs/examples/simple-task-tracker.yaml my-template.yaml
   ```

2. Modify the template:
   - Update `name` and `description`
   - Add/remove issue types
   - Customize screens and fields
   - Adjust workflows

3. Test deployment:
   ```python
   with open('my-template.yaml', 'r') as f:
       template = yaml.safe_load(f)

   project = client.projects().create(
       name="My Project",
       key="MYPROJ",
       template=template
   )
   ```

### Template Development Workflow

1. **Design** - Plan issue types, workflows, and screens
2. **Draft** - Create YAML file based on examples
3. **Test** - Deploy to test Jira instance
4. **Verify** - Check all resources created correctly
5. **Iterate** - Rollback and refine template
6. **Document** - Add comments explaining customisations
7. **Deploy** - Use in production

### Validation Checklist

Before deploying a custom template:

- [ ] All required sections present
- [ ] Issue type names are descriptive
- [ ] Screen tabs include necessary fields
- [ ] Workflow transitions are logical
- [ ] All references resolve correctly
- [ ] No duplicate names
- [ ] Tested in non-production environment
- [ ] Rollback tested

## Troubleshooting

### Field Not Found

```
Error: Field 'Custom Field' not found
```

**Solution:** The field must exist in Jira before deployment. Create it first or remove from template.

### Invalid Workflow Transition

```
Error: Transition from 'Done' to 'Open' not defined
```

**Solution:** Verify transition definitions match status names exactly.

### Screen Tab Empty

**Issue:** Screen shows but has no fields

**Solution:** Check that field names in `screen_tabs` match exactly as they appear in Jira.

## Next Steps

- [Template Structure Reference](../guides/template-structure.md) - Detailed template format documentation
- [Template Deployment Guide](../guides/template-deployment.md) - Full deployment guide
- [Rollback & Recovery](../guides/rollback-recovery.md) - How to rollback deployments

## Contributing

Have a useful template to share? Consider submitting it as an example! Ideal contributions:

- Demonstrate unique use cases
- Are well-documented
- Include deployment examples
- Have been tested successfully
