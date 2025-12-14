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

## [0.1.3] - 2025-12-14

### Added
- Enhanced agent instructions with content quality guidelines
- Comprehensive examples of generalizable patterns vs iteration-specific details
- SVG assets for banner and logo
- Content length and language constraints in agent instructions:
  - Summary: max 200 characters
  - Description: max 1000 characters
  - Content: max 4000 characters

### Changed
- Enhanced server instructions based on agent guidelines
- Improved tool responses with content quality requirements
- Updated README with latest command arguments

## [0.1.2] - 2025-12-14

### Added
- New `reflect_and_update_artifacts` tool for enforcing autonomous artifact management
- Explicit reflection checkpoints that prompt agents to create/update/archive artifacts based on learnings
- Enhanced test coverage with 206 new lines of tests for reflection and filtering functionality

### Changed
- Default artifact retrieval now excludes RESULT type artifacts (only includes PRACTICE, RULE, PROMPT)
- Improved artifact management prompts with more explicit instructions for autonomous updates
- Enhanced agent instructions emphasizing reflection before task completion
- Updated tool responses with clearer reminders to call `reflect_and_update_artifacts()` before finishing

### Fixed
- None

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

[0.1.3]: https://github.com/l0kifs/task-context-mcp/releases/tag/v0.1.3
[0.1.2]: https://github.com/l0kifs/task-context-mcp/releases/tag/v0.1.2
[0.1.1]: https://github.com/l0kifs/task-context-mcp/releases/tag/v0.1.1
[0.1.0]: https://github.com/l0kifs/task-context-mcp/releases/tag/v0.1.0
