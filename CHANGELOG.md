# Changelog

All notable changes to this project are documented in this file. The format follows Keep a Changelog (https://keepachangelog.com), and the project adheres to Semantic Versioning.

## [Unreleased]

### Fixed
- Aligned the test suite with the actual library API (inherited from dtJira, where these tests had never passed): corrected attribute names (`url`, `field_detail`, `project_detail`, `type_detail`, `scheme_detail`), method names (`delete_project`, `get_issue`, `add_issue_type`, `get_issues_updated_last_days`), the `Issues` constructor argument order, and the `IssueTypes.create` signature.
- Mocked the underlying `jira.JIRA` client in the `JiraClient` tests so the suite no longer makes live network requests during test runs.

## [0.2.0] - 2026-07-03

### Changed
- Renamed the project from `dtJira` to `jirakit` and migrated it from the digital-thought repository into a clean Cognisn-owned project. Git history was deliberately not carried over; `dtJira` 0.1.7 is retained as a read-only reference.
- Relicensed under MIT (Copyright Cognisn).
