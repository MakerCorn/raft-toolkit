"""
Configuration management following 12-factor app principles.
All configuration should be loaded from environment variables.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    from dotenv import load_dotenv as original_load_dotenv

    # Create a wrapper with consistent signature
    def load_dotenv(*args, **kwargs):
        return original_load_dotenv(*args, **kwargs)

except ImportError:
    # Fallback for environments where python-dotenv is not available
    def load_dotenv(*args, **kwargs):
        return False


import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class RaftConfig:
    """Configuration class for RAFT application following 12-factor principles."""

    # I/O Configuration
    datapath: Union[str, Path] = field(default_factory=lambda: Path("."))
    output: str = "./"
    output_format: str = "hf"
    output_type: str = "jsonl"
    output_chat_system_prompt: Optional[str] = None
    output_completion_prompt_column: str = "prompt"
    output_completion_completion_column: str = "completion"

    # Input Source Configuration
    source_type: str = "local"  # local, s3, sharepoint
    source_uri: Optional[str] = None  # If None, uses datapath
    source_credentials: Dict[str, Any] = field(default_factory=dict)
    source_include_patterns: list = field(default_factory=lambda: ["**/*"])
    source_exclude_patterns: list = field(default_factory=list)
    source_max_file_size: int = 50 * 1024 * 1024  # 50MB
    source_batch_size: int = 100

    # Processing Configuration
    distractors: int = 1
    p: float = 1.0
    questions: int = 5
    chunk_size: int = 512
    doctype: str = "pdf"
    chunking_strategy: str = "semantic"
    chunking_params: Dict[str, Any] = field(default_factory=dict)

    # AI Model Configuration
    openai_key: Optional[str] = None
    embedding_model: str = "nomic-embed-text"
    completion_model: str = "llama3.2"
    system_prompt_key: str = "gpt"

    # Azure Configuration
    use_azure_identity: bool = False
    azure_openai_enabled: bool = False

    # Performance Configuration
    workers: int = 1
    embed_workers: int = 1
    pace: bool = True
    auto_clean_checkpoints: bool = False

    # Rate Limiting Configuration
    rate_limit_enabled: bool = False
    rate_limit_strategy: str = "sliding_window"
    rate_limit_requests_per_minute: Optional[int] = None
    rate_limit_requests_per_hour: Optional[int] = None
    rate_limit_tokens_per_minute: Optional[int] = None
    rate_limit_tokens_per_hour: Optional[int] = None
    rate_limit_max_burst: Optional[int] = None
    rate_limit_burst_window: float = 60.0
    rate_limit_max_retries: int = 3
    rate_limit_base_delay: float = 1.0
    rate_limit_preset: Optional[str] = None

    # Template Configuration
    templates: str = "./templates"
    embedding_prompt_template: Optional[str] = None
    qa_prompt_template: Optional[str] = None
    answer_prompt_template: Optional[str] = None

    # LangWatch Observability Configuration
    langwatch_enabled: bool = False
    langwatch_api_key: Optional[str] = None
    langwatch_endpoint: Optional[str] = None
    langwatch_project: Optional[str] = None
    langwatch_debug: bool = False

    def __post_init__(self):
        """Convert string paths to Path objects."""
        if isinstance(self.datapath, str):
            self.datapath = Path(self.datapath)

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "RaftConfig":
        """Load configuration from environment variables."""
        if env_file:
            load_dotenv(env_file)
        else:
            # Load default .env file if it exists
            load_dotenv()

        config = cls()

        # I/O Configuration
        datapath_env = os.getenv("RAFT_DATAPATH")
        if datapath_env:
            config.datapath = Path(datapath_env)
        config.output = os.getenv("RAFT_OUTPUT", config.output)
        config.output_format = os.getenv("RAFT_OUTPUT_FORMAT", config.output_format)
        config.output_type = os.getenv("RAFT_OUTPUT_TYPE", config.output_type)
        config.output_chat_system_prompt = os.getenv("RAFT_OUTPUT_CHAT_SYSTEM_PROMPT")
        config.output_completion_prompt_column = os.getenv(
            "RAFT_OUTPUT_COMPLETION_PROMPT_COLUMN", config.output_completion_prompt_column
        )
        config.output_completion_completion_column = os.getenv(
            "RAFT_OUTPUT_COMPLETION_COMPLETION_COLUMN", config.output_completion_completion_column
        )

        # Input Source Configuration
        config.source_type = os.getenv("RAFT_SOURCE_TYPE", config.source_type)
        config.source_uri = os.getenv("RAFT_SOURCE_URI", config.source_uri)
        config.source_max_file_size = int(os.getenv("RAFT_SOURCE_MAX_FILE_SIZE", config.source_max_file_size))
        config.source_batch_size = int(os.getenv("RAFT_SOURCE_BATCH_SIZE", config.source_batch_size))

        # Parse source credentials from JSON string
        source_credentials_str = os.getenv("RAFT_SOURCE_CREDENTIALS")
        if source_credentials_str:
            try:
                config.source_credentials = json.loads(source_credentials_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse RAFT_SOURCE_CREDENTIALS: {e}")

        # Parse include/exclude patterns from JSON strings
        source_include_str = os.getenv("RAFT_SOURCE_INCLUDE_PATTERNS")
        if source_include_str:
            try:
                config.source_include_patterns = json.loads(source_include_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse RAFT_SOURCE_INCLUDE_PATTERNS: {e}")

        source_exclude_str = os.getenv("RAFT_SOURCE_EXCLUDE_PATTERNS")
        if source_exclude_str:
            try:
                config.source_exclude_patterns = json.loads(source_exclude_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse RAFT_SOURCE_EXCLUDE_PATTERNS: {e}")

        # Processing Configuration
        config.distractors = int(os.getenv("RAFT_DISTRACTORS", config.distractors))
        config.p = float(os.getenv("RAFT_P", config.p))
        config.questions = int(os.getenv("RAFT_QUESTIONS", config.questions))
        config.chunk_size = int(os.getenv("RAFT_CHUNK_SIZE", config.chunk_size))
        config.doctype = os.getenv("RAFT_DOCTYPE", config.doctype)
        config.chunking_strategy = os.getenv("RAFT_CHUNKING_STRATEGY", config.chunking_strategy)

        # Parse chunking params from JSON string
        chunking_params_str = os.getenv("RAFT_CHUNKING_PARAMS")
        if chunking_params_str:
            try:
                config.chunking_params = json.loads(chunking_params_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse RAFT_CHUNKING_PARAMS: {e}")

        # AI Model Configuration
        config.openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
        config.embedding_model = os.getenv("RAFT_EMBEDDING_MODEL", config.embedding_model)
        config.completion_model = os.getenv("RAFT_COMPLETION_MODEL", config.completion_model)
        config.system_prompt_key = os.getenv("RAFT_SYSTEM_PROMPT_KEY", config.system_prompt_key)

        # Azure Configuration
        config.use_azure_identity = os.getenv("RAFT_USE_AZURE_IDENTITY", "false").lower() in ("true", "1", "yes")
        config.azure_openai_enabled = os.getenv("AZURE_OPENAI_ENABLED", "false").lower() in ("true", "1", "yes")

        # Performance Configuration
        config.workers = int(os.getenv("RAFT_WORKERS", config.workers))
        config.embed_workers = int(os.getenv("RAFT_EMBED_WORKERS", config.embed_workers))
        config.pace = os.getenv("RAFT_PACE", "true").lower() in ("true", "1", "yes")
        config.auto_clean_checkpoints = os.getenv("RAFT_AUTO_CLEAN_CHECKPOINTS", "false").lower() in (
            "true",
            "1",
            "yes",
        )

        # Rate Limiting Configuration
        config.rate_limit_enabled = os.getenv("RAFT_RATE_LIMIT_ENABLED", "false").lower() in ("true", "1", "yes")
        config.rate_limit_strategy = os.getenv("RAFT_RATE_LIMIT_STRATEGY", config.rate_limit_strategy)
        config.rate_limit_preset = os.getenv("RAFT_RATE_LIMIT_PRESET")

        # Parse numeric rate limits
        requests_per_minute = os.getenv("RAFT_RATE_LIMIT_REQUESTS_PER_MINUTE")
        if requests_per_minute:
            config.rate_limit_requests_per_minute = int(requests_per_minute)
        requests_per_hour = os.getenv("RAFT_RATE_LIMIT_REQUESTS_PER_HOUR")
        if requests_per_hour:
            config.rate_limit_requests_per_hour = int(requests_per_hour)
        tokens_per_minute = os.getenv("RAFT_RATE_LIMIT_TOKENS_PER_MINUTE")
        if tokens_per_minute:
            config.rate_limit_tokens_per_minute = int(tokens_per_minute)
        tokens_per_hour = os.getenv("RAFT_RATE_LIMIT_TOKENS_PER_HOUR")
        if tokens_per_hour:
            config.rate_limit_tokens_per_hour = int(tokens_per_hour)
        max_burst = os.getenv("RAFT_RATE_LIMIT_MAX_BURST")
        if max_burst:
            config.rate_limit_max_burst = int(max_burst)

        config.rate_limit_burst_window = float(
            os.getenv("RAFT_RATE_LIMIT_BURST_WINDOW", config.rate_limit_burst_window)
        )
        config.rate_limit_max_retries = int(os.getenv("RAFT_RATE_LIMIT_MAX_RETRIES", config.rate_limit_max_retries))
        config.rate_limit_base_delay = float(os.getenv("RAFT_RATE_LIMIT_BASE_DELAY", config.rate_limit_base_delay))

        # Template Configuration
        config.templates = os.getenv("RAFT_TEMPLATES", config.templates)
        config.embedding_prompt_template = os.getenv("RAFT_EMBEDDING_PROMPT_TEMPLATE")
        config.qa_prompt_template = os.getenv("RAFT_QA_PROMPT_TEMPLATE")
        config.answer_prompt_template = os.getenv("RAFT_ANSWER_PROMPT_TEMPLATE")

        # LangWatch Configuration
        config.langwatch_enabled = os.getenv("LANGWATCH_ENABLED", "false").lower() in ("true", "1", "yes")
        config.langwatch_api_key = os.getenv("LANGWATCH_API_KEY")
        config.langwatch_endpoint = os.getenv("LANGWATCH_ENDPOINT")
        config.langwatch_project = os.getenv("LANGWATCH_PROJECT")
        config.langwatch_debug = os.getenv("LANGWATCH_DEBUG", "false").lower() in ("true", "1", "yes")

        return config

    def validate(self) -> None:
        """Validate configuration."""
        # Ensure datapath is a Path object
        if isinstance(self.datapath, str):
            self.datapath = Path(self.datapath)

        # For local sources, validate datapath
        if self.source_type == "local" and not self.source_uri:
            if not self.datapath.exists() and str(self.datapath) != ".":
                raise ValueError(f"Data path does not exist: {self.datapath}")

        # Validate source type
        if self.source_type not in ["local", "s3", "sharepoint"]:
            raise ValueError(f"Invalid source type: {self.source_type}")

        # For non-local sources, require source_uri
        if self.source_type != "local" and not self.source_uri:
            raise ValueError(f"source_uri is required for source type: {self.source_type}")

        if self.doctype not in ["pdf", "txt", "json", "api", "pptx"]:
            raise ValueError(f"Invalid doctype: {self.doctype}")

        if self.output_format not in ["hf", "completion", "chat", "eval"]:
            raise ValueError(f"Invalid output format: {self.output_format}")

        if self.output_type not in ["jsonl", "parquet"]:
            raise ValueError(f"Invalid output type: {self.output_type}")

        if self.chunking_strategy not in ["semantic", "fixed", "sentence"]:
            raise ValueError(f"Invalid chunking strategy: {self.chunking_strategy}")

        if self.output_chat_system_prompt and self.output_format != "chat":
            raise ValueError("output_chat_system_prompt can only be used with chat output format")

        # Validate source file size limit
        if self.source_max_file_size <= 0:
            raise ValueError("source_max_file_size must be positive")

        if self.source_batch_size <= 0:
            raise ValueError("source_batch_size must be positive")

        # Allow demo mode with mock API key
        if not self.openai_key and not self.use_azure_identity:
            raise ValueError("OpenAI API key is required unless using Azure identity")
        elif self.openai_key == "demo_key_for_testing":
            pass  # Allow demo mode


def get_config(env_file: Optional[str] = None) -> RaftConfig:
    """Get validated configuration instance."""
    config = RaftConfig.from_env(env_file)
    config.validate()
    return config
