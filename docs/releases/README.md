# Release History

This directory contains detailed release notes for all versions of jirakit.

## Latest Releases

### [v0.1.7](v0.1.7.md) - 9 October 2025
**Patch Release - Critical Bug Fix**

Fixed deprecated Jira API endpoint causing 410 Gone errors. Migrated from GET `/rest/api/3/search?jql=` to POST `/rest/api/3/search/jql` endpoint.

**Changes:**
- 🐛 Fixed deprecated search endpoint (CHANGE-2046)
- ✅ Updated to POST-based JQL search
- 📝 Added request body parameters

---

### [v0.1.6](v0.1.6.md) - 9 October 2025
**Major Feature Release**

Comprehensive documentation, deployment tracking, and test suite.

**Highlights:**
- ✨ DeploymentTracker with precision rollback
- 📚 Complete user documentation (8,300+ lines)
- ✅ 115 unit tests (84% pass rate)
- 📝 Enhanced inline code documentation
- 🎯 Example templates and guides

---

### [v0.1.2](v0.1.2.md) - 20 March 2025
**Minor Release**

Dependency cleanup and code streamlining.

**Changes:**
- 🔧 Removed mistune dependency
- 🧹 Code cleanup
- 📉 Reduced external dependencies

---

### [v0.1.1](v0.1.1.md) - 13 March 2025
**Minor Release**

Reliability improvements and automatic dependency management.

**Highlights:**
- ♻️ HTTP request retry with exponential backoff
- 🔄 Auto-install Node.js packages
- 🔍 Enhanced issue search capabilities
- 🧹 Code quality improvements

---

### [v0.1.0](v0.1.0.md) - 24 February 2025
**Initial Release**

First public release of jirakit.

**Core Features:**
- 🚀 Template-based project deployment
- 📊 YAML-driven configuration
- 🔧 Complete Jira Cloud automation
- 🏗️ Modular architecture
- 🌐 Jira Cloud REST API v3 support

---

## Release Timeline

```
v0.1.7 (Oct 2025)  ← Latest
  ↑
v0.1.6 (Oct 2025)  ← Major features
  ↑
v0.1.2 (Mar 2025)
  ↑
v0.1.1 (Mar 2025)
  ↑
v0.1.0 (Feb 2025)  ← Initial release
```

## Version Numbering

jirakit follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version (0.x.x) - Incompatible API changes
- **MINOR** version (x.X.x) - New functionality (backward-compatible)
- **PATCH** version (x.x.X) - Bug fixes (backward-compatible)

## Upgrade Guide

### From v0.1.6 to v0.1.7
No code changes required. Update and run:
```bash
pip install --upgrade jirakit
```

### From v0.1.2 to v0.1.6
New features available, no breaking changes:
```bash
pip install --upgrade jirakit
pip install -r requirements-test.txt  # Optional: for testing
```

Review new documentation at `docs/README.md` and consider using deployment tracking.

### From v0.1.1 to v0.1.2
No action required:
```bash
pip install --upgrade jirakit
```

### From v0.1.0 to v0.1.1
Ensure Node.js is installed. Library will auto-install npm packages:
```bash
pip install --upgrade jirakit
node --version  # Verify Node.js installation
```

## Migration Guides

### Deprecated API Endpoints

**v0.1.7 Fixed:**
- Issue search now uses POST `/rest/api/3/search/jql` (was GET with query parameter)
- Automatic - no code changes needed

### Breaking Changes

**None in current releases.** All versions maintain backward compatibility.

## Support

- **Documentation:** [Main Docs](../README.md)
- **API Reference:** [API Docs](../api-reference/README.md)
- **Examples:** [Example Templates](../examples/)
- **Guides:** [User Guides](../guides/)

## Contributing

See release-specific notes for contributor acknowledgements and areas where community contributions are welcome.
