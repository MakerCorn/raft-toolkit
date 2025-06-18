# Nomic Embeddings Integration

This document describes the integration of Nomic embeddings into the RAFT Toolkit.

## Overview

The RAFT Toolkit now supports the `nomic-embed-text` embedding model, which provides high-quality embeddings for document chunking and semantic search. This integration allows users to leverage Nomic's embedding models as an alternative to OpenAI's embedding models.

## Configuration

To use Nomic embeddings, set the embedding model in your configuration:

```bash
# Via command line
python raft.py --datapath your_docs/ --output your_output/ --embedding_model nomic-embed-text

# Via environment variable
export RAFT_EMBEDDING_MODEL=nomic-embed-text
python raft.py --datapath your_docs/ --output your_output/

# Via .env file
# Add this line to your .env file:
RAFT_EMBEDDING_MODEL=nomic-embed-text
```

## Dependencies

The following dependencies are required for Nomic embeddings:

```
langchain-core>=0.1.0,<0.2.0
langchain-community>=0.0.13,<0.1.0
nomic>=3.0.0,<4.0.0
```

These dependencies are automatically installed when you install the RAFT Toolkit with the updated requirements.

## Implementation Details

The Nomic embeddings integration is implemented in the following files:

1. `core/clients/openai_client.py` - Added support for detecting and using Nomic embeddings
2. `core/services/embedding_service.py` - Added proper handling of Nomic embeddings
3. `core/services/document_service.py` - Updated to handle Nomic embeddings for semantic chunking

The implementation includes fallback mechanisms to ensure that if Nomic embeddings are not available, the system will gracefully fall back to other embedding models or mock embeddings for testing.

## Testing

Unit tests for Nomic embeddings are available in:

```
tests/unit/test_nomic_embeddings.py
```

These tests verify that the Nomic embeddings integration works correctly and that appropriate fallbacks are in place.

## Troubleshooting

If you encounter issues with Nomic embeddings:

1. Ensure you have the required dependencies installed
2. Check that the `nomic` package is properly installed
3. If Nomic embeddings are not available, the system will fall back to OpenAI embeddings or mock embeddings
4. Check the logs for any error messages related to embedding model initialization

## Future Improvements

- Add support for additional Nomic embedding models
- Implement caching for embeddings to improve performance
- Add configuration options for Nomic-specific parameters
- Enhance the evaluation tools to compare embedding quality across different models