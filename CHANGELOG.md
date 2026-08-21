# Changelog

All notable changes to this project are documented in this file. The format follows Keep a Changelog (https://keepachangelog.com), and the project adheres to Semantic Versioning.

## [Unreleased]

### Fixed
- Every paginated list helper now checks the HTTP status before parsing the response body. Jira Cloud answers `401` with a `Content-Type` of `application/json` but a plain-text body, so an authentication failure surfaced as `JSONDecodeError: Expecting value: line 1 column 1 (char 0)` from inside a pagination loop, with nothing in the traceback naming the credentials as the cause (issue #7). The same masking applied to `403` and `429`. Ten helpers were affected, across `Groups`, `IssueTypes`, `Projects`, `Screens`, `Statuses` and `Workflows`; `Fields.get_all` already had the guard and is unchanged in that respect.
- Paginated helpers terminate when a response carries no `isLast` key, rather than treating its absence as "not the last page". Eight of the loops read `isLast` with `.get()`, so any response omitting it — which is what the admin-only endpoints return to a non-administrator, since an error body has no `isLast` — left them advancing `startAt` indefinitely. A single call to `Projects.get_project()` on a non-admin account was observed still climbing past a `startAt` of 19,950 a minute in, turning one API call into an unbounded request flood against Atlassian and a good way for an integration to be rate-limited. The remaining loops read `isLast` by subscript and raised `KeyError` instead, which was not a flood but was still not a usable error.

### Added
- `Projects.reconcile_template(project, template)` applies a template to a project it has already been deployed to, and `Projects.plan_template(project, template)` reports what that would change without changing it. `apply_template` was previously create-only, so every template change after the first deployment had to be reproduced by hand in the Jira UI; a consumer shipping a bundled template had no code path to bring existing projects up to date once the template gained a field (issue #8). Both accept a project or a project key.
- `Projects.missing_template_fields(project, template)` reports which template fields an issue type's create metadata does not carry, from create metadata alone. The screen and scheme endpoints a full plan reads require Jira administrator, and a service account that can otherwise use the site gets 403 on them; create metadata reads without it, so a least-privileged runtime can still report precisely what an administrator must change. Because Jira derives create metadata from screen tab membership, a field reported there is one that genuinely cannot be set on an issue of that type.
- `Screen.ensure_tab(name, field_ids)` finds a tab by name and adds only the fields it does not already carry, checking every tab of the screen first because a field may sit on only one tab per screen. `create_tab` always posted a new tab, so there was no way to add a field to a tab that already existed — the load-bearing operation for a template that gained a field.
- Get-or-create helpers for the resources a template deploys: `IssueTypes.ensure`, `IssueTypes.ensure_issue_type_scheme`, `IssueTypes.ensure_issue_type_screen_scheme`, `Screens.ensure` and `Screens.ensure_screen_scheme`. Each looks the resource up by the name the deployment gives it and creates it only when absent.
- `IssueTypeScheme.name` and `IssueTypeScreenScheme.name`, which the lookups match on. The latter copes with the nested `issueTypeScreenScheme` envelope its `id` property already handled.
- Opt-in workflow reconciliation. A workflow that already exists is left alone and reported as a `skip` change rather than a second one of the same name being created; passing `reconcile_workflows=True` updates it to the template's definition instead. It is opt-in because Jira Cloud's update endpoint replaces a whole workflow definition rather than merging into it, so running it against a workflow carrying live issues is a materially different risk from adding a field to a screen. `Workflows.update` carries the workflow's current version, which the endpoint uses for optimistic locking, and validates the payload first as creation does.
- A dry run mode throughout: `apply_template(..., dry_run=True)` reports the changes it would make and issues no request that writes.

### Changed
- `Projects.create` now creates the project and delegates everything the template describes to `apply_template`, which is the single implementation shared with reconciling an existing project. `apply_template` previously had no callers at all — `create` reimplemented the same sequence inline with rollback tracking — and the two had already drifted apart, `create` building new schemes where `apply_template` adopted the project's existing ones. Get-or-create is what makes them the same function: on a project the template has never been applied to everything is created, and on one it has been applied to before only the difference is.
- **Breaking:** `apply_template` returns a `TemplateApplication` (carrying `.project`, `.changes`, `.changed` and `.summary()`) rather than the project. Nothing in the package called it, and `create` still returns the project, so this only affects a caller that used `apply_template` directly.
- Resources that `apply_template` adopts rather than creates are deliberately not recorded against the deployment tracker, so a rollback never deletes something the deployment did not make.
- Workflow schemes that already exist are no longer recreated.
- Paginated helpers parse each page once rather than calling `resp.json()` a second time to read `values`.

### Fixed
- Corrected the deployment guide, which still described screen tabs being populated at step 7, before the screens are wired to the project. That ordering was fixed in 0.6.1 (issue #5) but the documentation was not updated with it.

## [0.6.1] - 2026-08-17

### Fixed
- Template deployments now populate screen tabs *after* the screens have been wired to the project, so the deployed custom fields register with Jira's issue create metadata. Jira registers a field with createmeta on the tab-membership change, but only for a screen that is already attached to a project; jirakit added the fields first and wired the screens afterwards, so every custom field stayed permanently invisible to createmeta and none of them could be set when creating an issue (`"Field 'customfield_xxxxx' cannot be set. It is not on the appropriate screen, or unknown."`). The project deployed "successfully" while being unable to do the thing it was deployed for (issue #5). Fixed in both deployment paths: `Projects.create`, where the tabs now follow the issue type screen scheme being assigned to the project, and `Projects.apply_template`, where they follow the screen scheme being mapped into the project's existing issue type screen scheme.

## [0.6.0] - 2026-08-16

### Fixed
- `Workflows.create` now creates workflows through `POST /rest/api/3/workflows/create`. It previously posted the legacy bulk payload to `POST /rest/api/3/workflow`, which Atlassian deprecated in 2024 and has since removed, so the endpoint returned 405 Method Not Allowed and every template deployment containing workflows aborted part-way through, leaving a half-configured project behind (issue #1). Workflow search and deletion are unaffected and are unchanged.
- `Workflow.entity_id` accepts an `id` given as a plain string, the shape the workflow creation response returns, as well as the legacy nested `{'id': {'entityId': ...}}` shape returned by workflow search. Deployment tracking records this value and rollback deletes by it, so without this a newly created workflow could not be tracked or rolled back.
- `Workflow.name` no longer raises `KeyError` for workflows returned by `Workflows.get_all`. Workflow search nests the name under `id` and returns none at the top level, so reading `name` on any searched workflow raised; the rollback fallback path (which has no tracking file and matches workflows by name) could not run at all. Confirmed against a live site, where a search result carries only `id`, `description`, `created` and `updated`. The test fixture now mirrors that response.
- Corrected the workflow sections of the template documentation and the example templates, which specified statuses with a `category` of "To Do"/"In Progress"/"Done" and omitted the required transition `type`. The deployment code reads `type` on both, and the status category vocabulary is `TODO`/`IN_PROGRESS`/`DONE`, so every published example would have failed to deploy. The examples also now carry the `INITIAL` transition each workflow requires.
- `rollback_template_deployment` now deletes the project first, then the resources that depended on it, in dependency order (workflow schemes then their workflows; issue type screen schemes, then screen schemes, then screens; issue type schemes then issue types). It previously deleted the screen-related resources while the project was still live, which Jira refuses with a 400, so a rollback left most of what it was asked to remove in place (issue #2).
- Rollback keeps the tracking file whenever anything was left behind, and deletes it only after a completely clean rollback. It previously deleted the record whenever the project itself was deleted, stranding orphaned resources with nothing to retry from.
- Rollback reports failures instead of swallowing them. A failed workflow deletion was logged as "likely active" and discarded, so orphaned workflows never reached `errors`; issue type schemes and workflow schemes were recorded as deleted without any deletion being attempted, on the assumption that deleting the project removed them.
- Rollback no longer loads the project's full configuration before deleting it. Loading reads the project's screens, schemes and mappings, which is unnecessary when the project is about to be deleted and can fail outright on the partially deployed projects that rollback exists to clean up.

### Added
- Workflow transition conditions and validators are translated to the rule keys the current workflow API expects: `AllowOnlyAssignee` maps to `system:restrict-issue-transition` and `ValueFieldCondition` to `system:check-field-value` (with the field name resolved to a field ID and the value JSON-array encoded, as that endpoint requires). A condition or validator may instead give an explicit `ruleKey` and `parameters`, which are passed through as written, so a template can use any workflow rule the site supports. A condition group's legacy `AND`/`OR` operator is expressed as the `ALL`/`ANY` operation the API takes.
- Workflow creation payloads are checked against `POST /rest/api/3/workflows/create/validation` before they are created, so a definition Jira will not accept raises a `ValueError` listing the validation codes and messages rather than a bare 400 from the create endpoint. Definitions that cannot be translated at all — an unmapped condition type, an unknown condition operator, or a transition naming a status the workflow does not define — raise before any request is made.
- Rollback retries deletions Jira refuses, for up to a new `retry_seconds` parameter (default 30 seconds, 0 to attempt each deletion once). This is defensive: with the corrected ordering every deletion has been observed succeeding on the first attempt against a live site.
- The rollback summary gained `resources_remaining` (each with `type`, `id`, `name` and `reason`), `shared_resources_left` (why custom fields and statuses are deliberately kept) and `skipped` (why a group of deletions was not attempted), so an operator can see exactly what is still on the site and why.
- Rollback now also deletes the resources the project template makes Jira create alongside the project, which nothing tracks and deleting the project does not remove: the workflow scheme and workflow (`<KEY>: Software Simplified Workflow Scheme`, `Software Simplified Workflow for Project <KEY>`), and the template's own screens, screen schemes, issue type screen scheme and issue type scheme. They are found by the `<KEY>: ` naming convention the deployment itself uses, which is also now the basis of the no-tracking-file fallback; matching is by prefix, so a resource merely mentioning the key elsewhere in its name is left alone.
- Rollback treats a project it cannot retrieve as already deleted, and goes on to clean up what it left behind. A rollback that leaves resources behind keeps its tracking file so it can be retried, and by the time it is retried the project itself is usually gone; previously that retry stopped at the missing project and could never finish the job.
- `Projects.get_project_reference(project_key)` fetches a project without loading its configuration, for callers that need only its identity.

### Changed
- `rollback_template_deployment(delete_project=False)` now deletes nothing and explains why in `skipped`, rather than attempting deletions that Jira refuses. Every scheme deletion fails while the project it is assigned to is live, so the previous behaviour could only produce 400s.
- `rollback_template_deployment(enable_undo=True)` now deletes the project and stops there, explaining why in `skipped`. `enable_undo` places the project in the recycle bin rather than deleting it, and a project in the recycle bin goes on holding the schemes assigned to it, so every dependent deletion is refused as "assigned to one or more projects" until the project is permanently deleted.


## [0.5.0] - 2026-07-09

### Added
- `Screen.add_field(field_id)` adds a field to an existing screen's default (first) tab, so a newly provisioned custom field can be placed onto an operator-chosen screen. It is idempotent — the field is checked against every tab of the screen (a field may sit on only one tab per screen) and only added if absent — and raises `ValueError` if the screen has no tabs.
- `JiraClient.can_administer()` reports whether the authenticated user holds the global ADMINISTER permission, via a non-mutating probe of `/rest/api/3/mypermissions`, so callers can gate field and screen provisioning.

## [0.4.0] - 2026-07-08

### Added
- `Issues.add_attachment(issue_key, filename, content)` attaches a file (given as bytes) to an issue, delegating to the underlying python-jira client for the multipart upload (the low-level `JiraClient` session is JSON-only).
- `Issues.available_fields(issue_type)` enumerates the fields on an issue type's create screen from the cached create metadata (no extra API call), returning `name`, `key`, `schema_type` and `allowed_values` (value labels for choice fields) per field — intended for building and validating field mappings.
- `Issues.unmapped_fields(issue_type, fields)` is a preflight for `create_issue`: given the same `fields` mapping, it returns the names of value-bearing fields that have no matching field on the create screen (by the same exact display-name lookup `create_issue` uses), so callers can warn before a field is silently dropped. `create_issue`'s existing behaviour and return type are unchanged.

## [0.3.1] - 2026-07-08

### Fixed
- `Issue._format_doc` now renders Atlassian Document Format (ADF) list nodes (`bulletList`, `orderedList`, `listItem`). Previously these fell through to a branch that read only a `text` key and never recursed into the list content, so every bullet and numbered list item was silently dropped from the plain-text conversion. Bullet items now render with a `- ` marker and ordered items with an incrementing number (honouring the node's `attrs.order` start value); nested lists are preserved. Surfaced downstream in VendorVet as list text in the Risk Assessment Outcome field not being copied to the SharePoint software-service register.

## [0.3.0] - 2026-07-07

### Added
- Configurable request timeouts on `JiraClient` via a new `timeout` constructor parameter, accepting a single value in seconds or a (connect, read) tuple and threaded through both the underlying `jira.JIRA` client and every session request. Defaults to `JiraClient.DEFAULT_TIMEOUT` of (10, 60), matching the workaround vendorvet previously carried; requests that used to hang indefinitely now raise `requests.exceptions.Timeout`. Pass `timeout=None` to restore the old unbounded behaviour.

### Fixed
- `Issue._format_doc` now reads Atlassian Document Format (ADF) node keys defensively, so a node missing an expected key (most commonly an empty paragraph `{"type": "paragraph"}` with no `content`) is rendered without raising and its sibling content is preserved. Previously such nodes raised a `KeyError` that was swallowed and logged as a bare, context-free `ERROR [root] 'content'`; the recoverable case is now logged at WARNING through a `jirakit.issues` logger with the offending node included. Surfaced downstream in VendorVet as repeated `ERROR [root] 'content'` when rendering rich-text fields containing empty paragraphs.
- Corrected broken code examples in the README and documentation that passed `api_token=` to `JiraClient`; the constructor takes the API token as `password`, so the published examples raised `TypeError` when copied.

### Removed
- Deleted `MIGRATION_REPORT.md` and `MIGRATION_REPORT.json`, the artefacts from the automated dtJira migration; their follow-up items are complete and the reports remain available in git history.

### Changed
- PyPI release prep: corrected the author and maintainer contact to `matthew@cognisn.com`, and added a trademark notice to the README stating jirakit is an independent project not affiliated with Atlassian (Jira is a registered trademark of Atlassian Corporation Pty Ltd). Distribution artefacts verified with `python -m build` and `twine check` (both pass).
- README refresh: pip-based installation instructions (from GitHub now, PyPI planned), current version references instead of the stale 0.1.7 string, accurate test suite status, corrected licence file link, and a 0.2.0 release-history section. Stale pass-rate claims and version strings were also removed from `docs/README.md` and `tests/README.md`.
- Packaging metadata clean-up: filled in the package description and keywords; corrected the licence declaration from a "The Unlicense" classifier to the SPDX expression `MIT` matching `LICENCE.txt` (Copyright Cognisn); corrected the Python classifiers from 3.9-3.11 to 3.12-3.14 in line with `requires-python`; repaired `MANIFEST.in`, which still referenced a different digital-thought project and would have produced source distributions missing `_version.txt`; and removed unused digital-thought metadata leftovers (`module.txt`, `_name.txt`, `_full_name.txt`, `_description.txt`, `_metadata.yaml`, `_licence.txt`).
- Replaced the Node.js `md-to-adf` subprocess with the pure Python `marklassian` package for Markdown to ADF conversion. jirakit no longer requires Node.js at all. Output was diffed against `md-to-adf` on representative content before the switch: 10 of 14 samples byte-identical, and the remainder equal or better (marklassian adds the valid `order` attribute on ordered lists, converts tables that `md-to-adf` could not, and fixes a case where `md-to-adf` split one ordered list into two and swallowed a following paragraph).
- Removed all import-time side effects from `jirakit/__init__.py`. Importing the package no longer checks for Node.js, demands administrative privileges, attempts OS-level Node.js installation, or runs `npm install -g md-to-adf`. The Node.js environment check now happens at first use in `convert_markdown_to_adf`, which raises a clear `RuntimeError` with installation guidance when Node.js is absent; the library never installs software on the caller's behalf.
- Removed the dead `install_node_linux` code path, which called `platform.linux_distribution()` (removed in Python 3.8) and crashed on any supported Python.

### Fixed
- Aligned the test suite with the actual library API (inherited from dtJira, where these tests had never passed): corrected attribute names (`url`, `field_detail`, `project_detail`, `type_detail`, `scheme_detail`), method names (`delete_project`, `get_issue`, `add_issue_type`, `get_issues_updated_last_days`), the `Issues` constructor argument order, and the `IssueTypes.create` signature.
- Mocked the underlying `jira.JIRA` client in the `JiraClient` tests so the suite no longer makes live network requests during test runs.

## [0.2.0] - 2026-07-03

### Changed
- Renamed the project from `dtJira` to `jirakit` and migrated it from the digital-thought repository into a clean Cognisn-owned project. Git history was deliberately not carried over; `dtJira` 0.1.7 is retained as a read-only reference.
- Relicensed under MIT (Copyright Cognisn).
