# Changelog

## [Unreleased]

### Added
- Support for Nomic embeddings with `nomic-embed-text` model
- Added langchain-core and langchain-community dependencies
- Added asyncio dependency for async operations
- Added unit tests for Nomic embeddings integration

### Fixed
- Fixed embedding service to properly handle Nomic embeddings
- Improved error handling in semantic chunking with fallback to fixed chunking
- Fixed type hints in OpenAI client implementation
- Added proper error handling for embedding model initialization
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

### Changed
- Updated requirements.txt and pyproject.toml with new dependencies
- Updated all requirements files (requirements*.txt) with security fixes and version alignments
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