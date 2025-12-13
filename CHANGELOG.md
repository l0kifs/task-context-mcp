# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- None yet

### Changed
- None yet

### Fixed
- None yet

## [0.1.1] - 2025-12-13

### Changed
- Improved documentation in README with simplified server run instructions using `uvx` command
- Updated default data directory to use cross-platform user home directory (`~/.task-context-mcp/data`)

### Fixed
- Fixed directory creation to use `parents=True` in Path.mkdir() for proper nested directory handling
- Fixed database initialization to ensure proper directory structure creation

## [0.1.0] - 2025-12-13

### Added
- Initial release of Task Context MCP Server
- Core task context management with SQLite storage
- Full-text search capabilities using SQLite FTS5
- Seven MCP tools for task context and artifact management:
  - `get_active_task_contexts` - List all active task contexts
  - `create_task_context` - Create new reusable task types
  - `get_artifacts_for_task_context` - Retrieve artifacts with filtering
  - `create_artifact` - Store practices, rules, prompts, and learnings
  - `update_artifact` - Modify existing artifacts
  - `archive_artifact` - Archive artifacts with reasons
  - `search_artifacts` - Full-text search across all artifacts
- Support for multiple artifacts per type per task context
- Lifecycle management with active/archived status tracking
- Transaction safety with ACID compliance
- Comprehensive test suite with 31 tests
- Documentation: README, BRD, PUBLISHING guide, and agent instructions
- CI/CD: GitHub Actions workflow for automated PyPI publishing
- MIT License

[0.1.1]: https://github.com/l0kifs/task-context-mcp/releases/tag/v0.1.1
[0.1.0]: https://github.com/l0kifs/task-context-mcp/releases/tag/v0.1.0
