# jirakit Test Suite

This directory contains comprehensive unit tests for the jirakit library. The test suite ensures code quality, validates API v3 migrations, verifies bug fixes, and tests the new deployment tracking system.

## Test Coverage Overview

**Current Status:** all tests passing. The suite runs fully offline: every HTTP interaction and the underlying `jira.JIRA` client are mocked. See `index.md` for the maintained per-file index.

The test suite covers all major modules of the jirakit library:

- **JiraClient** - HTTP methods, authentication, timeouts, factory methods
- **DeploymentTracker** - Deployment tracking and rollback
- **Groups** - CRUD operations, batch creation
- **Screens** - CRUD operations, tabs, schemes
- **Workflows** - Workflows and statuses management
- **Issue Types** - Creation, deletion, schemes
- **Fields** - Field management
- **Projects** - Basic operations
- **Issues** - Basic operations
- **Import behaviour** - No import-time side effects
- **Text area** - Markdown to ADF conversion (pure Python)

## Running Tests

### Run All Unit Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/jirakit --cov-report=html

# Run specific test file
pytest tests/test_tracking.py -v
```

### Run Specific Test Classes

```bash
# Run all tracking tests
pytest tests/test_tracking.py

# Run specific test class
pytest tests/test_tracking.py::TestDeploymentTrackerInitialisation

# Run specific test
pytest tests/test_tracking.py::TestDeploymentTrackerInitialisation::test_tracker_initialisation_minimal
```

### Integration Tests

Integration tests require live Jira credentials and are located in the root directory:

```bash
# NOT run by default (require credentials)
# test_api_fixes.py - API v3 migration verification
# test_tracking_deployment.py - Live deployment with tracking
# test_rollback.py - Live rollback testing
```

**Note:** Integration tests are excluded from the regular test suite as they require:
- Valid Jira Cloud instance
- Administrator API token
- Network connectivity

## Test Structure

### Configuration Files

#### `conftest.py` - Pytest Configuration

Shared fixtures and test utilities:

- **`mock_response()`** - Creates mock HTTP response objects
- **`mock_client()`** - Creates mock JiraClient instances
- **`sample_user()`** - Sample user data
- **`sample_project()`** - Sample project data
- **`sample_issue()`** - Sample issue data
- **`sample_field()`** - Sample field data
- **`sample_screen()`** - Sample screen data
- **`sample_workflow()`** - Sample workflow data
- **`paginated_response()`** - Creates paginated API responses

### Test Modules

#### 1. `test_tracking.py` - DeploymentTracker Tests

**Coverage:** Complete coverage of deployment tracking functionality

**Test Classes:**

1. **TestDeploymentTrackerInitialisation** (5 tests)
   - Minimal and full parameter initialisation
   - Directory creation
   - Tracking file creation
   - Data structure validation

2. **TestDeploymentTrackerSetters** (2 tests)
   - set_project_id()
   - set_deployed_by()

3. **TestDeploymentTrackerResourceTracking** (10 tests)
   - track_custom_field()
   - track_issue_type()
   - track_screen()
   - track_screen_scheme()
   - track_issue_type_screen_scheme()
   - track_issue_type_scheme()
   - track_workflow()
   - track_workflow_scheme()
   - Multiple resource tracking

4. **TestDeploymentTrackerErrorTracking** (2 tests)
   - Single error tracking
   - Multiple error tracking

5. **TestDeploymentTrackerStatus** (3 tests)
   - mark_completed()
   - mark_failed()
   - mark_partial()

6. **TestDeploymentTrackerLoad** (3 tests)
   - Loading existing tracker
   - Loading non-existent tracker
   - Loading from non-existent directory

7. **TestDeploymentTrackerSummary** (3 tests)
   - Empty summary generation
   - Summary with resources
   - Summary after completion

8. **TestDeploymentTrackerFileOperations** (4 tests)
   - File creation
   - File updates
   - File deletion
   - Non-existent file handling

9. **TestDeploymentTrackerPersistence** (2 tests)
   - Data persistence across saves
   - Complete deployment lifecycle

10. **TestDeploymentTrackerEdgeCases** (3 tests)
    - Special characters in names
    - Project keys with numbers
    - Long error messages

**Key Features Tested:**
- ✅ Tracker initialisation with all parameters
- ✅ Resource tracking for all types (issue types, screens, workflows, etc.)
- ✅ Error logging and tracking
- ✅ Status management (in_progress, completed, failed, partial)
- ✅ File persistence and loading
- ✅ Summary generation
- ✅ Edge cases and special characters

#### 2. `test_client.py` - JiraClient Tests

**Coverage:**
- Client initialisation and session authentication
- Request timeout configuration (default, custom, and pass-through to every verb)
- HTTP methods (GET, POST, PUT, DELETE)
- `get_me()` endpoint (v3 API)
- Factory methods for sub-modules

An autouse fixture mocks the underlying `jira.JIRA` client, so no test in this module touches the network.

#### 3. `test_groups.py` - Groups Module Tests

**Coverage:**
- Group class properties
- `get_groups()` with pagination
- `create_group()` single creation
- `create_groups()` batch creation with duplicate checking

**Key Tests:**
- ✅ Single and multi-page pagination
- ✅ Group creation with special characters
- ✅ Duplicate prevention in batch creation
- ✅ Empty list handling

**Features Verified:**
- API pagination handling
- Duplicate group detection
- Special character handling

#### 4. `test_issue_types.py` - Issue Types Module Tests

**Coverage:**
- IssueType class properties
- `create()` with standard and subtask types
- `delete()` operations
- `get_all()` and `get_all_user_issue_types()`
- IssueTypeScheme and IssueTypeScreenScheme operations

**Key Tests:**
- ✅ Issue type CRUD operations
- ✅ API v3 endpoint verification
- ✅ Scheme operations (create, get, delete)
- ✅ Scheme id extraction across the API's varied response shapes

#### 5. `test_screens.py` - Screens Module Tests

**Coverage:**
- Screen class properties and methods
- ScreenScheme class
- `create()` screen creation
- `create_screen_scheme()` operations
- Screen tabs management
- Delete operations

**Key Tests:**
- ✅ API v3 endpoint verification (not v2)
- ✅ Double slash bug fix verification
- ✅ `projectKey` parameter fix verification
- ✅ Screen and scheme CRUD operations
- ✅ Tab creation and field management

**Bug Fixes Verified:**
- Fixed double slash in delete URL (`/screens//{id}` → `/screens/{id}`)
- Fixed projectKey parameter (was using numeric ID instead of string key)

#### 6. `test_workflows.py` - Workflows Module Tests

**Coverage:**
- Workflow class properties
- `get_all()` with active filter
- Status class
- Status CRUD operations

**Key Tests:**
- ✅ Workflow property access
- ✅ Get all workflows with active parameter
- ✅ Status creation and deletion
- ✅ Get all statuses

#### 7. `test_fields.py` - Fields Module Tests

**Coverage:**
- Field class properties
- `get_all()` operations
- `delete_field()` operations

**Key Tests:**
- ✅ Field property access
- ✅ Get all fields
- ✅ Field deletion
- ✅ Field initialisation

#### 8. `test_projects.py` - Projects Module Tests

**Coverage:**
- Project class properties with `skip_load` flag
- `get_all()` operations
- `delete_project()` operations

**Key Tests:**
- ✅ Project properties with skip_load
- ✅ Get all projects with status filter
- ✅ Project initialisation
- ✅ Project deletion via `delete_project()`

**Note:** Template deployment and rollback are tested via integration tests in root directory.

#### 9. `test_issues.py` - Issues Module Tests

**Coverage:**
- Issue class properties
- `get_issue()` operations
- `get_issues_updated_last_days()` search via the v3 `/search/jql` endpoint

**Key Tests:**
- ✅ Issue initialisation and properties
- ✅ Fetching an issue by key
- ✅ JQL search construction and endpoint verification

#### 10. `test_import.py` - Package Import Behaviour

**Coverage:**
- Importing jirakit succeeds without Node.js on PATH
- Importing jirakit spawns no subprocesses and installs nothing

These tests guard against regressions of the import-time side effects removed in 2026-07 (Node.js checks, OS-level installs, `npm install -g md-to-adf`).

#### 11. `test_text_area.py` - Markdown to ADF Conversion

**Coverage:**
- `convert_markdown_to_adf()` producing valid ADF v1 documents (headings, marks, lists, tables)
- Conversion is pure Python: no subprocess, no Node.js
- `TextAreaContent` formatting of strings, lists, and JSON code blocks

## API v3 Migration Verification

All tests verify that the library uses Jira Cloud REST API v3 (not v2):

### Verified Endpoints

✅ `/rest/api/3/myself` - User information
✅ `/rest/api/3/project` - Project operations
✅ `/rest/api/3/issuetype` - Issue type operations
✅ `/rest/api/3/screens` - Screen operations
✅ `/rest/api/3/screenscheme` - Screen scheme operations
✅ `/rest/api/3/group/bulk` - Group operations

### Bug Fixes Verified

✅ **Double slash bug** - `/rest/api/3/screens//{id}` → `/rest/api/3/screens/{id}`
✅ **projectKey parameter** - Using string key instead of numeric ID
✅ **URL concatenation** - Proper handling of trailing/leading slashes in all HTTP methods

## Writing New Tests

### Test Template

```python
import pytest
from unittest.mock import MagicMock, patch

class TestMyFeature:
    """Test description."""

    def test_basic_functionality(self):
        """Test basic operation."""
        # Arrange
        mock_client = MagicMock()

        # Act
        result = my_function(mock_client)

        # Assert
        assert result == expected_value

    def test_error_handling(self):
        """Test error conditions."""
        mock_client = MagicMock()
        mock_client.get.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            my_function(mock_client)
```

### Using Fixtures

```python
def test_with_fixtures(mock_client, sample_project):
    """Test using shared fixtures."""
    # Fixtures are defined in conftest.py
    project = Project(sample_project, mock_client, skip_load=True)
    assert project.key == "TEST"
```

### Best Practices

1. **Use skip_load=True** for classes that load data during init
2. **Mock HTTP responses** using conftest.py factories
3. **Test one thing** per test function
4. **Use descriptive names** that explain what's being tested
5. **Document known issues** in test docstrings
6. **Group related tests** into test classes

## Test Data

Sample data fixtures in `conftest.py`:

```python
# Sample user data
sample_user = {
    'accountId': '123',
    'displayName': 'Test User',
    'emailAddress': 'test@example.com'
}

# Sample project data
sample_project = {
    'id': '10001',
    'key': 'TEST',
    'name': 'Test Project'
}

# And more...
```

## Continuous Integration

### Running in CI

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests with coverage
pytest tests/ --cov=src/jirakit --cov-report=xml

# Check coverage threshold
pytest tests/ --cov=src/jirakit --cov-fail-under=80
```

### Coverage Goals

- **Overall:** 80%+ coverage
- **Critical modules:** 90%+ coverage (DeploymentTracker, Projects, etc.)
- **Helper modules:** 70%+ coverage

## Troubleshooting

### Test Failures

**Problem:** Tests fail with `AttributeError`

**Solution:** Check if using `skip_load=True` for class initialisation

**Problem:** Mock responses don't match

**Solution:** Update mock data in conftest.py to match API v3 structure

**Problem:** Import errors

**Solution:** Ensure you're running from project root and `src/` is in path

### Running Specific Tests

```bash
# Run a subset of files
pytest tests/test_tracking.py tests/test_groups.py

# Run with specific markers
pytest tests/ -m "not integration"

# Run and stop on first failure
pytest tests/ -x
```

## Test Maintenance

### When Adding New Features

1. **Write tests first** (TDD approach)
2. **Add to appropriate test file** or create new one
3. **Update `index.md`** with the new or changed test files
4. **Ensure all new tests pass**
5. **Add fixtures** to conftest.py if needed

### When Fixing Bugs

1. **Write failing test** that reproduces bug
2. **Fix the bug** in source code
3. **Verify test passes**
4. **Document fix** in test docstring

## Summary

The jirakit test suite provides comprehensive coverage with:

- **All tests passing**, fully offline (no network, no Node.js)
- **Verified bug fixes** (URL concatenation, API v3 migration)
- **Regression guards** for import-time side effects and pure Python ADF conversion
- **Integration test support** for live deployment testing

The test suite ensures reliability and quality while supporting ongoing development and maintenance of the jirakit library.

## Related Documentation

- [Project README](../README.md) - Main project documentation
- [Complete Documentation](../docs/README.md) - User guides
