# Template File Structure Reference

This guide documents the YAML template file structure used for Jira project deployments.

## Overview

Templates are YAML files that define complete Jira project configurations including:
- Project metadata
- Groups and permissions
- Custom fields
- Issue types
- Screens and screen schemes
- Workflows and workflow schemes

## Basic Template Structure

```yaml
name: "Template Name"
description: "Template description"

groups:
  - ...

fields:
  - ...

issue_types:
  - ...

issue_type_schemes:
  - ...

screens:
  - ...

screen_tabs:
  - ...

screen_schemes:
  - ...

issue_type_screen_schemes:
  - ...

workflows:
  - ...

workflow_schemes:
  - ...
```

## Top-Level Fields

### name (required)

The template name for identification and tracking.

```yaml
name: "IT Service Desk Template"
```

### description (optional)

Human-readable description of the template.

```yaml
description: "Standard IT service desk with incident, problem, and change management"
```

## groups

Defines Jira groups to be created. Groups are shared resources.

```yaml
groups:
  - name: "it-service-desk-users"
  - name: "it-service-desk-administrators"
  - name: "it-service-desk-agents"
```

**Note:** Groups are created but NOT tracked for rollback as they may be shared across projects.

## fields

Defines custom fields to assign to the project.

```yaml
fields:
  - name: "Priority Level"
  - name: "Service Category"
  - name: "Affected Users"
  - name: "Resolution Notes"
```

**Note:** Fields must already exist in Jira. This section assigns existing fields to the project. Fields are NOT tracked for rollback.

## issue_types

Defines custom issue types to create.

```yaml
issue_types:
  - name: "Service Request"
    description: "Standard service request from users"
    subtask: false

  - name: "Incident"
    description: "Unplanned interruption or reduction in quality of service"
    subtask: false

  - name: "Problem"
    description: "Root cause of one or more incidents"
    subtask: false
```

**Fields:**
- `name` (required): Issue type name (will be prefixed with project key)
- `description` (required): Issue type description
- `subtask` (required): Boolean, whether this is a subtask type

**Created as:** `{PROJECT_KEY}: {name}`
**Example:** For project "ITSD", creates "ITSD: Service Request"

## issue_type_schemes

Maps issue types into schemes.

```yaml
issue_type_schemes:
  - name: "IT Service Desk Issue Type Scheme"
    description: "Issue types for IT service desk"
    issue_types:
      - "Service Request"
      - "Incident"
      - "Problem"
```

**Fields:**
- `name` (required): Scheme name (will be prefixed with project key)
- `description` (required): Scheme description
- `issue_types` (required): List of issue type names (without project key prefix)

**Note:** Issue type names reference the names defined in `issue_types` section.

## screens

Defines custom screens for issue views.

```yaml
screens:
  - name: "Service Request Screen"
    description: "Screen for service requests"

  - name: "Incident Screen"
    description: "Screen for incidents"
```

**Fields:**
- `name` (required): Screen name (will be prefixed with project key)
- `description` (required): Screen description

## screen_tabs

Defines tabs and fields for each screen.

```yaml
screen_tabs:
  - screen: "Service Request Screen"
    name: "Details"
    fields:
      - "Summary"
      - "Description"
      - "Priority Level"
      - "Service Category"
      - "Assignee"
      - "Reporter"

  - screen: "Incident Screen"
    name: "Incident Details"
    fields:
      - "Summary"
      - "Description"
      - "Priority"
      - "Affected Users"
      - "Assignee"
```

**Fields:**
- `screen` (required): Screen name (without project key prefix)
- `name` (required): Tab name
- `fields` (required): List of field names to include in tab

**Note:** Field names must match exactly as they appear in Jira.

## screen_schemes

Maps screens to operations (create/edit/view).

```yaml
screen_schemes:
  - name: "Service Request Screen Scheme"
    description: "Screen scheme for service requests"
    screens:
      default: "Service Request Screen"

  - name: "Incident Screen Scheme"
    description: "Screen scheme for incidents"
    screens:
      default: "Incident Screen"
```

**Fields:**
- `name` (required): Screen scheme name (will be prefixed with project key)
- `description` (required): Screen scheme description
- `screens` (required): Screen mappings
  - `default` (required): Screen for create/edit/view operations

**Note:** Currently only supports `default` mapping. All operations use the same screen.

## issue_type_screen_schemes

Maps issue types to screen schemes.

```yaml
issue_type_screen_schemes:
  - name: "IT Service Desk Issue Type Screen Scheme"
    description: "Maps issue types to their screens"
    default_screen_scheme: "Service Request Screen Scheme"
    mappings:
      - issue_type: "Service Request"
        screen_scheme: "Service Request Screen Scheme"
      - issue_type: "Incident"
        screen_scheme: "Incident Screen Scheme"
      - issue_type: "Problem"
        screen_scheme: "Incident Screen Scheme"
```

**Fields:**
- `name` (required): Scheme name (will be prefixed with project key)
- `description` (required): Scheme description
- `default_screen_scheme` (required): Default screen scheme for unmapped issue types
- `mappings` (required): List of issue type to screen scheme mappings
  - `issue_type`: Issue type name (without project key prefix)
  - `screen_scheme`: Screen scheme name (without project key prefix)

## workflows

Defines custom workflows.

```yaml
workflows:
  - name: "Service Request Workflow"
    description: "Workflow for service requests"
    statuses:
      - name: "Open"
        category: "To Do"
      - name: "In Progress"
        category: "In Progress"
      - name: "Resolved"
        category: "Done"
      - name: "Closed"
        category: "Done"
    transitions:
      - name: "Start Progress"
        from: ["Open"]
        to: "In Progress"
      - name: "Resolve"
        from: ["In Progress"]
        to: "Resolved"
      - name: "Close"
        from: ["Resolved"]
        to: "Closed"
      - name: "Reopen"
        from: ["Resolved", "Closed"]
        to: "Open"
```

**Fields:**
- `name` (required): Workflow name (will be prefixed with project key)
- `description` (required): Workflow description
- `statuses` (required): List of workflow statuses
  - `name`: Status name
  - `category`: Status category ("To Do", "In Progress", "Done")
- `transitions` (required): List of transitions between statuses
  - `name`: Transition name
  - `from`: List of source status names
  - `to`: Target status name

## workflow_schemes

Maps issue types to workflows.

```yaml
workflow_schemes:
  - name: "IT Service Desk Workflow Scheme"
    description: "Workflow scheme for IT service desk"
    defaultWorkflow: "jira"
    issueTypeMappings:
      - issue_type: "Service Request"
        workflow: "Service Request Workflow"
      - issue_type: "Incident"
        workflow: "Service Request Workflow"
      - issue_type: "Problem"
        workflow: "Service Request Workflow"
```

**Fields:**
- `name` (required): Workflow scheme name (will be prefixed with project key)
- `description` (required): Workflow scheme description
- `defaultWorkflow` (required): Default workflow for unmapped issue types (use "jira" for Jira default)
- `issueTypeMappings` (required): List of issue type to workflow mappings
  - `issue_type`: Issue type name (without project key prefix)
  - `workflow`: Workflow name (without project key prefix)

## Complete Example

Here's a minimal but complete template:

```yaml
name: "Simple Task Tracker"
description: "Basic task tracking template"

groups:
  - name: "task-tracker-users"

fields:
  - name: "Summary"
  - name: "Description"
  - name: "Assignee"
  - name: "Priority"

issue_types:
  - name: "Task"
    description: "A work item to be completed"
    subtask: false

issue_type_schemes:
  - name: "Task Tracker Issue Type Scheme"
    description: "Issue types for task tracking"
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
      - "Description"
      - "Assignee"
      - "Priority"

screen_schemes:
  - name: "Task Screen Scheme"
    description: "Screen scheme for tasks"
    screens:
      default: "Task Screen"

issue_type_screen_schemes:
  - name: "Task Tracker Issue Type Screen Scheme"
    description: "Maps issue types to screens"
    default_screen_scheme: "Task Screen Scheme"
    mappings:
      - issue_type: "Task"
        screen_scheme: "Task Screen Scheme"

workflows:
  - name: "Simple Task Workflow"
    description: "Basic workflow for tasks"
    statuses:
      - name: "To Do"
        category: "To Do"
      - name: "In Progress"
        category: "In Progress"
      - name: "Done"
        category: "Done"
    transitions:
      - name: "Start"
        from: ["To Do"]
        to: "In Progress"
      - name: "Complete"
        from: ["In Progress"]
        to: "Done"
      - name: "Reopen"
        from: ["Done"]
        to: "To Do"

workflow_schemes:
  - name: "Task Tracker Workflow Scheme"
    description: "Workflow scheme for task tracking"
    defaultWorkflow: "jira"
    issueTypeMappings:
      - issue_type: "Task"
        workflow: "Simple Task Workflow"
```

## Naming Conventions

### Project Key Prefixing

The deployment system automatically prefixes certain resource names with the project key:

**Prefixed Resources:**
- Issue types: `{PROJECT_KEY}: {name}`
- Issue type schemes: `{PROJECT_KEY}: {name}`
- Screens: `{PROJECT_KEY}: {name}`
- Screen schemes: `{PROJECT_KEY}: {name}`
- Issue type screen schemes: `{PROJECT_KEY}: {name}`
- Workflows: `{PROJECT_KEY}: {name}`
- Workflow schemes: `{PROJECT_KEY}: {name}`

**Not Prefixed:**
- Groups
- Fields

### Reference Resolution

When referencing resources within the template, use the base name WITHOUT the project key prefix:

```yaml
# ✓ Correct
issue_type_schemes:
  - name: "My Scheme"
    issue_types:
      - "Task"  # References "issue_types[0].name"

# ✗ Incorrect
issue_type_schemes:
  - name: "My Scheme"
    issue_types:
      - "MYPROJ: Task"  # Don't include project key
```

## Validation

### Required Sections

All templates must include:
- `name`
- `issue_types` (at least one)
- `issue_type_schemes` (at least one)
- `screens` (at least one)
- `screen_tabs` (at least one)
- `screen_schemes` (at least one)
- `issue_type_screen_schemes` (at least one)
- `workflows` (at least one)
- `workflow_schemes` (at least one)

### Common Issues

**1. Field Not Found**
```
Error: Field 'Custom Field' not found
```
Solution: Ensure the field exists in Jira before deployment

**2. Circular References**
```
Error: Workflow transition references non-existent status
```
Solution: Verify all status names in transitions match status definitions

**3. Missing References**
```
Error: Screen 'Task Screen' not found
```
Solution: Ensure referenced resources are defined earlier in the template

## Template Development Tips

### 1. Start Small

Begin with a minimal template and add complexity:

```yaml
# Step 1: Basic structure
name: "My Template"
issue_types:
  - name: "Task"
    description: "A task"
    subtask: false

# Step 2: Add screens
screens:
  - name: "Task Screen"
    description: "Screen for tasks"

# Step 3: Add workflows
# Step 4: Add more issue types
# etc.
```

### 2. Use Comments

Document your template with YAML comments:

```yaml
# Service Request Configuration
issue_types:
  # Customer-facing request type
  - name: "Service Request"
    description: "Standard service request"
    subtask: false

  # Internal issue types
  - name: "Incident"
    description: "Service interruption"
    subtask: false
```

### 3. Organize by Feature

Group related configurations:

```yaml
# === Service Request Configuration ===
issue_types:
  - name: "Service Request"
    # ...

screens:
  - name: "Service Request Screen"
    # ...

workflows:
  - name: "Service Request Workflow"
    # ...

# === Incident Configuration ===
issue_types:
  - name: "Incident"
    # ...
# ...
```

### 4. Reuse Screen Schemes

Reduce duplication by reusing screen schemes:

```yaml
screen_schemes:
  # Single scheme used by multiple issue types
  - name: "Standard Screen Scheme"
    description: "Used by all standard issue types"
    screens:
      default: "Standard Screen"

issue_type_screen_schemes:
  - name: "ITSS"
    description: "Issue type screen scheme"
    default_screen_scheme: "Standard Screen Scheme"
    mappings:
      # All use the same screen scheme
      - issue_type: "Task"
        screen_scheme: "Standard Screen Scheme"
      - issue_type: "Bug"
        screen_scheme: "Standard Screen Scheme"
      - issue_type: "Story"
        screen_scheme: "Standard Screen Scheme"
```

## Related Documentation

- [Example Templates](../examples/) - Ready-to-use template examples
- [Template Deployment Guide](template-deployment.md) - How to deploy templates
- [Tracking System Guide](tracking-system.md) - Understanding deployment tracking
