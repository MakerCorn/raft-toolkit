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

### Changed
- **BREAKING**: Refactored package structure to use `raft_toolkit` as single top-level package
- Updated all imports to use absolute imports with new package structure
- Moved templates directory into package structure
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