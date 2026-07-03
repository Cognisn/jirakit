# Changelog

All notable changes to this project are documented in this file. The format follows Keep a Changelog (https://keepachangelog.com), and the project adheres to Semantic Versioning.

## [Unreleased]

### Changed
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
