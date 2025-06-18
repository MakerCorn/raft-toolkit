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

### Changed
- Updated requirements.txt and pyproject.toml with new dependencies
- Refactored embedding service to use Protocol for better type checking
- Improved mock embeddings implementation for testing

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