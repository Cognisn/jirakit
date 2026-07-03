# Changelog

All notable changes to this project are documented in this file. The format follows Keep a Changelog (https://keepachangelog.com), and the project adheres to Semantic Versioning.

## [Unreleased]

### Added
- Configurable request timeouts on `JiraClient` via a new `timeout` constructor parameter, accepting a single value in seconds or a (connect, read) tuple and threaded through both the underlying `jira.JIRA` client and every session request. Defaults to `JiraClient.DEFAULT_TIMEOUT` of (10, 60), matching the workaround vendorvet previously carried; requests that used to hang indefinitely now raise `requests.exceptions.Timeout`. Pass `timeout=None` to restore the old unbounded behaviour.

### Changed
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
