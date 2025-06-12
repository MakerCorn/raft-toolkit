"""
Configuration management following 12-factor app principles.
All configuration should be loaded from environment variables.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional
try:
    from dotenv import load_dotenv
except ImportError:
    # Fallback for environments where python-dotenv is not available
    def load_dotenv(*args, **kwargs):
        pass
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class RaftConfig:
    """Configuration class for RAFT application following 12-factor principles."""
    
    # I/O Configuration
    datapath: Path = field(default_factory=lambda: Path("."))
    output: str = "./"
    output_format: str = "hf"
    output_type: str = "jsonl"
    output_chat_system_prompt: Optional[str] = None
    output_completion_prompt_column: str = "prompt"
    output_completion_completion_column: str = "completion"
    
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
    
    # Template Configuration
    templates: str = "./"
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> 'RaftConfig':
        """Load configuration from environment variables."""
        if env_file:
            load_dotenv(env_file)
        else:
            # Load default .env file if it exists
            load_dotenv()
        
        config = cls()
        
        # I/O Configuration
        if os.getenv('RAFT_DATAPATH'):
            config.datapath = Path(os.getenv('RAFT_DATAPATH'))
        config.output = os.getenv('RAFT_OUTPUT', config.output)
        config.output_format = os.getenv('RAFT_OUTPUT_FORMAT', config.output_format)
        config.output_type = os.getenv('RAFT_OUTPUT_TYPE', config.output_type)
        config.output_chat_system_prompt = os.getenv('RAFT_OUTPUT_CHAT_SYSTEM_PROMPT')
        config.output_completion_prompt_column = os.getenv('RAFT_OUTPUT_COMPLETION_PROMPT_COLUMN', config.output_completion_prompt_column)
        config.output_completion_completion_column = os.getenv('RAFT_OUTPUT_COMPLETION_COMPLETION_COLUMN', config.output_completion_completion_column)
        
        # Processing Configuration
        config.distractors = int(os.getenv('RAFT_DISTRACTORS', config.distractors))
        config.p = float(os.getenv('RAFT_P', config.p))
        config.questions = int(os.getenv('RAFT_QUESTIONS', config.questions))
        config.chunk_size = int(os.getenv('RAFT_CHUNK_SIZE', config.chunk_size))
        config.doctype = os.getenv('RAFT_DOCTYPE', config.doctype)
        config.chunking_strategy = os.getenv('RAFT_CHUNKING_STRATEGY', config.chunking_strategy)
        
        # Parse chunking params from JSON string
        chunking_params_str = os.getenv('RAFT_CHUNKING_PARAMS')
        if chunking_params_str:
            try:
                config.chunking_params = json.loads(chunking_params_str)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse RAFT_CHUNKING_PARAMS: {e}")
        
        # AI Model Configuration
        config.openai_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY')
        config.embedding_model = os.getenv('RAFT_EMBEDDING_MODEL', config.embedding_model)
        config.completion_model = os.getenv('RAFT_COMPLETION_MODEL', config.completion_model)
        config.system_prompt_key = os.getenv('RAFT_SYSTEM_PROMPT_KEY', config.system_prompt_key)
        
        # Azure Configuration
        config.use_azure_identity = os.getenv('RAFT_USE_AZURE_IDENTITY', 'false').lower() in ('true', '1', 'yes')
        config.azure_openai_enabled = os.getenv('AZURE_OPENAI_ENABLED', 'false').lower() in ('true', '1', 'yes')
        
        # Performance Configuration
        config.workers = int(os.getenv('RAFT_WORKERS', config.workers))
        config.embed_workers = int(os.getenv('RAFT_EMBED_WORKERS', config.embed_workers))
        config.pace = os.getenv('RAFT_PACE', 'true').lower() in ('true', '1', 'yes')
        config.auto_clean_checkpoints = os.getenv('RAFT_AUTO_CLEAN_CHECKPOINTS', 'false').lower() in ('true', '1', 'yes')
        
        # Template Configuration
        config.templates = os.getenv('RAFT_TEMPLATES', config.templates)
        
        return config
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.datapath.exists() and str(self.datapath) != ".":
            raise ValueError(f"Data path does not exist: {self.datapath}")
        
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