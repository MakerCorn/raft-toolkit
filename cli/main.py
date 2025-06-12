"""
CLI interface for RAFT toolkit using the shared core modules.
"""
import argparse
import logging
import sys
import time
from pathlib import Path

from core.config import RaftConfig, get_config
from core.raft_engine import RaftEngine
try:
    from core.logging import log_setup
except ImportError:
    def log_setup():
        import logging
        logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("raft_cli")

def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="RAFT Toolkit - Retrieval Augmentation Fine-Tuning Dataset Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # I/O Arguments
    parser.add_argument("--datapath", type=Path, required=True,
                        help="Path to the input document or directory")
    parser.add_argument("--output", type=str, default="./raft_output",
                        help="Path to save the generated dataset")
    parser.add_argument("--output-format", type=str, default="hf",
                        choices=["hf", "completion", "chat", "eval"],
                        help="Format to convert the dataset to")
    parser.add_argument("--output-type", type=str, default="jsonl",
                        choices=["jsonl", "parquet"],
                        help="File type to export the dataset to")
    parser.add_argument("--output-chat-system-prompt", type=str,
                        help="System prompt for chat output format")
    parser.add_argument("--output-completion-prompt-column", type=str, default="prompt",
                        help="Prompt column name for completion format")
    parser.add_argument("--output-completion-completion-column", type=str, default="completion",
                        help="Completion column name for completion format")

    # Processing Arguments
    parser.add_argument("--distractors", type=int, default=1,
                        help="Number of distractor documents per data point")
    parser.add_argument("--p", type=float, default=1.0,
                        help="Probability of including oracle document in context")
    parser.add_argument("--questions", type=int, default=5,
                        help="Number of questions to generate per chunk")
    parser.add_argument("--chunk_size", type=int, default=512,
                        help="Size of each chunk in tokens")
    parser.add_argument("--doctype", type=str, default="pdf",
                        choices=["pdf", "txt", "json", "api", "pptx"],
                        help="Type of the input document")
    parser.add_argument("--chunking-strategy", type=str, default="semantic",
                        choices=["semantic", "fixed", "sentence"],
                        help="Chunking algorithm to use")
    parser.add_argument("--chunking-params", type=str,
                        help="JSON string of extra chunker parameters")

    # AI Model Arguments
    parser.add_argument("--openai_key", type=str,
                        help="OpenAI API key (can also use OPENAI_API_KEY env var)")
    parser.add_argument("--embedding_model", type=str, default="nomic-embed-text",
                        help="Embedding model for chunking")
    parser.add_argument("--completion_model", type=str, default="llama3.2",
                        help="Model for question and answer generation")
    parser.add_argument("--system-prompt-key", type=str, default="gpt",
                        help="System prompt template to use")

    # Azure Arguments
    parser.add_argument("--use-azure-identity", action="store_true",
                        help="Use Azure Default Credentials for authentication")

    # Performance Arguments
    parser.add_argument("--workers", type=int, default=1,
                        help="Number of worker threads for QA generation")
    parser.add_argument("--embed-workers", type=int, default=1,
                        help="Number of worker threads for embedding/chunking")
    parser.add_argument("--pace", action="store_true", default=True,
                        help="Pace LLM calls to stay within rate limits")
    parser.add_argument("--auto-clean-checkpoints", action="store_true",
                        help="Automatically clean checkpoints after completion")

    # Template Arguments
    parser.add_argument("--templates", type=str, default="./templates/",
                        help="Directory containing prompt templates")

    # Utility Arguments
    parser.add_argument("--preview", action="store_true",
                        help="Show processing preview without running")
    parser.add_argument("--validate", action="store_true",
                        help="Validate configuration and inputs only")
    parser.add_argument("--env-file", type=str,
                        help="Path to .env file for configuration")

    return parser

def override_config_from_args(config: RaftConfig, args: argparse.Namespace) -> RaftConfig:
    """Override configuration with command line arguments."""
    # Only override if explicitly provided
    if args.datapath:
        config.datapath = args.datapath
    if args.output != "./raft_output":  # Only if changed from default
        config.output = args.output
    if args.output_format != "hf":
        config.output_format = args.output_format
    if args.output_type != "jsonl":
        config.output_type = args.output_type
    if args.output_chat_system_prompt:
        config.output_chat_system_prompt = args.output_chat_system_prompt
    if args.output_completion_prompt_column != "prompt":
        config.output_completion_prompt_column = args.output_completion_prompt_column
    if args.output_completion_completion_column != "completion":
        config.output_completion_completion_column = args.output_completion_completion_column
    
    if args.distractors != 1:
        config.distractors = args.distractors
    if args.p != 1.0:
        config.p = args.p
    if args.questions != 5:
        config.questions = args.questions
    if args.chunk_size != 512:
        config.chunk_size = args.chunk_size
    if args.doctype != "pdf":
        config.doctype = args.doctype
    if args.chunking_strategy != "semantic":
        config.chunking_strategy = args.chunking_strategy
    if args.chunking_params:
        import json
        try:
            config.chunking_params = json.loads(args.chunking_params)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid chunking params JSON: {e}")
            sys.exit(1)
    
    if args.openai_key:
        config.openai_key = args.openai_key
    if args.embedding_model != "nomic-embed-text":
        config.embedding_model = args.embedding_model
    if args.completion_model != "llama3.2":
        config.completion_model = args.completion_model
    if args.system_prompt_key != "gpt":
        config.system_prompt_key = args.system_prompt_key
    
    if args.use_azure_identity:
        config.use_azure_identity = args.use_azure_identity
    
    if args.workers != 1:
        config.workers = args.workers
    if args.embed_workers != 1:
        config.embed_workers = args.embed_workers
    if not args.pace:  # Only if explicitly disabled
        config.pace = args.pace
    if args.auto_clean_checkpoints:
        config.auto_clean_checkpoints = args.auto_clean_checkpoints
    
    if args.templates != "./templates/":
        config.templates = args.templates
    
    return config

def show_preview(engine: RaftEngine, data_path: Path) -> None:
    """Show processing preview."""
    try:
        preview = engine.get_processing_preview(data_path)
        
        print("\n" + "="*60)
        print("RAFT PROCESSING PREVIEW")
        print("="*60)
        print(f"Input Path: {preview['input_path']}")
        print(f"Document Type: {preview['doctype']}")
        print(f"Files to Process: {len(preview['files_to_process'])}")
        
        if len(preview['files_to_process']) <= 5:
            for file_path in preview['files_to_process']:
                print(f"  - {file_path}")
        else:
            for file_path in preview['files_to_process'][:3]:
                print(f"  - {file_path}")
            print(f"  ... and {len(preview['files_to_process']) - 3} more files")
        
        print(f"\nEstimated Chunks: {preview['estimated_chunks']}")
        print(f"Estimated QA Points: {preview['estimated_qa_points']}")
        print(f"Questions per Chunk: {engine.config.questions}")
        print(f"Distractors per Point: {engine.config.distractors}")
        print("\nUse --validate to check configuration or run without --preview to start processing.")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        sys.exit(1)

def validate_only(engine: RaftEngine, data_path: Path) -> None:
    """Validate configuration and inputs only."""
    try:
        engine.validate_inputs(data_path)
        print("\n✅ Configuration and inputs are valid!")
        print(f"Ready to process: {data_path}")
        print(f"Output will be saved to: {engine.config.output}")
        print(f"Document type: {engine.config.doctype}")
        print(f"Output format: {engine.config.output_format} ({engine.config.output_type})")
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)

def main():
    """Main CLI entry point."""
    log_setup()
    
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Load configuration from environment (and optional .env file)
        config = get_config(args.env_file)
        
        # Override with command line arguments
        config = override_config_from_args(config, args)
        
        # Create engine
        engine = RaftEngine(config)
        
        # Handle special modes
        if args.preview:
            show_preview(engine, config.datapath)
            return
        
        if args.validate:
            validate_only(engine, config.datapath)
            return
        
        # Normal processing
        logger.info("Starting RAFT dataset generation")
        logger.info(f"Input: {config.datapath}")
        logger.info(f"Output: {config.output}")
        logger.info(f"Document type: {config.doctype}")
        logger.info(f"Chunking strategy: {config.chunking_strategy}")
        logger.info(f"Model: {config.completion_model}")
        
        start_time = time.time()
        
        # Validate inputs
        engine.validate_inputs(config.datapath)
        
        # Generate dataset
        stats = engine.generate_dataset(config.datapath, config.output)
        
        # Show results
        total_time = time.time() - start_time
        print("\n" + "="*60)
        print("RAFT GENERATION COMPLETED")
        print("="*60)
        print(f"Total QA Points Generated: {stats['total_qa_points']}")
        print(f"Successful Chunks: {stats['successful_chunks']}")
        print(f"Failed Chunks: {stats['failed_chunks']}")
        print(f"Total Processing Time: {total_time:.2f}s")
        print(f"Average Time per Chunk: {stats['avg_time_per_chunk']:.2f}s")
        print(f"Tokens per Second: {stats['token_usage']['tokens_per_second']:.1f}")
        print(f"Total Tokens Used: {stats['token_usage']['total_tokens']:,}")
        print(f"Output Location: {config.output}")
        print("="*60)
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()