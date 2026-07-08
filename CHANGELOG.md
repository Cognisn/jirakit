# Changelog

All notable changes to this project are documented in this file. The format follows Keep a Changelog (https://keepachangelog.com), and the project adheres to Semantic Versioning.

## [Unreleased]

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
