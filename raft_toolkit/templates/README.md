# RAFT Toolkit Prompt Templates

This directory contains prompt templates used by RAFT Toolkit for various operations. These templates can be customized to improve the quality and relevance of embeddings and question-answer generation for your specific use case.

## Available Templates

### Embedding Templates

- **`embedding_prompt_template.txt`**: Default template for embedding generation
  - Used to provide context and instructions for generating document embeddings
  - Supports variables: `{content}`, `{document_type}`, `{metadata}`
  - Customize this to improve embedding quality for your domain

### Question-Answer Generation Templates

The following templates are used for RAFT (Retrieval-Augmented Fine-Tuning) dataset generation:

- **`gpt_template.txt`**: GPT-style question-answering template
  - Used for generating structured answers with reasoning and citations
  - Format includes step-by-step reasoning and follow-up questions

- **`gpt_qa_template.txt`**: GPT question generation template
  - Used for generating synthetic questions from context
  - Includes content filtering and complexity guidelines

- **`llama_template.txt`**: Llama-style question-answering template
  - Optimized for Llama and similar models
  - Includes detailed reasoning and answer extraction format

- **`llama_qa_template.txt`**: Llama question generation template
  - Generates questions with varying complexity levels
  - Includes specific formatting instructions

## Customizing Templates

### For Embedding Generation

1. **Copy the default template**:
   ```bash
   cp embedding_prompt_template.txt my_custom_template.txt
   ```

2. **Edit the template** to include domain-specific instructions:
   ```
   Generate embeddings optimized for [your domain] documents.
   Focus on [specific concepts/terminology] relevant to [your use case].
   ```

3. **Configure RAFT Toolkit** to use your custom template:
   ```bash
   export EMBEDDING_PROMPT_TEMPLATE="/path/to/templates/my_custom_template.txt"
   ```

### For RAFT Dataset Generation

1. **Choose the appropriate model template** (GPT or Llama)
2. **Customize the instructions** for your specific domain
3. **Test with sample documents** to ensure quality output

### Template Variables

When creating custom templates, you can use these variables:

#### Embedding Templates
- `{content}`: The actual document content to be embedded
- `{document_type}`: File type (pdf, txt, json, pptx, etc.)
- `{metadata}`: Additional document metadata (file size, source, etc.)
- `{chunk_index}`: Index of the current chunk within the document
- `{chunking_strategy}`: The chunking method used (semantic, fixed, sentence)

#### QA Generation Templates
- `{question}`: The question to be answered (for answer templates)
- `{context}`: The context/chunk for question generation
- `%s`: Placeholder for number of questions to generate

### Best Practices

1. **Be Specific**: Include domain-specific terminology and concepts
2. **Provide Context**: Explain the intended use case for the embeddings/QA pairs
3. **Keep It Concise**: Avoid overly long prompts that might confuse the model
4. **Test and Iterate**: Experiment with different prompts and measure quality
5. **Consider Your Model**: Different models may respond better to different prompt styles

## Configuration

### Environment Variables

Set template paths in your environment:

```bash
# Use custom prompt templates
export RAFT_EMBEDDING_PROMPT_TEMPLATE="/path/to/templates/my_embedding_template.txt"
export RAFT_QA_PROMPT_TEMPLATE="/path/to/templates/my_qa_template.txt"
export RAFT_ANSWER_PROMPT_TEMPLATE="/path/to/templates/my_answer_template.txt"

# Set templates directory
export RAFT_TEMPLATES="/path/to/templates/"

# Use default templates (no configuration needed)
# RAFT Toolkit will use the appropriate template by default
```

### CLI Arguments

Use command-line arguments to specify custom templates:

```bash
# Use custom templates
python raft.py --datapath docs/ --output training_data/ \
  --embedding-prompt-template "/path/to/custom_embedding.txt" \
  --qa-prompt-template "/path/to/custom_qa.txt" \
  --answer-prompt-template "/path/to/custom_answer.txt"

# Use custom templates directory
python raft.py --datapath docs/ --output training_data/ \
  --templates "/path/to/custom/templates/"
```

### Programmatic Configuration

Configure via the RAFT Toolkit configuration:

```python
config = RAFTConfig(
    templates="./templates",
    embedding_prompt_template="templates/my_custom_embedding.txt",
    qa_prompt_template="templates/gpt_qa_template.txt",
    answer_prompt_template="templates/gpt_template.txt"
)
```

## Examples

### Medical Documents
```
Generate embeddings for medical literature that capture:
- Clinical terminology and procedures
- Drug names and dosages
- Symptoms and diagnoses
- Treatment protocols and outcomes

Content: {content}
```

### Legal Documents
```
Generate embeddings for legal documents focusing on:
- Legal terminology and concepts
- Case citations and precedents
- Statutory references
- Contractual terms and conditions

Document Type: {document_type}
Content: {content}
```

### Technical Documentation
```
Generate embeddings for technical documentation emphasizing:
- API endpoints and parameters
- Code examples and syntax
- Configuration options
- Error messages and troubleshooting

Content: {content}
Metadata: {metadata}
```

### Custom QA Generation

For specialized domains, you can modify the question generation templates:

```
Generate questions about [your domain] that focus on:
- Key concepts and terminology
- Practical applications
- Common troubleshooting scenarios
- Best practices and guidelines

Context: {context}
```

## Integration with RAFT Toolkit

The templates integrate seamlessly with RAFT Toolkit's processing pipeline:

1. **Document Processing**: Uses embedding templates during document ingestion
2. **Dataset Generation**: Uses QA templates for synthetic dataset creation
3. **Fine-tuning**: Generated QA pairs are used for model fine-tuning
4. **Retrieval**: Embedded documents enable efficient similarity search

## Default Behavior

### Automatic Template Loading

RAFT Toolkit provides robust default template handling that ensures the system always has working prompts, even if no custom templates are specified:

1. **Template Search Order**:
   - Custom template file (if specified via CLI arguments or environment variables)
   - Model-specific template file (e.g., `gpt_template.txt`, `llama_qa_template.txt`)
   - Generic default template files (`default_embedding_template.txt`, `simple_qa_template.txt`)
   - Built-in hardcoded defaults (always available as final fallback)

2. **Smart Model Detection**:
   - Templates are automatically selected based on the model type being used
   - Llama models get Llama-optimized templates
   - GPT models get GPT-optimized templates
   - Unknown models fall back to GPT-style templates

3. **Graceful Degradation**:
   - If custom templates fail to load, the system falls back to defaults
   - Missing template directories are handled gracefully
   - Malformed template files trigger fallback to built-in defaults

### Available Default Templates

The following default template files are provided out of the box:

- `embedding_prompt_template.txt` - Main embedding template with detailed instructions
- `default_embedding_template.txt` - Simple embedding template
- `gpt_template.txt` - GPT-style answer generation with reasoning and citations
- `gpt_qa_template.txt` - GPT-style question generation with guidelines
- `llama_template.txt` - Llama-optimized answer generation
- `llama_qa_template.txt` - Llama-optimized question generation
- `default_qa_template.txt` - Generic question generation template
- `default_answer_template.txt` - Generic answer generation template
- `simple_qa_template.txt` - Minimal question generation template
- `simple_answer_template.txt` - Minimal answer generation template

### No Configuration Required

RAFT Toolkit works out of the box without any template configuration:

```bash
# This will work with all default templates
python raft.py --datapath docs/ --output training_data/
```

The system automatically:
- Uses appropriate templates for the selected model type
- Falls back to generic templates if model-specific ones aren't found
- Provides meaningful defaults for all prompt types
- Logs template loading decisions for debugging

For more information on using these templates, see the main RAFT Toolkit documentation.