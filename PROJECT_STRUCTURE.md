# RAFT Toolkit - Project Structure

## 📁 Directory Organization

```
raft-toolkit/
├── 📋 Documentation
│   ├── README.md              # Main project documentation
│   ├── CHANGELOG.md           # Version history and changes
│   ├── ARCHITECTURE.md        # Technical architecture details
│   └── PROJECT_STRUCTURE.md   # This file
│
├── 🚀 Application Entry Points
│   ├── raft.py                # CLI application entry point
│   └── run_web.py             # Web application entry point
│
├── 🏗️ Core Architecture
│   └── core/                  # Shared business logic
│       ├── __init__.py
│       ├── config.py          # 12-factor configuration management
│       ├── models.py          # Data models and types
│       ├── raft_engine.py     # Main orchestration engine
│       ├── services/          # Business services
│       │   ├── __init__.py
│       │   ├── document_service.py    # Document processing & chunking
│       │   ├── llm_service.py        # LLM interaction & Q&A generation  
│       │   └── dataset_service.py     # Dataset creation & export
│       ├── clients/           # Client libraries
│       │   ├── __init__.py
│       │   └── openai_client.py      # OpenAI/Azure client utilities
│       ├── formatters/        # Data formatters
│       │   ├── __init__.py
│       │   └── dataset_converter.py  # Dataset format converters
│       ├── utils/             # Utility modules
│       │   ├── __init__.py
│       │   ├── file_utils.py         # File manipulation utilities
│       │   ├── env_config.py         # Environment configuration helpers
│       │   └── identity_utils.py     # Azure identity management
│       └── logging/           # Logging configuration
│           ├── __init__.py
│           ├── log_setup.py          # Logging setup
│           └── logging.yaml          # Logging settings
│
├── 🖥️ User Interfaces
│   ├── cli/                   # Command-line interface
│   │   ├── __init__.py
│   │   └── main.py           # CLI implementation
│   │
│   └── web/                   # Web interface & REST API
│       ├── __init__.py
│       ├── app.py            # FastAPI application
│       └── static/           # Frontend assets
│           ├── index.html    # Main web interface
│           └── app.js        # Frontend JavaScript (Alpine.js)
│
├── 🐳 Deployment
│   ├── Dockerfile            # Container definition
│   ├── docker-compose.yml    # Multi-service orchestration
│   ├── .env.example         # Configuration template
│   └── .env                 # Local configuration (not in git)
│
├── 📦 Dependencies
│   ├── requirements.txt      # Core Python dependencies
│   └── requirements-web.txt  # Web interface dependencies
│
├── 🧪 Testing
│   ├── tests/              # Comprehensive test suite
│   │   ├── unit/          # Unit tests for core modules
│   │   ├── integration/   # Integration tests for services
│   │   ├── api/           # API endpoint tests
│   │   ├── cli/           # CLI interface tests
│   │   └── conftest.py    # Shared test fixtures
│   ├── run_tests.py       # Test runner script
│   ├── pytest.ini        # Pytest configuration
│   ├── requirements-test.txt # Test dependencies
│   └── TESTING.md         # Testing documentation
│
├── 🔧 Tools & Legacy
│   ├── tools/               # Standalone tools
│   │   └── eval.py         # Evaluation utility
│   │
│   └── legacy/             # Original implementation (preserved)
│       ├── README.md       # Legacy documentation
│       └── raft.py         # Original monolithic implementation
│
├── 📊 Data & Templates
│   ├── templates/            # Prompt templates
│   │   ├── gpt_template.txt     # GPT system prompts
│   │   ├── gpt_qa_template.txt  # GPT Q&A prompts
│   │   ├── llama_template.txt   # Llama system prompts
│   │   └── llama_qa_template.txt # Llama Q&A prompts
│   │
│   └── notebooks/            # Jupyter notebooks
│       ├── evaluation.ipynb # Evaluation examples
│       └── generation.ipynb # Generation examples
│
└── 🔍 Generated/Runtime
    ├── uploads/              # Uploaded files (runtime)
    ├── outputs/              # Generated datasets (runtime)
    └── logs/                 # Application logs (runtime)
```

## 🎯 Key Design Principles

### 1. **Separation of Concerns**
- **Core**: Business logic independent of interface
- **CLI**: Command-line specific functionality
- **Web**: Web interface and API endpoints
- **Legacy**: Original implementation preserved

### 2. **12-Factor App Compliance**
- Configuration via environment variables
- Stateless design for scaling
- Process isolation and port binding
- Environment parity

### 3. **Modular Architecture**
- Services can be used independently
- Clear dependency injection
- Easy testing and mocking
- Extensible design

### 4. **Developer Experience**
- Type hints throughout codebase
- Comprehensive documentation
- Clear error messages
- Hot reload for development

### 5. **Production Ready**
- Container support with Docker
- Health check endpoints
- Structured logging
- Error handling and recovery

## 🚦 Entry Points

### CLI Usage
```bash
python raft.py --datapath document.pdf --output ./results
```

### Web Interface
```bash
python run_web.py
# Open http://localhost:8000
```

### Docker Deployment
```bash
docker-compose up -d
```

## 📊 File Count Summary

- **Core Architecture**: 15 files (including all modules)
- **User Interfaces**: 4 files  
- **Testing**: 12 files (comprehensive test suite)
- **Tools**: 1 file
- **Legacy Files**: 2 files (preserved for reference)
- **Configuration**: 6 files
- **Documentation**: 5 files
- **Templates**: 4 files
- **CI/CD**: 1 file
- **Total**: ~50 organized files

This structure provides a clean, maintainable, and scalable foundation for the RAFT Toolkit while preserving the original implementation for reference.