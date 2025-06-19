# Changelog

## [Unreleased]

### Added
- Support for Nomic embeddings with `nomic-embed-text` model
- Added langchain-core and langchain-community dependencies
- Added unit tests for Nomic embeddings integration
- Added `.safety-policy.yml` to document and ignore false positive security vulnerabilities
- Added comprehensive CI optimization documentation (`docs/CI_OPTIMIZATION.md`)
- Added convenience dependency groups for faster installations (minimal, standard, complete)

### Fixed
- Fixed embedding service to properly handle Nomic embeddings
- Improved error handling in semantic chunking with fallback to fixed chunking
- Fixed type hints in OpenAI client implementation
- Added proper error handling for embedding model initialization
- Fixed wheel packaging issues by consolidating modules under single package namespace
- Resolved all flake8 linting errors across the codebase:
  - Fixed import redefinition errors (F811) in CLI and service modules
  - Removed unused imports (F401) throughout test files and core modules
  - Fixed unused variables (F841) in test files
  - Corrected f-string placeholder issues (F541) in evaluation tools
  - Reorganized module-level imports (E402) for proper code structure
  - Fixed multiple statements on one line (E704) in protocol definitions
- Resolved security vulnerabilities identified by safety and bandit:
  - Updated sentry-sdk to >=2.8.0 to address CVE-2024-40647 (environment variable exposure)
  - Updated sentence-transformers to >=3.1.0 to fix PVE-2024-73169 (arbitrary code execution)
  - Eliminated py package dependency to address CVE-2022-42969 (pytest>=7.0 has built-in functionality)
  - Documented langchain-experimental CVE-2024-46946 as false positive (affects unused component)
  - Fixed bandit security warnings with appropriate suppressions for legitimate use cases
  - Created safety policy file (.safety-policy.yml) to properly ignore false positive vulnerabilities
- **Fixed comprehensive test suite issues (25 test failures resolved)**:
  - Fixed DatasetService missing format methods (`_format_hf`, `_format_completion`, `_format_chat`, `_format_eval`)
  - Enhanced model classes with missing create() method parameters (embedding, metadata support)
  - Added missing QADataPoint methods (`get_all_contexts()`, `distractor_contexts` property)
  - Fixed TemplateLoader missing utility methods (`get_template_path()`, `template_exists()`)
  - Corrected import paths in integration tests for new package structure
  - Fixed file handling issues in dataset save operations
  - Resolved test assertion mismatches between expected and actual return values
  - Fixed SourceDocument constructor parameter validation
  - Enhanced empty dataset handling to return valid empty datasets instead of raising errors
- **Resolved Windows CI pipeline issues**:
  - Fixed mypy type checking differences between Windows and Unix systems
  - Added type stubs for Windows mypy compatibility (types-requests, types-PyYAML, types-simplejson, types-ujson)
  - Fixed cross-platform mypy configuration with `warn_unused_ignores = false`
  - Resolved import sorting issues across all test files
  - Fixed specific failing tests in nomic embeddings, LLM service integration, and CLI modules
- **Fixed Docker containerization issues**:
  - **Linux Docker**: Fixed dependency verification to only check core dependencies in base stage
  - **Linux Docker**: Added proper verification of optional dependencies in development stage
  - **Windows Docker**: Implemented direct Python 3.11.9 download and installation for Windows containers
  - **Windows Docker**: Fixed Python installation and PATH configuration in Windows Server Core containers
  - **Windows Docker**: Added PowerShell Core installation before using PowerShell commands in Windows containers
  - Enhanced PowerShell-based build process with comprehensive error handling and logging
  - Fixed GitHub Container Registry authentication for Windows builds in CI pipeline
  - Added robust Python and pip verification steps before dependency installation
  - Resolved Docker registry cache authentication errors on pull requests
  - Fixed security scan conditionals to only scan containers when they are actually built and pushed
  - Improved CI reliability with better error handling for Windows builds, mypy checks, and tool tests
  - Added timeouts and fallback handling for Windows Visual Studio Build Tools installation

### Changed
- **BREAKING**: Refactored package structure to use `raft_toolkit` as single top-level package
- **BREAKING**: Removed symbolic links (cli, core, web) and updated all imports to use full `raft_toolkit.*` paths
- Updated all imports to use absolute imports with new package structure
- Moved templates directory into package structure
- Updated pytest configuration and documentation to reference new package paths
- **Simplified containerization strategy**: Disabled Windows Docker builds in CI pipeline and release workflows due to complexity, focusing on Linux containers while maintaining cross-platform Python package support for Windows, macOS, and Linux
- **MAJOR: Optimized dependency structure for 70-80% faster CI builds**:
  - Reduced core dependencies from ~45 to ~15 packages
  - Moved heavy ML libraries (transformers, sentence-transformers, scikit-learn) to optional 'ai' group
  - Reorganized dependencies into logical optional groups (ai, langchain, embeddings, documents, web, cloud, tracing, dev)
  - Added convenience groups: minimal, standard, complete, all
  - Tightened version constraints for faster dependency resolution
- Updated requirements.txt to contain only essential core dependencies
- Updated all requirements files (requirements*.txt) with optimized version ranges
- Refactored embedding service to use Protocol for better type checking
- Improved mock embeddings implementation for testing
- Reorganized import statements across modules for better code organization
- Cleaned up unused imports and variables for improved code quality

## [0.2.0] - 2023-06-15

### Added
- Web interface for dataset generation and analysis
- Support for SharePoint document sources
- Enhanced logging with structured output
- Rate limiting for API calls
- Template system for customizing prompts
- Evaluation tools for dataset quality assessment

### Changed
- Refactored core engine for better modularity
- Improved chunking strategies with semantic chunking
- Enhanced error handling and reporting
- Updated documentation with comprehensive guides

### Fixed
- Fixed memory issues with large document processing
- Resolved concurrency issues in parallel processing
- Fixed token counting for rate limiting
- Improved error messages for configuration issues

## [0.1.0] - 2023-03-01

### Added
- Initial release with basic functionality
- Support for PDF, TXT, and JSON documents
- Command-line interface
- Basic chunking strategies
- Question and answer generation
- Dataset export in multiple formats